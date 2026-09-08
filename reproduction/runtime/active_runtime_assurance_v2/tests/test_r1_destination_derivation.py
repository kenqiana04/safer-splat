import dataclasses
import inspect
import unittest

from reproduction.runtime.active_runtime_assurance_v2.runtime_types import CandidateIdentity, CandidateRole, DeadlineObservation, DeadlineStatus, PublicCycleEvent, RuntimePhase, RuntimeRoutingContext
from reproduction.runtime.active_runtime_assurance_v2.supervisor import TransitionTable
from reproduction.runtime.active_runtime_assurance_v2.tests.public_cycle_test_support import build_public_cycle


class R1DestinationDerivationTests(unittest.TestCase):
    def test_route_metadata_is_copied_not_recomputed_from_destination(self):
        system = build_public_cycle()
        table = system["supervisor"].transition_table
        rules = list(table.rules)
        index = next(i for i, item in enumerate(rules) if item.rule_id == "ARB_NAV")
        rules[index] = dataclasses.replace(
            rules[index],
            may_start_next_stage=False,
            may_start_new_search=True,
            requires_arbitration=False,
            deadline_interpretation="FIXTURE_EXPLICIT_METADATA",
            backup_routing_allowed=True,
            terminal_routing_allowed=True,
        )
        fixture = TransitionTable(tuple(rules))
        context = RuntimeRoutingContext(
            RuntimePhase.ARBITRATION,
            DeadlineObservation(DeadlineStatus.OPEN, "ARB", 0.0, 1.0, "deadline:test"),
            system["registry"].transition_table_identity,
            CandidateRole.PRIMARY,
            CandidateIdentity("candidate:r1"),
            True,
            False,
            False,
            False,
            True,
            False,
            False,
            "NONE",
            True,
            False,
        )
        decision = fixture.resolve(PublicCycleEvent.ARBITRATE, context)
        self.assertEqual(decision.destination_phase, RuntimePhase.COMMIT)
        self.assertFalse(decision.may_start_next_stage)
        self.assertTrue(decision.may_start_new_search)
        self.assertFalse(decision.requires_arbitration)
        self.assertEqual(decision.deadline_interpretation, "FIXTURE_EXPLICIT_METADATA")
        self.assertTrue(decision.backup_routing_allowed)
        self.assertTrue(decision.terminal_routing_allowed)

    def test_supervisor_resolution_source_has_no_destination_flag_inference(self):
        source = inspect.getsource(TransitionTable.resolve)
        self.assertNotIn("destination not in", source)
        self.assertNotIn("destination == RuntimePhase.ALT_SEARCH", source)
        self.assertIn("rule.may_start_next_stage", source)
        self.assertIn("rule.deadline_interpretation", source)


if __name__ == "__main__":
    unittest.main()
