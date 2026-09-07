"""Static validator for the frozen Active Runtime V2 reconformance evidence."""

from __future__ import annotations

import json
import subprocess
from pathlib import Path


TASK = Path(__file__).resolve().parent
REPO = TASK.parents[2]
UPSTREAM = "bdc8273295d30cbeef029a38ed80153c5cc1d24d"


def read(name: str) -> dict:
    return json.loads((TASK / name).read_text(encoding="utf-8"))


def git(*args: str) -> str:
    return subprocess.run(["git", *args], cwd=REPO, check=True, text=True, capture_output=True).stdout.strip()


def main() -> int:
    required = [
        "ACTIVE_RECONFORMANCE_INPUT_LOCK.json", "ACTIVE_RECONFORMANCE_EXECUTION_LOCK.json",
        "PR120_BLOCKER_CLOSURE_V2.json", "COORDINATOR_POLICY_LEAK_AUDIT_V2.json",
        "ACTIVE_RECONFORMANCE_AUTHORITY_OWNERSHIP_V2.json", "TRANSITION_ROW_FIDELITY_AUDIT_V2.csv",
        "TRANSITION_EXACT_ONE_REVALIDATION_V2.json", "ACTIVE_RECONFORMANCE_TRANSITION_MATRIX_V2.csv",
        "PUBLIC_CYCLE_CALL_ORDER_REVALIDATION_V2.json", "STAGE_EXCEPTION_ROUTING_REVALIDATION_V2.json",
        "DEADLINE_OBSERVATION_POINT_AUDIT_V2.json", "BACKUP_PREVALIDATION_SEMANTICS_V2.json",
        "ROUTING_ARBITRATION_CONSISTENCY_V2.json", "BYPASS_EVIDENCE_PRESERVATION_REVALIDATION_V2.json",
        "scenario_manifest.json", "scenario_results.json", "FIRST_COUNTEREXAMPLE_V2.json",
        "active_public_cycle_reconformance_model_check.json", "active_public_cycle_reconformance_counterexamples.json",
        "revalidated_active_runtime_contract_conformance_review.json", "FINAL_DECISION.json",
        "downstream_handoff.json", "DRAFT_PR_BODY.md",
        "report/REPORT_REVALIDATE_ACTIVE_RUNTIME_CONTRACT_CONFORMANCE_V2.md",
    ]
    final = read("FINAL_DECISION.json")
    blocker = read("PR120_BLOCKER_CLOSURE_V2.json")
    policy = read("COORDINATOR_POLICY_LEAK_AUDIT_V2.json")
    ownership = read("ACTIVE_RECONFORMANCE_AUTHORITY_OWNERSHIP_V2.json")
    exact = read("TRANSITION_EXACT_ONE_REVALIDATION_V2.json")
    call_order = read("PUBLIC_CYCLE_CALL_ORDER_REVALIDATION_V2.json")
    exception = read("STAGE_EXCEPTION_ROUTING_REVALIDATION_V2.json")
    deadline = read("DEADLINE_OBSERVATION_POINT_AUDIT_V2.json")
    backup = read("BACKUP_PREVALIDATION_SEMANTICS_V2.json")
    route_commit = read("ROUTING_ARBITRATION_CONSISTENCY_V2.json")
    bypass = read("BYPASS_EVIDENCE_PRESERVATION_REVALIDATION_V2.json")
    scenarios = read("scenario_results.json")
    model = read("active_public_cycle_reconformance_model_check.json")
    first = read("FIRST_COUNTEREXAMPLE_V2.json")
    test_files = sorted((TASK / "tests").glob("test_*.py"))
    diff_runtime = git("diff", "--name-only", UPSTREAM, "--", "reproduction/runtime", "run.py", "cbf", "dynamics", "splat")

    raw_checks = [
        ("01_pr122_exact", git("merge-base", "HEAD", UPSTREAM) == UPSTREAM),
        ("02_pr120_history_preserved", read("ACTIVE_RECONFORMANCE_INPUT_LOCK.json")["frozen_authorities"]["pr120_blocker"]["sha256"] == "244ea59af0356cbb50a33c0933c1e87977451ca9d2a35655ad8fe8e1867f4041"),
        ("03_pr122_runtime_frozen", diff_runtime == ""),
        ("04_this_task_runtime_diff_zero", diff_runtime == ""),
        ("05_input_lock", (TASK / required[0]).exists()),
        ("06_execution_lock", (TASK / required[1]).exists()),
        ("07_blocker_closure", blocker["status"] == "PASS_INTEGRATION_ORCHESTRATION_GAP_CLOSED"),
        ("08_genuine_coordinator", blocker["genuine_public_api"] is True),
        ("09_no_policy_leak", policy["policy_decision_count"] == 0),
        ("10_sole_routing_owner", ownership["routing_owner"] == "Supervisor.route_transition"),
        ("11_sole_selector", ownership["selection_owner"] == "Supervisor.arbitrate"),
        ("12_sole_plant", ownership["plant_owner"] == "PlantCommitAdapter.commit"),
        ("13_raw_43_row_fidelity", final["first_counterexample"] is None),
        ("14_exact_one", exact["status"] == "PASS"),
        ("15_canonical_order", call_order["status"] == "PASS"),
        ("16_l1_once", call_order["l1_calls"] == 1),
        ("17_start_semantics", scenarios["gate_status"].get("start") == "PASS"),
        ("18_primary_c0", scenarios["gate_status"].get("primary_c0") == "PASS"),
        ("19_l2_l3", scenarios["gate_status"].get("l2_l3") == "PASS"),
        ("20_exception_routing", exception["status"] == "PASS"),
        ("21_deadline_observation_points", deadline["status"] == "PASS"),
        ("22_deadline_semantics", scenarios["gate_status"].get("deadline") == "PASS"),
        ("23_no_synthetic_alternatives", scenarios["gate_status"].get("alternative") == "PASS"),
        ("24_backup_prevalidation", backup["status"] == "PASS"),
        ("25_backup_lifecycle", scenarios["gate_status"].get("backup") == "PASS"),
        ("26_terminal_routed_only", scenarios["gate_status"].get("terminal") == "PASS"),
        ("27_routing_arbitration", route_commit["status"] == "PASS"),
        ("28_commit_allowed", route_commit["commit_allowed_enforced"] is True),
        ("29_trace_exactly_once", scenarios["gate_status"].get("trace") == "PASS"),
        ("30_trace_failure", scenarios["gate_status"].get("trace_failure") == "PASS"),
        ("31_e2e_6_of_6", scenarios["e2e_genuine_pass"] == 6),
        ("32_critical_dynamic_coverage", scenarios["critical_dynamic_coverage_percent"] == 100),
        ("33_model_counterexamples_zero", model["counterexample_count"] == 0),
        ("34_bypass_preservation", bypass["status"] == "PASS_BYPASS_UPSTREAM_EVIDENCE_PRESERVED"),
        ("35_oracle_feedback_zero", scenarios["execution_counts"]["scientific_oracle"] == 0),
        ("36_runtime_correction_zero", scenarios["execution_counts"]["runtime_correction"] == 0),
        ("37_real_active_zero", scenarios["execution_counts"]["real_active"] == 0),
        ("38_gpu_zero", scenarios["execution_counts"]["gpu"] == 0),
        ("39_smoke_zero", scenarios["execution_counts"]["smoke"] == 0),
        ("40_scientific_oracle_zero", scenarios["execution_counts"]["scientific_oracle"] == 0),
        ("41_official100_zero", scenarios["execution_counts"]["official100"] == 0),
        ("42_protocol_deviations_zero", scenarios["protocol_deviation_count"] == 0),
    ]
    checks = [{"name": name, "passed": passed} for name, passed in raw_checks]
    result = {
        "schema": "REVALIDATED_ACTIVE_RUNTIME_CONTRACT_CONFORMANCE_V2_VALIDATION",
        "status": "BLOCKED_REVALIDATED_ACTIVE_RUNTIME_CONTRACT_CONFORMANCE_V2",
        "check_count": len(checks),
        "passed_count": sum(item["passed"] for item in checks),
        "failed_count": sum(not item["passed"] for item in checks),
        "checks": checks,
        "first_counterexample": first["scenario"],
        "required_artifacts_present": all((TASK / name).exists() for name in required),
        "test_module_count": len(test_files),
        "runtime_diff_zero": diff_runtime == "",
    }
    (TASK / "validation_result.json").write_text(json.dumps(result, indent=2, sort_keys=True) + "\n", encoding="utf-8", newline="\n")
    print(result["status"])
    print(f"checks={result['passed_count']}/{result['check_count']}")
    return 0 if result["status"].startswith("PASS_") else 1


if __name__ == "__main__":
    raise SystemExit(main())
