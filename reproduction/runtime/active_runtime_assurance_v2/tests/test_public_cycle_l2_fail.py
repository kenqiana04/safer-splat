import unittest

from reproduction.runtime.active_runtime_assurance_v2.runtime_types import CertificateStatus
from reproduction.runtime.active_runtime_assurance_v2.tests.public_cycle_test_support import build_public_cycle, start_and_run


class PublicCycleL2FailTests(unittest.TestCase):
    def test_l2_fail_never_reaches_l3(self):
        system = build_public_cycle({"l2": CertificateStatus.FAIL})
        _, result = start_and_run(system)
        self.assertEqual(system["counters"]["l3"], 0)
        self.assertFalse(result.committed)


if __name__ == "__main__":
    unittest.main()
