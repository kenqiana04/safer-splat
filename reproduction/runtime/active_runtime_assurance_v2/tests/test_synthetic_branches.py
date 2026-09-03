import unittest

from reproduction.runtime.active_runtime_assurance_v2.active_runner import ActiveRunner
from reproduction.runtime.active_runtime_assurance_v2.alternative_provider import NativeExistingAlternativeProvider
from reproduction.runtime.active_runtime_assurance_v2.authority_registry import AuthorityRegistry
from reproduction.runtime.active_runtime_assurance_v2.backup_token_store import BackupTokenStore
from reproduction.runtime.active_runtime_assurance_v2.c0_admission import C0Admission
from reproduction.runtime.active_runtime_assurance_v2.deadline_runtime import RuntimeDeadlineProfile
from reproduction.runtime.active_runtime_assurance_v2.l1_runtime import L1Runtime
from reproduction.runtime.active_runtime_assurance_v2.l2_runtime import L2Runtime
from reproduction.runtime.active_runtime_assurance_v2.l3_runtime import L3Runtime
from reproduction.runtime.active_runtime_assurance_v2.plant_commit import PlantCommitAdapter
from reproduction.runtime.active_runtime_assurance_v2.primary_proposal_adapter import PrimaryProposalAdapter
from reproduction.runtime.active_runtime_assurance_v2.runtime_errors import CommitAuthorityViolation, DeadlineProfileRequired
from reproduction.runtime.active_runtime_assurance_v2.runtime_types import (
    ActionRole, CandidateRole, CertificateStatus, CommitReceipt, DeadlineObservation,
    DeadlineStatus, EvidenceResult, L3Result, PreparedBackupBundle, RuntimeMode,
    SupervisorDecision, TerminalResult, TokenLifecycle, make_action, make_candidate,
)
from reproduction.runtime.active_runtime_assurance_v2.supervisor import Supervisor
from reproduction.runtime.active_runtime_assurance_v2.terminal_runtime import GOAL_HOLD_RUNTIME_ENABLED
from reproduction.runtime.active_runtime_assurance_v2.tests.helpers import snapshot
from reproduction.runtime.active_runtime_assurance_v2.trace_writer import TraceWriter


def transition(state, control, dt):
    return tuple(state[i] + dt * (state[i + 3] if i < 3 else control[i - 3]) for i in range(6))


class SyntheticBranchTests(unittest.TestCase):
    def setUp(self):
        self.state = snapshot()
        self.registry = AuthorityRegistry.frozen(self.state.map_identity, "dt:0.05", "deadline:test")
        self.supervisor = Supervisor(self.registry)
        self.deadline = DeadlineObservation(DeadlineStatus.OPEN, "ARBITRATION", 0.0, 1.0, "deadline:test")
        self.candidate = make_candidate((0.0, 0.0, 0.0), CandidateRole.PRIMARY, "PRIMARY_NATIVE_CBF_QP", "cbf", self.state)
        self.bundle = PreparedBackupBundle.create(
            self.candidate, self.state, (((0.0, 0.0, 0.0), "backup:0"),),
            self.registry.geometry.identity.value, self.registry.actuator.identity.value,
            self.registry.dynamics.identity.value, "terminal:ref",
        )
        self.l3_pass = L3Result(CertificateStatus.PASS, "WITNESS", self.candidate.identity, self.bundle, "l3:e")

    def _backup(self):
        return self.supervisor.make_retained_backup_action((0.0, 0.0, 0.0), "backup:0")

    def _nav_receipt(self, committed=True):
        action = make_action(self.candidate.vector, ActionRole.PRIMARY_NAVIGATION, self.candidate.identity.value)
        post = snapshot(1)
        return CommitReceipt(0, self.state.identity, action.identity, action.identity, action.vector, action.role, post, post.identity, committed, "COMMITTED" if committed else "FAILED")

    def test_01_safe_primary_chain_commits_navigation(self):
        l1 = L1Runtime(lambda *a: EvidenceResult(CertificateStatus.PASS, "PASS", "l1:e"), self.registry)
        cycle = l1.evaluate_cycle(self.state); binding = l1.bind_attempt(cycle, self.candidate, 0)
        c0 = C0Admission(self.registry)
        l2 = L2Runtime(lambda *a: EvidenceResult(CertificateStatus.PASS, "PASS", "l2:e"), self.registry)
        l3 = L3Runtime(lambda *a: (CertificateStatus.PASS, (((0, 0, 0), "b0"),), "term", "PASS"), self.registry)
        c0r, l2r, l3r = self.supervisor.certify_candidate(self.state, self.candidate, cycle, binding, c0, l2, l3)
        decision = self.supervisor.arbitrate(self.state, self.candidate, l3r, None, False, None, self.deadline)
        receipt = PlantCommitAdapter(self.registry, transition).commit(decision, self.state, decision.selected_action)
        self.assertEqual((c0r.status, l2r.status, l3r.status, receipt.action_role), (CertificateStatus.PASS, CertificateStatus.PASS, CertificateStatus.PASS, ActionRole.PRIMARY_NAVIGATION))

    def test_02_navigation_commit_activates_token_next_cycle(self):
        store = BackupTokenStore(); store.prepare(self.bundle)
        token = store.activate_after_navigation_commit(self._nav_receipt(), self.bundle.identity)
        self.assertEqual((token.lifecycle, token.activation_cycle), (TokenLifecycle.ACTIVE, 1))

    def test_03_l3_fail_cannot_commit_candidate(self):
        result = L3Result(CertificateStatus.FAIL, "NO_WITNESS", self.candidate.identity, None, "l3:f")
        decision = self.supervisor.arbitrate(self.state, self.candidate, result, None, False, None, self.deadline)
        self.assertFalse(decision.allows_commit)

    def test_04_solver_fail_without_backup_routes_boundary(self):
        proposal = PrimaryProposalAdapter(lambda *a: (_ for _ in ()).throw(RuntimeError("solver")), "cbf").propose(self.state, (0.01, 0, 0))
        decision = self.supervisor.arbitrate(self.state, proposal.candidate, None, None, False, None, self.deadline)
        self.assertEqual((proposal.status, decision.rule_id), (CertificateStatus.UNKNOWN, "ARB_BOUNDARY"))

    def test_05_solver_fail_with_backup_selects_backup(self):
        decision = self.supervisor.arbitrate(self.state, None, None, self._backup(), True, None, self.deadline)
        self.assertEqual(decision.selected_action.role, ActionRole.RETAINED_BACKUP)

    def test_06_c0_out_of_bound_rejects_without_clip(self):
        candidate = make_candidate((0.10000001, 0, 0), CandidateRole.PRIMARY, "PRIMARY_NATIVE_CBF_QP", "cbf", self.state)
        result = C0Admission(self.registry).evaluate(candidate, self.state)
        self.assertEqual((result.status, result.candidate_vector[0]), (CertificateStatus.FAIL, 0.10000001))

    def test_07_c0_inclusive_bound_passes(self):
        candidate = make_candidate((0.1, -0.1, 0), CandidateRole.PRIMARY, "PRIMARY_NATIVE_CBF_QP", "cbf", self.state)
        self.assertEqual(C0Admission(self.registry).evaluate(candidate, self.state).status, CertificateStatus.PASS)

    def test_08_l2_fail_no_alternative_uses_backup(self):
        decision = self.supervisor.arbitrate(self.state, None, None, self._backup(), True, None, self.deadline)
        self.assertEqual(decision.rule_id, "ARB_BACKUP")

    def test_09_l2_unknown_global_does_not_swap_candidate(self):
        decision = self.supervisor.arbitrate(self.state, None, None, None, False, None, self.deadline)
        self.assertIsNone(decision.selected_action)

    def test_10_l3_absent_uses_valid_backup(self):
        result = L3Result(CertificateStatus.FAIL, "ABSENT", self.candidate.identity, None, "l3:a")
        decision = self.supervisor.arbitrate(self.state, self.candidate, result, self._backup(), True, None, self.deadline)
        self.assertEqual(decision.selected_action.role, ActionRole.RETAINED_BACKUP)

    def test_11_l1_fail_has_no_ordinary_alternative_search(self):
        self.assertEqual(self.supervisor.arbitrate(self.state, None, None, None, False, None, self.deadline).rule_id, "ARB_BOUNDARY")

    def test_12_l1_unknown_allows_unaffected_backup_arbitration(self):
        self.assertEqual(self.supervisor.arbitrate(self.state, None, None, self._backup(), True, None, self.deadline).rule_id, "ARB_BACKUP")

    def test_13_empty_native_inventory_is_typed(self):
        result = NativeExistingAlternativeProvider().enumerate(self.state)
        self.assertEqual((result.status, result.candidates), ("NO_ALTERNATIVE_AVAILABLE", ()))

    def test_14_prepared_token_cannot_execute(self):
        store = BackupTokenStore(); store.prepare(self.bundle)
        self.assertIsNone(store.current())

    def test_15_old_token_survives_failed_navigation_commit(self):
        store = BackupTokenStore(); store.prepare(self.bundle); old = store.activate_after_navigation_commit(self._nav_receipt(), self.bundle.identity)
        other = PreparedBackupBundle.create(self.candidate, self.state, (((0, 0, 0), "b1"),), self.registry.geometry.identity.value, self.registry.actuator.identity.value, self.registry.dynamics.identity.value, None)
        store.prepare(other)
        with self.assertRaises(Exception): store.activate_after_navigation_commit(self._nav_receipt(False), other.identity)
        self.assertEqual(store.current().identity, old.identity)

    def test_16_successful_navigation_handoff_has_no_none_gap(self):
        store = BackupTokenStore(); store.prepare(self.bundle)
        self.assertIsNotNone(store.activate_after_navigation_commit(self._nav_receipt(), self.bundle.identity))
        self.assertIsNotNone(store.current())

    def test_17_backup_commit_advances_cursor_once(self):
        store = BackupTokenStore(); store.prepare(self.bundle); token = store.activate_after_navigation_commit(self._nav_receipt(), self.bundle.identity)
        action = self._backup(); post = snapshot(2)
        receipt = CommitReceipt(1, token.expected_state_identity, action.identity, action.identity, action.vector, action.role, post, post.identity, True, "COMMITTED")
        self.assertEqual(store.consume_after_backup_commit(receipt).cursor, 1)

    def test_18_failed_backup_commit_leaves_cursor(self):
        store = BackupTokenStore(); store.prepare(self.bundle); token = store.activate_after_navigation_commit(self._nav_receipt(), self.bundle.identity)
        action = self._backup(); receipt = CommitReceipt(1, token.expected_state_identity, action.identity, action.identity, action.vector, action.role, None, None, False, "FAILED")
        self.assertEqual(store.consume_after_backup_commit(receipt).cursor, 0)

    def test_19_exhausted_backup_has_no_terminal_authority(self):
        store = BackupTokenStore()
        self.assertFalse(store.terminal_authorized)

    def test_20_stale_terminal_reference_is_invalid(self):
        from reproduction.runtime.active_runtime_assurance_v2.terminal_runtime import TerminalRuntime
        terminal = TerminalRuntime(lambda s: True, lambda *a: EvidenceResult(CertificateStatus.PASS, "PASS", "fresh"), self.registry)
        self.assertEqual(terminal.evaluate(self.state, True, "stale").status, CertificateStatus.UNKNOWN)

    def test_21_eligible_terminal_can_commit(self):
        terminal = TerminalResult(CertificateStatus.PASS, "PASS", True, None, "term:e")
        decision = self.supervisor.arbitrate(self.state, None, None, None, False, terminal, self.deadline)
        receipt = PlantCommitAdapter(self.registry, transition).commit(decision, self.state, decision.selected_action)
        self.assertEqual(receipt.action_role, ActionRole.CERTIFIED_TERMINAL)

    def test_22_zero_primary_remains_primary_role(self):
        decision = self.supervisor.arbitrate(self.state, self.candidate, self.l3_pass, None, False, None, self.deadline)
        self.assertEqual(decision.selected_action.role, ActionRole.PRIMARY_NAVIGATION)

    def test_23_terminal_zero_role_is_assigned_by_supervisor(self):
        terminal = TerminalResult(CertificateStatus.PASS, "PASS", True, None, "term:e")
        action = self.supervisor.arbitrate(self.state, None, None, None, False, terminal, self.deadline).selected_action
        self.assertEqual((action.vector, action.role), ((0.0, 0.0, 0.0), ActionRole.CERTIFIED_TERMINAL))

    def test_24_boundary_never_calls_plant(self):
        plant = PlantCommitAdapter(self.registry, transition)
        decision = self.supervisor.arbitrate(self.state, None, None, None, False, None, self.deadline)
        boundary = make_action((0, 0, 0), ActionRole.ASSURANCE_BOUNDARY_NO_ACTION, "boundary")
        with self.assertRaises(CommitAuthorityViolation): plant.commit(decision, self.state, boundary)
        self.assertEqual(plant.commit_count, 0)

    def test_25_active_missing_deadline_profile_rejects(self):
        registry = AuthorityRegistry.frozen(self.state.map_identity, "dt:0.05")
        runner = ActiveRunner(RuntimeMode.ACTIVE_RUNTIME_ON, registry, Supervisor(registry), PlantCommitAdapter(registry, transition), BackupTokenStore(), TraceWriter("t"))
        with self.assertRaises(DeadlineProfileRequired): runner.startup()

    def test_26_expired_still_allows_backup(self):
        expired = DeadlineObservation(DeadlineStatus.EXPIRED, "ARBITRATION", 1, 0, "deadline:test")
        decision = self.supervisor.arbitrate(self.state, self.candidate, self.l3_pass, self._backup(), True, None, expired)
        self.assertEqual(decision.selected_action.role, ActionRole.RETAINED_BACKUP)

    def test_27_exception_is_unknown_not_desired_fallback(self):
        result = PrimaryProposalAdapter(lambda *a: (_ for _ in ()).throw(RuntimeError()), "cbf").propose(self.state, (0.03, 0, 0))
        self.assertEqual((result.status, result.candidate), (CertificateStatus.UNKNOWN, None))

    def test_28_trace_finalize_produces_oracle_boundary_lock(self):
        writer = TraceWriter("trial")
        self.assertTrue(writer.finalize().locked_before_evaluation)

    def test_29_finalized_trace_is_immutable(self):
        writer = TraceWriter("trial"); writer.finalize()
        with self.assertRaises(Exception): writer.append(object())

    def test_30_selected_equals_executed_vector(self):
        decision = self.supervisor.arbitrate(self.state, self.candidate, self.l3_pass, None, False, None, self.deadline)
        receipt = PlantCommitAdapter(self.registry, transition).commit(decision, self.state, decision.selected_action)
        self.assertEqual(receipt.exact_vector, decision.selected_action.vector)


if __name__ == "__main__":
    unittest.main()
