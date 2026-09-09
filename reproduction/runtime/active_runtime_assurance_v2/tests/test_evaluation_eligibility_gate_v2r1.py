from __future__ import annotations

import unittest

from reproduction.runtime.active_runtime_assurance_v2.commit_transaction import ActiveCommitTransaction
from reproduction.runtime.active_runtime_assurance_v2.runtime_types import FinalizationStatus, TrialSessionStatus
from reproduction.runtime.active_runtime_assurance_v2.tests.public_cycle_test_support import build_public_cycle, start_and_run
from reproduction.runtime.active_runtime_assurance_v2.tests.test_trace_commit_atomicity_v2r1 import RaisingPlant
from reproduction.runtime.active_runtime_assurance_v2.trace_writer import TraceWriter


class CountingTraceWriter(TraceWriter):
    def __init__(self, trial_id: str, *, fail_append: bool = False) -> None:
        super().__init__(trial_id)
        self.fail_append = fail_append
        self.finalize_calls = 0

    def append(self, record) -> None:
        if self.fail_append:
            raise OSError("injected append failure")
        super().append(record)

    def finalize(self):
        self.finalize_calls += 1
        return super().finalize()


def inject_writer(system, writer: TraceWriter) -> None:
    runner = system["runner"]
    runner.trace_writer = writer
    runner._active_commit_transaction = ActiveCommitTransaction(runner.plant_commit, runner.token_store, writer)
    system["trace_writer"] = writer


def inject_plant(system, plant) -> None:
    runner = system["runner"]
    runner.plant_commit = plant
    runner._active_commit_transaction = ActiveCommitTransaction(plant, runner.token_store, runner.trace_writer)
    system["plant"] = plant


class EvaluationEligibilityGateV2R1Tests(unittest.TestCase):
    def assert_evaluation_ineligible(self, system, writer, expected_session: TrialSessionStatus) -> None:
        result = system["coordinator"].finalize_trial()

        self.assertEqual(result.status, FinalizationStatus.RECOVERY_REQUIRED)
        self.assertIsNone(result.trace_lock)
        self.assertFalse(result.retry_allowed)
        self.assertTrue(result.recovery_required)
        self.assertIn("TRIAL_EVALUATION_INELIGIBLE", result.failure_reason)
        self.assertEqual(writer.finalize_calls, 0)
        self.assertIsNone(writer._lock)
        self.assertEqual(system["coordinator"].session.status, expected_session)
        with self.assertRaisesRegex(Exception, "TRIAL_NOT_READY"):
            system["coordinator"].run_cycle(system["state"], system["request"])

    def test_c12_trace_incomplete_trial_cannot_finalize(self):
        system = build_public_cycle()
        writer = CountingTraceWriter(system["state"].trial_id, fail_append=True)
        inject_writer(system, writer)
        start_and_run(system)

        self.assertEqual(system["coordinator"].session.status, TrialSessionStatus.EVIDENCE_INCOMPLETE)
        self.assert_evaluation_ineligible(system, writer, TrialSessionStatus.EVIDENCE_INCOMPLETE)

    def test_e01_plant_unresolved_trial_cannot_finalize(self):
        system = build_public_cycle()
        writer = CountingTraceWriter(system["state"].trial_id)
        inject_writer(system, writer)
        inject_plant(system, RaisingPlant())
        start_and_run(system)

        self.assertEqual(system["coordinator"].session.status, TrialSessionStatus.RECOVERY_REQUIRED)
        self.assert_evaluation_ineligible(system, writer, TrialSessionStatus.RECOVERY_REQUIRED)

    def test_e02_no_action_trace_incomplete_trial_cannot_finalize(self):
        system = build_public_cycle({"proposal": "FAIL"})
        writer = CountingTraceWriter(system["state"].trial_id, fail_append=True)
        inject_writer(system, writer)
        start_and_run(system)

        self.assertEqual(system["coordinator"].session.status, TrialSessionStatus.EVIDENCE_INCOMPLETE)
        self.assert_evaluation_ineligible(system, writer, TrialSessionStatus.EVIDENCE_INCOMPLETE)


if __name__ == "__main__":
    unittest.main()
