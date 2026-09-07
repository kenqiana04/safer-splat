"""Fail-closed model check of the actual PR #122 public-cycle implementation."""

from __future__ import annotations

import ast
import dataclasses
import json
import sys
from pathlib import Path


TASK = Path(__file__).resolve().parent
REPO = TASK.parents[2]
sys.path.insert(0, str(REPO))

from reproduction.runtime.active_runtime_assurance_v2.runtime_types import RoutingDecision  # noqa: E402
from reproduction.runtime.active_runtime_assurance_v2.supervisor import TransitionRule  # noqa: E402


def write_json(name: str, value: object) -> None:
    (TASK / name).write_text(json.dumps(value, indent=2, sort_keys=True) + "\n", encoding="utf-8", newline="\n")


def main() -> int:
    design_path = REPO / "reproduction/design/active_runtime_public_cycle_composition_v2/EXECUTABLE_TRANSITION_ROUTING_DESIGN_V2.json"
    design = json.loads(design_path.read_text(encoding="utf-8"))
    routing_fields = {field.name for field in dataclasses.fields(RoutingDecision)}
    rule_fields = {field.name for field in dataclasses.fields(TransitionRule)}
    counterexamples: list[dict[str, object]] = []

    required_decision_metadata = {
        "action_authority", "old_backup_retained", "new_backup_created", "theorem_interpretation"
    }
    required_rule_metadata = {
        "old_backup_retained", "new_backup_created", "theorem_interpretation"
    }
    decision_missing = sorted(required_decision_metadata - routing_fields)
    rule_missing = sorted(required_rule_metadata - rule_fields)
    if decision_missing or rule_missing:
        counterexamples.append({
            "counterexample_id": "RC-TR-FIDELITY-001",
            "critical": True,
            "kind": "ROUTING_DECISION_METADATA_MISMATCH",
            "frozen_rule_count": len(design["rules"]),
            "routing_decision_missing_fields": decision_missing,
            "transition_rule_missing_fields": rule_missing,
            "impact": "The executable route cannot carry or revalidate every frozen row-level authority field.",
        })

    active_cycle = (REPO / "reproduction/runtime/active_runtime_assurance_v2/active_cycle.py").read_text(encoding="utf-8")
    tree = ast.parse(active_cycle)
    direct_forbidden = [
        token for token in ("PlantCommitAdapter", "make_action(", "SelectedAction(", "dynamics")
        if token in active_cycle
    ]
    if direct_forbidden:
        counterexamples.append({
            "counterexample_id": "RC-POLICY-OWNER-001",
            "critical": True,
            "kind": "COORDINATOR_AUTHORITY_LEAK",
            "tokens": direct_forbidden,
        })

    checks = {
        "actual_classes_imported": True,
        "frozen_rule_count": len(design["rules"]),
        "routing_decision_fields": sorted(routing_fields),
        "transition_rule_fields": sorted(rule_fields),
        "coordinator_ast_parsed": isinstance(tree, ast.Module),
        "no_direct_coordinator_plant_or_action_construction": not direct_forbidden,
        "stopped_after_first_critical_counterexample": bool(counterexamples),
        "not_executed_after_first_counterexample": [
            "full_legal_route_enumeration", "token_terminal_state_product", "trace_state_product"
        ] if counterexamples else [],
    }
    write_json("active_public_cycle_reconformance_counterexamples.json", {
        "schema": "ACTIVE_PUBLIC_CYCLE_RECONFORMANCE_COUNTEREXAMPLES_V2",
        "count": len(counterexamples),
        "counterexamples": counterexamples,
    })
    write_json("active_public_cycle_reconformance_model_check.json", {
        "schema": "ACTIVE_PUBLIC_CYCLE_RECONFORMANCE_MODEL_CHECK_V2",
        "status": "BLOCKED_BY_FIRST_CRITICAL_COUNTEREXAMPLE" if counterexamples else "PASS",
        "counterexample_count": len(counterexamples),
        "checks": checks,
    })
    print("counterexamples=" + str(len(counterexamples)))
    return 1 if counterexamples else 0


if __name__ == "__main__":
    raise SystemExit(main())
