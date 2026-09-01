#!/usr/bin/env python3
"""Run one preregistered trial in a fresh process and preserve raw evidence."""

from __future__ import annotations

import argparse
import os
import subprocess
import sys
from datetime import datetime, timezone
from pathlib import Path

from collection_common import (
    DATA_ROLE, EXPECTED_UPSTREAM_HEAD, MAP_AUTHORITY_ID, PROTOCOL_SHA256,
    atomic_write_json, formal_run_id, load_json, verify_execution_lock,
)


def utc_now() -> str:
    return datetime.now(timezone.utc).isoformat()


def count_nonempty(path: Path) -> int:
    if not path.is_file():
        return 0
    with path.open("rb") as handle:
        return sum(1 for line in handle if line.strip())


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--checkout", type=Path, required=True)
    parser.add_argument("--task-root", type=Path, required=True)
    parser.add_argument("--python", required=True)
    parser.add_argument("--trial-id", type=int, required=True)
    parser.add_argument("--attempt-id", type=int, choices=(0, 1), required=True)
    parser.add_argument("--execution-lock", type=Path, required=True)
    args = parser.parse_args()

    script_dir = Path(__file__).resolve().parent
    lock = verify_execution_lock(args.execution_lock, script_dir)
    run_id = formal_run_id(args.trial_id, args.attempt_id)
    attempt_root = args.task_root / "formal-v1" / f"trial-{args.trial_id:03d}" / f"attempt-{args.attempt_id}"
    if attempt_root.exists():
        raise RuntimeError(f"attempt overwrite forbidden: {attempt_root}")
    attempt_root.mkdir(parents=True)
    run_root = attempt_root / "run"

    manifest = load_json(args.checkout / "reproduction/protocol/l2_h1_prospective_shadow_cohort_v1/formal_trial_manifest.json")
    expected = manifest["trials"][args.trial_id]
    if expected["trial_id"] != args.trial_id or expected["formal_order"] != args.trial_id:
        raise RuntimeError("formal manifest/order mismatch")
    if expected["data_role"] != DATA_ROLE:
        raise RuntimeError("formal data-role mismatch")

    identity = {
        "schema_version": "L2_H1_FORMAL_ATTEMPT_IDENTITY_V1",
        "trial_id": args.trial_id,
        "attempt_id": args.attempt_id,
        "run_id": run_id,
        "data_role": DATA_ROLE,
        "eligible_for_formal_prospective_cohort": True,
        "protocol_sha256": PROTOCOL_SHA256,
        "collection_execution_lock_sha256": lock["collection_execution_lock_sha256"],
        "upstream_head": EXPECTED_UPSTREAM_HEAD,
        "map_authority_id": MAP_AUTHORITY_ID,
        "legacy_frozen_runner_qa_only_field_is_data_role_authority": False,
        "formal_data_role_authority": "PR100_FORMAL_MANIFEST_PLUS_EXECUTION_LOCK_PLUS_THIS_SIDECAR",
        "fresh_process": True,
        "started_at_utc": utc_now(),
    }
    atomic_write_json(attempt_root / "formal_attempt_identity.json", identity)

    runner = args.checkout / "reproduction/equivalence/l2_h1_shadow_instrumentation_off_vs_on_v1/server_run_one.py"
    command = [
        args.python, "-B", str(runner), "--arm", "C", "--trial-id", str(args.trial_id),
        "--seed", str(args.trial_id), "--run-id", run_id, "--checkout", str(args.checkout),
        "--run-dir", str(run_root), "--queue-capacity", "8", "--shutdown-timeout", "120",
    ]
    env = os.environ.copy()
    env.update({
        "CUDA_VISIBLE_DEVICES": "1", "PYTHONHASHSEED": "0", "CUBLAS_WORKSPACE_CONFIG": ":4096:8",
        "PYTHONNOUSERSITE": "1", "PYTHONDONTWRITEBYTECODE": "1",
    })
    started = utc_now()
    with (attempt_root / "stdout.log").open("wb") as stdout, (attempt_root / "stderr.log").open("wb") as stderr:
        completed = subprocess.run(command, cwd=args.checkout, env=env, stdout=stdout, stderr=stderr, check=False)
    capture_count = count_nonempty(run_root / "instrumentation/step_capture_log.jsonl")
    result_count = count_nonempty(run_root / "instrumentation/shadow_certificate_result_log.jsonl")
    intended_count = 0
    trace_path = run_root / "primary_trace.json"
    if trace_path.is_file():
        trace = load_json(trace_path)
        intended_count = len(trace.get("steps", [])) if isinstance(trace.get("steps"), list) else 0
    result = {
        "schema_version": "L2_H1_FORMAL_PROCESS_RESULT_V1",
        "trial_id": args.trial_id, "attempt_id": args.attempt_id, "run_id": run_id,
        "started_at_utc": started, "finished_at_utc": utc_now(), "exit_code": completed.returncode,
        "intended_step_count": intended_count, "capture_count": capture_count, "result_record_count": result_count,
        "scientific_row_count": result_count, "contains_scientific_outcome_aggregation": False,
    }
    atomic_write_json(attempt_root / "process_result.json", result)
    print(f"trial={args.trial_id:03d} attempt={args.attempt_id} exit={completed.returncode} intended={intended_count} capture={capture_count} result={result_count}", flush=True)
    return completed.returncode


if __name__ == "__main__":
    raise SystemExit(main())
