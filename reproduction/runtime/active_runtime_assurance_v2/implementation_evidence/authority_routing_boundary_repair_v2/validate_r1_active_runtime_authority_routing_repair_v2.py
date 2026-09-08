"""Validate the bounded R1 authority/routing repair (CPU/static only)."""

from __future__ import annotations

import ast
import csv
import hashlib
import json
import subprocess
import sys
from pathlib import Path


EVIDENCE = Path(__file__).resolve().parent
PACKAGE = EVIDENCE.parents[1]
REPO = PACKAGE.parents[2]
PR124 = "cef9dddc4ceb20e22f5962ee0740d92b91a3ff86"

# Keep imports deterministic when this validator is invoked by absolute path.
if str(REPO) not in sys.path:
    sys.path.insert(0, str(REPO))


def run(*args: str) -> str:
    return subprocess.check_output(args, cwd=REPO, text=True, stderr=subprocess.STDOUT).strip()


def sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def worktree_blob(path: str) -> str:
    return run("git", "hash-object", f"--path={path}", path)


def current_path(path: str) -> Path:
    """Prefer the caller's short relative path for Windows long-path files."""
    relative = Path(path)
    return relative if relative.is_file() else REPO / path


def method_identity(source: str, method: str) -> dict[str, str]:
    tree = ast.parse(source)
    for node in ast.walk(tree):
        if isinstance(node, ast.ClassDef) and node.name == "Supervisor":
            for item in node.body:
                if isinstance(item, (ast.FunctionDef, ast.AsyncFunctionDef)) and item.name == method:
                    segment = ast.get_source_segment(source, item) or ""
                    return {
                        "source_sha256": hashlib.sha256(segment.encode()).hexdigest(),
                        "ast_sha256": hashlib.sha256(ast.dump(item, annotate_fields=True, include_attributes=False).encode()).hexdigest(),
                    }
    raise KeyError(method)


def main() -> int:
    lock = json.loads((EVIDENCE / "R1_AUTHORITY_ROUTING_REPAIR_INPUT_LOCK.json").read_text(encoding="utf-8"))
    checks: list[dict[str, object]] = []

    def check(name: str, passed: bool, detail: object = None) -> None:
        checks.append({"name": name, "passed": bool(passed), "detail": detail})

    direct = lock["direct_upstream"]
    check("01_pr124_exact_identity", direct == {
        "repository": "kenqiana04/safer-splat", "pr": 124, "state": "OPEN_DRAFT",
        "title": "[Draft] Audit active runtime pre-repair architecture V2",
        "branch": "audit-active-runtime-pre-repair-architecture-v2", "head": PR124,
        "base": "revalidate-active-runtime-contract-conformance-v2", "base_sha": "3b01171d7d25c7f81efd53d0486ab95d7c73c7a9",
    })
    check("02_pr124_is_ancestor", run("git", "merge-base", PR124, "HEAD") == PR124)
    audit_ok = all(sha256(REPO / item["path"]) == item["sha256"] for item in lock["pr124_audit"].values())
    check("03_pr124_audit_artifacts_unchanged", audit_ok)
    check("04_r1_defect_allocation_exact", lock["defect_allocation"] == {"R1": ["D-AUTH-001", "D-TRANS-001"], "R2": ["D-EXC-001", "D-ALT-001"]})
    check("05_r2_defects_deferred", json.loads((EVIDENCE / "R1_DEFERRED_DEFECT_STATUS.json").read_text(encoding="utf-8"))["D-EXC-001"] == "OPEN_DEFERRED_TO_R2" and json.loads((EVIDENCE / "R1_DEFERRED_DEFECT_STATUS.json").read_text(encoding="utf-8"))["D-ALT-001"] == "OPEN_DEFERRED_TO_R2")
    source_freeze_path = EVIDENCE / "R1_AUTHORITY_ROUTING_SOURCE_FREEZE.json"
    source_freeze = json.loads(source_freeze_path.read_text(encoding="utf-8")) if source_freeze_path.is_file() else {}
    source_freeze_alias_path = EVIDENCE / "R1_AUTHORITY_ROUTING_SOURCE_FREEZE_V2.json"
    source_freeze_alias = json.loads(source_freeze_alias_path.read_text(encoding="utf-8")) if source_freeze_alias_path.is_file() else {}
    frozen_paths = set(source_freeze.get("files", {}))
    r1_validator_path = "reproduction/runtime/active_runtime_assurance_v2/implementation_evidence/authority_routing_boundary_repair_v2/validate_r1_active_runtime_authority_routing_repair_v2.py"
    expected_source_paths = set(lock["forbidden_runtime_file_shas"]) | set(lock["allowed_file_pre_repair_shas"]) | {
        "reproduction/runtime/active_runtime_assurance_v2/tests/test_r1_authority_routing_boundary.py",
        "reproduction/runtime/active_runtime_assurance_v2/tests/test_r1_transition_metadata_round_trip.py",
        "reproduction/runtime/active_runtime_assurance_v2/tests/test_r1_destination_derivation.py",
        "reproduction/runtime/active_runtime_assurance_v2/tests/test_r1_exact_one_and_repeated_guard.py",
    } | {r1_validator_path}
    check("05a_source_freeze_present", bool(source_freeze) and source_freeze.get("upstream") == PR124)
    check("05b_source_freeze_scope_complete", expected_source_paths <= frozen_paths)
    check("05b_alias_matches_canonical", bool(source_freeze_alias) and source_freeze_alias == source_freeze)
    check("05c_source_freeze_current_hashes", bool(source_freeze) and all(
        (not record.get("exists")) or record.get("sha256") == sha256(current_path(path))
        for path, record in source_freeze.get("files", {}).items()
    ))

    allowed_paths = {
        "reproduction/runtime/active_runtime_assurance_v2/active_cycle.py",
        "reproduction/runtime/active_runtime_assurance_v2/runtime_types.py",
        "reproduction/runtime/active_runtime_assurance_v2/supervisor.py",
    }
    changed = set(run("git", "diff", "--name-only", PR124, "HEAD").splitlines())
    expected_prefix = "reproduction/runtime/active_runtime_assurance_v2/"
    check("06_changed_source_scope", all(path.startswith(expected_prefix) for path in changed))
    check("07_allowed_runtime_set", changed & allowed_paths <= allowed_paths)
    check("08_forbidden_runtime_blobs_exact", all(value is None or worktree_blob(path) == value for path, value in lock["forbidden_runtime_file_shas"].items() if value is not None))
    check("09_protected_source_diff_zero", all(value is None or worktree_blob(path) == value for path, value in lock["forbidden_runtime_file_shas"].items() if value is not None))

    active_path = PACKAGE / "active_cycle.py"
    active = active_path.read_text(encoding="utf-8")
    types = (PACKAGE / "runtime_types.py").read_text(encoding="utf-8")
    supervisor_path = PACKAGE / "supervisor.py"
    supervisor = supervisor_path.read_text(encoding="utf-8")
    check("10_no_coordinator_alt_permission", "alternative_search_allowed" not in active and "allow_alt" not in active)
    check("11_no_coordinator_navigation_suppression", all(token not in active for token in ("navigation_timely", "routing_candidate", "navigation_ready")))
    check("12_no_coordinator_terminal_policy_field", "terminal_ready" not in active)
    check("13_no_coordinator_deadline_path_branch", "if deadline.status" not in active and "deadline.status !=" not in active)
    check("14_no_coordinator_policy_routing_decision", "RoutingDecision(" not in active)
    check("15_no_coordinator_direct_plant", "plant_commit.commit" not in active and "import dynamics" not in active.lower())
    check("16_supervisor_route_owner", "def route_transition(" in supervisor and "return self.transition_table.resolve" in supervisor)
    check("17_supervisor_repeated_guard_owner", "def routing_guard_block(" in supervisor)
    check("18_supervisor_final_selector_present", "def arbitrate(" in supervisor)
    check("19_fact_only_context_fields", all(token in types for token in ("certified_candidate_available", "terminal_evidence_eligible", "backup_state", "candidate_provenance_identity")))
    check("20_legacy_hints_not_written_by_coordinator", "legacy_alternative_hint" not in active and "legacy_navigation_hint" not in active and "legacy_terminal_hint" not in active)
    route_input = json.loads((EVIDENCE / "R1_ROUTE_INPUT_AUTHORITY_AUDIT_V2.json").read_text(encoding="utf-8"))
    check("20a_route_input_authority_audit", route_input.get("status") == "PASS" and route_input.get("coordinator_policy_inputs") == [] and route_input.get("destination_derived_policy") is False)

    from reproduction.runtime.active_runtime_assurance_v2.supervisor import TransitionTable

    transition_path = REPO / "reproduction/specification/method_logic_closure_v2/STATE_TRANSITION_TABLE_V2.csv"
    table = TransitionTable.from_csv(transition_path)
    check("21_actual_43_rules", len(table.rules) == 43)
    check("22_actual_43_unique_ids", len(table.by_id) == 43)
    with transition_path.open(encoding="utf-8", newline="") as handle:
        rows = list(csv.DictReader(handle))
    check("23_transition_rows_unchanged", sha256(transition_path) == lock["pr107_transition_table"]["sha256"])
    matrix_path = EVIDENCE / "R1_FROZEN_METADATA_CARRIER_MATRIX_V2.csv"
    with matrix_path.open(encoding="utf-8", newline="") as handle:
        matrix = list(csv.DictReader(handle))
    check("24_normative_carrier_43_of_43", len(matrix) == 43 and all(row["carrier_verdict"] == "EXACT_CARRIED" for row in matrix))
    round_trip = json.loads((EVIDENCE / "R1_43_RULE_ROUND_TRIP_RESULT.json").read_text(encoding="utf-8"))
    check("25_round_trip_43_of_43", round_trip["rule_count"] == 43 and round_trip["resolved_count"] == 43 and round_trip["exact"] is True and round_trip["mismatch_count"] == 0)
    derivation = json.loads((EVIDENCE / "R1_DESTINATION_DERIVATION_REMOVAL_V2.json").read_text(encoding="utf-8"))
    check("26_destination_derivation_removed", derivation["destination_only_derivation"] is False and all(value.startswith("EXPLICIT_CARRIED") for value in derivation["unsafe_fields"].values()))
    exact_one = json.loads((EVIDENCE / "R1_EXACT_ONE_REGRESSION_V2.json").read_text(encoding="utf-8"))
    check("27_exact_one_preserved", exact_one["legal_exact_one"] and exact_one["zero_match_typed_block"] and exact_one["multi_match_typed_block"] and not exact_one["first_match_wins"] and not exact_one["default_boundary"])
    check("28_transition_metadata_fields_present", all(hasattr(table.by_id["L1_PASS"], field) for field in ("old_backup_retained", "new_backup_created", "theorem_interpretation", "may_start_new_search", "requires_arbitration", "deadline_interpretation")))
    check("29_route_decision_carries_metadata", all(token in supervisor for token in ("rule.may_start_next_stage", "rule.may_start_new_search", "rule.requires_arbitration", "rule.deadline_interpretation", "rule.old_backup_retained", "rule.theorem_interpretation")))

    contracts = [
        "reproduction/specification/method_logic_closure_v2/STATE_TRANSITION_TABLE_V2.csv",
        "reproduction/specification/runtime_assurance_deadline_authority_v2/RUNTIME_ASSURANCE_DEADLINE_AUTHORITY_V2.json",
        "reproduction/specification/alternative_source_authority_v2/ALTERNATIVE_SOURCE_AUTHORITY_V2.json",
        "reproduction/design/active_runtime_public_cycle_composition_v2/EXECUTABLE_TRANSITION_ROUTING_DESIGN_V2.json",
    ]
    check("30_frozen_contracts_unchanged", all(worktree_blob(path) == (lock["pr107_transition_table"]["git_blob"] if path.endswith("STATE_TRANSITION_TABLE_V2.csv") else lock["pr110_deadline_contract"]["git_blob"] if path.endswith("RUNTIME_ASSURANCE_DEADLINE_AUTHORITY_V2.json") else lock["pr111_alternative_authority"]["git_blob"] if path.endswith("ALTERNATIVE_SOURCE_AUTHORITY_V2.json") else lock["pr121_routing_design"]["git_blob"]) for path in contracts))

    bypass = json.loads((EVIDENCE / "R1_BYPASS_PRESERVATION_AUDIT_V2.json").read_text(encoding="utf-8"))
    check("31_bypass_gate_pass", bypass["status"] == "PASS_PRESERVED" and bypass["BYPASS_REVALIDATION_REQUIRED"] is False and all(item["unchanged"] for item in bypass["methods"].values()))
    check("32_shared_runtime_unchanged", all(bypass[key] for key in ("active_runner_unchanged", "plant_commit_unchanged", "backup_token_store_unchanged", "terminal_runtime_unchanged", "trace_writer_unchanged")))
    deferred = json.loads((EVIDENCE / "R1_DEFERRED_DEFECT_STATUS.json").read_text(encoding="utf-8"))
    check("33_r2_not_silently_fixed", deferred.get("D-EXC-001") == "OPEN_DEFERRED_TO_R2" and deferred.get("D-ALT-001") == "OPEN_DEFERRED_TO_R2")
    check("34_active_api_and_runner_reuse", all(token in active for token in ("def start_trial(", "def run_cycle(", "def finalize_trial(", "self.active_runner.commit_active_decision")))

    suite = subprocess.run([sys.executable, "-B", "-m", "unittest", "discover", "-s", str(PACKAGE / "tests"), "-q"], cwd=REPO, text=True, capture_output=True)
    suite_output = suite.stderr + suite.stdout
    check("35_r1_and_existing_cpu_tests", suite.returncode == 0 and "Ran 120 tests" in suite_output, {"returncode": suite.returncode, "expected_test_count_seen": "Ran 120 tests" in suite_output})
    probes = json.loads((EVIDENCE / "R1_PROBE_RESULTS_V2.json").read_text(encoding="utf-8"))
    check("36_bounded_r1_probes", probes["probe_count"] >= 24 and probes["failed"] == 0 and probes["passed"] == probes["probe_count"])
    check("37_no_runtime_execution", json.loads((EVIDENCE / "test_results.json").read_text(encoding="utf-8"))["real_execution"] == {"active": 0, "bypass_pairs": 0, "gpu": 0, "official100": 0, "oracle": 0, "smoke": 0})
    counts = json.loads((EVIDENCE / "FINAL_DECISION.json").read_text(encoding="utf-8"))["real_execution_counts"]
    check("38_real_active_zero", counts["active"] == 0)
    check("39_gpu_zero", counts["gpu"] == 0)
    check("40_smoke_zero", counts["smoke"] == 0)
    check("41_oracle_zero", counts["oracle"] == 0)
    check("42_official100_zero", counts["official100"] == 0)
    check("43_real_bypass_zero", counts["real_bypass_pairs"] == 0)
    check("44_next_task_r2", json.loads((EVIDENCE / "FINAL_DECISION.json").read_text(encoding="utf-8"))["Only next task"] == "REPAIR_ACTIVE_RUNTIME_EXCEPTION_AND_UNKNOWN_ROUTING_V2")

    failed = [item for item in checks if not item["passed"]]
    result = {
        "schema": "R1_AUTHORITY_ROUTING_REPAIR_VALIDATION_V2",
        "checks": checks,
        "check_count": len(checks),
        "failed_count": len(failed),
        "status": "PASS_R1_ACTIVE_RUNTIME_AUTHORITY_ROUTING_REPAIR_V2_VALIDATION" if not failed else "BLOCKED_R1_ACTIVE_RUNTIME_AUTHORITY_ROUTING_REPAIR_V2_VALIDATION",
        "r1_defects_closed": ["D-AUTH-001", "D-TRANS-001"],
        "r2_defects_deferred": ["D-EXC-001", "D-ALT-001"],
        "real_execution_counts": counts,
    }
    (EVIDENCE / "validation_result.json").write_text(json.dumps(result, indent=2, ensure_ascii=False, sort_keys=True) + "\n", encoding="utf-8", newline="\n")
    print(result["status"])
    for item in failed:
        print(item["name"], item["detail"])
    return 0 if not failed else 1


if __name__ == "__main__":
    raise SystemExit(main())
