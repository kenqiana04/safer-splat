import unittest

from reproduction.runtime.active_runtime_assurance_v2.runtime_types import (
    ActionRole,
    ActiveCycleRequest,
    AlternativeInventoryResult,
    AlternativeInventoryStatus,
    CandidateRole,
    make_candidate,
)
from reproduction.runtime.active_runtime_assurance_v2.tests.public_cycle_test_support import build_public_cycle, start_and_run


class R2AlternativeStatusFidelityTests(unittest.TestCase):
    def _second_cycle(self, status, candidates=()):
        system = build_public_cycle()
        _, first = start_and_run(system)
        system["config"]["primary_vector"] = (0.2, 0.0, 0.0)
        system["coordinator"].alternative_provider.enumerate = lambda _snapshot: AlternativeInventoryResult(status, candidates)
        request = ActiveCycleRequest(first.next_state.trial_id, 1, (1.0, 0.0, 0.0), None)
        result = system["coordinator"].run_cycle(first.next_state, request)
        return system, result

    def test_available_candidate_remains_available(self):
        system = build_public_cycle()
        _, first = start_and_run(system)
        candidate = make_candidate((0.01, 0.0, 0.0), CandidateRole.ALTERNATIVE, "SOURCE_NATIVE_EXISTING", "native-controller", first.next_state)
        system["config"]["primary_vector"] = (0.2, 0.0, 0.0)
        system["coordinator"].alternative_provider.enumerate = lambda _snapshot: AlternativeInventoryResult("ALT_AVAILABLE", (candidate,))
        result = system["coordinator"].run_cycle(first.next_state, ActiveCycleRequest(first.next_state.trial_id, 1, (1.0, 0.0, 0.0), None))
        self.assertEqual(result.alternative_inventory_evidence.status, AlternativeInventoryStatus.ALT_AVAILABLE)
        self.assertEqual(result.action_role, ActionRole.ALTERNATIVE_NAVIGATION)

    def test_only_explicit_finite_absence_maps_exhausted(self):
        _, result = self._second_cycle("NO_ALTERNATIVE_AVAILABLE")
        self.assertEqual(result.alternative_inventory_evidence.status, AlternativeInventoryStatus.NO_ALTERNATIVE_AVAILABLE)
        self.assertIn("ALT_DONE", result.routing_rule_ids)

    def test_invalid_provenance_and_unknown_never_collapse_to_exhausted(self):
        for status, expected in (
            ("SOURCE_INVALID", AlternativeInventoryStatus.SOURCE_INVALID),
            ("PROVENANCE_MISSING", AlternativeInventoryStatus.PROVENANCE_MISSING),
            ("FUTURE_UNEXPECTED_STATUS", AlternativeInventoryStatus.UNRESOLVED_STATUS),
        ):
            with self.subTest(status=status):
                _, result = self._second_cycle(status)
                self.assertEqual(result.alternative_inventory_evidence.status, expected)
                self.assertNotIn("ALT_DONE", result.routing_rule_ids)
                self.assertEqual(result.action_role, ActionRole.RETAINED_BACKUP)


if __name__ == "__main__":
    unittest.main()
