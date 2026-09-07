import unittest

from reproduction.runtime.active_runtime_assurance_v2.runtime_types import ActionRole, CertificateStatus
from reproduction.runtime.active_runtime_assurance_v2.tests.public_cycle_test_support import build_public_cycle, start_and_run


class PublicCycleUnknownRouteTests(unittest.TestCase):
    def test_global_l1_unknown_routes_without_proposal_or_plant(self):
        system = build_public_cycle({"l1": CertificateStatus.UNKNOWN})
        _, result = start_and_run(system)
        self.assertEqual(system["counters"]["proposal"], 0)
        self.assertEqual(system["plant"].commit_count, 0)
        self.assertTrue(result.boundary)

    def test_stage_exception_never_falls_back_to_desired_control(self):
        system = build_public_cycle({"proposal": "EXCEPTION"})
        _, result = start_and_run(system)
        self.assertFalse(result.committed)
        self.assertEqual(system["plant"].commit_count, 0)
        self.assertNotEqual(result.action_role, ActionRole.PRIMARY_NAVIGATION)
        self.assertEqual(system["counters"]["proposal"], 1)


if __name__ == "__main__":
    unittest.main()
