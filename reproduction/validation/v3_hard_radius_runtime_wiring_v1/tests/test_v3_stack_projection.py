import copy
import unittest

from reproduction.runtime.active_runtime_assurance_v2.authority_registry import AuthorityRegistry
from reproduction.runtime.v3_hard_radius_runtime_wiring_v1.geometry_policy import V3_GEOMETRY_POLICY
from reproduction.runtime.v3_hard_radius_runtime_wiring_v1.stack_config import project_v3_runtime_config
from reproduction.runtime.v3_hard_radius_runtime_wiring_v1.stack_factory import make_v3_authority_registry


BASE_CONFIG = {
    "controller": {"controller_radius": 0.015, "alpha": 5.0},
    "certification": {
        "certification_effective_radius": 0.025,
        "rho_seg": 0.0,
        "terminal_velocity_tolerance": 1e-12,
    },
    "diagnostics": {"preserved": True},
}


class V3StackProjectionTests(unittest.TestCase):
    def test_projection_is_defensive_and_exact(self):
        source = copy.deepcopy(BASE_CONFIG)
        projected = project_v3_runtime_config(source)
        self.assertEqual(source, BASE_CONFIG)
        self.assertIsNot(projected, source)
        self.assertEqual(projected["controller"]["controller_radius"], 0.015)
        self.assertEqual(projected["certification"]["certification_margin"], 0.0)
        self.assertEqual(projected["certification"]["certification_effective_radius"], 0.015)
        self.assertEqual(projected["certification"]["rho_seg"], 0.0)
        self.assertEqual(projected["diagnostics"]["historical_v2_geometry"]["historical_v2_reserve_shell_q"], 0.025)
        self.assertFalse(projected["diagnostics"]["historical_v2_geometry"]["runtime_authority"])
        self.assertTrue(projected["diagnostics"]["preserved"])

    def test_v2_default_and_explicit_v3_registry_both_validate(self):
        v2 = AuthorityRegistry.frozen("map:test", "dt:test")
        v3 = make_v3_authority_registry("map:test", "dt:test")
        v2.verify_all(active=False)
        v3.verify_all(active=False)
        self.assertEqual(v2.geometry.certification_margin_m, 0.010)
        self.assertEqual(v2.geometry.certification_effective_radius_m, 0.025)
        self.assertEqual(v3.geometry.certification_margin_m, 0.0)
        self.assertEqual(v3.geometry.certification_effective_radius_m, 0.015)

    def test_historical_shell_is_not_runtime_consumed(self):
        projected = project_v3_runtime_config(BASE_CONFIG)
        runtime_values = {
            projected["controller"]["controller_radius"],
            projected["certification"]["certification_margin"],
            projected["certification"]["certification_effective_radius"],
            projected["certification"]["rho_seg"],
        }
        self.assertNotIn(0.025, runtime_values)
        self.assertEqual(projected["diagnostics"]["historical_v2_geometry"]["historical_v2_reserve_shell_q"], 0.025)


if __name__ == "__main__":
    unittest.main()
