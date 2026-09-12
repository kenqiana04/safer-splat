import unittest

from reproduction.runtime.v3_hard_radius_runtime_wiring_v1.geometry_policy import V3_GEOMETRY_POLICY


class V3GeometryPolicyTests(unittest.TestCase):
    def test_frozen_values_and_invariants(self):
        policy = V3_GEOMETRY_POLICY
        policy.validate()
        self.assertEqual(policy.hard_runtime_radius_q, 0.015)
        self.assertEqual(policy.runtime_margin_q, 0.0)
        self.assertEqual(policy.runtime_effective_radius_q, 0.015)
        self.assertEqual(policy.rho_seg_q, 0.0)
        self.assertEqual(policy.historical_diagnostic_radius_q, 0.025)
        self.assertFalse(policy.historical_diagnostic_runtime_authority)
        self.assertFalse(policy.historical_design_reserve_runtime_authority)
        self.assertTrue(policy.historical_design_reserve_diagnostic_only)
        self.assertTrue(policy.historical_design_reserve_v2_only)

    def test_geometry_authority_is_explicit_v3_identity(self):
        authority = V3_GEOMETRY_POLICY.to_geometry_authority()
        self.assertEqual(authority.identity.kind, "V3_HARD_RADIUS_GEOMETRY_AUTHORITY_V1")
        self.assertEqual(authority.controller_radius_m, 0.015)
        self.assertEqual(authority.certification_margin_m, 0.0)
        self.assertEqual(authority.certification_effective_radius_m, 0.015)
        self.assertEqual(authority.rho_seg_m, 0.0)


if __name__ == "__main__":
    unittest.main()
