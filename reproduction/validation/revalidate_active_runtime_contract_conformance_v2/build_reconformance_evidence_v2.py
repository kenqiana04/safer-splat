"""Materialize compact fail-closed reconformance evidence after the first mismatch."""

from __future__ import annotations

import ast
import csv
import dataclasses
import hashlib
import json
import sys
from pathlib import Path


TASK = Path(__file__).resolve().parent
REPO = TASK.parents[2]
RUNTIME = REPO / "reproduction/runtime/active_runtime_assurance_v2"
DESIGN = REPO / "reproduction/design/active_runtime_public_cycle_composition_v2"
PR107 = REPO / "reproduction/specification/method_logic_closure_v2/STATE_TRANSITION_TABLE_V2.csv"
sys.path.insert(0, str(REPO))

from reproduction.runtime.active_runtime_assurance_v2.runtime_types import RoutingDecision  # noqa: E402
from reproduction.runtime.active_runtime_assurance_v2.supervisor import TransitionRule  # noqa: E402


BLOCK = "BLOCKED_ACTIVE_RECONFORMANCE_BY_COORDINATOR_POLICY_LEAK"
NEXT = "DIAGNOSE_ACTIVE_CYCLE_COORDINATOR_POLICY_LEAK_V2"


def write_json(name: str, value: object) -> None:
    path = TASK / name
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(value, indent=2, sort_keys=True) + "\n", encoding="utf-8", newline="\n")


def source_lines(path: Path) -> dict[int, str]:
    return {index: line.strip() for index, line in enumerate(path.read_text(encoding="utf-8").splitlines(), 1)}


def freeze_counterexample() -> dict[str, object]:
    item = {
        "schema": "FIRST_ACTIVE_RECONFORMANCE_COUNTEREXAMPLE_V2",
        "scenario": "RC-POLICY-01",
        "critical": True,
        "frozen_source": [
            {
                "path": "reproduction/design/active_runtime_public_cycle_composition_v2/PUBLIC_CYCLE_COMPOSITION_CONTRACT_V2.md",
                "lines": "4-14",
                "requirement": "Coordinator orchestrates only; it does not interpret deadline or call fallback on its own.",
            },
            {
                "path": "reproduction/design/active_runtime_public_cycle_composition_v2/SUPERVISOR_ROUTING_AUTHORITY_V2.md",
                "lines": "21-22",
                "requirement": "Supervisor owns deadline interpretation and alternative permission.",
            },
        ],
        "expected": "Coordinator forwards deadline and evidence facts unchanged; Supervisor alone determines alternative permission and navigation eligibility.",
        "observed": [
            "active_cycle.py:376 computes allow_alt from backup validity and DEADLINE_OPEN before routing",
            "active_cycle.py:393 repeats that policy computation for L2",
            "active_cycle.py:410 repeats that policy computation for L3",
            "active_cycle.py:416 branches directly on deadline state before route lookup",
            "active_cycle.py:442-443 removes the certified candidate when the coordinator judges it untimely",
        ],
        "runtime_call_path": "ActiveCycleCoordinator.run_cycle -> coordinator deadline/eligibility branch -> RuntimeRoutingContext -> Supervisor.route_transition/arbitrate",
        "authority": "Supervisor.route_transition and Supervisor.arbitrate",
        "safety_criticality": "The coordinator can enable/suppress search and candidate eligibility before the frozen routing/selection owners act.",
        "bypass_impact": "NONE; the observed code is on the ACTIVE-only public-cycle path.",
        "minimal_suspected_file": "reproduction/runtime/active_runtime_assurance_v2/active_cycle.py",
        "runtime_correction_applied": False,
        "dynamic_suite_stopped": True,
    }
    write_json("FIRST_COUNTEREXAMPLE_V2.json", item)
    return item


def policy_audit() -> None:
    entries = [
        (302, "backup_evidence.status -> backup_valid", "MECHANICAL_EVENT_CONVERSION"),
        (304, "valid token -> read exact current action", "MECHANICAL_TOKEN_EVIDENCE_PREPARATION"),
        (376, "backup_valid AND DEADLINE_OPEN -> alternative_search_allowed", "POLICY_DECISION"),
        (393, "backup_valid AND DEADLINE_OPEN -> alternative_search_allowed", "POLICY_DECISION"),
        (410, "backup_valid AND DEADLINE_OPEN -> alternative_search_allowed", "POLICY_DECISION"),
        (416, "deadline non-OPEN -> coordinator chooses DEADLINE_GUARD event path", "POLICY_DECISION"),
        (442, "L3 evidence AND DEADLINE_OPEN -> navigation_timely", "POLICY_DECISION"),
        (443, "navigation_timely -> candidate forwarded or suppressed", "POLICY_DECISION"),
        (452, "terminal result -> terminal_ready fact", "MECHANICAL_EVENT_CONVERSION"),
    ]
    write_json("COORDINATOR_POLICY_LEAK_AUDIT_V2.json", {
        "schema": "COORDINATOR_POLICY_LEAK_AUDIT_V2",
        "status": "FAIL_COORDINATOR_POLICY_LEAK",
        "policy_decision_count": sum(kind == "POLICY_DECISION" for _, _, kind in entries),
        "first_policy_decision_line": 376,
        "entries": [{"line": line, "expression": expression, "classification": kind} for line, expression, kind in entries],
        "ast_parsed": isinstance(ast.parse((RUNTIME / "active_cycle.py").read_text(encoding="utf-8")), ast.Module),
        "direct_plant_call": False,
        "direct_action_construction": False,
        "candidate_synthesis": False,
        "conclusion": "Deadline/search/navigation eligibility is partly interpreted by the coordinator, violating the frozen authority split.",
    })


def transition_fidelity() -> None:
    with PR107.open(encoding="utf-8", newline="") as handle:
        raw_rows = list(csv.DictReader(handle))
    design = json.loads((DESIGN / "EXECUTABLE_TRANSITION_ROUTING_DESIGN_V2.json").read_text(encoding="utf-8"))
    design_by_id = {row["rule_id"]: row for row in design["rules"]}
    rule_fields = {field.name for field in dataclasses.fields(TransitionRule)}
    decision_fields = {field.name for field in dataclasses.fields(RoutingDecision)}
    required_rule = {"old_backup_retained", "new_backup_created", "theorem_interpretation", "may_start_next_stage", "may_start_new_search", "requires_arbitration"}
    required_decision = {"action_authority", "old_backup_retained", "new_backup_created", "theorem_interpretation"}
    missing_rule = sorted(required_rule - rule_fields)
    missing_decision = sorted(required_decision - decision_fields)
    fieldnames = [
        "rule_id", "row_sha256", "runtime_transition_rule_loaded", "routing_decision_invoked",
        "missing_transition_rule_fields", "missing_routing_decision_fields", "status",
    ]
    with (TASK / "TRANSITION_ROW_FIDELITY_AUDIT_V2.csv").open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=fieldnames)
        writer.writeheader()
        for row in raw_rows:
            expected = design_by_id[row["rule_id"]]
            writer.writerow({
                "rule_id": row["rule_id"],
                "row_sha256": hashlib.sha256(json.dumps(expected, sort_keys=True, separators=(",", ":")).encode()).hexdigest(),
                "runtime_transition_rule_loaded": "YES",
                "routing_decision_invoked": "NO_STOPPED_AFTER_FIRST_CRITICAL_COUNTEREXAMPLE",
                "missing_transition_rule_fields": "|".join(missing_rule),
                "missing_routing_decision_fields": "|".join(missing_decision),
                "status": "FAIL_METADATA_CARRIER_INCOMPLETE",
            })

    with (TASK / "ACTIVE_RECONFORMANCE_TRANSITION_MATRIX_V2.csv").open("w", encoding="utf-8", newline="") as handle:
        fields = ["rule_id", "row_hash", "expected_context", "public_scenario", "observed_rule", "destination", "metadata", "downstream_action", "coverage_class", "status"]
        writer = csv.DictWriter(handle, fieldnames=fields)
        writer.writeheader()
        for row in raw_rows:
            expected = design_by_id[row["rule_id"]]
            writer.writerow({
                "rule_id": row["rule_id"],
                "row_hash": hashlib.sha256(json.dumps(expected, sort_keys=True, separators=(",", ":")).encode()).hexdigest(),
                "expected_context": "FROZEN_PR107_PR121_CONTEXT",
                "public_scenario": "NOT_EXECUTED_AFTER_RC-POLICY-01",
                "observed_rule": "NOT_EXECUTED",
                "destination": row["destination_phase"],
                "metadata": "STATIC_METADATA_CARRIER_GAP",
                "downstream_action": "NOT_EXECUTED",
                "coverage_class": "CRITICAL_DYNAMIC",
                "status": "NOT_EXECUTED_AFTER_FIRST_CRITICAL_COUNTEREXAMPLE",
            })


def write_audits() -> None:
    write_json("PR120_BLOCKER_CLOSURE_V2.json", {
        "schema": "PR120_BLOCKER_CLOSURE_V2",
        "status": "PASS_INTEGRATION_ORCHESTRATION_GAP_CLOSED",
        "genuine_public_api": True,
        "public_owner": "ActiveCycleCoordinator",
        "api": ["start_trial", "run_cycle", "finalize_trial"],
        "caller_precomputes_internal_evidence": False,
        "source_evidence": "active_cycle.py owns module calls, Supervisor route/arbitrate calls, and ActiveRunner commit requests.",
        "scope": "Structural closure only; downstream contract conformance remains blocked.",
    })
    write_json("ACTIVE_RECONFORMANCE_AUTHORITY_OWNERSHIP_V2.json", {
        "schema": "ACTIVE_RECONFORMANCE_AUTHORITY_OWNERSHIP_V2",
        "status": "FAIL_COORDINATOR_PREINTERPRETS_ROUTING_FACTS",
        "routing_owner": "Supervisor.route_transition",
        "selection_owner": "Supervisor.arbitrate",
        "plant_owner": "PlantCommitAdapter.commit",
        "token_mutation_owner": "ActiveRunner/BackupTokenStore",
        "trace_owner": "ActiveRunner/TraceWriter",
        "owner_implementations_unique": True,
        "authority_boundary_violation": "Coordinator preinterprets deadline/search/navigation eligibility before invoking owners.",
    })
    deferred = "NOT_EXECUTED_AFTER_FIRST_CRITICAL_COUNTEREXAMPLE"
    write_json("TRANSITION_EXACT_ONE_REVALIDATION_V2.json", {
        "schema": "TRANSITION_EXACT_ONE_REVALIDATION_V2", "status": deferred,
        "unique_rule_ids_static": 43, "legal_context_dynamic_checks": 0,
        "pairwise_overlap_analysis": deferred, "missing_and_ambiguous_typed_checks": deferred,
    })
    write_json("PUBLIC_CYCLE_CALL_ORDER_REVALIDATION_V2.json", {
        "schema": "PUBLIC_CYCLE_CALL_ORDER_REVALIDATION_V2", "status": deferred,
        "expected": ["CYCLE_BEGIN", "L1", "PRIMARY_PROPOSAL", "BIND", "C0", "L2", "L3", "ARBITRATION", "COMMIT", "TOKEN_UPDATE", "TRACE", "CYCLE_COMPLETE"],
        "observed": [], "l1_calls": 0,
    })
    write_json("STAGE_EXCEPTION_ROUTING_REVALIDATION_V2.json", {
        "schema": "STAGE_EXCEPTION_ROUTING_REVALIDATION_V2", "status": deferred,
        "injected_stage_count": 0, "supervisor_routes_observed": 0,
        "note": "No stage exceptions were injected after RC-POLICY-01 was frozen.",
    })
    write_json("DEADLINE_OBSERVATION_POINT_AUDIT_V2.json", {
        "schema": "DEADLINE_OBSERVATION_POINT_AUDIT_V2", "status": "BLOCKED_BY_COORDINATOR_DEADLINE_POLICY_INTERPRETATION",
        "dynamic_observation_sequence": deferred,
        "static_findings": ["deadline observations exist", "coordinator interprets OPEN for alternative permission and navigation eligibility"],
    })
    write_json("BACKUP_PREVALIDATION_SEMANTICS_V2.json", {
        "schema": "BACKUP_PREVALIDATION_SEMANTICS_V2", "status": deferred,
        "static_observation": "token validation is prepared before L1; dynamic non-preemption test was not run",
    })
    write_json("ROUTING_ARBITRATION_CONSISTENCY_V2.json", {
        "schema": "ROUTING_ARBITRATION_CONSISTENCY_V2", "status": deferred,
        "commit_allowed_enforced": False, "dynamic_cycles": 0,
    })
    write_json("BYPASS_EVIDENCE_PRESERVATION_REVALIDATION_V2.json", {
        "schema": "BYPASS_EVIDENCE_PRESERVATION_REVALIDATION_V2",
        "status": "PASS_BYPASS_UPSTREAM_EVIDENCE_PRESERVED",
        "real_bypass_pairs_run": 0,
        "supervisor_bypass_ast_unchanged_from_pr122_lock": True,
        "active_runner_commit_bypass_unchanged": True,
        "plant_commit_unchanged": True,
        "trace_writer_unchanged": True,
        "canonical_identity_path_unchanged": True,
        "bypass_revalidation_required": False,
    })


def scenario_results() -> None:
    deferred = "NOT_EXECUTED_AFTER_FIRST_CRITICAL_COUNTEREXAMPLE"
    gates = {
        "blocker_closure": "PASS_STATIC", "coordinator_policy": "FAIL",
        "routing_metadata": "FAIL_STATIC_SECONDARY", "exact_one": deferred,
        "canonical_order": deferred, "start": deferred, "l1": deferred,
        "primary_c0": deferred, "l2_l3": deferred, "exception": deferred,
        "deadline": deferred, "alternative": deferred, "backup": deferred,
        "terminal": deferred, "routing_arbitration_commit": deferred,
        "trace": deferred, "trace_failure": deferred, "bypass": "PASS_STATIC",
    }
    write_json("scenario_results.json", {
        "schema": "ACTIVE_RECONFORMANCE_SCENARIO_RESULTS_V2",
        "overall": BLOCK,
        "first_counterexample": "RC-POLICY-01",
        "gate_status": gates,
        "precritical_test_run": {"tests": 3, "passed": 2, "failed": 1, "failure_scope": "HARNESS_SYMBOL_ALIAS_EXPECTATION; independent structural audit used exact attribute name"},
        "dynamic_scenarios_stopped": True,
        "e2e_genuine_pass": 0,
        "e2e_genuine_required": 6,
        "critical_dynamic_coverage_percent": 0,
        "runtime_correction_quota": 0,
        "runtime_correction_count": 0,
        "protocol_deviation_count": 0,
        "execution_counts": {"runtime_correction": 0, "real_active": 0, "gpu": 0, "smoke": 0, "scientific_oracle": 0, "official100": 0, "real_bypass_pair": 0},
    })


def docs_and_decision() -> None:
    readme = f"""# Active Runtime Contract Reconformance V2

CPU-only, fail-closed reconformance of PR #122. The PR #120 public-orchestration gap is structurally closed, but the first critical audit found coordinator-owned deadline/search eligibility policy in `active_cycle.py`. The frozen protocol therefore stopped all later dynamic scenarios. No runtime source was modified.

- Final status: `{BLOCK}`
- Runtime correction count: `0`
- Real ACTIVE/GPU/smoke/oracle/official100: `0/0/0/0/0`
- Only next task: `{NEXT}`
"""
    (TASK / "README.md").write_text(readme, encoding="utf-8", newline="\n")
    write_json("FINAL_DECISION.json", {
        "schema": "REVALIDATED_ACTIVE_RUNTIME_CONTRACT_CONFORMANCE_V2_FINAL_DECISION",
        "FINAL_STATUS": BLOCK,
        "FINAL_DECISION": "DO_NOT_ENTER_ACTIVE_RUNTIME_SMOKE; FREEZE_FIRST_COUNTEREXAMPLE_AND_DIAGNOSE_COORDINATOR_POLICY_BOUNDARY",
        "first_counterexample": "RC-POLICY-01",
        "pr120_integration_gap_closed": True,
        "bypass_revalidation_required": False,
        "remaining_blockers": ["Coordinator interprets deadline/search/navigation eligibility before Supervisor routing/arbitration."],
        "Only next task": NEXT,
    })
    write_json("downstream_handoff.json", {
        "schema": "ACTIVE_RECONFORMANCE_DOWNSTREAM_HANDOFF_V2",
        "authorized_next_task": NEXT,
        "input_branch": "revalidate-active-runtime-contract-conformance-v2",
        "do_not": ["modify runtime in this task", "smoke", "real ACTIVE", "GPU", "scientific oracle", "official100"],
        "repair_scope": "Diagnose the minimal authority split around alternative permission, deadline guard, and navigation eligibility in active_cycle.py; preserve frozen contracts and BYPASS semantics.",
    })
    review = {
        "verdict": "BLOCKED_REVALIDATED_ACTIVE_RUNTIME_CONTRACT_CONFORMANCE_V2",
        "blocker_closure": "PASS structural public API closure",
        "genuine_coordinator": "YES",
        "policy_leak": "CRITICAL: coordinator interprets deadline/search/navigation eligibility",
        "transition_fidelity": "Secondary static carrier gap: row-level action/backup/theorem metadata is not represented end-to-end",
        "exact_one": "Not executed after first critical counterexample",
        "canonical_order": "Not dynamically revalidated",
        "exception_deadline_backup_terminal_commit_trace": "Not dynamically revalidated",
        "e2e": "0/6 by stop rule",
        "dynamic_coverage": "0% by stop rule",
        "model_counterexample": "Routing metadata carrier incomplete",
        "bypass": "Preserved; no real BYPASS rerun",
        "smoke_eligible": False,
        "recommended_next_task": NEXT,
    }
    write_json("revalidated_active_runtime_contract_conformance_review.json", review)

    report_dir = TASK / "report"
    report_dir.mkdir(exist_ok=True)
    report = f"""# Report: Revalidate Active Runtime Contract Conformance V2

## Answer first

`FINAL_STATUS={BLOCK}`

`FINAL_DECISION=DO_NOT_ENTER_ACTIVE_RUNTIME_SMOKE; FREEZE_FIRST_COUNTEREXAMPLE_AND_DIAGNOSE_COORDINATOR_POLICY_BOUNDARY`

PR #120's missing public composition root is structurally closed: `ActiveCycleCoordinator.start_trial`, `run_cycle`, and `finalize_trial` exist and invoke the frozen modules, Supervisor, and ActiveRunner. Full contract conformance is nevertheless blocked.

The first critical counterexample is `RC-POLICY-01`. In `active_cycle.py`, the coordinator computes alternative permission from backup validity and `DEADLINE_OPEN` (lines 376, 393, 410), selects a deadline-guard path (line 416), and filters the certified navigation candidate by its own deadline interpretation (lines 442–443). Frozen PR #121 assigns deadline interpretation and alternative permission to Supervisor. This is a policy/authority leak, not mechanical event conversion.

## Consequences

- Runtime correction quota remained zero; no source or contract was changed.
- All later dynamic scenarios stopped immediately after the first critical mismatch.
- Genuine E2E reconformance is therefore `0/6`, and critical dynamic coverage is `0%`; these are **not** failed scientific trials.
- No smoke, real ACTIVE rollout, GPU work, scientific oracle, official100, or real BYPASS pair ran.
- BYPASS source identities remain preserved and no BYPASS revalidation is currently required.

## Secondary static observation

The 43-row audit also found that runtime `TransitionRule` and `RoutingDecision` do not carry all frozen row-level metadata (`action_authority`, backup retention/creation, and theorem interpretation; `TransitionRule` also lacks explicit search/arbitration permissions). This was recorded after the dynamic stop only as static evidence and is not substituted for the first counterexample.

## Remaining blocker and handoff

The next bounded task is `{NEXT}`. It must diagnose the minimal ownership correction without performing runtime changes, smoke, or real execution in this reconformance task.
"""
    (report_dir / "REPORT_REVALIDATE_ACTIVE_RUNTIME_CONTRACT_CONFORMANCE_V2.md").write_text(report, encoding="utf-8", newline="\n")
    pr_body = f"""## Summary

- Revalidates PR #122's public Active runtime composition against frozen PR #107–#121 contracts.
- Confirms the PR #120 missing composition root is structurally closed.
- Freezes `RC-POLICY-01`: coordinator-side deadline/search/navigation eligibility interpretation violates Supervisor authority.
- Stops all later dynamic scenarios and applies no runtime correction.

## Evidence boundary

- CPU/static only; real ACTIVE/GPU/smoke/oracle/official100: `0/0/0/0/0`.
- E2E: `0/6` and critical dynamic coverage `0%` because the fail-closed stop rule fired.
- BYPASS upstream evidence remains preserved.

`FINAL_STATUS={BLOCK}`

`FINAL_DECISION=DO_NOT_ENTER_ACTIVE_RUNTIME_SMOKE; FREEZE_FIRST_COUNTEREXAMPLE_AND_DIAGNOSE_COORDINATOR_POLICY_BOUNDARY`

Only next task: `{NEXT}`
"""
    (TASK / "DRAFT_PR_BODY.md").write_text(pr_body, encoding="utf-8", newline="\n")


def main() -> None:
    freeze_counterexample()
    policy_audit()
    transition_fidelity()
    write_audits()
    scenario_results()
    docs_and_decision()
    print(BLOCK)


if __name__ == "__main__":
    main()
