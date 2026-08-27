import unittest
from dataclasses import replace

from fixtures.synthetic_fixtures import sphere_case
from l2_h1_shadow_certifier import l2_h1_shadow_certify
from shadow_contract import load_frozen_robot_margin_contract
from shadow_types import ShadowL2Status


class RobotMarginContractTests(unittest.TestCase):
    def test_frozen_values(self):
        contract = load_frozen_robot_margin_contract()
        self.assertEqual((contract.robot_radius_m, contract.margin_m, contract.effective_radius_m, contract.rho_seg), (0.10, 0.01, 0.11, 0.0))

    def test_contract_drift_is_unknown(self):
        state, candidate, snapshot, context = sphere_case("safe")
        drifted = replace(load_frozen_robot_margin_contract(), margin_m=0.02)
        result = l2_h1_shadow_certify(state, candidate, snapshot, context, drifted)
        self.assertEqual(result.status, ShadowL2Status.UNKNOWN)
        self.assertEqual(result.reason_code, "ROBOT_MARGIN_CONTRACT_MISMATCH")


if __name__ == "__main__":
    unittest.main()
