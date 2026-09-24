from __future__ import annotations

import dataclasses
import unittest

from reproduction.runtime.active_runtime_assurance_v2.bounded_recovery import SOURCE as RECOVERY_SOURCE
from reproduction.runtime.active_runtime_assurance_v2.runtime_types import (
    CandidateIdentity,
    CandidateRole,
    CertificateStatus,
    DeadlineObservation,
    DeadlineStatus,
    L3Result,
    PreparedBackupBundle,
    PublicCycleEvent,
    RouteResolutionStatus,
    RuntimePhase,
    RuntimeRoutingContext,
    TerminalResult,
    make_candidate,
)
from reproduction.runtime.active_runtime_assurance_v2.tests.public_cycle_test_support import build_public_cycle


class InadmissibleRecoveryTerminalPredicateTests(unittest.TestCase):
    def setUp(self):
        self.system = build_public_cycle()
        self.supervisor = self.system["supervisor"]
        self.registry = self.system["registry"]
        self.snapshot = self.system["state"]
        self.candidate, self.l3 = self._certified_recovery()

    def _certified_recovery(self):
        candidate = make_candidate((0.1, 0.0, 0.0), CandidateRole.ALTERNATIVE, RECOVERY_SOURCE, "recovery-grant", self.snapshot)
        bundle = PreparedBackupBundle.create(
            candidate,
            self.snapshot,
            (((0.0, 0.0, 0.0), "backup:fixture"),),
            self.registry.geometry.identity.value,
            self.registry.actuator.identity.value,
            self.registry.dynamics.identity.value,
            None,
        )
        l3 = L3Result(CertificateStatus.PASS, "L3_PASS", candidate.identity, bundle, "l3:fixture")
        return candidate, l3

    def _context(self, deadline: DeadlineStatus, *, certified=True, backup_valid=False, terminal=True):
        return RuntimeRoutingContext(
            source_phase=RuntimePhase.ARBITRATION,
            deadline=DeadlineObservation(deadline, "FINAL_COMMIT_GUARD", 0.9, 0.1, "deadline:test"),
            authority_identity=self.registry.transition_table_identity,
            candidate_role=CandidateRole.ALTERNATIVE,
            candidate_identity=self.candidate.identity,
            candidate_available=True,
            retained_backup_present=backup_valid,
            retained_backup_valid=backup_valid,
            terminal_evaluated=True,
            terminal_evidence_eligible=terminal,
            certified_candidate_available=certified,
            candidate_source_type=RECOVERY_SOURCE,
        )

    def _terminal(self, eligible=True):
        return TerminalResult(CertificateStatus.PASS, "TERMINAL_PASS", eligible, None, "terminal:fixture")

    def test_warning_certified_recovery_terminal_uses_existing_arb_terminal(self):
        decision = self.supervisor.route_transition(PublicCycleEvent.ARBITRATE, self._context(DeadlineStatus.WARNING))
        self.assertEqual(decision.status, RouteResolutionStatus.RESOLVED)
        self.assertEqual(decision.rule_id, "ARB_TERMINAL")
        self.assertEqual(decision.destination_phase, RuntimePhase.COMMIT)

    def test_expired_certified_recovery_terminal_uses_existing_arb_terminal(self):
        decision = self.supervisor.route_transition(PublicCycleEvent.ARBITRATE, self._context(DeadlineStatus.EXPIRED))
        self.assertEqual(decision.status, RouteResolutionStatus.RESOLVED)
        self.assertEqual(decision.rule_id, "ARB_TERMINAL")
        self.assertEqual(decision.destination_phase, RuntimePhase.COMMIT)

    def test_arbitrate_keeps_existing_terminal_decision_identity(self):
        decision = self.supervisor.arbitrate(
            self.snapshot,
            self.candidate,
            self.l3,
            None,
            False,
            self._terminal(True),
            DeadlineObservation(DeadlineStatus.WARNING, "FINAL_COMMIT_GUARD", 0.9, 0.1, "deadline:test"),
        )
        self.assertEqual(decision.rule_id, "ARB_TERMINAL")
        self.assertTrue(decision.allows_commit)

    def test_identity_mismatch_fails_closed(self):
        mismatched = dataclasses.replace(self.l3, candidate_identity=CandidateIdentity("candidate:mismatch"))
        decision = self.supervisor.arbitrate(
            self.snapshot,
            self.candidate,
            mismatched,
            None,
            False,
            self._terminal(True),
            DeadlineObservation(DeadlineStatus.WARNING, "FINAL_COMMIT_GUARD", 0.9, 0.1, "deadline:test"),
        )
        self.assertEqual(decision.rule_id, "ARB_BOUNDARY")
        self.assertFalse(decision.allows_commit)
        self.assertIsNone(decision.selected_action)

    def test_missing_prepared_bundle_fails_closed(self):
        missing_bundle = dataclasses.replace(self.l3, prepared_bundle=None)
        decision = self.supervisor.arbitrate(
            self.snapshot,
            self.candidate,
            missing_bundle,
            None,
            False,
            self._terminal(True),
            DeadlineObservation(DeadlineStatus.EXPIRED, "FINAL_COMMIT_GUARD", 0.9, 0.1, "deadline:test"),
        )
        self.assertEqual(decision.rule_id, "ARB_BOUNDARY")
        self.assertFalse(decision.allows_commit)

    def test_l3_fail_does_not_match_terminal_row(self):
        decision = self.supervisor.route_transition(
            PublicCycleEvent.ARBITRATE,
            self._context(DeadlineStatus.WARNING, certified=False, terminal=True),
        )
        self.assertEqual(decision.status, RouteResolutionStatus.BLOCKED_MISSING)
        self.assertIsNone(decision.rule_id)

    def test_valid_backup_remains_higher_priority(self):
        decision = self.supervisor.route_transition(
            PublicCycleEvent.ARBITRATE,
            self._context(DeadlineStatus.WARNING, backup_valid=True, terminal=True),
        )
        self.assertEqual(decision.status, RouteResolutionStatus.RESOLVED)
        self.assertEqual(decision.rule_id, "ARB_BACKUP_GUARD")
        self.assertEqual(decision.destination_phase, RuntimePhase.BACKUP_EXECUTION)

    def test_open_deadline_keeps_navigation_behavior(self):
        decision = self.supervisor.route_transition(
            PublicCycleEvent.ARBITRATE,
            self._context(DeadlineStatus.OPEN, terminal=False),
        )
        self.assertEqual(decision.status, RouteResolutionStatus.RESOLVED)
        self.assertEqual(decision.rule_id, "ARB_NAV")
        self.assertEqual(decision.destination_phase, RuntimePhase.COMMIT)


if __name__ == "__main__":
    unittest.main()
