"""Validate the frozen post-R2 Active Runtime conformance evidence package."""

from __future__ import annotations

import csv
import hashlib
import json
import subprocess
from pathlib import Path


TASK = Path(__file__).resolve().parent
REPO = TASK.parents[2]


def read(name: str):
    return json.loads((TASK / name).read_text(encoding="utf-8"))


def main() -> int:
    checks: list[dict[str, object]] = []
    def check(name: str, passed: bool, detail: object = None):
        checks.append({"name": name, "passed": bool(passed), "detail": detail})

    inputs = read("POST_R2_ACTIVE_RECONFORMANCE_INPUT_LOCK.json")
    execution = read("POST_R2_ACTIVE_RECONFORMANCE_EXECUTION_LOCK.json")
    runtime_diff = read("POST_R2_RUNTIME_DIFF_AUDIT_V2.json")
    scenarios = read("POST_R2_CONFORMANCE_SCENARIO_RESULTS_V2.json")
    model = read("POST_R2_ACTIVE_RUNTIME_MODEL_CHECK_V2.json")
    decision = read("FINAL_DECISION.json")
    fidelity_rows = list(csv.DictReader((TASK / "POST_R2_TRANSITION_43_ROW_FIDELITY_V2.csv").open(encoding="utf-8", newline="")))
    dynamic_rows = list(csv.DictReader((TASK / "POST_R2_43_RULE_DYNAMIC_EXECUTION_MATRIX_V2.csv").open(encoding="utf-8", newline="")))
    closure = list(csv.DictReader((TASK / "POST_R2_CONFIRMED_DEFECT_CLOSURE_MATRIX_V2.csv").open(encoding="utf-8", newline="")))
    by_id = {item["scenario_id"]: item for item in scenarios["results"]}
    domain_pass = lambda domain: all(item["passed"] for item in scenarios["results"] if item["domain"] == domain)
    counts = scenarios["execution_counts"]

    check("01_pr126_exact", inputs["pr126"]["head"] == "c38a51310767669e51ef6c87307c831405221277")
    check("02_runtime_diff_zero", runtime_diff["runtime_source_diff_count"] == 0)
    check("03_input_lock", bool(inputs["frozen_artifact_sha256"]))
    check("04_execution_lock", execution["runtime_correction_quota"] == 0 and execution["test_expectation_correction_quota"] == 0)
    check("05_four_defects_closed", len(closure) == 4 and all(row["verdict"] == "CLOSED" for row in closure))
    for index, (name, artifact, predicate) in enumerate([
        ("Coordinator authority", "POST_R2_COORDINATOR_AUTHORITY_AUDIT_V2.json", lambda x: x["status"] == "PASS_FACT_ONLY_COORDINATOR"),
        ("sole owner chain", "POST_R2_AUTHORITY_OWNER_CHAIN_V2.json", lambda x: x["status"] == "PASS_SOLE_OWNER_CHAIN"),
        ("43 row fidelity", None, lambda _: len(fidelity_rows) == 43 and all(r["status"] == "PASS" for r in fidelity_rows)),
        ("exact one", "POST_R2_TRANSITION_EXACT_ONE_V2.json", lambda x: x["status"] == "PASS_EXACT_ONE"),
        ("43 dynamic", None, lambda _: len(dynamic_rows) == 43 and all(r["status"] == "PASS" for r in dynamic_rows)),
        ("critical coverage", "POST_R2_CRITICAL_ROUTE_COVERAGE_V2.json", lambda x: x["critical_dynamic_coverage_percent"] == 100.0),
        ("public orchestration", "POST_R2_INTEGRATION_ORCHESTRATION_CLOSURE_V2.json", lambda x: x["status"] == "PASS_GENUINE_PUBLIC_COMPOSITION"),
        ("canonical order", "POST_R2_CANONICAL_CALL_ORDER_V2.json", lambda x: x["status"] == "PASS_CANONICAL_ORDER"),
        ("start R0", "POST_R2_START_R0_CONFORMANCE_V2.json", lambda x: x["status"] == "PASS_START_R0"),
        ("primary C0", "POST_R2_PRIMARY_C0_CONFORMANCE_V2.json", lambda x: x["status"] == "PASS_PRIMARY_C0"),
        ("L2 L3", "POST_R2_L2_L3_CONFORMANCE_V2.json", lambda x: x["status"] == "PASS_L2_L3"),
        ("numeric", "POST_R2_NUMERIC_AUTHORITY_AUDIT_V2.json", lambda x: x["status"] == "PASS_NUMERIC_AUTHORITY"),
        ("deadline", "POST_R2_DEADLINE_CONFORMANCE_V2.json", lambda x: x["status"] == "PASS_DEADLINE_CONFORMANCE"),
        ("deadline points", "POST_R2_DEADLINE_OBSERVATION_POINT_AUDIT_V2.json", lambda x: x["status"] == "PASS_DEADLINE_OBSERVATION_POINTS"),
        ("alternative", "POST_R2_ALTERNATIVE_STATUS_CONFORMANCE_V2.json", lambda x: x["status"] == "PASS_ALTERNATIVE_STATUS_FIDELITY"),
        ("backup", "POST_R2_BACKUP_TOKEN_CONFORMANCE_V2.json", lambda x: x["status"] == "PASS_BACKUP_TOKEN_CONFORMANCE"),
        ("backup distinction", "POST_R2_BACKUP_STATE_DISTINCTION_VERDICT_V2.json", lambda x: x["verdict"] == "RESOLVED_NOT_A_BUG"),
        ("terminal", "POST_R2_TERMINAL_CONTEXT_AUTHORITY_VERDICT_V2.json", lambda x: x["verdict"] == "RESOLVED_ROUTE_DERIVED_NOT_A_BUG"),
        ("exceptions", "POST_R2_STAGE_EXCEPTION_CONFORMANCE_V2.json", lambda x: x["passed"] == 8 and x["total"] == 8),
        ("reason scope", "POST_R2_REASON_SCOPE_VERDICT_V2.json", lambda x: x["verdict"] == "RESOLVED_TYPED_SCOPE"),
        ("commit authority", "POST_R2_COMMIT_AUTHORITY_CHAIN_V2.json", lambda x: x["status"] == "PASS_COMMIT_AUTHORITY_CHAIN"),
        ("boundary", "POST_R2_ASSURANCE_BOUNDARY_CONFORMANCE_V2.json", lambda x: x["status"] == "PASS_ASSURANCE_BOUNDARY"),
        ("trace", "POST_R2_TRACE_FAULT_SEMANTICS_V2.json", lambda x: x["status"] == "PASS_TRACE_FAULT_SEMANTICS"),
        ("bypass", "POST_R2_BYPASS_PRESERVATION_VERDICT_V2.json", lambda x: x["status"] == "PASS_BYPASS_PRIOR_EVIDENCE_REUSABLE"),
        ("not a bug", "POST_R2_NOT_A_BUG_RETENTION_V2.json", lambda x: x["reopen_condition_count"] == 0),
    ], start=6):
        value = {} if artifact is None else read(artifact)
        check(f"{index:02d}_{name.lower().replace(' ', '_')}", predicate(value))

    check("31_e2e_core_6", sum(by_id[f"E2E-{i:02d}"]["passed"] for i in range(1, 7)) == 6)
    check("32_e2e_extended_6", sum(by_id[f"E2E-{i:02d}"]["passed"] for i in range(7, 13)) == 6)
    check("33_scenario_matrix_complete", scenarios["scenario_count"] >= 60)
    check("34_model_counterexamples_zero", model["counterexample_count"] == 0)
    tests = read("test_results.json")
    check("35_all_applicable_tests", tests["failed"] == 0)
    check("36_runtime_correction_zero", counts["runtime_correction"] == 0)
    for offset, key in enumerate(("real_active", "gpu", "smoke", "scientific_oracle", "official100", "real_bypass"), start=37):
        check(f"{offset:02d}_{key}_zero", counts[key] == 0)
    check("43_failure_register_complete", (TASK / "POST_R2_CONFORMANCE_FAILURE_REGISTER_V2.csv").exists())
    check("44_downstream_mechanical", decision["FINAL_STATUS"].startswith("BLOCKED_") if scenarios["failed_count"] else decision["FINAL_STATUS"].startswith("PASS_"))
    check("45_sweep_mode", scenarios["sweep_mode"] == "COMPLETE_INDEPENDENT_MATRIX")
    check("46_transition_domain", domain_pass("transition_43"))
    check("47_exact_one_domain", domain_pass("exact_one"))
    check("48_alternative_domain", domain_pass("alternative") and domain_pass("e2e_extended"))
    check("49_backup_domain", domain_pass("backup"))
    check("50_terminal_domain", domain_pass("terminal"))
    check("51_exception_domain", domain_pass("exception"))
    check("52_reason_scope_domain", domain_pass("reason_scope"))
    check("53_trace_fault_domain", domain_pass("trace_fault"))
    check("54_next_task", bool(decision["Only next task"]))

    failed = [item for item in checks if not item["passed"]]
    result = {
        "schema": "POST_R2_ACTIVE_RUNTIME_CONTRACT_CONFORMANCE_VALIDATION_V2",
        "check_count": len(checks),
        "passed_count": len(checks) - len(failed),
        "failed_count": len(failed),
        "checks": checks,
        "status": "PASS_POST_R2_ACTIVE_RUNTIME_CONTRACT_CONFORMANCE_V2_VALIDATION" if not failed else "BLOCKED_POST_R2_ACTIVE_RUNTIME_CONTRACT_CONFORMANCE_V2_VALIDATION",
    }
    (TASK / "validation_result.json").write_text(json.dumps(result, indent=2, sort_keys=True) + "\n", encoding="utf-8", newline="\n")
    return 0 if not failed else 1


if __name__ == "__main__":
    raise SystemExit(main())

