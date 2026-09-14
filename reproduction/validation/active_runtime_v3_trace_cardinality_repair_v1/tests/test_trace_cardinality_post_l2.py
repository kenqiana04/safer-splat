from __future__ import annotations

import unittest

from reproduction.runtime.active_runtime_assurance_v2.runtime_types import (
    ActionRole,
    DeadlineStatus,
    EvidenceStatus,
)
from reproduction.runtime.active_runtime_assurance_v2.tests.public_cycle_test_support import (
    build_public_cycle,
    start_and_run,
)


class _AdvanceClockAfterL2:
    def __init__(self, delegate, clock, seconds: float) -> None:
        self._delegate = delegate
        self._clock = clock
        self._seconds = seconds

    def evaluate(self, snapshot, candidate):
        result = self._delegate.evaluate(snapshot, candidate)
        self._clock.advance(self._seconds)
        return result


class TraceCardinalityPostL2Tests(unittest.TestCase):
    def test_post_l2_warning_block_is_traced_without_plant_or_l3(self):
        system = build_public_cycle()
        coordinator = system["coordinator"]
        coordinator.l2_runtime = _AdvanceClockAfterL2(
            coordinator.l2_runtime,
            system["clock"],
            8.5,
        )

        _, result = start_and_run(system)

        self.assertEqual(system["counters"]["l2"], 1)
        self.assertEqual(system["counters"]["l3"], 0)
        self.assertEqual(result.deadline_observations[-1].status, DeadlineStatus.WARNING)
        self.assertEqual(result.typed_stop_or_failure_reason, "ROUTING_RULE_MISSING")
        self.assertEqual(result.final_supervisor_decision.rule_id, "ROUTING_BLOCK")
        self.assertFalse(result.final_supervisor_decision.allows_commit)
        self.assertIsNone(result.final_supervisor_decision.selected_action)
        self.assertTrue(result.boundary)
        self.assertFalse(result.committed)
        self.assertIsNone(result.next_state)
        self.assertEqual(system["plant"].commit_count, 0)
        self.assertEqual(len(system["trace_writer"].records), 1)
        self.assertEqual(
            system["trace_writer"].records[0].action_role,
            ActionRole.ASSURANCE_BOUNDARY_NO_ACTION,
        )
        self.assertEqual(
            result.commit_transaction_result.evidence_status,
            EvidenceStatus.NO_ACTION_COMPLETE,
        )
        self.assertIsNotNone(result.trace_ref)

        finalization = coordinator.finalize_trial()
        self.assertEqual(finalization.trace_lock.record_count, 1)

    def test_pre_l2_warning_block_uses_same_trace_authority(self):
        system = build_public_cycle({"l1_advance": 8.5})
        _, result = start_and_run(system)

        self.assertEqual(result.typed_stop_or_failure_reason, "ROUTING_RULE_MISSING")
        self.assertEqual(system["counters"]["proposal"], 0)
        self.assertEqual(system["plant"].commit_count, 0)
        self.assertEqual(len(system["trace_writer"].records), 1)
        self.assertEqual(
            result.commit_transaction_result.evidence_status,
            EvidenceStatus.NO_ACTION_COMPLETE,
        )

    def test_normal_primary_path_still_commits_and_traces_once(self):
        system = build_public_cycle()
        _, result = start_and_run(system)

        self.assertTrue(result.committed)
        self.assertFalse(result.boundary)
        self.assertEqual(system["plant"].commit_count, 1)
        self.assertEqual(len(system["trace_writer"].records), 1)
        self.assertEqual(result.commit_transaction_result.evidence_status, EvidenceStatus.COMPLETE)


if __name__ == "__main__":
    unittest.main()
