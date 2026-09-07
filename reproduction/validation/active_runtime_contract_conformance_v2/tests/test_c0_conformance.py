import unittest

from reproduction.runtime.active_runtime_assurance_v2.c0_admission import C0Admission
from reproduction.runtime.active_runtime_assurance_v2.runtime_types import CertificateStatus, CandidateRole, make_candidate
from conformance_support import candidate, registry, snapshot


class C0Conformance(unittest.TestCase):
    def test_inclusive_bounds_unknown_provenance_and_no_clip(self):
        state = snapshot()
        c0 = C0Admission(registry())
        self.assertEqual(c0.evaluate(candidate(state, (0.1, -0.1, 0)), state).status, CertificateStatus.PASS)
        self.assertEqual(c0.evaluate(candidate(state, (0.10000001, 0, 0)), state).status, CertificateStatus.FAIL)
        mismatched = make_candidate((0, 0, 0), CandidateRole.PRIMARY, "PRIMARY_NATIVE_CBF_QP", "controller:cpu", snapshot(1))
        self.assertEqual(c0.evaluate(mismatched, state).status, CertificateStatus.UNKNOWN)


if __name__ == "__main__":
    unittest.main()
