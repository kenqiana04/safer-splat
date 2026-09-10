#!/usr/bin/env python3
"""Run the frozen paired Active Runtime Pilot V2.

The program is task-local orchestration.  It does not modify runtime or
production code, and its evaluation oracle is invoked only after immutable
execution evidence has been written.
"""

from __future__ import annotations

import argparse
from collections import Counter
import csv
import dataclasses
import hashlib
import importlib.util
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
from typing import Any

import numpy as np


TASK_DIR = Path(__file__).resolve().parent
CONFIG_PATH = TASK_DIR / "PILOT_CONFIG.json"
EXPECTED_SOURCE_HEAD = "8ba397bee31d4c42deebc52104c6409336a96fd9"
EXPECTED_RUNTIME_TREE = "c60be4c1977932c53b37e500e96c5ddf7cd2d820"
FIXED_TRIALS = (5, 15, 25, 35, 45, 55, 65, 75, 85, 95)
FIXED_ARMS = ("REFERENCE_CBF_QP", "ACTIVE_RUNTIME_V2")
GPU_ONE_UUID = "GPU-78ef17e4-66cc-4a58-fe43-67d31be8981d"


def normalize(value: Any) -> Any:
    if dataclasses.is_dataclass(value):
        return normalize(dataclasses.asdict(value))
    if isinstance(value, dict):
        return {str(k): normalize(v) for k, v in value.items()}
    if isinstance(value, (tuple, list)):
        return [normalize(v) for v in value]
    if hasattr(value, "value"):
        return normalize(value.value)
    if isinstance(value, np.generic):
        return value.item()
    return value


def write_json(path: Path, value: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    tmp = path.with_suffix(path.suffix + ".tmp")
    tmp.write_text(json.dumps(normalize(value), indent=2, sort_keys=True, allow_nan=False) + "\n", encoding="utf-8", newline="\n")
    tmp.replace(path)


def write_jsonl(path: Path, rows: list[dict[str, Any]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    tmp = path.with_suffix(path.suffix + ".tmp")
    with tmp.open("w", encoding="utf-8", newline="\n") as handle:
        for row in rows:
            handle.write(json.dumps(normalize(row), sort_keys=True, allow_nan=False) + "\n")
        handle.flush()
        os.fsync(handle.fileno())
    tmp.replace(path)


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def semantic_sha256(value: Any) -> str:
    payload = json.dumps(normalize(value), sort_keys=True, separators=(",", ":"), allow_nan=False).encode()
    return hashlib.sha256(payload).hexdigest()


def git_output(checkout: Path, *args: str) -> str:
    return subprocess.run(["git", "-C", str(checkout), *args], check=True, text=True, capture_output=True).stdout.strip()


def percentile(values: list[float], fraction: float) -> float | None:
    if not values:
        return None
    ordered = sorted(values)
    index = min(len(ordered) - 1, max(0, math.ceil(fraction * len(ordered)) - 1))
    return float(ordered[index])


def trial_geometry(trial_id: int) -> tuple[np.ndarray, np.ndarray]:
    t = np.linspace(0, 2 * np.pi, 100)
    t_z = 10 * np.linspace(0, 2 * np.pi, 100)
    radius = 0.784 / 2
    center = np.array([-0.08, -0.03, 0.05])
    starts = np.stack([radius * np.cos(t), radius * np.sin(t), 0.01 * np.sin(t_z)], axis=-1) + center
    goals = np.stack([radius * np.cos(t + np.pi), radius * np.sin(t + np.pi), 0.01 * np.sin(t_z + np.pi)], axis=-1) + center
    return starts[trial_id], goals[trial_id]


def desired_control(state: tuple[float, ...], goal: tuple[float, ...]) -> tuple[float, float, float]:
    position = np.asarray(state[:3], dtype=np.float64)
    velocity = np.asarray(state[3:], dtype=np.float64)
    goal_position = np.asarray(goal[:3], dtype=np.float64)
    desired_velocity = np.clip(5.0 * (goal_position - position), -0.1, 0.1)
    desired_velocity = desired_velocity - velocity
    return tuple(float(x) for x in np.clip(desired_velocity - velocity, -0.1, 0.1))


def verify_inputs(checkout: Path, config: dict[str, Any]) -> tuple[str, list[dict[str, Any]]]:
    if git_output(checkout, "rev-parse", "HEAD") != EXPECTED_SOURCE_HEAD:
        raise RuntimeError("RUNTIME_SOURCE_DRIFT")
    if git_output(checkout, "rev-parse", "HEAD:reproduction/runtime/active_runtime_assurance_v2") != EXPECTED_RUNTIME_TREE:
        raise RuntimeError("RUNTIME_TREE_IDENTITY_MISMATCH")
    if git_output(checkout, "diff", "--name-only", EXPECTED_SOURCE_HEAD, "--", "reproduction/runtime/active_runtime_assurance_v2"):
        raise RuntimeError("RUNTIME_SOURCE_DIFF_NONZERO")
    map_root = (checkout / config["map_relative_path"]).resolve(strict=True)
    actual = []
    for expected in config["map_artifacts"]:
        path = map_root / expected["relative_path"]
        row = {"relative_path": expected["relative_path"], "size": path.stat().st_size, "sha256": sha256_file(path)}
        if row != expected:
            raise RuntimeError("MAP_ARTIFACT_IDENTITY_MISMATCH:" + expected["relative_path"])
        actual.append(row)
    identity = semantic_sha256({"scene": "stonehenge", "artifacts": actual})
    if identity != config["map_identity"]:
        raise RuntimeError("MAP_SEMANTIC_IDENTITY_MISMATCH")
    return identity, actual


def load_smoke_helper(checkout: Path) -> Any:
    path = checkout / "reproduction/smoke/active_runtime_smoke_v2/run_active_runtime_smoke_v2.py"
    spec = importlib.util.spec_from_file_location("frozen_active_smoke_helper", path)
    if spec is None or spec.loader is None:
        raise RuntimeError("SMOKE_HELPER_IMPORT_FAILED")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def make_source_stack(checkout: Path, config: dict[str, Any]):
    unified = checkout / "reproduction/cross_dataset/fas_cbf_unified_executable_safety_certifier_v1"
    sys.path[:0] = [str(unified), str(checkout)]
    import torch
    from cbf.cbf_utils import CBF
    from dynamics.systems import DoubleIntegrator, double_integrator_dynamics
    from splat.gsplat_utils import GSplatLoader

    device = torch.device("cuda:0")
    map_root = (checkout / config["map_relative_path"]).resolve(strict=True)
    loader = GSplatLoader(map_root / "config.yml", device)
    ccfg = config["controller"]
    source_cbf = CBF(loader, DoubleIntegrator(device=device, ndim=3), ccfg["alpha"], ccfg["beta"], ccfg["controller_radius"], distance_type=ccfg["distance_method"])

    def solve(state: tuple[float, ...], desired: tuple[float, ...]) -> tuple[bool, tuple[float, ...] | None, str]:
        x = torch.tensor(state, device=device, dtype=torch.float32)
        u_des = torch.tensor(desired, device=device, dtype=torch.float32)
        torch.cuda.synchronize()
        output = source_cbf.solve_QP(x, u_des)
        torch.cuda.synchronize()
        if not bool(source_cbf.solver_success):
            return False, None, "CURRENT_PRIMARY_CBF_QP_FAILED"
        return True, tuple(float(v) for v in output.detach().cpu().tolist()), "CURRENT_PRIMARY_CBF_QP_SOLVED"

    def transition(state: tuple[float, ...], control: tuple[float, ...], dt: float) -> tuple[float, ...]:
        x = torch.tensor(state, device=device, dtype=torch.float32)
        u = torch.tensor(control, device=device, dtype=torch.float32)
        post = x + double_integrator_dynamics(x, u) * float(dt)
        return tuple(float(v) for v in post.detach().cpu().tolist())

    return loader, solve, transition


def inverse_barrier_clearance(lower_bound: float, radius: float) -> float:
    raw = float(lower_bound) + float(radius) ** 2
    signed_distance = math.copysign(math.sqrt(abs(raw)), raw)
    return signed_distance - float(radius)


def evaluate_oracle(checkout: Path, loader: Any, states: list[tuple[float, ...]], goal: tuple[float, ...], config: dict[str, Any], map_identity: str) -> dict[str, Any]:
    from adapters.gaussian_barrier_adapter import SourceGaussianBarrierAdapter
    from certifier.result_types import SegmentStatus
    from certifier.segment_backends.conservative_interval import ConservativeSignedDistanceIntervalBackend
    import torch

    oracle = config["oracle"]
    if oracle["feedback"] or not oracle["posthoc_only"]:
        raise RuntimeError("ORACLE_AUTHORITY_VIOLATION")
    positions = [np.asarray(state[:3], dtype=np.float64) for state in states]

    def metrics_for_radius(radius: float) -> dict[str, Any]:
        def query(point: Any, **kwargs: Any):
            if not torch.is_tensor(point):
                point = torch.as_tensor(point, device=torch.device("cuda:0"), dtype=torch.float32)
            return loader.query_distance(point, **kwargs)

        provider = SourceGaussianBarrierAdapter(query, map_identity, radius, int(loader.means.shape[0]))
        backend = ConservativeSignedDistanceIntervalBackend(provider)
        violations = 0
        unknown = 0
        clearances: list[float] = []
        statuses: Counter[str] = Counter()
        first_violation = None
        for index, (start, end) in enumerate(zip(positions[:-1], positions[1:])):
            cert = backend.certify(start, end, map_identity, map_identity, radius, float(oracle["rho_seg"]))
            statuses[cert.status.value] += 1
            if cert.lower_bound is not None and math.isfinite(float(cert.lower_bound)):
                clearances.append(inverse_barrier_clearance(float(cert.lower_bound), radius))
            if cert.status == SegmentStatus.CERTIFIED_UNSAFE:
                violations += 1
                if first_violation is None:
                    first_violation = index
            elif cert.status != SegmentStatus.CERTIFIED_SAFE:
                unknown += 1
        return {
            "radius_m": radius,
            "segment_count": max(0, len(states) - 1),
            "violation_segment_count": violations,
            "violation_trial": violations > 0,
            "unknown_segment_count": unknown,
            "first_violation_cycle": first_violation,
            "min_clearance_m": min(clearances) if clearances else None,
            "status_counts": dict(statuses),
            "clearance_semantics": "CONSERVATIVE_SIGNED_DISTANCE_LOWER_BOUND_MINUS_EFFECTIVE_RADIUS"
        }

    collision = metrics_for_radius(float(oracle["collision_radius_m"]))
    margin = metrics_for_radius(float(oracle["certification_margin_radius_m"]))
    initial_distance = float(np.linalg.norm(positions[0] - np.asarray(goal[:3], dtype=np.float64)))
    final_distance = float(np.linalg.norm(positions[-1] - np.asarray(goal[:3], dtype=np.float64)))
    progress = None if initial_distance == 0 else (initial_distance - final_distance) / initial_distance
    goal_reached = any(float(np.linalg.norm(np.asarray(state, dtype=np.float64) - np.asarray(goal, dtype=np.float64))) < float(oracle["goal_l2_tolerance"]) for state in states)
    return {
        "schema": "ACTIVE_RUNTIME_PILOT_V2_POSTHOC_ORACLE",
        "feedback": False,
        "evaluated_after_execution_evidence_lock": True,
        "represented_map_collision_proxy": collision,
        "certification_margin_violation": margin,
        "goal_reached": goal_reached,
        "goal_l2_tolerance": oracle["goal_l2_tolerance"],
        "normalized_progress": progress,
        "progress_clipping": "NONE",
        "initial_goal_distance_m": initial_distance,
        "final_goal_distance_m": final_distance,
        "evaluation_eligible": collision["unknown_segment_count"] == 0 and margin["unknown_segment_count"] == 0
    }


def blank_summary(trial_id: int, arm: str) -> dict[str, Any]:
    return {
        "schema": "ACTIVE_RUNTIME_PILOT_V2_ARM_SUMMARY",
        "trial_id": trial_id,
        "arm": arm,
        "process_exit_code": 2,
        "execution_complete": False,
        "evaluation_eligible": False,
        "steps_executed": 0,
        "typed_termination": "NOT_RUN",
        "baseline_solver_failure_count": 0,
        "primary_proposal_qp_failure_count": 0,
        "plant_commit_count": 0,
        "primary_navigation_commit_count": 0,
        "alternative_navigation_commit_count": 0,
        "retained_backup_commit_count": 0,
        "terminal_commit_count": 0,
        "assurance_boundary_count": 0,
        "L1_status_counts": {"PASS": 0, "FAIL": 0, "UNKNOWN": 0},
        "C0_status_counts": {"PASS": 0, "FAIL": 0, "UNKNOWN": 0},
        "L2_status_counts": {"PASS": 0, "FAIL": 0, "UNKNOWN": 0},
        "L3_status_counts": {"PASS": 0, "FAIL": 0, "UNKNOWN": 0},
        "deadline_status_counts": {"OPEN": 0, "WARNING": 0, "EXPIRED": 0},
        "token_activation_count": 0,
        "token_consume_count": 0,
        "evidence_incomplete_count": 0,
        "recovery_required_count": 0,
        "runtime_exception_count": 0,
        "integrity_failure_count": 0,
        "active_constraint_count": "NOT_INSTRUMENTED",
        "compute_time_median_s": None,
        "compute_time_p95_s": None,
        "compute_time_max_s": None,
        "episode_wall_time_s": None,
        "oracle": None,
        "raw_evidence_lock": None,
        "hard_blocker": None,
        "gpu_released_after_process": None
    }


def persist_raw(arm_dir: Path, state_rows: list[dict[str, Any]], action_rows: list[dict[str, Any]], timing_rows: list[dict[str, Any]], termination: str) -> dict[str, Any]:
    state_path = arm_dir / "trajectory_states.jsonl"
    action_path = arm_dir / "executed_actions.jsonl"
    timing_path = arm_dir / "step_timing.jsonl"
    write_jsonl(state_path, state_rows)
    write_jsonl(action_path, action_rows)
    write_jsonl(timing_path, timing_rows)
    write_json(arm_dir / "termination.json", {"typed_termination": termination, "steps_executed": len(action_rows)})
    files = []
    for path in (state_path, action_path, timing_path, arm_dir / "termination.json"):
        files.append({"name": path.name, "size": path.stat().st_size, "sha256": sha256_file(path)})
    lock = {"schema": "ACTIVE_RUNTIME_PILOT_V2_RAW_EVIDENCE_LOCK", "files": files, "state_count": len(state_rows), "action_count": len(action_rows), "timing_count": len(timing_rows)}
    lock["identity"] = "pilot-raw:sha256:" + semantic_sha256(lock)
    write_json(arm_dir / "raw_evidence_lock.json", lock)
    return lock


def run_reference(checkout: Path, output_dir: Path, trial_id: int, config: dict[str, Any], map_identity: str) -> int:
    import torch
    arm = "REFERENCE_CBF_QP"
    arm_dir = output_dir / "raw" / f"trial_{trial_id:03d}" / arm.lower()
    summary = blank_summary(trial_id, arm)
    started = time.perf_counter()
    loader = None
    states: list[tuple[float, ...]] = []
    state_rows: list[dict[str, Any]] = []
    action_rows: list[dict[str, Any]] = []
    timing_rows: list[dict[str, Any]] = []
    try:
        loader, solve, transition = make_source_stack(checkout, config)
        start, goal_position = trial_geometry(trial_id)
        state = tuple(float(v) for v in np.concatenate((start.astype(np.float32), np.zeros(3, dtype=np.float32))))
        goal = tuple(float(v) for v in np.concatenate((goal_position.astype(np.float32), np.zeros(3, dtype=np.float32))))
        states.append(state)
        state_rows.append({"sequence": 0, "state": state, "state_hash": semantic_sha256(state)})
        termination = "MAX_STEPS_TIMEOUT"
        compute: list[float] = []
        for step in range(int(config["max_steps"])):
            desired = desired_control(state, goal)
            t0 = time.perf_counter()
            success, action, reason = solve(state, desired)
            if success and action is not None:
                post = transition(state, action, float(config["dynamics"]["dt"]))
            torch.cuda.synchronize()
            elapsed = time.perf_counter() - t0
            timing_rows.append({"step": step, "compute_time_s": elapsed})
            compute.append(elapsed)
            if not success or action is None:
                summary["baseline_solver_failure_count"] += 1
                termination = "BASELINE_SOLVER_FAILURE"
                break
            if any(not math.isfinite(v) for v in (*action, *post)):
                raise RuntimeError("NONFINITE_REFERENCE_EXECUTION")
            action_rows.append({"step": step, "action": action, "action_hash": semantic_sha256(action), "source": reason})
            state = post
            states.append(state)
            state_rows.append({"sequence": step + 1, "state": state, "state_hash": semantic_sha256(state)})
            if np.linalg.norm(np.asarray(states[-1]) - np.asarray(states[-2])) < 0.001:
                termination = "NATIVE_NOT_MOVING"
                break
        summary["typed_termination"] = termination
        summary["steps_executed"] = len(action_rows)
        lock = persist_raw(arm_dir, state_rows, action_rows, timing_rows, termination)
        summary["raw_evidence_lock"] = lock["identity"]
        oracle = evaluate_oracle(checkout, loader, states, goal, config, map_identity)
        summary["oracle"] = oracle
        summary["evaluation_eligible"] = bool(oracle["evaluation_eligible"])
        summary["execution_complete"] = True
        summary["compute_time_median_s"] = statistics.median(compute) if compute else None
        summary["compute_time_p95_s"] = percentile(compute, 0.95)
        summary["compute_time_max_s"] = max(compute) if compute else None
        summary["environment"] = {"python": platform.python_version(), "torch": torch.__version__, "cuda": torch.version.cuda, "numpy": np.__version__}
    except Exception as exc:
        summary["runtime_exception_count"] += 1
        summary["integrity_failure_count"] += 1
        summary["hard_blocker"] = f"BLOCKED_ACTIVE_RUNTIME_PILOT_BY_REFERENCE_EXCEPTION:{type(exc).__name__}:{exc}"
    finally:
        summary["episode_wall_time_s"] = time.perf_counter() - started
        summary["process_exit_code"] = 0 if summary["hard_blocker"] is None else 2
        write_json(arm_dir / "summary.json", summary)
        if loader is not None:
            del loader
        torch.cuda.empty_cache()
    return int(summary["process_exit_code"])


def run_active(checkout: Path, output_dir: Path, trial_id: int, config: dict[str, Any], map_identity: str) -> int:
    import torch
    from reproduction.runtime.active_runtime_assurance_v2.runtime_types import ActiveCycleRequest, ActiveTrialContext, EvidenceStatus, FinalizationStatus, PublicCyclePhase, RuntimeStateSnapshot
    arm = "ACTIVE_RUNTIME_V2"
    arm_dir = output_dir / "raw" / f"trial_{trial_id:03d}" / arm.lower()
    summary = blank_summary(trial_id, arm)
    started = time.perf_counter()
    stack = None
    states: list[tuple[float, ...]] = []
    state_rows: list[dict[str, Any]] = []
    action_rows: list[dict[str, Any]] = []
    timing_rows: list[dict[str, Any]] = []
    hard = None
    try:
        helper = load_smoke_helper(checkout)
        stack = helper.build_stack(checkout, arm_dir, trial_id, config, map_identity)
        start, goal_position = trial_geometry(trial_id)
        state = tuple(float(v) for v in np.concatenate((start.astype(np.float32), np.zeros(3, dtype=np.float32))))
        goal = tuple(float(v) for v in np.concatenate((goal_position.astype(np.float32), np.zeros(3, dtype=np.float32))))
        canonical_trial = f"STONEHENGE_TRIAL_{trial_id:03d}"
        snapshot = RuntimeStateSnapshot.create(canonical_trial, 0, state, goal, map_identity, config["dynamics"]["dt"])
        states.append(state)
        state_rows.append({"sequence": 0, "state": state, "state_hash": semantic_sha256(state), "runtime_state_identity": snapshot.identity.value})
        start_result = stack["coordinator"].start_trial(snapshot, ActiveTrialContext(canonical_trial, map_identity))
        summary["startup_status"] = "PASS" if start_result.ready else start_result.status.value
        termination = "MAX_STEPS_TIMEOUT"
        compute: list[float] = []
        if not start_result.ready:
            termination = "ACTIVE_TYPED_NON_READY_OUTCOME"
        else:
            for step in range(int(config["max_steps"])):
                pre = tuple(float(v) for v in snapshot.state)
                desired = desired_control(pre, goal)
                before_plant = stack["plant"].commit_count
                before_trace = len(stack["trace"].records)
                t0 = time.perf_counter()
                result = stack["coordinator"].run_cycle(snapshot, ActiveCycleRequest(canonical_trial, step, desired, None))
                torch.cuda.synchronize()
                elapsed = time.perf_counter() - t0
                compute.append(elapsed)
                timing_rows.append({"step": step, "compute_time_s": elapsed})
                summary["completed_cycles"] = summary.get("completed_cycles", 0) + 1
                if len(stack["trace"].records) != before_trace + 1:
                    raise RuntimeError("TRACE_CARDINALITY_VIOLATION")
                if stack["plant"].commit_count - before_plant not in (0, 1):
                    raise RuntimeError("PLANT_COMMIT_CARDINALITY_VIOLATION")
                transaction = result.commit_transaction_result
                if transaction is None:
                    summary["evidence_incomplete_count"] += 1
                    raise RuntimeError("MISSING_COMMIT_TRANSACTION_EVIDENCE")
                if transaction.evidence_status not in {EvidenceStatus.COMPLETE, EvidenceStatus.NO_ACTION_COMPLETE}:
                    summary["evidence_incomplete_count"] += int("INCOMPLETE" in transaction.evidence_status.value)
                    summary["recovery_required_count"] += int(bool(transaction.recovery_required))
                    raise RuntimeError("ACTIVE_EVIDENCE_FAILURE:" + transaction.evidence_status.value)
                if PublicCyclePhase.PRIMARY_PROPOSAL in result.phase_history and not result.candidate_refs:
                    summary["primary_proposal_qp_failure_count"] += 1
                if result.committed:
                    receipt = result.commit_receipt
                    decision = result.final_supervisor_decision
                    if receipt is None or decision is None or decision.selected_action is None or receipt.post_state is None:
                        raise RuntimeError("COMMIT_EVIDENCE_INCOMPLETE")
                    if receipt.selected_action_identity != decision.selected_action.identity or receipt.executed_action_identity != decision.selected_action.identity:
                        raise RuntimeError("SELECTED_EXECUTED_IDENTITY_MISMATCH")
                    if any(not math.isfinite(float(v)) for v in (*receipt.exact_vector, *receipt.post_state.state)):
                        raise RuntimeError("NONFINITE_ACTIVE_EXECUTION")
                    role_key = {
                        "PRIMARY_NAVIGATION": "primary_navigation_commit_count",
                        "ALTERNATIVE_NAVIGATION": "alternative_navigation_commit_count",
                        "RETAINED_BACKUP": "retained_backup_commit_count",
                        "CERTIFIED_TERMINAL": "terminal_commit_count",
                    }[receipt.action_role.value]
                    summary[role_key] += 1
                    action = tuple(float(v) for v in receipt.exact_vector)
                    action_rows.append({"step": step, "action": action, "action_hash": semantic_sha256(action), "role": receipt.action_role.value, "selected_action_identity": receipt.selected_action_identity.value})
                    snapshot = receipt.post_state
                    state = tuple(float(v) for v in snapshot.state)
                    states.append(state)
                    state_rows.append({"sequence": len(states) - 1, "state": state, "state_hash": semantic_sha256(state), "runtime_state_identity": snapshot.identity.value})
                else:
                    summary["assurance_boundary_count"] += int(bool(result.boundary))
                if result.boundary:
                    termination = "ACTIVE_ASSURANCE_BOUNDARY"
                    break
                if not result.committed:
                    termination = "ACTIVE_TYPED_NON_READY_OUTCOME"
                    break
                if np.linalg.norm(np.asarray(states[-1]) - np.asarray(states[-2])) < 0.001:
                    termination = "NATIVE_NOT_MOVING"
                    break
        summary["typed_termination"] = termination
        summary["steps_executed"] = len(action_rows)
        finalization = stack["coordinator"].finalize_trial()
        summary["finalization_status"] = finalization.status.value
        if finalization.status != FinalizationStatus.FINALIZED or finalization.trace_lock is None:
            summary["recovery_required_count"] += int(bool(finalization.recovery_required))
            raise RuntimeError("ACTIVE_TRACE_FINALIZATION_FAILURE")
        summary["trace_lock_identity"] = finalization.trace_lock.identity.value
        summary["trace_lock_record_count"] = finalization.trace_lock.record_count
        summary["trace_record_count"] = len(stack["trace"].records)
        if summary["trace_record_count"] != summary.get("completed_cycles", 0):
            raise RuntimeError("TRACE_CYCLE_COUNT_MISMATCH")
        lock = persist_raw(arm_dir, state_rows, action_rows, timing_rows, termination)
        summary["raw_evidence_lock"] = lock["identity"]
        oracle = evaluate_oracle(checkout, stack["loader"], states, goal, config, map_identity)
        summary["oracle"] = oracle
        summary["evaluation_eligible"] = bool(oracle["evaluation_eligible"])
        summary["execution_complete"] = True
        summary["compute_time_median_s"] = statistics.median(compute) if compute else None
        summary["compute_time_p95_s"] = percentile(compute, 0.95)
        summary["compute_time_max_s"] = max(compute) if compute else None
        summary["plant_commit_count"] = stack["plant"].commit_count
        summary["token_activation_count"] = stack["tokens"].activation_count
        summary["token_consume_count"] = stack["tokens"].consume_count
        for stage in ("L1", "C0", "L2", "L3"):
            summary[stage + "_status_counts"] = {name: int(stack["counters"][stage][name]) for name in ("PASS", "FAIL", "UNKNOWN")}
        summary["deadline_status_counts"] = {name: int(stack["counters"]["DEADLINE"][name]) for name in ("OPEN", "WARNING", "EXPIRED")}
    except Exception as exc:
        summary["runtime_exception_count"] += 1
        summary["integrity_failure_count"] += 1
        hard = f"BLOCKED_ACTIVE_RUNTIME_PILOT_BY_ACTIVE_EXCEPTION:{type(exc).__name__}:{exc}"
    finally:
        summary["hard_blocker"] = hard
        summary["episode_wall_time_s"] = time.perf_counter() - started
        summary["process_exit_code"] = 0 if hard is None else 2
        write_json(arm_dir / "summary.json", summary)
        if stack is not None:
            del stack
        torch.cuda.empty_cache()
    return int(summary["process_exit_code"])


def gpu_one_is_clean() -> bool:
    result = subprocess.run(["nvidia-smi", "--query-compute-apps=gpu_uuid,pid,process_name", "--format=csv,noheader,nounits"], text=True, capture_output=True, check=False)
    return all(GPU_ONE_UUID not in line for line in result.stdout.splitlines())


def arm_summary_path(output_dir: Path, trial_id: int, arm: str) -> Path:
    return output_dir / "raw" / f"trial_{trial_id:03d}" / arm.lower() / "summary.json"


def run_one(checkout: Path, output_dir: Path, trial_id: int, arm: str) -> int:
    if trial_id not in FIXED_TRIALS or arm not in FIXED_ARMS:
        raise ValueError("ARM_NOT_IN_FROZEN_MANIFEST")
    if os.environ.get("CUDA_VISIBLE_DEVICES") != "1":
        raise RuntimeError("CUDA_VISIBLE_DEVICES_MUST_EQUAL_1")
    import torch
    if not torch.cuda.is_available() or torch.cuda.device_count() != 1:
        raise RuntimeError("SINGLE_VISIBLE_GPU_REQUIRED")
    config = json.loads(CONFIG_PATH.read_text(encoding="utf-8"))
    map_identity, _ = verify_inputs(checkout, config)
    random.seed(config["seed"])
    np.random.seed(config["seed"])
    torch.manual_seed(config["seed"])
    torch.cuda.manual_seed_all(config["seed"])
    if arm == "REFERENCE_CBF_QP":
        return run_reference(checkout, output_dir, trial_id, config, map_identity)
    return run_active(checkout, output_dir, trial_id, config, map_identity)


def aggregate(output_dir: Path) -> None:
    summaries = []
    for trial in FIXED_TRIALS:
        for arm in FIXED_ARMS:
            path = arm_summary_path(output_dir, trial, arm)
            if path.exists():
                summaries.append(json.loads(path.read_text(encoding="utf-8")))
    trial_rows = []
    for row in summaries:
        oracle = row.get("oracle") or {}
        collision = oracle.get("represented_map_collision_proxy") or {}
        margin = oracle.get("certification_margin_violation") or {}
        trial_rows.append({
            "trial_id": row["trial_id"], "arm": row["arm"], "execution_complete": row["execution_complete"], "evaluation_eligible": row["evaluation_eligible"],
            "typed_termination": row["typed_termination"], "steps_executed": row["steps_executed"], "collision_proxy_trial": collision.get("violation_trial"),
            "collision_proxy_segment_count": collision.get("violation_segment_count"), "min_collision_clearance_m": collision.get("min_clearance_m"),
            "margin_violation_trial": margin.get("violation_trial"), "min_margin_clearance_m": margin.get("min_clearance_m"), "goal_reached": oracle.get("goal_reached"),
            "normalized_progress": oracle.get("normalized_progress"), "compute_median_s": row.get("compute_time_median_s"), "compute_p95_s": row.get("compute_time_p95_s"),
            "episode_wall_time_s": row.get("episode_wall_time_s"), "hard_blocker": row.get("hard_blocker")
        })
    with (output_dir / "pilot_trials.csv").open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=list(trial_rows[0].keys()) if trial_rows else ["trial_id", "arm"])
        writer.writeheader(); writer.writerows(trial_rows)
    pair_rows = []
    by_key = {(r["trial_id"], r["arm"]): r for r in trial_rows}
    for trial in FIXED_TRIALS:
        ref, active = by_key.get((trial, FIXED_ARMS[0])), by_key.get((trial, FIXED_ARMS[1]))
        if not ref or not active:
            continue
        pair_rows.append({
            "trial_id": trial,
            "progress_delta_active_minus_reference": active["normalized_progress"] - ref["normalized_progress"] if active["normalized_progress"] is not None and ref["normalized_progress"] is not None else None,
            "collision_proxy_difference": int(bool(active["collision_proxy_trial"])) - int(bool(ref["collision_proxy_trial"])),
            "margin_violation_difference": int(bool(active["margin_violation_trial"])) - int(bool(ref["margin_violation_trial"])),
            "min_collision_clearance_difference_m": active["min_collision_clearance_m"] - ref["min_collision_clearance_m"] if active["min_collision_clearance_m"] is not None and ref["min_collision_clearance_m"] is not None else None,
            "goal_discordance": bool(active["goal_reached"]) != bool(ref["goal_reached"]),
            "step_count_difference": active["steps_executed"] - ref["steps_executed"],
            "compute_median_ratio": active["compute_median_s"] / ref["compute_median_s"] if active["compute_median_s"] and ref["compute_median_s"] else None,
            "compute_p95_ratio": active["compute_p95_s"] / ref["compute_p95_s"] if active["compute_p95_s"] and ref["compute_p95_s"] else None,
            "termination_category_pair": ref["typed_termination"] + " | " + active["typed_termination"]
        })
    with (output_dir / "pilot_pairs.csv").open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=list(pair_rows[0].keys()) if pair_rows else ["trial_id"])
        writer.writeheader(); writer.writerows(pair_rows)
    arms = {arm: [r for r in summaries if r["arm"] == arm] for arm in FIXED_ARMS}
    def vals(arm: str, field: str) -> list[float]:
        return [float((r.get("oracle") or {}).get(field)) for r in arms[arm] if (r.get("oracle") or {}).get(field) is not None]
    summary = {
        "schema": "ACTIVE_RUNTIME_PILOT_V2_SUMMARY",
        "pair_count_complete": len(pair_rows), "arm_count_complete": sum(bool(r["execution_complete"]) for r in summaries),
        "evaluation_eligible_count": sum(bool(r["evaluation_eligible"]) for r in summaries), "integrity_failure_count": sum(int(r["integrity_failure_count"]) for r in summaries),
        "by_arm": {}, "descriptive_only": True, "p_value_count": 0, "confidence_interval_count": 0
    }
    for arm in FIXED_ARMS:
        progress = vals(arm, "normalized_progress")
        subset = arms[arm]
        summary["by_arm"][arm] = {
            "trial_count": len(subset), "collision_proxy_trial_count": sum(bool((r.get("oracle") or {}).get("represented_map_collision_proxy", {}).get("violation_trial")) for r in subset),
            "margin_violation_trial_count": sum(bool((r.get("oracle") or {}).get("certification_margin_violation", {}).get("violation_trial")) for r in subset),
            "goal_reached_count": sum(bool((r.get("oracle") or {}).get("goal_reached")) for r in subset),
            "normalized_progress_mean": statistics.mean(progress) if progress else None, "normalized_progress_median": statistics.median(progress) if progress else None,
            "steps_total": sum(int(r["steps_executed"]) for r in subset), "termination_counts": dict(Counter(r["typed_termination"] for r in subset)),
            "compute_median_across_trial_medians_s": statistics.median([r["compute_time_median_s"] for r in subset if r["compute_time_median_s"] is not None]) if subset else None,
            "compute_median_across_trial_p95_s": statistics.median([r["compute_time_p95_s"] for r in subset if r["compute_time_p95_s"] is not None]) if subset else None
        }
    write_json(output_dir / "pilot_summary.json", summary)
    active = arms["ACTIVE_RUNTIME_V2"]
    diagnostics = {
        "schema": "ACTIVE_RUNTIME_PILOT_V2_ACTIVE_DIAGNOSTICS",
        "role_counts": {key: sum(int(r[key]) for r in active) for key in ("primary_navigation_commit_count", "alternative_navigation_commit_count", "retained_backup_commit_count", "terminal_commit_count", "assurance_boundary_count")},
        "certificate_status_counts": {stage: {status: sum(int(r[stage + "_status_counts"][status]) for r in active) for status in ("PASS", "FAIL", "UNKNOWN")} for stage in ("L1", "C0", "L2", "L3")},
        "deadline_status_counts": {status: sum(int(r["deadline_status_counts"][status]) for r in active) for status in ("OPEN", "WARNING", "EXPIRED")},
        "primary_proposal_qp_failure_count": sum(int(r["primary_proposal_qp_failure_count"]) for r in active),
        "token_activation_count": sum(int(r["token_activation_count"]) for r in active), "token_consume_count": sum(int(r["token_consume_count"]) for r in active),
        "active_trials_with_primary_commit": sum(int(r["primary_navigation_commit_count"] > 0) for r in active),
        "early_terminal_trials_first_three_cycles": sum(int(r["terminal_commit_count"] > 0 and r["steps_executed"] <= 3) for r in active),
        "active_constraint_count": "NOT_INSTRUMENTED"
    }
    write_json(output_dir / "pilot_active_diagnostics.json", diagnostics)
    oracle_audit = {"schema": "ACTIVE_RUNTIME_PILOT_V2_ORACLE_AUDIT", "feedback": False, "posthoc_only": True, "arm_count_evaluated": sum(r.get("oracle") is not None for r in summaries), "evaluation_ineligible_count": sum(not bool(r["evaluation_eligible"]) for r in summaries), "collision_radius_m": 0.015, "margin_radius_m": 0.025, "goal_tolerance": 0.001, "progress_clipping": "NONE"}
    write_json(output_dir / "pilot_oracle_audit.json", oracle_audit)


def run_batch(checkout: Path, output_dir: Path) -> int:
    config = json.loads(CONFIG_PATH.read_text(encoding="utf-8"))
    verify_inputs(checkout, config)
    env = os.environ.copy(); env.update(config["environment"])
    for trial in FIXED_TRIALS:
        for arm in FIXED_ARMS:
            result = subprocess.run([sys.executable, str(Path(__file__).resolve()), "--one-trial", str(trial), "--arm", arm, "--checkout", str(checkout), "--output-dir", str(output_dir)], env=env)
            path = arm_summary_path(output_dir, trial, arm)
            if not path.exists():
                return 2
            row = json.loads(path.read_text(encoding="utf-8"))
            row["process_exit_code"] = result.returncode
            row["gpu_released_after_process"] = gpu_one_is_clean()
            if not row["gpu_released_after_process"]:
                row["integrity_failure_count"] += 1
                row["hard_blocker"] = row.get("hard_blocker") or "BLOCKED_ACTIVE_RUNTIME_PILOT_BY_GPU_RELEASE"
            write_json(path, row)
            if result.returncode != 0 or row["hard_blocker"]:
                aggregate(output_dir)
                return 2
    aggregate(output_dir)
    return 0


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--checkout", type=Path, required=True)
    parser.add_argument("--output-dir", type=Path, required=True)
    parser.add_argument("--one-trial", type=int)
    parser.add_argument("--arm", choices=FIXED_ARMS)
    parser.add_argument("--all", action="store_true")
    parser.add_argument("--aggregate-only", action="store_true")
    args = parser.parse_args()
    checkout = args.checkout.resolve(strict=True); output_dir = args.output_dir.resolve(); output_dir.mkdir(parents=True, exist_ok=True)
    modes = sum((args.one_trial is not None, args.all, args.aggregate_only))
    if modes != 1:
        raise SystemExit("choose exactly one mode")
    if args.aggregate_only:
        aggregate(output_dir); return 0
    if args.all:
        return run_batch(checkout, output_dir)
    if args.arm is None:
        raise SystemExit("--arm is required with --one-trial")
    return run_one(checkout, output_dir, int(args.one_trial), args.arm)


if __name__ == "__main__":
    raise SystemExit(main())
