#!/usr/bin/env python3
"""Fail-closed formal-analysis validator locked before scientific reveal."""

from __future__ import annotations

import argparse
import csv
import json
from pathlib import Path
from typing import Any

from analysis_common import (
    COLLECTION_LOCK_SHA256, DATA_ROLE, EXPECTED_PR101_HEAD, ORDERED_RESULT_COMMITMENT_SHA256,
    PROTOCOL_SHA256, RAW_MANIFEST_SHA256, RESULT_COMMITMENT_FILE_SHA256, file_sha256, load_json, semantic_sha256,
)


def prohibited_claim_hits(text: str, prohibited: list[str]) -> list[str]:
    lowered = text.lower()
    return [item for item in prohibited if item.lower() in lowered]


def validate_primary(primary: dict[str, Any]) -> list[str]:
    failures = []
    total = primary.get("N_L2_PASS", 0) + primary.get("N_L2_FAIL", 0) + primary.get("N_L2_UNKNOWN", 0)
    if primary.get("N_primary") != total or not primary.get("tri_state_algebra_pass"):
        failures.append("tri_state_algebra")
    expected = primary["N_L2_FAIL"] / primary["N_primary"] if primary.get("N_primary") else None
    if primary.get("prospective_future_safety_signal_rate") != expected:
        failures.append("primary_formula")
    if primary.get("known_status_sensitivity_label") != "SECONDARY_SENSITIVITY_ONLY":
        failures.append("known_status_secondary_boundary")
    return failures


def validate_lock(lock: dict[str, Any]) -> bool:
    payload = dict(lock)
    combined = payload.pop("combined_analysis_execution_sha256", None)
    return combined == semantic_sha256(payload)


def validate_task(task: Path, *, expected_head: str) -> dict[str, Any]:
    checks: dict[str, bool] = {}
    unlock = load_json(task / "SCIENTIFIC_ANALYSIS_UNLOCK.json")
    execution = load_json(task / "ANALYSIS_EXECUTION_LOCK.json")
    primary = load_json(task / "primary_result.json")
    primary_lock = load_json(task / "PRIMARY_RESULT_LOCK.json")
    bootstrap = load_json(task / "primary_bootstrap.json")
    secondary = load_json(task / "secondary_endpoints.json")
    manifest = load_json(task / "formal_analysis_table_manifest.json")
    claim_audit = load_json(task / "claim_boundary_audit.json")
    decision = load_json(task / "FINAL_CASE_DECISION.json")
    checks["pr101_exact_identity"] = expected_head == EXPECTED_PR101_HEAD and unlock["upstream_PR101_head"] == EXPECTED_PR101_HEAD
    checks["protocol_sha_exact"] = unlock["protocol_sha"] == PROTOCOL_SHA256
    checks["collection_lock_exact"] = unlock["collection_lock_sha"] == COLLECTION_LOCK_SHA256
    checks["raw_manifest_exact"] = unlock["raw_manifest_sha"] == RAW_MANIFEST_SHA256
    checks["result_commitments_exact"] = unlock["result_commitment_file_sha"] == RESULT_COMMITMENT_FILE_SHA256 and unlock["ordered_result_commitment_sha"] == ORDERED_RESULT_COMMITMENT_SHA256
    checks["unlock_before_outcome_read"] = unlock["outcomes_read_before_unlock"] is False and unlock["unlock_authorized"] is True
    checks["analysis_lock_before_reveal"] = execution["created_before_outcome_reveal"] is True and execution["real_outcome_rows_read"] == 0 and validate_lock(execution)
    checks["locked_analyzer_hashes_unchanged"] = all(file_sha256(task / name) == expected for name, expected in execution["core_script_sha256"].items())
    checks["formal_data_role_only"] = secondary["data_role"] == DATA_ROLE and manifest["row_count"] == 14122
    checks["qa_exclusion_and_join_integrity"] = all(manifest[key] == 0 for key in ("duplicate_analysis_unit_count", "unresolved_join_count", "invalid_map_authority_count", "selected_role_mismatch_count", "provenance_mismatch_count"))
    checks["primary_eligibility_and_algebra"] = validate_primary(primary) == [] and primary["N_primary_eligible"] == primary["N_primary"]
    checks["unknown_in_primary_denominator"] = primary["N_primary"] == primary["N_L2_PASS"] + primary["N_L2_FAIL"] + primary["N_L2_UNKNOWN"]
    checks["known_status_secondary_only"] = primary["known_status_sensitivity_label"] == "SECONDARY_SENSITIVITY_ONLY"
    checks["bootstrap_contract_exact"] = (
        bootstrap["rng_seed"] == 20260831 and bootstrap["cluster_count"] == 100 and bootstrap["clusters_per_replicate"] == 100
        and bootstrap["resampling"] == "WITH_REPLACEMENT" and bootstrap["bootstrap_valid_replicates"] == 10000
        and bootstrap["step_iid_assumption"] is False and bootstrap["p_value_or_significance_test"] is False
    )
    checks["secondary_endpoint_list_exact"] = secondary["secondary_endpoint_ids"] == [
        "L2_UNKNOWN_RATE", "L2_SELECTED_REACH_RATE", "FORMAL_LOGGING_COMPLETENESS", "PER_TRIAL_L1_PASS_L2_FAIL_DISTRIBUTION",
        "BACKEND_USAGE_COUNTS", "NATIVE_MULTI_CANDIDATE_OPPORTUNITY_AND_DISAGREEMENT", "SELECTED_VS_NATIVE_NONSELECTED_STATUS",
    ]
    checks["candidate_contract_exact"] = secondary["u_des_is_native_alternative"] is False and secondary["synthetic_candidate_generation_count"] == 0
    checks["collision_progress_analysis_absent"] = secondary["collision_progress_use"] == "RUN_CONTEXT_AND_IDENTITY_ONLY"
    checks["claims_bounded"] = claim_audit["prohibited_claim_hits"] == [] and claim_audit["p_value_computed"] is False
    lock_copy = dict(primary_lock)
    checks["primary_result_lock_valid"] = lock_copy["primary_result_sha256"] == semantic_sha256(primary) and lock_copy["primary_result_file_sha256"] == file_sha256(task / "primary_result.json")
    checks["figures_from_compact_summaries"] = load_json(task / "figure_provenance.json")["source_is_locked_compact_summary"] is True
    checks["raw_formal_logs_git_zero"] = not any(path.suffix in {".jsonl", ".log"} for path in task.rglob("*"))
    checks["final_status_valid"] = decision["final_status"] == "PASS_L2_H1_PROSPECTIVE_SHADOW_COHORT_ANALYSIS_V1"
    passed = all(checks.values())
    return {"schema_version": "L2_H1_FORMAL_ANALYSIS_VALIDATION_RESULT_V1", "checks": checks,
            "passed_check_count": sum(checks.values()), "failed_checks": [key for key, value in checks.items() if not value], "pass": passed,
            "validator": "PASS_L2_H1_PROSPECTIVE_SHADOW_COHORT_ANALYSIS_V1_VALIDATION" if passed else "FAIL_L2_H1_PROSPECTIVE_SHADOW_COHORT_ANALYSIS_V1_VALIDATION"}


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--task-dir", type=Path, required=True)
    parser.add_argument("--expected-head", required=True)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    result = validate_task(args.task_dir, expected_head=args.expected_head)
    args.output.write_text(json.dumps(result, indent=2, sort_keys=True) + "\n", encoding="utf-8", newline="\n")
    print(json.dumps({"validator": result["validator"], "failed_checks": result["failed_checks"]}, sort_keys=True))
    return 0 if result["pass"] else 2


if __name__ == "__main__":
    raise SystemExit(main())

