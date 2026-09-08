"""Execute the complete independent CPU-only post-R2 conformance matrix."""

from __future__ import annotations

import ast
import csv
import hashlib
import inspect
import json
import textwrap
from dataclasses import asdict
from pathlib import Path
from typing import Callable

from reproduction.runtime.active_runtime_assurance_v2.active_cycle import (
    ActiveCycleCoordinator,
    PublicCycleStateError,
)
from reproduction.runtime.active_runtime_assurance_v2.active_runner import ActiveRunner
from reproduction.runtime.active_runtime_assurance_v2.backup_token_store import BackupTokenStore
from reproduction.runtime.active_runtime_assurance_v2.deadline_runtime import RuntimeDeadlineProfile
from reproduction.runtime.active_runtime_assurance_v2.runtime_errors import DeadlineProfileRequired
from reproduction.runtime.active_runtime_assurance_v2.runtime_types import (
    ActionRole,
    ActiveCycleRequest,
    ActiveTrialContext,
    AlternativeInventoryStatus,
    CandidateRole,
    CertificateStatus,
    DeadlineStatus,
    PublicCycleEvent,
    PublicCyclePhase,
    ReasonScope,
    RouteResolutionStatus,
    RuntimeMode,
    RuntimePhase,
    RuntimeRoutingContext,
    TokenLifecycle,
    make_action,
)
from reproduction.runtime.active_runtime_assurance_v2.supervisor import Supervisor, TransitionTable
from reproduction.runtime.active_runtime_assurance_v2.tests.helpers import snapshot

from reproduction.validation.revalidate_active_runtime_contract_conformance_v2_post_r2.tests._support import (
    TRANSITION_CSV,
    ambiguous_table,
    backup_system,
    boom,
    build_public_cycle,
    context_for_row,
    lawful_alternative,
    set_provider_status,
    stage_exception_system,
    start_and_run,
)


TASK = Path(__file__).resolve().parent
REPO = TASK.parents[2]
Scenario = tuple[str, str, Callable[[], dict[str, object]]]


def outcome(passed: bool, **detail: object) -> dict[str, object]:
    return {"passed": bool(passed), **detail}


def route_row(row: dict[str, str]) -> dict[str, object]:
    system = build_public_cycle()
    table = system["supervisor"].transition_table
    context = context_for_row(row, system["registry"].transition_table_identity)
    decision = table.resolve(PublicCycleEvent(row["observation/result"]), context)
    checks = {
        "rule_id": decision.rule_id == row["rule_id"],
        "source_phase": decision.source_phase.value == row["source_phase"],
        "destination_phase": decision.destination_phase.value == row["destination_phase"],
        "commit_allowed": decision.commit_allowed == (row["commit_allowed"].lower() == "true"),
        "action_authority": decision.action_authority == row["action_authority"],
        "old_backup_retained": decision.old_backup_retained == (row["old_backup_retained"].lower() == "true"),
        "new_backup_created": decision.new_backup_created == (row["new_backup_created"].lower() == "true"),
        "theorem_interpretation": decision.theorem_interpretation == row["theorem_interpretation"],
        "reason_scope": decision.reason_scope == row["reason_scope"],
        "guard": decision.guard == row["guard"],
    }
    return outcome(all(checks.values()), expected_rule=row["rule_id"], observed_rule=decision.rule_id, checks=checks)


def missing_route() -> dict[str, object]:
    system = build_public_cycle()
    context = RuntimeRoutingContext(
        RuntimePhase.C0,
        system["coordinator"].deadline_tracker.observe("fixture") if system["coordinator"].deadline_tracker._start is not None else None,
        system["registry"].transition_table_identity,
    )
    if context.deadline is None:
        system["coordinator"].deadline_tracker.start()
        context = RuntimeRoutingContext(RuntimePhase.C0, system["coordinator"].deadline_tracker.observe("fixture"), system["registry"].transition_table_identity)
    decision = system["supervisor"].route_transition(PublicCycleEvent.COMMIT_FAILURE, context)
    return outcome(decision.status == RouteResolutionStatus.BLOCKED_MISSING, status=decision.status.value)


def ambiguous_route() -> dict[str, object]:
    system = build_public_cycle()
    original = system["supervisor"].transition_table
    row = next(r for r in csv.DictReader(TRANSITION_CSV.open(encoding="utf-8", newline="")) if r["rule_id"] == "C0_PASS")
    table = ambiguous_table(original, list(original.by_id).index("C0_PASS"))
    decision = table.resolve(PublicCycleEvent.C0_PASS, context_for_row(row, system["registry"].transition_table_identity))
    return outcome(decision.status == RouteResolutionStatus.BLOCKED_AMBIGUOUS, status=decision.status.value)


def normal_primary() -> dict[str, object]:
    system = build_public_cycle()
    start, result = start_and_run(system)
    expected = [
        PublicCyclePhase.CYCLE_BEGIN,
        PublicCyclePhase.L1_IMMEDIATE_CERTIFICATION,
        PublicCyclePhase.PRIMARY_PROPOSAL,
        PublicCyclePhase.PRIMARY_C0,
        PublicCyclePhase.PRIMARY_L2,
        PublicCyclePhase.PRIMARY_L3,
        PublicCyclePhase.BACKUP_VALIDATION,
        PublicCyclePhase.ARBITRATION,
        PublicCyclePhase.COMMIT,
        PublicCyclePhase.TRACE_APPEND,
        PublicCyclePhase.CYCLE_COMPLETE,
    ]
    passed = (
        start.ready
        and result.committed
        and result.action_role == ActionRole.PRIMARY_NAVIGATION
        and list(result.phase_history) == expected
        and system["counters"]["l1"] == 1
        and system["counters"]["bind"] == 1
        and system["plant"].commit_count == 1
        and len(system["trace_writer"].records) == 1
        and system["token_store"].current() is not None
    )
    return outcome(passed, action_role=result.action_role.value, phases=[x.value for x in result.phase_history], counters=system["counters"])


def backup_fallback(source: str = "L2_FAIL") -> dict[str, object]:
    system, state, request = backup_system()
    if source == "L1_FAIL":
        system["config"]["l1"] = CertificateStatus.FAIL
    elif source == "L2_FAIL":
        system["config"]["l2"] = CertificateStatus.FAIL
    elif source == "L3_FAIL":
        system["config"]["l3"] = CertificateStatus.FAIL
    result = system["coordinator"].run_cycle(state, request)
    token = system["token_store"].current()
    return outcome(
        result.committed and result.action_role == ActionRole.RETAINED_BACKUP and token is not None and token.cursor == 1,
        source=source,
        action_role=None if result.action_role is None else result.action_role.value,
        cursor=None if token is None else token.cursor,
    )


def terminal_fallback() -> dict[str, object]:
    system = build_public_cycle({"proposal": "FAIL", "terminal_member": True, "terminal": CertificateStatus.PASS})
    start, result = start_and_run(system)
    return outcome(start.ready and result.committed and result.action_role == ActionRole.CERTIFIED_TERMINAL and system["counters"]["terminal"] == 1, calls=system["counters"]["terminal"])


def boundary_path() -> dict[str, object]:
    system = build_public_cycle({"proposal": "FAIL"})
    _, result = start_and_run(system)
    return outcome(result.boundary and not result.committed and result.next_state is None and system["plant"].commit_count == 0 and len(system["trace_writer"].records) == 1, trace_count=len(system["trace_writer"].records))


def expired_backup() -> dict[str, object]:
    system, state, request = backup_system()
    system["clock"].advance(10.0)
    system["config"]["l1"] = CertificateStatus.FAIL
    result = system["coordinator"].run_cycle(state, request)
    return outcome(result.committed and result.action_role == ActionRole.RETAINED_BACKUP and all(obs.status == DeadlineStatus.EXPIRED for obs in result.deadline_observations), action_role=result.action_role.value)


def global_unknown_boundary() -> dict[str, object]:
    system = build_public_cycle({"l1": CertificateStatus.UNKNOWN})
    _, result = start_and_run(system)
    return outcome(result.boundary and not result.committed and bool(result.stage_failures) and result.stage_failures[-1].reason_scope == ReasonScope.UNRESOLVED_SCOPE, scope=result.stage_failures[-1].reason_scope.value)


def exception_case(stage: str) -> dict[str, object]:
    system, _, result = stage_exception_system(stage)
    failure = result.stage_failures[-1]
    if stage in {"TERMINAL_EVALUATION", "ARBITRATION"}:
        fallback_ok = result.boundary and not result.committed and system["plant"].commit_count == 0
    else:
        fallback_ok = result.committed and result.action_role == ActionRole.RETAINED_BACKUP
    return outcome(
        fallback_ok and failure.source_phase.value == stage and failure.reason_scope == ReasonScope.INFRASTRUCTURE_HEALTH,
        stage=stage,
        action_role=None if result.action_role is None else result.action_role.value,
        failure=asdict(failure),
    )


def l3_exception_terminal() -> dict[str, object]:
    system = build_public_cycle({"terminal_member": True, "terminal": CertificateStatus.PASS})
    system["coordinator"].l3_runtime.evaluate = boom()
    _, result = start_and_run(system)
    return outcome(result.committed and result.action_role == ActionRole.CERTIFIED_TERMINAL, action_role=result.action_role.value)


def provider_status(status: str) -> dict[str, object]:
    system, state, request = backup_system()
    system["config"]["primary_vector"] = (0.2, 0.0, 0.0)
    candidates = (lawful_alternative(state),) if status == "ALT_AVAILABLE" else ()
    set_provider_status(system, status, candidates)
    result = system["coordinator"].run_cycle(state, request)
    expected = AlternativeInventoryStatus(status) if status in {x.value for x in AlternativeInventoryStatus} else AlternativeInventoryStatus.UNRESOLVED_STATUS
    exhausted = "ALT_DONE" in result.routing_rule_ids
    passed = result.alternative_inventory_evidence is not None and result.alternative_inventory_evidence.status == expected and exhausted == (status == "NO_ALTERNATIVE_AVAILABLE")
    if status == "ALT_AVAILABLE":
        passed = passed and result.action_role == ActionRole.ALTERNATIVE_NAVIGATION and system["counters"]["l1"] == 2 and system["counters"]["bind"] == 3
    return outcome(passed, status=status, normalized=expected.value, exhausted=exhausted, action_role=None if result.action_role is None else result.action_role.value)


def start_case(status: CertificateStatus) -> dict[str, object]:
    system = build_public_cycle({"start": status})
    start = system["coordinator"].start_trial(system["state"], system["trial"])
    passed = (start.ready and not start.blocked) if status == CertificateStatus.PASS else (start.blocked and not start.ready and system["plant"].commit_count == 0)
    if status == CertificateStatus.UNKNOWN:
        passed = passed and start.admission_status == CertificateStatus.UNKNOWN
    return outcome(passed, status=status.value, ready=start.ready, blocked=start.blocked)


def identity_mismatch() -> dict[str, object]:
    system = build_public_cycle()
    bad = ActiveTrialContext("different", system["state"].map_identity)
    try:
        system["coordinator"].start_trial(system["state"], bad)
    except PublicCycleStateError as exc:
        return outcome(str(exc) == "TRIAL_START_IDENTITY_MISMATCH", reason=str(exc))
    return outcome(False, reason="not blocked")


def missing_deadline_profile() -> dict[str, object]:
    state = snapshot()
    from reproduction.runtime.active_runtime_assurance_v2.authority_registry import AuthorityRegistry
    from reproduction.runtime.active_runtime_assurance_v2.plant_commit import PlantCommitAdapter
    from reproduction.runtime.active_runtime_assurance_v2.trace_writer import TraceWriter

    registry = AuthorityRegistry.frozen(state.map_identity, "dt:0.05", None)
    runner = ActiveRunner(RuntimeMode.ACTIVE_RUNTIME_ON, registry, Supervisor(registry), PlantCommitAdapter(registry, lambda s, u, dt: s), BackupTokenStore(), TraceWriter(state.trial_id), None)
    try:
        runner.startup()
    except DeadlineProfileRequired as exc:
        return outcome(str(exc) == "DEADLINE_PROFILE_REQUIRED", reason=str(exc))
    return outcome(False, reason="startup accepted")


def reason_scope(reason: str, expected: ReasonScope) -> dict[str, object]:
    observed = build_public_cycle()["supervisor"].classify_reason_scope("L2", reason)
    return outcome(observed == expected, reason=reason, observed=observed.value, expected=expected.value)


def terminal_route_derived(kind: str) -> dict[str, object]:
    if kind == "normal":
        system = build_public_cycle()
        _, result = start_and_run(system)
        return outcome(result.action_role == ActionRole.PRIMARY_NAVIGATION and system["counters"]["terminal"] == 0, calls=system["counters"]["terminal"])
    if kind == "backup":
        system, state, request = backup_system()
        system["config"]["l1"] = CertificateStatus.FAIL
        result = system["coordinator"].run_cycle(state, request)
        return outcome(result.action_role == ActionRole.RETAINED_BACKUP and system["counters"]["terminal"] == 0, calls=system["counters"]["terminal"])
    system = build_public_cycle({"proposal": "FAIL"})
    captured = []
    original = system["coordinator"].terminal_runtime.evaluate
    def wrapped(snap, fallback_context, expected_ref=None):
        captured.append(fallback_context)
        return original(snap, fallback_context, expected_ref)
    system["coordinator"].terminal_runtime.evaluate = wrapped
    _, result = start_and_run(system)
    return outcome(captured == [True] and "ARB_EVAL_TERMINAL" in result.routing_rule_ids, fallback_context=captured, routes=list(result.routing_rule_ids))


def backup_state_distinction(state_name: str) -> dict[str, object]:
    system = build_public_cycle()
    table = system["supervisor"].transition_table
    row = next(r for r in csv.DictReader(TRANSITION_CSV.open(encoding="utf-8", newline="")) if r["rule_id"] == "ARB_BOUNDARY")
    base = context_for_row(row, system["registry"].transition_table_identity)
    context = RuntimeRoutingContext(
        source_phase=base.source_phase,
        deadline=base.deadline,
        authority_identity=base.authority_identity,
        retained_backup_present=state_name != "NONE",
        retained_backup_valid=False,
        terminal_evaluated=True,
        terminal_evidence_eligible=False,
        backup_state=state_name,
    )
    decision = table.resolve(PublicCycleEvent.ARBITRATE, context)
    return outcome(decision.rule_id == "ARB_BOUNDARY" and context.backup_state == state_name, state=state_name, rule=decision.rule_id)


def trace_exactly_once(role: str) -> dict[str, object]:
    if role == "nav":
        system = build_public_cycle()
        _, result = start_and_run(system)
    elif role == "backup":
        system, state, request = backup_system()
        system["config"]["l1"] = CertificateStatus.FAIL
        before = len(system["trace_writer"].records)
        result = system["coordinator"].run_cycle(state, request)
        return outcome(len(system["trace_writer"].records) == before + 1 and result.action_role == ActionRole.RETAINED_BACKUP, role=role)
    elif role == "terminal":
        system = build_public_cycle({"proposal": "FAIL", "terminal_member": True, "terminal": CertificateStatus.PASS})
        _, result = start_and_run(system)
    else:
        system = build_public_cycle({"proposal": "FAIL"})
        _, result = start_and_run(system)
    return outcome(len(system["trace_writer"].records) == 1, role=role, count=len(system["trace_writer"].records), committed=result.committed)


def trace_fault(kind: str) -> dict[str, object]:
    if kind == "TRACE-F01":
        system = build_public_cycle({"proposal": "FAIL"})
        system["trace_writer"].append = boom("trace append failed before any plant side effect")
        try:
            start_and_run(system)
        except RuntimeError:
            return outcome(system["plant"].commit_count == 0, plant_count=system["plant"].commit_count, execution_fact="NO_ACTION_PATH")
        return outcome(False, reason="trace failure silently ignored")
    if kind == "TRACE-F02":
        system = build_public_cycle()
        system["trace_writer"].append = boom("trace append failed after plant")
        escaped = None
        try:
            start_and_run(system)
        except RuntimeError as exc:
            escaped = str(exc)
        # Frozen contract requires no untraced plant commit. Current execution
        # is a conformance failure if plant/token side effects occur without a trace.
        passed = system["plant"].commit_count == 0 or len(system["trace_writer"].records) == 1
        return outcome(passed, plant_count=system["plant"].commit_count, trace_count=len(system["trace_writer"].records), token_active=system["token_store"].current() is not None, escaped=escaped)
    system = build_public_cycle()
    _, result = start_and_run(system)
    system["trace_writer"].finalize = boom("trace finalize failure")
    escaped = None
    try:
        system["coordinator"].finalize_trial()
    except RuntimeError as exc:
        escaped = str(exc)
    # No frozen typed post-commit session state exists for finalize failure.
    passed = escaped is None
    return outcome(passed, prior_commit=result.committed, prior_trace_count=len(system["trace_writer"].records), finalize_exception=escaped, session_status=system["coordinator"].session.status.value)


def bypass_preservation() -> dict[str, object]:
    source = textwrap.dedent(inspect.getsource(Supervisor.bypass_decision))
    normalized = ast.dump(ast.parse(source), include_attributes=False)
    body_sha = hashlib.sha256(source.encode()).hexdigest()
    normalized_sha = hashlib.sha256(normalized.encode()).hexdigest()
    expected_blob = "173837401de824fcdbdb8b5b7b9d4dfb8bb43037"
    actual_blob = __import__("subprocess").check_output(["git", "hash-object", str(REPO / "reproduction/runtime/active_runtime_assurance_v2/supervisor.py")], text=True).strip()
    return outcome(actual_blob == expected_blob, body_sha256=body_sha, normalized_ast_sha256=normalized_sha, supervisor_blob=actual_blob)


def numeric_authority() -> dict[str, object]:
    system = build_public_cycle()
    g = system["registry"].geometry
    a = system["registry"].actuator
    passed = g.controller_radius_m == 0.015 and g.certification_margin_m == 0.01 and g.certification_effective_radius_m == 0.025 and g.rho_seg == 0.0 and a.u_min == (-0.1, -0.1, -0.1) and a.u_max == (0.1, 0.1, 0.1)
    return outcome(passed, controller_radius=g.controller_radius_m, margin=g.certification_margin_m, effective_radius=g.certification_effective_radius_m, rho_seg=g.rho_seg, u_min=a.u_min, u_max=a.u_max)


def session_guard(kind: str) -> dict[str, object]:
    system = build_public_cycle()
    try:
        if kind == "before_start":
            system["coordinator"].run_cycle(system["state"], system["request"])
        elif kind == "double_start":
            system["coordinator"].start_trial(system["state"], system["trial"])
            system["coordinator"].start_trial(system["state"], system["trial"])
        else:
            system["coordinator"].start_trial(system["state"], system["trial"])
            bad = ActiveCycleRequest(system["state"].trial_id, 1, (1.0, 0.0, 0.0), None)
            system["coordinator"].run_cycle(system["state"], bad)
    except PublicCycleStateError as exc:
        return outcome(True, kind=kind, reason=str(exc))
    return outcome(False, kind=kind, reason="not blocked")


def scenario_definitions() -> list[Scenario]:
    scenarios: list[Scenario] = []
    with TRANSITION_CSV.open(encoding="utf-8", newline="") as handle:
        for row in csv.DictReader(handle):
            scenarios.append((f"ROUTE-{row['rule_id']}", "transition_43", lambda item=row: route_row(item)))
    scenarios.extend([
        ("ROUTE-MISSING", "exact_one", missing_route),
        ("ROUTE-AMBIGUOUS", "exact_one", ambiguous_route),
        ("E2E-01", "e2e_core", normal_primary),
        ("E2E-02", "e2e_core", lambda: backup_fallback("L2_FAIL")),
        ("E2E-03", "e2e_core", terminal_fallback),
        ("E2E-04", "e2e_core", boundary_path),
        ("E2E-05", "e2e_core", expired_backup),
        ("E2E-06", "e2e_core", global_unknown_boundary),
        ("E2E-07", "e2e_extended", lambda: exception_case("L2")),
        ("E2E-08", "e2e_extended", l3_exception_terminal),
        ("E2E-09", "e2e_extended", lambda: provider_status("SOURCE_INVALID")),
        ("E2E-10", "e2e_extended", lambda: provider_status("PROVENANCE_MISSING")),
        ("E2E-11", "e2e_extended", lambda: provider_status("NO_ALTERNATIVE_AVAILABLE")),
        ("E2E-12", "e2e_extended", lambda: provider_status("ALT_AVAILABLE")),
        ("START-PASS", "start_r0", lambda: start_case(CertificateStatus.PASS)),
        ("START-FAIL", "start_r0", lambda: start_case(CertificateStatus.FAIL)),
        ("START-UNKNOWN", "start_r0", lambda: start_case(CertificateStatus.UNKNOWN)),
        ("START-IDENTITY", "start_r0", identity_mismatch),
        ("START-DEADLINE-PROFILE", "start_r0", missing_deadline_profile),
        ("L1-FAIL-BACKUP", "fallback", lambda: backup_fallback("L1_FAIL")),
        ("L3-FAIL-BACKUP", "fallback", lambda: backup_fallback("L3_FAIL")),
        ("ALT-UNRESOLVED", "alternative", lambda: provider_status("FUTURE_UNEXPECTED_STATUS")),
        ("TERM-NORMAL-NOCALL", "terminal", lambda: terminal_route_derived("normal")),
        ("TERM-BACKUP-NOCALL", "terminal", lambda: terminal_route_derived("backup")),
        ("TERM-ROUTE-DERIVED", "terminal", lambda: terminal_route_derived("route")),
        ("BACKUP-NONE", "backup", lambda: backup_state_distinction("NONE")),
        ("BACKUP-INVALID", "backup", lambda: backup_state_distinction("INVALID")),
        ("BACKUP-EXHAUSTED", "backup", lambda: backup_state_distinction("EXHAUSTED")),
        ("TRACE-NAV", "trace", lambda: trace_exactly_once("nav")),
        ("TRACE-BACKUP", "trace", lambda: trace_exactly_once("backup")),
        ("TRACE-TERMINAL", "trace", lambda: trace_exactly_once("terminal")),
        ("TRACE-BOUNDARY", "trace", lambda: trace_exactly_once("boundary")),
        ("TRACE-F01", "trace_fault", lambda: trace_fault("TRACE-F01")),
        ("TRACE-F02", "trace_fault", lambda: trace_fault("TRACE-F02")),
        ("TRACE-F03", "trace_fault", lambda: trace_fault("TRACE-F03")),
        ("BYPASS-PRESERVATION", "bypass", bypass_preservation),
        ("NUMERIC-AUTHORITY", "numeric", numeric_authority),
        ("SESSION-BEFORE-START", "session", lambda: session_guard("before_start")),
        ("SESSION-DOUBLE-START", "session", lambda: session_guard("double_start")),
        ("SESSION-CYCLE-MISMATCH", "session", lambda: session_guard("cycle_mismatch")),
    ])
    for stage in ("L1", "PRIMARY_PROPOSAL", "C0", "L2", "L3", "ALT_SEARCH", "TERMINAL_EVALUATION", "ARBITRATION"):
        scenarios.append((f"EXC-{stage}", "exception", lambda value=stage: exception_case(value)))
    for reason, expected in (
        ("MAP_IDENTITY_MISMATCH", ReasonScope.GLOBAL_AUTHORITY_OR_EVIDENCE),
        ("CANDIDATE_NONFINITE_OR_WRONG_DIMENSION", ReasonScope.CANDIDATE_LOCAL_COMPUTATION),
        ("L2_BACKEND_EXCEPTION:RuntimeError", ReasonScope.INFRASTRUCTURE_HEALTH),
        ("opaque missing timeout exception unknown", ReasonScope.UNRESOLVED_SCOPE),
        ("timeout", ReasonScope.UNRESOLVED_SCOPE),
    ):
        scenarios.append((f"SCOPE-{len(scenarios):03d}", "reason_scope", lambda r=reason, e=expected: reason_scope(r, e)))
    return scenarios


def execute_all() -> dict[str, object]:
    results = []
    for scenario_id, domain, function in scenario_definitions():
        try:
            detail = function()
            passed = bool(detail.pop("passed"))
            results.append({"scenario_id": scenario_id, "domain": domain, "passed": passed, "detail": detail})
        except Exception as exc:
            results.append({"scenario_id": scenario_id, "domain": domain, "passed": False, "detail": {"exception": type(exc).__name__, "message": str(exc)}})
    return {
        "schema": "POST_R2_CONFORMANCE_SCENARIO_RESULTS_V2",
        "sweep_mode": "COMPLETE_INDEPENDENT_MATRIX",
        "scenario_count": len(results),
        "passed_count": sum(item["passed"] for item in results),
        "failed_count": sum(not item["passed"] for item in results),
        "results": results,
        "execution_counts": {"runtime_correction": 0, "real_active": 0, "gpu": 0, "smoke": 0, "scientific_oracle": 0, "official100": 0, "real_bypass": 0},
    }


def main() -> int:
    result = execute_all()
    (TASK / "POST_R2_CONFORMANCE_SCENARIO_RESULTS_V2.json").write_text(json.dumps(result, indent=2, sort_keys=True) + "\n", encoding="utf-8", newline="\n")
    return 0 if result["failed_count"] == 0 else 1


if __name__ == "__main__":
    raise SystemExit(main())

