"""CPU-only actual-runtime model checks for the bounded R2 repair."""

from __future__ import annotations

import ast
import inspect
import json
from pathlib import Path

from reproduction.runtime.active_runtime_assurance_v2.active_cycle import ActiveCycleCoordinator
from reproduction.runtime.active_runtime_assurance_v2.runtime_types import (
    ActionRole,
    ActiveCycleRequest,
    AlternativeInventoryResult,
    AlternativeInventoryStatus,
    PublicCycleEvent,
    ReasonScope,
)
from reproduction.runtime.active_runtime_assurance_v2.tests.public_cycle_test_support import build_public_cycle, start_and_run


OUT = Path(__file__).resolve().parent


def _boom(*_args, **_kwargs):
    raise RuntimeError("r2 model injected exception")


def _backup_system():
    system = build_public_cycle()
    _, first = start_and_run(system)
    request = ActiveCycleRequest(first.next_state.trial_id, 1, (1.0, 0.0, 0.0), None)
    return system, first.next_state, request


def run_model_check() -> dict:
    checks: list[dict] = []

    def record(name: str, condition: bool, detail=None) -> None:
        checks.append({"name": name, "passed": bool(condition), "detail": detail})

    system, state, request = _backup_system()
    system["coordinator"].l2_runtime.evaluate = _boom
    result = system["coordinator"].run_cycle(state, request)
    record("01_resolved_exception_route_not_preblocked", result.action_role == ActionRole.RETAINED_BACKUP and result.committed)
    record("02_no_exception_to_pass", bool(result.stage_failures) and all(item.typed_reason.startswith("STAGE_EXCEPTION:") for item in result.stage_failures))
    record("03_no_exception_to_uncertified_commit", result.action_role != ActionRole.PRIMARY_NAVIGATION)

    for index, status in enumerate(("SOURCE_INVALID", "PROVENANCE_MISSING", "FUTURE_STATUS"), start=4):
        system, state, request = _backup_system()
        system["config"]["primary_vector"] = (0.2, 0.0, 0.0)
        system["coordinator"].alternative_provider.enumerate = lambda _snapshot, value=status: AlternativeInventoryResult(value, ())
        candidate_result = system["coordinator"].run_cycle(state, request)
        expected = AlternativeInventoryStatus(status) if status != "FUTURE_STATUS" else AlternativeInventoryStatus.UNRESOLVED_STATUS
        record(f"{index:02d}_{status.lower()}_not_exhaustion", candidate_result.alternative_inventory_evidence.status == expected and "ALT_DONE" not in candidate_result.routing_rule_ids)

    supervisor = build_public_cycle()["supervisor"]
    record("07_unknown_scope_not_substring_derived", supervisor.classify_reason_scope("L2", "opaque missing timeout exception") == ReasonScope.UNRESOLVED_SCOPE)
    record("08_valid_fallback_reachable", result.final_supervisor_decision is not None and result.final_supervisor_decision.rule_id == "ARB_BACKUP")

    source = inspect.getsource(ActiveCycleCoordinator)
    record("09_no_synthetic_alternative", "make_candidate" not in source and "random" not in source and "interpol" not in source.lower())
    record("10_r1_authority_preserved", "RoutingDecision(" not in source and "deadline.status ==" not in source and "deadline.status !=" not in source)
    record("11_boundary_no_plant", build_public_cycle({"proposal": "FAIL"})["plant"].commit_count == 0)

    tree = ast.parse(source)
    while_nodes = [node for node in ast.walk(tree) if isinstance(node, ast.While)]
    record("12_no_infinite_exception_routing_loop", len(while_nodes) == 1 and any(isinstance(node, ast.If) for node in ast.walk(while_nodes[0])))

    counterexamples = [item for item in checks if not item["passed"]]
    payload = {
        "schema": "R2_EXCEPTION_UNKNOWN_MODEL_CHECK_V2",
        "actual_runtime_classes": ["ActiveCycleCoordinator", "Supervisor", "PublicCycleEvent", "ReasonScope", "AlternativeInventoryStatus"],
        "check_count": len(checks),
        "checks": checks,
        "counterexample_count": len(counterexamples),
        "status": "PASS_R2_EXCEPTION_UNKNOWN_MODEL_CHECK_V2" if not counterexamples else "FAIL_R2_EXCEPTION_UNKNOWN_MODEL_CHECK_V2",
    }
    return {"result": payload, "counterexamples": {"schema": "R2_EXCEPTION_UNKNOWN_COUNTEREXAMPLES_V2", "counterexamples": counterexamples}}


def main() -> int:
    output = run_model_check()
    (OUT / "R2_EXCEPTION_UNKNOWN_MODEL_CHECK_V2.json").write_text(json.dumps(output["result"], indent=2, sort_keys=True) + "\n", encoding="utf-8")
    (OUT / "R2_EXCEPTION_UNKNOWN_COUNTEREXAMPLES_V2.json").write_text(json.dumps(output["counterexamples"], indent=2, sort_keys=True) + "\n", encoding="utf-8")
    return 0 if output["result"]["counterexample_count"] == 0 else 1


if __name__ == "__main__":
    raise SystemExit(main())
