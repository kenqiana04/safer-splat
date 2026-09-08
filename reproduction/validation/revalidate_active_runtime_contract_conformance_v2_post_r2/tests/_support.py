from __future__ import annotations

from dataclasses import replace
from pathlib import Path

from reproduction.runtime.active_runtime_assurance_v2.runtime_types import (
    ActiveCycleRequest,
    AlternativeInventoryResult,
    CandidateIdentity,
    CandidateRole,
    DeadlineObservation,
    DeadlineStatus,
    PublicCycleEvent,
    RuntimePhase,
    RuntimeRoutingContext,
    make_candidate,
)
from reproduction.runtime.active_runtime_assurance_v2.supervisor import TransitionTable
from reproduction.runtime.active_runtime_assurance_v2.tests.public_cycle_test_support import (
    build_public_cycle,
    start_and_run,
)


REPO = Path(__file__).resolve().parents[4]
TRANSITION_CSV = REPO / "reproduction/specification/method_logic_closure_v2/STATE_TRANSITION_TABLE_V2.csv"


def boom(message: str = "post-r2 injected exception"):
    def _raise(*_args, **_kwargs):
        raise RuntimeError(message)

    return _raise


def backup_system():
    system = build_public_cycle()
    start, first = start_and_run(system)
    assert start.ready and first.committed and first.next_state is not None
    request = ActiveCycleRequest(first.next_state.trial_id, 1, (1.0, 0.0, 0.0), None)
    return system, first.next_state, request


def set_provider_status(system, status: str, candidates=()):
    system["coordinator"].alternative_provider.enumerate = (
        lambda _snapshot: AlternativeInventoryResult(status, tuple(candidates))
    )


def lawful_alternative(snapshot, vector=(0.01, 0.0, 0.0)):
    return make_candidate(
        vector,
        CandidateRole.ALTERNATIVE,
        "SOURCE_NATIVE_EXISTING",
        "native-controller",
        snapshot,
    )


def context_for_row(row: dict[str, str], authority: str) -> RuntimeRoutingContext:
    requirement = row["deadline_requirement"]
    deadline_status = (
        DeadlineStatus.WARNING if requirement == "GUARD_OR_EXPIRED" else DeadlineStatus.OPEN
    )
    candidate_requirement = row["candidate_requirement"]
    candidate_role = None
    candidate_available = candidate_requirement != "NONE"
    if candidate_requirement in {"PRIMARY", "PRIMARY_OR_ALTERNATIVE"}:
        candidate_role = CandidateRole.PRIMARY
    elif candidate_requirement == "ALTERNATIVE":
        candidate_role = CandidateRole.ALTERNATIVE
    backup_requirement = row["retained_backup_requirement"]
    backup_present = backup_requirement == "VALID"
    backup_valid = backup_requirement == "VALID"
    terminal_evaluated = row["rule_id"] in {"ARB_TERMINAL", "ARB_BOUNDARY"}
    return RuntimeRoutingContext(
        source_phase=RuntimePhase(row["source_phase"]),
        deadline=DeadlineObservation(
            deadline_status,
            row["source_phase"],
            0.0,
            1.0,
            "deadline:post-r2-fixture",
        ),
        authority_identity=authority,
        candidate_role=candidate_role,
        candidate_identity=CandidateIdentity("candidate:post-r2") if candidate_available else None,
        candidate_available=candidate_available,
        retained_backup_present=backup_present,
        retained_backup_valid=backup_valid,
        certified_candidate_available=row["rule_id"] == "ARB_NAV",
        terminal_evaluated=terminal_evaluated,
        terminal_evidence_eligible=row["rule_id"] == "ARB_TERMINAL",
        backup_state="ACTIVE" if backup_valid else "NONE",
    )


def ambiguous_table(table: TransitionTable, rule_index: int = 13) -> TransitionTable:
    rules = list(table.rules)
    rules.append(replace(rules[rule_index], rule_id="SYNTHETIC_DUPLICATE_FOR_AMBIGUITY_TEST"))
    return TransitionTable(tuple(rules))


def stage_exception_system(stage: str):
    if stage in {"TERMINAL_EVALUATION", "ARBITRATION"}:
        system = build_public_cycle({"proposal": "FAIL"})
        if stage == "TERMINAL_EVALUATION":
            system["coordinator"].terminal_runtime.evaluate = boom()
        else:
            system["supervisor"].arbitrate = boom()
        start, result = start_and_run(system)
        return system, start, result

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
    setattr(owner, method, boom())
    result = system["coordinator"].run_cycle(state, request)
    return system, None, result

