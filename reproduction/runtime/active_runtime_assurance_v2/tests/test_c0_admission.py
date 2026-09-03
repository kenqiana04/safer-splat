import unittest

from reproduction.runtime.active_runtime_assurance_v2.authority_registry import AuthorityRegistry
from reproduction.runtime.active_runtime_assurance_v2.c0_admission import C0Admission
from reproduction.runtime.active_runtime_assurance_v2.runtime_types import CandidateRole, CertificateStatus, make_candidate
from reproduction.runtime.active_runtime_assurance_v2.tests.helpers import snapshot


class C0AdmissionTests(unittest.TestCase):
    def setUp(self):
        self.state = snapshot()
        self.c0 = C0Admission(AuthorityRegistry.frozen(self.state.map_identity, "dt:0.05"))

    def candidate(self, x):
        return make_candidate((x, -0.1, 0.1), CandidateRole.PRIMARY, "PRIMARY_NATIVE_CBF_QP", "cbf", self.state)

    def test_inclusive_bounds_pass(self):
        self.assertEqual(self.c0.evaluate(self.candidate(0.1), self.state).status, CertificateStatus.PASS)
        self.assertEqual(self.c0.evaluate(self.candidate(-0.1), self.state).status, CertificateStatus.PASS)

    def test_outside_rejected_without_clip(self):
        result = self.c0.evaluate(self.candidate(0.10000001), self.state)
        self.assertEqual(result.status, CertificateStatus.FAIL)
        self.assertEqual(result.candidate_vector[0], 0.10000001)


if __name__ == "__main__": unittest.main()
