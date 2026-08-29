#!/usr/bin/env python3
"""Validate compact logging-pilot artifacts without opening server raw logs."""

from __future__ import annotations

import csv
import json
from pathlib import Path
import subprocess
from typing import Any


TASK = Path(__file__).resolve().parent
REPO = TASK.parents[2]
EXPECTED_HEAD = "b47b0e924804e3e446b1f9c184ee5ea5d268d613"
EXPECTED_IDS = [10, 30, 50, 70, 90]
RATE_KEYS = (
    "capture_completeness", "selected_u_completeness", "map_authority_completeness",
    "reachability_completeness", "shadow_result_completion", "join_completeness",
)
ERROR_KEYS = (
    "N_queue_drop", "N_serialization_error", "N_worker_exception", "N_worker_unavailable",
    "N_alignment_failure", "N_schema_failure", "N_map_authority_failure",
    "N_shutdown_incomplete", "N_sequence_gap", "N_duplicate_payload", "N_duplicate_result",
    "N_orphan_result", "N_capture_without_result",
)


def load(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def main() -> int:
    upstream = load(TASK / "audit/upstream_identity.json")
    protected = load(TASK / "audit/protected_no_mutation.json")
    selection = load(TASK / "pilot_trial_selection.json")
    exclusion = load(TASK / "formal_cohort_exclusion.json")
    manifest = load(TASK / "pilot_run_manifest.json")
    summary = load(TASK / "pilot_overall_summary.json")
    join = load(TASK / "join_integrity.json")
    sequence = load(TASK / "sequence_integrity.json")
    decision = load(TASK / "FINAL_CASE_DECISION.json")
    with (TASK / "pilot_anomalies.csv").open(encoding="utf-8", newline="") as handle:
        anomaly_rows = list(csv.DictReader(handle))

    task_files = [path for path in TASK.rglob("*") if path.is_file()]
    raw_in_git = [
        path.relative_to(TASK).as_posix() for path in task_files
        if path.suffix == ".jsonl" or "raw_runs" in path.parts or "raw_logs" in path.parts
    ]
    git_diff_check = subprocess.run(
        ["git", "diff", "--check"], cwd=REPO, text=True, capture_output=True, check=False,
    )
    runs = manifest.get("runs", [])
    environments = [run.get("environment", {}) for run in runs]
    environment_hashes = {env.get("pairing_identity_hash") for env in environments if env}
    map_ids = {env.get("map_authority_id") for env in environments if env}

    checks = {
        "pr98_exact_identity": upstream.get("identity_match") is True and upstream.get("pr", {}).get("headRefOid") == EXPECTED_HEAD,
        "protected_identity_unchanged": protected.get("all_match") is True and protected.get("protected_path_diff_count") == 0,
        "no_method_or_instrumentation_mutation": protected.get("controller_mutation_count") == 0 and protected.get("instrumentation_mutation_count") == 0,
        "frozen_trial_selection": selection.get("selected_trial_ids") == EXPECTED_IDS and selection.get("frozen_before_any_pilot_navigation_run") is True and selection.get("outcome_conditioned_selection") is False,
        "exactly_five_valid_wrapper_on_runs": len(runs) == 5 and [run.get("trial_id") for run in runs] == EXPECTED_IDS and all(run.get("arm") == "WRAPPER_ON" and run.get("exit_code") == 0 and run.get("activation_valid") is True and run.get("retry_count") == 0 for run in runs),
        "single_environment_identity": len(environment_hashes) == 1,
        "single_map_authority_identity": len(map_ids) == 1,
        "independent_denominator_resolved": summary.get("denominator_resolved") is True and summary.get("N_intended_steps", 0) > 0,
        "capture_equation": summary.get("N_captured_payloads") == summary.get("N_intended_steps"),
        "selected_u_equation": summary.get("N_valid_selected_u") == summary.get("N_intended_steps"),
        "payload_hash_equation": summary.get("N_valid_payload_hash") == summary.get("N_intended_steps"),
        "map_authority_equation": summary.get("N_map_authority_resolved") == summary.get("N_intended_steps"),
        "reachability_equation": summary.get("N_reachability_complete") == summary.get("N_intended_steps"),
        "terminal_result_equation": summary.get("N_terminal_shadow_records") == summary.get("N_captured_payloads"),
        "join_equation": summary.get("N_joinable_records") == summary.get("N_captured_payloads"),
        "all_completeness_rates_one": all(summary.get(key) == 1.0 for key in RATE_KEYS),
        "all_error_counts_zero": all(summary.get(key) == 0 for key in ERROR_KEYS),
        "join_integrity": join.get("pass") is True,
        "sequence_integrity": sequence.get("pass") is True,
        "health_separate_from_l2_unknown": summary.get("instrumentation_health_separate_from_l2_unknown") is True,
        "no_anomalies": len(anomaly_rows) == 1 and anomaly_rows[0].get("category") == "NONE",
        "pilot_formal_exclusion": exclusion.get("data_role") == "PILOT_QA_ONLY" and exclusion.get("eligible_for_formal_prospective_cohort") is False and all(run.get("data_role") == "PILOT_QA_ONLY" and run.get("eligible_for_formal_prospective_cohort") is False for run in runs),
        "zero_authority_and_replacement": summary.get("controller_intervention_count") == 0 and summary.get("candidate_replacement_count") == 0,
        "zero_formal_or_claim_metrics": summary.get("formal_on_policy_cohort_count") == 0 and summary.get("formal_performance_metric_count") == 0 and summary.get("formal_runtime_metric_count") == 0,
        "raw_logs_excluded_from_git": not raw_in_git,
        "case_a_frozen": decision.get("selected_case") == summary.get("selected_case") == "CASE_A",
        "git_diff_check": git_diff_check.returncode == 0,
    }
    failures = [key for key, value in checks.items() if not value]
    result = {
        "validator": "PASS_L2_H1_SHADOW_LOGGING_COMPLETENESS_PILOT_V1_VALIDATION" if not failures else "FAIL_L2_H1_SHADOW_LOGGING_COMPLETENESS_PILOT_V1_VALIDATION",
        "pass": not failures,
        "check_count": len(checks),
        "passed_check_count": sum(checks.values()),
        "checks": checks,
        "failed_checks": failures,
        "raw_log_files_committed_to_git": len(raw_in_git),
        "raw_log_paths": raw_in_git,
    }
    (TASK / "validation_result.json").write_text(json.dumps(result, indent=2, sort_keys=True) + "\n", encoding="utf-8", newline="\n")
    print(result["validator"])
    if failures:
        print("failed_checks=" + ",".join(failures))
    return 0 if not failures else 2


if __name__ == "__main__":
    raise SystemExit(main())
