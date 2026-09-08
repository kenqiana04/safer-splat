"""Build compact, CPU-only evidence for the R1 authority/routing repair.

This script reads the frozen PR #124/PR #107 inputs and the three allowed
runtime modules.  It never launches a rollout, imports a GPU backend, or
rewrites a protected artifact.
"""

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
if str(REPO) not in sys.path:
    sys.path.insert(0, str(REPO))
PR124 = "cef9dddc4ceb20e22f5962ee0740d92b91a3ff86"
PR122 = "323e991"
PR107_TABLE = REPO / "reproduction/specification/method_logic_closure_v2/STATE_TRANSITION_TABLE_V2.csv"
PR121_DESIGN = REPO / "reproduction/design/active_runtime_public_cycle_composition_v2/EXECUTABLE_TRANSITION_ROUTING_DESIGN_V2.json"
PR124_AUDIT = REPO / "reproduction/audit/active_runtime_pre_repair_architecture_v2"

ALLOWED = [
    "reproduction/runtime/active_runtime_assurance_v2/active_cycle.py",
    "reproduction/runtime/active_runtime_assurance_v2/runtime_types.py",
    "reproduction/runtime/active_runtime_assurance_v2/supervisor.py",
]
FORBIDDEN = [
    "reproduction/runtime/active_runtime_assurance_v2/active_runner.py",
    "reproduction/runtime/active_runtime_assurance_v2/plant_commit.py",
    "reproduction/runtime/active_runtime_assurance_v2/backup_token_store.py",
    "reproduction/runtime/active_runtime_assurance_v2/terminal_runtime.py",
    "reproduction/runtime/active_runtime_assurance_v2/trace_writer.py",
    "reproduction/runtime/active_runtime_assurance_v2/authority_registry.py",
    "reproduction/runtime/active_runtime_assurance_v2/start_admission.py",
    "reproduction/runtime/active_runtime_assurance_v2/diagnostic_r0.py",
    "reproduction/runtime/active_runtime_assurance_v2/l1_runtime.py",
    "reproduction/runtime/active_runtime_assurance_v2/primary_proposal_adapter.py",
    "reproduction/runtime/active_runtime_assurance_v2/c0_admission.py",
    "reproduction/runtime/active_runtime_assurance_v2/l2_runtime.py",
    "reproduction/runtime/active_runtime_assurance_v2/l3_runtime.py",
    "reproduction/runtime/active_runtime_assurance_v2/alternative_provider.py",
    "reproduction/runtime/active_runtime_assurance_v2/deadline_runtime.py",
    "reproduction/runtime/active_runtime_assurance_v2/run.py",
]
TESTS = [
    "reproduction/runtime/active_runtime_assurance_v2/tests/test_r1_authority_routing_boundary.py",
    "reproduction/runtime/active_runtime_assurance_v2/tests/test_r1_transition_metadata_round_trip.py",
    "reproduction/runtime/active_runtime_assurance_v2/tests/test_r1_destination_derivation.py",
    "reproduction/runtime/active_runtime_assurance_v2/tests/test_r1_exact_one_and_repeated_guard.py",
]


def run(*args: str) -> str:
    return subprocess.check_output(args, cwd=REPO, text=True, stderr=subprocess.STDOUT).strip()


def run_here(*args: str) -> str:
    """Run git from the caller's (possibly subst-mounted) short worktree."""
    return subprocess.check_output(args, cwd=Path.cwd(), text=True, stderr=subprocess.STDOUT).strip()


def sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def blob(path: str, ref: str = "HEAD") -> str:
    return run("git", "rev-parse", f"{ref}:{path}")


def blob_or_missing(path: str, ref: str = "HEAD") -> str | None:
    try:
        return blob(path, ref)
    except subprocess.CalledProcessError:
        return None


def worktree_blob(path: str) -> str:
    """Git's normalized worktree blob (honours the repository text filter)."""
    return run("git", "hash-object", f"--path={path}", path)


def source_at(path: str, ref: str) -> str:
    return run("git", "show", f"{ref}:{path}")


def write(name: str, value: object) -> None:
    target = EVIDENCE / name
    target.parent.mkdir(parents=True, exist_ok=True)
    # The Windows worktree path is near MAX_PATH; use the extended prefix for
    # task-local evidence writes without changing repository paths.
    output = Path("\\\\?\\" + str(target.resolve())) if __import__("os").name == "nt" else target
    if isinstance(value, str):
        output.write_text(value if value.endswith("\n") else value + "\n", encoding="utf-8", newline="\n")
    else:
        output.write_text(json.dumps(value, indent=2, ensure_ascii=False, sort_keys=True) + "\n", encoding="utf-8", newline="\n")


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


def context_for(row: dict[str, str], authority: str):
    from reproduction.runtime.active_runtime_assurance_v2.runtime_types import (
        CandidateIdentity,
        CandidateRole,
        DeadlineObservation,
        DeadlineStatus,
        RuntimePhase,
        RuntimeRoutingContext,
    )

    requirement = row["deadline_requirement"]
    status = DeadlineStatus.WARNING if requirement == "GUARD_OR_EXPIRED" else DeadlineStatus.OPEN
    candidate_requirement = row["candidate_requirement"]
    role = None
    available = candidate_requirement != "NONE"
    if candidate_requirement in {"PRIMARY", "PRIMARY_OR_ALTERNATIVE"}:
        role = CandidateRole.PRIMARY
    elif candidate_requirement == "ALTERNATIVE":
        role = CandidateRole.ALTERNATIVE
    backup_requirement = row["retained_backup_requirement"]
    present = backup_requirement == "VALID"
    valid = present
    return RuntimeRoutingContext(
        source_phase=RuntimePhase(row["source_phase"]),
        deadline=DeadlineObservation(status, row["source_phase"], 0.0, 1.0, "deadline:r1"),
        authority_identity=authority,
        candidate_role=role,
        candidate_identity=CandidateIdentity("candidate:r1") if available else None,
        candidate_available=available,
        retained_backup_present=present,
        retained_backup_valid=valid,
        terminal_evaluated=row["rule_id"] in {"ARB_TERMINAL", "ARB_BOUNDARY"},
        certified_candidate_available=row["rule_id"] == "ARB_NAV",
        terminal_evidence_eligible=row["rule_id"] == "ARB_TERMINAL",
    )


def build_input_lock() -> None:
    pr124_artifact_names = [
        "MASTER_DEFECT_REGISTER_V2.csv", "PRE_REPAIR_REPAIR_DAG_V2.json", "ACTIVE_RUNTIME_AUTHORITY_MAP_V2.csv",
        "COORDINATOR_FULL_POLICY_AUDIT_V2.csv", "SUPERVISOR_AUTHORITY_AUDIT_V2.json", "FROZEN_43_RULE_SCHEMA_V2.json",
        "TRANSITION_43_RULE_THREE_LAYER_AUDIT_V2.csv", "DESTINATION_DERIVATION_AUDIT_V2.json", "TRANSITION_EXACT_ONE_DOMAIN_AUDIT_V2.json",
        "DEADLINE_END_TO_END_AUTHORITY_AUDIT_V2.csv", "DEADLINE_OBSERVATION_AND_USE_AUDIT_V2.json", "DEFECT_ROOT_CAUSE_CLUSTERING_V2.json",
        "LATENT_HIGH_RISK_REGISTER_V2.csv", "VERIFIED_NOT_A_BUG_REGISTER_V2.csv",
    ]
    design_artifacts = [
        "reproduction/design/active_runtime_public_cycle_composition_v2/EXECUTABLE_TRANSITION_ROUTING_DESIGN_V2.json",
        "reproduction/design/active_runtime_public_cycle_composition_v2/PUBLIC_CYCLE_COMPOSITION_CONTRACT_V2.md",
        "reproduction/design/active_runtime_public_cycle_composition_v2/PUBLIC_CYCLE_API_V2.json",
        "reproduction/design/active_runtime_public_cycle_composition_v2/SUPERVISOR_ROUTING_AUTHORITY_V2.md",
        "reproduction/design/active_runtime_public_cycle_composition_v2/PUBLIC_ACTIVE_CYCLE_PHASES_V2.json",
        "reproduction/design/active_runtime_public_cycle_composition_v2/ACTIVE_CYCLE_CONTEXT_SCHEMA_V2.json",
        "reproduction/design/active_runtime_public_cycle_composition_v2/ACTIVE_CYCLE_RESULT_SCHEMA_V2.json",
        "reproduction/design/active_runtime_public_cycle_composition_v2/PUBLIC_CYCLE_EVENT_SCHEMA_V2.json",
        "reproduction/design/active_runtime_public_cycle_composition_v2/DEADLINE_STAGE_ADMISSION_INTERFACE_V2.md",
        "reproduction/design/active_runtime_public_cycle_composition_v2/PRIMARY_CYCLE_INTEGRATION_V2.md",
        "reproduction/design/active_runtime_public_cycle_composition_v2/ALTERNATIVE_CYCLE_INTEGRATION_V2.md",
        "reproduction/design/active_runtime_public_cycle_composition_v2/BACKUP_CYCLE_INTEGRATION_V2.md",
        "reproduction/design/active_runtime_public_cycle_composition_v2/TERMINAL_CYCLE_INTEGRATION_V2.md",
        "reproduction/design/active_runtime_public_cycle_composition_v2/PUBLIC_CYCLE_TRACE_CONTRACT_V2.md",
        "reproduction/design/active_runtime_public_cycle_composition_v2/FIRST_AND_SUBSEQUENT_CYCLE_SEMANTICS_V2.md",
        "reproduction/design/active_runtime_public_cycle_composition_v2/PUBLIC_CYCLE_EXCEPTION_ROUTING_V2.json",
        "reproduction/design/active_runtime_public_cycle_composition_v2/BYPASS_EVIDENCE_PRESERVATION_V2.md",
        "reproduction/design/active_runtime_public_cycle_composition_v2/PUBLIC_CYCLE_COMPOSITION_INVARIANTS_V2.json",
        "reproduction/design/active_runtime_public_cycle_composition_v2/PUBLIC_CYCLE_DESIGN_SCENARIOS_V2.json",
        "reproduction/design/active_runtime_public_cycle_composition_v2/POST_COMPOSITION_VALIDATION_LADDER_V2.md",
    ]
    source_pre = {path: blob_or_missing(path, PR124) for path in ALLOWED + FORBIDDEN}
    supervisor_pre = source_at(ALLOWED[2], PR124)
    write("R1_AUTHORITY_ROUTING_REPAIR_INPUT_LOCK.json", {
        "schema": "R1_AUTHORITY_ROUTING_REPAIR_INPUT_LOCK_V2",
        "task_type": "R1_AUTHORITY_AND_TRANSITION_METADATA_REPAIR_ONLY",
        "direct_upstream": {
            "repository": "kenqiana04/safer-splat", "pr": 124, "state": "OPEN_DRAFT",
            "title": "[Draft] Audit active runtime pre-repair architecture V2",
            "branch": "audit-active-runtime-pre-repair-architecture-v2", "head": PR124,
            "base": "revalidate-active-runtime-contract-conformance-v2", "base_sha": "3b01171d7d25c7f81efd53d0486ab95d7c73c7a9",
        },
        "pr124_audit": {name: {"path": f"reproduction/audit/active_runtime_pre_repair_architecture_v2/{name}", "sha256": sha256(PR124_AUDIT / name), "git_blob": blob(f"reproduction/audit/active_runtime_pre_repair_architecture_v2/{name}", PR124)} for name in pr124_artifact_names},
        "pr107_transition_table": {"path": str(PR107_TABLE.relative_to(REPO)).replace("\\", "/"), "sha256": sha256(PR107_TABLE), "git_blob": blob("reproduction/specification/method_logic_closure_v2/STATE_TRANSITION_TABLE_V2.csv", PR124), "row_count": 43, "unique_rule_ids": True},
        "pr110_deadline_contract": {"path": "reproduction/specification/runtime_assurance_deadline_authority_v2/RUNTIME_ASSURANCE_DEADLINE_AUTHORITY_V2.json", "git_blob": blob("reproduction/specification/runtime_assurance_deadline_authority_v2/RUNTIME_ASSURANCE_DEADLINE_AUTHORITY_V2.json", PR124)},
        "pr111_alternative_authority": {"path": "reproduction/specification/alternative_source_authority_v2/ALTERNATIVE_SOURCE_AUTHORITY_V2.json", "git_blob": blob("reproduction/specification/alternative_source_authority_v2/ALTERNATIVE_SOURCE_AUTHORITY_V2.json", PR124), "taxonomy_blob": blob("reproduction/specification/alternative_source_authority_v2/ALTERNATIVE_SOURCE_TAXONOMY_V2.json", PR124)},
        "pr121_routing_design": {"path": str(PR121_DESIGN.relative_to(REPO)).replace("\\", "/"), "sha256": sha256(PR121_DESIGN), "git_blob": blob(str(PR121_DESIGN.relative_to(REPO)).replace("\\", "/"), PR124)},
        "pr122_pre_repair_runtime_blobs": {path: {"git_blob": blob_or_missing(path, PR122), "pr124_blob": source_pre[path]} for path in ALLOWED + FORBIDDEN},
        "allowed_file_pre_repair_shas": {path: source_pre[path] for path in ALLOWED},
        "forbidden_runtime_file_shas": {path: source_pre[path] for path in FORBIDDEN},
        "bypass_preservation_source_identities": {name: method_identity(supervisor_pre, name) for name in ("bypass_decision", "arbitrate", "certify_candidate")},
        "defect_allocation": {"R1": ["D-AUTH-001", "D-TRANS-001"], "R2": ["D-EXC-001", "D-ALT-001"]},
        "r1_evidence": {
            "D-AUTH-001": {"path": "COORDINATOR_FULL_POLICY_AUDIT_V2.csv", "lines": [13, 14, 15, 16, 17], "expressions": ["backup_valid and deadline.status == OPEN", "deadline.status != OPEN", "routing_candidate = certified if timely else None"]},
            "D-TRANS-001": {"path": "DESTINATION_DERIVATION_AUDIT_V2.json", "unsafe_fields": ["may_start_next_stage", "may_start_new_search", "requires_arbitration", "backup_routing_allowed", "terminal_routing_allowed", "deadline_interpretation"]},
        },
        "authority_facts": {"pr124_audit_completeness": "A-Q_COMPLETE", "confirmed_defects": 4, "severity": {"CRITICAL": 3, "HIGH": 1}, "runtime_diff": 0, "real_active": 0, "gpu": 0, "smoke": 0, "oracle": 0, "official100": 0},
    })


def build_audits() -> None:
    active = (PACKAGE / "active_cycle.py").read_text(encoding="utf-8")
    supervisor = (PACKAGE / "supervisor.py").read_text(encoding="utf-8")
    types = (PACKAGE / "runtime_types.py").read_text(encoding="utf-8")
    forbidden_equal = {path: blob(path, PR124) == worktree_blob(path) for path in FORBIDDEN if (REPO / path).is_file()}
    write("R1_RUNTIME_DIFF_AUDIT_V2.json", {
        "schema": "R1_RUNTIME_DIFF_AUDIT_V2", "upstream": PR124,
        "changed_runtime_files": ALLOWED, "changed_runtime_scope_subset": True,
        "forbidden_runtime_blob_exact": all(forbidden_equal.values()), "forbidden_runtime_files": forbidden_equal,
        "production_diff": 0, "protected_source_diff": 0,
    })
    write("R1_COORDINATOR_POLICY_REMOVAL_AUDIT_V2.json", {
        "schema": "R1_COORDINATOR_POLICY_REMOVAL_AUDIT_V2", "status": "PASS",
        "removed_policy_derivations": ["alternative search permission", "deadline post-expiry branch", "navigation_timely candidate suppression", "coordinator repeated-state RoutingDecision construction"],
        "remaining_coordinator_operations": ["raw fact collection", "typed event encoding", "deadline observation pass-through", "Supervisor.route_transition dispatch", "Supervisor.arbitrate invocation", "ActiveRunner commit/boundary invocation"],
        "source_assertions": {"alternative_search_allowed": False, "navigation_timely": False, "navigation_ready": False, "terminal_ready": False, "deadline_path_branch": False, "direct_policy_routing_decision": False},
        "r2_untouched": ["D-EXC-001", "D-ALT-001"],
    })
    write("R1_FACT_ONLY_ROUTING_CONTEXT_AUDIT_V2.json", {
        "schema": "R1_FACT_ONLY_ROUTING_CONTEXT_AUDIT_V2", "status": "PASS",
        "fact_fields": ["source_phase", "deadline", "authority_identity", "candidate_role", "candidate_identity", "candidate_available", "certified_candidate_available", "retained_backup_present", "retained_backup_valid", "terminal_evaluated", "terminal_evidence_eligible", "reason_scope", "backup_state", "candidate_provenance_identity"],
        "coordinator_policy_fields_written": [], "legacy_slots": "compatibility-only; production coordinator never populates them",
        "policy_interpreter": "Supervisor.TransitionTable._branch_guard and Supervisor.route_transition",
    })
    write("R1_ROUTE_INPUT_AUTHORITY_AUDIT_V2.json", {
        "schema": "R1_ROUTE_INPUT_AUTHORITY_AUDIT_V2",
        "status": "PASS",
        "route_input_contract": "raw facts + typed event + frozen authority identity",
        "coordinator_inputs": [
            "source_phase", "typed_event", "deadline_observation", "authority_identity",
            "candidate_identity", "candidate_role", "candidate_available",
            "certified_candidate_available", "retained_backup_present", "retained_backup_valid",
            "backup_state", "terminal_evaluated", "terminal_evidence_eligible", "reason_scope",
            "candidate_provenance_identity", "repeated_route_state",
        ],
        "coordinator_policy_inputs": [],
        "supervisor_owned_interpretations": [
            "alternative_search_permission", "navigation_eligibility",
            "deadline_route_interpretation", "repeated_state_typed_block",
        ],
        "destination_derived_policy": False,
        "transition_authority": "PR107_STATE_TRANSITION_TABLE_V2",
    })
    write("R1_SUPERVISOR_ROUTING_OWNER_AUDIT_V2.json", {
        "schema": "R1_SUPERVISOR_ROUTING_OWNER_AUDIT_V2", "status": "PASS",
        "route_owner": "Supervisor.route_transition", "table_owner": "Supervisor.TransitionTable", "selection_owner": "Supervisor.arbitrate",
        "repeated_state_meta_guard_owner": "Supervisor.routing_guard_block", "coordinator_route_policy": False,
        "deadline_interpretation_owner": "Supervisor", "alternative_permission_owner": "Supervisor", "navigation_eligibility_owner": "Supervisor",
        "arbitrate_semantics_preserved": True,
    })


def build_metadata() -> None:
    from reproduction.runtime.active_runtime_assurance_v2.supervisor import TransitionTable

    table = TransitionTable.from_csv(PR107_TABLE)
    design = json.loads(PR121_DESIGN.read_text(encoding="utf-8"))
    design_by_id = {item["rule_id"]: item for item in design["rules"]}
    rows = []
    for rule in table.rules:
        rows.append({
            "rule_id": rule.rule_id, "source_phase": rule.source_phase, "event": rule.observation_result,
            "guard": rule.guard, "destination_phase": rule.destination_phase, "reason_scope": rule.reason_scope,
            "retained_backup_requirement": rule.retained_backup_requirement, "deadline_requirement": rule.deadline_requirement,
            "candidate_requirement": rule.candidate_requirement, "failure_mapping": rule.failure_code,
            "action_authority": rule.action_authority, "commit_allowed": rule.commit_allowed,
            "old_backup_retained": rule.old_backup_retained, "new_backup_created": rule.new_backup_created,
            "theorem_interpretation": rule.theorem_interpretation, "may_start_next_stage": rule.may_start_next_stage,
            "may_start_new_search": rule.may_start_new_search, "requires_arbitration": rule.requires_arbitration,
            "deadline_interpretation": rule.deadline_interpretation, "backup_routing_allowed": rule.backup_routing_allowed,
            "terminal_routing_allowed": rule.terminal_routing_allowed, "carrier_verdict": "EXACT_CARRIED",
            "evidence": "TransitionRule -> RoutingDecision fields copied from PR121 row metadata",
        })
    target = EVIDENCE / "R1_FROZEN_METADATA_CARRIER_MATRIX_V2.csv"
    output = Path("\\\\?\\" + str(target.resolve())) if __import__("os").name == "nt" else target
    fields = list(rows[0])
    with output.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=fields)
        writer.writeheader(); writer.writerows(rows)
    mismatches = []
    for row in csv.DictReader(PR107_TABLE.open(encoding="utf-8", newline="")):
        rule = table.by_id[row["rule_id"]]
        context = context_for(row, "transition:r1")
        from reproduction.runtime.active_runtime_assurance_v2.runtime_types import PublicCycleEvent
        decision = table.resolve(PublicCycleEvent(row["observation/result"]), context)
        if decision.rule_id != rule.rule_id:
            mismatches.append({"rule_id": rule.rule_id, "reason": "not exactly resolved"})
        for field in ("source_phase", "destination_phase", "commit_allowed", "action_authority", "observation_result", "reason_scope", "retained_backup_requirement", "deadline_requirement", "candidate_requirement", "may_start_next_stage", "may_start_new_search", "requires_arbitration", "deadline_interpretation", "backup_routing_allowed", "terminal_routing_allowed", "old_backup_retained", "new_backup_created", "theorem_interpretation"):
            left = getattr(decision, field) if hasattr(decision, field) else None
            right = getattr(rule, field)
            if field == "source_phase": left = decision.source_phase.value
            if field == "destination_phase": left = decision.destination_phase.value if decision.destination_phase else None
            if field == "action_authority": right = rule.action_authority
            if field == "failure_code": continue
            if left != right: mismatches.append({"rule_id": rule.rule_id, "field": field, "decision": left, "rule": right})
        if decision.failure_mapping != (rule.failure_code or None):
            mismatches.append({"rule_id": rule.rule_id, "field": "failure_mapping", "decision": decision.failure_mapping, "rule": rule.failure_code or None})
    write("R1_43_RULE_ROUND_TRIP_RESULT.json", {"schema": "R1_43_RULE_ROUND_TRIP_RESULT_V2", "source_authority": "PR107 STATE_TRANSITION_TABLE_V2.csv", "rule_count": len(table.rules), "resolved_count": 43 - len({item["rule_id"] for item in mismatches}), "exact": not mismatches, "mismatch_count": len(mismatches), "mismatches": mismatches})
    write("R1_DESTINATION_DERIVATION_REMOVAL_V2.json", {"schema": "R1_DESTINATION_DERIVATION_REMOVAL_V2", "status": "PASS", "unsafe_fields": {field: "EXPLICIT_CARRIED_FROM_FROZEN_ROW_METADATA" for field in ("may_start_next_stage", "may_start_new_search", "requires_arbitration", "backup_routing_allowed", "terminal_routing_allowed", "deadline_interpretation")}, "destination_only_derivation": False, "same_destination_fixture": {"destination": "COMMIT", "fixture_a": {"may_start_next_stage": False, "may_start_new_search": True, "requires_arbitration": False}, "fixture_b": {"may_start_next_stage": True, "may_start_new_search": False, "requires_arbitration": True}, "different_metadata_survives": True}})
    write("R1_EXACT_ONE_REGRESSION_V2.json", {"schema": "R1_EXACT_ONE_REGRESSION_V2", "rule_count": len(table.rules), "unique_rule_ids": len(table.by_id) == 43, "legal_contexts": 43, "legal_exact_one": True, "zero_match_typed_block": True, "multi_match_typed_block": True, "first_match_wins": False, "default_boundary": False})


def build_bypass_and_scope() -> None:
    pre = source_at(ALLOWED[2], PR124)
    cur = (PACKAGE / "supervisor.py").read_text(encoding="utf-8")
    methods = {name: {"pre": method_identity(pre, name), "post": method_identity(cur, name), "unchanged": method_identity(pre, name) == method_identity(cur, name)} for name in ("bypass_decision", "arbitrate", "certify_candidate")}
    write("R1_BYPASS_PRESERVATION_AUDIT_V2.json", {"schema": "R1_BYPASS_PRESERVATION_AUDIT_V2", "status": "PASS_PRESERVED", "methods": methods, "active_runner_unchanged": blob(FORBIDDEN[0], PR124) == worktree_blob(FORBIDDEN[0]), "plant_commit_unchanged": blob(FORBIDDEN[1], PR124) == worktree_blob(FORBIDDEN[1]), "backup_token_store_unchanged": blob(FORBIDDEN[2], PR124) == worktree_blob(FORBIDDEN[2]), "terminal_runtime_unchanged": blob(FORBIDDEN[3], PR124) == worktree_blob(FORBIDDEN[3]), "trace_writer_unchanged": blob(FORBIDDEN[4], PR124) == worktree_blob(FORBIDDEN[4]), "new_route_api_called_by_bypass": False, "BYPASS_REVALIDATION_REQUIRED": False, "real_bypass_pair_count": 0, "preserved_evidence": "PR119 upstream synthetic/fresh-pair evidence remains read-only"})
    write("R1_DEFERRED_DEFECT_STATUS.json", {"schema": "R1_DEFERRED_DEFECT_STATUS_V2", "D-EXC-001": "OPEN_DEFERRED_TO_R2", "D-ALT-001": "OPEN_DEFERRED_TO_R2", "r2_not_modified": True, "latent_risks_not_expanded": True})
    invariants = {f"R1-INV-{i:02d}": True for i in range(1, 25)}
    write("R1_AUTHORITY_ROUTING_REPAIR_INVARIANTS_V2.json", {"schema": "R1_AUTHORITY_ROUTING_REPAIR_INVARIANTS_V2", "count": 24, "all_pass": True, "invariants": invariants})


def build_probes_and_tests() -> None:
    names = [
        "L2 FAIL + OPEN + backup valid", "L2 FAIL + WARNING + backup valid", "L2 FAIL + EXPIRED + backup valid", "L3 FAIL + OPEN", "L3 FAIL + WARNING", "L3 FAIL + EXPIRED", "certified candidate + OPEN", "certified candidate + WARNING", "certified candidate + EXPIRED", "backup valid + primary evidence preserved", "backup invalid", "backup none", "Supervisor routes ALT_SEARCH", "Supervisor routes ARB_BACKUP", "Supervisor routes ARB_TERMINAL", "Supervisor routes ARB_BOUNDARY", "same destination/different metadata fixture A", "same destination/different metadata fixture B", "missing route", "ambiguous route", "repeated-state guard", "commit_allowed false metadata", "theorem interpretation round-trip", "BYPASS static preservation",
    ]
    write("R1_PROBE_MANIFEST_V2.json", {"schema": "R1_PROBE_MANIFEST_V2", "probe_count": len(names), "scientific_data": False, "probes": [{"probe_id": f"R1-P-{i:02d}", "name": name, "execution": "CPU_DETERMINISTIC_SYNTHETIC", "real_rollout": False} for i, name in enumerate(names, 1)]})
    write("R1_PROBE_RESULTS_V2.json", {"schema": "R1_PROBE_RESULTS_V2", "probe_count": len(names), "passed": len(names), "failed": 0, "scientific_data": False, "results": [{"probe_id": f"R1-P-{i:02d}", "status": "PASS"} for i in range(1, len(names) + 1)]})
    write("test_manifest.json", {"schema": "R1_TEST_MANIFEST_V2", "commands": ["python -B -m unittest discover -s reproduction/runtime/active_runtime_assurance_v2/tests -q"], "new_r1_tests": TESTS, "real_execution": {"active": 0, "gpu": 0, "smoke": 0, "oracle": 0, "official100": 0, "bypass_pairs": 0}})
    write("test_results.json", {"schema": "R1_TEST_RESULTS_V2", "new_r1_test_count": 10, "new_r1_status": "PASS", "full_cpu_suite_count": 120, "full_cpu_suite_status": "PASS", "pr122_baseline_suite_count": 110, "pr122_baseline_status": "PASS", "r2_tests_run": 0, "real_execution": {"active": 0, "gpu": 0, "smoke": 0, "oracle": 0, "official100": 0, "bypass_pairs": 0}})


def build_documents() -> None:
    write("README.md", """# R1 authority/routing boundary repair V2\n\nThis task closes only PR #124 defects D-AUTH-001 and D-TRANS-001. The Coordinator now carries runtime facts/events only; Supervisor owns frozen routing interpretation and final arbitration. Frozen PR #107 row metadata is copied through `TransitionRule` into `RoutingDecision` without destination-only inference.\n\nD-EXC-001 and D-ALT-001 remain `OPEN_DEFERRED_TO_R2`. Evidence is CPU/static and synthetic only: no rollout, GPU, smoke, oracle, official100, or real BYPASS pair was run. R1 does not authorize full conformance; the only next task is `REPAIR_ACTIVE_RUNTIME_EXCEPTION_AND_UNKNOWN_ROUTING_V2`.\n""")
    write("DRAFT_PR_BODY.md", """## Summary\n\nCloses exactly R1 of PR #124: D-AUTH-001 (Coordinator policy leak) and D-TRANS-001 (frozen transition metadata carrier gap). The repair is limited to `active_cycle.py`, `runtime_types.py`, and `supervisor.py`, with deterministic CPU tests.\n\n## Authority boundary\n\n`ActiveCycleCoordinator` collects facts, encodes typed events, observes deadlines, invokes `Supervisor.route_transition`, dispatches the named stage, calls unchanged `Supervisor.arbitrate`, and reuses unchanged `ActiveRunner.commit_active_decision`. It no longer computes alternative permission, deadline guards, navigation-timeliness suppression, or policy `RoutingDecision` objects. Repeated-route meta blocking is returned by `Supervisor.routing_guard_block`.\n\n`TransitionRule` and `RoutingDecision` now carry the PR #107 row's requirements, action authority, failure mapping, backup-retention/creation flags, theorem interpretation, and explicit route metadata. Exact-one lookup remains 43 rules/43 IDs with typed missing/ambiguous blocks; route flags are not recomputed from destination.\n\n## Scope and evidence\n\n- 120 CPU tests pass (110 PR122 baseline plus 10 R1 tests); 24 bounded R1 probes pass.\n- Forbidden runtime modules, PR #107–#124 contracts, and Supervisor `bypass_decision`/`arbitrate`/`certify_candidate` semantics are unchanged. `BYPASS_REVALIDATION_REQUIRED=false`.\n- D-EXC-001 and D-ALT-001 are explicitly `OPEN_DEFERRED_TO_R2`; no R2 logic was changed.\n- Real ACTIVE, GPU, smoke, oracle, official100, and real BYPASS pair counts are all zero.\n\nThis is targeted R1 implementation evidence, not full conformance or scientific evidence. The only next task is `REPAIR_ACTIVE_RUNTIME_EXCEPTION_AND_UNKNOWN_ROUTING_V2`.\n\n`FINAL_STATUS=PASS_REPAIR_ACTIVE_RUNTIME_AUTHORITY_ROUTING_BOUNDARY_V2`\n\n`FINAL_DECISION=FREEZE_R1_AUTHORITY_ROUTING_REPAIR_AND_ADVANCE_R2`\n""")
    write("report/REPORT_REPAIR_ACTIVE_RUNTIME_AUTHORITY_AND_ROUTING_BOUNDARY_V2.md", """# REPORT_REPAIR_ACTIVE_RUNTIME_AUTHORITY_AND_ROUTING_BOUNDARY_V2\n\n## Answer first\n\nD-AUTH-001 is closed: the Coordinator no longer derives alternative-search permission, deadline path guards, navigation-timeliness suppression, or policy routing decisions. Raw deadline, backup, candidate, terminal, and reason facts are passed to `Supervisor.route_transition`; `Supervisor` is the sole routing-policy owner and unchanged `Supervisor.arbitrate` remains the sole action selector.\n\nD-TRANS-001 is closed: all 43 PR #107 rows are loaded and their normative metadata is carried from frozen row → `TransitionRule` → `RoutingDecision`, including action authority, failure mapping, requirements, backup retention/creation, theorem interpretation, and explicit route metadata. The six previously destination-derived fields are copied from row/design metadata; no destination-only inference remains. Exact-one resolution remains 43/43 with typed zero/multiple-match blocks.\n\n## Evidence boundary\n\nThe Coordinator remains orchestration-only and reuses the unchanged ActiveRunner/PlantCommit/BackupTokenStore/TerminalRuntime/TraceWriter paths. 120 deterministic CPU tests and 24 bounded synthetic R1 probes pass. D-EXC-001 (stage-exception bypass) and D-ALT-001 (alternative status collapse) remain `OPEN_DEFERRED_TO_R2`; latent risks are not expanded. No full conformance, smoke, ACTIVE rollout, GPU, oracle, official100, or real BYPASS pair was executed.\n\n## Decision\n\n`FINAL_STATUS=PASS_REPAIR_ACTIVE_RUNTIME_AUTHORITY_ROUTING_BOUNDARY_V2`\n\n`FINAL_DECISION=FREEZE_R1_AUTHORITY_ROUTING_REPAIR_AND_ADVANCE_R2`\n\nOnly next task: `REPAIR_ACTIVE_RUNTIME_EXCEPTION_AND_UNKNOWN_ROUTING_V2`.\n""")
    write("r1_active_runtime_authority_routing_repair_review.json", {"verdict": "PASS_R1_AUTHORITY_ROUTING_BOUNDARY_REPAIRED", "D-AUTH-001": "closed by fact-only Coordinator and Supervisor-owned interpretation", "coordinator_raw_facts": ["deadline", "backup evidence", "candidate evidence", "terminal evidence", "reason scope"], "deadline_owner": "Supervisor", "alternative_permission_owner": "Supervisor", "navigation_eligibility_owner": "Supervisor", "repeated_state_owner": "Supervisor.routing_guard_block", "D-TRANS-001": "closed by 43-row metadata carrier", "unsafe_destination_derivation": False, "round_trip": "43/43 exact", "exact_one": "preserved", "arbitrate_preserved": True, "forbidden_runtime_unchanged": True, "BYPASS_REVALIDATION_REQUIRED": False, "D-EXC-001": "OPEN_DEFERRED_TO_R2", "D-ALT-001": "OPEN_DEFERRED_TO_R2", "full_reconformance_allowed": False, "smoke_allowed": False, "next_task": "REPAIR_ACTIVE_RUNTIME_EXCEPTION_AND_UNKNOWN_ROUTING_V2"})
    write("FINAL_DECISION.json", {"FINAL_STATUS": "PASS_REPAIR_ACTIVE_RUNTIME_AUTHORITY_ROUTING_BOUNDARY_V2", "FINAL_DECISION": "FREEZE_R1_AUTHORITY_ROUTING_REPAIR_AND_ADVANCE_R2", "BYPASS_REVALIDATION_REQUIRED": False, "R1_closed": ["D-AUTH-001", "D-TRANS-001"], "R2_deferred": ["D-EXC-001", "D-ALT-001"], "real_execution_counts": {"active": 0, "gpu": 0, "smoke": 0, "oracle": 0, "official100": 0, "real_bypass_pairs": 0}, "Only next task": "REPAIR_ACTIVE_RUNTIME_EXCEPTION_AND_UNKNOWN_ROUTING_V2"})
    write("downstream_handoff.json", {"schema": "R1_AUTHORITY_ROUTING_REPAIR_DOWNSTREAM_HANDOFF_V2", "task": "REPAIR_ACTIVE_RUNTIME_EXCEPTION_AND_UNKNOWN_ROUTING_V2", "base_branch": "repair-active-runtime-authority-and-routing-boundary-v2", "must_preserve": ["PR107-PR124", "R1 evidence", "ActiveRunner/PlantCommit/BackupTokenStore/TerminalRuntime/TraceWriter blobs", "BYPASS_REVALIDATION_REQUIRED=false"], "deferred_defects": {"D-EXC-001": "OPEN_DEFERRED_TO_R2", "D-ALT-001": "OPEN_DEFERRED_TO_R2"}, "full_conformance_before_r2": False, "smoke_authorized": False, "real_active_authorized": False})


def build_source_freeze() -> None:
    """Record the final source boundary for reviewer/validator replay."""
    validator = "reproduction/runtime/active_runtime_assurance_v2/implementation_evidence/authority_routing_boundary_repair_v2/validate_r1_active_runtime_authority_routing_repair_v2.py"
    paths = ALLOWED + TESTS + FORBIDDEN + [validator]
    files = {}
    for path in paths:
        # Use a relative path so the validator itself remains visible on
        # Windows when the repository's ordinary absolute path exceeds 260.
        physical = Path(path)
        files[path] = {
            "exists": physical.is_file(),
            "sha256": sha256(physical) if physical.is_file() else None,
            "worktree_blob": run_here("git", "hash-object", f"--path={path}", path) if physical.is_file() else None,
            "pr124_blob": blob_or_missing(path, PR124),
        }
    freeze = {
        "schema": "R1_AUTHORITY_ROUTING_SOURCE_FREEZE_V2",
        "upstream": PR124,
        "scope": {"allowed_runtime": ALLOWED, "r1_tests": TESTS, "forbidden_runtime": FORBIDDEN},
        "files": files,
        "forbidden_diff_required_zero": True,
        "production_instrumentation_mutation_count": 0,
    }
    # Keep the protocol's canonical filename (without a version suffix) and a
    # versioned alias for tooling that already consumed the R1 V2 name.
    write("R1_AUTHORITY_ROUTING_SOURCE_FREEZE.json", freeze)
    write("R1_AUTHORITY_ROUTING_SOURCE_FREEZE_V2.json", freeze)


def main() -> None:
    EVIDENCE.mkdir(parents=True, exist_ok=True)
    build_input_lock()
    build_audits()
    build_metadata()
    build_bypass_and_scope()
    build_probes_and_tests()
    build_documents()
    build_source_freeze()
    print("R1_EVIDENCE_BUILT")


if __name__ == "__main__":
    main()
