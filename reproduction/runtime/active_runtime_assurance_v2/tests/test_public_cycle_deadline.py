import unittest

from reproduction.runtime.active_runtime_assurance_v2.runtime_types import ActionRole, ActiveCycleRequest, CertificateStatus, DeadlineStatus
from reproduction.runtime.active_runtime_assurance_v2.tests.public_cycle_test_support import build_public_cycle, start_and_run


class PublicCycleDeadlineTests(unittest.TestCase):
    def test_warning_is_interpreted_by_supervisor_lookup_and_blocks_new_primary_stage(self):
        system = build_public_cycle({"l1_advance": 8.5})
        _, result = start_and_run(system)
        self.assertEqual(result.deadline_observations[-1].status, DeadlineStatus.WARNING)
        self.assertEqual(result.typed_stop_or_failure_reason, "ROUTING_RULE_MISSING")
        self.assertEqual(system["counters"]["proposal"], 0)

    def test_expired_with_valid_backup_routes_backup(self):
        system = build_public_cycle()
        _, first = start_and_run(system)
        system["config"].update({"l1": CertificateStatus.FAIL, "l1_advance": 10.0})
        request = ActiveCycleRequest(first.next_state.trial_id, 1, (1.0, 0.0, 0.0), None)
        result = system["coordinator"].run_cycle(first.next_state, request)
        self.assertEqual(result.action_role, ActionRole.RETAINED_BACKUP)
        self.assertEqual(result.final_supervisor_decision.rule_id, "ARB_BACKUP")


if __name__ == "__main__":
    unittest.main()
