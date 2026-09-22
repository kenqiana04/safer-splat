from __future__ import annotations

import dataclasses
import unittest

from reproduction.runtime.active_runtime_assurance_v2.bounded_recovery import SOURCE as RECOVERY_SOURCE
from reproduction.runtime.active_runtime_assurance_v2.runtime_types import (
    ActionRole,
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
    make_candidate,
)
from reproduction.runtime.active_runtime_assurance_v2.tests.public_cycle_test_support import build_public_cycle


class CertifiedRecoveryDeadlineBoundaryTests(unittest.TestCase):
    def setUp(self):
        self.system = build_public_cycle()
        self.table = self.system["supervisor"].transition_table
        self.snapshot = self.system["state"]
        self.authority = self.system["registry"].transition_table_identity

    def context(
        self,
        deadline: DeadlineStatus,
        *,
        source: str = RECOVERY_SOURCE,
        certified: bool = True,
        backup_valid: bool = False,
        terminal_eligible: bool = False,
        role: CandidateRole = CandidateRole.ALTERNATIVE,
    ) -> RuntimeRoutingContext:
        return RuntimeRoutingContext(
            source_phase=RuntimePhase.ARBITRATION,
            deadline=DeadlineObservation(deadline, "FINAL_COMMIT_GUARD", 0.9, 0.1, "deadline:test"),
            authority_identity=self.authority,
            candidate_role=role,
            candidate_identity=None if not certified else "candidate:fixture",
            candidate_available=True,
            retained_backup_present=backup_valid,
            retained_backup_valid=backup_valid,
            terminal_evaluated=True,
            terminal_evidence_eligible=terminal_eligible,
            certified_candidate_available=certified,
            candidate_source_type=source,
        )

    def route(self, context: RuntimeRoutingContext):
        return self.table.resolve(PublicCycleEvent.ARBITRATE, context)

    def test_t1_warning_certified_recovery_without_backup_selects_navigation(self):
        decision = self.route(self.context(DeadlineStatus.WARNING))
        self.assertEqual(decision.status, RouteResolutionStatus.RESOLVED)
        self.assertEqual(decision.rule_id, "ARB_RECOVERY_WARNING_CERTIFIED_NAVIGATION")
        self.assertEqual(decision.destination_phase, RuntimePhase.COMMIT)
        self.assertTrue(decision.commit_allowed)
        self.assertEqual(decision.action_authority, "CERTIFIED_NAVIGATION")
        self.assertFalse(decision.may_start_new_search)

    def test_t2_expired_certified_recovery_without_backup_is_explicit_boundary(self):
        decision = self.route(self.context(DeadlineStatus.EXPIRED))
        self.assertEqual(decision.status, RouteResolutionStatus.RESOLVED)
        self.assertEqual(decision.rule_id, "ARB_RECOVERY_EXPIRED_BOUNDARY")
        self.assertEqual(decision.destination_phase, RuntimePhase.ASSURANCE_BOUNDARY)
        self.assertFalse(decision.commit_allowed)
        self.assertFalse(decision.may_start_new_search)

    def test_t3_warning_valid_backup_keeps_existing_guard(self):
        decision = self.route(self.context(DeadlineStatus.WARNING, backup_valid=True))
        self.assertEqual(decision.rule_id, "ARB_BACKUP_GUARD")
        self.assertEqual(decision.destination_phase, RuntimePhase.BACKUP_EXECUTION)

    def test_t4_expired_valid_backup_keeps_existing_guard(self):
        decision = self.route(self.context(DeadlineStatus.EXPIRED, backup_valid=True))
        self.assertEqual(decision.rule_id, "ARB_BACKUP_GUARD")
        self.assertEqual(decision.destination_phase, RuntimePhase.BACKUP_EXECUTION)

    def test_t5_open_certified_recovery_keeps_navigation(self):
        decision = self.route(self.context(DeadlineStatus.OPEN))
        self.assertEqual(decision.rule_id, "ARB_NAV")
        self.assertEqual(decision.destination_phase, RuntimePhase.COMMIT)

    def test_t6_recovery_l2_unknown_cannot_match_new_boundary(self):
        decision = self.route(self.context(DeadlineStatus.WARNING, certified=False))
        self.assertEqual(decision.rule_id, "ARB_RECOVERY_WARNING_BOUNDARY")
        self.assertFalse(decision.commit_allowed)

    def test_t7_recovery_l3_fail_cannot_match_new_boundary(self):
        decision = self.route(self.context(DeadlineStatus.EXPIRED, certified=False))
        self.assertNotIn(decision.rule_id, {"ARB_RECOVERY_WARNING_BOUNDARY", "ARB_RECOVERY_EXPIRED_BOUNDARY"})

    def test_t8_identity_or_bundle_gap_cannot_match_new_boundary(self):
        decision = self.route(self.context(DeadlineStatus.WARNING, certified=False))
        self.assertEqual(decision.rule_id, "ARB_RECOVERY_WARNING_BOUNDARY")
        self.assertFalse(decision.commit_allowed)

    def test_t9_primary_or_alternative_source_cannot_match_recovery_rows(self):
        decision = self.route(self.context(DeadlineStatus.WARNING, source="PRIMARY_NATIVE_CBF_QP"))
        self.assertNotIn(decision.rule_id, {"ARB_RECOVERY_WARNING_BOUNDARY", "ARB_RECOVERY_EXPIRED_BOUNDARY"})

    def test_t10_warning_and_expired_rows_are_mutually_exclusive(self):
        warning = self.route(self.context(DeadlineStatus.WARNING))
        expired = self.route(self.context(DeadlineStatus.EXPIRED))
        self.assertEqual(warning.rule_id, "ARB_RECOVERY_WARNING_CERTIFIED_NAVIGATION")
        self.assertEqual(expired.rule_id, "ARB_RECOVERY_EXPIRED_BOUNDARY")
        self.assertNotEqual(warning.rule_id, expired.rule_id)

    def _certified_recovery(self):
        candidate = make_candidate((0.1, 0.0, 0.0), CandidateRole.ALTERNATIVE, RECOVERY_SOURCE, "recovery-grant", self.snapshot)
        candidate = dataclasses.replace(candidate, provenance=dataclasses.replace(candidate.provenance, lawful=True))
        registry = self.system["registry"]
        bundle = PreparedBackupBundle.create(
            candidate,
            self.snapshot,
            (((0.0, 0.0, 0.0), "backup:fixture"),),
            registry.geometry.identity.value,
            registry.actuator.identity.value,
            registry.dynamics.identity.value,
            None,
        )
        l3 = L3Result(CertificateStatus.PASS, "L3_PASS", candidate.identity, bundle, "l3:fixture")
        return candidate, l3

    def test_t11_supervisor_warning_selects_recovery_and_expired_stays_boundary(self):
        candidate, l3 = self._certified_recovery()
        warning = self.system["supervisor"].arbitrate(
            self.snapshot, candidate, l3, None, False, None,
            DeadlineObservation(DeadlineStatus.WARNING, "FINAL_COMMIT_GUARD", 0.9, 0.1, "deadline:test"),
        )
        self.assertEqual(warning.rule_id, "ARB_RECOVERY_WARNING_CERTIFIED_NAVIGATION")
        self.assertEqual(warning.selected_action.role, ActionRole.ALTERNATIVE_NAVIGATION)
        self.assertTrue(warning.allows_commit)
        expired = self.system["supervisor"].arbitrate(
            self.snapshot, candidate, l3, None, False, None,
            DeadlineObservation(DeadlineStatus.EXPIRED, "FINAL_COMMIT_GUARD", 0.9, 0.1, "deadline:test"),
        )
        self.assertEqual(expired.rule_id, "ARB_RECOVERY_EXPIRED_BOUNDARY")
        self.assertIsNone(expired.selected_action)
        self.assertFalse(expired.allows_commit)

    def test_t12_warning_action_preserves_candidate_and_authority_identity(self):
        candidate, l3 = self._certified_recovery()
        decision = self.system["supervisor"].arbitrate(
            self.snapshot, candidate, l3, None, False, None,
            DeadlineObservation(DeadlineStatus.WARNING, "FINAL_COMMIT_GUARD", 0.9, 0.1, "deadline:test"),
        )
        self.assertEqual(decision.rule_id, "ARB_RECOVERY_WARNING_CERTIFIED_NAVIGATION")
        self.assertEqual(decision.selected_action.role, ActionRole.ALTERNATIVE_NAVIGATION)
        self.assertEqual(decision.selected_action.source_identity, candidate.identity.value)
        self.assertEqual(decision.prepared_bundle.identity, l3.prepared_bundle.identity)
        self.assertIn(self.system["registry"].geometry.identity.value, decision.selected_action.authority_references)
        self.assertIn(self.system["registry"].actuator.identity.value, decision.selected_action.authority_references)
        self.assertIn(l3.evidence_identity, decision.selected_action.authority_references)

    def test_t13_identity_mismatch_blocks_warning_recovery_action(self):
        candidate, l3 = self._certified_recovery()
        mismatched_l3 = dataclasses.replace(l3, candidate_identity=CandidateIdentity("candidate:mismatch"))
        decision = self.system["supervisor"].arbitrate(
            self.snapshot, candidate, mismatched_l3, None, False, None,
            DeadlineObservation(DeadlineStatus.WARNING, "FINAL_COMMIT_GUARD", 0.9, 0.1, "deadline:test"),
        )
        self.assertEqual(decision.rule_id, "ARB_BOUNDARY")
        self.assertIsNone(decision.selected_action)
        self.assertFalse(decision.allows_commit)

    def test_t14_l3_fail_blocks_warning_recovery_action(self):
        candidate, l3 = self._certified_recovery()
        failed_l3 = dataclasses.replace(l3, status=CertificateStatus.FAIL, reason="L3_FAIL")
        decision = self.system["supervisor"].arbitrate(
            self.snapshot, candidate, failed_l3, None, False, None,
            DeadlineObservation(DeadlineStatus.WARNING, "FINAL_COMMIT_GUARD", 0.9, 0.1, "deadline:test"),
        )
        self.assertEqual(decision.rule_id, "ARB_BOUNDARY")
        self.assertIsNone(decision.selected_action)
        self.assertFalse(decision.allows_commit)


if __name__ == "__main__":
    unittest.main()
