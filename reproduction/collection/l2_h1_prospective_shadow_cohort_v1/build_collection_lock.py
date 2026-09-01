#!/usr/bin/env python3
"""Build the deterministic outcome-blind collection lock after 100 QC passes."""

from __future__ import annotations

import argparse
import csv
from pathlib import Path
from typing import Any

from collection_common import (
    DATA_ROLE, MAP_AUTHORITY_ID, PROTOCOL_SHA256, atomic_write_json, file_sha256,
    load_json, semantic_sha256, verify_execution_lock,
)

RATE_FIELDS = (
    "capture_completeness", "selected_u_completeness", "map_authority_completeness",
    "reachability_completeness", "shadow_result_completion", "join_completeness",
)


def write_csv(path: Path, rows: list[dict[str, Any]], fieldnames: tuple[str, ...]) -> None:
    with path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=fieldnames, lineterminator="\n", extrasaction="ignore")
        writer.writeheader()
        writer.writerows(rows)


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--task-root", type=Path, required=True)
    parser.add_argument("--execution-lock", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    script_dir = Path(__file__).resolve().parent
    execution = verify_execution_lock(args.execution_lock, script_dir)
    progress = load_json(args.task_root / "formal_collection_progress.json")
    passed = [row for row in progress.get("trials", []) if row.get("state") == "PASSED_OUTCOME_BLIND_QC"]
    if progress.get("completed_trial_count") != 100 or len(passed) != 100 or progress.get("running_trial_count") != 0:
        raise RuntimeError("collection is not exactly 100 terminal QC-passed trials")
    passed.sort(key=lambda row: int(row["trial_id"]))
    if [int(row["trial_id"]) for row in passed] != list(range(100)):
        raise RuntimeError("formal trial coverage/order mismatch")

    qc_rows: list[dict[str, Any]] = []
    manifest_refs: list[dict[str, Any]] = []
    per_trial_sha: dict[str, str] = {}
    result_commitment_rows: list[dict[str, Any]] = []
    totals = {"intended_step_count": 0, "capture_count": 0, "result_record_count": 0, "joinable_record_count": 0}
    deviations = []
    for failed in (row for row in progress.get("trials", []) if row.get("state") != "PASSED_OUTCOME_BLIND_QC"):
        deviations.append({
            "trial_id": failed["trial_id"], "attempt_id": failed["attempt_id"], "classification": failed["state"],
            "intended_step_count": failed.get("intended_step_count", 0),
            "capture_count": failed.get("capture_count", 0), "result_record_count": failed.get("result_record_count", 0),
        })
    for record in passed:
        trial_id = int(record["trial_id"])
        attempt_root = args.task_root / "formal-v1" / f"trial-{trial_id:03d}" / f"attempt-{record['attempt_id']}"
        qc_path = attempt_root / "outcome_blind_qc.json"
        qc = load_json(qc_path)
        if qc.get("pass") is not True or qc.get("outcome_blind") is not True or qc.get("scientific_outcome_aggregation_count") != 0:
            raise RuntimeError(f"trial {trial_id}: QC is not a clean outcome-blind pass")
        if any(qc["rates"].get(key) != 1.0 for key in RATE_FIELDS) or any(value != 0 for value in qc["errors"].values()):
            raise RuntimeError(f"trial {trial_id}: completeness/error gate failed")
        for key in totals:
            totals[key] += int(qc[key])
        qc_rows.append({
            "trial_id": trial_id, "attempt_id": record["attempt_id"], "run_id": record["run_id"],
            "data_role": DATA_ROLE, "outcome_blind_qc_pass": True,
            "intended_step_count": qc["intended_step_count"], "capture_count": qc["capture_count"],
            "result_record_count": qc["result_record_count"], "joinable_record_count": qc["joinable_record_count"],
            **qc["rates"], "aggregate_error_count": sum(qc["errors"].values()),
        })
        manifest_path = attempt_root / "raw_artifact_manifest.csv"
        manifest_summary = load_json(manifest_path.with_suffix(".summary.json"))
        manifest_sha = file_sha256(manifest_path)
        if manifest_summary.get("artifact_manifest_sha256") != manifest_sha:
            raise RuntimeError(f"trial {trial_id}: raw artifact manifest hash mismatch")
        manifest_refs.append({
            "trial_id": trial_id, "attempt_id": record["attempt_id"], "run_id": record["run_id"],
            "server_path": str(manifest_path), "sha256": manifest_sha,
        })
        per_trial_sha[record["run_id"]] = semantic_sha256({
            "formal_attempt_identity_sha256": file_sha256(attempt_root / "formal_attempt_identity.json"),
            "outcome_blind_qc_sha256": file_sha256(qc_path),
            "raw_artifact_manifest_sha256": manifest_sha,
        })
        result_path = attempt_root / "run/instrumentation/shadow_certificate_result_log.jsonl"
        result_commitment_rows.append({
            "trial_id": trial_id, "run_id": record["run_id"], "relative_path": result_path.relative_to(args.task_root).as_posix(),
            "size": result_path.stat().st_size, "sha256": file_sha256(result_path),
        })

    qc_csv = args.task_root / "collection_qc_per_trial.csv"
    write_csv(qc_csv, qc_rows, (
        "trial_id", "attempt_id", "run_id", "data_role", "outcome_blind_qc_pass",
        "intended_step_count", "capture_count", "result_record_count", "joinable_record_count", *RATE_FIELDS,
        "aggregate_error_count",
    ))
    deviation_csv = args.task_root / "collection_deviations.csv"
    write_csv(deviation_csv, deviations, (
        "trial_id", "attempt_id", "classification", "intended_step_count", "capture_count", "result_record_count",
    ))
    result_commitment = {
        "schema_version": "L2_H1_FORMAL_RESULT_ARTIFACT_COMMITMENT_V1",
        "data_role": DATA_ROLE,
        "result_artifact_count": 100,
        "ordered_result_artifacts": result_commitment_rows,
        "ordered_result_commitment_sha256": semantic_sha256(result_commitment_rows),
        "scientific_outcome_aggregation_count": 0,
    }
    commitment_path = args.task_root / "scientific_outcome_artifact_commitment.json"
    atomic_write_json(commitment_path, result_commitment)
    summary = {
        "schema_version": "L2_H1_FORMAL_OUTCOME_BLIND_COLLECTION_SUMMARY_V1",
        "data_role": DATA_ROLE, "formal_trial_count": 100, **totals,
        "rates": {key: 1.0 for key in RATE_FIELDS},
        "aggregate_error_count": 0,
        "pre_data_retry_count": len(deviations),
        "post_data_failure_count": 0,
        "scientific_outcome_aggregation_count": 0,
        "collection_qc_per_trial_sha256": file_sha256(qc_csv),
        "result_artifact_commitment_sha256": file_sha256(commitment_path),
    }
    atomic_write_json(args.task_root / "collection_qc_summary.json", summary)
    lock = {
        "schema_version": "FORMAL_COLLECTION_LOCK_V1",
        "formal_trial_count": 100,
        "formal_run_ids": [row["run_id"] for row in passed],
        "raw_artifact_manifests": manifest_refs,
        "per_trial_sha256": per_trial_sha,
        "environment_identity": execution["environment_identity_sha256"],
        "map_identity": MAP_AUTHORITY_ID,
        "protocol_lock_sha256": PROTOCOL_SHA256,
        "qc_completeness": True,
        "collection_deviations": deviations,
        "collection_locked_before_scientific_analysis": True,
    }
    atomic_write_json(args.output, lock)
    (args.output.parent / "FORMAL_COLLECTION_LOCK.sha256").write_text(file_sha256(args.output) + "\n", encoding="ascii", newline="\n")
    print(f"formal_trial_count=100 lock_sha256={file_sha256(args.output)} scientific_analysis_performed=false")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
