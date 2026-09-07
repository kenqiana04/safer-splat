"""Sole Active Runtime V2 action-selection authority."""

from __future__ import annotations

import csv
from dataclasses import dataclass
from pathlib import Path

from .authority_registry import AuthorityRegistry
from .runtime_types import (
    ActionRole,
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
    SelectedAction,
    SupervisorDecision,
    TerminalResult,
    make_action,
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


class TransitionTable:
    def __init__(self, rules: tuple[TransitionRule, ...]) -> None:
        if len(rules) != 43 or len({rule.rule_id for rule in rules}) != 43:
            raise ValueError("TRANSITION_TABLE_NOT_43_EXACTLY_ONCE")
        self.rules = rules
        self.by_id = {rule.rule_id: rule for rule in rules}

    @classmethod
    def from_csv(cls, path: Path) -> "TransitionTable":
        with path.open(encoding="utf-8", newline="") as handle:
            rows = list(csv.DictReader(handle))
        return cls(tuple(TransitionRule(
            rule_id=row["rule_id"],
            source_phase=row["source_phase"],
            destination_phase=row.get("runtime_destination") or row["destination_phase"],
            commit_allowed=row["commit_allowed"].lower() == "true",
            action_authority=row.get("commit_authority") or row["action_authority"],
            failure_code=row.get("failure_mapping") or row["failure_code_if_any"],
            observation_result=row["observation/result"],
            reason_scope=row["reason_scope"],
            retained_backup_requirement=row["retained_backup_requirement"],
            deadline_requirement=row["deadline_requirement"],
            candidate_requirement=row["candidate_requirement"],
            guard=row["guard"],
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
    def _branch_guard(rule: TransitionRule, context: RuntimeRoutingContext) -> bool:
        if rule.rule_id in {
            "C0_FAIL_LOCAL_ALT", "C0_UNKNOWN_LOCAL_ALT", "L2_FAIL_ALT",
            "L2_UNKNOWN_LOCAL_ALT", "L3_ABSENT_ALT", "L3_UNKNOWN_LOCAL_ALT",
        }:
            return context.alternative_search_allowed
        if rule.rule_id in {
            "C0_FAIL_LOCAL_ARB", "C0_UNKNOWN_LOCAL_ARB", "L2_FAIL_ARB",
            "L2_UNKNOWN_LOCAL_ARB", "L3_ABSENT_ARB", "L3_UNKNOWN_LOCAL_ARB",
        }:
            return not context.alternative_search_allowed
        if rule.rule_id == "ARB_NAV":
            return context.navigation_ready and context.deadline.status == DeadlineStatus.OPEN
        if rule.rule_id == "ARB_BACKUP":
            return not context.navigation_ready and context.retained_backup_valid
        if rule.rule_id == "ARB_TERMINAL":
            return not context.navigation_ready and not context.retained_backup_valid and context.terminal_evaluated and context.terminal_ready
        if rule.rule_id == "ARB_EVAL_TERMINAL":
            return not context.navigation_ready and not context.retained_backup_valid and not context.terminal_evaluated and context.deadline.status == DeadlineStatus.OPEN
        if rule.rule_id == "ARB_BOUNDARY":
            return not context.navigation_ready and not context.retained_backup_valid and not context.terminal_ready and (context.terminal_evaluated or context.deadline.status != DeadlineStatus.OPEN)
        return True

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
            return RoutingDecision(status, None, context.source_phase, None, False, False, False, reason, "SUPERVISOR_BLOCKS_UNRESOLVED_LOOKUP", False, False, False, reason)
        rule = matches[0]
        destination = RuntimePhase(rule.destination_phase)
        return RoutingDecision(
            RouteResolutionStatus.RESOLVED,
            rule.rule_id,
            context.source_phase,
            destination,
            destination not in {RuntimePhase.ARBITRATION, RuntimePhase.ASSURANCE_BOUNDARY},
            destination == RuntimePhase.ALT_SEARCH,
            destination in {RuntimePhase.ARBITRATION, RuntimePhase.BACKUP_EXECUTION, RuntimePhase.COMMIT},
            rule.failure_code or None,
            f"SUPERVISOR_INTERPRETED_{context.deadline.status.value}",
            destination in {RuntimePhase.ARBITRATION, RuntimePhase.BACKUP_EXECUTION},
            destination in {RuntimePhase.ARBITRATION, RuntimePhase.TERMINAL_EVALUATION},
            rule.commit_allowed,
            rule.guard,
        )


class Supervisor:
    def __init__(self, registry: AuthorityRegistry, transition_table: TransitionTable | None = None) -> None:
        self.registry = registry
        self.transition_table = transition_table

    def make_retained_backup_action(self, vector: tuple[float, float, float], action_id: str) -> SelectedAction:
        return make_action(vector, ActionRole.RETAINED_BACKUP, action_id, (self.registry.actuator.identity.value, self.registry.geometry.identity.value))

    def route_transition(self, event: PublicCycleEvent | str, runtime_context: RuntimeRoutingContext) -> RoutingDecision:
        if self.transition_table is None:
            return RoutingDecision(RouteResolutionStatus.BLOCKED_MISSING, None, runtime_context.source_phase, None, False, False, False, "ROUTING_RULE_MISSING", "SUPERVISOR_TRANSITION_TABLE_REQUIRED", False, False, False, "ROUTING_RULE_MISSING")
        return self.transition_table.resolve(event, runtime_context)

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
        if certified_candidate is not None and l3_result is not None and l3_result.status == CertificateStatus.PASS and l3_result.prepared_bundle is not None and l3_result.candidate_identity == certified_candidate.identity and deadline.status == DeadlineStatus.OPEN:
            role = ActionRole.PRIMARY_NAVIGATION if certified_candidate.role == CandidateRole.PRIMARY else ActionRole.ALTERNATIVE_NAVIGATION
            action = make_action(certified_candidate.vector, role, certified_candidate.identity.value, (self.registry.geometry.identity.value, self.registry.actuator.identity.value, l3_result.evidence_identity or ""))
            return SupervisorDecision(snapshot.cycle_index, snapshot.identity, action, True, "TIMELY_CERTIFIED_NAVIGATION_WITH_PREPARED_TOKEN", "ARB_NAV", l3_result.prepared_bundle)
        if backup_valid and retained_backup_action is not None and retained_backup_action.role == ActionRole.RETAINED_BACKUP:
            return SupervisorDecision(snapshot.cycle_index, snapshot.identity, retained_backup_action, True, "STILL_VALID_RETAINED_BACKUP", "ARB_BACKUP")
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
