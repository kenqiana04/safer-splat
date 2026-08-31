#!/usr/bin/env python3
"""Independent validator for the frozen L2/H1 prospective shadow protocol V1."""

from __future__ import annotations

import argparse
import hashlib
import json
import re
import subprocess
from pathlib import Path
from typing import Any


PASS_TOKEN = "PASS_L2_H1_PROSPECTIVE_SHADOW_COHORT_PROTOCOL_V1_VALIDATION"
EXPECTED_UPSTREAM = "17bec44c51207bf7f831db724e108b86adb0ace8"
EXPECTED_MANIFEST_SHA = "1b236bba8173c8a37fb7752fd2e2f09fc569191d6820089759b4be547bd6c344"
FORMAL_ROLE = "FORMAL_PROSPECTIVE_SHADOW_COHORT_V1"
QA_ROLES = {"EQUIVALENCE_QA_ONLY", "PILOT_QA_ONLY", "FROZEN_HISTORICAL_REPLAY"}


def load_json(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def sha256_file(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def compact_canonical_bytes(value: Any) -> bytes:
    return json.dumps(value, sort_keys=True, ensure_ascii=False, allow_nan=False, separators=(",", ":")).encode("utf-8")


def combined_hash(per_file: dict[str, str]) -> str:
    records = [{"path": path, "sha256": per_file[path]} for path in sorted(per_file)]
    return hashlib.sha256(compact_canonical_bytes(records)).hexdigest()


def validate(root: Path) -> dict[str, Any]:
    root = root.resolve(strict=True)
    repo = root.parents[2]
    lock = load_json(root / "PROTOCOL_LOCK.json")
    manifest = load_json(root / "formal_trial_manifest.json")
    run_schema = load_json(root / "formal_run_id_schema.json")
    exclusion = load_json(root / "formal_exclusion_contract.json")
    analysis = load_json(root / "formal_analysis_contract.json")
    join = load_json(root / "formal_identity_join_contract.json")
    qc = load_json(root / "formal_qc_contract.json")
    outcome_blind = load_json(root / "outcome_blind_qc_contract.json")
    retry = load_json(root / "formal_retry_stop_policy.json")
    retention = load_json(root / "formal_artifact_retention_policy.json")
    environment = load_json(root / "formal_collection_environment_contract.json")
    collection_schema = load_json(root / "formal_collection_lock_schema.json")
    claims = load_json(root / "formal_claim_contract.json")
    final = load_json(root / "FINAL_CASE_DECISION.json")
    methods = load_json(root / "reviewers/methods_statistics_review.json")
    systems = load_json(root / "reviewers/systems_reproducibility_review.json")
    report = (root / "report/REPORT_FREEZE_L2_H1_PROSPECTIVE_SHADOW_COHORT_PROTOCOL_V1.md").read_text(encoding="utf-8")

    checks: dict[str, bool] = {}
    recorded_hashes = lock["per_file_sha256"]
    recomputed_hashes = {name: sha256_file(root / name) for name in recorded_hashes}
    checks["protocol_per_file_sha_exact"] = recorded_hashes == recomputed_hashes
    checks["combined_protocol_sha_exact"] = lock["combined_protocol_sha256"] == combined_hash(recomputed_hashes)
    checks["upstream_pr99_exact"] = lock["upstream_pr99_head"] == EXPECTED_UPSTREAM == manifest["upstream_pr99_head"]
    checks["official_manifest_sha_exact"] = lock["official100_manifest_sha256"] == EXPECTED_MANIFEST_SHA == manifest["official100_manifest_sha256"]

    trials = manifest["trials"]
    ids = [row["trial_id"] for row in trials]
    run_ids = [row["attempt_0_run_id"] for row in trials]
    checks["official100_exactly_100_unique"] = len(trials) == 100 and ids == list(range(100)) and len(set(ids)) == 100
    checks["formal_run_order_stable"] = [row["formal_order"] for row in trials] == list(range(100))
    pattern = re.compile(run_schema["properties"]["run_id"]["pattern"])
    checks["formal_run_ids_unique_and_valid"] = len(set(run_ids)) == 100 and all(pattern.fullmatch(value) for value in run_ids)
    checks["formal_namespace_disjoint_from_qa"] = not (set(run_ids) & set(exclusion["hard_rejected_qa_run_ids"]))
    checks["pilot_ids_rerun_fresh_formal"] = all(trials[trial_id]["prior_qa_trial_id_reused_formally"] and trials[trial_id]["attempt_0_run_id"].startswith("formal-v1-") for trial_id in [10, 30, 50, 70, 90])
    checks["qa_roles_permanently_excluded"] = set(exclusion["hard_rejected_data_roles"]) == QA_ROLES and exclusion["qa_exclusion_is_permanent"] is True

    checks["analysis_unit_frozen"] = len(analysis["analysis_unit_key"]) == 7 and "selected/executed" in analysis["analysis_unit"]
    checks["primary_eligibility_complete"] = len(analysis["primary_eligibility_all"]) == 10
    checks["primary_algebra_frozen"] = analysis["tri_state_algebra"] == "N_primary=N_L2_PASS+N_L2_FAIL+N_L2_UNKNOWN"
    checks["unknown_in_primary_denominator"] = analysis["unknown_in_primary_denominator"] is True and "UNKNOWN" in analysis["primary_denominator"]
    checks["udes_not_native_alternative"] = analysis["candidate_roles"]["u_des"] == "NOMINAL_REFERENCE" and analysis["multi_candidate_contract"]["u_des_is_native_alternative"] is False
    checks["synthetic_candidate_zero"] = analysis["multi_candidate_contract"]["synthetic_candidate_generation_count"] == 0
    bootstrap = analysis["cluster_bootstrap"]
    checks["cluster_bootstrap_frozen"] = all((bootstrap["cluster_unit"] == "formal_trial", bootstrap["cluster_count"] == 100, bootstrap["clusters_per_replicate"] == 100, bootstrap["valid_replicates"] == 10000, bootstrap["rng_seed"] == 20260831, bootstrap["maximum_total_draws"] == 100000, bootstrap["step_iid_assumption"] is False))

    join_keys = set(join["capture_result_join_key"])
    checks["join_key_complete"] = {"run_id", "process_local_trial_token", "step_id", "state_sequence_id", "decision_commit_id", "payload_sequence_id", "selected_candidate_id", "map_authority_id"}.issubset(join_keys)
    checks["official_vs_runtime_trial_identity_separated"] = join["official_trial_identity"]["not_equal_to_process_local_token_by_assumption"] is True and join["process_local_trial_token"]["must_not_be_used_as_official_trial_id"] is True
    checks["join_hotfix_forbidden"] = join["change_after_first_formal_run"] == "STOP_V1_AND_CREATE_PROTOCOL_V2" and join["hot_fix_and_mix_v1_data"] is False
    aggregator = repo / "reproduction/pilot/l2_h1_shadow_logging_completeness_pilot_v1/aggregate_logging_pilot.py"
    checks["join_source_aggregator_sha_exact"] = join["source"]["pr99_final_aggregator_sha256"] == sha256_file(aggregator)

    checks["per_trial_qc_all_rates_one"] = set(qc["completeness_required"].values()) == {1.0}
    checks["per_trial_qc_all_errors_zero"] = set(qc["error_count_required"].values()) == {0}
    checks["outcome_blind_qc_blocks_science"] = outcome_blind["collection_task_may_analyze_scientific_outcomes"] is False and {"PASS_FAIL_UNKNOWN_DISTRIBUTION", "PRIMARY_ENDPOINT", "BOOTSTRAP_CI"}.issubset(outcome_blind["forbidden_collection_outputs"])
    checks["status_presence_type_only"] = "l2_status_field_presence_and_type_only" in outcome_blind["allowed_checks"]
    checks["analysis_unlock_requires_collection_lock"] = "FORMAL_COLLECTION_LOCK_VALID=true" in outcome_blind["scientific_analysis_unlock_all"]

    checks["retry_pre_data_only"] = retry["automatic_retry_failure_class"] == "PRE_DATA_INFRA_FAILURE" and retry["maximum_automatic_retries_per_trial"] == 1 and retry["post_data_automatic_retry"] is False
    checks["post_data_stops_cohort"] = retry["continue_remaining_trials_after_post_data_failure"] is False and retry["mix_partial_and_rerun_in_v1"] is False
    checks["raw_logs_git_excluded"] = retention["raw_log_files_committed_to_git"] == 0 and set(retention["git_forbidden_suffixes"]) == {".jsonl", ".log"}
    raw_paths = [path for path in root.rglob("*") if path.is_file() and path.suffix.lower() in {".jsonl", ".log"}]
    checks["no_raw_navigation_logs_present"] = not raw_paths

    checks["environment_frozen"] = environment["physical_gpu_index"] == 1 and environment["trial_count"] == 100 and environment["fresh_process_each_trial"] is True and environment["adaptive_stopping"] is False
    checks["formal_role_unique"] = environment["data_role"] == FORMAL_ROLE == exclusion["accepted_data_role"]
    checks["collection_lock_schema_only"] = collection_schema["template_only"] is True and collection_schema["actual_formal_collection_lock_generated"] is False and collection_schema["properties"]["formal_trial_count"]["const"] == 100
    checks["claim_boundary_frozen"] = claims["l2_controller_authority"] is False and len(claims["prohibited_claims"]) >= 10
    checks["zero_execution_counts"] = all(final[key] == 0 for key in ["navigation_run_count", "formal_collection_run_count", "new_research_data_count", "controller_intervention_count", "candidate_replacement_count", "formal_performance_metric_count", "formal_runtime_metric_count"])
    checks["case_a_frozen"] = final["selected_case"] == "CASE_A" and final["FINAL_STATUS"] == "PASS_L2_H1_PROSPECTIVE_SHADOW_COHORT_PROTOCOL_FREEZE_V1"
    checks["reviewers_pass_case_a"] = all(item["verdict"] == "PASS" and item["recommended_case"] == "CASE_A" and not item["critical_blockers"] for item in [methods, systems])
    checks["report_answers_q1_q22"] = all(f"Q{index}" in report for index in range(1, 23))
    checks["report_contains_lock_sha"] = lock["combined_protocol_sha256"] in report
    checks["no_placeholder_language"] = not any(token in (root / "FORMAL_COHORT_PROTOCOL.md").read_text(encoding="utf-8") for token in ["TBD", "TODO", "PLACEHOLDER"])
    diff = subprocess.run(["git", "-C", str(repo), "diff", "--check"], capture_output=True, text=True, check=False)
    checks["git_diff_check"] = diff.returncode == 0

    failed = sorted(key for key, value in checks.items() if not value)
    result = {
        "validator": PASS_TOKEN if not failed else "FAIL_L2_H1_PROSPECTIVE_SHADOW_COHORT_PROTOCOL_V1_VALIDATION",
        "pass": not failed,
        "check_count": len(checks),
        "passed_check_count": sum(checks.values()),
        "checks": checks,
        "failed_checks": failed,
        "combined_protocol_sha256": lock["combined_protocol_sha256"],
        "raw_log_files_committed_to_git": 0,
        "raw_log_paths": [path.relative_to(root).as_posix() for path in raw_paths],
    }
    (root / "validation_result.json").write_text(json.dumps(result, indent=2, sort_keys=True) + "\n", encoding="utf-8", newline="\n")
    return result


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--root", type=Path, default=Path(__file__).resolve().parent)
    args = parser.parse_args()
    result = validate(args.root)
    print(result["validator"])
    if result["failed_checks"]:
        print(json.dumps({"failed_checks": result["failed_checks"]}, sort_keys=True))
    return 0 if result["pass"] else 2


if __name__ == "__main__":
    raise SystemExit(main())
