#!/usr/bin/env python3
"""Fail-closed validator for the completed bounded equivalence task."""

from __future__ import annotations

import csv
import json
from pathlib import Path
import sys
from typing import Any


ROOT = Path(__file__).resolve().parent
EXPECTED_HEAD = "7d48bf6c3b8932aa65d851c3cd70404404453cb3"
EXPECTED_STATUS = "PASS_L2_H1_SHADOW_INSTRUMENTATION_OFF_VS_ON_EQUIVALENCE_V1"
VALIDATOR_PASS = "PASS_L2_H1_SHADOW_INSTRUMENTATION_EQUIVALENCE_V1_VALIDATION"
TRIALS = (0, 24, 49, 74, 99)


def load(path: Path) -> Any:
    return json.loads(path.read_text(encoding="utf-8"))


def jsonl(path: Path) -> list[dict[str, Any]]:
    return [json.loads(line) for line in path.read_text(encoding="utf-8").splitlines() if line]


def main() -> int:
    checks: dict[str, bool] = {}
    errors: list[str] = []

    def check(name: str, condition: bool) -> None:
        checks[name] = bool(condition)
        if not condition:
            errors.append(name)

    required = [
        "README.md", "EQUIVALENCE_PROTOCOL.md", "paired_equivalence_contract.json",
        "equivalence_trial_selection.json", "paired_run_manifest.json", "environment_identity.json",
        "trace_schema.json", "trace_capture.py", "canonical_trace_hash.py", "compare_traces.py",
        "find_first_divergence.py", "arm_activation_validator.py", "self_consistency_results.json",
        "equivalence_matrix.csv", "equivalence_summary.json", "first_divergence_forensic.json",
        "first_divergence_context.md", "arm_c_log_sanity.json", "FINAL_CASE_DECISION.json",
        "run_manifest.json", "downstream_handoff.json", "DRAFT_PR_BODY.md",
        "report/REPORT_VALIDATE_L2_H1_SHADOW_INSTRUMENTATION_OFF_VS_ON_EQUIVALENCE_V1.md",
    ]
    required += [
        "audit/frozen_upstream_identity.json", "audit/protected_source_audit.json",
        "audit/no_method_mutation.json", "audit/no_intervention.json",
        "audit/no_pilot_no_formal_cohort.json", "audit/test_execution_evidence.json",
        "reviewers/control_theory_review.json", "reviewers/robotics_systems_review.json",
        "reviewers/software_reproducibility_review.json", "reviewers/scientific_claim_review.json",
    ]
    check("required_artifacts", all((ROOT / item).is_file() for item in required))

    pipeline = load(ROOT / "pipeline_result.json")
    upstream = load(ROOT / "audit" / "frozen_upstream_identity.json")
    protected = load(ROOT / "audit" / "protected_source_audit.json")
    selection = load(ROOT / "equivalence_trial_selection.json")
    pairing_contract = load(ROOT / "paired_equivalence_contract.json")
    self_result = load(ROOT / "self_consistency_results.json")
    c_sanity = load(ROOT / "arm_c_log_sanity.json")
    final = load(ROOT / "FINAL_CASE_DECISION.json")
    tests = load(ROOT / "audit" / "test_execution_evidence.json")

    check("pr97_exact_identity", upstream["expected_pr97_head"] == EXPECTED_HEAD == upstream["actual_pr97_head"] == upstream["local_head"])
    check("pr97_frozen_before_navigation", upstream["frozen_before_navigation"] is True)
    check("protected_source_unchanged", protected["all_match"] is True and protected["protected_blob_count"] == 17 and protected["protected_path_diff_count"] == 0)
    check("no_method_or_instrumentation_mutation", protected["controller_mutation_count"] == 0 and protected["instrumentation_mutation_count"] == 0)
    check("trial_manifest_frozen", selection["frozen_before_any_navigation_run"] is True and selection["results_observed_at_freeze"] is False and tuple(selection["selected_trial_ids"]) == TRIALS)
    check("no_outcome_conditioned_replacement", selection["outcome_conditioned_selection"] is False and selection["replacement_allowed"] is False)
    check("exact_tolerance_contract", pairing_contract["numeric_tolerance"] is None and pairing_contract["post_hoc_tolerance_change_allowed"] is False)

    check("pipeline_pass", pipeline["FINAL_STATUS"] == EXPECTED_STATUS and pipeline["selected_case"] == "CASE_A")
    check("run_counts", pipeline["real_qa_navigation_run_count"] == 21 and pipeline["native_off_run_count"] == 7 and pipeline["wrapper_off_run_count"] == 7 and pipeline["wrapper_on_run_count"] == 7)
    check("zero_mutation_and_intervention", all(pipeline[key] == 0 for key in ("controller_mutation_count", "instrumentation_mutation_count", "controller_intervention_count", "candidate_replacement_count")))
    check("zero_out_of_scope_execution", all(pipeline[key] == 0 for key in ("logging_pilot_run_count", "formal_on_policy_cohort_count", "formal_performance_metric_count", "formal_runtime_metric_count", "L3_implementation_count", "L4_implementation_count", "L5_implementation_count", "H2_implementation_count")))
    check("self_consistency_all_exact", all(self_result[arm]["valid"] and self_result[arm]["exact"] for arm in "ABC"))

    with (ROOT / "equivalence_matrix.csv").open(newline="", encoding="utf-8") as handle:
        matrix = list(csv.DictReader(handle))
    check("comparison_row_count", len(matrix) == 21 == pipeline["exact_comparison_count"])
    check("all_comparisons_exact", all(row["exact_match"] == "True" and row["pairing_identity_match"] == "True" and not row["first_divergence_field"] for row in matrix))
    check("all_pair_families_present", all(sum(row["pair"].startswith(prefix) for row in matrix) == 5 for prefix in ("A_VS_B_TRIAL_", "B_VS_C_TRIAL_", "A_VS_C_TRIAL_")))
    first_divergence = load(ROOT / "first_divergence_forensic.json")
    check("no_first_divergence", pipeline["first_divergence_count"] == 0 and first_divergence["first_divergence_count"] == 0 and first_divergence["status"] == "NONE")

    run_root = ROOT / "run_logs" / "compact_runs"
    run_ids = sorted(path.name for path in run_root.iterdir() if path.is_dir() and (path / "run_metadata.json").exists())
    check("fresh_process_run_count", len(run_ids) == 21)
    pids: list[int] = []
    pairing_hashes: set[str] = set()
    map_ids: set[str] = set()
    trace_required = {
        "step_id", "trial_id", "seed", "x_k", "u_des", "selected_u_k",
        "solver_success", "controller_branch", "plant_input_x", "plant_input_u",
        "plant_output_x_next", "termination_flag", "termination_reason",
        "goal_terminal_status", "goal", "map_authority_id",
    }
    all_trace_fields = True
    all_metadata_trace_match = True
    for run_id in run_ids:
        meta = load(run_root / run_id / "run_metadata.json")
        act = load(run_root / run_id / "arm_activation.json")
        env = load(run_root / run_id / "environment_identity.json")
        trace = load(ROOT / "traces" / f"{run_id}.json")
        pids.append(meta["pid"])
        pairing_hashes.add(env["pairing_identity_hash"])
        map_ids.add(env["map_authority_id"])
        all_metadata_trace_match &= meta["trace_hash"] == trace["primary_trace_semantic_hash"] and meta["trace_step_count"] == len(trace["steps"])
        all_trace_fields &= bool(trace["steps"]) and all(trace_required <= set(step) for step in trace["steps"])
        all_trace_fields &= all(step["selected_u_k"] == step["plant_input_u"] for step in trace["steps"])
        if run_id.startswith("self_a") or run_id.startswith("cross_a"):
            all_trace_fields &= act["wrapper_loaded"] is False and act["observer_enabled"] is False and act["worker_start_requested"] is False
        elif run_id.startswith("self_b") or run_id.startswith("cross_b"):
            all_trace_fields &= act["wrapper_loaded"] is True and act["observer_enabled"] is False and act["worker_start_requested"] is False
        else:
            all_trace_fields &= act["wrapper_loaded"] is True and act["observer_enabled"] is True and act["worker_start_requested"] is True
            all_trace_fields &= act["intended_state_valid"] is True and act["worker_processed_count"] == len(trace["steps"])
            all_trace_fields &= act["leftover_shadow_worker_count"] == 0 and act["worker_alive_after_shutdown"] is False
        all_trace_fields &= act["controller_authority"] is False and act["controller_intervention_count"] == 0 and act["selected_candidate_replacement_count"] == 0
    check("fresh_process_pid_unique", len(pids) == len(set(pids)) == 21)
    check("same_environment_and_map", len(pairing_hashes) == 1 and len(map_ids) == 1)
    check("trace_schema_and_alignment", all_trace_fields)
    check("trace_hash_metadata_match", all_metadata_trace_match)

    cross_exact = True
    for trial in TRIALS:
        traces = [load(ROOT / "traces" / f"cross_{arm}_trial{trial:03d}.json") for arm in "abc"]
        cross_exact &= len({item["primary_trace_semantic_hash"] for item in traces}) == 1
        cross_exact &= traces[0]["steps"] == traces[1]["steps"] == traces[2]["steps"]
    check("cross_arm_full_trace_exact", cross_exact)

    c_logs_valid = c_sanity["all_pass"] is True and c_sanity["run_count"] == 7
    for item in c_sanity["runs"]:
        inst = ROOT / "run_logs" / "c_instrumentation" / item["run_id"]
        captures = jsonl(inst / "step_capture_log.jsonl")
        results = jsonl(inst / "shadow_certificate_result_log.jsonl")
        health = jsonl(inst / "instrumentation_health_log.jsonl")
        manifest = load(inst / "map_authority_manifest.json")
        c_logs_valid &= len(captures) == item["capture_count"] == len(results) == item["result_count"]
        c_logs_valid &= len(health) == item["health_count"] and manifest["map_authority_id"] == item["map_authority_id"]
        capture_hashes = {row["payload_semantic_hash"] for row in captures}
        result_hashes = {row["payload_enqueue_semantic_hash"] for row in results}
        c_logs_valid &= capture_hashes == result_hashes and all(row["selected_candidate"]["u"] is not None for row in captures)
    check("arm_c_logs_parse_and_join", c_logs_valid)

    reviewers = [load(path) for path in sorted((ROOT / "reviewers").glob("*.json"))]
    check("four_reviewers_pass", len(reviewers) == 4 and all(item["verdict"] == "PASS" and item["recommended_case"] == "CASE_A" and not item["critical_blockers"] for item in reviewers))
    check("final_case_and_claim_boundary", final["selected_case"] == "CASE_A" and final["reviewer_case_votes"] == {"CASE_A": 4} and not final["unresolved_blockers"])
    check("compileall_and_unittest", tests["server_compileall"] == "PASS" and tests["server_unittest"] == "PASS_3_OF_3" and tests["local_unittest"] == "PASS_3_OF_3")
    check("pytest_if_available", tests["server_pytest"] == "NOT_AVAILABLE" and tests["local_pytest"] == "NOT_AVAILABLE" and tests["pytest_policy"] == "RUN_IF_AVAILABLE")
    check("git_diff_and_credentials", tests["git_diff_check"] == "PASS" and tests["credential_scan"] == "PASS_NO_MATCH")

    result = {
        "schema_version": "L2_H1_SHADOW_INSTRUMENTATION_EQUIVALENCE_VALIDATION_V1",
        "validator": VALIDATOR_PASS if not errors else "FAIL_L2_H1_SHADOW_INSTRUMENTATION_EQUIVALENCE_V1_VALIDATION",
        "pass": not errors,
        "checks": checks,
        "failed_checks": errors,
        "check_count": len(checks),
        "passed_check_count": sum(checks.values()),
    }
    (ROOT / "validation_result.json").write_text(json.dumps(result, indent=2, sort_keys=True) + "\n", encoding="utf-8", newline="\n")
    print(result["validator"])
    if errors:
        print("FAILED_CHECKS=" + ",".join(errors))
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
