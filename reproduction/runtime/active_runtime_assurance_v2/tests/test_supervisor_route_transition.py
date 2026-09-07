import unittest

from reproduction.runtime.active_runtime_assurance_v2.runtime_types import CandidateRole, DeadlineObservation, DeadlineStatus, PublicCycleEvent, RouteResolutionStatus, RuntimePhase, RuntimeRoutingContext
from reproduction.runtime.active_runtime_assurance_v2.tests.public_cycle_test_support import build_public_cycle


class SupervisorRouteTransitionTests(unittest.TestCase):
    def test_resolves_primary_path_from_frozen_table(self):
        system = build_public_cycle()
        context = RuntimeRoutingContext(RuntimePhase.L1, DeadlineObservation(DeadlineStatus.OPEN, "L1", 0.0, 1.0, "deadline:test"), system["registry"].transition_table_identity)
        decision = system["supervisor"].route_transition(PublicCycleEvent.L1_PASS, context)
        self.assertEqual(decision.status, RouteResolutionStatus.RESOLVED)
        self.assertEqual((decision.rule_id, decision.destination_phase), ("L1_PASS", RuntimePhase.PRIMARY_PROPOSAL))

    def test_final_selection_is_not_part_of_route_decision(self):
        fields = set(system_field for system_field in RuntimeRoutingContext.__dataclass_fields__)
        self.assertNotIn("selected_action", fields)
        self.assertIn(CandidateRole.PRIMARY, tuple(CandidateRole))


if __name__ == "__main__":
    unittest.main()
