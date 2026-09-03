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
        return cls(tuple(TransitionRule(row["rule_id"], row["source_phase"], row.get("runtime_destination", row["destination_phase"]), row["commit_allowed"].lower() == "true", row.get("commit_authority", row["action_authority"]), row.get("failure_mapping", row["failure_code_if_any"])) for row in rows))


class Supervisor:
    def __init__(self, registry: AuthorityRegistry, transition_table: TransitionTable | None = None) -> None:
        self.registry = registry
        self.transition_table = transition_table

    def make_retained_backup_action(self, vector: tuple[float, float, float], action_id: str) -> SelectedAction:
        return make_action(vector, ActionRole.RETAINED_BACKUP, action_id, (self.registry.actuator.identity.value, self.registry.geometry.identity.value))

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
