import unittest

from reproduction.runtime.active_runtime_assurance_v2.runtime_types import TokenLifecycle
from reproduction.runtime.active_runtime_assurance_v2.tests.public_cycle_test_support import build_public_cycle, start_and_run


class PublicCycleTokenHandoffTests(unittest.TestCase):
    def test_navigation_uses_runner_owned_atomic_token_activation(self):
        system = build_public_cycle()
        _, result = start_and_run(system)
        token = system["token_store"].current()
        self.assertIsNotNone(token)
        self.assertEqual(token.lifecycle, TokenLifecycle.ACTIVE)
        self.assertEqual(token.expected_state_identity, result.next_state.identity)
        self.assertFalse(hasattr(system["coordinator"], "prepare"))


if __name__ == "__main__":
    unittest.main()
