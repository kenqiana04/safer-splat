import unittest

import numpy as np

from _support import assert_tuple_allclose
from l2_h1_shadow_certifier import h1_point, propagate_h1_endpoints
from shadow_types import ShadowCandidate, ShadowState


class H1PropagationTests(unittest.TestCase):
    def setUp(self):
        self.state = ShadowState((1.0, -2.0, 0.5), (0.2, -0.1, 0.3), "s")
        self.candidate = ShadowCandidate((0.4, -0.2, 0.1), "u")
        self.dt = 0.25

    def test_position_first_euler_formulas(self):
        out = propagate_h1_endpoints(self.state, self.candidate, self.dt)
        p = np.asarray(self.state.p_k); v = np.asarray(self.state.v_k); u = np.asarray(self.candidate.u_k)
        assert_tuple_allclose(self, out.p_k1, p + self.dt * v)
        assert_tuple_allclose(self, out.v_k1, v + self.dt * u)
        assert_tuple_allclose(self, out.p_k2, p + 2.0 * self.dt * v + self.dt**2 * u)

    def test_zero_acceleration_oracle(self):
        u0 = ShadowCandidate((0.0, 0.0, 0.0), "zero")
        out = propagate_h1_endpoints(self.state, u0, self.dt)
        assert_tuple_allclose(self, out.p_k2, np.asarray(self.state.p_k) + 2.0 * self.dt * np.asarray(self.state.v_k))

    def test_h1_alpha_endpoints(self):
        out = propagate_h1_endpoints(self.state, self.candidate, self.dt)
        assert_tuple_allclose(self, h1_point(self.state, self.candidate, self.dt, 0.0), out.p_k1)
        assert_tuple_allclose(self, h1_point(self.state, self.candidate, self.dt, 1.0), out.p_k2)


if __name__ == "__main__":
    unittest.main()
