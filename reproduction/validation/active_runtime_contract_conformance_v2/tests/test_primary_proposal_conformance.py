import unittest

from reproduction.runtime.active_runtime_assurance_v2.primary_proposal_adapter import PrimaryProposalAdapter
from reproduction.runtime.active_runtime_assurance_v2.runtime_types import CertificateStatus
from conformance_support import snapshot


class PrimaryProposalConformance(unittest.TestCase):
    def test_solver_failure_has_no_desired_fallback_and_success_is_primary(self):
        state = snapshot()
        fail = PrimaryProposalAdapter(lambda *_: (False, None, "QP_FAIL"), "controller:cpu").propose(state, (0.2, 0, 0))
        self.assertEqual(fail.status, CertificateStatus.FAIL)
        self.assertIsNone(fail.candidate)
        ok = PrimaryProposalAdapter(lambda *_: (True, (0.01, 0, 0), "QP_OK"), "controller:cpu").propose(state, (0.2, 0, 0))
        self.assertEqual(ok.status, CertificateStatus.PASS)
        self.assertEqual(ok.candidate.role.value, "PRIMARY")


if __name__ == "__main__":
    unittest.main()
