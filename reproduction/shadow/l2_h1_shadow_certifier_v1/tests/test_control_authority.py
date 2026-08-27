import inspect
import unittest

import numpy as np

from _support import assert_tuple_allclose
from l2_h1_shadow_certifier import propagate_h1_endpoints
from shadow_types import ShadowCandidate, ShadowState


class ControlAuthorityTests(unittest.TestCase):
    def test_off_by_one_and_candidate_derivative(self):
        state = ShadowState((0.1, 0.2, 0.3), (0.4, -0.2, 0.1), "s")
        a = ShadowCandidate((0.1, 0.0, -0.1), "a")
        b = ShadowCandidate((-0.2, 0.3, 0.4), "b")
        dt = 0.2
        pa = propagate_h1_endpoints(state, a, dt)
        pb = propagate_h1_endpoints(state, b, dt)
        self.assertEqual(pa.p_k1, pb.p_k1)
        self.assertNotEqual(pa.p_k2, pb.p_k2)
        assert_tuple_allclose(self, np.asarray(pa.p_k2) - np.asarray(pb.p_k2), dt**2 * (np.asarray(a.u_k) - np.asarray(b.u_k)))

    def test_no_u_k_plus_1_argument(self):
        parameters = tuple(inspect.signature(propagate_h1_endpoints).parameters)
        self.assertEqual(parameters, ("x_k", "u_k", "dt"))
        self.assertNotIn("u_k1", parameters)


if __name__ == "__main__":
    unittest.main()
