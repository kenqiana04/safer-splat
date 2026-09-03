"""Composition root for reference delegation, BYPASS, and future ACTIVE mode."""

from __future__ import annotations

from .authority_registry import AuthorityRegistry
from .backup_token_store import BackupTokenStore
from .deadline_runtime import RuntimeDeadlineProfile
from .plant_commit import PlantCommitAdapter
from .runtime_types import ActionRole, CommitReceipt, RuntimeMode, RuntimeStateSnapshot, SelectedAction, TraceStepRecord
from .supervisor import Supervisor
from .trace_writer import TraceWriter


class ActiveRunner:
    def __init__(self, mode: RuntimeMode, registry: AuthorityRegistry, supervisor: Supervisor, plant_commit: PlantCommitAdapter, token_store: BackupTokenStore, trace_writer: TraceWriter, deadline_profile: RuntimeDeadlineProfile | None = None) -> None:
        self.mode = mode
        self.registry = registry
        self.supervisor = supervisor
        self.plant_commit = plant_commit
        self.token_store = token_store
        self.trace_writer = trace_writer
        self.deadline_profile = deadline_profile
        self.started = False

    def startup(self) -> None:
        self.registry.verify_all(active=self.mode == RuntimeMode.ACTIVE_RUNTIME_ON)
        if self.mode == RuntimeMode.ACTIVE_RUNTIME_ON and (self.deadline_profile is None or self.registry.deadline_profile_identity != self.deadline_profile.identity):
            from .runtime_errors import DeadlineProfileRequired
            raise DeadlineProfileRequired("DEADLINE_PROFILE_REQUIRED")
        self.started = True

    def commit_bypass(self, snapshot: RuntimeStateSnapshot, reference_action: SelectedAction) -> CommitReceipt:
        if not self.started or self.mode != RuntimeMode.ACTIVE_HARNESS_BYPASS:
            raise RuntimeError("BYPASS_MODE_NOT_STARTED")
        decision = self.supervisor.bypass_decision(snapshot, reference_action)
        receipt = self.plant_commit.commit(decision, snapshot, reference_action)
        self._append(snapshot, decision.selected_action, receipt, "BYPASS_REFERENCE_ACTION_UNCHANGED")
        return receipt

    def commit_active_decision(self, snapshot: RuntimeStateSnapshot, decision) -> CommitReceipt | None:
        if not self.started or self.mode != RuntimeMode.ACTIVE_RUNTIME_ON:
            raise RuntimeError("ACTIVE_MODE_NOT_STARTED")
        if not decision.allows_commit or decision.selected_action is None:
            self._append(snapshot, None, None, decision.reason)
            return None
        receipt = self.plant_commit.commit(decision, snapshot, decision.selected_action)
        if receipt.committed and decision.prepared_bundle is not None and receipt.action_role in {ActionRole.PRIMARY_NAVIGATION, ActionRole.ALTERNATIVE_NAVIGATION}:
            self.token_store.prepare(decision.prepared_bundle)
            self.token_store.activate_after_navigation_commit(receipt, decision.prepared_bundle.identity)
        elif receipt.action_role == ActionRole.RETAINED_BACKUP:
            self.token_store.consume_after_backup_commit(receipt)
        self._append(snapshot, decision.selected_action, receipt, decision.reason)
        return receipt

    def _append(self, snapshot: RuntimeStateSnapshot, action: SelectedAction | None, receipt: CommitReceipt | None, reason: str) -> None:
        role = ActionRole.ASSURANCE_BOUNDARY_NO_ACTION if action is None else action.role
        self.trace_writer.append(TraceStepRecord(snapshot.trial_id, snapshot.cycle_index, snapshot.identity, role, None if action is None else action.identity, None if receipt is None else receipt.executed_action_identity, "NO_ACTION" if receipt is None else receipt.reason, (("runtime_reason", reason), ("map_identity", snapshot.map_identity))))

    def finalize_trace(self):
        return self.trace_writer.finalize()
