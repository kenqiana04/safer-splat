#!/usr/bin/env python3
"""Serial, resumable, outcome-blind formal cohort scheduler."""

from __future__ import annotations

import argparse
import subprocess
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from collection_common import (
    DATA_ROLE, PROTOCOL_SHA256, atomic_write_json, formal_run_id, load_json,
    verify_execution_lock,
)


def now() -> str:
    return datetime.now(timezone.utc).isoformat()


def default_progress() -> dict[str, Any]:
    return {
        "schema_version": "L2_H1_FORMAL_COLLECTION_PROGRESS_V1",
        "data_role": DATA_ROLE,
        "protocol_sha256": PROTOCOL_SHA256,
        "state": "READY",
        "completed_trial_count": 0,
        "running_trial_count": 0,
        "failed_pre_data_attempt_count": 0,
        "failed_post_data_attempt_count": 0,
        "trials": [],
        "scientific_outcome_aggregation_count": 0,
        "updated_at_utc": now(),
    }


def run(command: list[str], log: Path) -> int:
    log.parent.mkdir(parents=True, exist_ok=True)
    with log.open("ab") as handle:
        completed = subprocess.run(command, stdout=handle, stderr=subprocess.STDOUT, check=False)
    return completed.returncode


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--checkout", type=Path, required=True)
    parser.add_argument("--task-root", type=Path, required=True)
    parser.add_argument("--python", required=True)
    parser.add_argument("--execution-lock", type=Path, required=True)
    args = parser.parse_args()
    script_dir = Path(__file__).resolve().parent
    lock = verify_execution_lock(args.execution_lock, script_dir)
    progress_path = args.task_root / "formal_collection_progress.json"
    progress = load_json(progress_path) if progress_path.exists() else default_progress()
    if progress.get("protocol_sha256") != PROTOCOL_SHA256 or progress.get("scientific_outcome_aggregation_count") != 0:
        raise RuntimeError("progress identity/scope mismatch")
    if progress.get("state") in {"LOCKED", "STOPPED_POST_DATA_FAILURE"}:
        print(f"collection_state={progress['state']}")
        return 0 if progress["state"] == "LOCKED" else 3
    completed_trials = {int(row["trial_id"]): row for row in progress["trials"] if row.get("state") == "PASSED_OUTCOME_BLIND_QC"}

    for trial_id in range(100):
        if trial_id in completed_trials:
            continue
        prior = [row for row in progress["trials"] if int(row["trial_id"]) == trial_id]
        attempts_used = {int(row["attempt_id"]) for row in prior}
        attempt_id = 0 if 0 not in attempts_used else 1
        if attempt_id == 1:
            zero_data_prior = any(
                row.get("state") == "FAILED_PRE_DATA_INFRASTRUCTURE"
                and row.get("intended_step_count") == row.get("capture_count") == row.get("result_record_count") == 0
                for row in prior
            )
            if not zero_data_prior:
                raise RuntimeError("retry authorization absent")
        run_id = formal_run_id(trial_id, attempt_id)
        record = {
            "trial_id": trial_id, "attempt_id": attempt_id, "run_id": run_id,
            "state": "RUNNING", "started_at_utc": now(),
        }
        progress["trials"].append(record)
        progress.update({"state": "RUNNING", "running_trial_count": 1, "updated_at_utc": now()})
        atomic_write_json(progress_path, progress)
        attempt_root = args.task_root / "formal-v1" / f"trial-{trial_id:03d}" / f"attempt-{attempt_id}"
        runner_command = [
            args.python, "-B", str(script_dir / "run_one_formal_trial.py"),
            "--checkout", str(args.checkout), "--task-root", str(args.task_root), "--python", args.python,
            "--trial-id", str(trial_id), "--attempt-id", str(attempt_id), "--execution-lock", str(args.execution_lock),
        ]
        runner_rc = run(runner_command, args.task_root / "scheduler.log")
        process_path = attempt_root / "process_result.json"
        process = load_json(process_path) if process_path.exists() else {
            "exit_code": runner_rc, "intended_step_count": 0, "capture_count": 0, "result_record_count": 0, "scientific_row_count": 0,
        }
        record.update({key: int(process.get(key, 0)) for key in ("intended_step_count", "capture_count", "result_record_count", "scientific_row_count")})
        record["exit_code"] = int(process.get("exit_code", runner_rc))
        any_data = any(record[key] > 0 for key in ("intended_step_count", "capture_count", "result_record_count", "scientific_row_count"))
        if runner_rc != 0:
            record["finished_at_utc"] = now()
            progress["running_trial_count"] = 0
            if not any_data and attempt_id == 0:
                record["state"] = "FAILED_PRE_DATA_INFRASTRUCTURE"
                progress["failed_pre_data_attempt_count"] += 1
                progress["state"] = "READY_RETRY_PRE_DATA"
                atomic_write_json(progress_path, progress)
                continue
            record["state"] = "FAILED_POST_DATA" if any_data else "FAILED_PRE_DATA_RETRY_EXHAUSTED"
            progress["failed_post_data_attempt_count"] += int(any_data)
            progress["state"] = "STOPPED_POST_DATA_FAILURE" if any_data else "STOPPED_PRE_DATA_RETRY_EXHAUSTED"
            progress["updated_at_utc"] = now()
            atomic_write_json(progress_path, progress)
            return 3

        qc_path = attempt_root / "outcome_blind_qc.json"
        qc_rc = run([
            args.python, "-B", str(script_dir / "outcome_blind_qc.py"),
            "--attempt-root", str(attempt_root), "--output", str(qc_path),
        ], args.task_root / "scheduler.log")
        raw_manifest = attempt_root / "raw_artifact_manifest.csv"
        manifest_rc = run([
            args.python, "-B", str(script_dir / "raw_artifact_manifest.py"),
            "--attempt-root", str(attempt_root), "--output", str(raw_manifest),
        ], args.task_root / "scheduler.log")
        qc = load_json(qc_path) if qc_path.exists() else {"pass": False}
        record["finished_at_utc"] = now()
        record["outcome_blind_qc_path"] = str(qc_path)
        record["raw_artifact_manifest_path"] = str(raw_manifest)
        progress["running_trial_count"] = 0
        if qc_rc != 0 or manifest_rc != 0 or qc.get("pass") is not True:
            record["state"] = "FAILED_POST_DATA" if any_data else "FAILED_PRE_DATA_INFRASTRUCTURE"
            if any_data:
                progress["failed_post_data_attempt_count"] += 1
                progress["state"] = "STOPPED_POST_DATA_FAILURE"
                progress["updated_at_utc"] = now()
                atomic_write_json(progress_path, progress)
                return 3
            if attempt_id == 0:
                progress["failed_pre_data_attempt_count"] += 1
                progress["state"] = "READY_RETRY_PRE_DATA"
                atomic_write_json(progress_path, progress)
                continue
            progress["state"] = "STOPPED_PRE_DATA_RETRY_EXHAUSTED"
            atomic_write_json(progress_path, progress)
            return 3
        record["state"] = "PASSED_OUTCOME_BLIND_QC"
        record["outcome_blind_qc_pass"] = True
        progress["completed_trial_count"] += 1
        progress["state"] = "RUNNING" if progress["completed_trial_count"] < 100 else "COLLECTION_COMPLETE_AWAITING_LOCK"
        progress["updated_at_utc"] = now()
        atomic_write_json(progress_path, progress)
        print(f"formal_progress={progress['completed_trial_count']}/100 trial={trial_id:03d} qc=pass", flush=True)

    build_rc = run([
        args.python, "-B", str(script_dir / "build_collection_lock.py"),
        "--task-root", str(args.task_root), "--execution-lock", str(args.execution_lock),
        "--output", str(args.task_root / "FORMAL_COLLECTION_LOCK.json"),
    ], args.task_root / "scheduler.log")
    if build_rc != 0:
        progress["state"] = "COLLECTION_COMPLETE_LOCK_FAILED"
        atomic_write_json(progress_path, progress)
        return 4
    progress["state"] = "LOCKED"
    progress["formal_collection_lock_path"] = str(args.task_root / "FORMAL_COLLECTION_LOCK.json")
    progress["updated_at_utc"] = now()
    atomic_write_json(progress_path, progress)
    print("formal_collection=locked trials=100 scientific_analysis_performed=false", flush=True)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
