import importlib.util
from pathlib import Path
import sys
import unittest

ROOT = Path(__file__).resolve().parents[1]
SPEC = importlib.util.spec_from_file_location("checker", ROOT / "model_check_backup_token_lifecycle_v2.py")
CHECKER = importlib.util.module_from_spec(SPEC)
assert SPEC.loader
sys.modules[SPEC.name] = CHECKER
SPEC.loader.exec_module(CHECKER)


class BackupTokenSchemaTests(unittest.TestCase):
    def test_01_incomplete_bundle_cannot_prepare(self):
        with self.assertRaisesRegex(ValueError, "INCOMPLETE_WITNESS"):
            CHECKER.prepare(CHECKER.make_bundle(tail=0))

    def test_02_prepared_is_not_executable(self):
        self.assertFalse(CHECKER.executable(CHECKER.prepare(CHECKER.make_bundle())))

    def test_03_activation_is_k_plus_one(self):
        prepared = CHECKER.prepare(CHECKER.make_bundle(cycle=8))
        active = CHECKER.activate(prepared, selected_candidate="candidate-A", commit_success=True, exact_identity=True)
        self.assertEqual(active.activation_cycle, 9)

    def test_04_nonselected_prepared_aborts(self):
        prepared = CHECKER.prepare(CHECKER.make_bundle())
        token = CHECKER.activate(prepared, selected_candidate="other", commit_success=True, exact_identity=True)
        self.assertEqual(token.phase, "ABORTED_PREPARED")

    def test_05_state_mismatch_fails_validity(self):
        prepared = CHECKER.prepare(CHECKER.make_bundle())
        active = CHECKER.activate(prepared, selected_candidate="candidate-A", commit_success=True, exact_identity=True)
        self.assertFalse(CHECKER.still_valid(active, current_cycle=5, current_state="wrong"))

    def test_06_invalid_is_absorbing(self):
        prepared = CHECKER.prepare(CHECKER.make_bundle())
        active = CHECKER.activate(prepared, selected_candidate="candidate-A", commit_success=True, exact_identity=True)
        invalid = CHECKER.invalidate(active)
        self.assertEqual(CHECKER.invalidate(invalid).status, "INVALID")

    def test_07_no_advance_before_commit(self):
        prepared = CHECKER.prepare(CHECKER.make_bundle())
        active = CHECKER.activate(prepared, selected_candidate="candidate-A", commit_success=True, exact_identity=True)
        self.assertEqual(CHECKER.consume(active, action_id="backup-0", commit_success=False).cursor, 0)

    def test_08_double_consumption_rejected(self):
        prepared = CHECKER.prepare(CHECKER.make_bundle())
        active = CHECKER.activate(prepared, selected_candidate="candidate-A", commit_success=True, exact_identity=True)
        once = CHECKER.consume(active, action_id="backup-0", commit_success=True)
        self.assertEqual(CHECKER.consume(once, action_id="backup-0", commit_success=True).status, "INVALID")

    def test_09_last_action_exhausts_without_terminal_authority(self):
        prepared = CHECKER.prepare(CHECKER.make_bundle(tail=1))
        active = CHECKER.activate(prepared, selected_candidate="candidate-A", commit_success=True, exact_identity=True)
        exhausted = CHECKER.consume(active, action_id="backup-0", commit_success=True)
        self.assertEqual(exhausted.status, "EXHAUSTED")
        self.assertFalse(exhausted.terminal_authorized)

    def test_10_expired_deadline_allows_valid_retained_selection(self):
        prepared = CHECKER.prepare(CHECKER.make_bundle())
        active = CHECKER.activate(prepared, selected_candidate="candidate-A", commit_success=True, exact_identity=True)
        self.assertTrue(CHECKER.backup_selectable("DEADLINE_EXPIRED", active))

    def test_11_expired_deadline_blocks_discovery(self):
        self.assertFalse(CHECKER.discovery_allowed("DEADLINE_EXPIRED"))

    def test_12_atomic_handoff_has_one_active_and_bundle_is_immutable(self):
        old = CHECKER.activate(CHECKER.prepare(CHECKER.make_bundle("old", 3)), selected_candidate="old", commit_success=True, exact_identity=True)
        prepared = CHECKER.prepare(CHECKER.make_bundle())
        old_after, new = CHECKER.atomic_handoff(old, prepared, selected_candidate="candidate-A", commit_success=True, exact_identity=True)
        self.assertEqual(old_after.phase, "RETIRED_SUPERSEDED")
        self.assertEqual(new.phase, "ACTIVE")
        self.assertEqual(new.bundle, prepared.bundle)


if __name__ == "__main__":
    unittest.main()
