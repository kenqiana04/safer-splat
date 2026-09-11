import unittest

from reproduction.runtime.active_runtime_assurance_v2.runtime_types import (
    ActionRole,
    ActiveCycleRequest,
    CandidateRole,
    DeadlineObservation,
    DeadlineStatus,
    PublicCycleEvent,
    RouteResolutionStatus,
    RuntimePhase,
    RuntimeRoutingContext,
)
from reproduction.runtime.active_runtime_assurance_v2.tests.public_cycle_test_support import build_public_cycle


class DeadlineAwareBackupArbitrationRowTests(unittest.TestCase):
    def setUp(self):
        self.system = build_public_cycle()
        self.table = self.system["supervisor"].transition_table

    def context(
        self,
        deadline: DeadlineStatus,
        role: CandidateRole | None,
        *,
        candidate_available: bool,
        certified: bool,
        backup_present: bool,
        backup_valid: bool,
    ) -> RuntimeRoutingContext:
        return RuntimeRoutingContext(
            source_phase=RuntimePhase.ARBITRATION,
            deadline=DeadlineObservation(deadline, "FINAL_COMMIT_GUARD", 0.0, 1.0, "deadline:test"),
            authority_identity=self.system["registry"].transition_table_identity,
            candidate_role=role,
            candidate_available=candidate_available,
            retained_backup_present=backup_present,
            retained_backup_valid=backup_valid,
            reason_scope="NONE",
            certified_candidate_available=certified,
        )

    def assert_route(self, context: RuntimeRoutingContext, rule_id: str, destination: RuntimePhase) -> None:
        decision = self.table.resolve(PublicCycleEvent.ARBITRATE, context)
        self.assertEqual(decision.status, RouteResolutionStatus.RESOLVED)
        self.assertEqual(decision.rule_id, rule_id)
        self.assertEqual(decision.destination_phase, destination)

    def test_warning_certified_primary_valid_backup_uses_guard_row(self):
        self.assert_route(
            self.context(DeadlineStatus.WARNING, CandidateRole.PRIMARY, candidate_available=True, certified=True, backup_present=True, backup_valid=True),
            "ARB_BACKUP_GUARD",
            RuntimePhase.BACKUP_EXECUTION,
        )

    def test_warning_certified_alternative_valid_backup_uses_guard_row(self):
        self.assert_route(
            self.context(DeadlineStatus.WARNING, CandidateRole.ALTERNATIVE, candidate_available=True, certified=True, backup_present=True, backup_valid=True),
            "ARB_BACKUP_GUARD",
            RuntimePhase.BACKUP_EXECUTION,
        )

    def test_expired_certified_primary_valid_backup_uses_guard_row(self):
        self.assert_route(
            self.context(DeadlineStatus.EXPIRED, CandidateRole.PRIMARY, candidate_available=True, certified=True, backup_present=True, backup_valid=True),
            "ARB_BACKUP_GUARD",
            RuntimePhase.BACKUP_EXECUTION,
        )

    def test_open_certified_primary_valid_backup_keeps_navigation_row(self):
        self.assert_route(
            self.context(DeadlineStatus.OPEN, CandidateRole.PRIMARY, candidate_available=True, certified=True, backup_present=True, backup_valid=True),
            "ARB_NAV",
            RuntimePhase.COMMIT,
        )

    def test_warning_no_candidate_valid_backup_keeps_backup_row(self):
        self.assert_route(
            self.context(DeadlineStatus.WARNING, None, candidate_available=False, certified=False, backup_present=True, backup_valid=True),
            "ARB_BACKUP",
            RuntimePhase.BACKUP_EXECUTION,
        )

    def test_new_row_does_not_match_without_valid_backup(self):
        decision = self.table.resolve(
            PublicCycleEvent.ARBITRATE,
            self.context(DeadlineStatus.WARNING, CandidateRole.PRIMARY, candidate_available=True, certified=True, backup_present=True, backup_valid=False),
        )
        self.assertNotEqual(decision.rule_id, "ARB_BACKUP_GUARD")

    def test_new_row_does_not_match_uncertified_candidate(self):
        decision = self.table.resolve(
            PublicCycleEvent.ARBITRATE,
            self.context(DeadlineStatus.WARNING, CandidateRole.PRIMARY, candidate_available=True, certified=False, backup_present=True, backup_valid=True),
        )
        self.assertNotEqual(decision.rule_id, "ARB_BACKUP_GUARD")

    def test_supervisor_selection_identity_matches_guard_route(self):
        first = self.system["coordinator"].start_trial(self.system["state"], self.system["trial"])
        self.assertTrue(first.ready)
        candidate = self.system["primary_candidate"] if "primary_candidate" in self.system else None
        # Build the candidate/L3 evidence with the existing modules so the
        # final selector is exercised without bypassing authority identities.
        proposal = self.system["coordinator"].primary_proposal.propose(self.system["state"], (1.0, 0.0, 0.0))
        candidate = proposal.candidate
        l1 = self.system["coordinator"].l1_runtime.evaluate_cycle(self.system["state"])
        binding = self.system["coordinator"].l1_runtime.bind_attempt(l1, candidate, 0)
        c0, l2, l3 = self.system["supervisor"].certify_candidate(
            self.system["state"],
            candidate,
            l1,
            binding,
            self.system["coordinator"].c0_admission,
            self.system["coordinator"].l2_runtime,
            self.system["coordinator"].l3_runtime,
        )
        self.assertIsNotNone(c0)
        self.assertIsNotNone(l2)
        self.assertIsNotNone(l3)
        backup = self.system["supervisor"].make_retained_backup_action((0.0, 0.0, 0.0), "backup:fixture")
        decision = self.system["supervisor"].arbitrate(
            self.system["state"],
            candidate,
            l3,
            backup,
            True,
            None,
            DeadlineObservation(DeadlineStatus.WARNING, "FINAL_COMMIT_GUARD", 0.9, 0.1, "deadline:test"),
        )
        self.assertEqual(decision.rule_id, "ARB_BACKUP_GUARD")
        self.assertEqual(decision.selected_action.role, ActionRole.RETAINED_BACKUP)

    def test_public_cycle_reuses_existing_backup_commit_path_at_warning_guard(self):
        _, first = (
            self.system["coordinator"].start_trial(self.system["state"], self.system["trial"]),
            self.system["coordinator"].run_cycle(self.system["state"], self.system["request"]),
        )
        self.system["config"]["l3_advance"] = 8.5
        second = self.system["coordinator"].run_cycle(
            first.next_state,
            ActiveCycleRequest(first.next_state.trial_id, 1, (1.0, 0.0, 0.0), None),
        )
        self.assertEqual(second.action_role, ActionRole.RETAINED_BACKUP)
        self.assertEqual(second.final_supervisor_decision.rule_id, "ARB_BACKUP_GUARD")
        self.assertIn("ARB_BACKUP_GUARD", second.routing_rule_ids)
        self.assertIn("BACKUP_COMMIT", second.routing_rule_ids)
        self.assertTrue(second.committed)
        self.assertEqual(self.system["plant"].commit_count, 2)
        self.assertEqual(len(self.system["trace_writer"].records), 2)


if __name__ == "__main__":
    unittest.main()
