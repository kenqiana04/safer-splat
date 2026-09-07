import unittest

from reproduction.runtime.active_runtime_assurance_v2.runtime_types import ActionRole, ActiveCycleRequest
from reproduction.runtime.active_runtime_assurance_v2.tests.public_cycle_test_support import build_public_cycle, start_and_run


class PublicCycleBackupFallbackTests(unittest.TestCase):
    def test_valid_backup_is_selected_only_by_supervisor(self):
        system = build_public_cycle()
        _, first = start_and_run(system)
        system["config"]["proposal"] = "FAIL"
        request = ActiveCycleRequest(first.next_state.trial_id, 1, (1.0, 0.0, 0.0), None)
        result = system["coordinator"].run_cycle(first.next_state, request)
        self.assertEqual(result.action_role, ActionRole.RETAINED_BACKUP)
        self.assertEqual(result.final_supervisor_decision.rule_id, "ARB_BACKUP")

    def test_invalid_backup_never_commits(self):
        system = build_public_cycle({"proposal": "FAIL"})
        _, result = start_and_run(system)
        self.assertNotEqual(result.action_role, ActionRole.RETAINED_BACKUP)
        self.assertEqual(system["plant"].commit_count, 0)


if __name__ == "__main__":
    unittest.main()
