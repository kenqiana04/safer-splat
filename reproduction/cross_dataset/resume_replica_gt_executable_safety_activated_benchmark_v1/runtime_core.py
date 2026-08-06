"""Task-local read-only bindings for the frozen Replica map and PR84/PR86 methods."""
from __future__ import annotations

import math
import subprocess
import sys
import time
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Iterable, Iterator

import clarabel
import numpy as np
from scipy import sparse

from common import canonical_json_bytes, jsonable, sha256_json
from task_config import (
    CERTIFIER_TIME_BUDGET_S, DT, EFFECTIVE_RADIUS, H_STOP_MAX, LIBRARY_ID,
    MAP_SNAPSHOT_ID, MARGIN, PHYSICAL_MIN_CLEARANCE_M, ROBOT_RADIUS,
    ROUTE_FRACTIONS, SLOT_IDS, SURFACE_CLEARANCE_OFFSETS_M,
    SURFACE_TANGENT_OFFSETS_M, TERMINAL_TOLERANCE, U_BOUND,
    V_BOUND, VELOCITY_MAGNITUDES,
)

TASK_ROOT = Path(__file__).resolve().parent
for payload in (TASK_ROOT / "runtime_payload/pr84", TASK_ROOT / "runtime_payload/pr86"):
    if payload.exists() and str(payload) not in sys.path:
        sys.path.insert(0, str(payload))

try:
    from adapters.current_cbf_adapter import CurrentCBFAdapter
    from adapters.gaussian_barrier_adapter import AnalyticSphereGaussianMapAdapter
    from adapters.normative_dynamics_adapter import PositionFirstForwardEulerDoubleIntegrator
    from alternative_library.directional_library import build_directional_library
    from alternative_library.result_types import Bounds as DirectionalBounds
    from certifier.actuator_certificate import certify_actuator
    from certifier.backup_certifier import BackupCertifier
    from certifier.braking_backup_policy import DeterministicBrakingPolicy
    from certifier.current_feasibility_certificate import certify_current_feasibility
    from certifier.executable_safety_certifier import ExecutableSafetyCertifier
    from certifier.result_types import (
        ActuatorBounds, BarrierStatus, Control, ExecutableStatus, State,
    )
    from certifier.segment_certificate import SweptSegmentCertifier
    from certifier.terminal_certificate import TerminalCertifier
    from certifier.terminal_set import BrakingToRestTerminalSet
except ImportError as exc:  # pragma: no cover - explicit server payload gate
    raise RuntimeError("RUNTIME_PAYLOAD_NOT_MATERIALIZED") from exc


ALPHA = 5.0
BETA = 1.0


def unit(vector: np.ndarray) -> np.ndarray | None:
    value = np.asarray(vector, dtype=np.float64)
    norm = float(np.linalg.norm(value))
    if value.shape != (3,) or not np.all(np.isfinite(value)) or norm <= 1.0e-12:
        return None
    return value / norm


def deterministic_tangent(normal: np.ndarray, preferred: np.ndarray) -> np.ndarray:
    projected = preferred - float(preferred @ normal) * normal
    result = unit(projected)
    if result is not None:
        return result
    axes = np.eye(3, dtype=np.float64)
    index = min(range(3), key=lambda item: (abs(float(axes[item] @ normal)), item))
    projected = axes[index] - float(axes[index] @ normal) * normal
    result = unit(projected)
    if result is None:
        raise RuntimeError("DETERMINISTIC_TANGENT_DEGENERATE")
    return result


def nominal_control(position: np.ndarray, velocity: np.ndarray, goal: np.ndarray) -> np.ndarray:
    desired_velocity = np.clip(5.0 * (np.asarray(goal) - np.asarray(position)), -V_BOUND, V_BOUND)
    return np.clip(desired_velocity - np.asarray(velocity), -U_BOUND, U_BOUND)


@dataclass(frozen=True)
class FilteredPrimary:
    status: str
    u_nom: np.ndarray
    u_filtered: np.ndarray | None
    residual_max: float | None
    active_ids: np.ndarray
    runtime_s: float


class ReplicaRuntime:
    """One immutable represented-map runtime shared by every method."""

    def __init__(self, map_root: Path) -> None:
        self.map_root = Path(map_root)
        self.map_adapter = AnalyticSphereGaussianMapAdapter.from_canonical_arrays(
            self.map_root, MAP_SNAPSHOT_ID, EFFECTIVE_RADIUS
        )
        self.centers = self.map_adapter.centers
        self.radii = self.map_adapter.primitive_radii
        self.tree = self.map_adapter.tree
        self.max_primitive_radius = float(np.max(self.radii))
        self.bounds = ActuatorBounds(
            (-U_BOUND,) * 3, (U_BOUND,) * 3, (-V_BOUND,) * 3,
            (V_BOUND,) * 3, DT,
        )
        self.dynamics = PositionFirstForwardEulerDoubleIntegrator(self.bounds)
        self.current_adapter = CurrentCBFAdapter(
            self.map_adapter, candidate_constraint_provider=self.current_cbf_rows,
            tolerance=1.0e-10,
        )
        self.segment_certifier = SweptSegmentCertifier(
            self.dynamics, self.map_adapter.segment_backend, EFFECTIVE_RADIUS, 0.0
        )
        self.terminal_set = BrakingToRestTerminalSet(TERMINAL_TOLERANCE)
        self.terminal_certifier = TerminalCertifier(
            self.terminal_set, self.current_adapter, self.segment_certifier
        )
        self.braking_policy = DeterministicBrakingPolicy(self.bounds, TERMINAL_TOLERANCE)
        if self.braking_policy.h_stop_max() != H_STOP_MAX:
            raise RuntimeError("H_STOP_MAX_IDENTITY_MISMATCH")
        self.backup_certifier = BackupCertifier(
            self.dynamics, self.segment_certifier, self.terminal_certifier,
            self.braking_policy,
        )
        identities = {
            "map_snapshot": MAP_SNAPSHOT_ID,
            "normative_model": self.dynamics.identity,
            "terminal_set": self.terminal_set.identity,
            "braking_policy": self.braking_policy.identity,
            "directional_library": LIBRARY_ID,
        }
        self.unified_certifier = ExecutableSafetyCertifier(
            self.current_adapter, self.segment_certifier, self.terminal_certifier,
            self.backup_certifier, self.braking_policy, identities,
        )

    def point_result(self, point: np.ndarray):
        return self.map_adapter.query(np.asarray(point, dtype=np.float64), MAP_SNAPSHOT_ID, "FULL")

    def current_cbf_rows(self, state: State) -> tuple[np.ndarray, np.ndarray]:
        position = np.asarray(state.position, dtype=np.float64)
        velocity = np.asarray(state.velocity, dtype=np.float64)
        h_limit = (math.sqrt(3.0) * U_BOUND + 6.0 * math.sqrt(3.0) * V_BOUND) / (ALPHA * BETA)
        radius = self.max_primitive_radius + EFFECTIVE_RADIUS + h_limit + 1.0e-12
        ids = np.asarray(self.tree.query_ball_point(position, radius), dtype=np.int64)
        return self.cbf_rows_for_ids(position, velocity, ids)[:2]

    def cbf_rows_for_ids(self, position: np.ndarray, velocity: np.ndarray, ids: np.ndarray) -> tuple[np.ndarray, np.ndarray, np.ndarray]:
        ids = np.asarray(ids, dtype=np.int64)
        if ids.size == 0:
            return np.empty((0, 3)), np.empty((0,)), ids
        centers = np.asarray(self.centers[ids], dtype=np.float64)
        radii = np.asarray(self.radii[ids], dtype=np.float64) + EFFECTIVE_RADIUS
        delta = np.asarray(position, dtype=np.float64)[None, :] - centers
        distance = np.linalg.norm(delta, axis=1)
        safe_distance = np.maximum(distance, 1.0e-12)
        normal = delta / safe_distance[:, None]
        h = distance - radii
        projection = normal @ np.asarray(velocity, dtype=np.float64)
        hessian_v = (
            np.asarray(velocity, dtype=np.float64)[None, :] - normal * projection[:, None]
        ) / safe_distance[:, None]
        v_h_v = np.einsum("ij,j->i", hessian_v, np.asarray(velocity, dtype=np.float64))
        legacy_l = -v_h_v - ALPHA * projection - BETA * (projection + ALPHA * h)
        return -normal, -legacy_l, ids

    def potentially_active_ids(self, position: np.ndarray) -> np.ndarray:
        h_limit = (math.sqrt(3.0) * U_BOUND + 6.0 * math.sqrt(3.0) * V_BOUND) / (ALPHA * BETA)
        radius = self.max_primitive_radius + EFFECTIVE_RADIUS + h_limit + 1.0e-12
        return np.asarray(self.tree.query_ball_point(np.asarray(position), radius), dtype=np.int64)

    def filter_primary(self, position: np.ndarray, velocity: np.ndarray, goal: np.ndarray) -> FilteredPrimary:
        started = time.perf_counter()
        u_nom = nominal_control(position, velocity, goal)
        ids = self.potentially_active_ids(position)
        a_cbf, b_cbf, ids = self.cbf_rows_for_ids(position, velocity, ids)
        eye = np.eye(3, dtype=np.float64)
        rows = np.concatenate((a_cbf, eye, -eye, DT * eye, -DT * eye), axis=0)
        rhs = np.concatenate((
            b_cbf,
            np.full(3, U_BOUND), np.full(3, U_BOUND),
            np.full(3, V_BOUND) - velocity,
            np.full(3, V_BOUND) + velocity,
        ))
        settings = clarabel.DefaultSettings()
        settings.verbose = False
        solver = clarabel.DefaultSolver(
            sparse.csc_matrix(eye), -u_nom, sparse.csc_matrix(rows), rhs,
            [clarabel.NonnegativeConeT(rows.shape[0])], settings,
        )
        solution = solver.solve()
        status = str(solution.status)
        if status != "Solved":
            return FilteredPrimary(status, u_nom, None, None, ids, time.perf_counter() - started)
        control = np.asarray(solution.x, dtype=np.float64)
        residual = float(np.max(rows @ control - rhs))
        return FilteredPrimary(status, u_nom, control, residual, ids, time.perf_counter() - started)

    @staticmethod
    def make_state(record: dict[str, Any], *, timestamp: float = 0.0) -> State:
        return State(
            tuple(float(value) for value in record["position_m"]),
            tuple(float(value) for value in record["velocity_m_per_s"]),
            float(timestamp), MAP_SNAPSHOT_ID,
        )

    def directional_set(self, state: State, goal: np.ndarray, current_query=None):
        query = current_query or self.point_result(np.asarray(state.position))
        return build_directional_library(
            state.position, state.velocity, goal, query.status.value,
            query.active_gaussian_ids, self.centers,
            DirectionalBounds(),
        )

    @staticmethod
    def control_from_primary(primary: FilteredPrimary) -> Control | None:
        if primary.u_filtered is None:
            return None
        return Control(
            tuple(float(value) for value in primary.u_filtered),
            "EXISTING_CBF_FILTERED", "PRIMARY-CBF-FILTERED",
        )

    @staticmethod
    def directional_controls(candidate_set) -> tuple[Control, ...]:
        return tuple(
            Control(tuple(float(value) for value in slot.acceleration), slot.source, slot.candidate_id)
            for slot in candidate_set.available_slots
        )

    def evaluate_stage(self, record: dict[str, Any]) -> dict[str, Any]:
        state = self.make_state(record)
        position = np.asarray(state.position)
        velocity = np.asarray(state.velocity)
        goal = np.asarray(record["goal_m"], dtype=np.float64)
        current_query = self.point_result(position)
        primary = self.filter_primary(position, velocity, goal)
        primary_control = self.control_from_primary(primary)
        current_cert = None if primary_control is None else certify_current_feasibility(state, self.current_adapter, primary_control)
        endpoint = position + DT * velocity
        endpoint_query = self.point_result(endpoint)
        segment = None if primary_control is None else self.segment_certifier.certify(state, primary_control, MAP_SNAPSHOT_ID)
        terminal = self.terminal_certifier.certify(state, MAP_SNAPSHOT_ID)
        primary_backup = None
        if primary_control is not None and segment is not None and segment.certified and current_cert is not None and current_cert.certified:
            primary_backup = self.backup_certifier.certify(state, primary_control, MAP_SNAPSHOT_ID)
        candidate_set = self.directional_set(state, goal, current_query)
        alternatives = self.directional_controls(candidate_set)
        b2 = None
        b3 = None
        # Stage predicates need B2/B3 only after a safe immediate segment and
        # a failed primary backup witness. Earlier gates determine G0/G1/G4/G5
        # without consulting downstream method outcomes.
        if (
            primary_control is not None and current_cert is not None
            and current_cert.certified and segment is not None
            and segment.certified and primary_backup is not None
            and not primary_backup.certified and not terminal.certified
        ):
            b2 = self.unified_certifier.certify(
                state, primary_control, (), MAP_SNAPSHOT_ID, CERTIFIER_TIME_BUDGET_S
            )
            b3 = self.unified_certifier.certify(
                state, primary_control, alternatives, MAP_SNAPSHOT_ID,
                CERTIFIER_TIME_BUDGET_S,
            )

        current_feasible = bool(
            primary_control is not None and current_cert is not None and current_cert.certified
            and current_query.status == BarrierStatus.FINITE
        )
        endpoint_accept = bool(
            endpoint_query.status == BarrierStatus.FINITE
            and endpoint_query.h is not None and endpoint_query.h >= 0.0
        )
        segment_safe = bool(segment is not None and segment.certified)
        segment_unsafe = bool(segment is not None and segment.status.value == "CERTIFIED_UNSAFE")
        primary_backup_pass = bool(primary_backup is not None and primary_backup.certified)
        b2_pass = bool(b2 is not None and b2.committed_control_or_none is not None)
        b3_directional = bool(
            b3 is not None
            and b3.status == ExecutableStatus.CERTIFIED_ALTERNATIVE_CONTROL
            and b3.committed_control_or_none is not None
            and b3.committed_control_or_none.candidate_id in SLOT_IDS
        )
        b3_pass = bool(b3 is not None and b3.committed_control_or_none is not None)
        nonterminal = not terminal.certified

        group = None
        if not current_feasible and current_query.status == BarrierStatus.FINITE:
            group = "G5"
        elif terminal.certified:
            group = "G4"
        elif current_feasible and endpoint_accept and segment_unsafe and nonterminal:
            group = "G1"
        elif current_feasible and segment_safe and not primary_backup_pass and not b2_pass and b3_directional:
            group = "G3"
        elif current_feasible and segment_safe and not primary_backup_pass and not b2_pass and not b3_pass:
            group = "G2"
        elif current_feasible and segment_safe and primary_backup_pass and nonterminal:
            group = "G0"

        result = {
            "group": group,
            "state": record,
            "state_goal_hash": sha256_json({"position": record["position_m"], "velocity": record["velocity_m_per_s"], "goal": record["goal_m"], "map": MAP_SNAPSHOT_ID}),
            "u_nom": primary.u_nom,
            "u_filtered": primary.u_filtered,
            "primary_filter_status": primary.status,
            "primary_filter_residual_max": primary.residual_max,
            "active_cbf_row_count": len(primary.active_ids),
            "current_status": current_query.status.value,
            "current_h": current_query.h,
            "current_feasible": current_feasible,
            "endpoint_diagnostic_pass": endpoint_accept,
            "segment_safe": segment_safe,
            "segment_unsafe": segment_unsafe,
            "segment_lower_bound": None if segment is None else segment.lower_bound,
            "terminal": terminal.certified,
            "primary_backup_pass": primary_backup_pass,
            "primary_backup_horizon": None if primary_backup is None else primary_backup.horizon,
            "b2_pass": b2_pass,
            "b2_status": None if b2 is None else b2.status.value,
            "b3_pass": b3_pass,
            "b3_status": None if b3 is None else b3.status.value,
            "b3_directional_rescue": b3_directional,
            "b3_selected_candidate": None if b3 is None or b3.committed_control_or_none is None else b3.committed_control_or_none.candidate_id,
            "directional_slot_states": [jsonable(slot) for slot in candidate_set.slots],
            "directional_available_count": len(candidate_set.available_slots),
            "reference_future_read_count": 0,
            "formal_method_run_count": 0,
        }
        result["canonical_stage_sha256"] = sha256_json(result)
        return jsonable(result)

    def method_decision(self, method: str, record: dict[str, Any], *, timestamp: float = 0.0) -> dict[str, Any]:
        started = time.perf_counter()
        state = self.make_state(record, timestamp=timestamp)
        position = np.asarray(state.position)
        velocity = np.asarray(state.velocity)
        goal = np.asarray(record["goal_m"], dtype=np.float64)
        current_started = time.perf_counter()
        current_query = self.point_result(position)
        primary = self.filter_primary(position, velocity, goal)
        current_runtime = time.perf_counter() - current_started
        primary_control = self.control_from_primary(primary)
        base = {
            "method": method,
            "state_id": record["state_id"],
            "u_nom": primary.u_nom,
            "u_filtered": primary.u_filtered,
            "primary_filter_status": primary.status,
            "current_query_status": current_query.status.value,
            "current_h": current_query.h,
            "map_snapshot_id": MAP_SNAPSHOT_ID,
            "shared_input_hash": sha256_json({
                "state": {"position": state.position, "velocity": state.velocity, "timestamp": state.timestamp},
                "goal": goal, "u_nom": primary.u_nom,
                "u_filtered": primary.u_filtered, "map": MAP_SNAPSHOT_ID,
                "bounds": self.bounds.to_dict(), "effective_radius": EFFECTIVE_RADIUS,
            }),
            "directional_slot_states": [],
            "selected_candidate": None,
            "committed": False,
            "semantic_status": "FAIL_CLOSED_CURRENT_CBF_INFEASIBLE",
            "typed_reason": primary.status,
            "segment_lower_bound": None,
            "backup_horizon": None,
            "rejected_candidate_table": [],
            "component_timing": {"current_query_and_filter": current_runtime},
        }
        if primary_control is None:
            base["total_runtime_s"] = time.perf_counter() - started
            base["deadline_miss"] = base["total_runtime_s"] > DT
            return jsonable(base)
        actuator = certify_actuator(primary_control, self.bounds)
        current_cert = certify_current_feasibility(state, self.current_adapter, primary_control)
        if not actuator.certified or not current_cert.certified:
            base.update({
                "semantic_status": "FAIL_CLOSED_CURRENT_CBF_INFEASIBLE",
                "typed_reason": actuator.reason_code if not actuator.certified else current_cert.reason_code,
            })
        elif method == "B0_CURRENT_CBF_ONLY":
            base.update({
                "committed": True,
                "semantic_status": "CERTIFIED_NOMINAL_CONTROL",
                "typed_reason": "B0_CURRENT_FULL_QUERY_AND_ACTUATOR_PASS",
                "selected_candidate": primary_control.candidate_id,
                "control": primary_control.acceleration,
            })
        elif method == "B1_PLUS_SWEPT_SEGMENT":
            segment_started = time.perf_counter()
            segment = self.segment_certifier.certify(state, primary_control, MAP_SNAPSHOT_ID)
            base["component_timing"]["segment"] = time.perf_counter() - segment_started
            base["segment_lower_bound"] = segment.lower_bound
            if segment.certified:
                base.update({"committed": True, "semantic_status": "CERTIFIED_NOMINAL_CONTROL", "typed_reason": "B1_IMMEDIATE_SEGMENT_PASS", "selected_candidate": primary_control.candidate_id, "control": primary_control.acceleration})
            else:
                base.update({"semantic_status": "FAIL_CLOSED_IMMEDIATE_SEGMENT_UNSAFE", "typed_reason": segment.reason_code})
        else:
            alternatives = ()
            if method == "B3_FULL_UNIFIED_WITH_DIRECTIONAL_ALTERNATIVES":
                directional_started = time.perf_counter()
                candidate_set = self.directional_set(state, goal, current_query)
                alternatives = self.directional_controls(candidate_set)
                base["directional_slot_states"] = [jsonable(slot) for slot in candidate_set.slots]
                base["component_timing"]["alternative_generation"] = time.perf_counter() - directional_started
            result = self.unified_certifier.certify(
                state, primary_control, alternatives, MAP_SNAPSHOT_ID,
                CERTIFIER_TIME_BUDGET_S,
            )
            base.update({
                "committed": result.committed_control_or_none is not None,
                "semantic_status": result.status.value,
                "typed_reason": result.fail_closed_reason or result.status.value,
                "selected_candidate": None if result.committed_control_or_none is None else result.committed_control_or_none.candidate_id,
                "control": None if result.committed_control_or_none is None else result.committed_control_or_none.acceleration,
                "segment_lower_bound": None if result.segment_certificate is None else result.segment_certificate.lower_bound,
                "backup_horizon": None if result.backup_witness is None else result.backup_witness.horizon,
                "rejected_candidate_table": [item.to_dict() for item in result.rejected_candidates],
            })
            for key, value in result.timing.items():
                base["component_timing"][key] = value
        base["total_runtime_s"] = time.perf_counter() - started
        base["deadline_miss"] = base["total_runtime_s"] > DT
        return jsonable(base)


def velocity_directions(route_direction: np.ndarray, normal: np.ndarray, tangent: np.ndarray) -> tuple[tuple[str, np.ndarray], ...]:
    values = [
        ("ROUTE", route_direction), ("INWARD_NORMAL", -normal),
        ("OUTWARD_NORMAL", normal), ("TANGENT_POS", tangent),
        ("TANGENT_NEG", -tangent),
    ]
    for name, raw in (
        ("ROUTE_OUTWARD", route_direction + normal),
        ("ROUTE_INWARD", route_direction - normal),
        ("AXIS_X_POS", np.array([1.0, 0.0, 0.0])),
        ("AXIS_X_NEG", np.array([-1.0, 0.0, 0.0])),
        ("AXIS_Y_POS", np.array([0.0, 1.0, 0.0])),
        ("AXIS_Y_NEG", np.array([0.0, -1.0, 0.0])),
        ("AXIS_Z_POS", np.array([0.0, 0.0, 1.0])),
        ("AXIS_Z_NEG", np.array([0.0, 0.0, -1.0])),
    ):
        direction = unit(raw)
        if direction is not None:
            values.append((name, direction))
    return tuple(values)


def iter_activated_candidates(routes: list[dict[str, Any]], runtime: ReplicaRuntime) -> Iterator[dict[str, Any]]:
    """Fixed generator; it contains no method or reference outcome dependency."""
    seen: set[str] = set()
    for route in sorted(routes, key=lambda item: (int(item["execution_order"]), str(item["route_id"]))):
        start = np.asarray(route["start_m"], dtype=np.float64)
        goal = np.asarray(route["goal_m"], dtype=np.float64)
        direction = unit(goal - start)
        if direction is None:
            continue
        for fraction in ROUTE_FRACTIONS:
            base = (1.0 - fraction) * start + fraction * goal
            distance, primitive_id = runtime.tree.query(base, k=1)
            del distance
            center = np.asarray(runtime.centers[int(primitive_id)], dtype=np.float64)
            normal = unit(base - center)
            if normal is None:
                continue
            tangent = deterministic_tangent(normal, direction)
            directions = velocity_directions(direction, normal, tangent)
            position_templates: list[tuple[str, np.ndarray, float | None, float | None]] = [
                ("ROUTE_NODE" if fraction == 0.0 else "ROUTE_EDGE", base, None, None)
            ]
            primitive_surface_radius = float(runtime.radii[int(primitive_id)] + EFFECTIVE_RADIUS)
            for clearance in SURFACE_CLEARANCE_OFFSETS_M:
                for tangent_offset in SURFACE_TANGENT_OFFSETS_M:
                    position = center + normal * (primitive_surface_radius + clearance) + tangent * tangent_offset
                    position_templates.append(("REPRESENTED_SPHERE_SURFACE_NEIGHBOR", position, clearance, tangent_offset))
            for source_type, position, clearance, tangent_offset in position_templates:
                for direction_type, velocity_direction in directions:
                    for magnitude in VELOCITY_MAGNITUDES:
                        velocity = np.zeros(3, dtype=np.float64) if magnitude == 0.0 else magnitude * velocity_direction
                        state_key = sha256_json({"p": position, "v": velocity, "g": goal, "map": MAP_SNAPSHOT_ID})
                        if state_key in seen:
                            continue
                        seen.add(state_key)
                        yield {
                            "candidate_id": state_key,
                            "route_id": route["route_id"],
                            "route_execution_order": int(route["execution_order"]),
                            "source_type": source_type,
                            "route_fraction": float(fraction),
                            "velocity_direction_type": direction_type if magnitude > 0.0 else "ZERO",
                            "velocity_magnitude": float(magnitude),
                            "surface_clearance_offset_m": clearance,
                            "surface_tangent_offset_m": tangent_offset,
                            "represented_primitive_id": int(primitive_id),
                            "position_m": position,
                            "velocity_m_per_s": velocity,
                            "goal_m": goal,
                            "route_subset": route.get("subset"),
                            "reference_selection_inputs": [],
                            "future_outcome_inputs": [],
                        }


def representative_candidates(routes: list[dict[str, Any]]) -> list[dict[str, Any]]:
    records = []
    for route in sorted(routes, key=lambda item: (int(item["execution_order"]), str(item["route_id"]))):
        start = np.asarray(route["start_m"], dtype=np.float64)
        goal = np.asarray(route["goal_m"], dtype=np.float64)
        direction = unit(goal - start)
        if direction is None:
            continue
        for quartile, fraction in enumerate(ROUTE_FRACTIONS):
            position = (1.0 - fraction) * start + fraction * goal
            source = "ROUTE_NODE" if fraction == 0.0 else "ROUTE_EDGE"
            for magnitude in VELOCITY_MAGNITUDES:
                velocity = magnitude * direction
                record = {
                    "route_id": route["route_id"],
                    "route_execution_order": int(route["execution_order"]),
                    "source_type": source,
                    "spatial_quartile": int(quartile),
                    "route_fraction": float(fraction),
                    "velocity_direction_type": "ROUTE" if magnitude > 0.0 else "ZERO",
                    "velocity_magnitude": float(magnitude),
                    "zero_velocity": magnitude == 0.0,
                    "position_m": position,
                    "velocity_m_per_s": velocity,
                    "goal_m": goal,
                    "route_subset": route.get("subset"),
                    "physical_registry_segment_clearance_m": route.get("segment_mesh_distance_m"),
                    "selection_inputs": ["route_id", "node_or_edge", "velocity_magnitude", "spatial_quartile", "zero_nonzero", "canonical_sha256"],
                }
                record["candidate_id"] = sha256_json({"p": position, "v": velocity, "g": goal, "map": MAP_SNAPSHOT_ID})
                records.append(jsonable(record))
    return records


class ReplicaMeshOracle:
    """Batch-only client for the previously validated float64 official mesh oracle."""

    def __init__(self, backend: Path, mesh: Path, work_dir: Path) -> None:
        self.backend = Path(backend)
        self.mesh = Path(mesh)
        self.work_dir = Path(work_dir)

    @staticmethod
    def point_query(point: np.ndarray) -> str:
        return "P " + " ".join(f"{float(value):.17g}" for value in point)

    @staticmethod
    def segment_query(start: np.ndarray, end: np.ndarray) -> str:
        return "S " + " ".join(f"{float(value):.17g}" for value in np.concatenate((start, end)))

    def _run(self, queries: Iterable[str], name: str) -> list[float]:
        queries = list(queries)
        if not queries:
            return []
        self.work_dir.mkdir(parents=True, exist_ok=True)
        query_path = self.work_dir / f"{name}.queries.txt"
        output_path = self.work_dir / f"{name}.oracle.txt"
        query_path.write_text("\n".join(queries) + "\n", encoding="utf-8")
        subprocess.run([str(self.backend), str(self.mesh), str(query_path), str(output_path)], check=True)
        values = []
        for line in output_path.read_text(encoding="utf-8").splitlines():
            tokens = line.split()
            if len(tokens) < 2 or tokens[0] not in {"P", "S"}:
                raise RuntimeError("REFERENCE_ORACLE_OUTPUT_INVALID")
            value = float(tokens[1])
            if not math.isfinite(value):
                raise RuntimeError("REFERENCE_ORACLE_OUTPUT_NONFINITE")
            values.append(value)
        if len(values) != len(queries):
            raise RuntimeError("REFERENCE_ORACLE_ROW_COUNT_MISMATCH")
        return values

    def points(self, points: Iterable[np.ndarray], name: str) -> list[float]:
        return self._run((self.point_query(point) for point in points), name)

    def segments(self, segments: Iterable[tuple[np.ndarray, np.ndarray]], name: str) -> list[float]:
        return self._run((self.segment_query(start, end) for start, end in segments), name)


def physically_admissible(point_distance: float, goal_distance: float) -> bool:
    return bool(
        math.isfinite(point_distance) and math.isfinite(goal_distance)
        and point_distance >= PHYSICAL_MIN_CLEARANCE_M
        and goal_distance >= PHYSICAL_MIN_CLEARANCE_M
    )
