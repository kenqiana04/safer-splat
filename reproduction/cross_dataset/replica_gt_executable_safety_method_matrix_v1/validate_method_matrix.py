"""Fail-closed validation for the method-design-only B0-B3 contract freeze."""
from __future__ import annotations

import json
from pathlib import Path
import subprocess

from common import write_json
from task_config import PASS_DECISION, PASS_NEXT, PASS_STATUS, PASS_VALIDATION, PR84_HEAD, PR85_HEAD, REPO_ROOT, TASK_ROOT


def load(relative: str):
    return json.loads((TASK_ROOT / relative).read_text(encoding="utf-8"))


def main() -> None:
    required = (
        "IMPLEMENTATION_PLAN.md", "freeze_pr85_inputs.py", "audit_upstream_contract.py", "materialize_pr84_smoke_payload.py", "task_config.py",
        "input_freeze/pr85_identity.json", "input_freeze/pr85_artifact_manifest.json", "input_freeze/pr84_certifier_identity.json", "input_freeze/protected_source_hashes.json", "input_freeze/replica_map_identity.json", "input_freeze/reference_mesh_identity.json",
        "audits/pr84_candidate_contract_gap.json", "audits/pr85_fairness_blocker_reproduction.json", "audits/source_semantics_trace.csv", "audits/three_process_determinism.json", "audits/execution_count_audit.json",
        "methods/method_registry.json", "methods/method_difference_matrix.csv", "methods/nested_causal_contract.md", "methods/method_canonical_identity.json", "methods/b2_primary_and_braking_wrapper.py", "methods/b3_directional_library_wrapper.py", "methods/fairness_audit.json",
        "alternative_library/alternative_library_contract.json", "alternative_library/alternative_library_slot_schema.json", "alternative_library/alternative_library_source_manifest.json", "alternative_library/alternative_library_identity.json",
        "smoke/generator_only_replica_smoke_records.json", "smoke/three_process_determinism.json", "report/test_execution.json", "report/system_final_state.json", "report/downstream_handoff.json", "report/REPORT_FREEZE_REPLICA_GT_EXECUTABLE_SAFETY_METHOD_MATRIX_V1.md", "report/DRAFT_PR_BODY.md",
    )
    freeze, pr84, fairness = load("input_freeze/pr85_identity.json"), load("input_freeze/pr84_certifier_identity.json"), load("methods/fairness_audit.json")
    map_identity, ref_identity = load("input_freeze/replica_map_identity.json"), load("input_freeze/reference_mesh_identity.json")
    smoke, smoke_determinism, counts, deterministic = load("smoke/generator_only_replica_smoke_records.json"), load("smoke/three_process_determinism.json"), load("audits/execution_count_audit.json")["counters"], load("audits/three_process_determinism.json")
    method_registry, library_identity, tests, system = load("methods/method_registry.json"), load("alternative_library/alternative_library_identity.json"), load("report/test_execution.json"), load("report/system_final_state.json")
    pr85_live = json.loads(subprocess.run(["gh", "pr", "view", "85", "--json", "state,isDraft,mergeable,mergedAt,headRefOid"], cwd=REPO_ROOT, check=True, capture_output=True, text=True).stdout)
    pr84_live = json.loads(subprocess.run(["gh", "pr", "view", "84", "--json", "state,isDraft,mergeable,mergedAt,headRefOid"], cwd=REPO_ROOT, check=True, capture_output=True, text=True).stdout)
    source = "\n".join(path.read_text(encoding="utf-8") for path in (TASK_ROOT / "alternative_library").glob("*.py"))
    forbidden_imports = ("import reference", "from reference", "import oracle", "from oracle", "import benchmark", "from benchmark")
    tracked = subprocess.run(["git", "ls-files", "--", "reproduction/cross_dataset/replica_gt_executable_safety_method_matrix_v1"], cwd=REPO_ROOT, check=True, capture_output=True, text=True).stdout.splitlines()
    cached = [path for path in tracked if path.endswith((".pyc", ".pyo")) or "/__pycache__/" in path.replace("\\", "/")]
    protected_status = subprocess.run(["git", "status", "--porcelain=v1"], cwd=REPO_ROOT, check=True, capture_output=True, text=True).stdout.splitlines()
    scope_ok = all("reproduction/cross_dataset/replica_gt_executable_safety_method_matrix_v1/" in row.replace("\\", "/") for row in protected_status)
    matrix = {item["id"]: item for item in method_registry["methods"]}
    zero = ("map_training_count", "map_mutation_count", "dataset_switch_count", "protected_source_mutation_count", "controller_parameter_tuning_count", "safety_threshold_tuning_count", "benchmark_candidate_search_count", "benchmark_registry_count", "reference_query_count", "formal_method_run_count", "logical_rollout_count")
    report = (TASK_ROOT / "report/REPORT_FREEZE_REPLICA_GT_EXECUTABLE_SAFETY_METHOD_MATRIX_V1.md").read_text(encoding="utf-8")
    checks = {
        "required_files": all((TASK_ROOT / item).exists() for item in required), "pr85_identity": freeze["status"] == "PASS_PR85_PR84_AND_EXTERNAL_INPUT_FREEZE",
        "pr85_preserved": pr85_live == {"headRefOid": PR85_HEAD, "isDraft": True, "mergeable": "MERGEABLE", "mergedAt": None, "state": "OPEN"},
        "pr84_preserved": pr84_live == {"headRefOid": PR84_HEAD, "isDraft": True, "mergeable": "MERGEABLE", "mergedAt": None, "state": "OPEN"},
        "blocker_reproduced": load("audits/pr85_fairness_blocker_reproduction.json")["status"] == "PASS_PR85_BLOCKER_REPRODUCED",
        "map_identity": map_identity["status"] == "PASS_REPLICA_GT_FINE_IDENTITY", "reference_identity_no_query": ref_identity["status"] == "PASS_OFFICIAL_REPLICA_REFERENCE_IDENTITY" and ref_identity["reference_query_count"] == 0,
        "fairness": fairness["status"] == "PASS_METHOD_FAIRNESS_CONTRACT_FREEZE" and all(fairness["checks"].values()),
        "matrix_complete": set(matrix) == {"B0_CURRENT_CBF_ONLY", "B1_PLUS_SWEPT_SEGMENT", "B2_PLUS_TERMINAL_BACKUP_WITH_BUILTIN_BRAKING", "B3_FULL_UNIFIED_WITH_FROZEN_DIRECTIONAL_ALTERNATIVES"},
        "b2_b3_braking_parity": matrix["B2_PLUS_TERMINAL_BACKUP_WITH_BUILTIN_BRAKING"]["candidates"][-1] == matrix["B3_FULL_UNIFIED_WITH_FROZEN_DIRECTIONAL_ALTERNATIVES"]["candidates"][-1] == "DETERMINISTIC_BRAKING" and matrix["B2_PLUS_TERMINAL_BACKUP_WITH_BUILTIN_BRAKING"]["external_alternative_controls"] == [],
        "b3_only_six_slots": len(matrix["B3_FULL_UNIFIED_WITH_FROZEN_DIRECTIONAL_ALTERNATIVES"]["candidates"]) == 8 and library_identity["library_id"] == "REPLICA_GT_REPRESENTED_MAP_DIRECTIONAL_ALTERNATIVE_LIBRARY_V1",
        "no_forbidden_import": not any(item in source for item in forbidden_imports), "smoke": smoke["status"] == "GENERATOR_ONLY_REPLICA_SMOKE_PASS" and smoke["state_count"] == 25,
        "zero_benchmark": all(counts[key] == 0 for key in zero), "determinism": deterministic["process_determinism_run_count"] == 3 and deterministic["process_determinism_mismatch_count"] == 0 and smoke_determinism["process_count"] == 3 and smoke_determinism["mismatch_count"] == 0,
        "actuator_nonfinite": counts["actuator_violation_count"] == 0 and counts["nonfinite_output_count"] == 0,
        "test_suite": tests["source_compile"]["exit_code"] == 0 and tests["pytest"]["exit_code"] == 0,
        "figures": len(list((TASK_ROOT / "figures").glob("*.png"))) >= 20, "no_pycache": not cached,
        "no_forbidden_artifacts": not any(path.suffix.lower() in {".npy", ".npz", ".ply", ".ckpt", ".tar", ".zip"} for path in TASK_ROOT.rglob("*") if path.is_file()),
        "scope": scope_ok, "gpu_clean": system["gpu1_compute_process_count"] == 0 and system["task_owned_remote_process_count"] == 0,
        "watchdog": system["status"] == "PASS_FINAL_SYSTEM_READONLY_CHECK", "report_consistent": all(value in report for value in (PASS_STATUS, PASS_DECISION, PASS_NEXT)),
    }
    failed = sorted(key for key, value in checks.items() if not value)
    result = {"status": PASS_VALIDATION if not failed else "BLOCKED_REPLICA_GT_EXECUTABLE_SAFETY_METHOD_MATRIX_FREEZE_VALIDATION", "final_status": PASS_STATUS if not failed else "BLOCKED_BY_METHOD_FREEZE_VALIDATION", "checks": checks, "failed_checks": failed, "file_count": sum(1 for path in TASK_ROOT.rglob("*") if path.is_file()), "figure_count": len(list((TASK_ROOT / "figures").glob("*.png"))), "pytest_passed": tests["pytest"]["passed_count"]}
    write_json(TASK_ROOT / "report/validation_result.json", result)
    if failed:
        raise SystemExit(result["status"] + ":" + ",".join(failed))
    print(result["status"])


if __name__ == "__main__":
    main()
