import unittest

from reproduction.runtime.active_runtime_assurance_v2.authority_registry import AuthorityRegistry
from reproduction.runtime.active_runtime_assurance_v2.runtime_errors import AuthorityMismatch


class AuthorityRegistryTests(unittest.TestCase):
    def test_frozen_values(self):
        registry = AuthorityRegistry.frozen("map:g3:abc", "dt:0.05")
        registry.verify_all(active=False)
        self.assertEqual(registry.geometry.controller_radius_m, 0.015)
        self.assertEqual(registry.geometry.certification_effective_radius_m, 0.025)
        self.assertEqual(registry.actuator.u_min, (-0.1, -0.1, -0.1))
        self.assertFalse(registry.terminal.goal_hold_enabled)
        self.assertFalse(registry.oracle.feedback_authority)

    def test_missing_map_fails_closed(self):
        registry = AuthorityRegistry.frozen("", "dt:0.05")
        with self.assertRaises(AuthorityMismatch):
            registry.verify_all(active=False)


if __name__ == "__main__": unittest.main()
