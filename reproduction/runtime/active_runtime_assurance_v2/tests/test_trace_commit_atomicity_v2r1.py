from __future__ import annotations

import ast
import tempfile
import unittest
from pathlib import Path

from reproduction.runtime.active_runtime_assurance_v2.commit_transaction import ActiveCommitTransaction
from reproduction.runtime.active_runtime_assurance_v2.backup_token_store import BackupTokenStore
from reproduction.runtime.active_runtime_assurance_v2.runtime_types import (
    ActionRole,
    CommitReceipt,
    CommitTransactionState,
    EvidenceStatus,
    FinalizationStatus,
    PlantOutcome,
    PreparedBackupBundle,
    SupervisorDecision,
    TokenMutationStatus,
    TraceStatus,
    TrialSessionStatus,
    make_action,
    make_candidate,
    CandidateRole,
)
from reproduction.runtime.active_runtime_assurance_v2.tests.public_cycle_test_support import build_public_cycle, start_and_run
from reproduction.runtime.active_runtime_assurance_v2.trace_writer import TraceFinalizedError, TraceWriter


ROOT = Path(__file__).resolve().parents[3]


class RaisingTraceWriter(TraceWriter):
    def append(self, record):
        raise OSError("injected append failure")


class FailOncePersistTraceWriter(TraceWriter):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.persist_attempts = 0

    def _persist(self, lines, candidate_lock):
        self.persist_attempts += 1
        if self.persist_attempts == 1:
            raise OSError("injected persistence failure")
        return super()._persist(lines, candidate_lock)


class AlwaysFailPersistTraceWriter(TraceWriter):
    def _persist(self, lines, candidate_lock):
        raise OSError("injected persistence failure")


class RaisingPlant:
    def __init__(self):
        self.commit_count = 0

    def commit(self, *_args):
        self.commit_count += 1
        raise RuntimeError("ambiguous plant acknowledgement")


class NotCommittedPlant:
    def __init__(self):
        self.commit_count = 0

    def commit(self, _decision, snapshot, action):
        self.commit_count += 1
        return CommitReceipt(
            snapshot.cycle_index,
            snapshot.identity,
            action.identity,
            action.identity,
            action.vector,
            action.role,
            None,
            None,
            False,
            "NOT_COMMITTED_FIXTURE",
        )


class RaisingTokenStore(BackupTokenStore):
    def prepare(self, _bundle):
        raise RuntimeError("token prepare failure")

    def activate_after_navigation_commit(self, *_args):
        raise AssertionError("activation must not follow failed prepare")

    def consume_after_backup_commit(self, _receipt):
        raise RuntimeError("token consume failure")


class TraceCommitAtomicityV2R1Tests(unittest.TestCase):
    def _direct_fixture(self, *, plant=None, token_store=None, trace_writer=None, role=ActionRole.PRIMARY_NAVIGATION, bundle=False):
        system = build_public_cycle()
        state = system["state"]
        action = make_action((0.0, 0.0, 0.0), role, "fixture")
        prepared = None
        if bundle:
            candidate = make_candidate((0.0, 0.0, 0.0), CandidateRole.PRIMARY, "PRIMARY_NATIVE_CBF_QP", "fixture", state)
            prepared = PreparedBackupBundle.create(
                candidate,
                state,
                ((((0.0, 0.0, 0.0)), "backup:0"),),
                system["registry"].geometry.identity.value,
                system["registry"].actuator.identity.value,
                system["registry"].dynamics.identity.value,
                None,
            )
        decision = SupervisorDecision(state.cycle_index, state.identity, action, True, "FIXTURE", "FIXTURE", prepared)
        transaction = ActiveCommitTransaction(
            plant or system["plant"],
            token_store or system["token_store"],
            trace_writer or TraceWriter(state.trial_id),
        )
        return system, state, action, decision, transaction

    @staticmethod
    def _inject_trace_writer(system, writer):
        runner = system["runner"]
        runner.trace_writer = writer
        runner._active_commit_transaction = ActiveCommitTransaction(runner.plant_commit, runner.token_store, writer)
        system["trace_writer"] = writer

    @staticmethod
    def _inject_token_store(system, token_store):
        runner = system["runner"]
        runner.token_store = token_store
        runner._active_commit_transaction = ActiveCommitTransaction(runner.plant_commit, token_store, runner.trace_writer)
        system["coordinator"].backup_token_store = token_store

    @staticmethod
    def _inject_plant(system, plant):
        runner = system["runner"]
        runner.plant_commit = plant
        runner._active_commit_transaction = ActiveCommitTransaction(plant, runner.token_store, runner.trace_writer)

    # TC-TEST-01
    def test_01_preplant_abort_has_zero_plant_calls(self):
        system, state, _action, decision, transaction = self._direct_fixture()
        result = transaction.aborted(state, decision, "PREPLANT_FAILURE")
        self.assertEqual(system["plant"].commit_count, 0)
        self.assertEqual(result.evidence_status, EvidenceStatus.ABORTED_BEFORE_PLANT)
        self.assertEqual(result.plant_outcome, PlantOutcome.NOT_ATTEMPTED)

    # TC-TEST-02
    def test_02_plant_not_committed_is_typed(self):
        plant = NotCommittedPlant()
        _system, state, _action, decision, transaction = self._direct_fixture(plant=plant)
        result = transaction.execute(state, decision)
        self.assertFalse(result.committed)
        self.assertEqual(result.plant_outcome, PlantOutcome.NOT_COMMITTED)
        self.assertEqual(result.evidence_status, EvidenceStatus.PLANT_NOT_COMMITTED)

    # TC-TEST-03
    def test_03_normal_commit_is_complete(self):
        _system, state, _action, decision, transaction = self._direct_fixture()
        result = transaction.execute(state, decision)
        self.assertTrue(result.committed)
        self.assertEqual(result.evidence_status, EvidenceStatus.COMPLETE)
        self.assertEqual(result.transaction_state, CommitTransactionState.COMPLETE)
        self.assertEqual(result.trace_status, TraceStatus.RECORDED)

    # TC-TEST-04
    def test_04_plant_raise_is_unresolved_not_false(self):
        plant = RaisingPlant()
        _system, state, _action, decision, transaction = self._direct_fixture(plant=plant)
        result = transaction.execute(state, decision)
        self.assertIsNone(result.committed)
        self.assertEqual(result.plant_outcome, PlantOutcome.UNRESOLVED)
        self.assertEqual(result.evidence_status, EvidenceStatus.PLANT_OUTCOME_UNRESOLVED)
        self.assertTrue(result.recovery_required)
        self.assertFalse(result.retry_allowed)

    # TC-TEST-05
    def test_05_navigation_token_failure_preserves_commit(self):
        _system, state, _action, decision, transaction = self._direct_fixture(token_store=RaisingTokenStore(), bundle=True)
        result = transaction.execute(state, decision)
        self.assertTrue(result.committed)
        self.assertEqual(result.evidence_status, EvidenceStatus.COMMITTED_TOKEN_INCOMPLETE)
        self.assertEqual(result.token_status, TokenMutationStatus.INCOMPLETE)
        self.assertIsNotNone(result.commit_receipt)

    # TC-TEST-06
    def test_06_backup_consume_failure_preserves_commit(self):
        _system, state, _action, decision, transaction = self._direct_fixture(token_store=RaisingTokenStore(), role=ActionRole.RETAINED_BACKUP)
        result = transaction.execute(state, decision)
        self.assertTrue(result.committed)
        self.assertEqual(result.evidence_status, EvidenceStatus.COMMITTED_TOKEN_INCOMPLETE)

    # TC-TEST-07
    def test_07_trace_f02_returns_typed_result(self):
        writer = RaisingTraceWriter("trial:fixture")
        _system, state, _action, decision, transaction = self._direct_fixture(trace_writer=writer)
        result = transaction.execute(state, decision)
        self.assertEqual(result.evidence_status, EvidenceStatus.COMMITTED_TRACE_INCOMPLETE)
        self.assertEqual(result.trace_status, TraceStatus.INCOMPLETE)
        self.assertTrue(result.committed)

    # TC-TEST-08
    def test_08_boundary_trace_failure_has_zero_plant(self):
        system = build_public_cycle({"proposal": "FAIL"})
        writer = RaisingTraceWriter(system["state"].trial_id)
        self._inject_trace_writer(system, writer)
        _start, result = start_and_run(system)
        self.assertEqual(system["plant"].commit_count, 0)
        self.assertEqual(result.commit_transaction_result.evidence_status, EvidenceStatus.NO_ACTION_TRACE_INCOMPLETE)
        self.assertFalse(result.committed)

    # TC-TEST-09
    def test_09_finalize_failure_does_not_publish_lock(self):
        system = build_public_cycle()
        writer = AlwaysFailPersistTraceWriter(system["state"].trial_id)
        self._inject_trace_writer(system, writer)
        start_and_run(system)
        result = system["coordinator"].finalize_trial()
        self.assertEqual(result.status, FinalizationStatus.FINALIZATION_INCOMPLETE)
        self.assertIsNone(writer._lock)
        self.assertEqual(system["coordinator"].session.status, TrialSessionStatus.FINALIZATION_FAILED)

    # TC-TEST-10
    def test_10_finalize_retry_same_content_succeeds(self):
        system = build_public_cycle()
        with tempfile.TemporaryDirectory() as directory:
            writer = FailOncePersistTraceWriter(system["state"].trial_id, Path(directory))
            self._inject_trace_writer(system, writer)
            start_and_run(system)
            first = system["coordinator"].finalize_trial()
            second = system["coordinator"].finalize_trial()
        self.assertEqual(first.status, FinalizationStatus.FINALIZATION_INCOMPLETE)
        self.assertEqual(second.status, FinalizationStatus.FINALIZED)
        self.assertEqual(first.content_hash, second.content_hash)

    # TC-TEST-11
    def test_11_finalize_retry_changed_identity_requires_recovery(self):
        system = build_public_cycle()
        writer = AlwaysFailPersistTraceWriter(system["state"].trial_id)
        self._inject_trace_writer(system, writer)
        start_and_run(system)
        first = system["coordinator"].finalize_trial()
        writer._records = []  # deliberate corruption fixture after the frozen first attempt
        second = system["coordinator"].finalize_trial()
        self.assertEqual(first.status, FinalizationStatus.FINALIZATION_INCOMPLETE)
        self.assertEqual(second.status, FinalizationStatus.RECOVERY_REQUIRED)
        self.assertEqual(system["coordinator"].session.status, TrialSessionStatus.RECOVERY_REQUIRED)

    # TC-TEST-12
    def test_12_run_cycle_after_trace_incomplete_rejected(self):
        system = build_public_cycle()
        self._inject_trace_writer(system, RaisingTraceWriter(system["state"].trial_id))
        start_and_run(system)
        self.assertEqual(system["coordinator"].session.status, TrialSessionStatus.EVIDENCE_INCOMPLETE)
        with self.assertRaisesRegex(Exception, "TRIAL_NOT_READY"):
            system["coordinator"].run_cycle(system["state"], system["request"])

    # TC-TEST-13
    def test_13_run_cycle_after_token_incomplete_rejected(self):
        system = build_public_cycle()
        self._inject_token_store(system, RaisingTokenStore())
        start_and_run(system)
        self.assertEqual(system["coordinator"].session.status, TrialSessionStatus.EVIDENCE_INCOMPLETE)
        with self.assertRaisesRegex(Exception, "TRIAL_NOT_READY"):
            system["coordinator"].run_cycle(system["state"], system["request"])

    # TC-TEST-14
    def test_14_run_cycle_after_unresolved_plant_rejected(self):
        system = build_public_cycle()
        self._inject_plant(system, RaisingPlant())
        start_and_run(system)
        self.assertEqual(system["coordinator"].session.status, TrialSessionStatus.RECOVERY_REQUIRED)
        with self.assertRaisesRegex(Exception, "TRIAL_NOT_READY"):
            system["coordinator"].run_cycle(system["state"], system["request"])

    # TC-TEST-15
    def test_15_receipt_preserved_after_trace_failure(self):
        _system, state, _action, decision, transaction = self._direct_fixture(trace_writer=RaisingTraceWriter("trial:fixture"))
        result = transaction.execute(state, decision)
        self.assertTrue(result.commit_receipt.committed)

    # TC-TEST-16
    def test_16_post_state_preserved_after_trace_failure(self):
        _system, state, _action, decision, transaction = self._direct_fixture(trace_writer=RaisingTraceWriter("trial:fixture"))
        result = transaction.execute(state, decision)
        self.assertEqual(result.post_state, result.commit_receipt.post_state)
        self.assertIsNotNone(result.post_state)

    # TC-TEST-17
    def test_17_trace_failure_does_not_rollback_token(self):
        system, state, _action, decision, transaction = self._direct_fixture(trace_writer=RaisingTraceWriter("trial:fixture"), bundle=True)
        result = transaction.execute(state, decision)
        self.assertEqual(result.token_status, TokenMutationStatus.APPLIED)
        self.assertIsNotNone(system["token_store"].current())
        self.assertEqual(result.evidence_status, EvidenceStatus.COMMITTED_TRACE_INCOMPLETE)

    # TC-TEST-18
    def test_18_boundary_does_not_fake_zero_action(self):
        system = build_public_cycle({"proposal": "FAIL"})
        _start, result = start_and_run(system)
        self.assertIsNone(result.final_supervisor_decision.selected_action)
        self.assertIsNone(result.next_state)
        self.assertEqual(system["plant"].commit_count, 0)

    # TC-TEST-19
    def test_19_selected_executed_identity_preserved(self):
        _system, state, action, decision, transaction = self._direct_fixture()
        result = transaction.execute(state, decision)
        self.assertEqual(result.selected_action.identity, action.identity)
        self.assertEqual(result.executed_action_identity, action.identity)

    # TC-TEST-20
    def test_20_incomplete_evidence_is_not_oracle_eligible(self):
        _system, state, _action, decision, transaction = self._direct_fixture(trace_writer=RaisingTraceWriter("trial:fixture"))
        result = transaction.execute(state, decision)
        oracle_eligible = result.evidence_status in {EvidenceStatus.COMPLETE, EvidenceStatus.NO_ACTION_COMPLETE}
        self.assertFalse(oracle_eligible)

    # TC-TEST-21
    def test_21_component_declares_memory_only_no_durable_journal(self):
        source = (ROOT / "runtime" / "active_runtime_assurance_v2" / "commit_transaction.py").read_text(encoding="utf-8")
        self.assertIn("memory-level", source)
        self.assertNotIn("fsync", source.lower())
        self.assertFalse((ROOT / "runtime" / "active_runtime_assurance_v2" / "commit_journal.py").exists())

    # TC-TEST-22
    def test_22_plant_exception_is_not_retried(self):
        plant = RaisingPlant()
        _system, state, _action, decision, transaction = self._direct_fixture(plant=plant)
        result = transaction.execute(state, decision)
        self.assertEqual(plant.commit_count, 1)
        self.assertFalse(result.retry_allowed)

    # TC-TEST-23
    def test_23_bypass_execution_body_preserved(self):
        path = ROOT / "runtime" / "active_runtime_assurance_v2" / "active_runner.py"
        current = ast.parse(path.read_text(encoding="utf-8"))
        upstream = ast.parse(__import__("subprocess").check_output(["git", "show", "d7d2703f305d43661cf24bb818d846a092a67066:" + str(path.relative_to(ROOT.parent)).replace("\\", "/")], text=True))
        def body(tree):
            return ast.dump(next(node for node in ast.walk(tree) if isinstance(node, ast.FunctionDef) and node.name == "commit_bypass"), include_attributes=False)
        self.assertEqual(body(current), body(upstream))

    # TC-TEST-24
    def test_24_append_disabled_after_finalize_failure(self):
        system = build_public_cycle()
        writer = AlwaysFailPersistTraceWriter(system["state"].trial_id)
        self._inject_trace_writer(system, writer)
        start_and_run(system)
        system["coordinator"].finalize_trial()
        with self.assertRaises(TraceFinalizedError):
            writer.append(writer.records[0])

    def test_25_complete_state_history_is_legal(self):
        _system, state, _action, decision, transaction = self._direct_fixture()
        result = transaction.execute(state, decision)
        self.assertEqual(
            result.state_history,
            (
                CommitTransactionState.PREPARED,
                CommitTransactionState.PLANT_ATTEMPTED,
                CommitTransactionState.COMMITTED,
                CommitTransactionState.TRACE_RECORDED,
                CommitTransactionState.COMPLETE,
            ),
        )

    def test_26_trace_never_precedes_commit_in_history(self):
        _system, state, _action, decision, transaction = self._direct_fixture()
        history = transaction.execute(state, decision).state_history
        self.assertLess(history.index(CommitTransactionState.COMMITTED), history.index(CommitTransactionState.TRACE_RECORDED))

    def test_27_finalize_failure_freezes_canonical_hash(self):
        system = build_public_cycle()
        writer = AlwaysFailPersistTraceWriter(system["state"].trial_id)
        self._inject_trace_writer(system, writer)
        start_and_run(system)
        result = system["coordinator"].finalize_trial()
        self.assertTrue(result.content_hash)
        self.assertEqual(result.content_hash, writer.frozen_trace_sha256)

    def test_28_shared_finalize_requires_bypass_revalidation(self):
        design = ROOT / "design" / "active_runtime_trace_commit_atomicity_v2r1" / "TRACE_COMMIT_BYPASS_IMPACT_V2R1.json"
        self.assertIn('"BYPASS_REVALIDATION_REQUIRED": true', design.read_text(encoding="utf-8"))


if __name__ == "__main__":
    unittest.main()
