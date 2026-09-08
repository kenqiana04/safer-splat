"""Sole Active Runtime V2 action-selection authority."""

from __future__ import annotations

import csv
import json
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
        if len(rules) != 43 or len({rule.rule_id for rule in rules}) != 43:
            raise ValueError("TRANSITION_TABLE_NOT_43_EXACTLY_ONCE")
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
            return TransitionTable._certified_candidate_fact(context) and context.deadline.status == DeadlineStatus.OPEN
        if rule.rule_id == "ARB_BACKUP":
            return not TransitionTable._certified_candidate_fact(context) and context.retained_backup_valid
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
        return self.transition_table.resolve(event, runtime_context)

    def routing_guard_block(self, runtime_context: RuntimeRoutingContext, reason: str = "ROUTING_STATE_REPEATED") -> RoutingDecision:
        """Supervisor-owned typed block for an impossible repeated route state."""
        return TransitionTable._blocked_decision(runtime_context, RouteResolutionStatus.BLOCKED_AMBIGUOUS, reason)

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
