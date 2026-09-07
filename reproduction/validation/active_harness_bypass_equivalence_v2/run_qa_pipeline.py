#!/usr/bin/env python3
"""Serial Q1/Q2 fail-closed execution for frozen BYPASS equivalence pairs."""

from __future__ import annotations

import csv
from datetime import datetime, timezone
import json
import os
from pathlib import Path
import subprocess
import sys
from typing import Any

from compare_bypass_equivalence import compare_trial, write_csv, write_json


ORDER = (("Q1", 50), ("Q2", 10), ("Q2", 30), ("Q2", 70), ("Q2", 90))
ARMS = ("REFERENCE_CONTROL_PLANT", "ACTIVE_HARNESS_BYPASS")


def now() -> str:
    return datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")


def persist_manifest(path: Path, records: list[dict[str, Any]]) -> None:
    fields = ["execution_index", "phase", "trial_id", "arm", "repo_sha", "environment_id", "device_id", "start_hash", "goal_hash", "output_path", "process_exit_code", "started_at", "completed_at", "comparison_status"]
    with path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=fields)
        writer.writeheader(); writer.writerows(records)


def load(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def run_arm(python: Path, task_code: Path, checkout: Path, root: Path, phase: str, trial_id: int, arm: str, execution_index: int) -> tuple[dict[str, Any], int]:
    arm_dir_name = "reference" if arm == "REFERENCE_CONTROL_PLANT" else "bypass"
    output_dir = root / "artifacts" / arm_dir_name / f"trial_{trial_id}"
    script = task_code / ("run_reference_arm.py" if arm == "REFERENCE_CONTROL_PLANT" else "run_bypass_arm.py")
    command = [str(python), "-B", str(script), "--trial-id", str(trial_id), "--checkout", str(checkout), "--output-dir", str(output_dir), "--seed", "0"]
    env = os.environ.copy()
    env.update({"CUDA_VISIBLE_DEVICES": "1", "PYTHONHASHSEED": "0", "PYTHONDONTWRITEBYTECODE": "1", "CUBLAS_WORKSPACE_CONFIG": ":4096:8"})
    started = now()
    result = subprocess.run(command, cwd=checkout, env=env, text=True, capture_output=True, check=False)
    completed = now()
    logs = root / "run_logs"; logs.mkdir(exist_ok=True)
    label = f"{execution_index:02d}_{phase.lower()}_trial_{trial_id}_{arm.lower()}"
    (logs / f"{label}.stdout.log").write_text(result.stdout, encoding="utf-8", newline="\n")
    (logs / f"{label}.stderr.log").write_text(result.stderr, encoding="utf-8", newline="\n")
    record = {
        "execution_index": execution_index, "phase": phase, "trial_id": trial_id, "arm": arm,
        "repo_sha": subprocess.run(["git", "rev-parse", "HEAD"], cwd=checkout, check=True, text=True, capture_output=True).stdout.strip(),
        "environment_id": "UNAVAILABLE_ON_FAILED_ARM", "device_id": "physical:1/visible:0",
        "start_hash": "UNAVAILABLE_ON_FAILED_ARM", "goal_hash": "UNAVAILABLE_ON_FAILED_ARM",
        "output_path": str(output_dir), "process_exit_code": result.returncode,
        "started_at": started, "completed_at": completed, "comparison_status": "NOT_COMPARED",
    }
    summary_path = output_dir / f"trial_{trial_id}_summary.json"
    env_path = output_dir / "environment_identity.json"
    if summary_path.is_file() and env_path.is_file():
        summary, environment = load(summary_path), load(env_path)
        record.update({
            "environment_id": environment["pairing_identity"],
            "start_hash": __import__("hashlib").sha256(json.dumps(summary["initial_state_bits"], separators=(",", ":")).encode()).hexdigest(),
            "goal_hash": __import__("hashlib").sha256(json.dumps(summary["goal_bits"], separators=(",", ":")).encode()).hexdigest(),
        })
    return record, result.returncode


def main() -> int:
    import argparse
    parser = argparse.ArgumentParser()
    parser.add_argument("--checkout", required=True, type=Path)
    parser.add_argument("--task-code", required=True, type=Path)
    parser.add_argument("--output-root", required=True, type=Path)
    parser.add_argument("--python", required=True, type=Path)
    args = parser.parse_args()
    root = args.output_root.resolve()
    if root.exists():
        raise FileExistsError(root)
    root.mkdir(parents=True)
    for name in ("artifacts/reference", "artifacts/bypass", "comparison", "run_logs"):
        (root / name).mkdir(parents=True, exist_ok=True)
    records: list[dict[str, Any]] = []
    trials: list[dict[str, Any]] = []
    all_steps: list[dict[str, Any]] = []
    mismatch = None
    execution_index = 0
    for phase, trial_id in ORDER:
        pair_records = []
        for arm in ARMS:
            execution_index += 1
            record, exit_code = run_arm(args.python, args.task_code, args.checkout, root, phase, trial_id, arm, execution_index)
            records.append(record); pair_records.append(record)
            persist_manifest(root / "BYPASS_QA_EXECUTION_MANIFEST.csv", records)
            if exit_code != 0:
                mismatch = {"taxonomy": "M_BYPASS_HARNESS_INTERVENTION" if arm == "ACTIVE_HARNESS_BYPASS" else "M_REF_ADAPTER_DRIFT", "trial_id": trial_id, "arm": arm, "exit_code": exit_code}
                break
        if mismatch is not None:
            break
        ref_dir = root / "artifacts/reference" / f"trial_{trial_id}"
        byp_dir = root / "artifacts/bypass" / f"trial_{trial_id}"
        ref_env, byp_env = load(ref_dir / "environment_identity.json"), load(byp_dir / "environment_identity.json")
        if ref_env["pairing_identity"] != byp_env["pairing_identity"]:
            summary, step_rows = ({"trial_id": trial_id, "trial_verdict": "FAIL", "first_mismatch": {"taxonomy": "M_UPSTREAM_SOURCE_DRIFT", "reason": "environment pairing mismatch"}}, [])
        else:
            summary, step_rows = compare_trial(ref_dir, byp_dir, trial_id)
        trials.append(summary); all_steps.extend(step_rows)
        status = summary["trial_verdict"]
        for record in pair_records:
            record["comparison_status"] = status
        persist_manifest(root / "BYPASS_QA_EXECUTION_MANIFEST.csv", records)
        write_json(root / "comparison" / f"trial_{trial_id}_equivalence.json", summary)
        write_csv(root / "comparison" / f"trial_{trial_id}_per_step.csv", step_rows)
        if status != "PASS":
            mismatch = summary.get("first_mismatch") or {"taxonomy": "M_UNCLASSIFIED", "trial_id": trial_id}
            break

    write_csv(root / "comparison" / "per_step_equivalence.csv", all_steps)
    write_json(root / "comparison" / "per_trial_equivalence.json", {"trials": trials})
    completed = sum(item.get("trial_verdict") == "PASS" for item in trials)
    total_rows = len(all_steps)
    summary = {
        "schema": "BYPASS_EQUIVALENCE_SUMMARY_V2",
        "frozen_trial_count_planned": 5,
        "completed_trial_count": completed,
        "exact_pass_count": completed,
        "failed_count": 0 if mismatch is None else 1,
        "real_execution_count": len(records),
        "total_compared_steps": total_rows,
        "action_exact_rate": 1.0 if total_rows and all(row.get("action_bits_equal") is True for row in all_steps) else (0.0 if total_rows else None),
        "selected_executed_exact_rate": 1.0 if total_rows and all(row.get("selected_executed_equal") is True for row in all_steps) else (0.0 if total_rows else None),
        "state_exact_rate": 1.0 if total_rows and all(row.get("state_bits_equal") is True for row in all_steps) else (0.0 if total_rows else None),
        "termination_exact_rate": completed / len(trials) if trials else None,
        "active_intervention_count": sum(item.get("active_intervention_count", 0) for item in trials),
        "token_mutation_count": sum(item.get("token_mutation_count", 0) for item in trials),
        "trace_lock_count": sum(bool(item.get("trace_lock_present")) for item in trials),
        "first_mismatch": mismatch,
        "mismatch_taxonomy": [] if mismatch is None else [mismatch.get("taxonomy", "M_UNCLASSIFIED")],
        "sentinel_verdict": next((item["trial_verdict"] for item in trials if item["trial_id"] == 50), "NOT_COMPLETED"),
        "outcome_tolerance_changed": False,
        "scientific_oracle_execution_count": 0,
        "active_runtime_on_execution_count": 0,
        "official100_execution_count": 0,
        "FINAL_STATUS": "PASS_ACTIVE_HARNESS_BYPASS_EQUIVALENCE_V2" if mismatch is None and completed == 5 else "BLOCKED_ACTIVE_HARNESS_BYPASS_EQUIVALENCE",
    }
    write_json(root / "comparison" / "summary.json", summary)
    write_json(root / "BYPASS_EQUIVALENCE_MISMATCH_REGISTER.json", {"schema": "BYPASS_EQUIVALENCE_MISMATCH_REGISTER_V2", "mismatch_count": 0 if mismatch is None else 1, "first_mismatch": mismatch})
    print(json.dumps(summary, sort_keys=True), flush=True)
    return 0 if summary["FINAL_STATUS"] == "PASS_ACTIVE_HARNESS_BYPASS_EQUIVALENCE_V2" else 2


if __name__ == "__main__":
    raise SystemExit(main())
