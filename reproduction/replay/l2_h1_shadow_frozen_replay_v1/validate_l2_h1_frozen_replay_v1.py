"""Fail-closed validator for the frozen historical L2/H1 replay task."""
from __future__ import annotations

from collections import Counter
import importlib.util
import json
from pathlib import Path
import re
import subprocess
import sys
from typing import Any

from replay_common import PR94_HEAD, REPO_ROOT, TASK_ROOT, read_json, sha256_file, write_json


REQUIRED = [
    "README.md", "FROZEN_REPLAY_PROTOCOL.md", "source_inventory.csv", "source_inventory.json",
    "source_universe_freeze.json", "replayability_audit.csv", "replayability_reason_breakdown.csv",
    "frozen_replay_manifest.jsonl", "replay_results.jsonl", "replay_results.csv", "replay_summary.json",
    "denominator_audit.json", "architecture_reachability_audit.csv", "executed_candidate_replay_summary.json",
    "nonexecuted_candidate_replay_summary.json", "stored_l1_vs_l2_crosstab.csv",
    "recomputed_diagnostic_l1_vs_l2_crosstab.csv", "l2_information_increment_summary.json",
    "l2_unknown_reason_breakdown.csv", "l2_unknown_by_source.csv", "multi_candidate_group_analysis.csv",
    "coverage_by_source.csv", "coverage_by_run.csv", "coverage_by_trial.csv", "missingness_reason_by_source.csv",
    "selection_bias_audit.md", "replay_determinism_audit.json", "replay_differential_integrity_audit.json",
    "historical_evidence_non_upgrade_audit.json", "claim_boundary.md", "reviewers/control_theory_review.json",
    "reviewers/robotics_systems_review.json", "reviewers/statistics_evaluation_review.json",
    "reviewers/software_reproducibility_review.json", "FINAL_CASE_DECISION.json", "run_manifest.json",
    "downstream_handoff.json", "DRAFT_PR_BODY.md", "validate_l2_h1_frozen_replay_v1.py",
    "report/REPORT_VALIDATE_L2_H1_SHADOW_CERTIFIER_ON_FROZEN_REPLAY_V1.md",
]
ALLOWED_PREFIX = "reproduction/replay/l2_h1_shadow_frozen_replay_v1/"


def run(args: list[str], cwd: Path = REPO_ROOT, check: bool = True) -> subprocess.CompletedProcess[str]:
    return subprocess.run(args, cwd=cwd, check=check, capture_output=True, text=True)


def jsonl(name: str) -> list[dict[str, Any]]:
    return [json.loads(line) for line in (TASK_ROOT / name).read_text(encoding="utf-8").splitlines() if line]


def main() -> None:
    checks: dict[str, Any] = {}
    checks["required_artifacts"] = all((TASK_ROOT / path).is_file() for path in REQUIRED)
    missing_artifacts = [path for path in REQUIRED if not (TASK_ROOT / path).is_file()]
    upstream = read_json(TASK_ROOT / "audit/upstream_identity.json")
    protected = read_json(TASK_ROOT / "audit/protected_source_audit.json")
    checks["upstream_pr_count"] = upstream["pr_count"] == 10
    checks["pr94_identity"] = upstream["pr94_expected_head"] == PR94_HEAD and upstream["pr94_is_ancestor"] is True
    checks["protected_blob_count"] = protected["protected_blob_count"] == 17
    checks["protected_raw_identities"] = all(
        row["git_blob"] == row["actual_git_blob"] and row["mode"] == row["actual_mode"] and
        row["size"] == row["actual_size"] and row["sha256"] == row["actual_sha256"]
        for row in protected["records"]
    )
    run(["git", "merge-base", "--is-ancestor", PR94_HEAD, "HEAD"])
    changed = set(run(["git", "diff", "--name-only", PR94_HEAD, "--"]).stdout.splitlines())
    untracked = set(run(["git", "ls-files", "--others", "--exclude-standard"]).stdout.splitlines())
    scope_paths = changed | untracked
    checks["task_local_scope_only"] = all(path.startswith(ALLOWED_PREFIX) for path in scope_paths)
    checks["protected_path_diff_count"] = sum(row["path"] in scope_paths for row in protected["records"]) == 0

    freeze = read_json(TASK_ROOT / "source_universe_freeze.json")
    manifest = jsonl("frozen_replay_manifest.jsonl")
    results = jsonl("replay_results.jsonl")
    denominator = read_json(TASK_ROOT / "denominator_audit.json")
    checks["source_frozen_before_results"] = freeze["status"] == "PASS_SOURCE_UNIVERSE_FROZEN_BEFORE_REPLAY" and freeze["replay_execution_started"] is False and freeze["l2_result_field_count"] == 0
    checks["manifest_identity"] = sha256_file(TASK_ROOT / "frozen_replay_manifest.jsonl") == freeze["manifest_sha256"]
    checks["N_all"] = len(manifest) == freeze["N_all"] == denominator["N_all"] == 6853
    replayability = Counter(row["replayability_class"] for row in manifest)
    checks["replayability_typed"] = set(replayability) <= {"FORMAL_REPLAYABLE", "DIAGNOSTIC_RECONSTRUCTABLE", "NOT_REPLAYABLE"}
    checks["replayability_partition"] = sum(replayability.values()) == len(manifest)
    formal = [row for row in manifest if row["replayability_class"] == "FORMAL_REPLAYABLE"]
    checks["formal_authority_complete"] = all(
        all(row.get(field) not in (None, "") for field in (
            "p_k", "v_k", "u_k", "candidate_id", "map_snapshot_id", "map_content_sha256",
            "robot_margin_contract_sha256", "backend_identity", "query_context_identity",
        )) for row in formal
    )
    result_ids = {row["row_id"] for row in results}
    eligible_ids = {
        row["row_id"] for row in manifest
        if row["replayability_class"] == "FORMAL_REPLAYABLE" and row["l2_reached"] is True and row["primary_analysis_eligible"] is True
    }
    not_replayable_ids = {row["row_id"] for row in manifest if row["replayability_class"] == "NOT_REPLAYABLE"}
    checks["architecture_primary_set_exact"] = result_ids == eligible_ids
    checks["not_replayable_never_unknown"] = not (result_ids & not_replayable_ids)
    checks["result_lineage"] = all(row["l2_reached"] is True and row["primary_analysis_eligible"] is True for row in results)
    status = Counter(row["status"] for row in results)
    checks["L2_counts"] = (len(results), status["PASS"], status["FAIL"], status["UNKNOWN"]) == (788, 770, 18, 0)
    checks["denominator_status_partition"] = denominator["N_L2_PASS"] + denominator["N_L2_FAIL"] + denominator["N_L2_UNKNOWN"] == denominator["N_L2_candidate_evaluated"]
    checks["dynamics_contract"] = all(abs(row["dt"] - 0.05) == 0.0 for row in results)
    checks["no_u_k1"] = all("u_k1" not in row and "u_(k+1)" not in row for row in results)
    checks["formal_backend_identity"] = all(row["backend_identity"] in {"EXACT_ANALYTIC_SPHERE_SEGMENT_MINIMUM", "CONSERVATIVE_SIGNED_DISTANCE_LIPSCHITZ_INTERVAL"} for row in results)
    checks["endpoint_fallback_disabled"] = all(row["endpoint_fallback_enabled"] is False for row in results)
    checks["tri_state_preserved"] = set(status) <= {"PASS", "FAIL", "UNKNOWN"}
    checks["controller_authority_zero"] = all(row["controller_authority"] is False and row["controller_intervention"] is False and row["runtime_intervention"] is False for row in results)
    checks["determinism"] = read_json(TASK_ROOT / "replay_determinism_audit.json")["status"] == "PASS_REPLAY_DETERMINISM"
    checks["differential_integrity"] = read_json(TASK_ROOT / "replay_differential_integrity_audit.json")["status"] == "PASS_REPLAY_DIFFERENTIAL_INTEGRITY"
    increment = read_json(TASK_ROOT / "l2_information_increment_summary.json")
    checks["stored_L1_increment"] = increment["N_L1_PASS_L2_FAIL"] == 18 and increment["collision_prevention_claim_authorized"] is False
    multi = read_json(TASK_ROOT / "multi_candidate_summary.json")
    checks["multi_candidate_historical_only"] = multi["synthetic_candidate_count"] == 0
    checks["case_A"] = read_json(TASK_ROOT / "FINAL_CASE_DECISION.json")["selected_case"] == "CASE_A"
    run_manifest = read_json(TASK_ROOT / "run_manifest.json")
    zero_counts = [
        "formal_navigation_rollout_count", "on_policy_collection_count", "controller_intervention_count",
        "new_data_collection_count", "new_external_dataset_count", "synthetic_state_generation_count",
        "synthetic_candidate_generation_count", "map_generation_count", "map_training_count", "map_mutation_count",
        "controller_mutation_count", "production_method_mutation_count", "dynamics_mutation_count",
        "candidate_library_mutation_count", "backup_mutation_count", "terminal_mutation_count", "H2_implementation_count",
        "formal_runtime_claim_count", "formal_performance_claim_count",
    ]
    checks["all_mutation_authority_counts_zero"] = all(run_manifest["counts"][name] == 0 for name in zero_counts)
    checks["reviewer_count_and_votes"] = run_manifest["counts"]["reviewer_count"] == 4 and set(run_manifest["reviewer_case_votes"].values()) == {"CASE_A"}
    checks["downstream_only_next_task"] = read_json(TASK_ROOT / "downstream_handoff.json")["only_next_task"] == "DESIGN_L2_H1_ON_POLICY_SHADOW_OBSERVATION_V1"
    checks["analysis_QA"] = read_json(TASK_ROOT / "audit/analysis_validation_report.json")["overall_assessment"] == "READY_TO_SHARE_WITH_EXPLICIT_CAVEATS"

    credential_patterns = [re.compile(pattern, re.I) for pattern in (r"hf_[A-Za-z0-9]{20,}", r"ghp_[A-Za-z0-9]{20,}", r"BEGIN (?:RSA |OPENSSH )?PRIVATE KEY")]
    credential_hits = []
    forbidden_assets = []
    for path in TASK_ROOT.rglob("*"):
        if not path.is_file() or "__pycache__" in path.parts:
            continue
        if path.suffix.lower() in {".ckpt", ".pth", ".pt", ".npy", ".npz", ".tar", ".zip", ".ply"}:
            forbidden_assets.append(path.relative_to(TASK_ROOT).as_posix())
        if path.suffix.lower() in {".md", ".json", ".jsonl", ".csv", ".py"}:
            text = path.read_text(encoding="utf-8", errors="ignore")
            if any(pattern.search(text) for pattern in credential_patterns):
                credential_hits.append(path.relative_to(TASK_ROOT).as_posix())
    checks["no_credentials"] = not credential_hits
    checks["no_large_binary_assets"] = not forbidden_assets

    compile_result = run([sys.executable, "-B", "-m", "compileall", "-q", str(TASK_ROOT)])
    unittest_result = run([sys.executable, "-B", "-m", "unittest", "discover", "-s", "tests", "-v"], cwd=TASK_ROOT)
    pytest_available = importlib.util.find_spec("pytest") is not None
    pytest_result = run([sys.executable, "-B", "-m", "pytest", "-q", "tests"], cwd=TASK_ROOT) if pytest_available else None
    diff_check = run(["git", "diff", "--check"])
    checks["compileall"] = compile_result.returncode == 0
    checks["unittest"] = unittest_result.returncode == 0
    checks["pytest_if_available"] = not pytest_available or (pytest_result is not None and pytest_result.returncode == 0)
    checks["git_diff_check"] = diff_check.returncode == 0

    failed = sorted(key for key, value in checks.items() if value is not True)
    result = {
        "status": "PASS_L2_H1_FROZEN_REPLAY_V1_VALIDATION" if not failed else "FAIL_L2_H1_FROZEN_REPLAY_V1_VALIDATION",
        "checks": checks,
        "failed_checks": failed,
        "missing_artifacts": missing_artifacts,
        "credential_hits": credential_hits,
        "forbidden_assets": forbidden_assets,
        "tooling": {
            "compileall": compile_result.stdout + compile_result.stderr,
            "unittest": unittest_result.stdout + unittest_result.stderr,
            "pytest": "NOT_AVAILABLE" if pytest_result is None else pytest_result.stdout + pytest_result.stderr,
            "git_diff_check": diff_check.stdout + diff_check.stderr,
        },
        "FINAL_STATUS": "PASS_L2_H1_FROZEN_REPLAY_VALIDATION_V1" if not failed else "FAIL_L2_H1_FROZEN_REPLAY_V1_VALIDATION",
        "FINAL_DECISION": "FREEZE_REPLAY_EVIDENCE_AND_PREPARE_NONINVASIVE_ON_POLICY_SHADOW_OBSERVATION" if not failed else "DO_NOT_USE_REPLAY_RESULTS_AND_FIX_REPLAY_PIPELINE",
    }
    write_json(TASK_ROOT / "validation_result.json", result)
    if failed:
        raise RuntimeError("VALIDATION_FAILED:" + ",".join(failed))
    print("PASS_L2_H1_FROZEN_REPLAY_V1_VALIDATION")


if __name__ == "__main__":
    main()
