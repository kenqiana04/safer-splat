import unittest

from reproduction.runtime.active_runtime_assurance_v2.authority_registry import AuthorityRegistry
from reproduction.runtime.active_runtime_assurance_v2.l3_runtime import L3Runtime
from reproduction.runtime.active_runtime_assurance_v2.runtime_types import CandidateRole, CertificateStatus, L2Result, make_candidate
from reproduction.runtime.active_runtime_assurance_v2.tests.helpers import snapshot


class L3RuntimeTests(unittest.TestCase):
    def test_l2_pass_prepares_but_does_not_activate_bundle(self):
        state = snapshot()
        candidate = make_candidate((0.01, 0.0, 0.0), CandidateRole.PRIMARY, "PRIMARY_NATIVE_CBF_QP", "cbf", state)
        l2 = L2Result.create(CertificateStatus.PASS, "L2_PASS", candidate.identity, (0,0,0), (0,0,0), "seg", "e2")
        builder = lambda s, c: (CertificateStatus.PASS, (((0.0,0.0,0.0), "backup:0"),), "terminal:ref", "WITNESS")
        result = L3Runtime(builder, AuthorityRegistry.frozen(state.map_identity, "dt:0.05")).evaluate(state, candidate, l2)
        self.assertEqual(result.status, CertificateStatus.PASS)
        self.assertIsNotNone(result.prepared_bundle)
        self.assertEqual(result.prepared_bundle.lifecycle, "PREPARED_UNCOMMITTED")

    def test_l2_fail_does_not_call_builder(self):
        state = snapshot(); calls=[]
        candidate = make_candidate((0,0,0), CandidateRole.PRIMARY, "PRIMARY_NATIVE_CBF_QP", "cbf", state)
        l2 = L2Result.create(CertificateStatus.FAIL, "L2_FAIL", candidate.identity, (0,0,0), (0,0,0), "seg", "e2")
        result = L3Runtime(lambda *a: calls.append(a), AuthorityRegistry.frozen(state.map_identity, "dt:0.05")).evaluate(state, candidate, l2)
        self.assertEqual(result.status, CertificateStatus.UNKNOWN)
        self.assertFalse(calls)


if __name__ == "__main__": unittest.main()
