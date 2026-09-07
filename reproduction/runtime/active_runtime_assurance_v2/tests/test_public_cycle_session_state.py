import unittest

from reproduction.runtime.active_runtime_assurance_v2.active_cycle import PublicCycleStateError
from reproduction.runtime.active_runtime_assurance_v2.runtime_types import ActiveCycleRequest, RuntimeStateSnapshot
from reproduction.runtime.active_runtime_assurance_v2.tests.public_cycle_test_support import build_public_cycle


class PublicCycleSessionStateTests(unittest.TestCase):
    def test_cycle_before_start_and_double_start_are_blocked(self):
        system = build_public_cycle()
        with self.assertRaises(PublicCycleStateError):
            system["coordinator"].run_cycle(system["state"], system["request"])
        system["coordinator"].start_trial(system["state"], system["trial"])
        with self.assertRaises(PublicCycleStateError):
            system["coordinator"].start_trial(system["state"], system["trial"])

    def test_cycle_identity_mismatch_is_typed_block(self):
        system = build_public_cycle()
        system["coordinator"].start_trial(system["state"], system["trial"])
        with self.assertRaises(PublicCycleStateError):
            system["coordinator"].run_cycle(system["state"], ActiveCycleRequest(system["state"].trial_id, 1, (0.0, 0.0, 0.0), None))

    def test_run_after_finalize_is_blocked(self):
        system = build_public_cycle()
        system["coordinator"].start_trial(system["state"], system["trial"])
        system["coordinator"].finalize_trial()
        with self.assertRaises(PublicCycleStateError):
            system["coordinator"].run_cycle(system["state"], system["request"])


if __name__ == "__main__":
    unittest.main()
