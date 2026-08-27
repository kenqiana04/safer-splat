import unittest

from fixtures.synthetic_fixtures import conservative_case, direct_frozen_certificate, sphere_case
from l2_h1_shadow_certifier import l2_h1_shadow_certify
from shadow_contract import load_frozen_robot_margin_contract


class DifferentialConsistencyTests(unittest.TestCase):
    def test_exact_and_conservative_match_direct_calls(self):
        robot = load_frozen_robot_margin_contract()
        for fixture in (sphere_case("safe"), sphere_case("intersection"), conservative_case("safe"), conservative_case("intersection")):
            result = l2_h1_shadow_certify(*fixture, robot)
            direct = direct_frozen_certificate(fixture, robot)
            self.assertEqual(result.formal_backend_status, direct.status.value)
            self.assertAlmostEqual(result.formal_value_or_bound, direct.lower_bound, places=12)
            self.assertEqual(result.backend_identity, direct.method)


if __name__ == "__main__":
    unittest.main()
