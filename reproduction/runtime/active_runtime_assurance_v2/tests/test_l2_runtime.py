import unittest

from reproduction.runtime.active_runtime_assurance_v2.authority_registry import AuthorityRegistry
from reproduction.runtime.active_runtime_assurance_v2.l2_runtime import L2Runtime
from reproduction.runtime.active_runtime_assurance_v2.runtime_types import CandidateRole, make_candidate
from reproduction.runtime.active_runtime_assurance_v2.tests.helpers import pass_backend, snapshot


class L2RuntimeTests(unittest.TestCase):
    def test_h1_equations_and_v2_authority(self):
        calls = []
        def backend(*args):
            calls.append(args)
            return pass_backend()
        state = snapshot()
        candidate = make_candidate((0.2, 0.0, 0.0), CandidateRole.PRIMARY, "PRIMARY_NATIVE_CBF_QP", "cbf", state)
        result = L2Runtime(backend, AuthorityRegistry.frozen(state.map_identity, "dt:0.05")).evaluate(state, candidate)
        self.assertEqual(result.p_k1, (0.005000000000000001, -0.005000000000000001, 0.0))
        self.assertAlmostEqual(result.p_k2[0], 0.0105, places=15)
        self.assertEqual(calls[0][3:], (0.025, 0.0))


if __name__ == "__main__": unittest.main()
