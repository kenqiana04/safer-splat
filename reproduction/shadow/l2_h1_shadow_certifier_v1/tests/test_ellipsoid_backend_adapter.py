import unittest

from fixtures.synthetic_fixtures import conservative_case
from l2_h1_shadow_certifier import l2_h1_shadow_certify
from shadow_contract import load_frozen_robot_margin_contract
from shadow_types import ShadowL2Status


class EllipsoidBackendAdapterTests(unittest.TestCase):
    def test_conservative_safe_unsafe_and_budget_unknown(self):
        robot = load_frozen_robot_margin_contract()
        safe = l2_h1_shadow_certify(*conservative_case("safe"), robot)
        unsafe = l2_h1_shadow_certify(*conservative_case("intersection"), robot)
        budget = l2_h1_shadow_certify(*conservative_case("budget"), robot)
        self.assertEqual(safe.status, ShadowL2Status.PASS)
        self.assertEqual(unsafe.status, ShadowL2Status.FAIL)
        self.assertEqual(budget.status, ShadowL2Status.UNKNOWN)
        self.assertEqual(budget.reason_code, "CERTIFICATE_BUDGET_EXHAUSTED")
        self.assertEqual(safe.backend_class, "CONSERVATIVE_LOWER_BOUND")


if __name__ == "__main__":
    unittest.main()
