import unittest

from reproduction.runtime.active_runtime_assurance_v2.authority_registry import AuthorityRegistry
from reproduction.runtime.active_runtime_assurance_v2.backup_token_store import BackupTokenStore
from reproduction.runtime.active_runtime_assurance_v2.runtime_errors import TokenLifecycleViolation
from reproduction.runtime.active_runtime_assurance_v2.runtime_types import (
    ActionRole, CandidateRole, CommitReceipt, PreparedBackupBundle, TokenLifecycle,
    make_action, make_candidate,
)
from reproduction.runtime.active_runtime_assurance_v2.tests.helpers import snapshot


def bundle_and_receipt(committed=True):
    state = snapshot()
    registry = AuthorityRegistry.frozen(state.map_identity, "dt:0.05")
    candidate = make_candidate((0.01,0,0), CandidateRole.PRIMARY, "PRIMARY_NATIVE_CBF_QP", "cbf", state)
    bundle = PreparedBackupBundle.create(candidate, state, (((0.0,0.0,0.0),"backup:0"), ((0.0,0.0,0.0),"backup:1")), registry.geometry.identity.value, registry.actuator.identity.value, registry.dynamics.identity.value, "terminal:ref")
    action = make_action(candidate.vector, ActionRole.PRIMARY_NAVIGATION, candidate.identity.value)
    post = snapshot(1)
    receipt = CommitReceipt(0, state.identity, action.identity, action.identity, action.vector, action.role, post, post.identity, committed, "COMMITTED" if committed else "FAILED")
    return registry, bundle, receipt


class BackupTokenStoreTests(unittest.TestCase):
    def test_prepared_is_not_active(self):
        _, bundle, _ = bundle_and_receipt()
        store = BackupTokenStore(); store.prepare(bundle)
        self.assertIsNone(store.current())

    def test_navigation_commit_atomic_activation(self):
        registry, bundle, receipt = bundle_and_receipt()
        store = BackupTokenStore(); store.prepare(bundle)
        token = store.activate_after_navigation_commit(receipt, bundle.identity)
        self.assertEqual(token.lifecycle, TokenLifecycle.ACTIVE)
        self.assertEqual(token.activation_cycle, 1)
        self.assertEqual(store.validate(snapshot(1), registry).status.value, "PASS")

    def test_failed_navigation_keeps_old_token(self):
        _, bundle, receipt = bundle_and_receipt()
        store = BackupTokenStore(); store.prepare(bundle)
        with self.assertRaises(TokenLifecycleViolation):
            store.activate_after_navigation_commit(CommitReceipt(**{**receipt.__dict__, "committed": False}), bundle.identity)
        self.assertIsNone(store.current())

    def test_backup_cursor_advances_only_after_success(self):
        registry, bundle, receipt = bundle_and_receipt()
        store = BackupTokenStore(); store.prepare(bundle); token = store.activate_after_navigation_commit(receipt, bundle.identity)
        vector, action_id = token.current_action
        action = make_action(vector, ActionRole.RETAINED_BACKUP, action_id)
        failed = CommitReceipt(1, snapshot(1).identity, action.identity, action.identity, vector, action.role, snapshot(2), snapshot(2).identity, False, "FAILED")
        self.assertEqual(store.consume_after_backup_commit(failed).cursor, 0)
        passed = CommitReceipt(**{**failed.__dict__, "committed": True, "reason": "COMMITTED"})
        self.assertEqual(store.consume_after_backup_commit(passed).cursor, 1)

    def test_exhausted_does_not_authorize_terminal(self):
        _, bundle, receipt = bundle_and_receipt()
        store = BackupTokenStore(); store.prepare(bundle); token = store.activate_after_navigation_commit(receipt, bundle.identity)
        for cycle in (1,2):
            vector, action_id = store.current().current_action
            action = make_action(vector, ActionRole.RETAINED_BACKUP, action_id)
            pre = snapshot(cycle); post = snapshot(cycle+1)
            store.consume_after_backup_commit(CommitReceipt(cycle, pre.identity, action.identity, action.identity, vector, action.role, post, post.identity, True, "COMMITTED"))
        self.assertEqual(store.current().lifecycle, TokenLifecycle.EXHAUSTED)
        self.assertFalse(store.terminal_authorized)


if __name__ == "__main__": unittest.main()
