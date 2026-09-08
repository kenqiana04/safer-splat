import dataclasses
import unittest

from reproduction.runtime.active_runtime_assurance_v2.runtime_types import ActiveCycleContext, CandidateRole, DeadlineObservation, DeadlineStatus, PublicCycleEvent, PublicCyclePhase, RouteResolutionStatus, RuntimePhase, RuntimeRoutingContext
from reproduction.runtime.active_runtime_assurance_v2.supervisor import TransitionTable
from reproduction.runtime.active_runtime_assurance_v2.tests.public_cycle_test_support import build_public_cycle


class R1ExactOneAndRepeatedGuardTests(unittest.TestCase):
    def test_frozen_table_exactly_43_and_missing_ambiguous_are_typed(self):
        system = build_public_cycle()
        table = system["supervisor"].transition_table
        self.assertEqual(len(table.rules), 43)
        self.assertEqual(len(table.by_id), 43)
        context = RuntimeRoutingContext(RuntimePhase.C0, DeadlineObservation(DeadlineStatus.OPEN, "C0", 0.0, 1.0, "deadline:test"), system["registry"].transition_table_identity, CandidateRole.PRIMARY, None, True)
        missing = table.resolve(PublicCycleEvent.COMMIT_FAILURE, context)
        self.assertEqual(missing.status, RouteResolutionStatus.BLOCKED_MISSING)
        rules = list(table.rules)
        rules[-1] = dataclasses.replace(rules[13], rule_id=rules[-1].rule_id)
        ambiguous = TransitionTable(tuple(rules)).resolve(PublicCycleEvent.C0_PASS, context)
        self.assertEqual(ambiguous.status, RouteResolutionStatus.BLOCKED_AMBIGUOUS)

    def test_repeated_state_uses_supervisor_meta_guard(self):
        system = build_public_cycle()
        base = ActiveCycleContext("trial-1", 0, system["state"].identity.value, system["state"].identity.value, system["registry"].transition_table_identity, "deadline:test", PublicCyclePhase.CYCLE_BEGIN, ())
        routing_context = RuntimeRoutingContext(RuntimePhase.L1, DeadlineObservation(DeadlineStatus.OPEN, "L1", 0.0, 1.0, "deadline:test"), system["registry"].transition_table_identity)
        seen = set()
        system["coordinator"]._route(base, PublicCycleEvent.L1_PASS, routing_context, seen)
        _, repeated = system["coordinator"]._route(base, PublicCycleEvent.L1_PASS, routing_context, seen)
        self.assertEqual(repeated.status, RouteResolutionStatus.BLOCKED_AMBIGUOUS)
        self.assertEqual(repeated.reason, "ROUTING_STATE_REPEATED")


if __name__ == "__main__":
    unittest.main()
