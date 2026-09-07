import unittest

from reproduction.runtime.active_runtime_assurance_v2.runtime_types import CertificateStatus
from reproduction.runtime.active_runtime_assurance_v2.tests.public_cycle_test_support import build_public_cycle, start_and_run


class PublicCycleL3FailTests(unittest.TestCase):
    def test_l3_fail_cannot_commit_uncertified_navigation(self):
        system = build_public_cycle({"l3": CertificateStatus.FAIL})
        _, result = start_and_run(system)
        self.assertEqual(system["plant"].commit_count, 0)
        self.assertFalse(result.committed)
        self.assertTrue(result.boundary)


if __name__ == "__main__":
    unittest.main()
