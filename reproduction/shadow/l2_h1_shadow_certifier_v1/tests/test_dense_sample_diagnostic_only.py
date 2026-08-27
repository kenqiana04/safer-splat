import unittest

from fixtures.synthetic_fixtures import diagnostic_context, sphere_case
from l2_h1_shadow_certifier import l2_h1_shadow_certify
from shadow_contract import load_frozen_robot_margin_contract
from shadow_types import ShadowL2Status


class DenseDiagnosticTests(unittest.TestCase):
    def test_sample_count_cannot_change_formal_status(self):
        state, candidate, snapshot, context = sphere_case("safe")
        a = l2_h1_shadow_certify(state, candidate, snapshot, diagnostic_context(context, 17), load_frozen_robot_margin_contract())
        b = l2_h1_shadow_certify(state, candidate, snapshot, diagnostic_context(context, 257), load_frozen_robot_margin_contract())
        self.assertEqual((a.status, a.reason_code, a.formal_value_or_bound), (b.status, b.reason_code, b.formal_value_or_bound))
        self.assertTrue(a.diagnostic_only_fields["available"])
        self.assertTrue(a.diagnostic_available)
        self.assertIsNotNone(a.diagnostic_result)
        self.assertFalse(a.diagnostic_result["formal_authority"])

    def test_sampled_backend_has_no_formal_authority(self):
        state, candidate, snapshot, context = sphere_case("safe")
        diag_only = diagnostic_context(context, 33, diagnostic_as_formal=True)
        result = l2_h1_shadow_certify(state, candidate, snapshot, diag_only, load_frozen_robot_margin_contract())
        self.assertEqual(result.status, ShadowL2Status.UNKNOWN)


if __name__ == "__main__":
    unittest.main()
