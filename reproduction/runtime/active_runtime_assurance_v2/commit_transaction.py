"""Active-only memory-level commit/evidence transaction state machine.

This module sequences existing owners.  It does not provide physical ACID,
durable crash recovery, plant authority, token authority, or trace authority.
"""

from __future__ import annotations

from .backup_token_store import BackupTokenStore
from .plant_commit import PlantCommitAdapter
from .runtime_types import (
    ActionRole,
    CommitTransactionResult,
    CommitTransactionState,
    EvidenceStatus,
    PlantOutcome,
    RuntimeStateSnapshot,
    SelectedAction,
    TokenMutationStatus,
    TraceStatus,
    TraceStepRecord,
    canonical_sha256,
)
from .trace_writer import TraceWriter


class ActiveCommitTransaction:
    """Sequence one ACTIVE commit attempt while retaining execution facts."""

    def __init__(self, plant_commit: PlantCommitAdapter, token_store: BackupTokenStore, trace_writer: TraceWriter) -> None:
        self.plant_commit = plant_commit
        self.token_store = token_store
        self.trace_writer = trace_writer

    @staticmethod
    def attempt_identity(snapshot: RuntimeStateSnapshot, decision) -> str:
        material = {
            "trial_id": snapshot.trial_id,
            "cycle_index": snapshot.cycle_index,
            "snapshot_identity": snapshot.identity,
            "map_identity": snapshot.map_identity,
            "decision": decision,
            "selected_action_identity": None if decision.selected_action is None else decision.selected_action.identity,
        }
        return "commit-attempt:sha256:" + canonical_sha256(material)

    @staticmethod
    def _record(snapshot: RuntimeStateSnapshot, action: SelectedAction | None, receipt, reason: str) -> TraceStepRecord:
        role = ActionRole.ASSURANCE_BOUNDARY_NO_ACTION if action is None else action.role
        return TraceStepRecord(
            snapshot.trial_id,
            snapshot.cycle_index,
            snapshot.identity,
            role,
            None if action is None else action.identity,
            None if receipt is None else receipt.executed_action_identity,
            "NO_ACTION" if receipt is None else receipt.reason,
            (("runtime_reason", reason), ("map_identity", snapshot.map_identity)),
        )

    def _append(self, record: TraceStepRecord) -> str:
        self.trace_writer.append(record)
        return "trace-step:sha256:" + canonical_sha256(record)

    def aborted(self, snapshot: RuntimeStateSnapshot, decision, reason: str) -> CommitTransactionResult:
        return CommitTransactionResult(
            self.attempt_identity(snapshot, decision),
            CommitTransactionState.PREPARED,
            PlantOutcome.NOT_ATTEMPTED,
            EvidenceStatus.ABORTED_BEFORE_PLANT,
            TokenMutationStatus.UNCHANGED,
            TraceStatus.NOT_ATTEMPTED,
            False,
            None,
            decision.selected_action,
            None,
            None,
            None,
            False,
            False,
            reason,
            (CommitTransactionState.PREPARED,),
        )

    def execute(self, snapshot: RuntimeStateSnapshot, decision) -> CommitTransactionResult:
        attempt = self.attempt_identity(snapshot, decision)
        action = decision.selected_action
        history = (CommitTransactionState.PREPARED,)

        if not decision.allows_commit or action is None:
            record = self._record(snapshot, None, None, decision.reason)
            try:
                trace_ref = self._append(record)
            except Exception as exc:
                return CommitTransactionResult(
                    attempt, CommitTransactionState.EVIDENCE_INCOMPLETE, PlantOutcome.NOT_ATTEMPTED,
                    EvidenceStatus.NO_ACTION_TRACE_INCOMPLETE, TokenMutationStatus.UNCHANGED,
                    TraceStatus.INCOMPLETE, False, None, None, None, None, None, True, False,
                    f"NO_ACTION_TRACE_INCOMPLETE:{type(exc).__name__}",
                    history + (CommitTransactionState.EVIDENCE_INCOMPLETE,),
                )
            return CommitTransactionResult(
                attempt, CommitTransactionState.COMPLETE, PlantOutcome.NOT_ATTEMPTED,
                EvidenceStatus.NO_ACTION_COMPLETE, TokenMutationStatus.UNCHANGED,
                TraceStatus.RECORDED, False, None, None, None, None, trace_ref, False, False,
                decision.reason,
                history + (CommitTransactionState.TRACE_RECORDED, CommitTransactionState.COMPLETE),
            )

        history += (CommitTransactionState.PLANT_ATTEMPTED,)
        try:
            receipt = self.plant_commit.commit(decision, snapshot, action)
        except Exception as exc:
            return CommitTransactionResult(
                attempt, CommitTransactionState.RECOVERY_REQUIRED, PlantOutcome.UNRESOLVED,
                EvidenceStatus.PLANT_OUTCOME_UNRESOLVED, TokenMutationStatus.INCOMPLETE,
                TraceStatus.NOT_ATTEMPTED, None, None, action, None, None, None, True, False,
                f"PLANT_OUTCOME_UNRESOLVED:{type(exc).__name__}",
                history + (CommitTransactionState.PLANT_OUTCOME_UNRESOLVED, CommitTransactionState.RECOVERY_REQUIRED),
            )

        if not receipt.committed:
            history += (CommitTransactionState.PLANT_NOT_COMMITTED,)
            try:
                trace_ref = self._append(self._record(snapshot, action, receipt, decision.reason))
                trace_status = TraceStatus.RECORDED
                recovery_required = False
                state = CommitTransactionState.PLANT_NOT_COMMITTED
                failure = receipt.reason
            except Exception as exc:
                trace_ref = None
                trace_status = TraceStatus.INCOMPLETE
                recovery_required = True
                state = CommitTransactionState.EVIDENCE_INCOMPLETE
                history += (state,)
                failure = f"PLANT_NOT_COMMITTED_TRACE_INCOMPLETE:{type(exc).__name__}"
            return CommitTransactionResult(
                attempt, state, PlantOutcome.NOT_COMMITTED, EvidenceStatus.PLANT_NOT_COMMITTED,
                TokenMutationStatus.UNCHANGED, trace_status, False, receipt, action,
                receipt.executed_action_identity, receipt.post_state, trace_ref, recovery_required, False,
                failure, history,
            )

        history += (CommitTransactionState.COMMITTED,)
        token_status = TokenMutationStatus.NOT_APPLICABLE
        try:
            if decision.prepared_bundle is not None and receipt.action_role in {ActionRole.PRIMARY_NAVIGATION, ActionRole.ALTERNATIVE_NAVIGATION}:
                self.token_store.prepare(decision.prepared_bundle)
                self.token_store.activate_after_navigation_commit(receipt, decision.prepared_bundle.identity)
                token_status = TokenMutationStatus.APPLIED
                history += (CommitTransactionState.TOKEN_APPLIED,)
            elif receipt.action_role == ActionRole.RETAINED_BACKUP:
                self.token_store.consume_after_backup_commit(receipt)
                token_status = TokenMutationStatus.APPLIED
                history += (CommitTransactionState.TOKEN_APPLIED,)
        except Exception as exc:
            return CommitTransactionResult(
                attempt, CommitTransactionState.EVIDENCE_INCOMPLETE, PlantOutcome.COMMITTED,
                EvidenceStatus.COMMITTED_TOKEN_INCOMPLETE, TokenMutationStatus.INCOMPLETE,
                TraceStatus.INCOMPLETE, True, receipt, action, receipt.executed_action_identity,
                receipt.post_state, None, True, False,
                f"COMMITTED_TOKEN_INCOMPLETE:{type(exc).__name__}",
                history + (CommitTransactionState.EVIDENCE_INCOMPLETE,),
            )

        try:
            trace_ref = self._append(self._record(snapshot, action, receipt, decision.reason))
        except Exception as exc:
            return CommitTransactionResult(
                attempt, CommitTransactionState.EVIDENCE_INCOMPLETE, PlantOutcome.COMMITTED,
                EvidenceStatus.COMMITTED_TRACE_INCOMPLETE, token_status, TraceStatus.INCOMPLETE,
                True, receipt, action, receipt.executed_action_identity, receipt.post_state, None,
                True, False, f"COMMITTED_TRACE_INCOMPLETE:{type(exc).__name__}",
                history + (CommitTransactionState.EVIDENCE_INCOMPLETE,),
            )

        return CommitTransactionResult(
            attempt, CommitTransactionState.COMPLETE, PlantOutcome.COMMITTED, EvidenceStatus.COMPLETE,
            token_status, TraceStatus.RECORDED, True, receipt, action,
            receipt.executed_action_identity, receipt.post_state, trace_ref, False, False,
            receipt.reason,
            history + (CommitTransactionState.TRACE_RECORDED, CommitTransactionState.COMPLETE),
        )
