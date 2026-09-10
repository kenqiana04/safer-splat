#!/usr/bin/env python3
"""Run the frozen three-trial Active Runtime Smoke V2.

This task-local program only wires existing runtime and map/controller modules.
It owns no routing, certification, selection, plant, token, or trace policy.
"""

from __future__ import annotations

import argparse
from collections import Counter
import dataclasses
import hashlib
import json
import math
import os
from pathlib import Path
import platform
import random
import statistics
import subprocess
import sys
import time
from typing import Any, Callable

import numpy as np
import torch


TASK_DIR = Path(__file__).resolve().parent
CONFIG_PATH = TASK_DIR / "SMOKE_CONFIG.json"
EXPECTED_HEAD = "8ba397bee31d4c42deebc52104c6409336a96fd9"
FIXED_TRIALS = (10, 50, 90)


def normalize(value: Any) -> Any:
    if dataclasses.is_dataclass(value):
        return normalize(dataclasses.asdict(value))
    if isinstance(value, dict):
        return {str(key): normalize(item) for key, item in value.items()}
    if isinstance(value, (tuple, list)):
        return [normalize(item) for item in value]
    if hasattr(value, "value"):
        return normalize(value.value)
    if isinstance(value, np.generic):
        return value.item()
    return value


def write_json(path: Path, value: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary = path.with_suffix(path.suffix + ".tmp")
    temporary.write_text(json.dumps(normalize(value), indent=2, sort_keys=True, allow_nan=False) + "\n", encoding="utf-8", newline="\n")
    temporary.replace(path)


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def semantic_sha256(value: Any) -> str:
    payload = json.dumps(normalize(value), sort_keys=True, separators=(",", ":"), allow_nan=False).encode("utf-8")
    return hashlib.sha256(payload).hexdigest()


def git_output(checkout: Path, *args: str) -> str:
    return subprocess.run(["git", "-C", str(checkout), *args], check=True, text=True, capture_output=True).stdout.strip()


def trial_geometry(trial_id: int) -> tuple[np.ndarray, np.ndarray]:
    t = np.linspace(0, 2 * np.pi, 100)
    t_z = 10 * np.linspace(0, 2 * np.pi, 100)
    radius_config = 0.784 / 2
    center = np.array([-0.08, -0.03, 0.05])
    starts = np.stack([radius_config * np.cos(t), radius_config * np.sin(t), 0.01 * np.sin(t_z)], axis=-1) + center
    goals = np.stack([radius_config * np.cos(t + np.pi), radius_config * np.sin(t + np.pi), 0.01 * np.sin(t_z + np.pi)], axis=-1) + center
    return starts[trial_id], goals[trial_id]


def verify_inputs(checkout: Path, config: dict[str, Any]) -> tuple[str, list[dict[str, Any]]]:
    if git_output(checkout, "rev-parse", "HEAD") != EXPECTED_HEAD:
        raise RuntimeError("RUNTIME_SOURCE_DRIFT")
    tree = git_output(checkout, "rev-parse", "HEAD:reproduction/runtime/active_runtime_assurance_v2")
    if tree != "c60be4c1977932c53b37e500e96c5ddf7cd2d820":
        raise RuntimeError("RUNTIME_TREE_IDENTITY_MISMATCH")
    runtime_diff = git_output(checkout, "diff", "--name-only", EXPECTED_HEAD, "--", "reproduction/runtime/active_runtime_assurance_v2")
    if runtime_diff:
        raise RuntimeError("RUNTIME_SOURCE_DIFF_NONZERO")
    root = (checkout / config["map_relative_path"]).resolve(strict=True)
    records = []
    for expected in config["map_artifacts"]:
        path = root / expected["relative_path"]
        actual = {"relative_path": expected["relative_path"], "size": path.stat().st_size, "sha256": sha256_file(path)}
        if actual != expected:
            raise RuntimeError("MAP_ARTIFACT_IDENTITY_MISMATCH:" + expected["relative_path"])
        records.append(actual)
    map_identity = semantic_sha256({"scene": "stonehenge", "artifacts": records})
    if map_identity != config["map_identity"]:
        raise RuntimeError("MAP_SEMANTIC_IDENTITY_MISMATCH")
    return map_identity, records


class CountedModule:
    def __init__(self, module: Any, method: str, counter: Counter[str]) -> None:
        self._module = module
        self._method = method
        self._counter = counter

    def __getattr__(self, name: str) -> Any:
        if name != self._method:
            return getattr(self._module, name)

        def invoke(*args: Any, **kwargs: Any) -> Any:
            result = getattr(self._module, name)(*args, **kwargs)
            status = getattr(getattr(result, "status", None), "value", "NO_STATUS")
            self._counter[str(status)] += 1
            return result

        return invoke


class ObservedDeadlineTracker:
    def __init__(self, tracker: Any, counter: Counter[str]) -> None:
        self._tracker = tracker
        self.profile = tracker.profile
        self._counter = counter

    def start(self) -> None:
        self._tracker.start()

    def observe(self, stage: str) -> Any:
        result = self._tracker.observe(stage)
        self._counter[result.status.value] += 1
        return result


class ObservedTokenStore:
    def __init__(self, store: Any) -> None:
        self._store = store
        self.activation_count = 0
        self.consume_count = 0
        self.invalid_existing_count = 0

    @property
    def terminal_authorized(self) -> bool:
        return self._store.terminal_authorized

    def current(self) -> Any:
        return self._store.current()

    def prepare(self, bundle: Any) -> Any:
        return self._store.prepare(bundle)

    def validate(self, snapshot: Any, registry: Any) -> Any:
        before = self._store.current()
        result = self._store.validate(snapshot, registry)
        if before is not None and result.status.value != "PASS":
            self.invalid_existing_count += 1
        return result

    def activate_after_navigation_commit(self, receipt: Any, bundle_identity: Any) -> Any:
        value = self._store.activate_after_navigation_commit(receipt, bundle_identity)
        self.activation_count += 1
        return value

    def consume_after_backup_commit(self, receipt: Any) -> Any:
        value = self._store.consume_after_backup_commit(receipt)
        self.consume_count += 1
        return value

    def abort_prepared(self, candidate_id: str) -> None:
        self._store.abort_prepared(candidate_id)

    def invalidate(self, reason: str) -> Any:
        return self._store.invalidate(reason)


def build_stack(checkout: Path, output_dir: Path, trial_id: int, config: dict[str, Any], map_identity: str):
    unified = checkout / "reproduction/cross_dataset/fas_cbf_unified_executable_safety_certifier_v1"
    sys.path[:0] = [str(unified), str(checkout)]

    from adapters.current_cbf_adapter import CurrentCBFAdapter
    from adapters.gaussian_barrier_adapter import SourceGaussianBarrierAdapter
    from adapters.normative_dynamics_adapter import PositionFirstForwardEulerDoubleIntegrator
    from cbf.cbf_utils import CBF
    from certifier.backup_certifier import BackupCertifier
    from certifier.braking_backup_policy import DeterministicBrakingPolicy
    from certifier.result_types import ActuatorBounds, BarrierStatus, Control, SegmentStatus, State
    from certifier.segment_backends.conservative_interval import ConservativeSignedDistanceIntervalBackend
    from certifier.segment_certificate import SweptSegmentCertifier
    from certifier.terminal_certificate import TerminalCertifier
    from certifier.terminal_set import BrakingToRestTerminalSet
    from dynamics.systems import DoubleIntegrator, double_integrator_dynamics
    from splat.gsplat_utils import GSplatLoader

    from reproduction.runtime.active_runtime_assurance_v2.active_cycle import ActiveCycleCoordinator
    from reproduction.runtime.active_runtime_assurance_v2.active_runner import ActiveRunner
    from reproduction.runtime.active_runtime_assurance_v2.alternative_provider import NativeExistingAlternativeProvider
    from reproduction.runtime.active_runtime_assurance_v2.authority_registry import AuthorityRegistry
    from reproduction.runtime.active_runtime_assurance_v2.backup_token_store import BackupTokenStore
    from reproduction.runtime.active_runtime_assurance_v2.c0_admission import C0Admission
    from reproduction.runtime.active_runtime_assurance_v2.deadline_runtime import DeadlineTracker, RuntimeDeadlineProfile
    from reproduction.runtime.active_runtime_assurance_v2.diagnostic_r0 import DiagnosticR0
    from reproduction.runtime.active_runtime_assurance_v2.l1_runtime import L1Runtime
    from reproduction.runtime.active_runtime_assurance_v2.l2_runtime import L2Runtime
    from reproduction.runtime.active_runtime_assurance_v2.l3_runtime import L3Runtime
    from reproduction.runtime.active_runtime_assurance_v2.plant_commit import PlantCommitAdapter
    from reproduction.runtime.active_runtime_assurance_v2.primary_proposal_adapter import PrimaryProposalAdapter
    from reproduction.runtime.active_runtime_assurance_v2.runtime_types import CertificateStatus, EvidenceResult, RuntimeMode, canonical_sha256
    from reproduction.runtime.active_runtime_assurance_v2.start_admission import StartAdmission
    from reproduction.runtime.active_runtime_assurance_v2.supervisor import Supervisor, TransitionTable
    from reproduction.runtime.active_runtime_assurance_v2.terminal_runtime import TerminalRuntime
    from reproduction.runtime.active_runtime_assurance_v2.trace_writer import TraceWriter

    device = torch.device("cuda:0")
    map_root = (checkout / config["map_relative_path"]).resolve(strict=True)
    loader = GSplatLoader(map_root / "config.yml", device)
    controller_cfg = config["controller"]
    cert_cfg = config["certification"]
    dynamics_cfg = config["dynamics"]
    deadline_cfg = config["deadline_profile"]
    dt = float(dynamics_cfg["dt"])
    effective_radius = float(cert_cfg["certification_effective_radius"])

    def query_bridge(point: Any, **kwargs: Any):
        if not torch.is_tensor(point):
            point = torch.as_tensor(point, device=device, dtype=torch.float32)
        return loader.query_distance(point, **kwargs)

    map_adapter = SourceGaussianBarrierAdapter(query_bridge, map_identity, effective_radius, int(loader.means.shape[0]))
    segment_backend = ConservativeSignedDistanceIntervalBackend(map_adapter)

    def evidence(status: Any, reason: str, payload: Any) -> Any:
        return EvidenceResult(status, reason, "evidence:sha256:" + canonical_sha256(payload))

    def full_query(position: tuple[float, float, float], expected_map: str, radius: float):
        if radius != effective_radius:
            return evidence(CertificateStatus.UNKNOWN, "GEOMETRY_IDENTITY_MISMATCH", {"radius": radius})
        result = map_adapter.query(np.asarray(position, dtype=np.float64), expected_map, "FULL")
        if result.status != BarrierStatus.FINITE or result.h is None or not math.isfinite(float(result.h)):
            return evidence(CertificateStatus.UNKNOWN, result.reason_code, result.to_dict())
        status = CertificateStatus.PASS if float(result.h) >= 0.0 else CertificateStatus.FAIL
        return evidence(status, "CURRENT_FULL_QUERY_" + status.value, result.to_dict())

    def segment_query(start: Any, end: Any, expected_map: str, radius: float, rho: float):
        result = segment_backend.certify(np.asarray(start), np.asarray(end), map_identity, expected_map, radius, rho)
        if result.status == SegmentStatus.CERTIFIED_SAFE:
            status = CertificateStatus.PASS
        elif result.status == SegmentStatus.CERTIFIED_UNSAFE:
            status = CertificateStatus.FAIL
        else:
            status = CertificateStatus.UNKNOWN
        return evidence(status, result.reason_code, result.to_dict())

    profile = RuntimeDeadlineProfile.create(
        deadline_cfg["cycle_deadline_duration"],
        tuple((str(name), float(value)) for name, value in deadline_cfg["stage_budgets"]),
        deadline_cfg["warning_reserve"],
        deadline_cfg["latest_safe_commit"],
        deadline_cfg["clock_identity"],
    )
    registry = AuthorityRegistry.frozen(map_identity, "RUN_PY_DT_0P05", profile.identity)
    bounds = ActuatorBounds((-0.1,) * 3, (0.1,) * 3, (-0.1,) * 3, (0.1,) * 3, dt)
    normative_dynamics = PositionFirstForwardEulerDoubleIntegrator(bounds)
    source_cbf = CBF(loader, DoubleIntegrator(device=device, ndim=3), controller_cfg["alpha"], controller_cfg["beta"], controller_cfg["controller_radius"], distance_type=controller_cfg["distance_method"])

    def proposal_solver(snapshot: Any, desired: tuple[float, float, float]):
        x = torch.tensor(snapshot.state, device=device, dtype=torch.float32)
        u_des = torch.tensor(desired, device=device, dtype=torch.float32)
        torch.cuda.synchronize()
        output = source_cbf.solve_QP(x, u_des)
        torch.cuda.synchronize()
        success = bool(source_cbf.solver_success)
        values = None if not success else tuple(float(item) for item in output.detach().cpu().tolist())
        return success, values, "CURRENT_PRIMARY_CBF_QP_SOLVED" if success else "CURRENT_PRIMARY_CBF_QP_FAILED"

    current_adapter = CurrentCBFAdapter(map_adapter)
    swept = SweptSegmentCertifier(normative_dynamics, segment_backend, effective_radius, cert_cfg["rho_seg"])
    terminal_set = BrakingToRestTerminalSet(cert_cfg["terminal_velocity_tolerance"])
    terminal_certifier = TerminalCertifier(terminal_set, current_adapter, swept)
    braking = DeterministicBrakingPolicy(bounds, cert_cfg["terminal_velocity_tolerance"])
    backup_certifier = BackupCertifier(normative_dynamics, swept, terminal_certifier, braking)

    def to_certifier_state(snapshot: Any) -> Any:
        return State(tuple(snapshot.position), tuple(snapshot.velocity), snapshot.cycle_index * snapshot.dt, snapshot.map_identity)

    def l3_witness(snapshot: Any, candidate: Any):
        state = to_certifier_state(snapshot)
        control = Control(tuple(candidate.vector), candidate.provenance.source_type, candidate.identity.value)
        witness = backup_certifier.certify(state, control, snapshot.map_identity, None)
        if not witness.certified:
            return CertificateStatus.FAIL, (), None, witness.reason_code
        tail = tuple((item.acceleration, f"{candidate.identity.value}:backup:{index}:{item.candidate_id}") for index, item in enumerate(witness.backup_controls))
        terminal_ref = "terminal-evidence:sha256:" + canonical_sha256(witness.terminal_certificate.to_dict())
        return CertificateStatus.PASS, tail, terminal_ref, witness.reason_code

    def terminal_membership(snapshot: Any) -> bool:
        return terminal_set.velocity_is_terminal(to_certifier_state(snapshot))

    def terminal_backend(snapshot: Any, expected_map: str, radius: float):
        if radius != effective_radius or expected_map != map_identity:
            return evidence(CertificateStatus.UNKNOWN, "TERMINAL_AUTHORITY_MISMATCH", {"map": expected_map, "radius": radius})
        certificate = terminal_certifier.certify(to_certifier_state(snapshot), expected_map)
        status = CertificateStatus.PASS if certificate.certified else CertificateStatus.FAIL
        return evidence(status, certificate.reason_code, certificate.to_dict())

    def plant_transition(state: tuple[float, ...], control: tuple[float, ...], dt_value: float):
        x = torch.tensor(state, device=device, dtype=torch.float32)
        u = torch.tensor(control, device=device, dtype=torch.float32)
        post = x + double_integrator_dynamics(x, u) * float(dt_value)
        return tuple(float(item) for item in post.detach().cpu().tolist())

    counters = {name: Counter() for name in ("L1", "C0", "L2", "L3", "TERMINAL", "DEADLINE")}
    start = StartAdmission(full_query, registry)
    l1 = CountedModule(L1Runtime(segment_query, registry), "evaluate_cycle", counters["L1"])
    c0 = CountedModule(C0Admission(registry), "evaluate", counters["C0"])
    l2 = CountedModule(L2Runtime(segment_query, registry), "evaluate", counters["L2"])
    l3 = CountedModule(L3Runtime(l3_witness, registry), "evaluate", counters["L3"])
    terminal = CountedModule(TerminalRuntime(terminal_membership, terminal_backend, registry), "evaluate", counters["TERMINAL"])
    deadline = ObservedDeadlineTracker(DeadlineTracker(profile), counters["DEADLINE"])
    supervisor = Supervisor(registry, TransitionTable.from_csv(checkout / "reproduction/specification/method_logic_closure_v2/STATE_TRANSITION_TABLE_V2.csv"))
    token_store = ObservedTokenStore(BackupTokenStore())
    trace_writer = TraceWriter(f"STONEHENGE_TRIAL_{trial_id:03d}", output_dir / "raw" / f"trial_{trial_id}")
    plant = PlantCommitAdapter(registry, plant_transition)
    runner = ActiveRunner(RuntimeMode.ACTIVE_RUNTIME_ON, registry, supervisor, plant, token_store, trace_writer, profile)
    coordinator = ActiveCycleCoordinator(
        registry,
        start,
        DiagnosticR0(),
        l1,
        PrimaryProposalAdapter(
            proposal_solver,
            "CURRENT_PRIMARY_CBF_QP",
            actuator_bounds=(registry.actuator.u_min, registry.actuator.u_max),
            source_scalar_contract="IEEE754_BINARY32",
        ),
        c0,
        l2,
        l3,
        NativeExistingAlternativeProvider(),
        token_store,
        terminal,
        deadline,
        supervisor,
        runner,
    )
    return {
        "coordinator": coordinator,
        "profile": profile,
        "registry": registry,
        "plant": plant,
        "tokens": token_store,
        "trace": trace_writer,
        "counters": counters,
        "loader": loader,
    }


def blank_summary(trial_id: int) -> dict[str, Any]:
    return {
        "schema": "ACTIVE_RUNTIME_SMOKE_V2_TRIAL_SUMMARY",
        "trial_id": trial_id,
        "process_exit_code": 2,
        "startup_status": "NOT_RUN",
        "initial_state_identity": None,
        "goal_identity": None,
        "goal_value": None,
        "map_identity": None,
        "deadline_profile_identity": None,
        "completed_cycles": 0,
        "plant_commit_count": 0,
        "primary_navigation_commit_count": 0,
        "alternative_navigation_commit_count": 0,
        "retained_backup_commit_count": 0,
        "terminal_commit_count": 0,
        "assurance_boundary_count": 0,
        "selected_executed_identity_mismatch_count": 0,
        "action_bound_violation_count": 0,
        "nonfinite_count": 0,
        "deadline_status_counts": {"OPEN": 0, "WARNING": 0, "EXPIRED": 0},
        "L1_status_counts": {"PASS": 0, "FAIL": 0, "UNKNOWN": 0},
        "C0_status_counts": {"PASS": 0, "FAIL": 0, "UNKNOWN": 0},
        "L2_status_counts": {"PASS": 0, "FAIL": 0, "UNKNOWN": 0},
        "L3_status_counts": {"PASS": 0, "FAIL": 0, "UNKNOWN": 0},
        "token_activation_count": 0,
        "token_consume_count": 0,
        "evidence_incomplete_count": 0,
        "recovery_required_count": 0,
        "exception_count": 0,
        "trace_record_count": 0,
        "finalization_status": "NOT_RUN",
        "trace_lock_identity": None,
        "trace_lock_record_count": 0,
        "wall_time_total": 0.0,
        "cycle_time_median": None,
        "cycle_time_p95": None,
        "cycle_time_max": None,
        "termination_reason": "NOT_RUN",
        "hard_blocker": None,
        "gpu_released_after_process": None
    }


def percentile(values: list[float], fraction: float) -> float | None:
    if not values:
        return None
    ordered = sorted(values)
    index = min(len(ordered) - 1, max(0, math.ceil(fraction * len(ordered)) - 1))
    return float(ordered[index])


def run_one(checkout: Path, output_dir: Path, trial_id: int) -> int:
    summary = blank_summary(trial_id)
    started = time.perf_counter()
    stack = None
    cycle_times: list[float] = []
    hard_blocker = None
    try:
        if trial_id not in FIXED_TRIALS:
            raise ValueError("TRIAL_ID_NOT_FROZEN")
        if os.environ.get("CUDA_VISIBLE_DEVICES") != "1":
            raise RuntimeError("CUDA_VISIBLE_DEVICES_MUST_EQUAL_1")
        if not torch.cuda.is_available() or torch.cuda.device_count() != 1:
            raise RuntimeError("SINGLE_VISIBLE_GPU_REQUIRED")
        config = json.loads(CONFIG_PATH.read_text(encoding="utf-8"))
        map_identity, _ = verify_inputs(checkout, config)
        random.seed(config["seed"])
        np.random.seed(config["seed"])
        torch.manual_seed(config["seed"])
        torch.cuda.manual_seed_all(config["seed"])
        stack = build_stack(checkout, output_dir, trial_id, config, map_identity)
        from reproduction.runtime.active_runtime_assurance_v2.runtime_types import ActiveCycleRequest, ActiveTrialContext, EvidenceStatus, FinalizationStatus, RuntimeStateSnapshot

        start, goal_position = trial_geometry(trial_id)
        state = tuple(float(item) for item in np.concatenate((start.astype(np.float32), np.zeros(3, dtype=np.float32))))
        goal = tuple(float(item) for item in np.concatenate((goal_position.astype(np.float32), np.zeros(3, dtype=np.float32))))
        canonical_trial = f"STONEHENGE_TRIAL_{trial_id:03d}"
        snapshot = RuntimeStateSnapshot.create(canonical_trial, 0, state, goal, map_identity, config["dynamics"]["dt"])
        summary.update({
            "initial_state_identity": snapshot.identity.value,
            "goal_identity": "goal:sha256:" + semantic_sha256(goal),
            "goal_value": list(goal),
            "map_identity": map_identity,
            "deadline_profile_identity": stack["profile"].identity,
            "environment": {
                "python": platform.python_version(), "executable": sys.executable,
                "torch": torch.__version__, "torch_cuda": torch.version.cuda,
                "numpy": np.__version__, "cuda_visible_devices": os.environ.get("CUDA_VISIBLE_DEVICES"),
                "visible_device_count": torch.cuda.device_count(), "device_name": torch.cuda.get_device_name(0)
            }
        })
        start_result = stack["coordinator"].start_trial(snapshot, ActiveTrialContext(canonical_trial, map_identity))
        summary["startup_status"] = "PASS" if start_result.ready else start_result.status.value
        if not start_result.ready:
            hard_blocker = "BLOCKED_ACTIVE_RUNTIME_SMOKE_BY_STARTUP_ADMISSION:" + start_result.reason
        else:
            for cycle in range(config["maximum_completed_cycles_per_trial"]):
                pre_state = np.asarray(snapshot.state, dtype=np.float64)
                position = np.asarray(snapshot.position, dtype=np.float64)
                velocity = np.asarray(snapshot.velocity, dtype=np.float64)
                goal_position_now = np.asarray(snapshot.goal[:3], dtype=np.float64)
                desired_velocity = np.clip(5.0 * (goal_position_now - position), -0.1, 0.1)
                desired_velocity = desired_velocity - velocity
                desired = tuple(float(item) for item in np.clip(desired_velocity - velocity, -0.1, 0.1))
                before_plant = stack["plant"].commit_count
                before_trace = len(stack["trace"].records)
                t0 = time.perf_counter()
                result = stack["coordinator"].run_cycle(snapshot, ActiveCycleRequest(canonical_trial, cycle, desired, None))
                torch.cuda.synchronize()
                cycle_times.append(time.perf_counter() - t0)
                after_plant = stack["plant"].commit_count
                after_trace = len(stack["trace"].records)
                summary["completed_cycles"] += 1
                if after_trace != before_trace + 1:
                    hard_blocker = "BLOCKED_ACTIVE_RUNTIME_SMOKE_BY_TRACE_CARDINALITY"
                    break
                if after_plant - before_plant not in (0, 1):
                    hard_blocker = "BLOCKED_ACTIVE_RUNTIME_SMOKE_BY_DUPLICATE_PLANT_COMMIT"
                    break
                transaction = result.commit_transaction_result
                if transaction is None:
                    hard_blocker = "BLOCKED_ACTIVE_RUNTIME_SMOKE_BY_EVIDENCE_INCOMPLETE"
                    summary["evidence_incomplete_count"] += 1
                    break
                if transaction.evidence_status not in {EvidenceStatus.COMPLETE, EvidenceStatus.NO_ACTION_COMPLETE}:
                    summary["evidence_incomplete_count"] += int("INCOMPLETE" in transaction.evidence_status.value)
                    summary["recovery_required_count"] += int(bool(transaction.recovery_required))
                    hard_blocker = "BLOCKED_ACTIVE_RUNTIME_SMOKE_BY_EVIDENCE_FAILURE:" + transaction.evidence_status.value
                    break
                if any(item.status.value == "EXPIRED" for item in result.deadline_observations):
                    hard_blocker = "BLOCKED_ACTIVE_RUNTIME_SMOKE_BY_DEADLINE_EXPIRED"
                    break
                if result.committed:
                    receipt = result.commit_receipt
                    decision = result.final_supervisor_decision
                    if receipt is None or decision is None or decision.selected_action is None:
                        hard_blocker = "BLOCKED_ACTIVE_RUNTIME_SMOKE_BY_UNAUTHORIZED_PLANT"
                        break
                    if receipt.selected_action_identity != decision.selected_action.identity or receipt.executed_action_identity != decision.selected_action.identity:
                        summary["selected_executed_identity_mismatch_count"] += 1
                        hard_blocker = "BLOCKED_ACTIVE_RUNTIME_SMOKE_BY_SELECTED_EXECUTED_IDENTITY"
                        break
                    if any(not math.isfinite(float(v)) for v in (*receipt.exact_vector, *receipt.post_state.state)):
                        summary["nonfinite_count"] += 1
                        hard_blocker = "BLOCKED_ACTIVE_RUNTIME_SMOKE_BY_NONFINITE"
                        break
                    if any(v < -0.1 or v > 0.1 for v in receipt.exact_vector):
                        summary["action_bound_violation_count"] += 1
                        hard_blocker = "BLOCKED_ACTIVE_RUNTIME_SMOKE_BY_ACTION_BOUNDS"
                        break
                    summary[receipt.action_role.value.lower() + "_count"] = summary.get(receipt.action_role.value.lower() + "_count", 0) + 1
                    role_key = {
                        "PRIMARY_NAVIGATION": "primary_navigation_commit_count",
                        "ALTERNATIVE_NAVIGATION": "alternative_navigation_commit_count",
                        "RETAINED_BACKUP": "retained_backup_commit_count",
                        "CERTIFIED_TERMINAL": "terminal_commit_count",
                    }[receipt.action_role.value]
                    summary[role_key] += 1
                    snapshot = receipt.post_state
                else:
                    if after_plant != before_plant:
                        hard_blocker = "BLOCKED_ACTIVE_RUNTIME_SMOKE_BY_UNAUTHORIZED_PLANT"
                        break
                    summary["assurance_boundary_count"] += int(result.boundary)
                if result.boundary:
                    summary["termination_reason"] = "ASSURANCE_BOUNDARY"
                    break
                if result.next_state is None:
                    hard_blocker = "BLOCKED_ACTIVE_RUNTIME_SMOKE_BY_MISSING_NEXT_STATE"
                    break
                if np.linalg.norm(np.asarray(snapshot.state, dtype=np.float64) - pre_state) < 0.001:
                    summary["termination_reason"] = "NATIVE_NOT_MOVING"
                    break
                if cycle == config["maximum_completed_cycles_per_trial"] - 1:
                    summary["termination_reason"] = "MAX_COMPLETED_CYCLES"
            if summary["termination_reason"] == "NOT_RUN" and hard_blocker is None:
                summary["termination_reason"] = "MAX_COMPLETED_CYCLES"
        finalization = stack["coordinator"].finalize_trial()
        summary["finalization_status"] = finalization.status.value
        if finalization.trace_lock is not None:
            summary["trace_lock_identity"] = finalization.trace_lock.identity.value
            summary["trace_lock_record_count"] = finalization.trace_lock.record_count
        summary["trace_record_count"] = len(stack["trace"].records)
        summary["token_activation_count"] = stack["tokens"].activation_count
        summary["token_consume_count"] = stack["tokens"].consume_count
        summary["plant_commit_count"] = stack["plant"].commit_count
        for stage in ("L1", "C0", "L2", "L3"):
            summary[stage + "_status_counts"] = {name: int(stack["counters"][stage][name]) for name in ("PASS", "FAIL", "UNKNOWN")}
        summary["deadline_status_counts"] = {name: int(stack["counters"]["DEADLINE"][name]) for name in ("OPEN", "WARNING", "EXPIRED")}

        committed_role_count = sum(
            summary[key]
            for key in (
                "primary_navigation_commit_count",
                "alternative_navigation_commit_count",
                "retained_backup_commit_count",
                "terminal_commit_count",
            )
        )
        if summary["plant_commit_count"] != stack["plant"].commit_count:
            hard_blocker = hard_blocker or "BLOCKED_ACTIVE_RUNTIME_SMOKE_BY_PLANT_COUNT_CONSISTENCY"
        if summary["trace_record_count"] != len(stack["trace"].records):
            hard_blocker = hard_blocker or "BLOCKED_ACTIVE_RUNTIME_SMOKE_BY_TRACE_COUNT_CONSISTENCY"
        if summary["trace_lock_record_count"] != summary["trace_record_count"]:
            hard_blocker = hard_blocker or "BLOCKED_ACTIVE_RUNTIME_SMOKE_BY_TRACE_CARDINALITY"
        if committed_role_count != summary["plant_commit_count"]:
            hard_blocker = hard_blocker or "BLOCKED_ACTIVE_RUNTIME_SMOKE_BY_COMMIT_ROLE_CARDINALITY"
        if finalization.status != FinalizationStatus.FINALIZED:
            summary["recovery_required_count"] += int(finalization.recovery_required)
            hard_blocker = hard_blocker or "BLOCKED_ACTIVE_RUNTIME_SMOKE_BY_FINALIZATION"
        if summary["trace_record_count"] != summary["completed_cycles"]:
            hard_blocker = hard_blocker or "BLOCKED_ACTIVE_RUNTIME_SMOKE_BY_TRACE_CARDINALITY"
        if summary["plant_commit_count"] == 0:
            hard_blocker = hard_blocker or "INCONCLUSIVE_NO_ACTIVE_COMMIT"
        if stack["tokens"].invalid_existing_count and summary["retained_backup_commit_count"]:
            hard_blocker = hard_blocker or "BLOCKED_ACTIVE_RUNTIME_SMOKE_BY_STALE_BACKUP_REUSE"
    except Exception as exc:
        summary["exception_count"] += 1
        hard_blocker = hard_blocker or f"BLOCKED_ACTIVE_RUNTIME_SMOKE_BY_RUNTIME_EXCEPTION:{type(exc).__name__}:{exc}"
        if stack is not None:
            summary["plant_commit_count"] = stack["plant"].commit_count
            summary["trace_record_count"] = len(stack["trace"].records)
    finally:
        summary["hard_blocker"] = hard_blocker
        summary["process_exit_code"] = 0 if hard_blocker is None else 2
        summary["wall_time_total"] = time.perf_counter() - started
        summary["cycle_time_median"] = None if not cycle_times else statistics.median(cycle_times)
        summary["cycle_time_p95"] = percentile(cycle_times, 0.95)
        summary["cycle_time_max"] = None if not cycle_times else max(cycle_times)
        write_json(output_dir / f"trial_{trial_id}_summary.json", summary)
        if stack is not None:
            del stack
        torch.cuda.empty_cache()
    print(json.dumps({"trial_id": trial_id, "exit_code": summary["process_exit_code"], "blocker": hard_blocker}, sort_keys=True), flush=True)
    return int(summary["process_exit_code"])


def gpu_one_is_clean() -> bool:
    result = subprocess.run(
        ["nvidia-smi", "--query-compute-apps=gpu_uuid,pid,process_name", "--format=csv,noheader,nounits"],
        text=True, capture_output=True, check=False,
    )
    target = "GPU-78ef17e4-66cc-4a58-fe43-67d31be8981d"
    return all(target not in line for line in result.stdout.splitlines())


def run_batch(checkout: Path, output_dir: Path) -> int:
    config = json.loads(CONFIG_PATH.read_text(encoding="utf-8"))
    verify_inputs(checkout, config)
    overall = 0
    for index, trial_id in enumerate(FIXED_TRIALS):
        if overall:
            for remaining in FIXED_TRIALS[index:]:
                summary = blank_summary(remaining)
                summary["termination_reason"] = "NOT_RUN_AFTER_PRIOR_HARD_BLOCK"
                summary["hard_blocker"] = "PRIOR_TRIAL_HARD_BLOCK"
                write_json(output_dir / f"trial_{remaining}_summary.json", summary)
            break
        env = os.environ.copy()
        env.update(config["environment"])
        result = subprocess.run([sys.executable, str(Path(__file__).resolve()), "--one", str(trial_id), "--checkout", str(checkout), "--output-dir", str(output_dir)], env=env)
        summary_path = output_dir / f"trial_{trial_id}_summary.json"
        if summary_path.exists():
            summary = json.loads(summary_path.read_text(encoding="utf-8"))
            summary["process_exit_code"] = result.returncode
            summary["gpu_released_after_process"] = gpu_one_is_clean()
            if not summary["gpu_released_after_process"]:
                summary["hard_blocker"] = summary.get("hard_blocker") or "BLOCKED_ACTIVE_RUNTIME_SMOKE_BY_GPU_RELEASE"
                result = subprocess.CompletedProcess(result.args, 2)
            write_json(summary_path, summary)
        overall = result.returncode
    return overall


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--checkout", type=Path, required=True)
    parser.add_argument("--output-dir", type=Path, required=True)
    parser.add_argument("--one", type=int)
    parser.add_argument("--all", action="store_true")
    args = parser.parse_args()
    checkout = args.checkout.resolve(strict=True)
    output_dir = args.output_dir.resolve()
    output_dir.mkdir(parents=True, exist_ok=True)
    if (args.one is None) == (not args.all):
        raise SystemExit("choose exactly one of --one or --all")
    return run_batch(checkout, output_dir) if args.all else run_one(checkout, output_dir, int(args.one))


if __name__ == "__main__":
    raise SystemExit(main())
