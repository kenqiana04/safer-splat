#!/usr/bin/env python3
"""Freeze-check, execute, and summarize the three-trial V3 engineering smoke.

This runner is a thin task-local harness.  It reuses PR #140's V3 stack
factory and the frozen Active Runtime; it owns no geometry, certificate,
routing, selection, plant, token, terminal, or scientific-oracle policy.
"""

from __future__ import annotations

import argparse
import csv
import dataclasses
import hashlib
import importlib.util
import json
import math
import os
from pathlib import Path
import platform
import statistics
import subprocess
import sys
import time
from typing import Any


TASK_DIR = Path(__file__).resolve().parent
PROTOCOL_PATH = TASK_DIR / "SMOKE_V3_PROTOCOL.json"
EXECUTION_LOCK_PATH = TASK_DIR / "SMOKE_V3_EXECUTION_LOCK.json"
UPSTREAM = "47bd12f1f8efca059775ab294211ed21f7b39d77"
FIXED_TRIALS = (10, 50, 90)
PROTECTED_PATHS = (
    "cbf",
    "dynamics",
    "splat",
    "run.py",
    "reproduction/runtime/active_runtime_assurance_v2",
    "reproduction/cross_dataset/fas_cbf_unified_executable_safety_certifier_v1",
    "reproduction/smoke/active_runtime_smoke_v2",
    "reproduction/pilot/active_runtime_pilot_v2",
    "reproduction/formal",
    "reproduction/runtime/v3_hard_radius_runtime_wiring_v1",
    "reproduction/validation/v3_hard_radius_runtime_wiring_v1",
)


def normalize(value: Any) -> Any:
    if dataclasses.is_dataclass(value):
        return normalize(dataclasses.asdict(value))
    if isinstance(value, dict):
        return {str(key): normalize(item) for key, item in value.items()}
    if isinstance(value, (tuple, list)):
        return [normalize(item) for item in value]
    if hasattr(value, "value"):
        return normalize(value.value)
    if hasattr(value, "item") and callable(value.item):
        try:
            return value.item()
        except (TypeError, ValueError):
            pass
    return value


def write_json(path: Path, value: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary = path.with_suffix(path.suffix + ".tmp")
    temporary.write_text(
        json.dumps(normalize(value), indent=2, sort_keys=True, allow_nan=False) + "\n",
        encoding="utf-8",
        newline="\n",
    )
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


def percentile(values: list[float], fraction: float) -> float | None:
    if not values:
        return None
    ordered = sorted(values)
    index = min(len(ordered) - 1, max(0, math.ceil(fraction * len(ordered)) - 1))
    return float(ordered[index])


def git_output(checkout: Path, *args: str) -> str:
    return subprocess.run(
        ["git", "-C", str(checkout), *args], check=True, text=True, capture_output=True
    ).stdout.strip()


def read_protocol() -> dict[str, Any]:
    return json.loads(PROTOCOL_PATH.read_text(encoding="utf-8"))


def _load_v2_helpers(checkout: Path) -> Any:
    path = checkout / "reproduction/smoke/active_runtime_smoke_v2/run_active_runtime_smoke_v2.py"
    spec = importlib.util.spec_from_file_location("_active_smoke_v3_frozen_v2_helpers", path)
    if spec is None or spec.loader is None:
        raise RuntimeError("FROZEN_V2_HELPER_IMPORT_UNAVAILABLE")
    module = importlib.util.module_from_spec(spec)
    previous = sys.modules.get(spec.name)
    sys.modules[spec.name] = module
    try:
        spec.loader.exec_module(module)
    finally:
        if previous is None:
            sys.modules.pop(spec.name, None)
        else:
            sys.modules[spec.name] = previous
    return module


def verify_source_and_map(checkout: Path, protocol: dict[str, Any], require_execution_lock: bool = True) -> tuple[str, list[dict[str, Any]]]:
    if subprocess.run(
        ["git", "-C", str(checkout), "merge-base", "--is-ancestor", UPSTREAM, "HEAD"],
        check=False,
    ).returncode:
        raise RuntimeError("UPSTREAM_V3_COMMIT_NOT_IN_ANCESTRY")
    changed = git_output(checkout, "diff", "--name-only", UPSTREAM, "--", *PROTECTED_PATHS)
    if changed:
        raise RuntimeError("PROTECTED_SOURCE_DIFF_NONZERO:" + changed.replace("\n", ","))
    validation = json.loads(
        (checkout / "reproduction/validation/v3_hard_radius_runtime_wiring_v1/validation_result.json").read_text(encoding="utf-8")
    )
    if validation.get("FINAL_STATUS") != "PASS_IMPLEMENT_AND_VALIDATE_V3_HARD_RADIUS_RUNTIME_WIRING_V1":
        raise RuntimeError("V3_UPSTREAM_VALIDATION_NOT_PASS")
    if require_execution_lock:
        lock = json.loads(EXECUTION_LOCK_PATH.read_text(encoding="utf-8"))
        if lock.get("protocol_sha256") != sha256_file(PROTOCOL_PATH):
            raise RuntimeError("PROTOCOL_HASH_MISMATCH")
        protocol_commit = str(lock.get("protocol_git_commit", ""))
        if len(protocol_commit) != 40 or subprocess.run(
            ["git", "-C", str(checkout), "merge-base", "--is-ancestor", protocol_commit, "HEAD"],
            check=False,
        ).returncode:
            raise RuntimeError("PROTOCOL_COMMIT_NOT_IN_ANCESTRY")
        if lock.get("trial_order") != [10, 50, 90] or lock.get("upstream_commit") != UPSTREAM:
            raise RuntimeError("EXECUTION_LOCK_CONTENT_DRIFT")
    root = (checkout / protocol["map_relative_path"]).resolve(strict=True)
    records: list[dict[str, Any]] = []
    for expected in protocol["map_artifacts"]:
        path = root / expected["relative_path"]
        actual = {
            "relative_path": expected["relative_path"],
            "size": path.stat().st_size,
            "sha256": sha256_file(path),
        }
        if actual != expected:
            raise RuntimeError("MAP_ARTIFACT_IDENTITY_MISMATCH:" + expected["relative_path"])
        records.append(actual)
    identity = semantic_sha256({"scene": "stonehenge", "artifacts": records})
    if identity != protocol["map_identity"]:
        raise RuntimeError("MAP_SEMANTIC_IDENTITY_MISMATCH")
    return identity, records


def verify_environment(protocol: dict[str, Any]) -> None:
    for name in ("CUDA_VISIBLE_DEVICES", "PYTHONHASHSEED", "PYTHONNOUSERSITE", "PYTHONDONTWRITEBYTECODE", "CUBLAS_WORKSPACE_CONFIG"):
        if os.environ.get(name) != protocol["environment"][name]:
            raise RuntimeError("FROZEN_ENVIRONMENT_MISMATCH:" + name)


def build_v3_stack(checkout: Path, output_dir: Path, trial_id: int, protocol: dict[str, Any], map_identity: str) -> dict[str, Any]:
    sys.path.insert(0, str(checkout))
    from reproduction.runtime.v3_hard_radius_runtime_wiring_v1 import build_v3_stack_from_frozen_v2

    stack = build_v3_stack_from_frozen_v2(checkout, output_dir, trial_id, protocol, map_identity)
    audit = stack.get("v3_wiring_audit", {})
    expected = {
        "status": "PASS",
        "hard_runtime_radius_q": 0.015,
        "runtime_margin_q": 0.0,
        "runtime_effective_radius_q": 0.015,
        "rho_seg_q": 0.0,
        "historical_diagnostic_radius_q": 0.025,
        "historical_diagnostic_runtime_authority": False,
    }
    for key, value in expected.items():
        if audit.get(key) != value:
            raise RuntimeError(f"V3_STACK_PREFLIGHT_MISMATCH:{key}")
    if not all(audit.get("checks", {}).values()):
        raise RuntimeError("V3_STACK_OBJECT_GRAPH_CHECK_FAILED")
    return stack


def blank_summary(trial_id: int) -> dict[str, Any]:
    return {
        "schema": "ACTIVE_RUNTIME_SMOKE_V3_TRIAL_SUMMARY_V1",
        "trial_id": trial_id,
        "process_exit_code": 2,
        "startup_status": "NOT_RUN",
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
        "unintended_plant_commit_count": 0,
        "duplicate_plant_commit_count": 0,
        "duplicate_trace_append_count": 0,
        "illegal_token_mutation_count": 0,
        "evidence_incomplete_count": 0,
        "recovery_required_count": 0,
        "plant_outcome_unknown_count": 0,
        "exception_count": 0,
        "cuda_oom_count": 0,
        "trace_record_count": 0,
        "persisted_trace_line_count": 0,
        "trace_lock_record_count": 0,
        "trace_lock_identity": None,
        "finalization_status": "NOT_RUN",
        "deadline_status_counts": {"OPEN": 0, "WARNING": 0, "EXPIRED": 0},
        "L1_status_counts": {"PASS": 0, "FAIL": 0, "UNKNOWN": 0},
        "C0_status_counts": {"PASS": 0, "FAIL": 0, "UNKNOWN": 0},
        "L2_status_counts": {"PASS": 0, "FAIL": 0, "UNKNOWN": 0},
        "L3_status_counts": {"PASS": 0, "FAIL": 0, "UNKNOWN": 0},
        "cycle_time_values": [],
        "cycle_runtime_mean": None,
        "cycle_runtime_median": None,
        "cycle_runtime_p95": None,
        "cycle_runtime_max": None,
        "stage_timing_observations": [],
        "termination_reason": "NOT_RUN",
        "final_supervisor_reason": None,
        "hard_blocker": None,
        "gpu_trial_rerun": False,
        "task_local_autofixes": [],
    }


def run_preflight(checkout: Path, output_dir: Path) -> int:
    protocol = read_protocol()
    verify_environment(protocol)
    import torch

    if not torch.cuda.is_available() or torch.cuda.device_count() != 1:
        raise RuntimeError("SINGLE_VISIBLE_GPU_REQUIRED")
    map_identity, artifacts = verify_source_and_map(checkout, protocol)
    stack = build_v3_stack(checkout, output_dir, FIXED_TRIALS[0], protocol, map_identity)
    result = {
        "schema": "ACTIVE_RUNTIME_SMOKE_V3_GPU_PREFLIGHT_V1",
        "status": "PASS",
        "map_identity": map_identity,
        "map_artifacts": artifacts,
        "v3_wiring_audit": stack["v3_wiring_audit"],
        "gpu": {"visible_device_count": torch.cuda.device_count(), "device_name": torch.cuda.get_device_name(0)},
        "runtime_cycles_executed": 0,
    }
    write_json(output_dir / "raw" / "gpu_preflight.json", result)
    del stack
    torch.cuda.empty_cache()
    print("PASS_ACTIVE_RUNTIME_SMOKE_V3_GPU_PREFLIGHT", flush=True)
    return 0


def run_one(checkout: Path, output_dir: Path, trial_id: int) -> int:
    summary = blank_summary(trial_id)
    raw_dir = output_dir / "raw" / f"trial_{trial_id}"
    raw_dir.mkdir(parents=True, exist_ok=True)
    stack: dict[str, Any] | None = None
    blocker: str | None = None
    started = time.perf_counter()
    try:
        if trial_id not in FIXED_TRIALS:
            raise ValueError("TRIAL_ID_NOT_FROZEN")
        protocol = read_protocol()
        verify_environment(protocol)
        import numpy as np
        import torch

        if not torch.cuda.is_available() or torch.cuda.device_count() != 1:
            raise RuntimeError("SINGLE_VISIBLE_GPU_REQUIRED")
        map_identity, _ = verify_source_and_map(checkout, protocol)
        np.random.seed(protocol["seed"])
        torch.manual_seed(protocol["seed"])
        torch.cuda.manual_seed_all(protocol["seed"])
        helpers = _load_v2_helpers(checkout)
        stack = build_v3_stack(checkout, output_dir, trial_id, protocol, map_identity)
        from reproduction.runtime.active_runtime_assurance_v2.runtime_types import (
            ActiveCycleRequest,
            ActiveTrialContext,
            EvidenceStatus,
            FinalizationStatus,
            RuntimeStateSnapshot,
        )

        start, goal_position = helpers.trial_geometry(trial_id)
        state = tuple(float(item) for item in np.concatenate((start.astype(np.float32), np.zeros(3, dtype=np.float32))))
        goal = tuple(float(item) for item in np.concatenate((goal_position.astype(np.float32), np.zeros(3, dtype=np.float32))))
        canonical_trial = f"STONEHENGE_TRIAL_{trial_id:03d}"
        snapshot = RuntimeStateSnapshot.create(canonical_trial, 0, state, goal, map_identity, protocol["dynamics"]["dt"])
        summary.update({
            "initial_state_identity": snapshot.identity.value,
            "goal_identity": "goal:sha256:" + semantic_sha256(goal),
            "map_identity": map_identity,
            "deadline_profile_identity": stack["profile"].identity,
            "v3_wiring_audit": stack["v3_wiring_audit"],
            "environment": {
                "python": platform.python_version(),
                "executable": sys.executable,
                "torch": torch.__version__,
                "torch_cuda": torch.version.cuda,
                "numpy": np.__version__,
                "cuda_visible_devices": os.environ.get("CUDA_VISIBLE_DEVICES"),
                "visible_device_count": torch.cuda.device_count(),
                "device_name": torch.cuda.get_device_name(0),
            },
        })
        start_result = stack["coordinator"].start_trial(snapshot, ActiveTrialContext(canonical_trial, map_identity))
        summary["startup_status"] = "PASS" if start_result.ready else start_result.status.value
        if not start_result.ready:
            blocker = "BLOCKED_ACTIVE_RUNTIME_SMOKE_V3_BY_STARTUP_ADMISSION:" + start_result.reason
        else:
            for cycle in range(protocol["maximum_completed_cycles_per_trial"]):
                position = np.asarray(snapshot.position, dtype=np.float64)
                velocity = np.asarray(snapshot.velocity, dtype=np.float64)
                goal_now = np.asarray(snapshot.goal[:3], dtype=np.float64)
                desired_velocity = np.clip(5.0 * (goal_now - position), -0.1, 0.1) - velocity
                desired = tuple(float(item) for item in np.clip(desired_velocity - velocity, -0.1, 0.1))
                before_plant = stack["plant"].commit_count
                before_trace = len(stack["trace"].records)
                cycle_started = time.perf_counter()
                result = stack["coordinator"].run_cycle(snapshot, ActiveCycleRequest(canonical_trial, cycle, desired, None))
                torch.cuda.synchronize()
                elapsed = time.perf_counter() - cycle_started
                summary["cycle_time_values"].append(elapsed)
                summary["completed_cycles"] += 1
                for observation in result.deadline_observations:
                    summary["stage_timing_observations"].append(normalize(observation))
                plant_delta = stack["plant"].commit_count - before_plant
                trace_delta = len(stack["trace"].records) - before_trace
                if trace_delta != 1:
                    summary["duplicate_trace_append_count"] += int(trace_delta > 1)
                    blocker = "BLOCKED_ACTIVE_RUNTIME_SMOKE_V3_BY_TRACE_CARDINALITY"
                    break
                if plant_delta not in (0, 1):
                    summary["duplicate_plant_commit_count"] += int(plant_delta > 1)
                    blocker = "BLOCKED_ACTIVE_RUNTIME_SMOKE_V3_BY_PLANT_CARDINALITY"
                    break
                transaction = result.commit_transaction_result
                if transaction is None:
                    summary["evidence_incomplete_count"] += 1
                    blocker = "BLOCKED_ACTIVE_RUNTIME_SMOKE_V3_BY_EVIDENCE_INCOMPLETE"
                    break
                if transaction.evidence_status not in {EvidenceStatus.COMPLETE, EvidenceStatus.NO_ACTION_COMPLETE}:
                    status = transaction.evidence_status.value
                    summary["evidence_incomplete_count"] += int("INCOMPLETE" in status)
                    summary["recovery_required_count"] += int(transaction.recovery_required or status == "RECOVERY_REQUIRED")
                    summary["plant_outcome_unknown_count"] += int("PLANT_OUTCOME_UNRESOLVED" in status)
                    blocker = "BLOCKED_ACTIVE_RUNTIME_SMOKE_V3_BY_EVIDENCE_STATUS:" + status
                    break
                if result.committed:
                    receipt = result.commit_receipt
                    decision = result.final_supervisor_decision
                    if receipt is None or decision is None or decision.selected_action is None or plant_delta != 1:
                        summary["unintended_plant_commit_count"] += int(plant_delta != 1)
                        blocker = "BLOCKED_ACTIVE_RUNTIME_SMOKE_V3_BY_UNAUTHORIZED_PLANT"
                        break
                    if receipt.selected_action_identity != decision.selected_action.identity or receipt.executed_action_identity != decision.selected_action.identity:
                        summary["selected_executed_identity_mismatch_count"] += 1
                        blocker = "BLOCKED_ACTIVE_RUNTIME_SMOKE_V3_BY_SELECTED_EXECUTED_IDENTITY"
                        break
                    if receipt.post_state is None or any(not math.isfinite(float(v)) for v in (*receipt.exact_vector, *receipt.post_state.state)):
                        summary["nonfinite_count"] += 1
                        blocker = "BLOCKED_ACTIVE_RUNTIME_SMOKE_V3_BY_NONFINITE"
                        break
                    if any(v < -0.1 or v > 0.1 for v in receipt.exact_vector):
                        summary["action_bound_violation_count"] += 1
                        blocker = "BLOCKED_ACTIVE_RUNTIME_SMOKE_V3_BY_ACTION_BOUNDS"
                        break
                    role_key = {
                        "PRIMARY_NAVIGATION": "primary_navigation_commit_count",
                        "ALTERNATIVE_NAVIGATION": "alternative_navigation_commit_count",
                        "RETAINED_BACKUP": "retained_backup_commit_count",
                        "CERTIFIED_TERMINAL": "terminal_commit_count",
                    }.get(receipt.action_role.value)
                    if role_key is None:
                        blocker = "BLOCKED_ACTIVE_RUNTIME_SMOKE_V3_BY_UNKNOWN_ACTION_ROLE"
                        break
                    summary[role_key] += 1
                    snapshot = receipt.post_state
                else:
                    if plant_delta:
                        summary["unintended_plant_commit_count"] += 1
                        blocker = "BLOCKED_ACTIVE_RUNTIME_SMOKE_V3_BY_UNAUTHORIZED_PLANT"
                        break
                    summary["assurance_boundary_count"] += int(result.boundary)
                if result.final_supervisor_decision is not None:
                    summary["final_supervisor_reason"] = result.final_supervisor_decision.reason
                if result.boundary:
                    summary["termination_reason"] = "ASSURANCE_BOUNDARY"
                    break
                if result.next_state is None:
                    blocker = "BLOCKED_ACTIVE_RUNTIME_SMOKE_V3_BY_MISSING_NEXT_STATE"
                    break
                if cycle == protocol["maximum_completed_cycles_per_trial"] - 1:
                    summary["termination_reason"] = "MAX_COMPLETED_CYCLES"
            if summary["termination_reason"] == "NOT_RUN" and blocker is None:
                summary["termination_reason"] = "MAX_COMPLETED_CYCLES"

        finalization = stack["coordinator"].finalize_trial()
        summary["finalization_status"] = finalization.status.value
        if finalization.trace_lock is not None:
            summary["trace_lock_identity"] = finalization.trace_lock.identity.value
            summary["trace_lock_record_count"] = finalization.trace_lock.record_count
        summary["trace_record_count"] = len(stack["trace"].records)
        summary["plant_commit_count"] = stack["plant"].commit_count
        for stage in ("L1", "C0", "L2", "L3"):
            summary[stage + "_status_counts"] = {name: int(stack["counters"][stage][name]) for name in ("PASS", "FAIL", "UNKNOWN")}
        summary["deadline_status_counts"] = {name: int(stack["counters"]["DEADLINE"][name]) for name in ("OPEN", "WARNING", "EXPIRED")}
        trace_path = raw_dir / "runtime_trace.jsonl"
        summary["persisted_trace_line_count"] = len(trace_path.read_text(encoding="utf-8").splitlines()) if trace_path.exists() else 0
        committed_roles = sum(summary[key] for key in (
            "primary_navigation_commit_count",
            "alternative_navigation_commit_count",
            "retained_backup_commit_count",
            "terminal_commit_count",
        ))
        if committed_roles != summary["plant_commit_count"]:
            blocker = blocker or "BLOCKED_ACTIVE_RUNTIME_SMOKE_V3_BY_COMMIT_ROLE_CARDINALITY"
        if not (summary["trace_record_count"] == summary["trace_lock_record_count"] == summary["persisted_trace_line_count"] == summary["completed_cycles"]):
            blocker = blocker or "BLOCKED_ACTIVE_RUNTIME_SMOKE_V3_BY_TRACE_CARDINALITY"
        if finalization.status != FinalizationStatus.FINALIZED:
            summary["recovery_required_count"] += int(finalization.recovery_required)
            blocker = blocker or "BLOCKED_ACTIVE_RUNTIME_SMOKE_V3_BY_FINALIZATION"
    except Exception as exc:
        summary["exception_count"] += 1
        summary["cuda_oom_count"] += int("out of memory" in str(exc).lower())
        blocker = blocker or f"BLOCKED_ACTIVE_RUNTIME_SMOKE_V3_BY_CORE_RUNTIME:{type(exc).__name__}:{exc}"
        if stack is not None:
            summary["plant_commit_count"] = stack["plant"].commit_count
            summary["trace_record_count"] = len(stack["trace"].records)
    finally:
        values = [float(value) for value in summary["cycle_time_values"]]
        summary["cycle_runtime_mean"] = statistics.fmean(values) if values else None
        summary["cycle_runtime_median"] = statistics.median(values) if values else None
        summary["cycle_runtime_p95"] = percentile(values, 0.95)
        summary["cycle_runtime_max"] = max(values) if values else None
        summary["wall_time_total"] = time.perf_counter() - started
        summary["hard_blocker"] = blocker
        summary["process_exit_code"] = 0 if blocker is None else 2
        write_json(raw_dir / "trial_summary.json", summary)
        if stack is not None:
            del stack
        try:
            import torch
            torch.cuda.empty_cache()
        except ImportError:
            pass
    print(json.dumps({"trial_id": trial_id, "exit_code": summary["process_exit_code"], "blocker": blocker}, sort_keys=True), flush=True)
    return int(summary["process_exit_code"])


def gpu_pid_released(pid: int) -> bool:
    result = subprocess.run(
        ["nvidia-smi", "--query-compute-apps=pid", "--format=csv,noheader,nounits"],
        text=True,
        capture_output=True,
        check=False,
    )
    return str(pid) not in {line.strip() for line in result.stdout.splitlines()}


def complete_trial_evidence(output_dir: Path, trial_id: int) -> bool:
    raw = output_dir / "raw" / f"trial_{trial_id}"
    required = (raw / "trial_summary.json", raw / "runtime_trace.jsonl", raw / "runtime_trace_lock.json", raw / "process_exit_code.txt", raw / "gpu_released.txt")
    if not all(path.is_file() for path in required):
        return False
    summary = json.loads(required[0].read_text(encoding="utf-8"))
    lock = json.loads(required[2].read_text(encoding="utf-8"))
    return (
        int(required[3].read_text(encoding="utf-8").strip()) == 0
        and required[4].read_text(encoding="utf-8").strip() == "true"
        and summary.get("hard_blocker") is None
        and summary.get("finalization_status") == "FINALIZED"
        and summary.get("completed_cycles") == lock.get("record_count") == len(required[1].read_text(encoding="utf-8").splitlines())
    )


def run_batch(checkout: Path, output_dir: Path) -> int:
    protocol = read_protocol()
    verify_source_and_map(checkout, protocol)
    overall = 0
    for trial_id in FIXED_TRIALS:
        if complete_trial_evidence(output_dir, trial_id):
            print(f"TRIAL_{trial_id}_IMMUTABLE_EVIDENCE_ALREADY_COMPLETE_SKIP", flush=True)
            continue
        raw_dir = output_dir / "raw" / f"trial_{trial_id}"
        raw_dir.mkdir(parents=True, exist_ok=True)
        env = os.environ.copy()
        env.update(protocol["environment"])
        command = [
            protocol["environment"]["python"],
            str(Path(__file__).resolve()),
            "--one",
            str(trial_id),
            "--checkout",
            str(checkout),
            "--output-dir",
            str(output_dir),
        ]
        with (raw_dir / "stdout.log").open("w", encoding="utf-8", newline="\n") as stdout, (raw_dir / "stderr.log").open("w", encoding="utf-8", newline="\n") as stderr:
            process = subprocess.Popen(command, env=env, stdout=stdout, stderr=stderr, text=True)
            pid = process.pid
            code = process.wait()
        released = gpu_pid_released(pid)
        (raw_dir / "process_exit_code.txt").write_text(f"{code}\n", encoding="utf-8", newline="\n")
        (raw_dir / "gpu_released.txt").write_text(("true" if released else "false") + "\n", encoding="utf-8", newline="\n")
        if code or not released or not complete_trial_evidence(output_dir, trial_id):
            overall = code or 2
            print(f"TRIAL_{trial_id}_HARD_STOP exit={code} gpu_released={released}", flush=True)
            break
        print(f"TRIAL_{trial_id}_PASS", flush=True)
    summarize(output_dir)
    return overall


def summarize(output_dir: Path) -> dict[str, Any]:
    protocol = read_protocol()
    summaries: list[dict[str, Any]] = []
    failures: list[dict[str, Any]] = []
    all_times: list[float] = []
    for trial_id in FIXED_TRIALS:
        path = output_dir / "raw" / f"trial_{trial_id}" / "trial_summary.json"
        if path.is_file():
            summary = json.loads(path.read_text(encoding="utf-8"))
        else:
            summary = blank_summary(trial_id)
            summary["hard_blocker"] = "TRIAL_NOT_EXECUTED"
        summaries.append(summary)
        all_times.extend(float(value) for value in summary.get("cycle_time_values", []))
        if summary.get("hard_blocker"):
            failures.append({
                "trial_id": trial_id,
                "cycle_index": max(-1, int(summary.get("completed_cycles", 0)) - 1),
                "failure_class": summary["hard_blocker"],
                "runtime_or_task_local": "runtime",
                "scientific_integrity_affected": True,
                "raw_evidence_complete": bool(summary.get("trace_lock_identity")),
                "rerun_required": False,
                "resolution": "STOP_AND_PRESERVE_EVIDENCE",
            })
    fields = [
        "trial_id", "process_exit_code", "startup_status", "completed_cycles", "plant_commit_count",
        "primary_navigation_commit_count", "alternative_navigation_commit_count", "retained_backup_commit_count",
        "terminal_commit_count", "assurance_boundary_count", "finalization_status", "trace_record_count",
        "trace_lock_record_count", "persisted_trace_line_count", "termination_reason", "hard_blocker",
    ]
    with (output_dir / "SMOKE_V3_TRIAL_RESULTS.csv").open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=fields, extrasaction="ignore")
        writer.writeheader()
        writer.writerows(summaries)
    failure_fields = ["trial_id", "cycle_index", "failure_class", "runtime_or_task_local", "scientific_integrity_affected", "raw_evidence_complete", "rerun_required", "resolution"]
    with (output_dir / "SMOKE_V3_FAILURE_REGISTER.csv").open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=failure_fields)
        writer.writeheader()
        writer.writerows(failures)
    trace_rows = []
    for summary in summaries:
        trace_rows.append({
            "trial_id": summary["trial_id"],
            "completed_cycles": summary["completed_cycles"],
            "in_memory_trace_records": summary["trace_record_count"],
            "persisted_trace_lines": summary["persisted_trace_line_count"],
            "trace_lock_records": summary["trace_lock_record_count"],
            "cardinality_pass": summary["completed_cycles"] == summary["trace_record_count"] == summary["persisted_trace_line_count"] == summary["trace_lock_record_count"],
            "finalized": summary["finalization_status"] == "FINALIZED",
        })
    trace_audit = {
        "schema": "ACTIVE_RUNTIME_SMOKE_V3_TRACE_AUDIT_V1",
        "trials": trace_rows,
        "status": "PASS" if len(trace_rows) == 3 and all(row["cardinality_pass"] and row["finalized"] for row in trace_rows) else "FAIL",
    }
    write_json(output_dir / "SMOKE_V3_TRACE_AUDIT.json", trace_audit)
    timing = {
        "schema": "ACTIVE_RUNTIME_SMOKE_V3_TIMING_SUMMARY_V1",
        "interpretation": "ENGINEERING_TELEMETRY_ONLY_NO_REAL_TIME_OR_DEPLOYMENT_GUARANTEE",
        "cycle_count": len(all_times),
        "mean": statistics.fmean(all_times) if all_times else None,
        "median": statistics.median(all_times) if all_times else None,
        "p95": percentile(all_times, 0.95),
        "max": max(all_times) if all_times else None,
        "deadline_status_counts": {name: sum(int(item.get("deadline_status_counts", {}).get(name, 0)) for item in summaries) for name in ("OPEN", "WARNING", "EXPIRED")},
        "per_trial": [{key: item.get(key) for key in ("trial_id", "cycle_runtime_mean", "cycle_runtime_median", "cycle_runtime_p95", "cycle_runtime_max")} for item in summaries],
    }
    write_json(output_dir / "SMOKE_V3_TIMING_SUMMARY.json", timing)
    count_fields = (
        "completed_cycles", "plant_commit_count", "primary_navigation_commit_count", "alternative_navigation_commit_count",
        "retained_backup_commit_count", "terminal_commit_count", "assurance_boundary_count",
        "selected_executed_identity_mismatch_count", "nonfinite_count", "action_bound_violation_count",
        "evidence_incomplete_count", "recovery_required_count", "plant_outcome_unknown_count", "exception_count",
    )
    totals = {field: sum(int(item.get(field, 0)) for item in summaries) for field in count_fields}
    passed = (
        len(summaries) == 3
        and not failures
        and all(item.get("startup_status") == "PASS" and item.get("finalization_status") == "FINALIZED" and item.get("process_exit_code") == 0 for item in summaries)
        and trace_audit["status"] == "PASS"
        and totals["selected_executed_identity_mismatch_count"] == 0
        and totals["nonfinite_count"] == 0
        and totals["action_bound_violation_count"] == 0
        and totals["evidence_incomplete_count"] == 0
        and totals["recovery_required_count"] == 0
        and totals["plant_outcome_unknown_count"] == 0
    )
    execution = {
        "schema": "ACTIVE_RUNTIME_SMOKE_V3_EXECUTION_SUMMARY_V1",
        "trials": [item["trial_id"] for item in summaries],
        "trial_pass_count": sum(int(item.get("hard_blocker") is None and item.get("process_exit_code") == 0) for item in summaries),
        "finalization_pass_count": sum(int(item.get("finalization_status") == "FINALIZED") for item in summaries),
        "totals": totals,
        "deadline_status_counts": timing["deadline_status_counts"],
        "trace_cardinality": trace_audit["status"],
        "hard_runtime_radius_observed_q": 0.015 if all(item.get("v3_wiring_audit", {}).get("hard_runtime_radius_q") == 0.015 for item in summaries) else None,
        "historical_0_025_runtime_authority_observed": any(item.get("v3_wiring_audit", {}).get("historical_diagnostic_runtime_authority") is not False for item in summaries if item.get("v3_wiring_audit")),
        "gpu_trial_rerun_count": sum(int(item.get("gpu_trial_rerun", False)) for item in summaries),
        "formal_scientific_arm_count": 0,
        "pilot_count": 0,
        "official100_count": 0,
        "scientific_oracle_count": 0,
        "FINAL_STATUS": "PASS_ACTIVE_RUNTIME_SMOKE_V3" if passed else "BLOCKED_ACTIVE_RUNTIME_SMOKE_V3_BY_CORE_RUNTIME",
        "FINAL_DECISION": "ADVANCE_TO_ACTIVE_RUNTIME_PILOT_V3_PROTOCOL_FREEZE" if passed else "STOP_AND_PRESERVE_EVIDENCE",
    }
    write_json(output_dir / "SMOKE_V3_EXECUTION_SUMMARY.json", execution)
    handoff = {
        "schema": "ACTIVE_RUNTIME_SMOKE_V3_DOWNSTREAM_HANDOFF_V1",
        "status": "READY_FOR_ACTIVE_RUNTIME_PILOT_V3_PROTOCOL_FREEZE" if passed else "BLOCKED",
        "upstream_v3_commit": UPSTREAM,
        "hard_radius_q": 0.015,
        "runtime_margin_q": 0.0,
        "effective_radius_q": 0.015,
        "rho_seg_q": 0.0,
        "historical_diag_radius_q": 0.025,
        "historical_diag_runtime_authority": False,
        "smoke_trials": [10, 50, 90],
        "pilot_protocol_freeze_authorized": passed,
        "pilot_execution_authorized": False,
        "official100_authorized": False,
        "parameter_selection_authorized": False,
    }
    write_json(output_dir / "downstream_handoff.json", handoff)
    protocol_hash = sha256_file(PROTOCOL_PATH)
    report = f"""# Active Runtime Smoke V3

`FINAL_STATUS={execution['FINAL_STATUS']}`

`FINAL_DECISION={execution['FINAL_DECISION']}`

The pre-frozen Stonehenge V3 engineering smoke executed only trials 10, 50, and 90, serially in separate GPU-1 processes, with at most 200 completed cycles each. The runtime stack observed hard radius `0.015 q`, margin `0 q`, effective radius `0.015 q`, and `rho_seg=0 q`; the historical `0.025 q` shell retained no runtime authority.

- Protocol SHA256: `{protocol_hash}`
- Trial PASS/finalization PASS: {execution['trial_pass_count']}/3 and {execution['finalization_pass_count']}/3
- Cycles/plant commits: {totals['completed_cycles']}/{totals['plant_commit_count']}
- Primary/alternative/backup/terminal/boundary: {totals['primary_navigation_commit_count']}/{totals['alternative_navigation_commit_count']}/{totals['retained_backup_commit_count']}/{totals['terminal_commit_count']}/{totals['assurance_boundary_count']}
- Trace cardinality: {trace_audit['status']}
- Deadline OPEN/WARNING/EXPIRED: {timing['deadline_status_counts']['OPEN']}/{timing['deadline_status_counts']['WARNING']}/{timing['deadline_status_counts']['EXPIRED']}
- Identity mismatch/nonfinite/actuator violation/evidence incomplete/recovery required: {totals['selected_executed_identity_mismatch_count']}/{totals['nonfinite_count']}/{totals['action_bound_violation_count']}/{totals['evidence_incomplete_count']}/{totals['recovery_required_count']}

Timing is engineering telemetry only. This Smoke does not support collision, progress, noninferiority, efficacy, real-time, deployment, or parameter-selection claims. No Pilot, Official100, Formal comparison, reference arm, or scientific oracle ran.

Only next task: `FREEZE_ACTIVE_RUNTIME_PILOT_V3_PROTOCOL`.
"""
    report_path = output_dir / "report" / "REPORT_ACTIVE_RUNTIME_SMOKE_V3.md"
    report_path.parent.mkdir(parents=True, exist_ok=True)
    report_path.write_text(report, encoding="utf-8", newline="\n")
    return execution


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--checkout", type=Path, required=True)
    parser.add_argument("--output-dir", type=Path, required=True)
    modes = parser.add_mutually_exclusive_group(required=True)
    modes.add_argument("--preflight", action="store_true")
    modes.add_argument("--one", type=int)
    modes.add_argument("--all", action="store_true")
    modes.add_argument("--summarize", action="store_true")
    args = parser.parse_args()
    checkout = args.checkout.resolve(strict=True)
    output_dir = args.output_dir.resolve()
    output_dir.mkdir(parents=True, exist_ok=True)
    if args.preflight:
        return run_preflight(checkout, output_dir)
    if args.one is not None:
        return run_one(checkout, output_dir, int(args.one))
    if args.all:
        return run_batch(checkout, output_dir)
    summary = summarize(output_dir)
    print(summary["FINAL_STATUS"], flush=True)
    return 0 if summary["FINAL_STATUS"] == "PASS_ACTIVE_RUNTIME_SMOKE_V3" else 2


if __name__ == "__main__":
    raise SystemExit(main())
