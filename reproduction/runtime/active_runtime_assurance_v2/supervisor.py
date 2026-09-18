"""Sole Active Runtime V2 action-selection authority."""

from __future__ import annotations

import csv
import json
from dataclasses import dataclass
from pathlib import Path

from .authority_registry import AuthorityRegistry
from .bounded_recovery import RecoverySourceGrant, SOURCE as RECOVERY_SOURCE
from .runtime_types import (
    ActionRole,
    AlternativeInventoryEvidence,
    AlternativeInventoryStatus,
    Candidate,
    CandidateRole,
    CertificateStatus,
    DeadlineObservation,
    DeadlineStatus,
    L1AttemptBinding,
    L1CycleResult,
    L3Result,
    RuntimeStateSnapshot,
    RuntimePhase,
    RuntimeRoutingContext,
    RoutingDecision,
    RouteResolutionStatus,
    PublicCycleEvent,
    ReasonScope,
    RecoveryRoutingFacts,
    RecoverySupervisorDecision,
    SelectedAction,
    StageFailureEvidence,
    SupervisorDecision,
    TerminalResult,
    make_action,
)


_REASON_SCOPE_BY_CODE = {
    "MAP_IDENTITY_MISMATCH": ReasonScope.GLOBAL_AUTHORITY_OR_EVIDENCE,
    "CANDIDATE_STATE_OR_MAP_IDENTITY_MISMATCH": ReasonScope.GLOBAL_AUTHORITY_OR_EVIDENCE,
    "L2_AUTHORITY_OR_ALIGNMENT_MISMATCH": ReasonScope.GLOBAL_AUTHORITY_OR_EVIDENCE,
    "GOAL_HOLD_RUNTIME_AUTHORITY_INVALID": ReasonScope.GLOBAL_AUTHORITY_OR_EVIDENCE,
    "TERMINAL_MAP_IDENTITY_MISMATCH": ReasonScope.GLOBAL_AUTHORITY_OR_EVIDENCE,
    "STALE_TERMINAL_REFERENCE": ReasonScope.GLOBAL_AUTHORITY_OR_EVIDENCE,
    "SOURCE_INVALID": ReasonScope.GLOBAL_AUTHORITY_OR_EVIDENCE,
    "RECOVERY_SOURCE_UNAUTHORIZED": ReasonScope.GLOBAL_AUTHORITY_OR_EVIDENCE,
    "PROVENANCE_MISSING": ReasonScope.GLOBAL_AUTHORITY_OR_EVIDENCE,
    "CANDIDATE_NONFINITE_OR_WRONG_DIMENSION": ReasonScope.CANDIDATE_LOCAL_COMPUTATION,
    "F_ACTUATOR_ADMISSIBILITY_LOCAL": ReasonScope.CANDIDATE_LOCAL_COMPUTATION,
    "L1_BACKEND_EXCEPTION": ReasonScope.INFRASTRUCTURE_HEALTH,
    "L2_BACKEND_EXCEPTION": ReasonScope.INFRASTRUCTURE_HEALTH,
    "L3_BACKEND_EXCEPTION": ReasonScope.INFRASTRUCTURE_HEALTH,
    "QP_SOLVER_EXCEPTION": ReasonScope.INFRASTRUCTURE_HEALTH,
    "TERMINAL_EXCEPTION": ReasonScope.INFRASTRUCTURE_HEALTH,
    "CURRENT_QUERY_EXCEPTION": ReasonScope.INFRASTRUCTURE_HEALTH,
    "STAGE_EXCEPTION": ReasonScope.INFRASTRUCTURE_HEALTH,
}


# Only finite, candidate-dependent witness failures whose nested reason is
# typed as a represented-map unsafe witness or future terminal membership
# failure may open Gate 0 recovery.  Inconclusive/unknown/global/timeout
# reasons are never silently converted to a local FAIL.
_RECOVERY_LOCAL_L3_REASONS = frozenset({
    "BACKUP_SEGMENT_NOT_CERTIFIED:FINITE_UNSAFE_WITNESS",
    "BACKUP_SEGMENT_NOT_CERTIFIED:SEGMENT_EXACT_UNSAFE",
    "TERMINAL_CERTIFICATE_FAILED:TERMINAL_VELOCITY_NOT_ZERO_WITHIN_TOLERANCE",
    "TERMINAL_CERTIFICATE_FAILED:TERMINAL_ZERO_HOLD_NOT_CERTIFIED:FINITE_UNSAFE_WITNESS",
    "TERMINAL_CERTIFICATE_FAILED:TERMINAL_ZERO_HOLD_NOT_CERTIFIED:SEGMENT_EXACT_UNSAFE",
})


@dataclass(frozen=True)
class RecoveryTransitionRule:
    rule_id: str
    phase: RuntimePhase
    event: PublicCycleEvent
    destination: RuntimePhase
    guard: str


RECOVERY_TRANSITION_RULES = (
    RecoveryTransitionRule("REC_L3_PREFETCH", RuntimePhase.L3, PublicCycleEvent.L3_WITNESS_ABSENT, RuntimePhase.TERMINAL_EVALUATION, "RECOVERY_ENTRY_EXACT"),
    RecoveryTransitionRule("REC_ENTRY_IDENTITY_BLOCK", RuntimePhase.L3, PublicCycleEvent.L3_WITNESS_ABSENT, RuntimePhase.ASSURANCE_BOUNDARY, "RECOVERY_IDENTITY_MISMATCH"),
    RecoveryTransitionRule("REC_TERMINAL_PASS", RuntimePhase.TERMINAL_EVALUATION, PublicCycleEvent.TERMINAL_MEMBER_ELIGIBLE, RuntimePhase.RECOVERY_SEARCH, "PREFETCH_CERTIFIED"),
    RecoveryTransitionRule("REC_TERMINAL_GUARD", RuntimePhase.TERMINAL_EVALUATION, PublicCycleEvent.TERMINAL_MEMBER_ELIGIBLE, RuntimePhase.ARBITRATION, "PREFETCH_CERTIFIED_DEADLINE_GUARD"),
    RecoveryTransitionRule("REC_TERMINAL_BLOCK", RuntimePhase.TERMINAL_EVALUATION, PublicCycleEvent.TERMINAL_MEMBER_NOT_ELIGIBLE, RuntimePhase.ASSURANCE_BOUNDARY, "PREFETCH_NOT_CERTIFIED"),
    RecoveryTransitionRule("REC_TERMINAL_UNKNOWN", RuntimePhase.TERMINAL_EVALUATION, PublicCycleEvent.TERMINAL_UNKNOWN, RuntimePhase.ASSURANCE_BOUNDARY, "PREFETCH_UNKNOWN"),
    RecoveryTransitionRule("REC_SCAN_PASS", RuntimePhase.RECOVERY_SEARCH, PublicCycleEvent.RECOVERY_CERT_PASS, RuntimePhase.ARBITRATION, "FIRST_FULL_PASS"),
    RecoveryTransitionRule("REC_SCAN_ADMIT_OPEN", RuntimePhase.RECOVERY_SEARCH, PublicCycleEvent.RECOVERY_SCAN_ADMISSION, RuntimePhase.RECOVERY_SEARCH, "SCAN_ADMISSION_OPEN"),
    RecoveryTransitionRule("REC_SCAN_ADMIT_GUARD", RuntimePhase.RECOVERY_SEARCH, PublicCycleEvent.RECOVERY_SCAN_ADMISSION, RuntimePhase.ARBITRATION, "SCAN_ADMISSION_NOT_OPEN"),
    RecoveryTransitionRule("REC_CANDIDATE_AVAILABLE", RuntimePhase.RECOVERY_SEARCH, PublicCycleEvent.RECOVERY_CANDIDATE_AVAILABLE, RuntimePhase.C0, "NEXT_FROZEN_RANK_OPEN"),
    RecoveryTransitionRule("REC_SCAN_NEXT", RuntimePhase.RECOVERY_SEARCH, PublicCycleEvent.RECOVERY_CANDIDATE_REJECTED, RuntimePhase.RECOVERY_SEARCH, "UNTRIED_REMAIN_OPEN"),
    RecoveryTransitionRule("REC_SCAN_EXHAUSTED", RuntimePhase.RECOVERY_SEARCH, PublicCycleEvent.RECOVERY_SCAN_EXHAUSTED, RuntimePhase.ARBITRATION, "NO_UNTRIED_CANDIDATE"),
    RecoveryTransitionRule("REC_SCAN_PAUSED", RuntimePhase.RECOVERY_SEARCH, PublicCycleEvent.RECOVERY_SCAN_PAUSED, RuntimePhase.ARBITRATION, "DEADLINE_NOT_OPEN"),
    RecoveryTransitionRule("REC_SOURCE_BLOCKED", RuntimePhase.RECOVERY_SEARCH, PublicCycleEvent.RECOVERY_SOURCE_UNAUTHORIZED, RuntimePhase.ARBITRATION, "SOURCE_OR_IDENTITY_BLOCKED"),
    RecoveryTransitionRule("REC_C0_PASS", RuntimePhase.C0, PublicCycleEvent.C0_PASS, RuntimePhase.L2, "RECOVERY_C0_CERTIFIED"),
    RecoveryTransitionRule("REC_C0_LOCAL_FAIL", RuntimePhase.C0, PublicCycleEvent.C0_FAIL_LOCAL, RuntimePhase.RECOVERY_SEARCH, "RECOVERY_C0_LOCAL_REJECT"),
    RecoveryTransitionRule("REC_C0_GLOBAL_FAIL", RuntimePhase.C0, PublicCycleEvent.C0_FAIL_LOCAL, RuntimePhase.ARBITRATION, "RECOVERY_C0_GLOBAL_BLOCK"),
    RecoveryTransitionRule("REC_C0_UNKNOWN_LOCAL", RuntimePhase.C0, PublicCycleEvent.C0_UNKNOWN_LOCAL, RuntimePhase.ARBITRATION, "RECOVERY_C0_UNKNOWN"),
    RecoveryTransitionRule("REC_C0_UNKNOWN_GLOBAL", RuntimePhase.C0, PublicCycleEvent.C0_UNKNOWN_GLOBAL, RuntimePhase.ARBITRATION, "RECOVERY_C0_UNKNOWN"),
    RecoveryTransitionRule("REC_L2_PASS", RuntimePhase.L2, PublicCycleEvent.L2_PASS, RuntimePhase.L3, "RECOVERY_L2_CERTIFIED"),
    RecoveryTransitionRule("REC_L2_FAIL", RuntimePhase.L2, PublicCycleEvent.L2_FAIL, RuntimePhase.RECOVERY_SEARCH, "RECOVERY_L2_LOCAL_REJECT"),
    RecoveryTransitionRule("REC_L2_UNKNOWN_LOCAL", RuntimePhase.L2, PublicCycleEvent.L2_UNKNOWN_LOCAL, RuntimePhase.ARBITRATION, "RECOVERY_L2_UNKNOWN"),
    RecoveryTransitionRule("REC_L2_UNKNOWN_GLOBAL", RuntimePhase.L2, PublicCycleEvent.L2_UNKNOWN_GLOBAL, RuntimePhase.ARBITRATION, "RECOVERY_L2_UNKNOWN"),
    RecoveryTransitionRule("REC_L3_PASS", RuntimePhase.L3, PublicCycleEvent.L3_WITNESS_FOUND, RuntimePhase.ARBITRATION, "RECOVERY_L3_CERTIFIED"),
    RecoveryTransitionRule("REC_L3_LOCAL_FAIL", RuntimePhase.L3, PublicCycleEvent.L3_WITNESS_ABSENT, RuntimePhase.RECOVERY_SEARCH, "RECOVERY_L3_LOCAL_REJECT"),
    RecoveryTransitionRule("REC_L3_GLOBAL_FAIL", RuntimePhase.L3, PublicCycleEvent.L3_WITNESS_ABSENT, RuntimePhase.ARBITRATION, "RECOVERY_L3_UNCLASSIFIED_BLOCK"),
    RecoveryTransitionRule("REC_L3_UNKNOWN_LOCAL", RuntimePhase.L3, PublicCycleEvent.L3_UNKNOWN_LOCAL, RuntimePhase.ARBITRATION, "RECOVERY_L3_UNKNOWN"),
    RecoveryTransitionRule("REC_L3_UNKNOWN_GLOBAL", RuntimePhase.L3, PublicCycleEvent.L3_UNKNOWN_GLOBAL, RuntimePhase.ARBITRATION, "RECOVERY_L3_UNKNOWN"),
)


@dataclass(frozen=True)
class TransitionRule:
    rule_id: str
    source_phase: str
    destination_phase: str
    commit_allowed: bool
    action_authority: str
    failure_code: str
    observation_result: str = ""
    reason_scope: str = "NONE"
    retained_backup_requirement: str = "ANY"
    deadline_requirement: str = "ANY"
    candidate_requirement: str = "NONE"
    guard: str = ""
    # The following values are copied from the frozen routing-design row.  In
    # particular, they are not reconstructed from the destination enum.
    may_start_next_stage: bool = False
    may_start_new_search: bool = False
    requires_arbitration: bool = False
    deadline_interpretation: str = ""
    backup_routing_allowed: bool = False
    terminal_routing_allowed: bool = False
    old_backup_retained: bool = False
    new_backup_created: bool = False
    theorem_interpretation: str = ""


class TransitionTable:
    def __init__(self, rules: tuple[TransitionRule, ...]) -> None:
        if len(rules) != 44 or len({rule.rule_id for rule in rules}) != 44:
            raise ValueError("TRANSITION_TABLE_NOT_44_EXACTLY_ONCE")
        self.rules = rules
        self.by_id = {rule.rule_id: rule for rule in rules}

    @classmethod
    def from_csv(cls, path: Path) -> "TransitionTable":
        with path.open(encoding="utf-8", newline="") as handle:
            rows = list(csv.DictReader(handle))

        # PR #107 remains the row authority.  PR #121 supplies the additive
        # route-carrier fields, so the runtime copies those values by rule ID
        # instead of deriving policy from a destination enum.
        design_candidates = (
            path.with_name("EXECUTABLE_TRANSITION_ROUTING_DESIGN_V2.json"),
            Path(__file__).resolve().parents[3] / "reproduction" / "design" / "active_runtime_public_cycle_composition_v2" / "EXECUTABLE_TRANSITION_ROUTING_DESIGN_V2.json",
        )
        design_rows: dict[str, dict[str, object]] = {}
        for design_path in design_candidates:
            if not design_path.is_file():
                continue
            try:
                payload = json.loads(design_path.read_text(encoding="utf-8"))
                design_rows = {str(item["rule_id"]): item for item in payload.get("rules", [])}
            except (OSError, ValueError, TypeError, KeyError):
                design_rows = {}
            if design_rows:
                break

        def bool_value(row: dict[str, str], key: str, default: bool = False) -> bool:
            value = row.get(key)
            if value is None or value == "":
                return default
            return value.strip().lower() == "true"

        def design_value(rule_id: str, key: str, default: object = None) -> object:
            value = design_rows.get(rule_id, {}).get(key, default)
            return default if value is None else value

        return cls(tuple(TransitionRule(
            rule_id=row["rule_id"],
            source_phase=row["source_phase"],
            destination_phase=row.get("runtime_destination") or row["destination_phase"],
            commit_allowed=bool_value(row, "commit_allowed"),
            action_authority=row.get("commit_authority") or row["action_authority"],
            failure_code=row.get("failure_mapping") or row["failure_code_if_any"],
            observation_result=row["observation/result"],
            reason_scope=row["reason_scope"],
            retained_backup_requirement=row["retained_backup_requirement"],
            deadline_requirement=row["deadline_requirement"],
            candidate_requirement=row["candidate_requirement"],
            guard=row["guard"],
            may_start_next_stage=bool(design_value(row["rule_id"], "may_start_next_stage", False)),
            may_start_new_search=bool(design_value(row["rule_id"], "may_start_new_search", False)),
            requires_arbitration=bool(design_value(row["rule_id"], "requires_arbitration", False)),
            deadline_interpretation=str(design_value(row["rule_id"], "deadline_interpretation", "")),
            backup_routing_allowed=bool(design_value(row["rule_id"], "backup_routing_allowed", False)),
            terminal_routing_allowed=bool(design_value(row["rule_id"], "terminal_routing_allowed", False)),
            old_backup_retained=bool_value(row, "old_backup_retained", bool(design_value(row["rule_id"], "old_backup_retained", False))),
            new_backup_created=bool_value(row, "new_backup_created", bool(design_value(row["rule_id"], "new_backup_created", False))),
            theorem_interpretation=str(row.get("theorem_interpretation") or design_value(row["rule_id"], "theorem_interpretation", "")),
        ) for row in rows))

    @staticmethod
    def _deadline_matches(requirement: str, status: DeadlineStatus) -> bool:
        if requirement == "ANY":
            return True
        if requirement == "OPEN":
            return status == DeadlineStatus.OPEN
        if requirement == "GUARD_OR_EXPIRED":
            return status in {DeadlineStatus.WARNING, DeadlineStatus.EXPIRED}
        return False

    @staticmethod
    def _backup_matches(requirement: str, context: RuntimeRoutingContext) -> bool:
        if requirement == "ANY":
            return True
        if requirement == "VALID":
            return context.retained_backup_valid
        if requirement == "NONE":
            return not context.retained_backup_present
        if requirement == "NONE_OR_INVALID_OR_EXHAUSTED":
            return not context.retained_backup_valid
        return False

    @staticmethod
    def _candidate_matches(requirement: str, context: RuntimeRoutingContext) -> bool:
        if requirement == "NONE":
            return not context.candidate_available
        if requirement == "PRIMARY":
            return context.candidate_available and context.candidate_role == CandidateRole.PRIMARY
        if requirement == "ALTERNATIVE":
            return context.candidate_available and context.candidate_role == CandidateRole.ALTERNATIVE
        if requirement == "PRIMARY_OR_ALTERNATIVE":
            return context.candidate_available and context.candidate_role in {CandidateRole.PRIMARY, CandidateRole.ALTERNATIVE}
        return False

    @staticmethod
    def _alternative_branch_available(context: RuntimeRoutingContext) -> bool:
        """Return only raw prerequisites used by the frozen local-alt rows."""
        return context.deadline.status == DeadlineStatus.OPEN and context.retained_backup_valid

    @staticmethod
    def _certified_candidate_fact(context: RuntimeRoutingContext) -> bool:
        # ``legacy_navigation_hint`` is accepted only for old positional
        # fixtures; all production coordinator calls use the explicit factual
        # field and never provide a policy hint.
        return context.certified_candidate_available or context.legacy_navigation_hint

    @staticmethod
    def _terminal_eligibility_fact(context: RuntimeRoutingContext) -> bool:
        return context.terminal_evidence_eligible or context.legacy_terminal_hint

    @staticmethod
    def _branch_guard(rule: TransitionRule, context: RuntimeRoutingContext) -> bool:
        if rule.rule_id in {
            "C0_FAIL_LOCAL_ALT", "C0_UNKNOWN_LOCAL_ALT", "L2_FAIL_ALT",
            "L2_UNKNOWN_LOCAL_ALT", "L3_ABSENT_ALT", "L3_UNKNOWN_LOCAL_ALT",
        }:
            return TransitionTable._alternative_branch_available(context)
        if rule.rule_id in {
            "C0_FAIL_LOCAL_ARB", "C0_UNKNOWN_LOCAL_ARB", "L2_FAIL_ARB",
            "L2_UNKNOWN_LOCAL_ARB", "L3_ABSENT_ARB", "L3_UNKNOWN_LOCAL_ARB",
        }:
            return not TransitionTable._alternative_branch_available(context)
        if rule.rule_id == "ARB_NAV":
            return (TransitionTable._certified_candidate_fact(context) and context.deadline.status == DeadlineStatus.OPEN
                    and not (context.candidate_source_type == RECOVERY_SOURCE and context.retained_backup_valid))
        if rule.rule_id == "ARB_BACKUP_GUARD":
            return (
                TransitionTable._certified_candidate_fact(context)
                and context.retained_backup_valid
                and context.deadline.status in {DeadlineStatus.WARNING, DeadlineStatus.EXPIRED}
            )
        if rule.rule_id == "ARB_BACKUP":
            return (not TransitionTable._certified_candidate_fact(context) or context.candidate_source_type == RECOVERY_SOURCE) and context.retained_backup_valid
        if rule.rule_id == "ARB_TERMINAL":
            return not TransitionTable._certified_candidate_fact(context) and not context.retained_backup_valid and context.terminal_evaluated and TransitionTable._terminal_eligibility_fact(context)
        if rule.rule_id == "ARB_EVAL_TERMINAL":
            return not TransitionTable._certified_candidate_fact(context) and not context.retained_backup_valid and not context.terminal_evaluated and context.deadline.status == DeadlineStatus.OPEN
        if rule.rule_id == "ARB_BOUNDARY":
            return not TransitionTable._certified_candidate_fact(context) and not context.retained_backup_valid and not TransitionTable._terminal_eligibility_fact(context) and (context.terminal_evaluated or context.deadline.status != DeadlineStatus.OPEN)
        return True

    @staticmethod
    def _blocked_decision(context: RuntimeRoutingContext, status: RouteResolutionStatus, reason: str) -> RoutingDecision:
        return RoutingDecision(
            status=status,
            rule_id=None,
            source_phase=context.source_phase,
            destination_phase=None,
            may_start_next_stage=False,
            may_start_new_search=False,
            requires_arbitration=False,
            failure_mapping=reason,
            deadline_interpretation="SUPERVISOR_BLOCKS_UNRESOLVED_LOOKUP",
            backup_routing_allowed=False,
            terminal_routing_allowed=False,
            commit_allowed=False,
            reason=reason,
            action_authority=None,
            old_backup_retained=None,
            new_backup_created=None,
            theorem_interpretation=None,
            observation_result=None,
            guard=None,
            reason_scope=context.reason_scope,
            retained_backup_requirement=None,
            deadline_requirement=None,
            candidate_requirement=None,
        )

    def resolve(self, event: PublicCycleEvent | str, context: RuntimeRoutingContext) -> RoutingDecision:
        event_value = event.value if isinstance(event, PublicCycleEvent) else str(event)
        if not context.authority_identity:
            matches: list[TransitionRule] = []
        else:
            matches = [
                rule for rule in self.rules
                if rule.source_phase == context.source_phase.value
                and rule.observation_result == event_value
                and self._deadline_matches(rule.deadline_requirement, context.deadline.status)
                and self._backup_matches(rule.retained_backup_requirement, context)
                and self._candidate_matches(rule.candidate_requirement, context)
                and self._branch_guard(rule, context)
            ]
        if len(matches) != 1:
            status = RouteResolutionStatus.BLOCKED_MISSING if not matches else RouteResolutionStatus.BLOCKED_AMBIGUOUS
            reason = "ROUTING_RULE_MISSING" if not matches else "ROUTING_RULE_AMBIGUOUS"
            return self._blocked_decision(context, status, reason)
        rule = matches[0]
        destination = RuntimePhase(rule.destination_phase)
        return RoutingDecision(
            status=RouteResolutionStatus.RESOLVED,
            rule_id=rule.rule_id,
            source_phase=context.source_phase,
            destination_phase=destination,
            may_start_next_stage=rule.may_start_next_stage,
            may_start_new_search=rule.may_start_new_search,
            requires_arbitration=rule.requires_arbitration,
            failure_mapping=rule.failure_code or None,
            deadline_interpretation=rule.deadline_interpretation,
            backup_routing_allowed=rule.backup_routing_allowed,
            terminal_routing_allowed=rule.terminal_routing_allowed,
            commit_allowed=rule.commit_allowed,
            reason=rule.guard,
            action_authority=rule.action_authority,
            old_backup_retained=rule.old_backup_retained,
            new_backup_created=rule.new_backup_created,
            theorem_interpretation=rule.theorem_interpretation,
            observation_result=rule.observation_result,
            guard=rule.guard,
            reason_scope=rule.reason_scope,
            retained_backup_requirement=rule.retained_backup_requirement,
            deadline_requirement=rule.deadline_requirement,
            candidate_requirement=rule.candidate_requirement,
        )


class Supervisor:
    def __init__(self, registry: AuthorityRegistry, transition_table: TransitionTable | None = None) -> None:
        self.registry = registry
        self.transition_table = transition_table

    def make_retained_backup_action(self, vector: tuple[float, float, float], action_id: str) -> SelectedAction:
        return make_action(vector, ActionRole.RETAINED_BACKUP, action_id, (self.registry.actuator.identity.value, self.registry.geometry.identity.value))

    def route_transition(self, event: PublicCycleEvent | str, runtime_context: RuntimeRoutingContext) -> RoutingDecision:
        if self.transition_table is None:
            return TransitionTable._blocked_decision(runtime_context, RouteResolutionStatus.BLOCKED_MISSING, "ROUTING_RULE_MISSING")
        if runtime_context.recovery_facts is not None:
            recovery = runtime_context.recovery_facts
            if runtime_context.candidate_source_type == RECOVERY_SOURCE and runtime_context.source_phase in {RuntimePhase.C0, RuntimePhase.L2, RuntimePhase.L3}:
                return self._resolve_recovery(event, runtime_context)
            elif runtime_context.source_phase == RuntimePhase.L3 and event == PublicCycleEvent.L3_WITNESS_ABSENT:
                if self._recovery_entry_allowed(runtime_context):
                    return self._resolve_recovery(event, runtime_context)
                if (runtime_context.candidate_role == CandidateRole.PRIMARY and
                        not recovery.exact_identities):
                    return self._resolve_recovery(event, runtime_context)
            elif runtime_context.source_phase == RuntimePhase.TERMINAL_EVALUATION and recovery.terminal_prefetch:
                return self._resolve_recovery(event, runtime_context)
            elif runtime_context.source_phase == RuntimePhase.RECOVERY_SEARCH:
                return self._resolve_recovery(event, runtime_context)
        return self.transition_table.resolve(event, runtime_context)

    @staticmethod
    def classify_recovery_l3_fail(reason: str) -> ReasonScope:
        return (ReasonScope.CANDIDATE_LOCAL_COMPUTATION if str(reason) in _RECOVERY_LOCAL_L3_REASONS
                else ReasonScope.UNRESOLVED_SCOPE)

    @classmethod
    def _recovery_entry_allowed(cls, context: RuntimeRoutingContext) -> bool:
        facts = context.recovery_facts
        return bool(facts is not None and context.source_phase == RuntimePhase.L3
                    and context.candidate_role == CandidateRole.PRIMARY
                    and context.deadline.status == DeadlineStatus.OPEN
                    and not context.retained_backup_valid
                    and facts.l1_pass and facts.primary_exists and facts.primary_c0_pass and facts.primary_l2_pass
                    and facts.primary_l3_status == CertificateStatus.FAIL.value
                    and cls.classify_recovery_l3_fail(facts.primary_l3_reason) == ReasonScope.CANDIDATE_LOCAL_COMPUTATION
                    and facts.source_authorized and facts.exact_identities and facts.exhaustion_eligible)

    @classmethod
    def _resolve_recovery(cls, event: PublicCycleEvent | str, context: RuntimeRoutingContext) -> RoutingDecision:
        try:
            value = event if isinstance(event, PublicCycleEvent) else PublicCycleEvent(str(event))
        except ValueError:
            return TransitionTable._blocked_decision(context, RouteResolutionStatus.BLOCKED_MISSING, "RECOVERY_ROUTING_RULE_MISSING")
        facts = context.recovery_facts
        matches = []
        for rule in RECOVERY_TRANSITION_RULES:
            if rule.phase != context.source_phase or rule.event != value:
                continue
            guard = rule.guard
            if guard.startswith("RECOVERY_C0_") or guard.startswith("RECOVERY_L2_") or guard.startswith("RECOVERY_L3_"):
                if context.candidate_source_type != RECOVERY_SOURCE:
                    continue
            if guard == "RECOVERY_ENTRY_EXACT" and context.candidate_source_type == RECOVERY_SOURCE:
                continue
            if guard == "RECOVERY_ENTRY_EXACT" and not cls._recovery_entry_allowed(context):
                continue
            if guard == "RECOVERY_IDENTITY_MISMATCH" and not (
                    facts and context.candidate_role == CandidateRole.PRIMARY and
                    not facts.exact_identities):
                continue
            if guard == "PREFETCH_CERTIFIED" and not (facts and facts.terminal_prefetch and facts.terminal_pass and context.deadline.status == DeadlineStatus.OPEN):
                continue
            if guard == "PREFETCH_CERTIFIED_DEADLINE_GUARD" and not (facts and facts.terminal_prefetch and facts.terminal_pass and context.deadline.status != DeadlineStatus.OPEN):
                continue
            if guard in {"PREFETCH_NOT_CERTIFIED", "PREFETCH_UNKNOWN"} and not (facts and facts.terminal_prefetch and not facts.terminal_pass):
                continue
            if guard == "UNTRIED_REMAIN_OPEN" and not (facts and facts.remaining_candidates and context.deadline.status == DeadlineStatus.OPEN):
                continue
            if guard == "NEXT_FROZEN_RANK_OPEN" and not (facts and facts.remaining_candidates and context.deadline.status == DeadlineStatus.OPEN and context.candidate_source_type == RECOVERY_SOURCE):
                continue
            if guard == "NO_UNTRIED_CANDIDATE" and not (facts and not facts.remaining_candidates):
                continue
            if guard == "DEADLINE_NOT_OPEN" and context.deadline.status == DeadlineStatus.OPEN:
                continue
            if guard == "SCAN_ADMISSION_OPEN" and context.deadline.status != DeadlineStatus.OPEN:
                continue
            if guard == "SCAN_ADMISSION_NOT_OPEN" and context.deadline.status == DeadlineStatus.OPEN:
                continue
            if guard in {"RECOVERY_C0_LOCAL_REJECT", "RECOVERY_L3_LOCAL_REJECT"} and context.reason_scope != ReasonScope.CANDIDATE_LOCAL_COMPUTATION.value:
                continue
            if guard in {"RECOVERY_C0_GLOBAL_BLOCK", "RECOVERY_L3_UNCLASSIFIED_BLOCK"} and context.reason_scope == ReasonScope.CANDIDATE_LOCAL_COMPUTATION.value:
                continue
            matches.append(rule)
        if len(matches) != 1:
            status = RouteResolutionStatus.BLOCKED_MISSING if not matches else RouteResolutionStatus.BLOCKED_AMBIGUOUS
            return TransitionTable._blocked_decision(context, status, "RECOVERY_ROUTING_RULE_MISSING" if not matches else "RECOVERY_ROUTING_RULE_AMBIGUOUS")
        rule = matches[0]
        return RoutingDecision(
            status=RouteResolutionStatus.RESOLVED, rule_id=rule.rule_id,
            source_phase=context.source_phase, destination_phase=rule.destination,
            may_start_next_stage=True, may_start_new_search=rule.destination == RuntimePhase.RECOVERY_SEARCH,
            requires_arbitration=rule.destination in {RuntimePhase.ARBITRATION, RuntimePhase.ASSURANCE_BOUNDARY},
            failure_mapping=None, deadline_interpretation="SUPERVISOR_RECOVERY_GATE0",
            backup_routing_allowed=True, terminal_routing_allowed=True,
            commit_allowed=False, reason=rule.guard, action_authority="NONE",
            observation_result=value.value, guard=rule.guard, reason_scope=context.reason_scope,
            retained_backup_requirement="NONE_OR_INVALID_OR_EXHAUSTED",
            deadline_requirement="OPEN" if rule.destination == RuntimePhase.RECOVERY_SEARCH else "ANY",
            candidate_requirement="PRIMARY_OR_RECOVERY",
        )

    def authorize_recovery_source(self, snapshot: RuntimeStateSnapshot,
                                  context: RuntimeRoutingContext, transition_identity: str) -> RecoverySourceGrant | None:
        facts = context.recovery_facts
        if not (facts and facts.terminal_prefetch and facts.terminal_pass and
                context.deadline.status == DeadlineStatus.OPEN and not context.retained_backup_valid):
            return None
        if not (facts.l1_pass and facts.primary_c0_pass and facts.primary_l2_pass and
                facts.source_authorized and facts.exact_identities and facts.exhaustion_eligible and
                self.classify_recovery_l3_fail(facts.primary_l3_reason) == ReasonScope.CANDIDATE_LOCAL_COMPUTATION):
            return None
        if snapshot.map_identity != self.registry.map_identity or not transition_identity:
            return None
        return RecoverySourceGrant.create(snapshot, self.registry.actuator.identity.value, transition_identity)

    @staticmethod
    def attach_recovery_evidence(decision: SupervisorDecision,
                                 evidence: tuple[tuple[tuple[str, object], ...], ...]) -> RecoverySupervisorDecision:
        return RecoverySupervisorDecision(decision.cycle_index, decision.state_identity,
                                          decision.selected_action, decision.allows_commit,
                                          decision.reason, decision.rule_id,
                                          decision.prepared_bundle, evidence)

    @staticmethod
    def classify_reason_scope(stage_name: str, reason: str) -> ReasonScope:
        """Resolve only exact frozen reason codes; arbitrary text stays unresolved."""
        del stage_name  # stage remains an audit input, never a substring-policy hint
        reason_code = str(reason).split(":", 1)[0]
        return _REASON_SCOPE_BY_CODE.get(reason_code, ReasonScope.UNRESOLVED_SCOPE)

    @staticmethod
    def _meta_route_to_arbitration(runtime_context: RuntimeRoutingContext, reason: str) -> RoutingDecision:
        """Supervisor-owned non-rule route for typed evidence not represented by a PR #107 row."""
        return RoutingDecision(
            status=RouteResolutionStatus.RESOLVED,
            rule_id=None,
            source_phase=runtime_context.source_phase,
            destination_phase=RuntimePhase.ARBITRATION,
            may_start_next_stage=True,
            may_start_new_search=False,
            requires_arbitration=True,
            failure_mapping=reason,
            deadline_interpretation="SUPERVISOR_META_SAFETY_ROUTE",
            backup_routing_allowed=True,
            terminal_routing_allowed=True,
            commit_allowed=False,
            reason=reason,
            action_authority="NONE",
            old_backup_retained=runtime_context.retained_backup_present,
            new_backup_created=False,
            theorem_interpretation="typed failure preserves only already-certified fallback authority",
            observation_result=reason,
            guard="Supervisor-owned typed meta route; no frozen rule ID is fabricated",
            reason_scope=runtime_context.reason_scope,
            retained_backup_requirement="ANY",
            deadline_requirement="ANY",
            candidate_requirement="NONE",
        )

    def route_stage_failure(self, evidence: StageFailureEvidence, runtime_context: RuntimeRoutingContext) -> RoutingDecision:
        """Map typed stage failure evidence to a frozen route or explicit meta block."""
        phase = evidence.source_phase
        scope = evidence.reason_scope
        if phase == RuntimePhase.L1:
            event = (
                PublicCycleEvent.L1_UNKNOWN_HEALTH
                if scope == ReasonScope.INFRASTRUCTURE_HEALTH
                else PublicCycleEvent.L1_UNKNOWN_GLOBAL
                if scope == ReasonScope.GLOBAL_AUTHORITY_OR_EVIDENCE
                else PublicCycleEvent.L1_UNKNOWN_UNRESOLVED
            )
            return self.route_transition(event, runtime_context)
        if phase == RuntimePhase.PRIMARY_PROPOSAL:
            return self.route_transition(PublicCycleEvent.NO_CANDIDATE, runtime_context)
        if phase == RuntimePhase.C0:
            event = PublicCycleEvent.C0_UNKNOWN_LOCAL if scope == ReasonScope.CANDIDATE_LOCAL_COMPUTATION else PublicCycleEvent.C0_UNKNOWN_GLOBAL
            return self.route_transition(event, runtime_context)
        if phase == RuntimePhase.L2:
            event = PublicCycleEvent.L2_UNKNOWN_LOCAL if scope == ReasonScope.CANDIDATE_LOCAL_COMPUTATION else PublicCycleEvent.L2_UNKNOWN_GLOBAL
            return self.route_transition(event, runtime_context)
        if phase == RuntimePhase.L3:
            event = PublicCycleEvent.L3_UNKNOWN_LOCAL if scope == ReasonScope.CANDIDATE_LOCAL_COMPUTATION else PublicCycleEvent.L3_UNKNOWN_GLOBAL
            return self.route_transition(event, runtime_context)
        if phase == RuntimePhase.ALT_SEARCH:
            return self._meta_route_to_arbitration(runtime_context, evidence.typed_reason)
        if phase == RuntimePhase.TERMINAL_EVALUATION:
            return self.route_transition(PublicCycleEvent.TERMINAL_UNKNOWN, runtime_context)
        return TransitionTable._blocked_decision(
            runtime_context,
            RouteResolutionStatus.BLOCKED_MISSING,
            evidence.typed_reason,
        )

    def route_alternative_inventory(self, evidence: AlternativeInventoryEvidence, runtime_context: RuntimeRoutingContext) -> RoutingDecision:
        """Preserve provider status before applying frozen or meta routing authority."""
        if evidence.status == AlternativeInventoryStatus.ALT_AVAILABLE:
            return self.route_transition(PublicCycleEvent.ALT_AVAILABLE, runtime_context)
        if evidence.status == AlternativeInventoryStatus.NO_ALTERNATIVE_AVAILABLE:
            return self.route_transition(PublicCycleEvent.ALT_EXHAUSTED, runtime_context)
        return self._meta_route_to_arbitration(runtime_context, f"ALTERNATIVE_PROVIDER_{evidence.status.value}")

    def routing_guard_block(self, runtime_context: RuntimeRoutingContext, reason: str = "ROUTING_STATE_REPEATED") -> RoutingDecision:
        """Supervisor-owned typed block for an impossible repeated route state."""
        return TransitionTable._blocked_decision(runtime_context, RouteResolutionStatus.BLOCKED_AMBIGUOUS, reason)

    @staticmethod
    def blocked_cycle_decision(snapshot: RuntimeStateSnapshot, reason: str) -> SupervisorDecision:
        """Represent a typed orchestration block without granting commit authority."""
        return SupervisorDecision(
            snapshot.cycle_index,
            snapshot.identity,
            None,
            False,
            str(reason),
            "ROUTING_BLOCK",
        )

    def bypass_decision(self, snapshot: RuntimeStateSnapshot, reference_action: SelectedAction) -> SupervisorDecision:
        if reference_action.role == ActionRole.ASSURANCE_BOUNDARY_NO_ACTION:
            return SupervisorDecision(snapshot.cycle_index, snapshot.identity, None, False, "BYPASS_REFERENCE_NO_ACTION", "BYPASS")
        return SupervisorDecision(snapshot.cycle_index, snapshot.identity, reference_action, True, "BYPASS_REFERENCE_ACTION_UNCHANGED", "BYPASS")

    def arbitrate(
        self,
        snapshot: RuntimeStateSnapshot,
        certified_candidate: Candidate | None,
        l3_result: L3Result | None,
        retained_backup_action: SelectedAction | None,
        backup_valid: bool,
        terminal_result: TerminalResult | None,
        deadline: DeadlineObservation,
    ) -> SupervisorDecision:
        if (certified_candidate is not None and
                certified_candidate.provenance.source_type == RECOVERY_SOURCE and
                backup_valid and retained_backup_action is not None and
                retained_backup_action.role == ActionRole.RETAINED_BACKUP):
            return SupervisorDecision(snapshot.cycle_index, snapshot.identity,
                                      retained_backup_action, True,
                                      "VALID_RETAINED_BACKUP_OUTRANKS_RECOVERY",
                                      "ARB_BACKUP")
        if certified_candidate is not None and l3_result is not None and l3_result.status == CertificateStatus.PASS and l3_result.prepared_bundle is not None and l3_result.candidate_identity == certified_candidate.identity and deadline.status == DeadlineStatus.OPEN:
            role = ActionRole.PRIMARY_NAVIGATION if certified_candidate.role == CandidateRole.PRIMARY else ActionRole.ALTERNATIVE_NAVIGATION
            action = make_action(certified_candidate.vector, role, certified_candidate.identity.value, (self.registry.geometry.identity.value, self.registry.actuator.identity.value, l3_result.evidence_identity or ""))
            return SupervisorDecision(snapshot.cycle_index, snapshot.identity, action, True, "TIMELY_CERTIFIED_NAVIGATION_WITH_PREPARED_TOKEN", "ARB_NAV", l3_result.prepared_bundle)
        if backup_valid and retained_backup_action is not None and retained_backup_action.role == ActionRole.RETAINED_BACKUP:
            guard_handoff = certified_candidate is not None and deadline.status in {DeadlineStatus.WARNING, DeadlineStatus.EXPIRED}
            return SupervisorDecision(
                snapshot.cycle_index,
                snapshot.identity,
                retained_backup_action,
                True,
                "CERTIFIED_NAVIGATION_NOT_TIMELY_USE_VALID_RETAINED_BACKUP" if guard_handoff else "STILL_VALID_RETAINED_BACKUP",
                "ARB_BACKUP_GUARD" if guard_handoff else "ARB_BACKUP",
            )
        if terminal_result is not None and terminal_result.status == CertificateStatus.PASS and terminal_result.eligible:
            action = make_action(self.registry.terminal.zero_hold, ActionRole.CERTIFIED_TERMINAL, terminal_result.evidence_identity or "terminal", (self.registry.terminal.identity.value, self.registry.actuator.identity.value, self.registry.geometry.identity.value))
            return SupervisorDecision(snapshot.cycle_index, snapshot.identity, action, True, "ELIGIBLE_CURRENT_CERTIFIED_TERMINAL_ACTION", "ARB_TERMINAL")
        return SupervisorDecision(snapshot.cycle_index, snapshot.identity, None, False, "ASSURANCE_BOUNDARY_NO_CERTIFIED_ACTION", "ARB_BOUNDARY")

    def certify_candidate(self, snapshot: RuntimeStateSnapshot, candidate: Candidate, l1_result: L1CycleResult, l1_binding: L1AttemptBinding, c0, l2, l3):
        if l1_result.status != CertificateStatus.PASS or l1_binding.candidate_identity != candidate.identity or l1_binding.cycle_result_identity != l1_result.identity:
            return None, None, None
        c0_result = c0.evaluate(candidate, snapshot)
        if c0_result.status != CertificateStatus.PASS:
            return c0_result, None, None
        l2_result = l2.evaluate(snapshot, candidate)
        if l2_result.status != CertificateStatus.PASS:
            return c0_result, l2_result, None
        l3_result = l3.evaluate(snapshot, candidate, l2_result)
        return c0_result, l2_result, l3_result
