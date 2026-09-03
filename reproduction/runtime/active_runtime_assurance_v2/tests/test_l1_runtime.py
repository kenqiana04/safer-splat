import unittest

from reproduction.runtime.active_runtime_assurance_v2.authority_registry import AuthorityRegistry
from reproduction.runtime.active_runtime_assurance_v2.l1_runtime import L1Runtime
from reproduction.runtime.active_runtime_assurance_v2.runtime_types import CandidateRole, make_candidate
from reproduction.runtime.active_runtime_assurance_v2.tests.helpers import pass_backend, snapshot


class L1RuntimeTests(unittest.TestCase):
    def test_once_per_cycle_fresh_bindings(self):
        calls = []
        def backend(*args):
            calls.append(args)
            return pass_backend()
        state = snapshot()
        runtime = L1Runtime(backend, AuthorityRegistry.frozen(state.map_identity, "dt:0.05"))
        result = runtime.evaluate_cycle(state)
        a = make_candidate((0.0, 0.0, 0.0), CandidateRole.PRIMARY, "PRIMARY_NATIVE_CBF_QP", "cbf", state)
        b = make_candidate((0.01, 0.0, 0.0), CandidateRole.ALTERNATIVE, "SOURCE_NATIVE_EXISTING", "cbf", state)
        bind_a = runtime.bind_attempt(result, a, 0)
        bind_b = runtime.bind_attempt(result, b, 1)
        self.assertEqual(len(calls), 1)
        self.assertEqual(bind_a.cycle_result_identity, bind_b.cycle_result_identity)
        self.assertNotEqual(bind_a.identity, bind_b.identity)


if __name__ == "__main__": unittest.main()
