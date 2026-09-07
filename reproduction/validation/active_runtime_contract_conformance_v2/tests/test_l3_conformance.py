import unittest

from reproduction.runtime.active_runtime_assurance_v2.l3_runtime import L3Runtime
from reproduction.runtime.active_runtime_assurance_v2.runtime_types import CertificateStatus, L2Result
from conformance_support import evidence, registry, snapshot, candidate


class L3Conformance(unittest.TestCase):
    def test_l3_prepares_only_after_matching_l2_pass(self):
        state = snapshot()
        cand = candidate(state)
        l2 = L2Result.create(CertificateStatus.PASS, "PASS", cand.identity, state.position, state.position, "segment", "e")
        result = L3Runtime(lambda *_: (CertificateStatus.PASS, [((0.0, 0.0, 0.0), "tail")], "terminal", "WITNESS"), registry()).evaluate(state, cand, l2)
        self.assertEqual(result.status, CertificateStatus.PASS)
        self.assertIsNotNone(result.prepared_bundle)
        fail_l2 = L2Result.create(CertificateStatus.FAIL, "FAIL", cand.identity, state.position, state.position, "segment", "e")
        blocked = L3Runtime(lambda *_: (_ for _ in ()).throw(AssertionError("builder must not run")), registry()).evaluate(state, cand, fail_l2)
        self.assertEqual(blocked.status, CertificateStatus.UNKNOWN)


if __name__ == "__main__":
    unittest.main()
