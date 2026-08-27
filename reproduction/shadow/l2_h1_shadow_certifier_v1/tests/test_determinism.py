import unittest

from fixtures.synthetic_fixtures import sphere_case
from l2_h1_shadow_certifier import l2_h1_shadow_certify
from shadow_contract import load_frozen_robot_margin_contract


class DeterminismTests(unittest.TestCase):
    def test_semantic_serialization_is_identical(self):
        fixture = sphere_case("safe")
        robot = load_frozen_robot_margin_contract()
        values = [l2_h1_shadow_certify(*fixture, robot).to_json() for _ in range(5)]
        self.assertEqual(len(set(values)), 1)


if __name__ == "__main__":
    unittest.main()
