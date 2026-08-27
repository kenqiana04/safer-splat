import unittest

from fixtures.synthetic_fixtures import sphere_case
from l2_h1_shadow_certifier import l2_h1_shadow_certify
from shadow_contract import load_frozen_robot_margin_contract
from shadow_types import ShadowL2Status


class ContinuousSegmentTests(unittest.TestCase):
    def test_endpoint_trap_is_formally_unsafe(self):
        result = l2_h1_shadow_certify(*sphere_case("endpoint_trap"), load_frozen_robot_margin_contract())
        self.assertEqual(result.status, ShadowL2Status.FAIL)
        self.assertTrue(all(abs(x) > 0.11 for x in (result.segment_start[0], result.segment_end[0])))
        self.assertFalse(result.endpoint_fallback_enabled)


if __name__ == "__main__":
    unittest.main()
