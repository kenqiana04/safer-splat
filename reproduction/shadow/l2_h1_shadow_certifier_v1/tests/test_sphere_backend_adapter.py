import unittest

from fixtures.synthetic_fixtures import sphere_case
from l2_h1_shadow_certifier import l2_h1_shadow_certify
from shadow_contract import load_frozen_robot_margin_contract
from shadow_types import ShadowL2Status


class SphereBackendAdapterTests(unittest.TestCase):
    def test_exact_safe_intersection_and_tangency(self):
        robot = load_frozen_robot_margin_contract()
        safe = l2_h1_shadow_certify(*sphere_case("safe"), robot)
        hit = l2_h1_shadow_certify(*sphere_case("intersection"), robot)
        tangent = l2_h1_shadow_certify(*sphere_case("tangent"), robot)
        self.assertEqual((safe.status, hit.status, tangent.status), (ShadowL2Status.PASS, ShadowL2Status.FAIL, ShadowL2Status.PASS))
        self.assertEqual(safe.backend_class, "EXACT_ANALYTIC")
        self.assertAlmostEqual(tangent.formal_value_or_bound, 0.0, delta=1e-15)


if __name__ == "__main__":
    unittest.main()
