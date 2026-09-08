"""Run the bounded CPU-only R2 adversarial probe matrix."""

from __future__ import annotations

import dataclasses
import ast
import hashlib
import inspect
import json
import textwrap
from pathlib import Path

from reproduction.runtime.active_runtime_assurance_v2.runtime_types import (
    ActionRole,
    ActiveCycleRequest,
    AlternativeInventoryResult,
    AlternativeInventoryStatus,
    CandidateRole,
    CertificateStatus,
    DeadlineObservation,
    DeadlineStatus,
    PublicCycleEvent,
    ReasonScope,
    RouteResolutionStatus,
    RuntimePhase,
    RuntimeRoutingContext,
    make_candidate,
)
from reproduction.runtime.active_runtime_assurance_v2.supervisor import TransitionTable
from reproduction.runtime.active_runtime_assurance_v2.tests.public_cycle_test_support import build_public_cycle, start_and_run


OUT = Path(__file__).resolve().parent


def boom(*_args, **_kwargs):
    raise RuntimeError("r2 injected probe exception")


def backup_system():
    system = build_public_cycle()
    _, first = start_and_run(system)
    request = ActiveCycleRequest(first.next_state.trial_id, 1, (1.0, 0.0, 0.0), None)
    return system, first.next_state, request


def stage_exception(stage: str) -> dict:
    if stage in {"TERMINAL_EVALUATION", "ARBITRATION"}:
        system = build_public_cycle({"proposal": "FAIL"})
        if stage == "TERMINAL_EVALUATION":
            system["coordinator"].terminal_runtime.evaluate = boom
        else:
            system["supervisor"].arbitrate = boom
        _, result = start_and_run(system)
        expected_source = stage
        passed = result.boundary and not result.committed and result.stage_failures[-1].source_phase.value == expected_source
    else:
        system, state, request = backup_system()
        mapping = {
            "L1": (system["coordinator"].l1_runtime, "evaluate_cycle"),
            "PRIMARY_PROPOSAL": (system["coordinator"].primary_proposal, "propose"),
            "C0": (system["coordinator"].c0_admission, "evaluate"),
            "L2": (system["coordinator"].l2_runtime, "evaluate"),
            "L3": (system["coordinator"].l3_runtime, "evaluate"),
            "ALT_SEARCH": (system["coordinator"].alternative_provider, "enumerate"),
        }
        if stage == "ALT_SEARCH":
            system["config"]["primary_vector"] = (0.2, 0.0, 0.0)
        owner, method = mapping[stage]
        setattr(owner, method, boom)
        result = system["coordinator"].run_cycle(state, request)
        passed = result.action_role == ActionRole.RETAINED_BACKUP and result.committed and result.stage_failures[-1].source_phase.value == stage
    return {"passed": passed, "committed": result.committed, "boundary": result.boundary, "action_role": None if result.action_role is None else result.action_role.value}


def fallback_probe(kind: str) -> dict:
    if kind in {"L1_BACKUP", "L2_BACKUP", "L3_BACKUP", "EXPIRED_BACKUP"}:
        system, state, request = backup_system()
        if kind == "EXPIRED_BACKUP":
            system["clock"].advance(10.0)
            stage = "L1"
        else:
            stage = kind.split("_", 1)[0]
        owner, method = {
            "L1": (system["coordinator"].l1_runtime, "evaluate_cycle"),
            "L2": (system["coordinator"].l2_runtime, "evaluate"),
            "L3": (system["coordinator"].l3_runtime, "evaluate"),
        }[stage]
        setattr(owner, method, boom)
        result = system["coordinator"].run_cycle(state, request)
        passed = result.action_role == ActionRole.RETAINED_BACKUP and result.committed
    elif kind == "TERMINAL":
        system = build_public_cycle({"terminal_member": True, "terminal": CertificateStatus.PASS})
        system["coordinator"].primary_proposal.propose = boom
        _, result = start_and_run(system)
        passed = result.action_role == ActionRole.CERTIFIED_TERMINAL and result.committed
    else:
        system = build_public_cycle()
        system["coordinator"].primary_proposal.propose = boom
        _, result = start_and_run(system)
        passed = result.boundary and not result.committed and system["plant"].commit_count == 0
    return {"passed": passed, "committed": result.committed, "boundary": result.boundary, "action_role": None if result.action_role is None else result.action_role.value}


def alternative_probe(status: str) -> dict:
    system, state, request = backup_system()
    system["config"]["primary_vector"] = (0.2, 0.0, 0.0)
    candidates = ()
    if status == "ALT_AVAILABLE":
        candidates = (make_candidate((0.01, 0.0, 0.0), CandidateRole.ALTERNATIVE, "SOURCE_NATIVE_EXISTING", "native-controller", state),)
    system["coordinator"].alternative_provider.enumerate = lambda _snapshot: AlternativeInventoryResult(status, candidates)
    result = system["coordinator"].run_cycle(state, request)
    expected = AlternativeInventoryStatus(status) if status in {item.value for item in AlternativeInventoryStatus} else AlternativeInventoryStatus.UNRESOLVED_STATUS
    exhaustion_allowed = status == "NO_ALTERNATIVE_AVAILABLE"
    passed = result.alternative_inventory_evidence.status == expected and (("ALT_DONE" in result.routing_rule_ids) == exhaustion_allowed)
    return {"passed": passed, "normalized_status": expected.value, "routing_rule_ids": list(result.routing_rule_ids), "action_role": None if result.action_role is None else result.action_role.value}


def scope_probe(stage: str, reason: str, expected: ReasonScope) -> dict:
    scope = build_public_cycle()["supervisor"].classify_reason_scope(stage, reason)
    return {"passed": scope == expected, "scope": scope.value, "expected": expected.value}


def simple_probe(kind: str) -> dict:
    if kind == "DEADLINE_OPEN":
        system = build_public_cycle()
        _, result = start_and_run(system)
        return {"passed": result.committed and result.action_role == ActionRole.PRIMARY_NAVIGATION}
    if kind == "DEADLINE_WARNING":
        system = build_public_cycle({"l1_advance": 9.2})
        _, result = start_and_run(system)
        return {"passed": not result.committed and result.boundary}
    if kind == "DEADLINE_EXPIRED":
        return fallback_probe("EXPIRED_BACKUP")
    if kind == "BACKUP_VALID":
        return fallback_probe("L2_BACKUP")
    if kind == "BACKUP_INVALID":
        system = build_public_cycle({"proposal": "FAIL"})
        _, result = start_and_run(system)
        return {"passed": result.action_role != ActionRole.RETAINED_BACKUP and not result.committed}
    if kind == "TERMINAL_READY":
        system = build_public_cycle({"proposal": "FAIL", "terminal_member": True, "terminal": CertificateStatus.PASS})
        _, result = start_and_run(system)
        return {"passed": result.action_role == ActionRole.CERTIFIED_TERMINAL}
    if kind == "TERMINAL_NOT_READY":
        system = build_public_cycle({"proposal": "FAIL"})
        _, result = start_and_run(system)
        return {"passed": result.boundary and not result.committed}
    if kind in {"ROUTE_MISSING", "ROUTE_AMBIGUOUS"}:
        system = build_public_cycle()
        context = RuntimeRoutingContext(RuntimePhase.C0, DeadlineObservation(DeadlineStatus.OPEN, "C0", 0.0, 1.0, "deadline:test"), system["registry"].transition_table_identity, CandidateRole.PRIMARY, None, True)
        table = system["supervisor"].transition_table
        if kind == "ROUTE_MISSING":
            decision = table.resolve(PublicCycleEvent.COMMIT_FAILURE, context)
            passed = decision.status == RouteResolutionStatus.BLOCKED_MISSING
        else:
            rules = list(table.rules)
            rules[-1] = dataclasses.replace(rules[13], rule_id=rules[-1].rule_id)
            decision = TransitionTable(tuple(rules)).resolve(PublicCycleEvent.C0_PASS, context)
            passed = decision.status == RouteResolutionStatus.BLOCKED_AMBIGUOUS
        return {"passed": passed, "status": decision.status.value}
    if kind == "BYPASS_STATIC":
        from reproduction.runtime.active_runtime_assurance_v2.supervisor import Supervisor
        tree = ast.parse(textwrap.dedent(inspect.getsource(Supervisor.bypass_decision)))
        digest = hashlib.sha256(ast.dump(tree.body[0], include_attributes=False).encode()).hexdigest()
        return {"passed": digest == "44e08edc0ea4c18d259d2e35faa4a4e022b4c7434162b30708ef412c6143adf0", "ast_sha256": digest}
    raise AssertionError(kind)


def main() -> int:
    probes = []
    for stage in ("L1", "PRIMARY_PROPOSAL", "C0", "L2", "L3", "ALT_SEARCH", "TERMINAL_EVALUATION", "ARBITRATION"):
        probes.append((f"EXC-{stage}", "stage_exception", lambda value=stage: stage_exception(value)))
    for kind in ("L1_BACKUP", "L2_BACKUP", "L3_BACKUP", "TERMINAL", "NO_FALLBACK", "EXPIRED_BACKUP"):
        probes.append((f"EX-FB-{kind}", "exception_fallback", lambda value=kind: fallback_probe(value)))
    for status in ("ALT_AVAILABLE", "NO_ALTERNATIVE_AVAILABLE", "SOURCE_INVALID", "PROVENANCE_MISSING", "FUTURE_STATUS"):
        probes.append((f"ALT-{status}", "alternative_status", lambda value=status: alternative_probe(value)))
    scope_cases = (
        ("GLOBAL", "L1", "MAP_IDENTITY_MISMATCH", ReasonScope.GLOBAL_AUTHORITY_OR_EVIDENCE),
        ("LOCAL", "C0", "CANDIDATE_NONFINITE_OR_WRONG_DIMENSION", ReasonScope.CANDIDATE_LOCAL_COMPUTATION),
        ("HEALTH", "L2", "L2_BACKEND_EXCEPTION:RuntimeError", ReasonScope.INFRASTRUCTURE_HEALTH),
        ("MISSING_TEXT", "L3", "opaque missing string", ReasonScope.UNRESOLVED_SCOPE),
        ("TIMEOUT_TEXT", "L2", "opaque timeout string", ReasonScope.UNRESOLVED_SCOPE),
    )
    for name, stage, reason, expected in scope_cases:
        probes.append((f"SCOPE-{name}", "reason_scope", lambda s=stage, r=reason, e=expected: scope_probe(s, r, e)))
    for kind in ("DEADLINE_OPEN", "DEADLINE_WARNING", "DEADLINE_EXPIRED", "BACKUP_VALID", "BACKUP_INVALID", "TERMINAL_READY", "TERMINAL_NOT_READY", "ROUTE_MISSING", "ROUTE_AMBIGUOUS", "BYPASS_STATIC"):
        probes.append((kind, "cross_contract", lambda value=kind: simple_probe(value)))

    results = []
    for probe_id, category, function in probes:
        try:
            detail = function()
            passed = bool(detail.pop("passed"))
            results.append({"probe_id": probe_id, "category": category, "passed": passed, "detail": detail})
        except Exception as exc:
            results.append({"probe_id": probe_id, "category": category, "passed": False, "detail": {"exception": type(exc).__name__, "message": str(exc)}})

    manifest = {"schema": "R2_PROBE_MANIFEST_V2", "probe_count": len(results), "cpu_only": True, "probes": [{"probe_id": item["probe_id"], "category": item["category"]} for item in results]}
    summary = {"schema": "R2_PROBE_RESULTS_V2", "probe_count": len(results), "passed_count": sum(item["passed"] for item in results), "failed_count": sum(not item["passed"] for item in results), "results": results}
    (OUT / "R2_PROBE_MANIFEST_V2.json").write_text(json.dumps(manifest, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    (OUT / "R2_PROBE_RESULTS_V2.json").write_text(json.dumps(summary, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    return 0 if summary["failed_count"] == 0 and summary["probe_count"] >= 32 else 1


if __name__ == "__main__":
    raise SystemExit(main())
