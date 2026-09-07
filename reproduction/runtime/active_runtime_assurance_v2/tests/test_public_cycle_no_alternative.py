import dataclasses
import unittest

from reproduction.runtime.active_runtime_assurance_v2.runtime_types import ActionRole, ActiveCycleRequest
from reproduction.runtime.active_runtime_assurance_v2.tests.public_cycle_test_support import build_public_cycle, start_and_run


class PublicCycleNoAlternativeTests(unittest.TestCase):
    def test_empty_native_inventory_returns_to_supervisor_and_backup(self):
        system = build_public_cycle()
        _, first = start_and_run(system)
        system["config"]["primary_vector"] = (0.2, 0.0, 0.0)
        second_state = first.next_state
        request = ActiveCycleRequest(second_state.trial_id, 1, (1.0, 0.0, 0.0), None)
        result = system["coordinator"].run_cycle(second_state, request)
        self.assertEqual(system["counters"]["alternative"], 1)
        self.assertIn("ALT_DONE", result.routing_rule_ids)
        self.assertEqual(result.action_role, ActionRole.RETAINED_BACKUP)

    def test_future_lawful_native_alternative_reuses_l1_and_gets_fresh_binding(self):
        system = build_public_cycle()
        _, first = start_and_run(system)
        system["config"].update({"primary_vector": (0.2, 0.0, 0.0), "alternatives": ((0.01, 0.0, 0.0),)})
        result = system["coordinator"].run_cycle(first.next_state, ActiveCycleRequest(first.next_state.trial_id, 1, (1.0, 0.0, 0.0), None))
        self.assertEqual(result.action_role, ActionRole.ALTERNATIVE_NAVIGATION)
        self.assertEqual(system["counters"]["l1"], 2)
        self.assertEqual(system["counters"]["bind"], 3)
        self.assertEqual(len(result.candidate_refs), 2)


if __name__ == "__main__":
    unittest.main()
