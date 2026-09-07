#!/usr/bin/env python3
"""One-shot serial executor for the frozen V2R1 BYPASS equivalence protocol."""

from __future__ import annotations

import argparse
from datetime import datetime, timezone
import hashlib
import json
import os
from pathlib import Path
import subprocess
import sys
from typing import Any


ORDER = (50, 10, 30, 70, 90)
ARMS = ("REFERENCE_CONTROL_PLANT", "ACTIVE_HARNESS_BYPASS")


def now() -> str:
    return datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def load(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def write_json(path: Path, value: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(value, indent=2, sort_keys=True, allow_nan=False) + "\n", encoding="utf-8", newline="\n")


def append_ledger(path: Path, value: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("a", encoding="utf-8", newline="\n") as handle:
        handle.write(json.dumps(value, sort_keys=True, separators=(",", ":"), allow_nan=False) + "\n")
        handle.flush()
        os.fsync(handle.fileno())


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--checkout", required=True, type=Path)
    parser.add_argument("--task-bundle", required=True, type=Path)
    parser.add_argument("--output-root", required=True, type=Path)
    parser.add_argument("--python", required=True, type=Path)
    args = parser.parse_args()
    checkout, bundle, root = args.checkout.resolve(), args.task_bundle.resolve(), args.output_root.resolve()
    if root.exists():
        raise FileExistsError(f"OUTPUT_ROOT_ALREADY_EXISTS:{root}")
    root.mkdir(parents=True)
    for sub in ("raw/reference", "raw/bypass", "pairs", "logs"):
        (root / sub).mkdir(parents=True, exist_ok=True)
    input_lock = bundle / "BYPASS_EQUIVALENCE_V2R1_INPUT_LOCK.json"
    execution_lock = bundle / "BYPASS_EQUIVALENCE_V2R1_EXECUTION_LOCK.json"
    input_sha, execution_sha = sha256_file(input_lock), sha256_file(execution_lock)
    ledger = root / "REAL_ARM_EXECUTION_LEDGER_V2R1.jsonl"
    append_ledger(ledger, {"event_type": "LEDGER_INITIALIZED", "timestamp": now(), "counter_start": 0, "hard_cap": 10, "correction_quota": 0, "input_lock_sha256": input_sha, "execution_lock_sha256": execution_sha})
    sys.path.insert(0, str(checkout))
    sys.path.insert(0, str(bundle))
    from compare_v2r1 import compare_pair
    from reproduction.validation.bypass_qa_trace_identity_repair_v2.canonical_trial_identity import make_canonical_trial_identity

    real_count = 0
    pair_results: list[dict[str, Any]] = []
    blocked: dict[str, Any] | None = None
    for trial_id in ORDER:
        for arm in ARMS:
            if real_count >= 10:
                blocked = {"status": "BLOCKED_REFROZEN_BYPASS_EQUIVALENCE_BY_PROTOCOL_VIOLATION", "reason": "hard cap would be exceeded"}
                break
            ordinal = real_count + 1
            canonical_id = make_canonical_trial_identity(trial_id).canonical_trial_id
            arm_dir = "reference" if arm == "REFERENCE_CONTROL_PLANT" else "bypass"
            output_dir = root / "raw" / arm_dir / f"trial_{trial_id}"
            runner = checkout / "reproduction/validation/active_harness_bypass_equivalence_v2" / ("run_reference_arm.py" if arm == "REFERENCE_CONTROL_PLANT" else "run_bypass_arm.py")
            command = [str(args.python), "-B", str(runner), "--trial-id", str(trial_id), "--checkout", str(checkout), "--output-dir", str(output_dir), "--seed", "0"]
            started = now()
            append_ledger(ledger, {"event_type": "REAL_ARM_PLANNED", "execution_ordinal": ordinal, "native_trial_id": trial_id, "canonical_trial_id": canonical_id, "arm": arm, "start_timestamp": started, "input_lock_sha256": input_sha, "execution_lock_sha256": execution_sha, "classification": "PENDING_REAL_ARM_EXECUTION"})
            env = os.environ.copy()
            env.update({"CUDA_VISIBLE_DEVICES": "1", "PYTHONNOUSERSITE": "1", "PYTHONDONTWRITEBYTECODE": "1", "PYTHONHASHSEED": "0", "CUBLAS_WORKSPACE_CONFIG": ":4096:8"})
            proc = subprocess.Popen(command, cwd=checkout, env=env, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
            stdout, stderr = proc.communicate()
            ended = now()
            label = f"{ordinal:02d}_trial_{trial_id}_{arm.lower()}"
            (root / "logs" / f"{label}.stdout.log").write_text(stdout, encoding="utf-8", newline="\n")
            (root / "logs" / f"{label}.stderr.log").write_text(stderr, encoding="utf-8", newline="\n")
            summary_path = output_dir / f"trial_{trial_id}_summary.json"
            env_path = output_dir / "environment_identity.json"
            summary = load(summary_path) if summary_path.is_file() else {}
            env_identity = load(env_path).get("pairing_identity") if env_path.is_file() else None
            solver_steps = int(summary.get("attempted_step_count", 0))
            commits = int(summary.get("plant_commit_count", 0))
            trace_path = output_dir / f"trial_{trial_id}_trace_lock.json"
            finalized = 1 if trace_path.is_file() else 0
            classification = "REAL_ARM_EXECUTION"
            if solver_steps == 0 and commits == 0 and finalized == 0 and proc.returncode != 0:
                classification = "INFRA_ONLY_NOT_COUNTED_AS_REAL_ARM_EXECUTION"
            else:
                real_count += 1
            append_ledger(ledger, {
                "event_type": "REAL_ARM_COMPLETED", "execution_ordinal": ordinal,
                "native_trial_id": trial_id, "canonical_trial_id": canonical_id, "arm": arm,
                "process_id": proc.pid, "start_timestamp": started, "end_timestamp": ended,
                "environment_identity": env_identity, "input_lock_sha256": input_sha,
                "execution_lock_sha256": execution_sha, "exit_code": proc.returncode,
                "solver_step_count": solver_steps, "plant_commit_count": commits,
                "finalized_trace_count": finalized,
                "trace_lock_sha256": sha256_file(trace_path) if trace_path.is_file() else None,
                "termination_reason": summary.get("termination_reason"),
                "termination_step": summary.get("termination_step"), "classification": classification,
                "real_execution_counter_after": real_count,
            })
            if proc.returncode != 0:
                blocked = {"status": "BLOCKED_REFROZEN_BYPASS_EQUIVALENCE_BY_SENTINEL_INCOMPLETE_PAIR" if trial_id == 50 else "BLOCKED_REFROZEN_BYPASS_EQUIVALENCE_BY_PROTOCOL_VIOLATION", "reason": f"arm exit {proc.returncode}", "trial_id": trial_id, "arm": arm}
                break
        if blocked:
            break
        reference_dir = root / "raw/reference" / f"trial_{trial_id}"
        bypass_dir = root / "raw/bypass" / f"trial_{trial_id}"
        comparison = compare_pair(reference_dir, bypass_dir, trial_id)
        write_json(root / "pairs" / f"pair_{trial_id}_comparison.json", comparison)
        pair_results.append(comparison)
        if comparison["verdict"] != "PASS":
            first = comparison.get("first_mismatch") or {}
            taxonomy = first.get("taxonomy")
            mapping = {
                "M_REFERENCE_TO_SUPPLIED_ACTION_BITS": "BLOCKED_REFROZEN_BYPASS_EQUIVALENCE_BY_ACTION_MISMATCH",
                "M_SUPPLIED_TO_SELECTED_ACTION": "BLOCKED_REFROZEN_BYPASS_EQUIVALENCE_BY_ACTION_MISMATCH",
                "M_SELECTED_TO_EXECUTED_ACTION": "BLOCKED_REFROZEN_BYPASS_EQUIVALENCE_BY_ACTION_MISMATCH",
                "M_POST_STATE_BITS": "BLOCKED_REFROZEN_BYPASS_EQUIVALENCE_BY_STATE_MISMATCH",
                "M_SOLVER_BRANCH": "BLOCKED_REFROZEN_BYPASS_EQUIVALENCE_BY_BRANCH_MISMATCH",
                "M_TERMINATION_REASON": "BLOCKED_REFROZEN_BYPASS_EQUIVALENCE_BY_TERMINATION_MISMATCH",
                "M_TERMINATION_STEP": "BLOCKED_REFROZEN_BYPASS_EQUIVALENCE_BY_TERMINATION_MISMATCH",
                "M_TRACE_INCOMPLETE": "BLOCKED_REFROZEN_BYPASS_EQUIVALENCE_BY_TRACE_FAILURE",
                "M_UNEXPECTED_HARNESS_INTERVENTION": "BLOCKED_REFROZEN_BYPASS_EQUIVALENCE_BY_HARNESS_INTERVENTION",
            }
            blocked = {"status": mapping.get(taxonomy, "BLOCKED_REFROZEN_BYPASS_EQUIVALENCE_BY_PROTOCOL_VIOLATION"), "reason": taxonomy, "trial_id": trial_id}
            break

    total_mismatches = sum(int(item["mismatch_count"]) for item in pair_results)
    summary = {
        "schema": "BYPASS_EQUIVALENCE_V2R1_SUMMARY",
        "completed_pairs": len(pair_results), "passed_pairs": sum(item["verdict"] == "PASS" for item in pair_results),
        "real_execution_count": real_count,
        "infra_only_invocation_count": sum(json.loads(line).get("classification") == "INFRA_ONLY_NOT_COUNTED_AS_REAL_ARM_EXECUTION" for line in ledger.read_text(encoding="utf-8").splitlines()),
        "total_reference_steps": sum(item["reference_row_count"] for item in pair_results),
        "total_bypass_steps": sum(item["bypass_row_count"] for item in pair_results),
        "total_compared_steps": sum(item["total_compared_steps"] for item in pair_results),
        "action_mismatch_count": sum(item["mismatch_counts"]["M_REFERENCE_TO_SUPPLIED_ACTION_BITS"] for item in pair_results),
        "supplied_selected_mismatch_count": sum(item["mismatch_counts"]["M_SUPPLIED_TO_SELECTED_ACTION"] for item in pair_results),
        "selected_executed_mismatch_count": sum(item["mismatch_counts"]["M_SELECTED_TO_EXECUTED_ACTION"] for item in pair_results),
        "state_mismatch_count": sum(item["mismatch_counts"]["M_POST_STATE_BITS"] for item in pair_results),
        "branch_mismatch_count": sum(item["mismatch_counts"]["M_SOLVER_BRANCH"] for item in pair_results),
        "termination_mismatch_count": sum(item["mismatch_counts"]["M_TERMINATION_REASON"] + item["mismatch_counts"]["M_TERMINATION_STEP"] for item in pair_results),
        "trace_incomplete_count": sum(item["mismatch_counts"]["M_TRACE_INCOMPLETE"] for item in pair_results),
        "intervention_count": sum(item["active_intervention_count"] for item in pair_results),
        "token_mutation_count": sum(item["token_mutation_count"] for item in pair_results),
        "protocol_deviation_count": 0, "total_mismatch_count": total_mismatches,
        "first_mismatch": next((item["first_mismatch"] for item in pair_results if item["first_mismatch"]), blocked),
        "sentinel_verdict": next((item["verdict"] for item in pair_results if item["native_trial_id"] == 50), "NOT_COMPLETED"),
        "active_runtime_on_execution_count": 0, "scientific_oracle_execution_count": 0, "official100_execution_count": 0,
        "exact_equivalence_verdict": "ACTIVE_HARNESS_BYPASS_EQUIVALENT_TO_REFERENCE_UNDER_V2R1_QA" if len(pair_results) == 5 and total_mismatches == 0 and real_count == 10 else "NOT_ESTABLISHED",
        "FINAL_STATUS": "PASS_REFROZEN_BYPASS_EQUIVALENCE_V2R1" if len(pair_results) == 5 and total_mismatches == 0 and real_count == 10 else blocked["status"] if blocked else "BLOCKED_REFROZEN_BYPASS_EQUIVALENCE_BY_PROTOCOL_VIOLATION",
    }
    write_json(root / "BYPASS_EQUIVALENCE_V2R1_SUMMARY.json", summary)
    write_json(root / "mismatch_register.json", {"schema": "BYPASS_EQUIVALENCE_V2R1_MISMATCH_REGISTER", "mismatch_count": total_mismatches, "first_mismatch": summary["first_mismatch"]})
    print(json.dumps(summary, sort_keys=True), flush=True)
    return 0 if summary["FINAL_STATUS"] == "PASS_REFROZEN_BYPASS_EQUIVALENCE_V2R1" else 2


if __name__ == "__main__":
    raise SystemExit(main())

