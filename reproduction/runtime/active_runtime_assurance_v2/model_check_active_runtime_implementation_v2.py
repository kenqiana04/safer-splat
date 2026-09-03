#!/usr/bin/env python3
"""Bounded architecture check over the actual runtime transition objects."""

from __future__ import annotations

import ast
import json
import sys
from collections import deque
from pathlib import Path


PACKAGE = Path(__file__).resolve().parent
REPO = PACKAGE.parents[2]
EVIDENCE = PACKAGE / "implementation_evidence"
TRANSITIONS = EVIDENCE / "RUNTIME_TRANSITION_IMPLEMENTATION_MAP_V2.csv"
if str(REPO) not in sys.path:
    sys.path.insert(0, str(REPO))

from reproduction.runtime.active_runtime_assurance_v2.authority_registry import AuthorityRegistry
from reproduction.runtime.active_runtime_assurance_v2.plant_commit import LEGAL_ROLES, PlantCommitAdapter
from reproduction.runtime.active_runtime_assurance_v2.runtime_errors import CommitAuthorityViolation
from reproduction.runtime.active_runtime_assurance_v2.runtime_types import (
    ActionRole, DeadlineObservation, DeadlineStatus, RuntimeStateSnapshot, SupervisorDecision, make_action,
)
from reproduction.runtime.active_runtime_assurance_v2.supervisor import Supervisor, TransitionTable


def runtime_sources() -> list[Path]:
    return sorted(path for path in PACKAGE.glob("*.py") if path.name not in {Path(__file__).name, "validate_active_runtime_assurance_v2.py"})


def main() -> int:
    table = TransitionTable.from_csv(TRANSITIONS)
    checks: list[dict[str, object]] = []
    counterexamples: list[dict[str, object]] = []

    def record(name: str, passed: bool, evidence: object) -> None:
        checks.append({"check": name, "passed": passed, "evidence": evidence})
        if not passed:
            counterexamples.append({"check": name, "evidence": evidence})

    graph: dict[str, set[str]] = {}
    for rule in table.rules:
        graph.setdefault(rule.source_phase, set()).add(rule.destination_phase)
    reachable = {"START_ADMISSION"}
    queue = deque(reachable)
    while queue:
        source = queue.popleft()
        for destination in graph.get(source, set()):
            if destination not in reachable:
                reachable.add(destination)
                queue.append(destination)
    record("actual_transition_table_is_43_exactly_once", len(table.rules) == 43 and len(table.by_id) == 43, len(table.rules))
    record("commit_is_reachable_only_at_commit_phase", "COMMIT" in reachable and all(rule.destination_phase == "COMMIT" for rule in table.rules if rule.commit_allowed), [rule.rule_id for rule in table.rules if rule.commit_allowed])
    record("proposal_has_no_direct_commit", all(rule.destination_phase != "COMMIT" for rule in table.rules if rule.source_phase == "PRIMARY_PROPOSAL"), [rule.rule_id for rule in table.rules if rule.source_phase == "PRIMARY_PROPOSAL"])
    record("l2_has_no_direct_commit", all(rule.destination_phase != "COMMIT" for rule in table.rules if rule.source_phase == "L2"), [rule.rule_id for rule in table.rules if rule.source_phase == "L2"])
    record("l3_has_no_direct_commit", all(rule.destination_phase != "COMMIT" for rule in table.rules if rule.source_phase == "L3"), [rule.rule_id for rule in table.rules if rule.source_phase == "L3"])
    record("alternative_provider_has_no_direct_commit", all(rule.destination_phase != "COMMIT" for rule in table.rules if rule.source_phase == "ALT_SEARCH"), [rule.rule_id for rule in table.rules if rule.source_phase == "ALT_SEARCH"])
    record("terminal_membership_has_no_unsupervised_commit", table.by_id["TERM_ELIGIBLE"].action_authority == "CERTIFIED_TERMINAL", table.by_id["TERM_ELIGIBLE"].action_authority)

    dynamics_owners = []
    arbitration_owners = []
    oracle_imports = []
    for path in runtime_sources():
        text = path.read_text(encoding="utf-8")
        tree = ast.parse(text, filename=str(path))
        if "double_integrator_dynamics" in text:
            dynamics_owners.append(path.name)
        for node in ast.walk(tree):
            if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)) and node.name == "arbitrate":
                arbitration_owners.append(path.name)
            if isinstance(node, ast.Import):
                modules = [alias.name for alias in node.names]
            elif isinstance(node, ast.ImportFrom):
                modules = [node.module or ""]
            else:
                continue
            if any("evaluation_oracle" in module or "outcome_calculator" in module for module in modules):
                oracle_imports.append(f"{path.name}:{node.lineno}")
    record("sole_plant_owner", dynamics_owners == ["plant_commit.py"], dynamics_owners)
    record("sole_selection_owner", arbitration_owners == ["supervisor.py"], arbitration_owners)
    record("no_oracle_feedback_edge", not oracle_imports, oracle_imports)

    registry = AuthorityRegistry.frozen("map:test", "dt:test", "deadline:test")
    state = RuntimeStateSnapshot.create("trial", 0, (0, 0, 0, 0, 0, 0), (1, 0, 0, 0, 0, 0), "map:test", 0.05)
    supervisor = Supervisor(registry, table)
    plant_calls = {"count": 0}

    def transition(values, control, dt):
        plant_calls["count"] += 1
        return values

    plant = PlantCommitAdapter(registry, transition)
    deadline = DeadlineObservation(DeadlineStatus.OPEN, "ARBITRATION", 0.0, 1.0, "deadline:test")
    boundary = supervisor.arbitrate(state, None, None, None, False, None, deadline)
    boundary_action = make_action((0, 0, 0), ActionRole.ASSURANCE_BOUNDARY_NO_ACTION, "boundary")
    rejected = False
    try:
        plant.commit(boundary, state, boundary_action)
    except CommitAuthorityViolation:
        rejected = True
    record("boundary_cannot_call_plant", rejected and plant_calls["count"] == 0, plant_calls["count"])

    invalid_backup = supervisor.make_retained_backup_action((0, 0, 0), "invalid-token")
    invalid_decision = supervisor.arbitrate(state, None, None, invalid_backup, False, None, deadline)
    record("invalid_token_cannot_execute", not invalid_decision.allows_commit and invalid_decision.selected_action is None, invalid_decision.rule_id)

    selected = make_action((0.01, 0, 0), ActionRole.PRIMARY_NAVIGATION, "candidate")
    mismatched = make_action((0.02, 0, 0), ActionRole.PRIMARY_NAVIGATION, "other")
    decision = SupervisorDecision(0, state.identity, selected, True, "NAV", "ARB_NAV")
    mismatch_rejected = False
    try:
        plant.commit(decision, state, mismatched)
    except CommitAuthorityViolation:
        mismatch_rejected = True
    record("selected_executed_mismatch_impossible", mismatch_rejected and plant_calls["count"] == 0, plant_calls["count"])
    record("every_executable_role_is_frozen_allowed_role", LEGAL_ROLES == {ActionRole.PRIMARY_NAVIGATION, ActionRole.ALTERNATIVE_NAVIGATION, ActionRole.RETAINED_BACKUP, ActionRole.CERTIFIED_TERMINAL}, sorted(role.value for role in LEGAL_ROLES))

    result = {
        "schema": "ACTIVE_RUNTIME_IMPLEMENTATION_MODEL_CHECK_V2",
        "uses_actual_runtime_transition_objects": True,
        "transition_rule_count": len(table.rules),
        "reachable_runtime_phases": sorted(reachable),
        "check_count": len(checks),
        "counterexample_count": len(counterexamples),
        "checks": checks,
        "verdict": "PASS_ACTIVE_RUNTIME_IMPLEMENTATION_MODEL_CHECK" if not counterexamples else "FAIL_ACTIVE_RUNTIME_IMPLEMENTATION_MODEL_CHECK",
    }
    EVIDENCE.mkdir(parents=True, exist_ok=True)
    (EVIDENCE / "active_runtime_implementation_model_check.json").write_text(json.dumps(result, indent=2, sort_keys=True) + "\n", encoding="utf-8", newline="\n")
    (EVIDENCE / "active_runtime_implementation_counterexamples.json").write_text(json.dumps({"schema": "ACTIVE_RUNTIME_IMPLEMENTATION_COUNTEREXAMPLES_V2", "counterexample_count": len(counterexamples), "counterexamples": counterexamples}, indent=2, sort_keys=True) + "\n", encoding="utf-8", newline="\n")
    print(result["verdict"])
    print(f"transition_rules={len(table.rules)} counterexamples={len(counterexamples)}")
    return 0 if not counterexamples else 1


if __name__ == "__main__":
    raise SystemExit(main())
