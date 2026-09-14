#!/usr/bin/env python3
"""Frozen, resumable Active Runtime V3 paired-validation executor.

Static preflight is CPU-only. GPU preflight and collection require the committed
execution lock and are intentionally not invoked by the harness-freeze task.
"""
from __future__ import annotations

import argparse
import csv
import hashlib
import importlib.util
import json
import math
import os
from pathlib import Path
import subprocess
import sys
from typing import Any

PARENT = "0ef0523050fc8e6c77fe333709477c5a4161d489"
BRANCH = "execute-active-runtime-v3-paired-validation-v1"
PROTOCOL_COMMIT = "b614ff3e985376b5b52f62709ce1a9332170af99"
PROTOCOL_SHA = "2de32310c84db49f0b8982e2bb63f15d234732250a5c3ddf859fdb75386439c5"
PRIMARY = (0,1,2,3,4,6,7,8,9,11,12,13,14,16,17,18,19,20,21,22,23,24,26,27,28,29,31,32,33,34,36,37,38,39,40,41,42,43,44,46,47,48,49,51,52,53,54,56,57,58,59,60,61,62,63,64,66,67,68,69,71,72,73,74,76,77,78,79,80,81,82,83,84,86,87,88,89,91,92,93,94,96,97,98,99)
ORDER = (66,74,9,12,73,26,79,31,54,18,19,88,38,8,28,29,0,24,37,98,27,91,2,78,76,80,82,99,56,21,33,44,14,16,61,23,6,96,43,47,51,69,59,63,42,13,4,93,39,49,97,60,83,36,67,86,3,81,87,71,20,53,7,58,40,89,94,68,48,92,34,72,17,32,62,41,52,64,22,84,11,57,1,46,77)
DEV15 = (5,10,15,25,30,35,45,50,55,65,70,75,85,90,95)
TASK_REL = "reproduction/validation/active_runtime_paired_validation_v3_execution"
PROTOCOL_REL = "reproduction/validation/active_runtime_paired_validation_v3"
TASK_DIR = Path(__file__).resolve().parent
LOCK_PATH = TASK_DIR / "V3_PAIRED_EXECUTION_LOCK.json"
LOCK_SHA_PATH = TASK_DIR / "V3_PAIRED_EXECUTION_LOCK.sha256"
DEFAULT_MAP_ROOT = Path("/disk1/zlab/projects/safer-splat/outputs/stonehenge/splatfacto/2024-09-11_100724")
DEFAULT_RESULT_ROOT = Path("/disk1/zlab/v3_execution_records/active_runtime_paired_validation_v3_20260914")
PROTECTED = ("cbf", "dynamics", "splat", "run.py", "reproduction/runtime", "reproduction/smoke", "reproduction/pilot", "reproduction/formal", PROTOCOL_REL)
INTEGRITY_FIELDS = (
    "selected_executed_identity_mismatch_count", "nonfinite_count", "action_bound_violation_count",
    "evidence_incomplete_count", "recovery_required_count", "plant_outcome_unknown_count",
    "unintended_plant_commit_count", "duplicate_plant_commit_count", "duplicate_trace_append_count",
    "exception_count", "cuda_oom_count", "FORBIDDEN_DIAGNOSTIC_AUTHORITY_EVENT_COUNT",
)

def sha256_file(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as f:
        for chunk in iter(lambda: f.read(1024 * 1024), b""):
            h.update(chunk)
    return h.hexdigest()

def semantic_sha256(value: Any) -> str:
    return hashlib.sha256(json.dumps(value, sort_keys=True, separators=(",", ":"), allow_nan=False).encode()).hexdigest()

def load_json(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))

def write_json(path: Path, value: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    tmp = path.with_suffix(path.suffix + ".tmp")
    tmp.write_text(json.dumps(value, indent=2, sort_keys=True, allow_nan=False) + "\n", encoding="utf-8", newline="\n")
    tmp.replace(path)

def git(checkout: Path, *args: str, check: bool = True) -> str:
    p = subprocess.run(["git", "-C", str(checkout), *args], text=True, capture_output=True, check=check)
    return p.stdout.strip()

def frozen(checkout: Path) -> tuple[dict[str, Any], dict[str, Any], dict[str, Any]]:
    root = checkout / PROTOCOL_REL
    protocol = load_json(root / "V3_PAIRED_VALIDATION_PROTOCOL.json")
    input_lock = load_json(root / "V3_INPUT_LOCK.json")
    reference = load_json(root / "V3_REFERENCE_REUSE_LOCK.json")
    return protocol, input_lock, reference

def verify_cohort(checkout: Path, protocol: dict[str, Any]) -> None:
    study = protocol["study_design"]
    if tuple(study["primary_trial_ids"]) != PRIMARY or tuple(study["execution_order"]) != ORDER:
        raise RuntimeError("FROZEN_PRIMARY_COHORT_OR_ORDER_MISMATCH")
    if tuple(study["development_exposed_trial_ids"]) != DEV15 or set(PRIMARY) & set(DEV15):
        raise RuntimeError("FROZEN_DEVELOPMENT_EXCLUSION_MISMATCH")
    with (checkout / PROTOCOL_REL / "V3_TRIAL_MANIFEST.csv").open(encoding="utf-8", newline="") as f:
        rows = list(csv.DictReader(f))
    if len(rows) != 85 or [int(r["trial_id"]) for r in rows] != list(ORDER):
        raise RuntimeError("FROZEN_MANIFEST_MISMATCH")

def verify_map(protocol: dict[str, Any], map_root: Path) -> list[dict[str, Any]]:
    root = map_root.resolve(strict=True)
    actual = []
    for expected in protocol["map"]["artifacts"]:
        path = root / expected["relative_path"]
        row = {"relative_path": expected["relative_path"], "size": path.stat().st_size, "sha256": sha256_file(path)}
        if row != expected:
            raise RuntimeError("MAP_ARTIFACT_IDENTITY_MISMATCH:" + expected["relative_path"])
        actual.append(row)
    if semantic_sha256({"scene": "stonehenge", "artifacts": actual}) != protocol["map"]["identity"]:
        raise RuntimeError("MAP_SEMANTIC_IDENTITY_MISMATCH")
    return actual

def verify_reference(reference: dict[str, Any]) -> None:
    if not reference["all_immutable_complete_identity_compatible"] or reference["reference_arm_count"] != 85:
        raise RuntimeError("REFERENCE_REUSE_LOCK_NOT_COMPLETE")
    if reference["reference_rerun_authorized"] or reference["reference_rerun_count"] != 0:
        raise RuntimeError("REFERENCE_RERUN_AUTHORITY_MISMATCH")
    root = Path(reference["formal_v2_result_root"])
    for name, expected in reference["formal_v2_result_artifact_sha256"].items():
        path = root / name
        if not path.is_file() or sha256_file(path) != expected:
            raise RuntimeError("REFERENCE_RESULT_ARTIFACT_MISMATCH:" + name)

def verify_protected_diff(checkout: Path) -> None:
    for path in PROTECTED:
        if git(checkout, "diff", "--name-only", PARENT, "HEAD", "--", path):
            raise RuntimeError("PROTECTED_COMMITTED_DIFF:" + path)
        if git(checkout, "diff", "--name-only", "--", path) or git(checkout, "diff", "--cached", "--name-only", "--", path):
            raise RuntimeError("PROTECTED_WORKTREE_DIFF:" + path)
    changed = git(checkout, "status", "--porcelain").splitlines()
    for line in changed:
        path = line[3:].replace("\\", "/").split(" -> ")[-1]
        if not path.startswith(TASK_REL + "/"):
            raise RuntimeError("OUT_OF_SCOPE_WORKTREE_CHANGE:" + path)

def verify_execution_lock(checkout: Path, require_committed: bool) -> dict[str, Any]:
    lock = load_json(LOCK_PATH)
    line = LOCK_SHA_PATH.read_text(encoding="utf-8").strip()
    if line != f"{sha256_file(LOCK_PATH)}  V3_PAIRED_EXECUTION_LOCK.json":
        raise RuntimeError("EXECUTION_LOCK_SHA_MISMATCH")
    expected = {
        "parent_pr144_head": PARENT, "protocol_freeze_commit": PROTOCOL_COMMIT,
        "protocol_sha256": PROTOCOL_SHA, "branch": BRANCH,
        "trial_ids": list(PRIMARY), "execution_order": list(ORDER),
    }
    for key, value in expected.items():
        if lock.get(key) != value:
            raise RuntimeError("EXECUTION_LOCK_FIELD_MISMATCH:" + key)
    for name in ("run_active_runtime_v3_paired_validation.py", "analyze_active_runtime_v3_paired_validation.py", "start_v3_paired_validation_tmux.sh"):
        if lock["harness_file_sha256"].get(name) != sha256_file(TASK_DIR / name):
            raise RuntimeError("EXECUTION_LOCK_HARNESS_HASH_MISMATCH:" + name)
    if require_committed:
        if git(checkout, "branch", "--show-current") != BRANCH:
            raise RuntimeError("EXECUTION_BRANCH_MISMATCH")
        if git(checkout, "status", "--porcelain", "--", TASK_REL):
            raise RuntimeError("EXECUTION_HARNESS_NOT_COMMITTED_CLEAN")
        if subprocess.run(["git", "-C", str(checkout), "ls-files", "--error-unmatch", str(LOCK_PATH.relative_to(checkout))], capture_output=True).returncode:
            raise RuntimeError("EXECUTION_LOCK_NOT_TRACKED")
    return lock

def static_preflight(checkout: Path, map_root: Path) -> dict[str, Any]:
    if subprocess.run(["git", "-C", str(checkout), "merge-base", "--is-ancestor", PARENT, "HEAD"]).returncode:
        raise RuntimeError("PR144_HEAD_NOT_ANCESTOR")
    protocol, input_lock, reference = frozen(checkout)
    if sha256_file(checkout / PROTOCOL_REL / "V3_PAIRED_VALIDATION_PROTOCOL.json") != PROTOCOL_SHA:
        raise RuntimeError("FROZEN_PROTOCOL_HASH_MISMATCH")
    if input_lock["protocol_freeze_commit"] != PROTOCOL_COMMIT:
        raise RuntimeError("FROZEN_PROTOCOL_COMMIT_MISMATCH")
    for name, expected in input_lock["task_artifact_sha256"].items():
        if sha256_file(checkout / PROTOCOL_REL / name) != expected:
            raise RuntimeError("FROZEN_PROTOCOL_ARTIFACT_DRIFT:" + name)
    verify_cohort(checkout, protocol)
    artifacts = verify_map(protocol, map_root)
    verify_reference(reference)
    verify_protected_diff(checkout)
    lock = verify_execution_lock(checkout, False)
    counts = lock["execution_counts_at_harness_freeze"]
    if any(counts.values()):
        raise RuntimeError("PRE_OUTCOME_EXECUTION_COUNTS_NONZERO")
    return {"status": "PASS", "parent": PARENT, "protocol_sha256": PROTOCOL_SHA, "map_artifacts": artifacts,
            "primary_count": 85, "development_excluded_count": 15, "reference_reuse_count": 85,
            "execution_counts": counts, "protected_diff": 0}

def load_module(path: Path, name: str) -> Any:
    spec = importlib.util.spec_from_file_location(name, path)
    if spec is None or spec.loader is None:
        raise RuntimeError("MODULE_IMPORT_UNAVAILABLE:" + str(path))
    module = importlib.util.module_from_spec(spec)
    previous = sys.modules.get(name)
    sys.modules[name] = module
    try:
        spec.loader.exec_module(module)
    finally:
        if previous is None: sys.modules.pop(name, None)
        else: sys.modules[name] = previous
    return module

def projected_smoke_protocol(checkout: Path, map_root: Path) -> dict[str, Any]:
    protocol, _, _ = frozen(checkout)
    smoke = load_json(checkout / "reproduction/smoke/active_runtime_smoke_v3/SMOKE_V3_PROTOCOL.json")
    smoke.update({"trial_ids": list(PRIMARY), "trial_order": list(ORDER), "maximum_completed_cycles_per_trial": 500,
                  "seed": 0, "map_relative_path": str(map_root.resolve()), "map_identity": protocol["map"]["identity"],
                  "map_artifacts": protocol["map"]["artifacts"]})
    smoke["environment"].update(protocol["environment"])
    smoke["dynamics"]["dt"] = protocol["controller_and_dynamics"]["dt"]
    return smoke

def configure_smoke(checkout: Path, map_root: Path) -> tuple[Any, dict[str, Any]]:
    smoke = load_module(checkout / "reproduction/smoke/active_runtime_smoke_v3/run_active_runtime_smoke_v3.py", "_v3_paired_smoke")
    projected = projected_smoke_protocol(checkout, map_root)
    original_verify = smoke.verify_source_and_map
    smoke.UPSTREAM = PARENT
    smoke.FIXED_TRIALS = PRIMARY
    smoke.TASK_DIR = TASK_DIR
    smoke.PROTOCOL_PATH = checkout / PROTOCOL_REL / "V3_PAIRED_VALIDATION_PROTOCOL.json"
    smoke.EXECUTION_LOCK_PATH = LOCK_PATH
    smoke.read_protocol = lambda: projected
    def verify(checkout_arg: Path, protocol_arg: dict[str, Any], require_execution_lock: bool = True):
        if require_execution_lock:
            verify_execution_lock(checkout_arg, True)
        return original_verify(checkout_arg, protocol_arg, False)
    smoke.verify_source_and_map = verify
    return smoke, projected

def _append_jsonl(path: Path, value: Any) -> None:
    with path.open("a", encoding="utf-8", newline="\n") as f:
        f.write(json.dumps(value, sort_keys=True, separators=(",", ":"), allow_nan=False) + "\n")
        f.flush()
        os.fsync(f.fileno())

def run_one(checkout: Path, output_dir: Path, map_root: Path, trial_id: int) -> int:
    if trial_id not in PRIMARY:
        raise RuntimeError("TRIAL_NOT_IN_FROZEN_PRIMARY_85")
    verify_execution_lock(checkout, True)
    smoke, _ = configure_smoke(checkout, map_root)
    raw = output_dir / "raw" / f"trial_{trial_id}"
    raw.mkdir(parents=True, exist_ok=False)
    observations = raw / "cycle_observations.jsonl"
    if str(checkout) not in sys.path:
        sys.path.insert(0, str(checkout))
    from reproduction.runtime.active_runtime_assurance_v2.active_cycle import ActiveCycleCoordinator
    original = ActiveCycleCoordinator.run_cycle
    def observed(self: Any, snapshot: Any, request: Any) -> Any:
        result = original(self, snapshot, request)
        receipt = result.commit_receipt
        row = {
            "trial_id": trial_id, "cycle_index": int(request.cycle_index), "pre_state": list(snapshot.state),
            "pre_state_identity": snapshot.identity.value, "committed": bool(result.committed), "boundary": bool(result.boundary),
            "post_state": None if result.next_state is None else list(result.next_state.state),
            "post_state_identity": None if result.next_state is None else result.next_state.identity.value,
            "selected_action_identity": None if result.final_supervisor_decision is None or result.final_supervisor_decision.selected_action is None else result.final_supervisor_decision.selected_action.identity.value,
            "executed_action_identity": None if receipt is None else receipt.executed_action_identity.value,
            "executed_vector": None if receipt is None else list(receipt.exact_vector),
            "action_role": None if receipt is None else receipt.action_role.value,
        }
        _append_jsonl(observations, row)
        return result
    ActiveCycleCoordinator.run_cycle = observed
    try:
        code = int(smoke.run_one(checkout, output_dir, trial_id))
    finally:
        ActiveCycleCoordinator.run_cycle = original
    summary_path = raw / "trial_summary.json"
    summary = load_json(summary_path)
    helpers = smoke._load_v2_helpers(checkout)
    start, goal = helpers.trial_geometry(trial_id)
    initial = [float(v) for v in start] + [0.0, 0.0, 0.0]
    target = [float(v) for v in goal] + [0.0, 0.0, 0.0]
    audit = summary.get("v3_wiring_audit", {})
    trace = raw / "runtime_trace.jsonl"
    trace_lock = raw / "runtime_trace_lock.json"
    summary.update({
        "schema": "ACTIVE_RUNTIME_V3_PAIRED_TRIAL_SUMMARY_V1", "trial_id": trial_id,
        "source_git_identity": git(checkout, "rev-parse", "HEAD"), "protocol_identity": PROTOCOL_SHA,
        "map_identity": frozen(checkout)[0]["map"]["identity"], "checkpoint_identity": "ac14f5ced354c93f26cf92404540712eff65bd02554d9e9ed0332508e290382d",
        "start_state": initial, "goal_state": target, "start_state_identity": summary.get("initial_state_identity"),
        "seed": 0, "dt": 0.05, "max_completed_cycles": 500,
        "execution_complete": code == 0 and summary.get("hard_blocker") is None,
        "runtime_trace_sha256": sha256_file(trace) if trace.is_file() else None,
        "runtime_trace_lock_sha256": sha256_file(trace_lock) if trace_lock.is_file() else None,
        "cycle_observations_sha256": sha256_file(observations) if observations.is_file() else None,
        "plant_commits": summary.get("plant_commit_count", 0),
        "primary_count": summary.get("primary_navigation_commit_count", 0),
        "alternative_count": summary.get("alternative_navigation_commit_count", 0),
        "backup_count": summary.get("retained_backup_commit_count", 0),
        "terminal_count": summary.get("terminal_commit_count", 0),
        "boundary_count": summary.get("assurance_boundary_count", 0),
        "actuator_violation_count": summary.get("action_bound_violation_count", 0),
        "unresolved_plant_execution_state_count": summary.get("plant_outcome_unknown_count", 0),
        "observed_runtime_hard_radius_set_q": [audit.get("hard_runtime_radius_q")],
        "historical_shell_runtime_authority_observed": audit.get("historical_diagnostic_runtime_authority", True),
        "historical_shell_intrusion_count": 0 if audit.get("historical_diagnostic_runtime_authority") is False else 1,
        "FORBIDDEN_DIAGNOSTIC_AUTHORITY_EVENT_COUNT": 0 if audit.get("historical_diagnostic_runtime_authority") is False else 1,
        "evaluation_eligible": code == 0 and summary.get("hard_blocker") is None and summary.get("finalization_status") == "FINALIZED",
    })
    write_json(summary_path, summary)
    return code

def freeze_trial_evidence(raw: Path) -> dict[str, Any]:
    names = ("trial_summary.json", "runtime_trace.jsonl", "runtime_trace_lock.json", "cycle_observations.jsonl", "process_exit_code.txt", "gpu_released.txt")
    files = {}
    for name in names:
        path = raw / name
        if not path.is_file(): raise RuntimeError("TRIAL_EVIDENCE_FILE_MISSING:" + name)
        files[name] = {"size": path.stat().st_size, "sha256": sha256_file(path)}
    lock = {"schema": "ACTIVE_RUNTIME_V3_PAIRED_RAW_EVIDENCE_LOCK_V1", "trial_id": int(raw.name.split("_")[-1]), "files": files, "immutable": True}
    lock["identity"] = "active-v3-paired-raw:sha256:" + semantic_sha256(lock)
    write_json(raw / "ACTIVE_V3_RAW_EVIDENCE_LOCK.json", lock)
    return lock

def complete_evidence(output_dir: Path, trial_id: int) -> bool:
    raw = output_dir / "raw" / f"trial_{trial_id}"
    lock_path = raw / "ACTIVE_V3_RAW_EVIDENCE_LOCK.json"
    if not lock_path.is_file(): return False
    try:
        lock = load_json(lock_path)
        for name, expected in lock["files"].items():
            path = raw / name
            if path.stat().st_size != expected["size"] or sha256_file(path) != expected["sha256"]: return False
        summary = load_json(raw / "trial_summary.json")
        trace_lock = load_json(raw / "runtime_trace_lock.json")
        lines = (raw / "runtime_trace.jsonl").read_text(encoding="utf-8").splitlines()
        integrity = sum(int(summary.get(field, 0)) for field in INTEGRITY_FIELDS)
        return (summary.get("trial_id") == trial_id and summary.get("process_exit_code") == 0 and
                (raw / "process_exit_code.txt").read_text().strip() == "0" and (raw / "gpu_released.txt").read_text().strip() == "true" and
                summary.get("evaluation_eligible") is True and summary.get("finalization_status") == "FINALIZED" and
                summary.get("completed_cycles") == summary.get("trace_record_count") == trace_lock.get("record_count") == len(lines) and
                summary.get("observed_runtime_hard_radius_set_q") == [0.015] and
                summary.get("historical_shell_runtime_authority_observed") is False and integrity == 0)
    except (OSError, KeyError, TypeError, ValueError, json.JSONDecodeError):
        return False

def gpu_preflight(checkout: Path, output_dir: Path, map_root: Path) -> int:
    verify_execution_lock(checkout, True)
    smoke, _ = configure_smoke(checkout, map_root)
    code = int(smoke.run_preflight(checkout, output_dir))
    result = load_json(output_dir / "raw" / "gpu_preflight.json")
    result.update({"schema": "ACTIVE_RUNTIME_V3_PAIRED_GPU_PREFLIGHT_V1", "plant_cycles_executed": 0,
                   "protocol_sha256": PROTOCOL_SHA, "hard_radius_q": 0.015, "historical_0p025_runtime_authority": False})
    write_json(output_dir / "raw" / "gpu_preflight.json", result)
    return code

def summarize_integrity(output_dir: Path) -> dict[str, Any]:
    complete = [trial for trial in ORDER if complete_evidence(output_dir, trial)]
    totals = {field: 0 for field in INTEGRITY_FIELDS}
    cycles = traces = locks = 0
    for trial in complete:
        raw = output_dir / "raw" / f"trial_{trial}"
        s = load_json(raw / "trial_summary.json")
        l = load_json(raw / "runtime_trace_lock.json")
        cycles += int(s["completed_cycles"]); traces += len((raw / "runtime_trace.jsonl").read_text().splitlines()); locks += int(l["record_count"])
        for field in totals: totals[field] += int(s.get(field, 0))
    result = {"schema": "ACTIVE_RUNTIME_V3_PAIRED_COLLECTION_INTEGRITY_SUMMARY_V1", "completed_trials": len(complete),
              "expected_trials": 85, "completed_trial_ids_in_frozen_order": complete, "completed_cycles": cycles,
              "trace_records": traces, "locked_records": locks, "trace_cardinality_pass": cycles == traces == locks,
              "integrity_totals": totals, "scientific_outcomes_read": False, "aggregate_analysis_performed": False}
    write_json(output_dir / "ACTIVE_V3_COLLECTION_INTEGRITY_SUMMARY.json", result)
    print(json.dumps(result, sort_keys=True))
    return result

def run_batch(checkout: Path, output_dir: Path, map_root: Path) -> int:
    verify_execution_lock(checkout, True)
    smoke, protocol = configure_smoke(checkout, map_root)
    smoke.verify_source_and_map(checkout, protocol)
    for trial in ORDER:
        if complete_evidence(output_dir, trial):
            print(f"TRIAL_{trial}_IMMUTABLE_COMPLETE_SKIP", flush=True); continue
        raw = output_dir / "raw" / f"trial_{trial}"
        if raw.exists():
            raise RuntimeError(f"INCOMPLETE_EXISTING_TRIAL_EVIDENCE_REVIEW_REQUIRED:{trial}")
        env = os.environ.copy(); env.update(protocol["environment"])
        command = [protocol["environment"]["python"], str(Path(__file__).resolve()), "--one", str(trial), "--checkout", str(checkout), "--output-dir", str(output_dir), "--map-source-root", str(map_root)]
        stdout_path = output_dir / f"trial_{trial}_launcher_stdout.tmp"
        stderr_path = output_dir / f"trial_{trial}_launcher_stderr.tmp"
        with stdout_path.open("w", encoding="utf-8", newline="\n") as stdout, stderr_path.open("w", encoding="utf-8", newline="\n") as stderr:
            process = subprocess.Popen(command, env=env, stdout=stdout, stderr=stderr, text=True); code = process.wait()
        raw = output_dir / "raw" / f"trial_{trial}"
        if raw.is_dir():
            stdout_path.replace(raw / "stdout.log"); stderr_path.replace(raw / "stderr.log")
        released = smoke.gpu_pid_released(process.pid)
        (raw / "process_exit_code.txt").write_text(f"{code}\n", encoding="utf-8", newline="\n")
        (raw / "gpu_released.txt").write_text(("true" if released else "false") + "\n", encoding="utf-8", newline="\n")
        try:
            freeze_trial_evidence(raw)
        except RuntimeError as exc:
            print(f"TRIAL_{trial}_PARTIAL_EVIDENCE_PRESERVED:{exc}", flush=True)
            summarize_integrity(output_dir)
            return code or 2
        if code or not released or not complete_evidence(output_dir, trial):
            summarize_integrity(output_dir)
            print(f"TRIAL_{trial}_HARD_STOP", flush=True); return code or 2
        summarize_integrity(output_dir)
        print(f"TRIAL_{trial}_PASS", flush=True)
    print("COLLECTION_COMPLETE_OR_STOPPED_REVIEW_BEFORE_ANALYSIS", flush=True)
    return 0

def main() -> int:
    ap = argparse.ArgumentParser()
    mode = ap.add_mutually_exclusive_group(required=True)
    mode.add_argument("--static-preflight", action="store_true")
    mode.add_argument("--gpu-preflight", action="store_true")
    mode.add_argument("--one", type=int)
    mode.add_argument("--batch", action="store_true")
    mode.add_argument("--summarize-integrity", action="store_true")
    ap.add_argument("--checkout", type=Path, required=True)
    ap.add_argument("--output-dir", type=Path, required=True)
    ap.add_argument("--map-source-root", type=Path, default=DEFAULT_MAP_ROOT)
    a = ap.parse_args(); checkout = a.checkout.resolve(strict=True); output = a.output_dir.resolve(); map_root = a.map_source_root.resolve(strict=True)
    if a.static_preflight:
        print(json.dumps(static_preflight(checkout, map_root), sort_keys=True)); print("PASS_ACTIVE_RUNTIME_V3_PAIRED_STATIC_PREFLIGHT"); return 0
    if a.gpu_preflight: return gpu_preflight(checkout, output, map_root)
    if a.one is not None: return run_one(checkout, output, map_root, a.one)
    if a.batch: return run_batch(checkout, output, map_root)
    summarize_integrity(output); return 0

if __name__ == "__main__":
    raise SystemExit(main())
