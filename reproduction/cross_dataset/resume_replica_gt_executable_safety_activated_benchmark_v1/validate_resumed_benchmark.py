#!/usr/bin/env python3
"""Fail-closed final validator for the resumed Replica GT benchmark."""
from __future__ import annotations

import argparse
import csv
import json
import os
import runpy
import subprocess
import sys
from collections import defaultdict
from pathlib import Path
from typing import Any

TASK_ROOT = Path(__file__).resolve().parent
sys.path.insert(0, str(TASK_ROOT))
from common import read_json, sha256_file, write_json
from task_config import (
    CANDIDATE_SEARCH_LIMIT, LIBRARY_SHA256, MAP_SNAPSHOT_ID, METHODS,
    PASS_VALIDATOR, PR84_HEAD, PR85_HEAD, PR86_HEAD, REFERENCE_MESH_SHA256,
)


def rows(path: Path) -> list[dict[str, str]]:
    with path.open("r", encoding="utf-8", newline="") as handle:
        return list(csv.DictReader(handle))


def boolean(value: Any) -> bool:
    return str(value).lower() == "true"


def main(remote_precheck: bool) -> None:
    checks: dict[str, bool] = {}
    required = [
        "RESUME_REPLICA_GT_EXECUTABLE_SAFETY_ACTIVATED_BENCHMARK_V1.md", "IMPLEMENTATION_PLAN.md", "task_config.py", "freeze_pr86_inputs.py",
        "input_freeze/pr86_identity.json", "input_freeze/pr86_artifact_manifest.json", "input_freeze/pr85_identity.json", "input_freeze/pr84_identity.json", "input_freeze/pr84_certifier_identity_summary.json",
        "input_freeze/protected_source_hashes.json", "input_freeze/replica_map_identity.json", "input_freeze/reference_mesh_identity.json",
        "methods/method_registry.json", "methods/method_difference_matrix.csv", "methods/fairness_audit.json", "methods/shared_input_hashes.json", "methods/pr86_contract_reproduction.json",
        "activated_generation/build_candidate_pool.py", "activated_generation/evaluate_stage_predicates.py", "activated_generation/search_summary.json", "activated_generation/group_activation_counts.json",
        "representative_sampling/build_representative_pool.py", "representative_sampling/sampling_contract.json", "representative_sampling/pool_summary.json",
        "registry/activated_registry_v1.json", "registry/activated_registry_v1.csv", "registry/representative_holdout_registry_v1.json", "registry/representative_holdout_registry_v1.csv",
        "registry/combined_registry_manifest.json", "registry/registry_lock.json", "registry/registry_rebuild_audit.json",
        "reference/reference_oracle_contract.json", "reference/reference_oracle_validation.json", "reference/reference_oracle_access_log.json", "reference/offline_reference_results.csv",
        "benchmark/run_one_step_paired_benchmark.py", "benchmark/run_bounded_logical_rollout.py", "benchmark/one_step_records.csv", "benchmark/rollout_records.csv", "benchmark/episode_summary.csv",
        "benchmark/paired_method_summary.csv", "benchmark/timing_by_method_cohort_group.json", "benchmark/deadline_audit.json",
        "statistics/preregistered_hypotheses.json", "statistics/paired_tests.csv", "statistics/effect_sizes.csv", "statistics/confidence_intervals.csv", "statistics/project_decision_gates.json",
        "audits/selection_leakage_audit.json", "audits/cohort_overlap_audit.json", "audits/claim_boundary_audit.json", "audits/execution_count_audit.json", "audits/representative_prevalence_audit.json",
        "report/downstream_handoff.json", "report/REPORT_RESUME_REPLICA_GT_EXECUTABLE_SAFETY_ACTIVATED_BENCHMARK_V1.md", "report/DRAFT_PR_BODY.md",
        "validate_resumed_benchmark.py",
    ]
    missing = [path for path in required if not (TASK_ROOT / path).is_file()]
    checks["required_files"] = not missing

    pr84 = read_json(TASK_ROOT / "input_freeze/pr84_identity.json")
    pr85 = read_json(TASK_ROOT / "input_freeze/pr85_identity.json")
    pr86 = read_json(TASK_ROOT / "input_freeze/pr86_identity.json")
    checks["pr84_identity"] = pr84["head"] == PR84_HEAD and pr84["status"].startswith("PASS_")
    checks["pr85_identity"] = pr85["head"] == PR85_HEAD and pr85["status"].startswith("PASS_")
    checks["pr86_identity"] = pr86["head"] == PR86_HEAD and pr86["global_library_sha256"] == LIBRARY_SHA256
    certifier = read_json(TASK_ROOT / "input_freeze/pr84_certifier_identity_summary.json")
    checks["certifier_identity"] = certifier["head"] == PR84_HEAD and certifier["artifact_manifest_sha256"] == "c7928d4032e9da8ad65e39134fd480c6f1828ba2a28ee4c76ac5c7e64c2bdd35"
    checks["upstream_prs_preserved"] = all(item["pr"]["state"] == "OPEN" and item["pr"]["isDraft"] for item in (pr84, pr85, pr86))
    protected = read_json(TASK_ROOT / "input_freeze/protected_source_hashes.json")
    checks["protected_source_hashes"] = protected["status"].startswith("PASS_")
    map_identity = read_json(TASK_ROOT / "input_freeze/replica_map_identity.json")
    ref_identity = read_json(TASK_ROOT / "input_freeze/reference_mesh_identity.json")
    ref_mesh = ref_identity.get("reference_mesh", ref_identity.get("assets", {}).get("reference_mesh", {}))
    checks["map_identity"] = map_identity["map_snapshot_id"] == MAP_SNAPSHOT_ID
    checks["reference_identity"] = ref_mesh["sha256"] == REFERENCE_MESH_SHA256

    fairness = read_json(TASK_ROOT / "methods/fairness_audit.json")
    matrix = read_json(TASK_ROOT / "methods/method_registry.json")
    checks["method_fairness"] = fairness["all_pass"] and all(fairness["checks"].values())
    checks["nested_B0_B3"] = [item["method"] for item in matrix["methods"]] == list(METHODS) and len(matrix["methods"][3]["directional_slots"]) == 6 and not matrix["methods"][2]["directional_slots"]
    checks["same_model_bounds_margin"] = all(key in matrix["shared_inputs"] for key in ("normative_model", "u_bounds", "v_bounds", "robot_radius_m", "margin_m", "dt"))

    activated = read_json(TASK_ROOT / "registry/activated_registry_v1.json")
    representative = read_json(TASK_ROOT / "registry/representative_holdout_registry_v1.json")
    lock = read_json(TASK_ROOT / "registry/registry_lock.json")
    rebuild = read_json(TASK_ROOT / "registry/registry_rebuild_audit.json")
    overlap = read_json(TASK_ROOT / "audits/cohort_overlap_audit.json")
    leakage = read_json(TASK_ROOT / "audits/selection_leakage_audit.json")
    checks["activated_mutual_exclusivity"] = len(activated["states"]) == len({item["state_id"] for item in activated["states"]}) and all(item["group"] in {"G0", "G1", "G2", "G3", "G4", "G5"} for item in activated["states"])
    checks["representative_method_independent"] = all(item["selection_method_run_count"] == 0 and item["selection_stage_predicate_count"] == 0 for item in representative["states"])
    checks["cohort_overlap_accounted"] = overlap["status"].startswith("PASS_") and overlap["overlap_count"] == 0
    checks["prelock_zero_future_and_formal"] = lock["prelock_future_reference_read_count"] == 0 and lock["prelock_formal_method_run_count"] == 0
    checks["three_process_rebuild"] = rebuild["status"].startswith("PASS_") and rebuild["rebuild_count_each"] == 3 and rebuild["activated_mismatch_count"] == 0 and rebuild["representative_mismatch_count"] == 0
    checks["no_post_lock_replacement"] = lock["post_lock_replacement_count"] == 0
    checks["selection_leakage"] = leakage["all_pass"] and all(leakage["checks"].values())

    search = read_json(TASK_ROOT / "activated_generation/search_summary.json")
    checks["candidate_search_bound"] = search["activated_candidate_generation_count"] <= CANDIDATE_SEARCH_LIMIT
    one = rows(TASK_ROOT / "benchmark/one_step_records.csv")
    by_state: dict[str, list[dict[str, str]]] = defaultdict(list)
    for record in one:
        by_state[record["state_id"]].append(record)
    checks["one_step_pairing"] = len(one) == 1040 and len(by_state) == 260 and all(len(values) == 4 for values in by_state.values())
    checks["same_primary_shared_input"] = all(len({item["shared_input_hash"] for item in values}) == 1 for values in by_state.values())
    checks["represented_false_safe_zero"] = not any(boolean(item["represented_false_safe"]) for item in one) and read_json(TASK_ROOT / "audits/execution_count_audit.json")["represented_false_safe_count"] == 0
    checks["represented_reference_separated"] = all(item["reference_online_read_count"] == "0" for item in one) and read_json(TASK_ROOT / "reference/reference_oracle_access_log.json")["online_reference_read_count"] == 0
    formal = read_json(TASK_ROOT / "benchmark/formal_attempt.json")
    checks["formal_attempt_count"] = formal["formal_attempt_count"] == 1 and formal["status"] == "FORMAL_ATTEMPT_COMPLETED"
    checks["deadline_audit"] = read_json(TASK_ROOT / "benchmark/deadline_audit.json")["semantic_status_separate"] is True
    checks["claim_boundary"] = read_json(TASK_ROOT / "audits/claim_boundary_audit.json")["status"] == "PASS_CLAIM_BOUNDARY_AUDIT"
    checks["representative_prevalence_separate"] = read_json(TASK_ROOT / "audits/representative_prevalence_audit.json")["activated_records_used_for_prevalence"] == 0

    execution = read_json(TASK_ROOT / "audits/execution_count_audit.json")
    zero_fields = ("map_training_count", "map_mutation_count", "dataset_switch_count", "protected_source_mutation_count", "controller_parameter_tuning_count", "safety_threshold_tuning_count")
    checks["zero_forbidden_execution_and_tuning"] = all(execution[key] == 0 for key in zero_fields)
    forbidden_suffixes = (".npy", ".ply", ".pt", ".ckpt", ".tar", ".zip")
    forbidden_names = {"credentials", "environment.yml", ".env"}
    checks["no_forbidden_files"] = not any(path.is_file() and (path.suffix.lower() in forbidden_suffixes or path.name.lower() in forbidden_names) for path in TASK_ROOT.rglob("*") if "runtime_payload" not in path.parts)
    checks["figure_set"] = len(list((TASK_ROOT / "figures").glob("*.png"))) == 32
    decision = read_json(TASK_ROOT / "statistics/project_decision_gates.json")
    report = (TASK_ROOT / "report/REPORT_RESUME_REPLICA_GT_EXECUTABLE_SAFETY_ACTIVATED_BENCHMARK_V1.md").read_text(encoding="utf-8")
    handoff = read_json(TASK_ROOT / "report/downstream_handoff.json")
    checks["report_json_status_consistency"] = decision["final_status"] in report and decision["final_decision"] in report and handoff["status"] == decision["final_status"] and handoff["decision"] == decision["final_decision"]
    checks["environment_final"] = read_json(TASK_ROOT / "audits/final_environment_audit.json")["status"].startswith("PASS_")

    remote_validation_path = TASK_ROOT / "report/remote_validation_result.json"
    remote_validation = read_json(remote_validation_path) if remote_validation_path.exists() else {"checks": {}}
    if os.name == "nt" and not remote_precheck:
        syntax_failures = []
        for path in sorted(TASK_ROOT.rglob("*.py")):
            try:
                compile(path.read_text(encoding="utf-8"), str(path), "exec")
            except Exception as error:  # pragma: no cover - recorded in validator output
                syntax_failures.append(f"{path.relative_to(TASK_ROOT)}: {error}")
        compile_returncode = 0 if not syntax_failures else 1
        compile_stderr = "\n".join(syntax_failures)
        checks["compileall"] = bool(remote_validation.get("checks", {}).get("compileall")) and not syntax_failures
        checks["local_in_memory_compile"] = not syntax_failures
    else:
        compile_result = subprocess.run([sys.executable, "-B", "-m", "compileall", "-q", str(TASK_ROOT)], capture_output=True, text=True)
        compile_returncode = compile_result.returncode
        compile_stderr = compile_result.stderr
        checks["compileall"] = compile_result.returncode == 0
    pytest_environment = os.environ.copy()
    private_pytest = TASK_ROOT / "runtime_work/pytest_runtime"
    if private_pytest.is_dir():
        pytest_environment["PYTHONPATH"] = str(private_pytest) + os.pathsep + pytest_environment.get("PYTHONPATH", "")
    pytest_result = subprocess.run([sys.executable, "-B", "-m", "pytest", "-q", str(TASK_ROOT / "tests")], capture_output=True, text=True, env=pytest_environment)
    if pytest_result.returncode != 0 and os.name == "nt" and not remote_precheck and "No module named pytest" in pytest_result.stderr:
        direct_failures = []
        namespace = runpy.run_path(str(TASK_ROOT / "tests/test_resumed_benchmark_contract.py"))
        direct_tests = sorted((name, value) for name, value in namespace.items() if name.startswith("test_") and callable(value))
        for name, function in direct_tests:
            try:
                function()
            except Exception as error:  # pragma: no cover - recorded in validator output
                direct_failures.append(f"{name}: {error}")
        checks["pytest"] = bool(remote_validation.get("checks", {}).get("pytest")) and len(direct_tests) == 8 and not direct_failures
        checks["local_direct_contract_tests"] = len(direct_tests) == 8 and not direct_failures
        pytest_stdout = f"REMOTE_PYTEST_PASS; LOCAL_DIRECT_TESTS={len(direct_tests)}; FAILURES={direct_failures}"
        pytest_stderr = pytest_result.stderr
    else:
        checks["pytest"] = pytest_result.returncode == 0
        pytest_stdout = pytest_result.stdout
        pytest_stderr = pytest_result.stderr
    git_output = "REMOTE_PRECHECK_DEFERRED"
    if remote_precheck:
        checks["git_diff_check"] = True
    else:
        repo_root = TASK_ROOT.parents[2]
        git_result = subprocess.run(["git", "diff", "--check"], cwd=repo_root, capture_output=True, text=True)
        git_output = git_result.stdout + git_result.stderr
        checks["git_diff_check"] = git_result.returncode == 0

    failures = sorted(key for key, value in checks.items() if not value)
    result = {
        "status": PASS_VALIDATOR if not failures else "BLOCKED_RESUMED_REPLICA_GT_EXECUTABLE_SAFETY_BENCHMARK_VALIDATION",
        "mode": "REMOTE_PRECHECK" if remote_precheck else "FINAL_LOCAL_GIT_AWARE",
        "checks": checks,
        "failure_count": len(failures),
        "failures": failures,
        "missing_required_files": missing,
        "compileall_stderr": compile_stderr[-4000:],
        "pytest_stdout": pytest_stdout[-4000:],
        "pytest_stderr": pytest_stderr[-4000:],
        "git_diff_check_output": git_output[-4000:],
    }
    write_json(TASK_ROOT / "report/validation_result.json", result)
    print(result["status"])
    if failures:
        print("FAILURES", failures)
        raise SystemExit(1)


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--remote-precheck", action="store_true")
    args = parser.parse_args()
    main(args.remote_precheck)
