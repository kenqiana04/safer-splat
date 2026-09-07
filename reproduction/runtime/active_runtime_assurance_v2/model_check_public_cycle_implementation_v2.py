from __future__ import annotations

import ast
import csv
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[3]))

from reproduction.runtime.active_runtime_assurance_v2.runtime_types import (
    ActionRole,
    ActiveCycleRequest,
    CandidateIdentity,
    CandidateRole,
    CertificateStatus,
    DeadlineObservation,
    DeadlineStatus,
    PublicCycleEvent,
    RouteResolutionStatus,
    RuntimePhase,
    RuntimeRoutingContext,
)
from reproduction.runtime.active_runtime_assurance_v2.supervisor import TransitionTable
from reproduction.runtime.active_runtime_assurance_v2.tests.public_cycle_test_support import TRANSITION_TABLE, build_public_cycle, start_and_run


PACKAGE = Path(__file__).resolve().parent
EVIDENCE = PACKAGE / "public_cycle_implementation_evidence"


def routing_context(row: dict[str, str]) -> RuntimeRoutingContext:
    requirement = row["deadline_requirement"]
    deadline = DeadlineStatus.WARNING if requirement == "GUARD_OR_EXPIRED" else DeadlineStatus.OPEN
    role = None
    available = False
    if row["candidate_requirement"] in {"PRIMARY", "PRIMARY_OR_ALTERNATIVE"}:
        role, available = CandidateRole.PRIMARY, True
    elif row["candidate_requirement"] == "ALTERNATIVE":
        role, available = CandidateRole.ALTERNATIVE, True
    backup_present = row["retained_backup_requirement"] == "VALID"
    backup_valid = backup_present
    alternative = row["rule_id"].endswith("_ALT")
    navigation_ready = row["rule_id"] == "ARB_NAV"
    terminal_evaluated = row["rule_id"] in {"ARB_TERMINAL", "ARB_BOUNDARY"}
    terminal_ready = row["rule_id"] == "ARB_TERMINAL"
    if row["rule_id"] == "ARB_BACKUP":
        backup_present = backup_valid = True
    if row["rule_id"] == "ARB_EVAL_TERMINAL":
        terminal_evaluated = terminal_ready = False
    if row["rule_id"] == "ARB_BOUNDARY":
        terminal_evaluated, terminal_ready = True, False
    return RuntimeRoutingContext(
        RuntimePhase(row["source_phase"]),
        DeadlineObservation(deadline, row["source_phase"], 0.0, 1.0, "deadline:model-check"),
        "transition:model-check",
        role,
        CandidateIdentity("candidate:model-check") if available else None,
        available,
        backup_present,
        backup_valid,
        alternative,
        navigation_ready,
        terminal_evaluated,
        terminal_ready,
        row["reason_scope"],
    )


def main() -> None:
    counterexamples: list[dict[str, str]] = []
    checks: list[dict[str, object]] = []
    table = TransitionTable.from_csv(TRANSITION_TABLE)
    with TRANSITION_TABLE.open(encoding="utf-8", newline="") as handle:
        rows = list(csv.DictReader(handle))
    for row in rows:
        decision = table.resolve(PublicCycleEvent(row["observation/result"]), routing_context(row))
        passed = decision.status == RouteResolutionStatus.RESOLVED and decision.rule_id == row["rule_id"]
        checks.append({"check": "route:" + row["rule_id"], "passed": passed})
        if not passed:
            counterexamples.append({"check": "route:" + row["rule_id"], "observed": decision.reason})

    scenarios = (
        ("normal_navigation", {}),
        ("c0_fail_boundary", {"primary_vector": (0.2, 0.0, 0.0)}),
        ("l2_fail_boundary", {"l2": CertificateStatus.FAIL}),
        ("l3_fail_boundary", {"l3": CertificateStatus.FAIL}),
        ("no_primary_boundary", {"proposal": "FAIL"}),
        ("terminal_commit", {"proposal": "FAIL", "terminal_member": True, "terminal": CertificateStatus.PASS}),
    )
    for name, config in scenarios:
        system = build_public_cycle(config)
        _, result = start_and_run(system)
        legal = (result.committed and result.action_role in {ActionRole.PRIMARY_NAVIGATION, ActionRole.ALTERNATIVE_NAVIGATION, ActionRole.RETAINED_BACKUP, ActionRole.CERTIFIED_TERMINAL}) or (not result.committed and result.boundary and system["plant"].commit_count == 0)
        checks.append({"check": name, "passed": legal})
        if not legal:
            counterexamples.append({"check": name, "observed": result.typed_stop_or_failure_reason})

    system = build_public_cycle()
    _, first = start_and_run(system)
    system["config"]["proposal"] = "FAIL"
    backup = system["coordinator"].run_cycle(first.next_state, ActiveCycleRequest(first.next_state.trial_id, 1, (1.0, 0.0, 0.0), None))
    backup_ok = backup.action_role == ActionRole.RETAINED_BACKUP and backup.committed
    checks.append({"check": "valid_backup_commit", "passed": backup_ok})
    if not backup_ok:
        counterexamples.append({"check": "valid_backup_commit", "observed": backup.typed_stop_or_failure_reason})

    source = (PACKAGE / "active_cycle.py").read_text(encoding="utf-8")
    tree = ast.parse(source)
    called = {node.func.attr for node in ast.walk(tree) if isinstance(node, ast.Call) and isinstance(node.func, ast.Attribute)}
    static = {
        "route_between_stages": "route_transition" in source,
        "final_arbitration": "arbitrate" in called,
        "runner_commit_reused": "commit_active_decision" in called,
        "no_direct_plant_commit": "plant_commit.commit" not in source,
        "no_candidate_action_construction": "make_action" not in source and "SupervisorDecision(" not in source,
        "no_oracle_edge": "oracle" not in source.lower(),
        "no_direct_dynamics_edge": "import dynamics" not in source.lower(),
        "no_synthetic_alternative": all(token not in source.lower() for token in ("perturb", "interpolat", "random")),
        "no_duplicate_token_handoff": all(token not in called for token in ("prepare", "activate_after_navigation_commit", "consume_after_backup_commit")),
        "no_duplicate_trace_append": "trace_writer.append" not in source,
    }
    for name, passed in static.items():
        checks.append({"check": name, "passed": passed})
        if not passed:
            counterexamples.append({"check": name, "observed": "static implementation edge"})

    payload = {
        "schema": "PUBLIC_CYCLE_IMPLEMENTATION_MODEL_CHECK_V2",
        "actual_implementation": True,
        "transition_rules_resolved": sum(1 for item in checks if str(item["check"]).startswith("route:") and item["passed"]),
        "transition_rules_total": 43,
        "checks": checks,
        "counterexample_count": len(counterexamples),
        "status": "PASS_PUBLIC_CYCLE_IMPLEMENTATION_MODEL_CHECK" if not counterexamples else "BLOCKED_PUBLIC_CYCLE_IMPLEMENTATION_MODEL_CHECK",
    }
    EVIDENCE.mkdir(parents=True, exist_ok=True)
    (EVIDENCE / "public_cycle_implementation_model_check.json").write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8", newline="\n")
    (EVIDENCE / "public_cycle_implementation_counterexamples.json").write_text(json.dumps({"counterexamples": counterexamples}, indent=2, sort_keys=True) + "\n", encoding="utf-8", newline="\n")
    print(payload["status"])
    if counterexamples:
        raise SystemExit(1)


if __name__ == "__main__":
    main()
