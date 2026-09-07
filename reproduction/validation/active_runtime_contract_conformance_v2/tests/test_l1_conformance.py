import unittest

from reproduction.runtime.active_runtime_assurance_v2.l1_runtime import L1Runtime
from reproduction.runtime.active_runtime_assurance_v2.runtime_types import CertificateStatus
from conformance_support import evidence, registry, snapshot, candidate


class L1Conformance(unittest.TestCase):
    def test_once_per_cycle_and_candidate_independent(self):
        calls = []
        def backend(*args):
            calls.append(args)
            return evidence()
        runtime = L1Runtime(backend, registry())
        state = snapshot()
        result = runtime.evaluate_cycle(state)
        runtime.evaluate_cycle(state)
        self.assertEqual(result.status, CertificateStatus.PASS)
        self.assertEqual(len(calls), 1)
        self.assertEqual(calls[0][0], state.position)
        self.assertEqual(calls[0][1], tuple(p + state.dt * v for p, v in zip(state.position, state.velocity)))
        self.assertEqual(runtime.bind_attempt(result, candidate(state, (0.09, 0, 0)), 0).cycle_result_identity, result.identity)


if __name__ == "__main__":
    unittest.main()
