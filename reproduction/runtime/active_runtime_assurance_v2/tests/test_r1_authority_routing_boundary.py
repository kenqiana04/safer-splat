import ast
import unittest

from reproduction.runtime.active_runtime_assurance_v2.active_cycle import ActiveCycleCoordinator
from reproduction.runtime.active_runtime_assurance_v2.runtime_types import (
    ActiveCycleContext,
    CandidateRole,
    CertificateStatus,
    DeadlineObservation,
    DeadlineStatus,
    PublicCycleEvent,
    RouteResolutionStatus,
    RuntimePhase,
    RuntimeRoutingContext,
)
from reproduction.runtime.active_runtime_assurance_v2.tests.public_cycle_test_support import build_public_cycle


class R1AuthorityRoutingBoundaryTests(unittest.TestCase):
    def test_coordinator_has_no_policy_constructor_or_deadline_guard(self):
        source = (ActiveCycleCoordinator.__module__.replace(".", "/") + ".py")
        # Resolve through the imported class rather than depending on cwd.
        import inspect
        text = inspect.getsource(ActiveCycleCoordinator)
        self.assertNotIn("alternative_search_allowed", text)
        self.assertNotIn("navigation_timely", text)
        self.assertNotIn("navigation_ready", text)
        self.assertNotIn("terminal_ready", text)
        self.assertNotIn("deadline.status !=", text)
        tree = ast.parse(inspect.getsource(ActiveCycleCoordinator))
        self.assertFalse(any(isinstance(node, ast.Call) and isinstance(node.func, ast.Name) and node.func.id == "RoutingDecision" for node in ast.walk(tree)))

    def test_deadline_is_raw_context_fact_for_supervisor(self):
        system = build_public_cycle()
        for status in (DeadlineStatus.OPEN, DeadlineStatus.WARNING, DeadlineStatus.EXPIRED):
            observation = DeadlineObservation(status, "R1", 0.0, 1.0, "deadline:test")
            context = RuntimeRoutingContext(RuntimePhase.L1, observation, system["registry"].transition_table_identity)
            decision = system["supervisor"].route_transition(PublicCycleEvent.L1_PASS, context)
            self.assertEqual(context.deadline.status, status)
            self.assertEqual(decision.deadline_interpretation, "Supervisor-owned PR110 observation" if decision.status == RouteResolutionStatus.RESOLVED else "SUPERVISOR_BLOCKS_UNRESOLVED_LOOKUP")

    def test_certified_candidate_fact_is_not_suppressed_before_routing(self):
        system = build_public_cycle()
        candidate = system["coordinator"].primary_proposal.propose(system["state"], (0.0, 0.0, 0.0)).candidate
        context = system["coordinator"]._routing_context(
            RuntimePhase.ARBITRATION,
            DeadlineObservation(DeadlineStatus.EXPIRED, "R1", 1.0, -1.0, "deadline:test"),
            candidate=candidate,
            certified_candidate_available=True,
        )
        self.assertIsNotNone(candidate)
        self.assertTrue(context.candidate_available)
        self.assertTrue(context.certified_candidate_available)
        self.assertEqual(context.candidate_identity, candidate.identity)
        decision = system["supervisor"].route_transition(PublicCycleEvent.ARBITRATE, context)
        self.assertEqual(decision.status, RouteResolutionStatus.BLOCKED_MISSING)

    def test_backup_and_terminal_facts_do_not_select_actions_in_coordinator(self):
        import inspect
        text = inspect.getsource(ActiveCycleCoordinator)
        self.assertIn("self.supervisor.arbitrate", text)
        self.assertNotIn("return backup", text.lower())
        self.assertNotIn("return terminal", text.lower())
        self.assertNotIn("make_action", text)

    def test_repeated_route_block_is_supervisor_owned(self):
        system = build_public_cycle()
        base = ActiveCycleContext(
            trial_id=system["state"].trial_id,
            cycle_index=0,
            snapshot_id=system["state"].identity.value,
            state_id=system["state"].identity.value,
            authority_identity=system["registry"].transition_table_identity,
            deadline_identity="deadline:test",
            phase=__import__("reproduction.runtime.active_runtime_assurance_v2.runtime_types", fromlist=["PublicCyclePhase"]).PublicCyclePhase.CYCLE_BEGIN,
            phase_history=(),
        )
        context = RuntimeRoutingContext(RuntimePhase.L1, DeadlineObservation(DeadlineStatus.OPEN, "R1", 0.0, 1.0, "deadline:test"), system["registry"].transition_table_identity)
        seen = set()
        _, first = system["coordinator"]._route(base, PublicCycleEvent.L1_PASS, context, seen)
        _, second = system["coordinator"]._route(base, PublicCycleEvent.L1_PASS, context, seen)
        self.assertEqual(first.status, RouteResolutionStatus.RESOLVED)
        self.assertEqual(second.status, RouteResolutionStatus.BLOCKED_AMBIGUOUS)
        self.assertEqual(second.reason, "ROUTING_STATE_REPEATED")


if __name__ == "__main__":
    unittest.main()
