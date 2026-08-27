import unittest

from fixtures.synthetic_fixtures import sphere_case
from l2_h1_shadow_certifier import l2_h1_shadow_certify
from shadow_contract import load_frozen_robot_margin_contract
from shadow_types import ShadowCandidate, ShadowL2Status, ShadowState


class NonfiniteUnknownTests(unittest.TestCase):
    def test_nan_inf_dimension_and_dt_are_unknown(self):
        _, _, snapshot, context = sphere_case("safe")
        robot = load_frozen_robot_margin_contract()
        cases = [
            (ShadowState((float("nan"), 0.0, 0.0), (0.0, 0.0, 0.0), "nan"), ShadowCandidate((0.0, 0.0, 0.0), "u"), 0.1),
            (ShadowState((0.0, 0.0, 0.0), (0.0, 0.0, 0.0), "inf"), ShadowCandidate((float("inf"), 0.0, 0.0), "u"), 0.1),
            (ShadowState((0.0, 0.0), (0.0, 0.0), "dim"), ShadowCandidate((0.0, 0.0), "u"), 0.1),
            (ShadowState((0.0, 0.0, 0.0), (0.0, 0.0, 0.0), "dt"), ShadowCandidate((0.0, 0.0, 0.0), "u"), 0.0),
        ]
        for state, candidate, dt in cases:
            state = ShadowState(state.p_k, state.v_k, state.state_id, dt=dt)
            result = l2_h1_shadow_certify(state, candidate, snapshot, context, robot)
            self.assertEqual(result.status, ShadowL2Status.UNKNOWN)
            self.assertNotEqual(result.reason_code, "FORMAL_SEGMENT_UNSAFE")


if __name__ == "__main__":
    unittest.main()
