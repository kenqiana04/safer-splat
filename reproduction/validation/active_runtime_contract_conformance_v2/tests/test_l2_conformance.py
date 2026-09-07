import unittest

from reproduction.runtime.active_runtime_assurance_v2.l2_runtime import L2Runtime
from reproduction.runtime.active_runtime_assurance_v2.runtime_types import CertificateStatus
from conformance_support import evidence, registry, snapshot, candidate


class L2Conformance(unittest.TestCase):
    def test_h1_geometry_and_authority(self):
        state = snapshot()
        seen = []
        result = L2Runtime(lambda *args: (seen.append(args) or evidence()), registry()).evaluate(state, candidate(state, (0.02, 0.0, 0.0)))
        self.assertEqual(result.status, CertificateStatus.PASS)
        expected_k1 = tuple(p + state.dt * v for p, v in zip(state.position, state.velocity))
        expected_k2 = tuple(p + 2 * state.dt * v + state.dt * state.dt * u for p, v, u in zip(state.position, state.velocity, (0.02, 0, 0)))
        self.assertEqual(result.p_k1, expected_k1)
        self.assertEqual(result.p_k2, expected_k2)
        self.assertEqual(seen[0][3:], (0.025, 0.0))


if __name__ == "__main__":
    unittest.main()
