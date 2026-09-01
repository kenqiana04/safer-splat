#!/usr/bin/env python3
"""Independent fail-closed validator for the locked formal collection."""

from __future__ import annotations

import argparse
import csv
import hashlib
import json
import subprocess
from pathlib import Path
from typing import Any

from collection_common import (
    DATA_ROLE, EXPECTED_UPSTREAM_HEAD, MAP_AUTHORITY_ID, OFFICIAL100_SHA256, PROTOCOL_SHA256,
    atomic_write_json, file_sha256, load_json, semantic_sha256, verify_execution_lock,
)

RATE_FIELDS = (
    "capture_completeness", "selected_u_completeness", "map_authority_completeness",
    "reachability_completeness", "shadow_result_completion", "join_completeness",
)
FORBIDDEN_ANALYZERS = ("analyze_formal_cohort.py", "primary_rate.py", "bootstrap_ci.py", "multi_candidate_science.py")


def git_blob(checkout: Path, relative: str) -> bytes:
    return subprocess.check_output(["git", "-C", str(checkout), "cat-file", "blob", f"{EXPECTED_UPSTREAM_HEAD}:{relative}"])


def validate(root: Path, git_task_dir: Path | None) -> dict[str, Any]:
    checks: dict[str, bool] = {}
    execution = verify_execution_lock(root / "COLLECTION_EXECUTION_LOCK.json", root / "task_scripts")
    checks["execution_lock_valid_and_scripts_unchanged"] = True
    checks["pr100_exact_identity"] = execution["upstream_head"] == EXPECTED_UPSTREAM_HEAD
    checks["protocol_sha_exact"] = execution["protocol_sha256"] == PROTOCOL_SHA256
    checks["official100_sha_exact"] = execution["official100_sha256"] == OFFICIAL100_SHA256
    checks["environment_identity_frozen"] = file_sha256(root / "collection_environment_identity.json") == execution["environment_identity_sha256"]
    checks["map_authority_frozen"] = execution["map_authority_id"] == MAP_AUTHORITY_ID

    checkout = root / "checkout_pr100"
    lock_blob = json.loads(git_blob(checkout, "reproduction/protocol/l2_h1_prospective_shadow_cohort_v1/PROTOCOL_LOCK.json"))
    per_file = {}
    for name in lock_blob["per_file_sha256"]:
        relative = f"reproduction/protocol/l2_h1_prospective_shadow_cohort_v1/{name}"
        per_file[name] = hashlib.sha256(git_blob(checkout, relative)).hexdigest()
    checks["protocol_raw_git_blobs_exact"] = per_file == lock_blob["per_file_sha256"] and semantic_sha256([
        {"path": name, "sha256": per_file[name]} for name in sorted(per_file)
    ]) == PROTOCOL_SHA256

    progress = load_json(root / "formal_collection_progress.json")
    passed = sorted((row for row in progress["trials"] if row.get("state") == "PASSED_OUTCOME_BLIND_QC"), key=lambda row: int(row["trial_id"]))
    checks["progress_locked_100"] = progress.get("state") == "LOCKED" and progress.get("completed_trial_count") == 100 and progress.get("running_trial_count") == 0
    checks["stable_unique_order_0_99"] = [int(row["trial_id"]) for row in passed] == list(range(100))
    checks["no_pre_data_retry"] = progress.get("failed_pre_data_attempt_count") == 0 and all(int(row["attempt_id"]) == 0 for row in passed)
    checks["no_post_data_deviation"] = progress.get("failed_post_data_attempt_count") == 0
    checks["formal_namespace_disjoint"] = all(row["run_id"] == f"formal-v1-trial-{int(row['trial_id']):03d}-attempt-0" for row in passed)

    total = {"intended_step_count": 0, "capture_count": 0, "result_record_count": 0, "joinable_record_count": 0}
    intervention_count = replacement_count = 0
    per_trial_ok = True
    for record in passed:
        attempt = root / "formal-v1" / f"trial-{int(record['trial_id']):03d}" / "attempt-0"
        qc = load_json(attempt / "outcome_blind_qc.json")
        per_trial_ok &= (
            qc.get("pass") is True and qc.get("outcome_blind") is True
            and qc.get("scientific_outcome_aggregation_count") == 0
            and qc.get("l2_status_field_presence_and_type_checked") is True
            and all(qc["rates"].get(key) == 1.0 for key in RATE_FIELDS)
            and all(value == 0 for value in qc["errors"].values())
        )
        for key in total:
            total[key] += int(qc[key])
        activation = load_json(attempt / "run/arm_activation.json")
        intervention_count += int(activation.get("controller_intervention_count", 0))
        replacement_count += int(activation.get("selected_candidate_replacement_count", 0))
    summary = load_json(root / "collection_qc_summary.json")
    checks["all_per_trial_strict_blind_qc_pass"] = per_trial_ok and all(summary["rates"].get(key) == 1.0 for key in RATE_FIELDS) and summary.get("aggregate_error_count") == 0
    checks["compact_totals_reconcile"] = all(total[key] == summary[key] for key in total)
    checks["zero_authority_and_replacement"] = intervention_count == replacement_count == 0

    raw_index = load_json(root / "raw_artifact_manifest_index.json")
    raw_manifest = root / "raw_artifact_manifest.csv"
    checks["raw_artifact_index_valid"] = raw_index.get("formal_trial_count") == 100 and raw_index.get("per_attempt_manifest_count") == 100 and raw_index.get("combined_raw_artifact_manifest_sha256") == file_sha256(raw_manifest)
    raw_ok = True
    with raw_manifest.open("r", encoding="utf-8", newline="") as handle:
        raw_rows = list(csv.DictReader(handle))
    for row in raw_rows:
        artifact = root / row["server_relative_path"]
        raw_ok &= artifact.is_file() and artifact.stat().st_size == int(row["size_bytes"]) and file_sha256(artifact) == row["sha256"]
    checks["all_raw_artifact_hashes_resolve"] = raw_ok and len(raw_rows) == raw_index["raw_artifact_count"]

    commitment = load_json(root / "scientific_outcome_artifact_commitment.json")
    commitment_ok = commitment.get("result_artifact_count") == 100 and commitment.get("scientific_outcome_aggregation_count") == 0
    for row in commitment.get("ordered_result_artifacts", []):
        path = root / row["relative_path"]
        commitment_ok &= path.is_file() and path.stat().st_size == int(row["size"]) and file_sha256(path) == row["sha256"]
    checks["result_artifact_commitment_valid_without_analysis"] = commitment_ok

    formal_lock = load_json(root / "FORMAL_COLLECTION_LOCK.json")
    required = set(load_json(checkout / "reproduction/protocol/l2_h1_prospective_shadow_cohort_v1/formal_collection_lock_schema.json")["required"])
    canonical = json.dumps(formal_lock, indent=2, sort_keys=True, allow_nan=False) + "\n"
    checks["formal_collection_lock_valid"] = (
        set(formal_lock) == required and formal_lock.get("formal_trial_count") == 100
        and len(formal_lock.get("formal_run_ids", [])) == 100 and len(formal_lock.get("raw_artifact_manifests", [])) == 100
        and len(formal_lock.get("per_trial_sha256", {})) == 100 and formal_lock.get("qc_completeness") is True
        and formal_lock.get("collection_deviations") == [] and formal_lock.get("collection_locked_before_scientific_analysis") is True
        and canonical.encode("utf-8") == (root / "FORMAL_COLLECTION_LOCK.json").read_bytes()
    )
    expected_lock_sha = (root / "FORMAL_COLLECTION_LOCK.sha256").read_text(encoding="ascii").strip()
    checks["formal_collection_lock_hash_deterministic"] = expected_lock_sha == file_sha256(root / "FORMAL_COLLECTION_LOCK.json")
    checks["no_analyzer_artifacts"] = not any((root / name).exists() for name in FORBIDDEN_ANALYZERS)
    checks["no_scientific_outcome_summary"] = summary.get("scientific_outcome_aggregation_count") == 0 and load_json(root / "FORMAL_COLLECTION_LOCK_METADATA.json").get("outcome_distribution_exposed") is False
    raw_git_count = 0
    if git_task_dir is not None and git_task_dir.exists():
        raw_git_count = sum(1 for path in git_task_dir.rglob("*") if path.is_file() and path.suffix in {".jsonl", ".log"})
    checks["raw_logs_committed_to_git_zero"] = raw_git_count == 0
    pass_value = all(checks.values())
    return {
        "schema_version": "L2_H1_FORMAL_COLLECTION_VALIDATION_RESULT_V1",
        "checks": checks, "passed_check_count": sum(checks.values()), "failed_checks": [name for name, value in checks.items() if not value],
        "pass": pass_value, "formal_trial_count": len(passed), **total,
        "controller_intervention_count": intervention_count, "candidate_replacement_count": replacement_count,
        "raw_log_files_committed_to_git": raw_git_count,
        "scientific_analysis_performed": False, "outcome_distribution_exposed": False,
        "validator": "PASS_L2_H1_PROSPECTIVE_SHADOW_COHORT_COLLECTION_V1_VALIDATION" if pass_value else "FAIL_L2_H1_PROSPECTIVE_SHADOW_COHORT_COLLECTION_V1_VALIDATION",
    }


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--server-root", type=Path, required=True)
    parser.add_argument("--git-task-dir", type=Path)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    result = validate(args.server_root.resolve(strict=True), args.git_task_dir.resolve() if args.git_task_dir else None)
    atomic_write_json(args.output, result)
    print(json.dumps({"validator": result["validator"], "passed_check_count": result["passed_check_count"], "failed_checks": result["failed_checks"]}, sort_keys=True))
    return 0 if result["pass"] else 2


if __name__ == "__main__":
    raise SystemExit(main())
