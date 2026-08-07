"""Read-only PR84/PR86 runtime over official anisotropic SAFER maps."""
from __future__ import annotations

import json
import os
import sys
import time
from dataclasses import dataclass
from pathlib import Path
from typing import Any

import clarabel
import numpy as np
import torch
from scipy import sparse

TASK_ROOT = Path(__file__).resolve().parents[1]
PROJECT = Path("/disk1/zlab/projects/safer-splat")
sys.path[:0] = [str(TASK_ROOT / "runtime_payload/pr84"), str(TASK_ROOT / "runtime_payload/pr86"), str(PROJECT)]

from adapters.current_cbf_adapter import CurrentCBFAdapter  # noqa: E402
from adapters.gaussian_barrier_adapter import SourceGaussianBarrierAdapter  # noqa: E402
from adapters.normative_dynamics_adapter import PositionFirstForwardEulerDoubleIntegrator  # noqa: E402
from alternative_library.directional_library import build_directional_library  # noqa: E402
from alternative_library.result_types import Bounds as DirectionalBounds  # noqa: E402
from cbf.cbf_utils import CBF  # noqa: E402
from certifier.actuator_certificate import certify_actuator  # noqa: E402
from certifier.backup_certifier import BackupCertifier  # noqa: E402
from certifier.braking_backup_policy import DeterministicBrakingPolicy  # noqa: E402
from certifier.current_feasibility_certificate import certify_current_feasibility  # noqa: E402
from certifier.executable_safety_certifier import ExecutableSafetyCertifier  # noqa: E402
from certifier.result_types import ActuatorBounds, Control, ExecutableStatus, State  # noqa: E402
from certifier.segment_backends.conservative_interval import ConservativeSignedDistanceIntervalBackend  # noqa: E402
from certifier.segment_certificate import SweptSegmentCertifier  # noqa: E402
from certifier.terminal_certificate import TerminalCertifier  # noqa: E402
from certifier.terminal_set import BrakingToRestTerminalSet  # noqa: E402
from dynamics.systems import DoubleIntegrator  # noqa: E402
from splat.gsplat_utils import GSplatLoader  # noqa: E402

DT = .05
U_BOUND = .1
V_BOUND = .1
EFFECTIVE_RADIUS = .11
TERMINAL_TOLERANCE = 1e-12
H_STOP_MAX = 20
TIME_BUDGET = 30.0
LIBRARY_ID = "REPLICA_GT_REPRESENTED_MAP_DIRECTIONAL_ALTERNATIVE_LIBRARY_V1"
SLOT_IDS = {
    "ALT-01-OUTWARD", "ALT-02-GOAL-TANGENT", "ALT-03-AUX-TANGENT-POS",
    "ALT-04-AUX-TANGENT-NEG", "ALT-05-BRAKE-BIASED-GOAL-TANGENT",
    "ALT-06-BRAKE-BIASED-OUTWARD",
}


def jsonable(value: Any) -> Any:
    if isinstance(value, np.ndarray):
        return value.tolist()
    if isinstance(value, np.generic):
        return value.item()
    if hasattr(value, "to_dict"):
        return jsonable(value.to_dict())
    if isinstance(value, dict):
        return {str(key): jsonable(item) for key, item in value.items()}
    if isinstance(value, (list, tuple)):
        return [jsonable(item) for item in value]
    return value


def nominal_control(position: np.ndarray, velocity: np.ndarray, goal: np.ndarray) -> np.ndarray:
    desired_velocity = np.clip(5.0 * (goal - position), -V_BOUND, V_BOUND)
    return np.clip(desired_velocity - velocity, -U_BOUND, U_BOUND)


@dataclass
class Primary:
    status: str
    u_nom: np.ndarray
    control: np.ndarray | None
    residual: float | None
    reduced_rows: int
    runtime_s: float


class SourceRuntime:
    def __init__(self, config_path: Path, snapshot_id: str) -> None:
        os.chdir(PROJECT)
        self.snapshot_id = snapshot_id
        self.loader = GSplatLoader(Path(config_path), "cuda:0")
        def bridge(point, **kwargs):
            if not torch.is_tensor(point):
                point = torch.as_tensor(point, device="cuda:0", dtype=torch.float32)
            return self.loader.query_distance(point, **kwargs)
        self.map_adapter = SourceGaussianBarrierAdapter(bridge, snapshot_id, EFFECTIVE_RADIUS, int(self.loader.means.shape[0]))
        self.map_adapter.segment_backend = ConservativeSignedDistanceIntervalBackend(self.map_adapter)
        self.centers = self.loader.means.detach().cpu().double().numpy()
        bounds = ActuatorBounds((-U_BOUND,) * 3, (U_BOUND,) * 3, (-V_BOUND,) * 3, (V_BOUND,) * 3, DT)
        self.bounds = bounds
        self.dynamics = PositionFirstForwardEulerDoubleIntegrator(bounds)
        self.source_cbf = CBF(self.loader, DoubleIntegrator(torch.device("cuda:0")), 5.0, 1.0, EFFECTIVE_RADIUS, distance_type="ball-to-ellipsoid")
        self.current_adapter = CurrentCBFAdapter(self.map_adapter, candidate_constraint_provider=self.current_rows, tolerance=1e-10)
        self.segment_certifier = SweptSegmentCertifier(self.dynamics, self.map_adapter.segment_backend, EFFECTIVE_RADIUS, 0.0)
        self.terminal_set = BrakingToRestTerminalSet(TERMINAL_TOLERANCE)
        self.terminal_certifier = TerminalCertifier(self.terminal_set, self.current_adapter, self.segment_certifier)
        self.braking_policy = DeterministicBrakingPolicy(bounds, TERMINAL_TOLERANCE)
        if self.braking_policy.h_stop_max() != H_STOP_MAX:
            raise RuntimeError("H_STOP_MAX_IDENTITY_MISMATCH")
        self.backup_certifier = BackupCertifier(self.dynamics, self.segment_certifier, self.terminal_certifier, self.braking_policy)
        self.unified = ExecutableSafetyCertifier(self.current_adapter, self.segment_certifier, self.terminal_certifier, self.backup_certifier, self.braking_policy, {
            "map_snapshot": snapshot_id, "normative_model": self.dynamics.identity,
            "terminal_set": self.terminal_set.identity, "braking_policy": self.braking_policy.identity,
            "directional_library": LIBRARY_ID,
        })

    def torch_state(self, state: State) -> torch.Tensor:
        return torch.tensor((*state.position, *state.velocity), device="cuda:0", dtype=torch.float32)

    def current_rows(self, state: State) -> tuple[np.ndarray, np.ndarray]:
        x = self.torch_state(state)
        zero = torch.zeros(3, device="cuda:0", dtype=torch.float32)
        a, b, _, _ = self.source_cbf.get_QP_matrices(x, zero, minimal=False)
        return np.asarray(a, dtype=np.float64), np.asarray(b, dtype=np.float64)

    def filter_primary(self, state: State, goal: np.ndarray) -> Primary:
        started = time.perf_counter()
        position = np.asarray(state.position, dtype=np.float64)
        velocity = np.asarray(state.velocity, dtype=np.float64)
        u_nom = nominal_control(position, velocity, goal)
        x = self.torch_state(state)
        desired = torch.as_tensor(u_nom, device="cuda:0", dtype=torch.float32)
        try:
            a, b, p, q = self.source_cbf.get_QP_matrices(x, desired, minimal=True)
            eye = np.eye(3, dtype=np.float64)
            a = np.concatenate((np.asarray(a, dtype=np.float64), eye, -eye, DT * eye, -DT * eye), axis=0)
            b = np.concatenate((np.asarray(b, dtype=np.float64), np.full(3, U_BOUND), np.full(3, U_BOUND), np.full(3, V_BOUND) - velocity, np.full(3, V_BOUND) + velocity))
            settings = clarabel.DefaultSettings(); settings.verbose = False
            solver = clarabel.DefaultSolver(sparse.csc_matrix(p), np.asarray(q, dtype=np.float64), sparse.csc_matrix(a), b, [clarabel.NonnegativeConeT(len(b))], settings)
            solution = solver.solve()
            status = str(solution.status)
            if status != "Solved":
                return Primary(status, u_nom, None, None, len(a), time.perf_counter() - started)
            control = np.asarray(solution.x, dtype=np.float64)
            return Primary(status, u_nom, control, float(np.max(a @ control - b)), len(a), time.perf_counter() - started)
        except Exception as exc:
            return Primary("PRIMARY_QP_ERROR:" + type(exc).__name__, u_nom, None, None, 0, time.perf_counter() - started)

    def state(self, record: dict[str, Any], timestamp: float = 0.0) -> State:
        return State(tuple(record["position_m"]), tuple(record["velocity_m_per_s"]), timestamp, self.snapshot_id)

    def directional_controls(self, state: State, goal: np.ndarray, query) -> tuple[Control, ...]:
        candidates = build_directional_library(state.position, state.velocity, goal, query.status.value, query.active_gaussian_ids, self.centers, DirectionalBounds())
        return tuple(Control(tuple(slot.acceleration), slot.source, slot.candidate_id) for slot in candidates.available_slots)

    def method_decision(self, method: str, record: dict[str, Any], timestamp: float = 0.0) -> dict[str, Any]:
        started = time.perf_counter()
        state = self.state(record, timestamp)
        goal = np.asarray(record["goal_m"], dtype=np.float64)
        query = self.map_adapter.query(state.position, self.snapshot_id, "FULL")
        primary = self.filter_primary(state, goal)
        control = None if primary.control is None else Control(tuple(float(v) for v in primary.control), "EXISTING_CBF_FILTERED", "PRIMARY-CBF-FILTERED")
        result = {
            "method": method, "state_id": record["state_id"], "u_nom": primary.u_nom,
            "u_filtered": primary.control, "primary_filter_status": primary.status,
            "primary_filter_residual_max": primary.residual, "active_cbf_row_count": primary.reduced_rows,
            "current_query_status": query.status.value, "current_h": query.h,
            "selected_candidate": None, "committed": False,
            "semantic_status": "FAIL_CLOSED_CURRENT_CBF_INFEASIBLE", "typed_reason": primary.status,
            "segment_lower_bound": None, "backup_horizon": None, "directional_slot_states": [],
            "component_timing": {"current_query_and_filter": primary.runtime_s},
        }
        if control is not None:
            actuator = certify_actuator(control, self.bounds)
            current = certify_current_feasibility(state, self.current_adapter, control)
            if not actuator.certified or not current.certified:
                result["typed_reason"] = actuator.reason_code if not actuator.certified else current.reason_code
            elif method == "B0_CURRENT_CBF_ONLY":
                result.update({"committed": True, "semantic_status": "CERTIFIED_NOMINAL_CONTROL", "typed_reason": "B0_CURRENT_FULL_QUERY_AND_ACTUATOR_PASS", "selected_candidate": control.candidate_id})
            elif method == "B1_PLUS_SWEPT_SEGMENT":
                segment = self.segment_certifier.certify(state, control, self.snapshot_id)
                result["segment_lower_bound"] = segment.lower_bound
                if segment.certified:
                    result.update({"committed": True, "semantic_status": "CERTIFIED_NOMINAL_CONTROL", "typed_reason": "B1_IMMEDIATE_SEGMENT_PASS", "selected_candidate": control.candidate_id})
                else:
                    result.update({"semantic_status": "FAIL_CLOSED_IMMEDIATE_SEGMENT_UNSAFE", "typed_reason": segment.reason_code})
            else:
                alternatives = () if method.startswith("B2_") else self.directional_controls(state, goal, query)
                certified = self.unified.certify(state, control, alternatives, self.snapshot_id, TIME_BUDGET)
                result.update({
                    "committed": certified.committed_control_or_none is not None,
                    "semantic_status": certified.status.value,
                    "typed_reason": certified.fail_closed_reason or certified.status.value,
                    "selected_candidate": None if certified.committed_control_or_none is None else certified.committed_control_or_none.candidate_id,
                    "segment_lower_bound": None if certified.segment_certificate is None else certified.segment_certificate.lower_bound,
                    "backup_horizon": None if certified.backup_witness is None else certified.backup_witness.horizon,
                    "rejected_candidate_table": [item.to_dict() for item in certified.rejected_candidates],
                })
                for key, value in certified.timing.items():
                    result["component_timing"][key] = value
        result["total_runtime_s"] = time.perf_counter() - started
        result["deadline_miss"] = result["total_runtime_s"] > DT
        return jsonable(result)
