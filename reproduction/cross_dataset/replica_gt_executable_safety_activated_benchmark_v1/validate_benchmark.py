"""Validate the identity-complete, no-execution fairness-blocker package."""
from __future__ import annotations

import json
from pathlib import Path
import subprocess

from common import write_json
from task_config import BLOCK_DECISION, BLOCK_NEXT, BLOCK_STATUS, PR84_HEAD, REPO_ROOT, TASK_ROOT


def load(relative):
    return json.loads((TASK_ROOT / relative).read_text(encoding="utf-8"))


def main() -> None:
    required = [
        "BUILD_REPLICA_GT_EXECUTABLE_SAFETY_ACTIVATED_BENCHMARK_V1.md", "IMPLEMENTATION_PLAN.md", "freeze_pr84_inputs.py", "task_config.py",
        "input_freeze/pr84_identity.json", "input_freeze/pr84_artifact_manifest.json", "input_freeze/protected_source_hashes.json", "input_freeze/replica_map_identity.json", "input_freeze/reference_mesh_identity.json",
        "methods/method_registry.json", "methods/method_difference_matrix.csv", "methods/fairness_audit.json", "methods/shared_input_hashes.json",
        "scenario_generation/build_candidate_pool.py", "scenario_generation/evaluate_stage_predicates.py", "scenario_generation/physical_admissibility_contract.json", "scenario_generation/physical_admissibility_audit.csv", "scenario_generation/candidate_search_summary.json", "scenario_generation/group_activation_counts.json",
        "registry/replica_gt_executable_safety_registry_v1.json", "registry/replica_gt_executable_safety_registry_v1.csv", "registry/registry_lock.json", "registry/registry_rebuild_audit.json",
        "reference/reference_oracle_contract.json", "reference/reference_oracle_validation.json", "reference/reference_oracle_access_log.json", "reference/offline_reference_results.csv",
        "benchmark/run_one_step_paired_benchmark.py", "benchmark/run_bounded_logical_rollout.py", "benchmark/one_step_records.csv", "benchmark/rollout_records.csv", "benchmark/episode_summary.csv", "benchmark/paired_method_summary.csv", "benchmark/timing_by_method_group.json", "benchmark/deadline_audit.json",
        "statistics/preregistered_hypotheses.json", "statistics/paired_tests.csv", "statistics/effect_sizes.csv", "statistics/confidence_intervals.csv",
        "audits/selection_leakage_audit.json", "audits/claim_boundary_audit.json", "audits/cohort_overlap_audit.json", "audits/execution_count_audit.json",
        "report/validation_result.json", "report/downstream_handoff.json", "report/REPORT_BUILD_REPLICA_GT_EXECUTABLE_SAFETY_ACTIVATED_BENCHMARK_V1.md", "report/DRAFT_PR_BODY.md", "validate_benchmark.py",
    ]
    freeze, fairness = load("input_freeze/pr84_identity.json"), load("methods/fairness_audit.json")
    map_id, ref_id = load("input_freeze/replica_map_identity.json"), load("input_freeze/reference_mesh_identity.json")
    counters = load("audits/execution_count_audit.json")["counters"]
    system, tests = load("report/system_final_state.json"), load("report/test_execution.json")
    report = (TASK_ROOT / "report/REPORT_BUILD_REPLICA_GT_EXECUTABLE_SAFETY_ACTIVATED_BENCHMARK_V1.md").read_text(encoding="utf-8")
    pr = json.loads(subprocess.run(["gh", "pr", "view", "84", "--json", "state,isDraft,mergeable,mergedAt,headRefOid"], cwd=REPO_ROOT, check=True, capture_output=True, text=True).stdout)
    status_rows = subprocess.run(["git", "status", "--porcelain=v1"], cwd=REPO_ROOT, check=True, capture_output=True, text=True).stdout.splitlines()
    scope_ok = all("reproduction/cross_dataset/replica_gt_executable_safety_activated_benchmark_v1/" in row.replace("\\", "/") for row in status_rows)
    forbidden = [path for path in TASK_ROOT.rglob("*") if path.is_file() and path.suffix.lower() in {".npy", ".npz", ".ply", ".zip", ".tar", ".gz", ".ckpt"}]
    pycache = [path for path in TASK_ROOT.rglob("*") if path.name == "__pycache__" or path.suffix == ".pyc"]
    zero_keys = ["candidate_generation_count", "physical_valid_count", "stage_predicate_evaluation_count", "registry_state_count", "registry_rebuild_count", "prelock_future_reference_read_count", "prelock_formal_rollout_count", "reference_online_read_count", "one_step_method_run_count", "logical_episode_count", "logical_control_step_count", "formal_attempt_count", "map_training_count", "map_mutation_count", "dataset_switch_count", "controller_parameter_tuning_count", "safety_threshold_tuning_count", "protected_source_mutation_count"]
    checks = {
        "required_files_present": all((TASK_ROOT / path).exists() or path == "report/validation_result.json" for path in required),
        "pr84_identity": freeze["status"] == "PASS_PR84_AND_EXTERNAL_INPUT_FREEZE",
        "pr84_preserved": pr == {"headRefOid": PR84_HEAD, "isDraft": True, "mergeable": "MERGEABLE", "mergedAt": None, "state": "OPEN"},
        "map_identity": map_id["status"] == "PASS_REPLICA_GT_FINE_IDENTITY",
        "reference_identity": ref_id["status"] == "PASS_OFFICIAL_REPLICA_REFERENCE_IDENTITY",
        "fairness_blocker_is_genuine": fairness["status"] == BLOCK_STATUS and not fairness["fairness_pass"],
        "missing_library_contract_explicit": all(not fairness["facts"][key] for key in ("concrete_alternative_acceleration_values_frozen", "concrete_alternative_candidate_ids_frozen", "alternative_library_size_frozen", "alternative_library_canonical_identity_frozen")),
        "zero_execution_boundary": all(counters[key] == 0 for key in zero_keys),
        "selection_leakage_zero": load("audits/selection_leakage_audit.json")["status"] == "PASS_NO_SELECTION_OCCURRED",
        "fail_closed_not_safe_stop": load("audits/claim_boundary_audit.json")["fail_closed_not_safe_stop"],
        "candidate_exhaustion_not_unrecoverable": load("audits/claim_boundary_audit.json")["candidate_exhaustion_not_unrecoverable"],
        "represented_reference_separated": load("audits/claim_boundary_audit.json")["represented_reference_separated"],
        "deadline_audit_present": load("benchmark/deadline_audit.json")["decision_count"] == 0,
        "syntax_compile": tests["syntax_compile"]["exit_code"] == 0,
        "pytest": tests["pytest"]["exit_code"] == 0 and tests["pytest"]["passed_count"] >= 6,
        "figure_count": len(list((TASK_ROOT / "figures").glob("*.png"))) >= 25,
        "no_forbidden_files": not forbidden,
        "no_repository_pycache": not pycache,
        "no_large_files": all(path.stat().st_size < 1_000_000 for path in TASK_ROOT.rglob("*") if path.is_file()),
        "protected_scope_only": scope_ok,
        "gpu_clean": system["gpu1_compute_process_count"] == 0 and system["task_owned_remote_process_count"] == 0,
        "watchdog_ssh_preserved": system["status"] == "PASS_FINAL_SYSTEM_READONLY_CHECK",
        "report_status_consistent": BLOCK_STATUS in report and BLOCK_DECISION in report and BLOCK_NEXT in report,
    }
    failed = sorted(key for key, value in checks.items() if not value)
    result = {"status": "PASS_REPLICA_GT_EXECUTABLE_SAFETY_ACTIVATED_BENCHMARK_VALIDATION" if not failed else "BLOCKED_REPLICA_GT_EXECUTABLE_SAFETY_ACTIVATED_BENCHMARK_VALIDATION", "final_status": BLOCK_STATUS, "checks": checks, "failed_checks": failed, "file_count": sum(1 for path in TASK_ROOT.rglob("*") if path.is_file()), "figure_count": len(list((TASK_ROOT / "figures").glob("*.png"))), "pytest_passed": tests["pytest"]["passed_count"]}
    write_json(TASK_ROOT / "report/validation_result.json", result)
    if failed:
        raise SystemExit(result["status"] + ":" + ",".join(failed))
    print(result["status"])


if __name__ == "__main__":
    main()
