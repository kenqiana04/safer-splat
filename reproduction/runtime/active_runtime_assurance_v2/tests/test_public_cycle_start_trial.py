import unittest

from reproduction.runtime.active_runtime_assurance_v2.runtime_types import CertificateStatus, PublicCyclePhase
from reproduction.runtime.active_runtime_assurance_v2.tests.public_cycle_test_support import build_public_cycle


class PublicCycleStartTrialTests(unittest.TestCase):
    def test_start_pass_establishes_ready_session(self):
        system = build_public_cycle()
        result = system["coordinator"].start_trial(system["state"], system["trial"])
        self.assertTrue(result.ready)
        self.assertEqual(result.phase_history[-1], PublicCyclePhase.TRIAL_READY)
        self.assertEqual(system["plant"].commit_count, 0)

    def test_start_fail_and_unknown_never_commit(self):
        for status in (CertificateStatus.FAIL, CertificateStatus.UNKNOWN):
            system = build_public_cycle({"start": status})
            result = system["coordinator"].start_trial(system["state"], system["trial"])
            self.assertFalse(result.ready)
            self.assertTrue(result.boundary)
            self.assertEqual(system["plant"].commit_count, 0)


if __name__ == "__main__":
    unittest.main()
