import unittest

from reproduction.runtime.active_runtime_assurance_v2.tests.public_cycle_test_support import build_public_cycle, start_and_run


class PublicCycleBoundaryTests(unittest.TestCase):
    def test_boundary_has_no_plant_or_fake_next_state(self):
        system = build_public_cycle({"proposal": "FAIL"})
        _, result = start_and_run(system)
        self.assertTrue(result.boundary)
        self.assertFalse(result.committed)
        self.assertIsNone(result.next_state)
        self.assertIsNone(result.final_supervisor_decision.selected_action)
        self.assertEqual(system["plant"].commit_count, 0)
        self.assertEqual(len(system["trace_writer"].records), 1)


if __name__ == "__main__":
    unittest.main()
