"""Fail-closed validator for the Core V2 L2/H1 specification task."""

from __future__ import annotations

import csv
import importlib.util
import json
import re
import subprocess
import sys

from task_config import (
    BASE_BRANCH,
    BRANCH,
    EXPECTED_HEAD,
    EXPECTED_PRS,
    FIGURES,
    FINAL_CASE,
    FINAL_DECISION,
    FINAL_STATUS,
    ONLY_NEXT_TASK,
    REPO_ROOT,
    TASK_ROOT,
)


def fail(message: str) -> None:
    raise AssertionError(message)


def read_json(rel: str) -> dict:
    return json.loads((TASK_ROOT / rel).read_text(encoding="utf-8"))


def read_csv(rel: str) -> list[dict[str, str]]:
    with (TASK_ROOT / rel).open(encoding="utf-8", newline="") as handle:
        return list(csv.DictReader(handle))


def main() -> None:
    required = [
        "IMPLEMENTATION_PLAN.md",
        "CORE_V2_L2_H1_CAUSAL_INCREMENT_SPECIFICATION_V1.md",
        "FROZEN_UPSTREAM_IDENTITY.json",
        "PROTECTED_SOURCE_AUDIT.json",
        "CONTROL_AUTHORITY_H1_DERIVATION.md",
        "control_authority_h1_derivation.json",
        "H1_SEGMENT_CONTRACT.md",
        "L2_PREDICATE_CONTRACT.md",
        "map_safety_semantics_audit.json",
        "continuous_segment_semantics_audit.json",
        "execution_optimizer_verifier_consistency.json",
        "l2_l3_separation_contract.json",
        "ALT_ELIGIBLE_BOUNDARY_AUDIT.md",
        "L5_TERMINAL_FAIL_CLOSE_BOUNDARY.md",
        "H1_VS_H2_SCOPE_BOUNDARY.md",
        "unresolved_assumption_disposition.csv",
        "h1_option_comparison.csv",
        "FALSIFICATION_GATES.json",
        "STATE_MACHINE_DELTA_V1.md",
        "failure_taxonomy_l2_mapping.csv",
        "denominator_contract_l2.json",
        "historical_evidence_non_upgrade_audit.json",
        "SUPPORTED_AND_PROHIBITED_CLAIMS.md",
        "reviewers/control_theory_review.json",
        "reviewers/robotics_systems_review.json",
        "reviewers/statistics_review.json",
        "reviewers/novelty_publication_review.json",
        "FINAL_CASE_DECISION.json",
        "run_manifest.json",
        "validation_result.json",
        "downstream_handoff.json",
        "DRAFT_PR_BODY.md",
        "report/REPORT_WRITE_CORE_V2_CAUSAL_INCREMENT_SPECIFICATION_V1.md",
        "operational_state_audit.json",
        "operational_autonomy_actions.json",
        "task_config.py",
        "freeze_upstream_inputs.py",
        "verify_h1_control_authority.py",
        "build_core_v2_spec.py",
        "capture_operational_state.py",
        "validate_core_v2_causal_increment_spec.py",
        "tests/test_protocol_outputs.py",
        "figures/figure_manifest.json",
    ]
    required.extend(f"figures/{name}" for name in FIGURES)
    missing = [rel for rel in required if not (TASK_ROOT / rel).is_file() and rel != "validation_result.json"]
    if missing:
        fail(f"missing outputs: {missing}")

    if subprocess.check_output(["git", "branch", "--show-current"], cwd=REPO_ROOT, text=True).strip() != BRANCH:
        fail("branch mismatch")
    if subprocess.check_output(["git", "merge-base", "HEAD", BASE_BRANCH], cwd=REPO_ROOT, text=True).strip() != EXPECTED_HEAD:
        fail("base/head lineage mismatch")
    upstream = read_json("FROZEN_UPSTREAM_IDENTITY.json")
    if upstream["status"] != "PASS_FROZEN_UPSTREAM_IDENTITY" or upstream["upstream_pr_count"] != 8:
        fail("upstream identity freeze failure")
    if upstream["pr92_expected_head"] != EXPECTED_HEAD or upstream["pr92_actual_head"] != EXPECTED_HEAD:
        fail("BLOCKED_CORE_V2_SPEC_BY_UPSTREAM_IDENTITY_DRIFT")
    for row in upstream["pull_requests"]:
        branch, oid = EXPECTED_PRS[row["number"]]
        if row["state"] != "OPEN" or row["isDraft"] is not True or row["headRefName"] != branch or row["headRefOid"] != oid:
            fail(f"upstream PR drift: {row['number']}")

    protected = read_json("PROTECTED_SOURCE_AUDIT.json")
    if protected["status"] != "PASS_CORE_V2_PROTECTED_SOURCE_AUDIT" or protected["protected_blob_count"] != 17:
        fail("protected source audit failure")
    if any(row["verification"] != "PASS_RAW_GIT_OBJECT_MATCH" for row in protected["protected_records"]):
        fail("protected raw blob mismatch")
    if any(row["verification"] != "PASS_RAW_GIT_OBJECT_MATCH" for row in protected["supplemental_evidence_records"]):
        fail("supplemental source mismatch")

    manifest = read_json("run_manifest.json")
    counts = manifest["counts"]
    zero_counts = [
        "formal_method_run_count", "controller_mutation_count", "method_mutation_count", "dynamics_mutation_count",
        "map_training_count", "map_mutation_count", "dataset_addition_count", "cohort_addition_count",
        "candidate_library_mutation_count", "backup_mutation_count", "terminal_set_mutation_count",
        "parameter_tuning_count", "new_safety_primitive_count", "historical_evidence_recompute_count",
        "formal_performance_metric_count", "GPU_formal_compute_count", "task_owned_process_cleanup_count",
    ]
    if any(counts[key] != 0 for key in zero_counts):
        fail("no-implementation boundary violated")

    formula = read_json("control_authority_h1_derivation.json")
    if formula["status"] != "PASS_H1_CONTROL_AUTHORITY_DERIVATION" or formula["formula_check_count"] != 10:
        fail("formula audit failure")
    if formula["derivative"] != "d p_H1(alpha) / d u_k = alpha*dt^2*I":
        fail("H1 derivative mismatch")
    if formula["candidate_dependence_verdict"] != "NONZERO_FOR_EVERY_ALPHA_GREATER_THAN_ZERO":
        fail("candidate dependence not established")
    if "0.5*dt" in (TASK_ROOT / "CONTROL_AUTHORITY_H1_DERIVATION.md").read_text(encoding="utf-8"):
        fail("constant-acceleration model substituted")

    map_audit = read_json("map_safety_semantics_audit.json")
    if map_audit["status"] not in {"SUFFICIENT_FOR_H1_SPEC", "CONSERVATIVE_BUT_SUFFICIENT_FOR_H1_SPEC"}:
        fail("map semantics not sufficient")
    if map_audit["physical_world_truth_claim"] is not False or map_audit["effective_radius"] != "0.11 m":
        fail("map/robot/margin boundary failure")
    if "fail-closed" not in map_audit["unknown_semantics"]["l2_mapping"]:
        fail("UNKNOWN not fail closed")
    segment = read_json("continuous_segment_semantics_audit.json")
    if segment["status"] != "SUFFICIENT_FOR_H1_SPEC" or segment["endpoint_only_fallback"] is not False:
        fail("continuous-segment contract failure")
    if segment["diagnostic_backend"]["formal_pass_allowed"] is not False or len(segment["formal_backends"]) != 2:
        fail("backend classification failure")
    consistency = read_json("execution_optimizer_verifier_consistency.json")
    if consistency["status"] != "PASS_EXECUTION_OPTIMIZER_VERIFIER_H1_CONSISTENCY" or consistency["timing_conflict_count"] != 0:
        fail("execution/optimizer/verifier mismatch")

    separation = read_json("l2_l3_separation_contract.json")
    if separation["entry_condition"] != "L3 may be entered only after L2_PASS":
        fail("L2/L3 separation failure")
    alt = (TASK_ROOT / "ALT_ELIGIBLE_BOUNDARY_AUDIT.md").read_text(encoding="utf-8")
    if "not redefined" not in alt or "L2_UNKNOWN" not in alt:
        fail("ALT_ELIGIBLE boundary failure")
    if "not a safe stop" not in (TASK_ROOT / "L5_TERMINAL_FAIL_CLOSE_BOUNDARY.md").read_text(encoding="utf-8"):
        fail("L5 fail-close boundary failure")
    if "H2 remains deferred" not in (TASK_ROOT / "H1_VS_H2_SCOPE_BOUNDARY.md").read_text(encoding="utf-8"):
        fail("H2 not deferred")

    assumptions = read_csv("unresolved_assumption_disposition.csv")
    if len(assumptions) != 7 or {row["class"] for row in assumptions} - {"A", "B", "C", "D"}:
        fail("unresolved assumption disposition failure")
    options = read_csv("h1_option_comparison.csv")
    verdicts = {row["option"]: row["verdict"] for row in options}
    if verdicts != {"OPTION_H1_A": "SELECT", "OPTION_H1_B": "VALID_SUBCASE_OF_A", "OPTION_H1_C": "REJECT_AS_FORMAL_L2"}:
        fail("H1 option verdict failure")
    gates = read_json("FALSIFICATION_GATES.json")
    if gates["falsification_gate_count"] != 7 or not gates["all_resolved"] or not gates["all_pass"]:
        fail("G1-G7 failure")
    if any(not row["do_not_implement_condition"] for row in gates["gates"]):
        fail("non-falsifiable gate")

    failures = read_csv("failure_taxonomy_l2_mapping.csv")
    if len(failures) != 11 or any(row["upstream_taxonomy_status"] != "PRESERVED" for row in failures):
        fail("failure taxonomy changed")
    denominator = read_json("denominator_contract_l2.json")
    if denominator["new_prevalence_numbers_generated"] is not False or denominator["conditional_rate_denominator"] != "N_L2_candidate_evaluated":
        fail("denominator contract failure")
    historical = read_json("historical_evidence_non_upgrade_audit.json")
    if historical["historical_evidence_recompute_count"] != 0 or historical["historical_evidence_upgrade_count"] != 0:
        fail("historical evidence upgraded")

    reviews = [
        read_json("reviewers/control_theory_review.json"),
        read_json("reviewers/robotics_systems_review.json"),
        read_json("reviewers/statistics_review.json"),
        read_json("reviewers/novelty_publication_review.json"),
    ]
    if len({row["reviewer"] for row in reviews}) != 4 or any(row["case_vote"] != "CASE_A" or row["critical_blocker_count"] != 0 for row in reviews):
        fail("reviewer pass failure")
    decision = read_json("FINAL_CASE_DECISION.json")
    if decision["selected_case"] != FINAL_CASE or decision["FINAL_STATUS"] != FINAL_STATUS or decision["FINAL_DECISION"] != FINAL_DECISION:
        fail("selected case mismatch")
    if decision["Only_next_task"] != ONLY_NEXT_TASK:
        fail("Only next task mismatch")
    handoff = read_json("downstream_handoff.json")
    if handoff["Only_next_task"] != ONLY_NEXT_TASK or handoff["started"] is not False:
        fail("downstream handoff boundary failure")

    report = (TASK_ROOT / "report/REPORT_WRITE_CORE_V2_CAUSAL_INCREMENT_SPECIFICATION_V1.md").read_text(encoding="utf-8")
    for text in (FINAL_STATUS, FINAL_DECISION, ONLY_NEXT_TASK, "## Answers first", "G1-G7 all PASS"):
        if text not in report:
            fail(f"report missing: {text}")
    claims = (TASK_ROOT / "SUPPORTED_AND_PROHIBITED_CLAIMS.md").read_text(encoding="utf-8")
    for text in ("recursive feasibility", "safe-stop", "performance", "physical-world"):
        if text not in claims:
            fail(f"prohibited claim missing: {text}")

    figure_manifest = read_json("figures/figure_manifest.json")
    if figure_manifest["count"] != 10 or set(figure_manifest["files"]) != set(FIGURES):
        fail("figure manifest failure")
    for required_label in ("SPECIFICATION ONLY", "NO CORE V2 IMPLEMENTATION", "MAP-RELATIVE CLAIM ONLY", "NOT RECURSIVE FEASIBILITY", "NOT SAFE-STOP PROOF"):
        if required_label not in figure_manifest["annotation"]:
            fail(f"figure label missing: {required_label}")

    operational = read_json("operational_state_audit.json")
    if operational["status"] != "PASS_CORE_V2_SPEC_OPERATIONAL_PRESERVATION" or operational["task_owned_compute_process_count"] != 0:
        fail("GPU/process preservation failure")
    if not operational["watchdog_running"] or not operational["remote_wrapper_present"]:
        fail("watchdog/SSH preservation failure")

    allowed = "reproduction/specification/core_v2_causal_increment_specification_v1/"
    changed = subprocess.check_output(["git", "diff", "--name-only"], cwd=REPO_ROOT, text=True, encoding="utf-8").splitlines()
    staged = subprocess.check_output(["git", "diff", "--cached", "--name-only"], cwd=REPO_ROOT, text=True, encoding="utf-8").splitlines()
    untracked = subprocess.check_output(["git", "ls-files", "--others", "--exclude-standard"], cwd=REPO_ROOT, text=True, encoding="utf-8").splitlines()
    if any(not path.replace("\\", "/").startswith(allowed) for path in [*changed, *staged, *untracked]):
        fail("mutation outside authorized directory")
    diff = subprocess.run(["git", "diff", "--check"], cwd=REPO_ROOT, text=True, capture_output=True, check=False)
    if diff.returncode != 0 or diff.stdout.strip():
        fail("git diff --check failed")
    compile_result = subprocess.run([sys.executable, "-B", "-m", "compileall", "-q", str(TASK_ROOT)], text=True, capture_output=True, check=False)
    if compile_result.returncode != 0:
        fail(f"compileall failed: {compile_result.stderr.strip()}")
    for path in TASK_ROOT.rglob("*"):
        if path.is_file() and path.stat().st_size > 2_000_000:
            fail(f"large asset: {path}")
        if path.is_file() and re.search(r"(?:hf_|ghp_|github_pat_)[A-Za-z0-9_-]{10,}", path.read_text(encoding="utf-8", errors="ignore")):
            fail(f"credential-like text: {path}")

    result = {
        "status": "PASS_CORE_V2_CAUSAL_INCREMENT_SPECIFICATION_VALIDATION",
        **counts,
        "map_semantics_status": map_audit["status"],
        "continuous_segment_status": segment["status"],
        "reviewer_count": len(reviews),
        "reviewer_case_votes": {"CASE_A": 4},
        "selected_case": FINAL_CASE,
        "FINAL_STATUS": FINAL_STATUS,
        "FINAL_DECISION": FINAL_DECISION,
        "Only_next_task": ONLY_NEXT_TASK,
        "unresolved_critical_blocker_count": 0,
        "pytest_available": importlib.util.find_spec("pytest") is not None,
    }
    (TASK_ROOT / "validation_result.json").write_text(json.dumps(result, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(result["status"])


if __name__ == "__main__":
    main()
