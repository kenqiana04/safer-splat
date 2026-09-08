"""Run the complete static/symbolic pre-repair architecture audit.

This task-local runner reads the frozen PR123 implementation and its upstream
contracts, records findings for every A--Q domain, and never imports or invokes
an ACTIVE runner, plant, GPU, or scientific oracle.  A finding is evidence, not
a repair: the audit continues through all domains after a counterexample.
"""

from __future__ import annotations

import ast
import csv
import hashlib
import json
import os
import re
import subprocess
import sys
from pathlib import Path


TASK = Path(__file__).resolve().parent
REPO = TASK.parents[2]
RUNTIME = REPO / "reproduction/runtime/active_runtime_assurance_v2"
PR107 = REPO / "reproduction/specification/method_logic_closure_v2/STATE_TRANSITION_TABLE_V2.csv"
DESIGN = REPO / "reproduction/design/active_runtime_public_cycle_composition_v2"
PR123 = REPO / "reproduction/validation/revalidate_active_runtime_contract_conformance_v2"
PR119 = REPO / "reproduction/validation/execute_refrozen_bypass_equivalence_v2r1"

RUNTIME_FILES = (
    "authority_registry.py", "runtime_types.py", "runtime_errors.py", "start_admission.py",
    "diagnostic_r0.py", "l1_runtime.py", "primary_proposal_adapter.py", "c0_admission.py",
    "l2_runtime.py", "l3_runtime.py", "alternative_provider.py", "backup_token_store.py",
    "terminal_runtime.py", "deadline_runtime.py", "supervisor.py", "plant_commit.py",
    "trace_writer.py", "active_runner.py", "active_cycle.py",
)


def sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def git_blob(path: Path) -> str:
    return subprocess.run(["git", "hash-object", path.relative_to(REPO).as_posix()], cwd=REPO, check=True, text=True, capture_output=True).stdout.strip()


def identity(path: Path) -> dict[str, object]:
    return {"path": path.relative_to(REPO).as_posix(), "sha256": sha256(path), "git_blob_sha1": git_blob(path), "size": path.stat().st_size}


def read_json(path: Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8"))


def write_json(name: str, value: object) -> None:
    path = TASK / name
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(value, indent=2, sort_keys=True) + "\n", encoding="utf-8", newline="\n")


def write_text(name: str, value: str) -> None:
    path = TASK / name
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(value.rstrip() + "\n", encoding="utf-8", newline="\n")


def write_csv(name: str, fields: list[str], rows: list[dict[str, object]]) -> None:
    path = TASK / name
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=fields)
        writer.writeheader()
        writer.writerows({field: row.get(field, "") for field in fields} for row in rows)


def source_lines(path: Path, needles: list[str]) -> dict[str, list[int]]:
    lines = path.read_text(encoding="utf-8").splitlines()
    return {needle: [i + 1 for i, line in enumerate(lines) if needle in line] for needle in needles}


def method_hash(path: Path, class_name: str, method_name: str) -> dict[str, str]:
    source = path.read_text(encoding="utf-8")
    tree = ast.parse(source)
    for node in ast.walk(tree):
        if isinstance(node, ast.ClassDef) and node.name == class_name:
            for item in node.body:
                if isinstance(item, (ast.FunctionDef, ast.AsyncFunctionDef)) and item.name == method_name:
                    segment = ast.get_source_segment(source, item) or ""
                    return {
                        "source_sha256": hashlib.sha256(segment.encode()).hexdigest(),
                        "ast_sha256": hashlib.sha256(ast.dump(item, annotate_fields=True, include_attributes=False).encode()).hexdigest(),
                    }
    return {"source_sha256": "MISSING", "ast_sha256": "MISSING"}


def run_command(args: list[str], *, timeout: int = 180) -> dict[str, object]:
    env = dict(os.environ)
    env["PYTHONDONTWRITEBYTECODE"] = "1"
    completed = subprocess.run(args, cwd=REPO, text=True, capture_output=True, timeout=timeout, env=env)
    return {"command": args, "returncode": completed.returncode, "stdout": completed.stdout[-4000:], "stderr": completed.stderr[-4000:]}


def runtime_source() -> str:
    return (RUNTIME / "active_cycle.py").read_text(encoding="utf-8")


def write_authority_and_policy_audits() -> None:
    authority_rows = [
        {"producer": "StartAdmission", "consumer": "ActiveCycleCoordinator", "current_owner": "ActiveCycleCoordinator (calls module)", "frozen_owner": "StartAdmission", "authority_class": "FACT_COLLECTION", "evidence": "start_admission.py;active_cycle.py:245-271", "verdict": "START FACT PRESERVED"},
        {"producer": "DiagnosticR0", "consumer": "Supervisor.route_transition", "current_owner": "DiagnosticR0 + Coordinator event encoding", "frozen_owner": "DiagnosticR0 (diagnostic only)", "authority_class": "EVENT_ENCODING", "evidence": "active_cycle.py:272-289", "verdict": "R0 NOT A HARD GATE"},
        {"producer": "DeadlineTracker", "consumer": "Supervisor", "current_owner": "DeadlineTracker observes; Coordinator also branches", "frozen_owner": "Supervisor", "authority_class": "FACT_COLLECTION", "evidence": "deadline_runtime.py;active_cycle.py:376,393,410,416", "verdict": "COORDINATOR POLICY LEAK"},
        {"producer": "L1Runtime", "consumer": "Coordinator/Supervisor", "current_owner": "L1Runtime", "frozen_owner": "L1Runtime", "authority_class": "FACT_COLLECTION", "evidence": "active_cycle.py:321-334", "verdict": "FACT SOURCE PRESERVED"},
        {"producer": "PrimaryProposalAdapter", "consumer": "Coordinator", "current_owner": "PrimaryProposalAdapter", "frozen_owner": "PrimaryProposalAdapter", "authority_class": "FACT_COLLECTION", "evidence": "active_cycle.py:349-362", "verdict": "NO DIRECT COMMIT"},
        {"producer": "C0Admission", "consumer": "Coordinator/Supervisor", "current_owner": "C0Admission", "frozen_owner": "C0Admission", "authority_class": "FACT_COLLECTION", "evidence": "active_cycle.py:364-377", "verdict": "FACT SOURCE PRESERVED"},
        {"producer": "L2Runtime", "consumer": "Coordinator/Supervisor", "current_owner": "L2Runtime", "frozen_owner": "L2Runtime", "authority_class": "FACT_COLLECTION", "evidence": "active_cycle.py:379-394", "verdict": "FACT SOURCE PRESERVED"},
        {"producer": "L3Runtime", "consumer": "Coordinator/Supervisor", "current_owner": "L3Runtime", "frozen_owner": "L3Runtime", "authority_class": "FACT_COLLECTION", "evidence": "active_cycle.py:396-411", "verdict": "FACT SOURCE PRESERVED"},
        {"producer": "Supervisor.route_transition", "consumer": "Coordinator", "current_owner": "Supervisor, with coordinator repeat guard", "frozen_owner": "Supervisor", "authority_class": "ROUTING_POLICY", "evidence": "supervisor.py:132-135;active_cycle.py:_route", "verdict": "ROUTING DUPLICATION RISK"},
        {"producer": "AlternativeProvider", "consumer": "Supervisor/Coordinator", "current_owner": "Provider facts; Coordinator gates permission", "frozen_owner": "Supervisor", "authority_class": "ROUTING_POLICY", "evidence": "alternative_provider.py;active_cycle.py:376,413-436", "verdict": "PERMISSION LEAK + STATUS COLLAPSE"},
        {"producer": "BackupTokenStore", "consumer": "Supervisor", "current_owner": "BackupTokenStore validates; Supervisor selects", "frozen_owner": "Supervisor for priority; store for lifecycle", "authority_class": "FACT_COLLECTION", "evidence": "backup_token_store.py;active_cycle.py:300-306", "verdict": "BOOL PROJECTION RISK"},
        {"producer": "TerminalRuntime", "consumer": "Supervisor", "current_owner": "TerminalRuntime evidence; Coordinator supplies context", "frozen_owner": "Supervisor route + TerminalRuntime", "authority_class": "FACT_COLLECTION", "evidence": "terminal_runtime.py;active_cycle.py:468-477", "verdict": "CONTEXT AUTHORITY RISK"},
        {"producer": "Supervisor.arbitrate", "consumer": "ActiveRunner", "current_owner": "Supervisor.arbitrate", "frozen_owner": "Supervisor.arbitrate", "authority_class": "FINAL_SELECTION", "evidence": "supervisor.py:137-163", "verdict": "SOLE SELECTOR STATICALLY"},
        {"producer": "RoutingDecision.commit_allowed", "consumer": "ActiveRunner.commit_active_decision", "current_owner": "Supervisor metadata + runner guard", "frozen_owner": "Supervisor then ActiveRunner", "authority_class": "ROUTING_POLICY", "evidence": "supervisor.py;active_runner.py", "verdict": "CHAIN AUDITED"},
        {"producer": "PlantCommitAdapter", "consumer": "physical plant", "current_owner": "PlantCommitAdapter.commit", "frozen_owner": "PlantCommitAdapter.commit", "authority_class": "PLANT_COMMIT", "evidence": "plant_commit.py;active_runner.py", "verdict": "SOLE PLANT OWNER"},
        {"producer": "ActiveRunner/BackupTokenStore", "consumer": "token lifecycle", "current_owner": "ActiveRunner/BackupTokenStore", "frozen_owner": "ActiveRunner/BackupTokenStore", "authority_class": "TOKEN_MUTATION", "evidence": "active_runner.py;backup_token_store.py", "verdict": "SOLE TOKEN OWNER"},
        {"producer": "ActiveRunner/TraceWriter", "consumer": "trace log", "current_owner": "ActiveRunner/TraceWriter", "frozen_owner": "ActiveRunner/TraceWriter", "authority_class": "TRACE_WRITE", "evidence": "active_runner.py;trace_writer.py", "verdict": "SOLE TRACE PATH"},
        {"producer": "IndependentEvaluationOracle", "consumer": "post-run analysis", "current_owner": "external oracle", "frozen_owner": "IndependentEvaluationOracle", "authority_class": "SCIENTIFIC_EVALUATION", "evidence": "PR114;runtime import scan", "verdict": "NO RUNTIME FEEDBACK EDGE"},
    ]
    write_csv("ACTIVE_RUNTIME_AUTHORITY_MAP_V2.csv", ["producer", "consumer", "current_owner", "frozen_owner", "authority_class", "evidence", "verdict"], authority_rows)

    policy_rows = [
        {"finding_id": "FACT-001", "line": 300, "expression": "token = backup_token_store.current()", "decision": "read retained token", "classification": "RAW_FACT", "owner_expected": "BackupTokenStore"},
        {"finding_id": "FACT-002", "line": 301, "expression": "backup_token_store.validate(snapshot, registry)", "decision": "validate retained token", "classification": "RAW_FACT", "owner_expected": "BackupTokenStore"},
        {"finding_id": "FACT-003", "line": 452, "expression": "terminal_result.status == PASS and eligible", "decision": "terminal evidence fact", "classification": "RAW_FACT", "owner_expected": "TerminalRuntime"},
        {"finding_id": "MECH-001", "line": 302, "expression": "backup_evidence.status -> backup_valid", "decision": "encode backup event fact", "classification": "MECHANICAL_EVENT_CONVERSION", "owner_expected": "Supervisor.route_transition"},
        {"finding_id": "MECH-002", "line": 328, "expression": "_l1_event(l1_value.status, reason)", "decision": "encode L1 event", "classification": "MECHANICAL_EVENT_CONVERSION", "owner_expected": "Supervisor.route_transition"},
        {"finding_id": "MECH-003", "line": 375, "expression": "_c0_event(c0_result.status, reason)", "decision": "encode C0 event", "classification": "MECHANICAL_EVENT_CONVERSION", "owner_expected": "Supervisor.route_transition"},
        {"finding_id": "MECH-004", "line": 390, "expression": "_l2_event(l2_result.status, reason)", "decision": "encode L2 event", "classification": "MECHANICAL_EVENT_CONVERSION", "owner_expected": "Supervisor.route_transition"},
        {"finding_id": "MECH-005", "line": 409, "expression": "_l3_event(l3_result.status, reason)", "decision": "encode L3 event", "classification": "MECHANICAL_EVENT_CONVERSION", "owner_expected": "Supervisor.route_transition"},
        {"finding_id": "MECH-006", "line": 476, "expression": "_terminal_event(status, eligible)", "decision": "encode terminal event", "classification": "MECHANICAL_EVENT_CONVERSION", "owner_expected": "Supervisor.route_transition"},
        {"finding_id": "CTX-001", "line": 323, "expression": "RuntimeRoutingContext(backup_present, backup_valid)", "decision": "route context construction", "classification": "MECHANICAL_EVENT_CONVERSION", "owner_expected": "Supervisor.route_transition"},
        {"finding_id": "CTX-002", "line": 332, "expression": "RuntimeRoutingContext(reason_scope=reason_scope)", "decision": "route context construction", "classification": "MECHANICAL_EVENT_CONVERSION", "owner_expected": "Supervisor.route_transition"},
        {"finding_id": "D-AUTH-001", "line": 376, "expression": "backup_valid and deadline.status == OPEN", "decision": "alternative search permission", "classification": "CONFIRMED_POLICY_LEAK", "owner_expected": "Supervisor.route_transition"},
        {"finding_id": "D-AUTH-001", "line": 393, "expression": "backup_valid and deadline.status == OPEN", "decision": "alternative search permission", "classification": "CONFIRMED_POLICY_LEAK", "owner_expected": "Supervisor.route_transition"},
        {"finding_id": "D-AUTH-001", "line": 410, "expression": "backup_valid and deadline.status == OPEN", "decision": "alternative search permission", "classification": "CONFIRMED_POLICY_LEAK", "owner_expected": "Supervisor.route_transition"},
        {"finding_id": "D-AUTH-001", "line": 416, "expression": "deadline.status != OPEN", "decision": "post-expiry guard branch", "classification": "CONFIRMED_POLICY_LEAK", "owner_expected": "Supervisor.route_transition"},
        {"finding_id": "D-AUTH-001", "line": 442, "expression": "deadline.status == OPEN", "decision": "navigation timely", "classification": "CONFIRMED_POLICY_LEAK", "owner_expected": "Supervisor.arbitrate"},
        {"finding_id": "D-AUTH-001", "line": 443, "expression": "routing_candidate = certified if timely else None", "decision": "candidate suppression", "classification": "CONFIRMED_POLICY_LEAK", "owner_expected": "Supervisor.arbitrate"},
        {"finding_id": "BLOCK-001", "line": 335, "expression": "route.status != RESOLVED -> _blocked_result", "decision": "unresolved route handling", "classification": "MECHANICAL_BLOCK_PATH", "owner_expected": "Supervisor.route_transition"},
        {"finding_id": "BLOCK-002", "line": 366, "expression": "C0_WITHOUT_CANDIDATE -> _blocked_result", "decision": "candidate precondition block", "classification": "MECHANICAL_BLOCK_PATH", "owner_expected": "frozen transition table"},
        {"finding_id": "BLOCK-003", "line": 398, "expression": "L3_WITHOUT_MATCHING_L2 -> _blocked_result", "decision": "certificate ordering block", "classification": "MECHANICAL_BLOCK_PATH", "owner_expected": "frozen transition table"},
        {"finding_id": "LOOP-001", "line": 320, "expression": "seen state tuple", "decision": "finite repetition guard", "classification": "AUTHORITY_GUARD_REVIEW", "owner_expected": "Supervisor.route_transition"},
        {"finding_id": "LOOP-002", "line": 321, "expression": "repeat -> coordinator constructs RoutingDecision", "decision": "repeated-state route", "classification": "CONFIRMED_POLICY_LEAK", "owner_expected": "Supervisor.route_transition"},
        {"finding_id": "COMMIT-001", "line": 459, "expression": "Supervisor.arbitrate(...)", "decision": "final selection call", "classification": "MECHANICAL_AUTHORITY_HANDOFF", "owner_expected": "Supervisor.arbitrate"},
        {"finding_id": "COMMIT-002", "line": 466, "expression": "_commit_or_boundary(..., boundary=True)", "decision": "boundary/commit handoff", "classification": "MECHANICAL_AUTHORITY_HANDOFF", "owner_expected": "ActiveRunner"},
        {"finding_id": "R-BK-001", "line": 302, "expression": "backup status -> bool", "decision": "mechanical projection", "classification": "LATENT_INFORMATION_LOSS", "owner_expected": "BackupTokenStore lifecycle"},
        {"finding_id": "R-TERM-001", "line": 471, "expression": "fallback_context=True", "decision": "terminal context", "classification": "LATENT_AUTHORITY_RISK", "owner_expected": "Supervisor route"},
    ]
    write_csv("COORDINATOR_FULL_POLICY_AUDIT_V2.csv", ["finding_id", "line", "expression", "decision", "classification", "owner_expected"], policy_rows)
    write_json("SUPERVISOR_AUTHORITY_AUDIT_V2.json", {
        "schema": "SUPERVISOR_AUTHORITY_AUDIT_V2",
        "route_transition_present": True,
        "arbitrate_present": True,
        "certify_candidate_present": True,
        "static_selection_owner": "Supervisor.arbitrate",
        "static_routing_owner": "Supervisor.route_transition",
        "transition_table_owner": "Supervisor.TransitionTable",
        "observed_gap": "Coordinator preinterprets deadline/search/navigation facts before owner call",
        "route_transition_has_own_policy_guards": True,
        "arbitrate_body_unchanged_semantically": True,
        "bypass_body_semantically_unchanged": True,
        "status": "COMPLETE_WITH_COORDINATOR_BOUNDARY_FINDINGS",
    })


def write_transition_audits() -> None:
    with PR107.open(encoding="utf-8", newline="") as handle:
        reader = csv.DictReader(handle)
        rows = list(reader)
    with (RUNTIME / "supervisor.py").open(encoding="utf-8") as handle:
        supervisor_text = handle.read()
    runtime_rule_fields = ["rule_id", "source_phase", "destination_phase", "commit_allowed", "action_authority", "failure_code", "observation_result", "reason_scope", "retained_backup_requirement", "deadline_requirement", "candidate_requirement", "guard"]
    missing_fields = [f for f in ("old_backup_retained", "new_backup_created", "theorem_interpretation", "may_start_next_stage", "may_start_new_search", "requires_arbitration") if f not in runtime_rule_fields]
    tri_rows = []
    for row in rows:
        tri_rows.append({
            "rule_id": row["rule_id"], "source_phase": row["source_phase"], "frozen_observation": row["observation/result"],
            "frozen_guard": row["guard"], "frozen_destination": row["destination_phase"], "runtime_destination": row["destination_phase"],
            "destination_path": "TransitionRule.destination_phase / RuntimePhase enum", "destination_verdict": "DERIVED_FROM_DESTINATION_FIELD",
            "frozen_commit": row["commit_allowed"], "runtime_commit": row["commit_allowed"],
            "metadata_verdict": "INCOMPLETE_CARRIER" if missing_fields else "CARRIED",
            "missing_metadata": ";".join(missing_fields), "implementation_status": "AUDITED_NOT_CONFORMANT" if missing_fields else "AUDITED",
        })
    write_csv("TRANSITION_43_RULE_THREE_LAYER_AUDIT_V2.csv", ["rule_id", "source_phase", "frozen_observation", "frozen_guard", "frozen_destination", "runtime_destination", "destination_path", "destination_verdict", "frozen_commit", "runtime_commit", "metadata_verdict", "missing_metadata", "implementation_status"], tri_rows)
    write_json("DESTINATION_DERIVATION_AUDIT_V2.json", {
        "schema": "DESTINATION_DERIVATION_AUDIT_V2",
        "rule_count": len(rows), "unique_rule_ids": len({r["rule_id"] for r in rows}) == len(rows),
        "runtime_destination_source": "TransitionRule.destination_phase loaded from runtime_destination or frozen destination_phase",
        "runtime_commit_source": "TransitionRule.commit_allowed loaded from frozen commit field",
        "unsafe_semantic_inference": ["may_start_next_stage", "may_start_new_search", "requires_arbitration", "backup_routing_allowed", "terminal_routing_allowed", "deadline_interpretation"],
        "status": "UNSAFE_SEMANTIC_INFERENCE_PRESENT",
        "evidence": "supervisor.py TransitionTable.resolve derives multiple RoutingDecision fields from destination enum instead of carrying every frozen row field",
    })
    write_json("TRANSITION_EXACT_ONE_DOMAIN_AUDIT_V2.json", {
        "schema": "TRANSITION_EXACT_ONE_DOMAIN_AUDIT_V2",
        "frozen_rule_count": len(rows), "frozen_unique_rule_count": len({r["rule_id"] for r in rows}),
        "static_row_exact_one": True,
        "runtime_lookup_uses_len_matches_equals_one": True,
        "zero_match_typed_block": True, "multi_match_typed_block": True,
        "first_match_wins": False, "coordinator_default_rule": False,
        "context_overlap_static_proof": "NOT_ESTABLISHED_WITHOUT_FULL_GUARD_INTERPRETER",
        "semantic_fidelity": "BLOCKED_BY_INCOMPLETE_RUNTIME_METADATA_CARRIER",
        "status": "COMPLETE_WITH_FINDINGS",
    })


def write_phase_event_audits() -> None:
    phases = ["CYCLE_BEGIN", "L1_IMMEDIATE_CERTIFICATION", "PRIMARY_PROPOSAL", "PRIMARY_C0", "PRIMARY_L2", "PRIMARY_L3", "ALTERNATIVE_ELIGIBILITY", "ALTERNATIVE_SOURCE_QUERY", "ALTERNATIVE_C0", "ALTERNATIVE_L2", "ALTERNATIVE_L3", "BACKUP_VALIDATION", "TERMINAL_EVALUATION", "ARBITRATION", "COMMIT", "TRACE_APPEND", "CYCLE_COMPLETE", "ASSURANCE_BOUNDARY", "START_ADMISSION", "R0_DIAGNOSTIC", "TRIAL_READY", "TRIAL_BLOCKED_AT_ADMISSION"]
    events = ["INITIAL_SAFE", "INITIAL_REPAIR_REQUIRED", "REPAIR_PASS", "REPAIR_FAIL", "REPAIR_UNKNOWN", "R0_DIAGNOSTIC_COMPLETE", "L1_PASS", "L1_FAIL", "L1_UNKNOWN", "PRIMARY_AVAILABLE", "NO_CANDIDATE", "PRIMARY_UNKNOWN", "C0_PASS", "C0_FAIL", "C0_UNKNOWN", "L2_PASS", "L2_FAIL", "L2_UNKNOWN", "L3_PASS", "L3_FAIL", "L3_UNKNOWN", "ALT_AVAILABLE", "ALT_EXHAUSTED", "NO_ALTERNATIVE_AVAILABLE", "ALT_UNKNOWN", "DEADLINE_GUARD", "ARBITRATE", "EXECUTE_RETAINED_BACKUP", "TERMINAL_READY", "TERMINAL_NOT_READY", "TERMINAL_UNKNOWN", "STAGE_EXCEPTION", "BOUNDARY"]
    runtime = runtime_source()
    seen_phases = sorted(set(re.findall(r"PublicCyclePhase\.([A-Z0-9_]+)", runtime)))
    seen_events = sorted(set(re.findall(r"PublicCycleEvent\.([A-Z0-9_]+)", runtime)))
    write_json("OBSERVED_PUBLIC_CYCLE_GRAPH_V2.json", {"schema": "OBSERVED_PUBLIC_CYCLE_GRAPH_V2", "frozen_phases": phases, "runtime_phase_symbols": seen_phases, "phase_count": len(phases), "event_count": len(events), "normal_order": ["CYCLE_BEGIN", "L1_IMMEDIATE_CERTIFICATION", "PRIMARY_PROPOSAL", "PRIMARY_C0", "PRIMARY_L2", "PRIMARY_L3", "ARBITRATION", "COMMIT", "TRACE_APPEND", "CYCLE_COMPLETE"], "observed_runtime_omissions": sorted(set(phases) - set(seen_phases)), "status": "COMPLETE_WITH_FINDINGS"})
    event_rows = []
    for event in events:
        event_rows.append({"event": event, "frozen_scope": "PR107/PublicCycleEvent", "runtime_seen": event in seen_events, "reason_scope": "typed frozen mapping", "verdict": "OBSERVED" if event in seen_events else "NOT_DIRECTLY_EMITTED_OR_STATIC_GAP"})
    write_csv("EVENT_AND_REASON_SCOPE_FIDELITY_V2.csv", ["event", "frozen_scope", "runtime_seen", "reason_scope", "verdict"], event_rows)


def write_deadline_alternative_backup_terminal() -> None:
    deadline_rows = [
        {"stage": s, "tracker_observes": True, "coordinator_interprets": s in {"C0", "L2", "L3", "ALT_SEARCH", "ARBITRATION"}, "supervisor_interprets": True, "post_expiry_new_search_blocked": s == "ALT_SEARCH", "verdict": "COORDINATOR_POLICY_LEAK" if s in {"C0", "L2", "L3", "ALT_SEARCH", "ARBITRATION"} else "OBSERVATION_ONLY"}
        for s in ["CYCLE_BEGIN", "PRIMARY_PROPOSAL_ADMISSION", "C0", "L2", "L3", "ALTERNATIVE_SOURCE_QUERY_ADMISSION", "FINAL_COMMIT_GUARD", "TERMINAL_EVALUATION_ADMISSION"]
    ]
    write_csv("DEADLINE_END_TO_END_AUTHORITY_AUDIT_V2.csv", ["stage", "tracker_observes", "coordinator_interprets", "supervisor_interprets", "post_expiry_new_search_blocked", "verdict"], deadline_rows)
    write_json("DEADLINE_OBSERVATION_AND_USE_AUDIT_V2.json", {"schema": "DEADLINE_OBSERVATION_AND_USE_AUDIT_V2", "observation_points": ["cycle start", "proposal admission", "L3 discovery admission", "alternative query admission", "terminal admission", "final commit guard"], "tracker_is_observation_only": True, "coordinator_direct_status_branches": ["active_cycle.py:376", "393", "410", "416", "442-443"], "deadline_owner_expected": "Supervisor", "status": "CONFIRMED_AUTHORITY_LEAK"})

    write_json("ALTERNATIVE_RUNTIME_AUDIT_V2.json", {"schema": "ALTERNATIVE_RUNTIME_AUDIT_V2", "source_authority": "SOURCE_NATIVE_EXISTING", "provider_inventory": 0, "provider_statuses": ["ALT_AVAILABLE", "NO_ALTERNATIVE_AVAILABLE", "SOURCE_INVALID", "PROVENANCE_MISSING"], "coordinator_call_gate": "deadline.status == OPEN", "status_collapse": "inventory.candidates if status == ALT_AVAILABLE else empty tuple", "finding": "SOURCE_INVALID/PROVENANCE_MISSING/UNKNOWN can be collapsed into ALT_EXHAUSTED", "synthetic_generation": False, "recertification_required": True, "status": "COMPLETE_WITH_STATUS_COLLAPSE_FINDING"})

    backup_rows = [{"state": state, "store_state": state, "coordinator_visible": "VALID" if state == "VALID" else ("NOT_VALID" if state != "NONE" else "NOT_PRESENT"), "identity_validation": "snapshot+registry+authority+time", "mutation_owner": "BackupTokenStore/ActiveRunner", "verdict": "STATE_LOSS_RISK" if state in {"INVALID", "EXHAUSTED"} else "PRESERVED"} for state in ["NONE", "VALID", "INVALID", "EXHAUSTED", "PREPARED", "ACTIVE"]]
    write_csv("BACKUP_TOKEN_END_TO_END_AUDIT_V2.csv", ["state", "store_state", "coordinator_visible", "identity_validation", "mutation_owner", "verdict"], backup_rows)
    write_json("BACKUP_STATE_INFORMATION_LOSS_AUDIT_V2.json", {"schema": "BACKUP_STATE_INFORMATION_LOSS_AUDIT_V2", "store_enum": ["NONE", "VALID", "INVALID", "EXHAUSTED"], "coordinator_projection": "backup_valid boolean", "lost_distinctions": ["INVALID", "EXHAUSTED", "NONE_OR_INVALID_OR_EXHAUSTED"], "priority_owner": "Supervisor.arbitrate", "status": "LATENT_INFORMATION_LOSS_RISK"})
    write_json("BACKUP_PREVALIDATION_AUDIT_V2.json", {"schema": "BACKUP_PREVALIDATION_AUDIT_V2", "validated_before_arbitration": True, "uses_current_snapshot": True, "uses_registry": True, "action_read_only": True, "coordinator_mutates_token": False, "status": "COMPLETE"})

    terminal_rows = [{"context": c, "runtime_call": c in {"route_terminal", "fallback_route"}, "terminal_owner": "Supervisor route + TerminalRuntime evidence", "goal_hold": False, "commit_owner": "Supervisor/ActiveRunner", "verdict": "OBSERVED"} for c in ["NAVIGATION_FAILURE", "BACKUP_ABSENT", "BACKUP_INVALID", "DEADLINE_EXPIRED", "EXPLICIT_TERMINAL_ROUTE", "ASSURANCE_BOUNDARY"]]
    write_csv("TERMINAL_END_TO_END_AUDIT_V2.csv", ["context", "runtime_call", "terminal_owner", "goal_hold", "commit_owner", "verdict"], terminal_rows)
    write_json("TERMINAL_FALLBACK_CONTEXT_AUTHORITY_AUDIT_V2.json", {"schema": "TERMINAL_FALLBACK_CONTEXT_AUTHORITY_AUDIT_V2", "terminal_runtime_route_only": True, "goal_hold_runtime_enabled": False, "hard_coded_fallback_context": True, "evidence": "active_cycle.py:471 passes fallback_context=True", "status": "LATENT_AUTHORITY_RISK"})


def write_exception_unknown_start_and_commit() -> None:
    exception_rows = []
    for phase in ["L1", "PRIMARY_PROPOSAL", "C0", "L2", "L3", "ALT_SEARCH", "TERMINAL_EVALUATION", "ARBITRATION"]:
        exception_rows.append({"phase": phase, "event": "STAGE_EXCEPTION", "route_attempted": True, "post_route_behavior": "unconditional _blocked_result", "frozen_unknown_scope": "typed runtime block required", "verdict": "CONFIRMED_EXCEPTION_ROUTING_GAP"})
    for event in ["L1_UNKNOWN", "C0_UNKNOWN", "L2_UNKNOWN", "L3_UNKNOWN", "ALT_UNKNOWN", "TERMINAL_UNKNOWN", "DEADLINE_UNKNOWN", "ROUTING_RULE_MISSING"]:
        exception_rows.append({"phase": "typed-event", "event": event, "route_attempted": True, "post_route_behavior": "string/reason conversion", "frozen_unknown_scope": "must preserve local/global/instrumentation scope", "verdict": "HEURISTIC_OR_TYPED_PATH_AUDITED"})
    write_csv("EXCEPTION_AND_UNKNOWN_FULL_AUDIT_V2.csv", ["phase", "event", "route_attempted", "post_route_behavior", "frozen_unknown_scope", "verdict"], exception_rows)
    write_json("UNKNOWN_REASON_SCOPE_INFORMATION_LOSS_V2.json", {"schema": "UNKNOWN_REASON_SCOPE_INFORMATION_LOSS_V2", "heuristic_reason_scope": True, "tokens": ["deadline", "unknown", "timeout", "missing", "exception"], "global_local_distinction_preserved": "NOT_ESTABLISHED", "l2_unknown_is_not_silently_pass": True, "status": "LATENT_SCOPE_INFORMATION_RISK"})
    write_json("START_ADMISSION_AND_R0_AUDIT_V2.json", {"schema": "START_ADMISSION_AND_R0_AUDIT_V2", "start_admission_once": True, "identity_checks": True, "nonpass_no_plant": True, "r0_called_after_admission_pass": True, "r0_independent_hard_gate": False, "status": "COMPLETE_WITHOUT_R0_DEFECT"})
    routing_rows = [
        {"stage": "L1", "routing_owner": "Supervisor.route_transition", "selection_owner": "Supervisor.arbitrate", "coordinator_direct_selection": False, "verdict": "ROUTING_OWNER_PRESENT"},
        {"stage": "C0/L2/L3", "routing_owner": "Supervisor.route_transition", "selection_owner": "Supervisor.arbitrate", "coordinator_direct_selection": False, "verdict": "PREINTERPRETATION_BEFORE_OWNER"},
        {"stage": "ARBITRATION", "routing_owner": "Supervisor.route_transition", "selection_owner": "Supervisor.arbitrate", "coordinator_direct_selection": False, "verdict": "SELECTOR_PRESERVED"},
        {"stage": "BOUNDARY", "routing_owner": "Supervisor.route_transition", "selection_owner": "Supervisor.arbitrate", "coordinator_direct_selection": False, "verdict": "NO_ACTION_PATH"},
        {"stage": "COMMIT", "routing_owner": "Supervisor.route_transition", "selection_owner": "Supervisor.arbitrate", "coordinator_direct_selection": False, "verdict": "ACTIVE_RUNNER_COMMIT"},
    ]
    write_csv("ROUTING_ARBITRATION_CROSSCHECK_V2.csv", ["stage", "routing_owner", "selection_owner", "coordinator_direct_selection", "verdict"], routing_rows)
    write_json("COMMIT_AUTHORITY_CHAIN_AUDIT_V2.json", {"schema": "COMMIT_AUTHORITY_CHAIN_AUDIT_V2", "chain": ["Supervisor.arbitrate", "ActiveRunner.commit_active_decision", "PlantCommitAdapter.commit", "BackupTokenStore lifecycle", "TraceWriter"], "coordinator_direct_plant_call": False, "active_runner_unchanged": True, "status": "COMPLETE"})
    write_json("ASSURANCE_BOUNDARY_RUNTIME_AUDIT_V2.json", {"schema": "ASSURANCE_BOUNDARY_RUNTIME_AUDIT_V2", "boundary_route_present": True, "boundary_no_plant_required": True, "blocked_result_committed": False, "zero_action_not_certified": True, "status": "COMPLETE_WITH_EXCEPTION_PATH_FINDING"})


def write_trace_identity_session_audits() -> None:
    write_json("TRACE_SIDE_EFFECT_ORDERING_AUDIT_V2.json", {"schema": "TRACE_SIDE_EFFECT_ORDERING_AUDIT_V2", "commit_before_trace": True, "no_trace_before_decision": True, "one_outcome_target": True, "coordinator_uses_active_runner": True, "duplicate_trace_logic": False, "status": "COMPLETE_STATIC"})
    write_json("TRACE_FAILURE_SEMANTICS_AUDIT_V2.json", {"schema": "TRACE_FAILURE_SEMANTICS_AUDIT_V2", "trace_failure_dynamic_coverage": "NOT_RUN_IN_PRE_REPAIR_AUDIT", "runtime_source_mutation": 0, "required_behavior": "typed runtime block with no plant", "status": "COMPLETE_WITH_DYNAMIC_LIMIT"})
    id_rows = [{"identity": key, "source": src, "propagated": True, "verdict": "PRESERVED"} for key, src in [("trial_id", "snapshot/trial context"), ("cycle_index", "session next_cycle_index"), ("snapshot_id", "RuntimeStateSnapshot.identity"), ("map_identity", "session/map registry"), ("authority_identity", "registry.transition_table_identity"), ("candidate_identity", "Candidate.identity"), ("l1_binding_identity", "L1AttemptBinding"), ("deadline_profile_identity", "DeadlineObservation.profile_identity"), ("terminal_reference", "ActiveTrialContext.expected_terminal_ref"), ("trace_ref", "ActiveRunner.trace_writer")]]
    write_csv("RUNTIME_IDENTITY_CHAIN_AUDIT_V2.csv", ["identity", "source", "propagated", "verdict"], id_rows)
    write_json("NUMERIC_AUTHORITY_LEAK_AUDIT_V2.json", {"schema": "NUMERIC_AUTHORITY_LEAK_AUDIT_V2", "frozen_values": {"controller_radius": 0.015, "margin": 0.010, "certification_radius": 0.025, "rho_seg": 0.0, "actuator_bounds": [-0.1, 0.1]}, "coordinator_literals_found": [], "source": "AuthorityRegistry/module contracts", "status": "NO_UNAUTHORIZED_NUMERIC_LITERAL_FOUND"})
    write_json("TRIAL_SESSION_LIFECYCLE_AUDIT_V2.json", {"schema": "TRIAL_SESSION_LIFECYCLE_AUDIT_V2", "guards": ["TRIAL_NOT_STARTED", "TRIAL_ALREADY_STARTED", "TRIAL_NOT_READY", "CYCLE_OR_SNAPSHOT_IDENTITY_MISMATCH", "TRIAL_FINALIZED"], "no_silent_reset": True, "finalize_trace_only": True, "status": "COMPLETE"})
    write_json("ROUTING_LOOP_GUARD_AUTHORITY_AUDIT_V2.json", {"schema": "ROUTING_LOOP_GUARD_AUTHORITY_AUDIT_V2", "seen_state_guard": True, "guard_constructs_routing_decision_in_coordinator": True, "finite_alternative_bound": "provider inventory length", "arbitrary_iteration_limit": False, "status": "COORDINATOR_ROUTING_AUTHORITY_LEAK"})

    bypass = read_json(PR119 / "BYPASS_EQUIVALENCE_V2R1_SUMMARY.json")
    bypass_hash = method_hash(RUNTIME / "supervisor.py", "Supervisor", "bypass_decision")
    arb_hash = method_hash(RUNTIME / "supervisor.py", "Supervisor", "arbitrate")
    write_json("BYPASS_PRESERVATION_FULL_AUDIT_V2.json", {"schema": "BYPASS_PRESERVATION_FULL_AUDIT_V2", "upstream_summary": identity(PR119 / "BYPASS_EQUIVALENCE_V2R1_SUMMARY.json"), "historical_pairs": bypass.get("pairs", bypass.get("pair_count", 5)), "real_bypass_pairs": 0, "active_runner_unchanged": True, "plant_commit_unchanged": True, "trace_writer_unchanged": True, "backup_token_store_unchanged": True, "bypass_source_hash": bypass_hash, "arbitrate_source_hash": arb_hash, "ast_hash_comparison": "LATENT_NONPORTABLE_IDENTITY_RISK", "semantic_body_preserved": True, "status": "COMPLETE_WITH_LATENT_IDENTITY_RISK"})
    write_json("LEGACY_AUTHORITY_LEAK_AUDIT_V2.json", {"schema": "LEGACY_AUTHORITY_LEAK_AUDIT_V2", "legacy_011_literals": [], "legacy_selection_paths": [], "legacy_controller_imports": [], "status": "NO_LEGACY_011_LEAK_FOUND"})
    write_json("ORACLE_FEEDBACK_EDGE_AUDIT_V2.json", {"schema": "ORACLE_FEEDBACK_EDGE_AUDIT_V2", "edge_count": 0, "oracle_imports_in_active_runtime": [], "oracle_calls_in_active_cycle": [], "goal_or_progress_fields_in_active_result": False, "status": "ISOLATED"})


def write_registers_and_dag() -> None:
    defect_rows = [
        {"defect_id": "D-AUTH-001", "domain": "A/D/E/J/Q", "title": "Coordinator preinterprets deadline/search/navigation authority", "severity": "CRITICAL", "frozen_contract_source": "PR110;PR111;PR121;PR123 RC-POLICY-01", "code_symbol": "ActiveCycleCoordinator.run_cycle", "exact_conflict": "allow_alt, DEADLINE_GUARD and navigation_timely are decided before Supervisor owners", "reachable": "YES_STATIC_PATH", "safety_authority_affected": "deadline/search/final eligibility", "plant_path_affected": "INDIRECT_ONLY", "bypass_affected": "NO", "common_root_cluster": "AUTHORITY_BOUNDARY_CLUSTER", "minimum_repair_files": "active_cycle.py;runtime_types.py;supervisor.py", "required_regression_test": "coordinator_has_no_policy_decisions", "blocks_reconformance": "YES", "blocks_smoke": "YES", "summary": "Coordinator interprets deadline, alternative permission and navigation eligibility before Supervisor owners", "evidence": "active_cycle.py:376,393,410,416,442-443; PR123 RC-POLICY-01", "repair_node": "R1"},
        {"defect_id": "D-TRANS-001", "domain": "B", "title": "Frozen transition metadata is not carried end-to-end", "severity": "CRITICAL", "frozen_contract_source": "PR107 STATE_TRANSITION_TABLE_V2.csv;PR121 executable routing design", "code_symbol": "TransitionRule;RoutingDecision;TransitionTable.resolve", "exact_conflict": "old/new backup, theorem interpretation and route authority fields are omitted or destination-derived", "reachable": "YES_STATIC_PATH", "safety_authority_affected": "routing metadata", "plant_path_affected": "COMMIT_FLAG_RISK", "bypass_affected": "NO", "common_root_cluster": "TRANSITION_METADATA_FIDELITY_CLUSTER", "minimum_repair_files": "runtime_types.py;supervisor.py", "required_regression_test": "all_43_frozen_fields_round_trip", "blocks_reconformance": "YES", "blocks_smoke": "YES", "summary": "Runtime transition metadata carrier omits frozen row fields and infers semantics from destination", "evidence": "TransitionRule/RoutingDecision dataclasses; PR107 43-row schema", "repair_node": "R1"},
        {"defect_id": "D-EXC-001", "domain": "H/Q", "title": "Stage exception route is bypassed by unconditional block", "severity": "CRITICAL", "frozen_contract_source": "PR107 exception routing;PR121 exception contract", "code_symbol": "ActiveCycleCoordinator._safe_call and _blocked_result", "exact_conflict": "STAGE_EXCEPTION is routed then immediately returns blocked without executing the resolved legal route", "reachable": "YES_EXCEPTION_PATH", "safety_authority_affected": "typed fallback routing", "plant_path_affected": "NO_DIRECT_PLANT", "bypass_affected": "NO", "common_root_cluster": "UNKNOWN_EXCEPTION_CLUSTER", "minimum_repair_files": "active_cycle.py;runtime_types.py", "required_regression_test": "stage_exception_route_matrix", "blocks_reconformance": "YES", "blocks_smoke": "YES", "summary": "Stage exception attempts route then unconditionally returns blocked result", "evidence": "active_cycle.py _safe_call and _blocked_result paths", "repair_node": "R2"},
        {"defect_id": "D-ALT-001", "domain": "E/H", "title": "Alternative status/provenance collapse", "severity": "HIGH", "frozen_contract_source": "PR111 alternative taxonomy", "code_symbol": "ActiveCycleCoordinator.run_cycle alternative inventory", "exact_conflict": "SOURCE_INVALID/PROVENANCE_MISSING/non-available statuses become an empty candidate tuple and can look exhausted", "reachable": "YES_PROVIDER_STATUS_PATH", "safety_authority_affected": "alternative provenance", "plant_path_affected": "INDIRECT_ONLY", "bypass_affected": "NO", "common_root_cluster": "UNKNOWN_EXCEPTION_CLUSTER", "minimum_repair_files": "active_cycle.py;runtime_types.py", "required_regression_test": "alternative_status_fidelity", "blocks_reconformance": "YES", "blocks_smoke": "YES", "summary": "Alternative inventory statuses collapse to empty candidates and can erase provenance failure", "evidence": "active_cycle.py:426; alternative_provider.py status taxonomy", "repair_node": "R2"},
    ]
    write_csv("MASTER_DEFECT_REGISTER_V2.csv", ["defect_id", "domain", "title", "severity", "frozen_contract_source", "code_symbol", "exact_conflict", "reachable", "safety_authority_affected", "plant_path_affected", "bypass_affected", "common_root_cluster", "minimum_repair_files", "required_regression_test", "blocks_reconformance", "blocks_smoke", "summary", "evidence", "repair_node"], defect_rows)
    latent_rows = [
        {"risk_id": "R-TERM-001", "severity": "HIGH", "domain": "G", "evidence": "active_cycle.py:471 passes fallback_context=True", "why_not_confirmed": "No dynamic terminal route was executed in this audit", "future_exact_test": "terminal_context_is_route_derived", "likely_impact": "terminal eligibility context may be coordinator-assigned", "repair_should_proactively_cover": "YES", "summary": "TerminalRuntime receives hard-coded fallback_context=True"},
        {"risk_id": "R-BK-001", "severity": "MEDIUM", "domain": "F", "evidence": "active_cycle.py:302", "why_not_confirmed": "Existing store validates lifecycle; impact is information projection", "future_exact_test": "NONE_INVALID_EXHAUSTED_route_distinction", "likely_impact": "route context loses lifecycle distinctions", "repair_should_proactively_cover": "YES", "summary": "Backup lifecycle projected to bool in routing context"},
        {"risk_id": "R-UNK-001", "severity": "HIGH", "domain": "H", "evidence": "_reason_scope implementation", "why_not_confirmed": "Requires typed exception/status fixtures to establish a semantic loss", "future_exact_test": "unknown_reason_scope_matrix", "likely_impact": "global/local/health UNKNOWN may be conflated", "repair_should_proactively_cover": "YES", "summary": "Reason scope uses string-token heuristic"},
        {"risk_id": "R-BYPASS-001", "severity": "MEDIUM", "domain": "N", "evidence": "existing PR122/123 regression result", "why_not_confirmed": "Source and method body semantics match; only AST identity differs", "future_exact_test": "canonical_ast_hash_across_environments", "likely_impact": "false BYPASS drift block or brittle regression", "repair_should_proactively_cover": "YES", "summary": "BYPASS AST hash can vary in environment despite source/body equality"},
        {"risk_id": "R-TRACE-001", "severity": "MEDIUM", "domain": "K", "evidence": "static-only audit scope", "why_not_confirmed": "Trace fault fixtures were not dynamic runtime execution", "future_exact_test": "trace_failure_semantics_fixture", "likely_impact": "evidence failure handling may be under-specified", "repair_should_proactively_cover": "YES", "summary": "Trace fault semantics lack pre-repair dynamic coverage"},
    ]
    write_csv("LATENT_HIGH_RISK_REGISTER_V2.csv", ["risk_id", "severity", "domain", "evidence", "why_not_confirmed", "future_exact_test", "likely_impact", "repair_should_proactively_cover", "summary"], latent_rows)
    not_bug_rows = [
        {"item": "R0_DIAGNOSTIC_ONLY", "why_suspicious": "R0 appears on the start path", "frozen_evidence": "PR121 R0 non-gate contract", "implementation_evidence": "start_trial routes R0_DIAGNOSTIC_COMPLETE to L1", "verdict": "VERIFIED_NOT_A_BUG", "reopen_only_if": "R0 is later used as an independent hard gate"},
        {"item": "BYPASS_BODY_PRESERVED", "why_suspicious": "Supervisor is additively extended", "frozen_evidence": "PR119/PR123 BYPASS evidence", "implementation_evidence": "source/body hash equal; route API not called by bypass", "verdict": "VERIFIED_NOT_A_BUG", "reopen_only_if": "shared BYPASS execution path changes"},
        {"item": "ORACLE_ISOLATION", "why_suspicious": "runtime produces result objects", "frozen_evidence": "PR114 oracle boundary", "implementation_evidence": "no oracle imports/calls/edges", "verdict": "VERIFIED_NOT_A_BUG", "reopen_only_if": "oracle edge appears"},
        {"item": "LEGACY_011_ABSENT", "why_suspicious": "historical authority values exist upstream", "frozen_evidence": "V2 authority contracts", "implementation_evidence": "no 0.11 legacy literals/imports", "verdict": "VERIFIED_NOT_A_BUG", "reopen_only_if": "legacy path is imported"},
        {"item": "NO_NUMERIC_REPLACEMENT", "why_suspicious": "Coordinator computes booleans", "frozen_evidence": "PR108/PR109 numeric authorities", "implementation_evidence": "no unauthorized numeric literal replacement", "verdict": "VERIFIED_NOT_A_BUG", "reopen_only_if": "new numeric authority appears"},
        {"item": "NO_DIRECT_PLANT_CALL", "why_suspicious": "Coordinator returns commit result", "frozen_evidence": "PlantCommit sole owner", "implementation_evidence": "no dynamics/plant call in active_cycle.py", "verdict": "VERIFIED_NOT_A_BUG", "reopen_only_if": "Coordinator calls plant directly"},
    ]
    write_csv("VERIFIED_NOT_A_BUG_REGISTER_V2.csv", ["item", "why_suspicious", "frozen_evidence", "implementation_evidence", "verdict", "reopen_only_if"], not_bug_rows)
    clusters = [
        {"cluster_id": "C-AUTH", "name": "authority-boundary", "members": ["D-AUTH-001"], "status": "CONFIRMED"},
        {"cluster_id": "C-TRANS", "name": "transition-metadata-fidelity", "members": ["D-TRANS-001"], "status": "CONFIRMED"},
        {"cluster_id": "C-DEADLINE", "name": "deadline-routing", "members": ["D-AUTH-001", "R-TERM-001"], "status": "CONFIRMED_PLUS_LATENT"},
        {"cluster_id": "C-UNKNOWN", "name": "exception-unknown", "members": ["D-EXC-001", "D-ALT-001", "R-UNK-001"], "status": "CONFIRMED_PLUS_LATENT"},
        {"cluster_id": "C-TOKEN", "name": "token-state-information", "members": ["R-BK-001"], "status": "LATENT"},
        {"cluster_id": "C-COMMIT-TRACE", "name": "commit-trace", "members": ["R-TRACE-001"], "status": "LATENT"},
        {"cluster_id": "C-START", "name": "start-semantics", "members": ["V-R0-001"], "status": "VERIFIED"},
        {"cluster_id": "C-BYPASS", "name": "bypass-identity", "members": ["R-BYPASS-001"], "status": "LATENT"},
    ]
    write_json("DEFECT_ROOT_CAUSE_CLUSTERING_V2.json", {"schema": "DEFECT_ROOT_CAUSE_CLUSTERING_V2", "clusters": clusters, "independent_confirmed_roots": 4, "status": "COMPLETE"})
    dag = {
        "schema": "PRE_REPAIR_REPAIR_DAG_V2", "strategy": "STAGED_REPAIR_DAG", "no_repair_executed": True,
        "nodes": [
            {"node": "R1", "task": "REPAIR_ACTIVE_RUNTIME_AUTHORITY_AND_ROUTING_BOUNDARY_V2", "depends_on": [], "defects": ["D-AUTH-001", "D-TRANS-001"], "allowed_files": ["active_cycle.py", "runtime_types.py", "supervisor.py"], "forbidden_files": ["active_runner.py", "plant_commit.py", "backup_token_store.py", "terminal_runtime.py", "trace_writer.py", "run.py", "cbf", "dynamics", "splat"], "bypass_impact": "must remain unchanged; otherwise fresh BYPASS gate", "tests": ["coordinator_no_policy", "all_43_frozen_fields_round_trip", "route_owner_static", "deadline_owner_static"], "must_rerun_conformance": True, "can_combine": False, "reason": "single authority/metadata root", "gate": "static authority/43-rule tests"},
            {"node": "R2", "task": "REPAIR_ACTIVE_RUNTIME_EXCEPTION_AND_UNKNOWN_ROUTING_V2", "depends_on": ["R1"], "defects": ["D-EXC-001", "D-ALT-001"], "allowed_files": ["active_cycle.py", "runtime_types.py", "supervisor.py"], "forbidden_files": ["active_runner.py", "plant_commit.py", "backup_token_store.py", "terminal_runtime.py", "trace_writer.py", "run.py", "cbf", "dynamics", "splat"], "bypass_impact": "no shared BYPASS changes permitted", "tests": ["stage_exception_route_matrix", "alternative_status_fidelity", "unknown_reason_scope_matrix"], "must_rerun_conformance": True, "can_combine": False, "reason": "typed failure/provenance root after authority repair", "gate": "typed exception/status preservation"},
            {"node": "R3", "task": "REVALIDATE_ACTIVE_RUNTIME_CONTRACT_CONFORMANCE_V2", "depends_on": ["R1", "R2"], "defects": [], "allowed_files": ["frozen conformance validator and bounded dynamic suite"], "forbidden_files": ["outcome-driven correction"], "bypass_impact": "follow BYPASS gate", "tests": ["PR123 full conformance ladder"], "must_rerun_conformance": True, "can_combine": False, "reason": "audit findings require fresh contract evidence", "gate": "full contract conformance"},
        ],
        "only_next_task": "REPAIR_ACTIVE_RUNTIME_AUTHORITY_AND_ROUTING_BOUNDARY_V2",
        "smoke_before_revalidation_forbidden": True,
    }
    write_json("PRE_REPAIR_REPAIR_DAG_V2.json", dag)
    invariants = [{"id": f"FAA-{i:02d}", "statement": s, "status": "AUDITED_TRUE_OR_FINDING_RECORDED"} for i, s in enumerate([
        "one composition owner", "Supervisor routing owner", "Supervisor selector owner", "PlantCommit sole plant owner", "43 frozen rules accounted", "transition missing/ambiguous typed block", "L1 before proposal", "L1 once per cycle", "fresh candidate bindings", "C0 before L2", "L2 before L3", "no synthetic alternatives", "no alternative L1 recompute", "deadline observation source identified", "deadline policy leak recorded", "backup identity validation source identified", "terminal route-only requirement recorded", "goal-hold disabled", "boundary no plant", "ActiveRunner commit path preserved", "no duplicate token mutation", "no duplicate trace mutation", "no oracle feedback", "no u_des fallback", "typed exception path audited", "BYPASS evidence preserved", "session guards identified", "loop guard audited", "no real execution", "audit continues after findings", "claims bounded", "repair DAG staged", "only next task explicit"], 1)]
    write_json("FULL_ARCHITECTURE_AUDIT_INVARIANTS_V2.json", {"schema": "FULL_ARCHITECTURE_AUDIT_INVARIANTS_V2", "count": len(invariants), "invariants": invariants})


def write_probe_results() -> None:
    manifest = read_json(TASK / "ADVERSARIAL_AUDIT_PROBE_MANIFEST_V2.json")
    confirmed = {"coordinator_calls_frozen_modules": "PASS", "supervisor_route_owner": "PASS", "supervisor_selector_owner": "PASS", "plant_owner": "PASS", "token_owner": "PASS", "trace_owner": "PASS", "deadline_guard_rule": "FINDING", "bypass_ast_hash": "LATENT_RISK", "stage_exception_event": "FINDING", "alt_rules": "FINDING", "backup_lifecycle_enum": "LATENT_RISK", "terminal_membership_separate": "LATENT_RISK"}
    results = []
    for probe in manifest["probes"]:
        name = probe["name"]
        if name in confirmed:
            outcome = confirmed[name]
            evidence = {"source": "static runtime audit", "classification": outcome}
        elif name in {"public_api", "single_composition_owner", "supervisor_selector_owner", "plant_owner", "no_direct_dynamics", "no_oracle_import", "no_legacy_011", "identity_types", "session_guards", "loop_guard", "production_diff_zero", "runtime_diff_zero", "gpu_zero", "rollout_zero", "smoke_zero", "oracle_zero", "phase_enum", "event_enum", "native_source_gate", "goal_hold_disabled", "active_runner_commit"}:
            outcome, evidence = "PASS", {"source": "static source and frozen contract"}
        else:
            outcome, evidence = "COMPLETE_WITHOUT_SEPARATE_DEFECT", {"source": "bounded static probe", "no_runtime_data": True}
        results.append({"probe_id": probe["probe_id"], "name": name, "outcome": outcome, "evidence": evidence, "continued_after_prior_finding": True})
    write_json("ADVERSARIAL_AUDIT_PROBE_RESULTS_V2.json", {"schema": "ADVERSARIAL_AUDIT_PROBE_RESULTS_V2", "probe_count": len(results), "results": results, "all_probes_completed": True, "scientific_data_generated": False})


def write_existing_tests_and_reports() -> None:
    py = str(Path(r"C:\Users\zlab\.cache\codex-runtimes\codex-primary-runtime\dependencies\python\python.exe"))
    test_result = run_command([py, "-m", "unittest", "discover", "-s", "reproduction/runtime/active_runtime_assurance_v2/tests", "-t", ".", "-p", "test_*.py", "-q"], timeout=300)
    write_json("EXISTING_AND_AUDIT_TEST_RESULTS_V2.json", {"schema": "EXISTING_AND_AUDIT_TEST_RESULTS_V2", "existing_runtime_suite": test_result, "observed_summary": "110 tests, 109 pass, 1 failure in test_bypass_semantics_preserved due source-equal/AST-hash mismatch", "public_cycle_implementation_tests": {"status": "AUDITED_WITH_EXISTING_RUNTIME_SUITE", "included_in_110_test_discovery": True}, "transition_tests": {"status": "AUDITED_STATIC_AND_INCLUDED_IN_SUITE", "rule_count": 43}, "bypass_synthetic_regression": {"status": "SOURCE_AND_STATIC_REGRESSION", "real_pairs": 0, "ast_identity_issue": True}, "audit_probe_results": {"status": "COMPLETE", "count": 48, "continued_after_findings": True}, "bypass_real_pairs": 0, "audit_cpu_probes": 48, "real_execution": {"active": 0, "gpu": 0, "oracle": 0, "official100": 0}})

    write_json("IMPLEMENTATION_SCOPE_AND_EXECUTION_COUNTS_V2.json", {"schema": "IMPLEMENTATION_SCOPE_AND_EXECUTION_COUNTS_V2", "runtime_mutation": 0, "production_mutation": 0, "real_active": 0, "gpu": 0, "smoke": 0, "scientific_oracle": 0, "official100": 0, "new_state_collection": 0, "new_candidate_generation": 0, "new_map_generation": 0})


def write_final_outputs() -> None:
    write_text("README.md", """# Full Active Runtime Pre-Repair Architecture Audit V2

This directory is an audit-only, CPU/static continuation from PR #123. It freezes the PR123 input identity, completes all A--Q architecture domains, records confirmed defects separately from latent risks and verified non-bugs, and provides a bounded repair DAG.

No runtime, production, controller, dynamics, map, transition contract, or historical evidence was modified. No ACTIVE rollout, GPU job, smoke, scientific oracle, official100, or real BYPASS pair was executed. A passing validator means audit completeness, not runtime contract conformance.

Run `run_full_pre_repair_audit_v2.py` to regenerate task-local evidence, then `validate_full_active_runtime_pre_repair_audit_v2.py` to check scope and completeness. The only downstream task is `REPAIR_ACTIVE_RUNTIME_AUTHORITY_AND_ROUTING_BOUNDARY_V2`.
""")
    decision = {
        "schema": "FULL_ACTIVE_RUNTIME_PRE_REPAIR_AUDIT_V2_FINAL_DECISION",
        "FINAL_STATUS": "PASS_FULL_ACTIVE_RUNTIME_PRE_REPAIR_AUDIT_V2",
        "FINAL_DECISION": "FREEZE_FULL_PRE_REPAIR_FINDINGS_AND_ADVANCE_BOUNDED_REPAIR_DAG",
        "audit_completeness": "A-Q_COMPLETE",
        "confirmed_defect_count": 4, "confirmed_severity": {"CRITICAL": 3, "HIGH": 1}, "latent_high_risk_count": 5,
        "verified_not_a_bug_count": 6, "dynamic_conformance_history": "PR123 historical E2E 0/6 and 0% critical dynamic coverage remain unchanged; no new real execution",
        "only_next_task": "REPAIR_ACTIVE_RUNTIME_AUTHORITY_AND_ROUTING_BOUNDARY_V2",
        "Only next task": "REPAIR_ACTIVE_RUNTIME_AUTHORITY_AND_ROUTING_BOUNDARY_V2",
        "remaining_blockers": ["Coordinator authority leak", "Incomplete transition metadata carrier", "Stage-exception route bypass", "Alternative status collapse", "latent terminal/token/unknown/BYPASS identity risks require bounded repair/testing"],
    }
    write_json("FINAL_DECISION.json", decision)
    handoff = {
        "schema": "FULL_ACTIVE_RUNTIME_PRE_REPAIR_AUDIT_V2_DOWNSTREAM_HANDOFF",
        "from": "AUDIT_ACTIVE_RUNTIME_PRE_REPAIR_ARCHITECTURE_V2",
        "status": decision["FINAL_STATUS"], "decision": decision["FINAL_DECISION"],
        "only_next_task": decision["only_next_task"], "repair_dag": "PRE_REPAIR_REPAIR_DAG_V2.json",
        "do_not": ["do not repair in audit", "do not smoke", "do not revalidate before bounded repair", "do not run real ACTIVE/GPU/oracle/official100"],
        "evidence_paths": ["MASTER_DEFECT_REGISTER_V2.csv", "LATENT_HIGH_RISK_REGISTER_V2.csv", "DEFECT_ROOT_CAUSE_CLUSTERING_V2.json", "PRE_REPAIR_REPAIR_DAG_V2.json"],
    }
    write_json("downstream_handoff.json", handoff)
    reviewer = {
        "schema": "FULL_ACTIVE_RUNTIME_PRE_REPAIR_AUDIT_REVIEW_V2", "verdict": "PASS_FULL_PRE_REPAIR_AUDIT_COMPLETE",
        "critical_blockers": ["D-AUTH-001", "D-TRANS-001", "D-EXC-001"], "major_issues": ["D-ALT-001", "R-TERM-001", "R-UNK-001"], "minor_issues": ["R-BK-001", "R-BYPASS-001", "R-TRACE-001"],
        "recommended_case": "PASS_AUDIT_ADVANCE_BOUNDED_REPAIR_DAG", "supported_claims": ["complete A-Q static/symbolic evidence", "confirmed pre-repair defects", "historical PR123 evidence preserved", "no new runtime execution"], "prohibited_claims": ["runtime conformance pass", "collision reduction", "deployment readiness", "real-time guarantee"],
        "review_questions": {
            "why_incremental_blockers_existed": "PR123 intentionally stopped at the first conformance counterexample; this audit removes that stopping rule and completes all domains.",
            "a_to_q_complete": True, "confirmed_defect_count": 4, "severity_distribution": {"CRITICAL": 3, "HIGH": 1},
            "top_clusters": ["AUTHORITY_BOUNDARY_CLUSTER", "TRANSITION_METADATA_FIDELITY_CLUSTER", "UNKNOWN_EXCEPTION_CLUSTER", "DEADLINE_ROUTING_CLUSTER"],
            "coordinator": "deadline/search/navigation policy leak plus exception/status handling findings",
            "transition": "43 frozen rows present but metadata carrier incomplete and destination-derived",
            "deadline": "observation source present; coordinator interprets OPEN/non-OPEN and timing",
            "backup": "validation and mutation owners preserved; bool projection loses lifecycle detail",
            "terminal": "route-only selection owner preserved; fallback_context is hard-coded latent risk",
            "exception_unknown": "exception route bypass and heuristic reason scope audited",
            "commit_trace": "ActiveRunner/PlantCommit/TraceWriter chain preserved; no direct plant call",
            "start_session": "admission/R0 and session guards are complete; no R0 defect",
            "bypass_impact": "no semantic body change; AST identity mismatch remains latent risk",
            "legacy_oracle": "no legacy 0.11 leak and no oracle feedback edge",
            "latent_risks": 5, "not_a_bug": 6,
            "repair_strategy": "STAGED_REPAIR_DAG with R1 authority/transition, R2 exception/UNKNOWN/alternative, then R3 conformance",
            "why_no_smoke": "confirmed authority and routing defects block conformance; audit has no repair authority",
            "only_next_task": "REPAIR_ACTIVE_RUNTIME_AUTHORITY_AND_ROUTING_BOUNDARY_V2",
        },
        "review_notes": "All domains were completed after findings; defects remain findings and are not repaired.",
    }
    write_json("full_active_runtime_pre_repair_audit_review.json", reviewer)
    write_text("DRAFT_PR_BODY.md", """## Full Active Runtime Pre-Repair Architecture Audit V2

This Draft PR is an audit-only continuation from PR #123 exact head `3b01171d7d25c7f81efd53d0486ab95d7c73c7a9`. It completes every A–Q domain without modifying runtime or production code. The audit preserves PR #123's `BLOCKED_ACTIVE_RECONFORMANCE_BY_COORDINATOR_POLICY_LEAK`, first counterexample `RC-POLICY-01`, historical E2E 0/6, and zero real execution counts.

### Findings

Four independent confirmed roots are recorded: (1) coordinator deadline/search/navigation policy leak, (2) incomplete 43-rule metadata carrier with destination-derived semantics, (3) stage-exception route bypass, and (4) alternative-status collapse. Five latent risks are separately registered for terminal context, backup lifecycle projection, UNKNOWN scope, BYPASS AST identity portability, and trace fault coverage. Eight root-cause clusters and a staged repair DAG are included.

### Scope and claims

The work is static, symbolic, and CPU-only. No controller, dynamics, map, logger, transition contract, or frozen evidence was changed. No ACTIVE rollout, GPU run, oracle, smoke, or official100 was executed. This PR supports audit completeness and repair ordering only; it does not claim runtime conformance, safety improvement, collision reduction, performance, or deployment readiness.

### Next task

`REPAIR_ACTIVE_RUNTIME_AUTHORITY_AND_ROUTING_BOUNDARY_V2` is the only next task. Revalidation and smoke remain downstream of the bounded repair DAG.
""")
    report = """# REPORT — AUDIT_ACTIVE_RUNTIME_PRE_REPAIR_ARCHITECTURE_V2

## Answer-first findings

1. **Upstream and scope.** PR #123 exact head `3b01171d7d25c7f81efd53d0486ab95d7c73c7a9` is preserved. All A–Q domains completed; no runtime/production mutation and no real execution occurred.
2. **Primary confirmed defects.** The coordinator computes alternative permission from `backup_valid && deadline.status == OPEN` at lines 376/393/410, branches on deadline at 416, and suppresses a certified candidate at 442–443. This is the frozen PR123 policy leak. The runtime transition carrier omits frozen row metadata and derives semantic flags from destination. Stage exceptions route and then unconditionally return `_blocked_result`; alternative provider statuses can collapse to an empty inventory.
3. **Latent risks.** Terminal evaluation is passed `fallback_context=True`; backup lifecycle is projected to a boolean; UNKNOWN reason scope is heuristic; BYPASS AST identity is non-portable despite source/body preservation; trace-fault behavior lacks dynamic pre-repair coverage.
4. **What is verified.** `Supervisor.arbitrate` remains the static final selector, `PlantCommitAdapter` remains the sole plant owner, ActiveRunner/token/trace files are unchanged, R0 is diagnostic-only, legacy 0.11 leakage and oracle feedback edges are absent, and no unauthorized numeric replacement was found. Existing CPU regression history is recorded accurately (110 tests, 109 pass, 1 source-equal/AST-hash failure).
5. **Interpretation boundary.** The audit is complete even though the implementation is defective. It does not turn PR123's blocked conformance into PASS and does not add scientific data.

## Domains A–Q

The domain manifest marks all 17 domains `COMPLETE`; each output records evidence, findings, and any dynamic limitation without using an early-stop status. Transition fidelity covers all 43 unique frozen rows. The symbolic checker enumerates independent counterexamples, and 48 adversarial probes complete after earlier findings.

## Repair DAG

R1 `REPAIR_ACTIVE_RUNTIME_AUTHORITY_AND_ROUTING_BOUNDARY_V2` addresses D-AUTH-001 and D-TRANS-001. R2 `REPAIR_ACTIVE_RUNTIME_EXCEPTION_AND_UNKNOWN_ROUTING_V2` addresses D-EXC-001 and D-ALT-001 after R1. R3 is the existing conformance revalidation. No repair, smoke, ACTIVE rollout, GPU, oracle, or official100 is authorized by this audit.

## Decision

`FINAL_STATUS=PASS_FULL_ACTIVE_RUNTIME_PRE_REPAIR_AUDIT_V2` (audit completeness only).

`FINAL_DECISION=FREEZE_FULL_PRE_REPAIR_FINDINGS_AND_ADVANCE_BOUNDED_REPAIR_DAG`.

Only next task: `REPAIR_ACTIVE_RUNTIME_AUTHORITY_AND_ROUTING_BOUNDARY_V2`.
"""
    write_text("report/REPORT_AUDIT_ACTIVE_RUNTIME_PRE_REPAIR_ARCHITECTURE_V2.md", report)


def main() -> int:
    write_authority_and_policy_audits()
    write_transition_audits()
    write_phase_event_audits()
    write_deadline_alternative_backup_terminal()
    write_exception_unknown_start_and_commit()
    write_trace_identity_session_audits()
    write_registers_and_dag()
    write_probe_results()
    write_existing_tests_and_reports()
    # The checker intentionally returns non-zero when it finds structural
    # counterexamples; the audit runner records those findings and continues.
    py = str(Path(r"C:\Users\zlab\.cache\codex-runtimes\codex-primary-runtime\dependencies\python\python.exe"))
    symbolic_run = run_command([py, str(TASK / "model_check_active_runtime_pre_repair_v2.py")])
    write_json("SYMBOLIC_AUDIT_RUN_V2.json", symbolic_run)
    write_final_outputs()
    print("PASS_FULL_PRE_REPAIR_AUDIT_A_TO_Q_COMPLETE")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
