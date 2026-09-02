#!/usr/bin/env python3
"""Validate frozen Method Logic Closure V2 artifacts without runtime execution."""
from __future__ import annotations

import hashlib
import json
import subprocess
from pathlib import Path


ROOT = Path(__file__).resolve().parent
REPO = ROOT.parents[2]
UPSTREAM = "bb44f3058003585ce31f3b6a132eb1c28114f4e3"


def read(name: str) -> str:
    return (ROOT / name).read_text(encoding="utf-8")


def load(name: str) -> dict:
    return json.loads(read(name))


def sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def git(*args: str) -> str:
    return subprocess.check_output(["git", *args], cwd=REPO, text=True).strip()


def main() -> int:
    checks: dict[str, bool] = {}
    required_artifacts = [
        "README.md", "METHOD_LOGIC_INPUT_LOCK.json", "LOGIC_MODEL_EXECUTION_LOCK.json",
        "ROUTING_SUPERSESSION_NOTE.md", "CERTIFICATION_LAYER_V2.md",
        "RUNTIME_ASSURANCE_SUPERVISOR_V2.md", "CONTROL_ROLE_TAXONOMY_V2.json",
        "STATE_VARIABLES_V2.json", "STATE_TRANSITION_TABLE_V2.csv", "FAILURE_ROUTING_V2.csv",
        "UNKNOWN_REASON_SCOPE_V2.json", "BACKUP_RETENTION_AND_HANDOFF_V2.md",
        "TEMPORAL_INDEX_CONTRACT_V2.md", "temporal_index_checks.json",
        "TERMINAL_ACTION_ELIGIBILITY_V2.md", "ALTERNATIVE_RECERTIFICATION_V2.md",
        "ALTERNATIVE_SOURCE_REQUIREMENTS_V2.md", "RUNTIME_CURRENT_ROLE_AUDIT_V2.md",
        "METHOD_SCOPE_AND_CLAIM_BOUNDARY_V2.md", "CROSS_LAYER_AUTHORITY_REQUIREMENTS_V2.json",
        "PREIMPLEMENTATION_BLOCKER_REGISTER_V2.json", "PREIMPLEMENTATION_DEPENDENCY_DAG.json",
        "model_check_method_logic_v2.py", "model_check_result.json", "reachable_state_summary.json",
        "counterexamples.json", "logic_closure_review.json", "FINAL_DECISION.json",
        "downstream_handoff.json", "DRAFT_PR_BODY.md",
        "report/REPORT_RED_TEAM_AND_FREEZE_METHOD_LOGIC_CLOSURE_V2.md",
    ]
    checks["required_artifacts_complete"] = all((ROOT / item).is_file() for item in required_artifacts) and (ROOT / "tests").is_dir()
    lock = load("METHOD_LOGIC_INPUT_LOCK.json")
    checks["pr106_identity_exact"] = lock["upstream"]["pull_request"] == 106 and lock["upstream"]["head_sha"] == UPSTREAM and lock["upstream"]["state"] == "OPEN_DRAFT"
    checks["geometry_contract_exact"] = lock["geometry"]["canonical_contract_sha256"] == "23ba083d871d17f6389dde2872068e7439cba6898197572fc34246b5b46da7f3"

    source_ok = True
    for item in lock["source_identities"].values():
        source_ok &= sha256(REPO / item["path"]) == item["sha256"]
    checks["upstream_source_hashes_exact"] = source_ok

    changed = [x for x in git("diff", "--name-only", UPSTREAM).splitlines() if x]
    checks["task_local_only"] = all(x.startswith("reproduction/specification/method_logic_closure_v2/") for x in changed)
    checks["runtime_source_change_count_zero"] = not any(x in {"run.py", "cbf/cbf_utils.py"} or x.startswith(("dynamics/", "splat/")) for x in changed)
    checks["v1_scientific_change_count_zero"] = not any(x.startswith("reproduction/analysis/") or "formal_collection" in x for x in changed)

    cert = read("CERTIFICATION_LAYER_V2.md")
    sup = read("RUNTIME_ASSURANCE_SUPERVISOR_V2.md")
    checks["two_layer_architecture"] = "C0 — CANDIDATE_ADMISSIBILITY" in cert and "only component with action-selection" in sup
    checks["c0_total"] = all(x in cert for x in ("FAIL_CANDIDATE_LOCAL", "UNKNOWN_GLOBAL_OR_AUTHORITY", "UNKNOWN_CANDIDATE_LOCAL_COMPUTE"))
    unknown = load("UNKNOWN_REASON_SCOPE_V2.json")
    checks["l1_unknown"] = "UNKNOWN" in unknown["layer_totality"]["L1"]
    checks["l2_reason_scope"] = set(unknown["scopes"]) == {"GLOBAL_AUTHORITY_OR_EVIDENCE", "CANDIDATE_LOCAL_COMPUTATION", "INFRASTRUCTURE_HEALTH", "UNRESOLVED_SCOPE"}
    checks["l3_unknown"] = "UNKNOWN_GLOBAL" in unknown["layer_totality"]["L3"] and "UNKNOWN_LOCAL" in unknown["layer_totality"]["L3"]
    checks["alternative_recertification"] = "C0 → L2 → L3" in read("ALTERNATIVE_RECERTIFICATION_V2.md")
    roles = load("CONTROL_ROLE_TAXONOMY_V2.json")
    checks["active_precommit"] = roles["modes"]["ACTIVE_ASSURANCE_MODE"]["required_checks_precommit"] is True
    checks["shadow_active_distinct"] = roles["modes"]["SHADOW_OBSERVATION_MODE"]["feedback_channel"] is False
    backup = read("BACKUP_RETENTION_AND_HANDOFF_V2.md")
    checks["backup_retention"] = "old token remains available" in backup
    checks["atomic_handoff"] = "Replacement is atomic" in backup
    checks["deadline_guard"] = "guard preempts search" in sup.lower()
    checks["terminal_membership_eligibility_separate"] = "TERMINAL_SET_MEMBER" in read("TERMINAL_ACTION_ELIGIBILITY_V2.md") and "TERMINAL_ACTION_ELIGIBLE" in read("TERMINAL_ACTION_ELIGIBILITY_V2.md")
    checks["assurance_boundary_explicit"] = "ASSURANCE_BOUNDARY_NO_CERTIFIED_ACTION" in sup
    checks["r0_audited"] = "CHEAP_DIAGNOSTIC_OR_HEALTH_PRECHECK_ONLY" in read("RUNTIME_CURRENT_ROLE_AUDIT_V2.md")

    old_codes = {line.split(",", 1)[0] for line in (REPO / "reproduction/specification/core_causal_architecture_specification_v1/architecture/failure_types.csv").read_text(encoding="utf-8").splitlines()[1:] if line}
    new_codes = {line.split(",", 1)[0] for line in read("FAILURE_ROUTING_V2.csv").splitlines()[1:] if line}
    checks["failure_taxonomy_preserved"] = old_codes <= new_codes

    result = load("model_check_result.json")
    checks["p1_p20_executed"] = len(result["property_results"]) == 20 and all(v["status"] == "PASS" for v in result["property_results"].values())
    checks["all_hard_thresholds_zero"] = all(value == 0 for value in result["hard_violation_counts"].values())
    checks["no_outcome_tuning"] = result["correction_round_count"] == 0 and load("LOGIC_MODEL_EXECUTION_LOCK.json")["outcome_tuning_allowed"] is False
    dag = load("PREIMPLEMENTATION_DEPENDENCY_DAG.json")
    blockers = load("PREIMPLEMENTATION_BLOCKER_REGISTER_V2.json")
    checks["blocker_dag_present"] = dag["no_prerequisite_bypass"] is True and blockers["earliest_unresolved_prerequisite"] == "CROSS_LAYER_GEOMETRY_AUTHORITY"

    execution_lock = load("LOGIC_MODEL_EXECUTION_LOCK.json")
    checks["execution_lock_hashes_exact"] = (
        sha256(ROOT / "STATE_VARIABLES_V2.json") == execution_lock["state_model_sha256"]
        and sha256(ROOT / "STATE_TRANSITION_TABLE_V2.csv") == execution_lock["transition_table_sha256"]
        and sha256(ROOT / "model_check_method_logic_v2.py") == execution_lock["checker_sha256"]
        and sha256(ROOT / "PROPERTIES_P1_P20.json") == execution_lock["properties_sha256"]
        and sha256(ROOT / "ADVERSARIAL_SCENARIOS_V2.json") == execution_lock["scenario_manifest_sha256"]
    )

    status = "PASS_METHOD_LOGIC_CLOSURE_V2_VALIDATION" if all(checks.values()) else "FAIL_METHOD_LOGIC_CLOSURE_V2_VALIDATION"
    output = {
        "schema_version":"METHOD_LOGIC_CLOSURE_V2_VALIDATION_RESULT",
        "validator":status,
        "checks":checks,
        "check_count":len(checks),
        "pass_count":sum(checks.values()),
        "runtime_execution_count":0,
        "gpu_execution_count":0,
        "navigation_rollout_count":0,
        "formal_cohort_count":0,
        "parameter_tuning_count":0,
    }
    (ROOT / "validation_result.json").write_text(json.dumps(output, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(status)
    if not all(checks.values()):
        print("failed=" + ",".join(k for k, v in checks.items() if not v))
    return 0 if all(checks.values()) else 1


if __name__ == "__main__":
    raise SystemExit(main())
