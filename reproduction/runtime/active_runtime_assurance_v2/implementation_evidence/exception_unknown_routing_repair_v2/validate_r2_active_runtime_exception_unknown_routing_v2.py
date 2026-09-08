"""Fail-closed validator for the bounded R2 exception/UNKNOWN repair."""

from __future__ import annotations

import ast
import csv
import hashlib
import json
import subprocess
from pathlib import Path


HERE = Path(__file__).resolve().parent
ROOT = Path(__file__).resolve().parents[5]
RUNTIME = ROOT / "reproduction/runtime/active_runtime_assurance_v2"
PARENT = "303aa01c08e82d1d77a5f5cabf5127344109a996"
EXPECTED_FORBIDDEN = {
    "alternative_provider.py": "32da73b46fc7c5b0fb4b0ac7a5d583a0f3dba980",
    "active_runner.py": "64b747656b031881123c92587d1beca6e742be5e",
    "plant_commit.py": "f9116db0690983252ea0f60d286399b71d644134",
    "backup_token_store.py": "3af371733638bcd6aac9240db38328d9e2f6154f",
    "terminal_runtime.py": "9cbc9769970626ecee600e83909655f44e75466d",
    "trace_writer.py": "f7d1c768a28d36ab1ef88614bd01c8722e9ea292",
    "authority_registry.py": "c444b077fde51dcffc3c057302d1336dcb7ce0c9",
    "start_admission.py": "40e6774bc37cae76758db97ee3db43a48e373d55",
    "diagnostic_r0.py": "8556cdb5aa9082e323d47419736ceec5bb7660ae",
    "l1_runtime.py": "6a477fb4fd84f6c04c0e68a586e43baf6d5aa77c",
    "primary_proposal_adapter.py": "2de4ad2cbf92a71affd8a2d2630094f9a6d29936",
    "c0_admission.py": "3cbf74596980b22eb94d3233134f270ce6cc7f9f",
    "l2_runtime.py": "b7b26075ea01878deea39a12f66b5990c0d08de1",
    "l3_runtime.py": "93db2095cfc3102b37f35bfef91a611786de71d2",
    "deadline_runtime.py": "cf81341b655deb7b8b5a6261eafb6171580dbd45",
}


def load(name: str):
    return json.loads((HERE / name).read_text(encoding="utf-8"))


def sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def git(*args: str) -> str:
    return subprocess.check_output(["git", *args], cwd=ROOT, text=True).strip()


def method_ast(text: str, name: str) -> str:
    tree = ast.parse(text)
    for node in ast.walk(tree):
        if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)) and node.name == name:
            return hashlib.sha256(ast.dump(node, include_attributes=False).encode()).hexdigest()
    raise AssertionError(name)


def main() -> int:
    checks: list[dict] = []

    def check(name: str, condition: bool, detail=None) -> None:
        checks.append({"name": name, "passed": bool(condition), "detail": detail})

    input_lock = load("R2_EXCEPTION_UNKNOWN_REPAIR_INPUT_LOCK.json")
    diff_audit = load("R2_RUNTIME_DIFF_AUDIT_V2.json")
    stage_matrix = load("R2_STAGE_EXCEPTION_ROUTE_MATRIX_V2.json")
    alt_fidelity = load("R2_ALTERNATIVE_STATUS_FIDELITY_V2.json")
    r1_audit = load("R2_R1_REGRESSION_AUDIT_V2.json")
    bypass = load("R2_BYPASS_PRESERVATION_AUDIT_V2.json")
    probes = load("R2_PROBE_RESULTS_V2.json")
    model = load("R2_EXCEPTION_UNKNOWN_MODEL_CHECK_V2.json")
    tests = load("test_results.json")
    final = load("FINAL_DECISION.json")
    active = (RUNTIME / "active_cycle.py").read_text(encoding="utf-8")
    types = (RUNTIME / "runtime_types.py").read_text(encoding="utf-8")
    supervisor = (RUNTIME / "supervisor.py").read_text(encoding="utf-8")

    check("01_pr125_exact_identity", input_lock["pr125"]["head"] == PARENT and git("merge-base", "--is-ancestor", PARENT, "HEAD") == "")
    check("02_r1_remains_pass_frozen", r1_audit["status"] == "PASS_R1_REGRESSION_PRESERVED")
    check("03_d_exc_exact_input", input_lock["defect_row_sha256"]["D-EXC-001"] == "3574095a790051820e994c7bad983c2655430f1189e7729ab5636d5e1ab15cfc")
    check("04_d_alt_exact_input", input_lock["defect_row_sha256"]["D-ALT-001"] == "83237090aec467d2b0249ca691213d3a822c1e54e24fd4f979a4959f15d77937")
    check("05_allowed_source_scope", set(diff_audit["changed_runtime_source_files"]) <= {"active_cycle.py", "runtime_types.py", "supervisor.py"})
    current_forbidden = {name: git("rev-parse", f"HEAD:reproduction/runtime/active_runtime_assurance_v2/{name}") for name in EXPECTED_FORBIDDEN}
    check("06_forbidden_blobs_unchanged", current_forbidden == EXPECTED_FORBIDDEN)
    check("07_typed_reason_scope_exists", all(value in types for value in ("class ReasonScope", "CANDIDATE_LOCAL_COMPUTATION", "GLOBAL_AUTHORITY_OR_EVIDENCE", "INFRASTRUCTURE_HEALTH", "UNRESOLVED_SCOPE")))
    check("08_no_substring_scope_policy", "def _reason_scope" not in active and "if any(token in value" not in active and " in reason" not in supervisor)
    check("09_typed_stage_failure_evidence", "class StageFailureEvidence" in types and "@dataclass(frozen=True)" in types)
    for number, stage in enumerate(("L1", "PRIMARY_PROPOSAL", "C0", "L2", "L3", "ALT_SEARCH", "TERMINAL_EVALUATION", "ARBITRATION"), start=10):
        check(f"{number:02d}_{stage.lower()}_exception_handled", stage in stage_matrix["stages"] and stage_matrix["stages"][stage]["passed"])
    check("18_resolved_exception_route_executed", stage_matrix["resolved_routes_executed"])
    check("19_no_exception_unconditional_block", "context, route = self._stage_failure_route" in active and "return self._blocked_result(context, error)" not in active)
    check("20_authorized_fallback_reachable", load("R2_EXCEPTION_FALLBACK_MATRIX_V2.json")["passed_count"] == 6)
    for number, status in enumerate(("ALT_AVAILABLE", "NO_ALTERNATIVE_AVAILABLE", "SOURCE_INVALID", "PROVENANCE_MISSING"), start=21):
        check(f"{number:02d}_{status.lower()}_distinct", alt_fidelity["statuses"][status]["preserved"])
    check("25_unknown_provider_status_typed", alt_fidelity["statuses"]["UNRESOLVED_STATUS"]["preserved"])
    check("26_only_lawful_absence_maps_exhausted", alt_fidelity["only_lawful_absence_maps_exhausted"])
    check("27_no_synthetic_alternative", "make_candidate" not in active and "random" not in active and "interpol" not in active.lower())
    check("28_provider_unchanged", current_forbidden["alternative_provider.py"] == EXPECTED_FORBIDDEN["alternative_provider.py"])
    table_path = ROOT / "reproduction/specification/method_logic_closure_v2/STATE_TRANSITION_TABLE_V2.csv"
    check("29_43_table_unchanged", sha256(table_path) == input_lock["normative_sha256"]["PR107_STATE_TRANSITION_TABLE_V2.csv"])
    round_trip = json.loads((RUNTIME / "implementation_evidence/authority_routing_boundary_repair_v2/R1_43_RULE_ROUND_TRIP_RESULT.json").read_text(encoding="utf-8"))
    check("30_r1_43_roundtrip_pass", round_trip.get("exact") is True and round_trip.get("resolved_count") == 43 and round_trip.get("mismatch_count") == 0)
    check("31_r1_authority_regression_pass", r1_audit["failed_count"] == 0)
    parent_supervisor = git("show", f"{PARENT}:reproduction/runtime/active_runtime_assurance_v2/supervisor.py")
    check("32_supervisor_arbitrate_preserved", method_ast(parent_supervisor, "arbitrate") == method_ast(supervisor, "arbitrate"))
    check("33_runner_plant_unchanged", all(current_forbidden[name] == EXPECTED_FORBIDDEN[name] for name in ("active_runner.py", "plant_commit.py")))
    check("34_backup_terminal_trace_unchanged", all(current_forbidden[name] == EXPECTED_FORBIDDEN[name] for name in ("backup_token_store.py", "terminal_runtime.py", "trace_writer.py")))
    check("35_bypass_preserved", bypass["status"] == "PASS_PRESERVED" and bypass["BYPASS_REVALIDATION_REQUIRED"] is False)
    check("36_stage_matrix_pass", stage_matrix["passed_count"] == 8)
    scope = load("R2_REASON_SCOPE_MAPPING_V2.json")
    check("37_reason_scope_matrix_pass", scope["unmapped_fallback"] == "UNRESOLVED_SCOPE" and len(scope["mappings"]) >= 17)
    check("38_probe_count_and_pass", probes["probe_count"] >= 32 and probes["failed_count"] == 0)
    check("39_model_counterexamples_zero", model["counterexample_count"] == 0)
    check("40_existing_cpu_tests_pass", tests["returncode"] == 0 and tests["failed_count"] == 0)
    counts = final["real_execution_counts"]
    check("41_real_active_zero", counts["active"] == 0)
    check("42_gpu_zero", counts["gpu"] == 0)
    check("43_smoke_zero", counts["smoke"] == 0)
    check("44_scientific_oracle_zero", counts["oracle"] == 0)
    check("45_official100_zero", counts["official100"] == 0)
    check("46_real_bypass_zero", counts["real_bypass"] == 0)
    check("47_next_task_full_reconformance", final["Only next task"] == "REVALIDATE_ACTIVE_RUNTIME_CONTRACT_CONFORMANCE_V2")

    failed = [item for item in checks if not item["passed"]]
    result = {
        "schema": "R2_ACTIVE_RUNTIME_EXCEPTION_UNKNOWN_ROUTING_VALIDATION_V2",
        "status": "PASS_R2_ACTIVE_RUNTIME_EXCEPTION_UNKNOWN_ROUTING_V2_VALIDATION" if not failed else "FAIL_R2_ACTIVE_RUNTIME_EXCEPTION_UNKNOWN_ROUTING_V2_VALIDATION",
        "check_count": len(checks),
        "failed_count": len(failed),
        "checks": checks,
    }
    (HERE / "validation_result.json").write_text(json.dumps(result, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    return 0 if not failed else 1


if __name__ == "__main__":
    raise SystemExit(main())
