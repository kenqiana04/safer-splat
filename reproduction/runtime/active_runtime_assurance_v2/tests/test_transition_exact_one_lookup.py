import dataclasses
import unittest

from reproduction.runtime.active_runtime_assurance_v2.runtime_types import CandidateRole, DeadlineObservation, DeadlineStatus, PublicCycleEvent, RouteResolutionStatus, RuntimePhase, RuntimeRoutingContext
from reproduction.runtime.active_runtime_assurance_v2.supervisor import TransitionRule, TransitionTable
from reproduction.runtime.active_runtime_assurance_v2.tests.public_cycle_test_support import build_public_cycle


class TransitionExactOneLookupTests(unittest.TestCase):
    def context(self):
        system = build_public_cycle()
        return RuntimeRoutingContext(RuntimePhase.C0, DeadlineObservation(DeadlineStatus.OPEN, "C0", 0.0, 1.0, "deadline:test"), system["registry"].transition_table_identity, CandidateRole.PRIMARY, None, True)

    def test_zero_match_is_typed_block(self):
        table = build_public_cycle()["supervisor"].transition_table
        result = table.resolve(PublicCycleEvent.COMMIT_FAILURE, self.context())
        self.assertEqual(result.status, RouteResolutionStatus.BLOCKED_MISSING)

    def test_multiple_match_is_typed_block_not_first_match(self):
        source = build_public_cycle()["supervisor"].transition_table
        rules = list(source.rules)
        rules[-1] = dataclasses.replace(rules[13], rule_id=rules[-1].rule_id)
        result = TransitionTable(tuple(rules)).resolve(PublicCycleEvent.C0_PASS, self.context())
        self.assertEqual(result.status, RouteResolutionStatus.BLOCKED_AMBIGUOUS)


if __name__ == "__main__":
    unittest.main()
