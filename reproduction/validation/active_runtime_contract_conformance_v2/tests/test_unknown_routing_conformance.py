import unittest

from reproduction.runtime.active_runtime_assurance_v2.l1_runtime import L1Runtime
from reproduction.runtime.active_runtime_assurance_v2.l2_runtime import L2Runtime
from reproduction.runtime.active_runtime_assurance_v2.runtime_types import CertificateStatus
from conformance_support import registry, snapshot, candidate


class UnknownRoutingConformance(unittest.TestCase):
    def test_backend_exceptions_are_typed_unknown(self):
        state = snapshot()
        self.assertEqual(L1Runtime(lambda *_: (_ for _ in ()).throw(RuntimeError("x")), registry()).evaluate_cycle(state).status, CertificateStatus.UNKNOWN)
        self.assertEqual(L2Runtime(lambda *_: (_ for _ in ()).throw(RuntimeError("x")), registry()).evaluate(state, candidate(state)).status, CertificateStatus.UNKNOWN)


if __name__ == "__main__":
    unittest.main()
