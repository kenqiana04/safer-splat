import unittest

from reproduction.runtime.active_runtime_assurance_v2.start_admission import StartAdmission
from reproduction.runtime.active_runtime_assurance_v2.runtime_types import CertificateStatus
from conformance_support import evidence, registry, snapshot


class StartAdmissionConformance(unittest.TestCase):
    def test_pass_fail_unknown_and_no_invented_repair(self):
        state = snapshot()
        self.assertEqual(StartAdmission(lambda *_: evidence(), registry(), False).evaluate(state).status, CertificateStatus.PASS)
        self.assertEqual(StartAdmission(lambda *_: evidence(CertificateStatus.FAIL, "UNSAFE"), registry(), False).evaluate(state).status, CertificateStatus.FAIL)
        self.assertEqual(StartAdmission(lambda *_: evidence(CertificateStatus.UNKNOWN, "MAP"), registry(), False).evaluate(state).status, CertificateStatus.UNKNOWN)
        with self.assertRaises(ValueError):
            StartAdmission(lambda *_: evidence(), registry(), True)


if __name__ == "__main__":
    unittest.main()
