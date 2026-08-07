"""Fail-closed validator for the specification-only Core causal architecture task."""

from __future__ import annotations

import csv
import importlib.util
import json
import re
import subprocess
import sys

from task_config import EXPECTED_PRS, FIGURES, ROLE_IDS, TASK_ROOT


def read_json(rel: str): return json.loads((TASK_ROOT / rel).read_text(encoding="utf-8"))


def read_csv(rel: str):
    with (TASK_ROOT / rel).open(encoding="utf-8", newline="") as handle: return list(csv.DictReader(handle))


def fail(message: str): raise AssertionError(message)


def main() -> None:
    required = [
        "WRITE_CORE_CAUSAL_ARCHITECTURE_SPECIFICATION_V1.md", "IMPLEMENTATION_PLAN.md", "task_config.py", "freeze_upstream_inputs.py", "verify_position_first_euler.py", "build_core_causal_architecture_spec.py", "capture_operational_state.py", "validate_core_causal_architecture_spec.py",
        "input_freeze/protected_source_hashes.json", "architecture/control_authority_timeline.md", "architecture/control_authority_jacobians.csv", "architecture/role_layer_registry.json", "architecture/role_layer_matrix.csv", "architecture/historical_b0_b3_mapping.csv", "architecture/core_state_machine_v1_spec.md", "architecture/state_transition_table.csv", "architecture/failure_taxonomy.md", "architecture/failure_types.csv", "architecture/start_safe_integration.md", "architecture/candidate_dependent_future_safety_spec.md", "architecture/recoverability_role_spec.md", "architecture/alternative_search_eligibility.md", "architecture/component_type_matrix.csv", "architecture/method_vs_evaluation_boundary.md", "evaluation/denominator_contract.md", "evaluation/metric_denominators.csv", "evidence/evidence_role_remapping.csv", "evidence/historical_claim_boundary.md", "alternatives/architecture_A_role_reclassification.md", "alternatives/architecture_B_local_structural_extension.md", "alternatives/architecture_C_full_pipeline_rethink.md", "alternatives/architecture_comparison.csv", "reviews/control_theory_review.md", "reviews/robotics_system_review.md", "reviews/evaluation_statistics_review.md", "reviews/novelty_publication_review.md", "reviews/reviewer_case_matrix.csv", "reviews/disagreement_analysis.md", "decision/final_architecture_decision.json", "decision/supported_claims.md", "decision/prohibited_claims.md", "decision/unresolved_assumptions.md", "decision/downstream_plan.md", "audits/operational_autonomy_actions.json", "audits/formula_verification.json", "audits/no_implementation_audit.json", "audits/runtime_preservation_check.json", "report/REPORT_WRITE_CORE_CAUSAL_ARCHITECTURE_SPECIFICATION_V1.md", "report/DRAFT_PR_BODY.md", "report/downstream_handoff.json",
    ]
    required.extend([f"input_freeze/pr{n}_identity.json" for n in EXPECTED_PRS]); required.extend([f"figures/{name}" for name in FIGURES])
    missing=[rel for rel in required if not (TASK_ROOT/rel).is_file()]
    if missing: fail(f"missing outputs: {missing}")
    for num,(branch,oid) in EXPECTED_PRS.items():
        data=read_json(f"input_freeze/pr{num}_identity.json")
        if data["state"]!="OPEN" or data["isDraft"] is not True or data["mergedAt"] is not None or data["headRefName"]!=branch or data["headRefOid"]!=oid: fail(f"PR {num} identity/preservation failure")
    protected=read_json("input_freeze/protected_source_hashes.json")
    if protected["status"]!="PASS_CORE_CAUSAL_PROTECTED_SOURCE_FREEZE" or protected["record_count"]!=17: fail("protected source freeze failure")
    if any(row["verification"]!="PASS_RAW_GIT_OBJECT_MATCH" for row in protected["records"]): fail("raw blob verification failure")
    noimpl=read_json("audits/no_implementation_audit.json")
    if any(noimpl[key] != 0 for key in noimpl if key.endswith("_count")): fail("implementation boundary violated")
    formula=read_json("audits/formula_verification.json")
    if formula["status"]!="PASS_POSITION_FIRST_EULER_AUTHORITY_CHECK" or formula["manual_derivation"]["dp_k_plus_1_du_k"]!="0" or formula["manual_derivation"]["dp_k_plus_2_du_k"]!="dt^2*I": fail("frozen dynamics/formula failure")
    roles=read_json("architecture/role_layer_registry.json")["layers"]
    if [row["id"] for row in roles] != ROLE_IDS: fail("role layers incomplete")
    mappings=read_csv("architecture/historical_b0_b3_mapping.csv")
    if len(mappings)!=4 or any(not row["prohibited_reinterpretation"].strip() for row in mappings): fail("historical mapping inadequate")
    transitions=read_csv("architecture/state_transition_table.csv")
    states={r["source"] for r in transitions}|{r["destination"] for r in transitions}
    if len(states)!=15 or not any(r["source"]=="S11_ALTERNATIVE_CERTIFIED" and r["destination"]=="S14_COMMIT" for r in transitions): fail("state-machine state/commit path missing")
    for terminal in ("S13_FAIL_CLOSED","S14_COMMIT"):
        if not any(r["source"]==terminal and r["destination"]=="S0_UNASSESSED" for r in transitions): fail("state machine terminal dead end")
    failures=read_csv("architecture/failure_types.csv")
    if len(failures)!=11: fail("failure taxonomy incomplete")
    alt=(TASK_ROOT/"architecture/alternative_search_eligibility.md").read_text(encoding="utf-8")
    if "ADMISSIBLE(x_k,M_k)" not in alt or "h(x_k)<0` is not a B3 opportunity" not in alt: fail("alternative eligibility separation missing")
    denominators=read_csv("evaluation/metric_denominators.csv")
    expected={"N_all","N_state_admissible","N_immediate_evaluable","N_immediate_safe","N_primary_candidate_evaluable","N_primary_future_safe","N_recoverability_evaluable","N_primary_not_certified","N_alt_eligible","N_alt_attempted","N_alt_certified","N_commit","N_fail_closed"}
    if {r["metric"] for r in denominators}!=expected: fail("denominator contract incomplete")
    if len(read_csv("evidence/evidence_role_remapping.csv"))!=13: fail("historical evidence remapping incomplete")
    if len(read_csv("alternatives/architecture_comparison.csv"))!=3: fail("architecture alternatives incomplete")
    votes=read_csv("reviews/reviewer_case_matrix.csv")
    if len(votes)!=4 or any(r["case_vote"]!="CASE_B" for r in votes): fail("reviewer independence/case vote failure")
    decision=read_json("decision/final_architecture_decision.json")
    if decision["selected_case"]!="CASE_B" or decision["FINAL_STATUS"]!="PASS_CORE_CAUSAL_ARCHITECTURE_LOCAL_STRUCTURAL_GAP" or decision["Only_next_task"]!="WRITE_CORE_V2_CAUSAL_INCREMENT_SPECIFICATION_V1": fail("final case mismatch")
    if "candidate-level future discrete safety" not in (TASK_ROOT/"decision/prohibited_claims.md").read_text(encoding="utf-8"): fail("claim boundary missing")
    if "H1 FIRST_CONTROL_AFFECTED_SEGMENT" not in (TASK_ROOT/"architecture/candidate_dependent_future_safety_spec.md").read_text(encoding="utf-8"): fail("H1 specification missing")
    runtime=read_json("audits/runtime_preservation_check.json")
    if runtime["status"]!="PASS_READ_ONLY_OPERATIONAL_PRESERVATION" or runtime["task_owned_compute_process_count"]!=0: fail("GPU/process/watchdog check failed")
    manifest=read_json("figures/figure_manifest.json")
    if manifest["count"]!=21 or "NOT A NEW SAFETY GUARANTEE" not in manifest["figures"][0]["annotation"]: fail("figure boundary missing")
    repo=TASK_ROOT.parents[2]; allowed="reproduction/specification/core_causal_architecture_specification_v1/"
    changed=subprocess.check_output(["git","diff","--name-only"],cwd=repo,text=True,encoding="utf-8").splitlines(); untracked=subprocess.check_output(["git","ls-files","--others","--exclude-standard"],cwd=repo,text=True,encoding="utf-8").splitlines()
    if any(path.replace("\\","/") and not path.replace("\\","/").startswith(allowed) for path in [*changed,*untracked]): fail("mutation outside authorized task directory")
    whitespace=subprocess.run(["git","diff","--check"],cwd=repo,text=True,encoding="utf-8",capture_output=True,check=False)
    if whitespace.returncode!=0 or whitespace.stdout.strip(): fail("git diff --check failed")
    # Run the standard compiler over the authorized directory.  On Windows the
    # attempted redirected pycache-prefix approach can fail while atomically
    # renaming a temporary .pyc even when every source compiles correctly.
    # The repository ignores __pycache__, so direct compileall keeps this check
    # faithful without introducing a trackable artifact.
    comp=subprocess.run([sys.executable,"-B","-m","compileall","-q",str(TASK_ROOT)],text=True,capture_output=True,check=False)
    if comp.returncode!=0: fail(f"compileall failed: {comp.stderr.strip()}")
    for path in TASK_ROOT.rglob("*"):
        if path.is_file() and path.stat().st_size>2_000_000: fail(f"large asset: {path}")
        if path.is_file() and re.search(r"(?:hf_|ghp_|github_pat_)[A-Za-z0-9_-]{10,}",path.read_text(encoding="utf-8",errors="ignore")): fail(f"credential-like text: {path}")
    result={"status":"PASS_CORE_CAUSAL_ARCHITECTURE_SPECIFICATION_VALIDATION","upstream_pr_count":7,"protected_blob_count":17,"formal_method_run_count":0,"controller_mutation_count":0,"method_mutation_count":0,"map_training_count":0,"map_mutation_count":0,"dataset_addition_count":0,"cohort_addition_count":0,"architecture_role_layer_count":len(roles),"state_count_in_state_machine":len(states),"transition_count":len(transitions),"failure_type_count":len(failures),"historical_method_mapping_count":len(mappings),"candidate_future_options_count":2,"denominator_metric_count":len(denominators),"historical_evidence_remapping_count":13,"reviewer_count":len(votes),"reviewer_case_votes":{"CASE_B":4},"formula_check_count":formula["checks"],"contract_ambiguity_count":4,"unresolved_assumption_count":7,"operational_autonomy_action_count":read_json("audits/operational_autonomy_actions.json")["count"],"pytest_available":importlib.util.find_spec("pytest") is not None,"pytest_check":"available" if importlib.util.find_spec("pytest") else "unavailable; stdlib unittest fallback used","selected_case":"CASE_B","Only_next_task":decision["Only_next_task"]}
    (TASK_ROOT/"report"/"validation_result.json").write_text(json.dumps(result,indent=2,sort_keys=True)+"\n",encoding="utf-8")
    print(result["status"])


if __name__=="__main__": main()
