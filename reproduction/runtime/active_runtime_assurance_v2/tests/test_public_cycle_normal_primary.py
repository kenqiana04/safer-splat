import unittest

from reproduction.runtime.active_runtime_assurance_v2.runtime_types import ActionRole, PublicCyclePhase
from reproduction.runtime.active_runtime_assurance_v2.tests.public_cycle_test_support import build_public_cycle, start_and_run


class PublicCycleNormalPrimaryTests(unittest.TestCase):
    def test_full_primary_path_commits_through_existing_runner(self):
        system = build_public_cycle()
        start, result = start_and_run(system)
        self.assertTrue(start.ready)
        self.assertTrue(result.committed)
        self.assertEqual(result.action_role, ActionRole.PRIMARY_NAVIGATION)
        ordered = list(result.phase_history)
        for left, right in zip((PublicCyclePhase.L1_IMMEDIATE_CERTIFICATION, PublicCyclePhase.PRIMARY_PROPOSAL, PublicCyclePhase.PRIMARY_C0, PublicCyclePhase.PRIMARY_L2, PublicCyclePhase.PRIMARY_L3, PublicCyclePhase.ARBITRATION, PublicCyclePhase.COMMIT), (PublicCyclePhase.PRIMARY_PROPOSAL, PublicCyclePhase.PRIMARY_C0, PublicCyclePhase.PRIMARY_L2, PublicCyclePhase.PRIMARY_L3, PublicCyclePhase.ARBITRATION, PublicCyclePhase.COMMIT, PublicCyclePhase.TRACE_APPEND)):
            self.assertLess(ordered.index(left), ordered.index(right))
        self.assertEqual(system["counters"]["l1"], 1)
        self.assertEqual(system["plant"].commit_count, 1)

    def test_zero_vector_primary_keeps_primary_role(self):
        system = build_public_cycle({"primary_vector": (0.0, 0.0, 0.0)})
        _, result = start_and_run(system)
        self.assertEqual(result.action_role, ActionRole.PRIMARY_NAVIGATION)


if __name__ == "__main__":
    unittest.main()
