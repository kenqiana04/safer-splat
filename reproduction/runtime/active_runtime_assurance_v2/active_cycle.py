"""Public Active Runtime V2 cycle composition root.

The coordinator sequences frozen runtime modules.  Routing and final action
selection remain Supervisor authorities; plant, token, and trace side effects
remain inside the unchanged ActiveRunner commit boundary.
"""

from __future__ import annotations

from dataclasses import replace
from typing import Any, Callable

from .active_runner import ActiveRunner
from .alternative_provider import NativeExistingAlternativeProvider
from .authority_registry import AuthorityRegistry
from .backup_token_store import BackupTokenStore
from .c0_admission import C0Admission
from .deadline_runtime import DeadlineTracker
from .diagnostic_r0 import DiagnosticR0
from .l1_runtime import L1Runtime
from .l2_runtime import L2Runtime
from .l3_runtime import L3Runtime
from .primary_proposal_adapter import PrimaryProposalAdapter
from .runtime_types import (
    ActiveCycleContext,
    ActiveCycleRequest,
    ActiveCycleResult,
    ActiveTrialContext,
    Candidate,
    CandidateRole,
    CertificateStatus,
    CoordinatorSession,
    DeadlineObservation,
    DeadlineStatus,
    EvidenceResult,
    PublicCycleEvent,
    PublicCyclePhase,
    RouteResolutionStatus,
    RoutingDecision,
    RuntimePhase,
    RuntimeRoutingContext,
    RuntimeStateSnapshot,
    TrialSessionStatus,
    TrialStartResult,
    canonical_sha256,
)
from .start_admission import StartAdmission
from .supervisor import Supervisor
from .terminal_runtime import TerminalRuntime


class PublicCycleStateError(RuntimeError):
    """Typed session/orchestration block with no action authority."""


class ActiveCycleCoordinator:
    """Sole public composition owner for one frozen Active runtime trial."""

    def __init__(
        self,
        registry: AuthorityRegistry,
        start_admission: StartAdmission,
        diagnostic_r0: DiagnosticR0,
        l1_runtime: L1Runtime,
        primary_proposal: PrimaryProposalAdapter,
        c0_admission: C0Admission,
        l2_runtime: L2Runtime,
        l3_runtime: L3Runtime,
        alternative_provider: NativeExistingAlternativeProvider,
        backup_token_store: BackupTokenStore,
        terminal_runtime: TerminalRuntime,
        deadline_tracker: DeadlineTracker,
        supervisor: Supervisor,
        active_runner: ActiveRunner,
    ) -> None:
        if active_runner.registry is not registry or active_runner.supervisor is not supervisor:
            raise PublicCycleStateError("COORDINATOR_RUNNER_AUTHORITY_IDENTITY_MISMATCH")
        if active_runner.token_store is not backup_token_store:
            raise PublicCycleStateError("COORDINATOR_TOKEN_STORE_IDENTITY_MISMATCH")
        self.registry = registry
        self.start_admission = start_admission
        self.diagnostic_r0 = diagnostic_r0
        self.l1_runtime = l1_runtime
        self.primary_proposal = primary_proposal
        self.c0_admission = c0_admission
        self.l2_runtime = l2_runtime
        self.l3_runtime = l3_runtime
        self.alternative_provider = alternative_provider
        self.backup_token_store = backup_token_store
        self.terminal_runtime = terminal_runtime
        self.deadline_tracker = deadline_tracker
        self.supervisor = supervisor
        self.active_runner = active_runner
        self._session: CoordinatorSession | None = None

    @property
    def session(self) -> CoordinatorSession | None:
        return self._session

    def _routing_context(
        self,
        source_phase: RuntimePhase,
        deadline: DeadlineObservation,
        *,
        candidate: Candidate | None = None,
        candidate_available: bool | None = None,
        backup_present: bool = False,
        backup_valid: bool = False,
        alternative_search_allowed: bool = False,
        navigation_ready: bool = False,
        terminal_evaluated: bool = False,
        terminal_ready: bool = False,
        reason_scope: str = "NONE",
    ) -> RuntimeRoutingContext:
        return RuntimeRoutingContext(
            source_phase=source_phase,
            deadline=deadline,
            authority_identity=self.registry.transition_table_identity,
            candidate_role=None if candidate is None else candidate.role,
            candidate_identity=None if candidate is None else candidate.identity,
            candidate_available=(candidate is not None) if candidate_available is None else candidate_available,
            retained_backup_present=backup_present,
            retained_backup_valid=backup_valid,
            alternative_search_allowed=alternative_search_allowed,
            navigation_ready=navigation_ready,
            terminal_evaluated=terminal_evaluated,
            terminal_ready=terminal_ready,
            reason_scope=reason_scope,
        )

    def _route(
        self,
        context: ActiveCycleContext,
        event: PublicCycleEvent,
        routing_context: RuntimeRoutingContext,
        seen: set[tuple[str, str, str, str, str, bool, bool]],
    ) -> tuple[ActiveCycleContext, RoutingDecision]:
        state = (
            routing_context.source_phase.value,
            event.value,
            routing_context.deadline.status.value,
            "NONE" if routing_context.candidate_role is None else routing_context.candidate_role.value,
            "NONE" if routing_context.candidate_identity is None else routing_context.candidate_identity.value,
            routing_context.retained_backup_valid,
            routing_context.terminal_evaluated,
        )
        if state in seen:
            decision = RoutingDecision(
                RouteResolutionStatus.BLOCKED_AMBIGUOUS,
                None,
                routing_context.source_phase,
                None,
                False,
                False,
                False,
                "ROUTING_STATE_REPEATED",
                "FROZEN_FINITE_GRAPH_GUARD",
                False,
                False,
                False,
                "ROUTING_STATE_REPEATED",
            )
        else:
            seen.add(state)
            decision = self.supervisor.route_transition(event, routing_context)
        return replace(context, routing_decisions=context.routing_decisions + (decision,)), decision

    @staticmethod
    def _advance(context: ActiveCycleContext, phase: PublicCyclePhase, **changes: Any) -> ActiveCycleContext:
        return replace(context, phase=phase, phase_history=context.phase_history + (phase,), **changes)

    def _observe(self, context: ActiveCycleContext, stage: str) -> tuple[ActiveCycleContext, DeadlineObservation]:
        observation = self.deadline_tracker.observe(stage)
        return replace(context, deadline_observations=context.deadline_observations + (observation,)), observation

    @staticmethod
    def _safe_call(function: Callable[..., Any], *args: Any, **kwargs: Any) -> tuple[Any | None, str | None]:
        try:
            return function(*args, **kwargs), None
        except Exception as exc:
            return None, f"STAGE_EXCEPTION:{type(exc).__name__}"

    def _trace_ref(self) -> str | None:
        records = self.active_runner.trace_writer.records
        if not records:
            return None
        return "trace-step:sha256:" + canonical_sha256(records[-1])

    def _blocked_result(self, context: ActiveCycleContext, reason: str) -> ActiveCycleResult:
        self._session = replace(self._require_session(), status=TrialSessionStatus.BLOCKED)
        return self._result(context, None, False, True, reason)

    def _result(
        self,
        context: ActiveCycleContext,
        decision,
        committed: bool,
        boundary: bool,
        reason: str,
    ) -> ActiveCycleResult:
        candidates = []
        if context.primary_candidate is not None:
            candidates.append(context.primary_candidate.identity)
        candidates.extend(context.alternative_attempts)
        certificates = []
        if context.l1_result is not None:
            certificates.extend((context.l1_result.identity, context.l1_result.evidence_identity))
        if context.primary_l2 is not None:
            certificates.extend((context.primary_l2.identity, context.primary_l2.evidence_identity))
        if context.primary_l3 is not None and context.primary_l3.evidence_identity:
            certificates.append(context.primary_l3.evidence_identity)
        if context.backup_validation is not None:
            certificates.append(context.backup_validation.evidence_identity)
        if context.terminal_result is not None and context.terminal_result.evidence_identity:
            certificates.append(context.terminal_result.evidence_identity)
        receipt = context.commit_receipt
        return ActiveCycleResult(
            trial_id=context.trial_id,
            cycle_index=context.cycle_index,
            start_state_id=context.state_id,
            phase_history=context.phase_history,
            routing_rule_ids=tuple(item.rule_id for item in context.routing_decisions if item.rule_id is not None),
            deadline_observations=context.deadline_observations,
            l1_result=context.l1_result,
            candidate_refs=tuple(candidates),
            certificate_refs=tuple(dict.fromkeys(certificates)),
            backup_status="NOT_CHECKED" if context.backup_validation is None else context.backup_validation.reason,
            terminal_status="NOT_EVALUATED" if context.terminal_result is None else context.terminal_result.status.value,
            final_supervisor_decision=decision,
            supervisor_reason=reason if decision is None else decision.reason,
            action_role=None if decision is None or decision.selected_action is None else decision.selected_action.role,
            commit_receipt=receipt,
            committed=committed,
            next_state=None if receipt is None else receipt.post_state,
            boundary=boundary,
            trace_ref=context.trace_ref,
            typed_stop_or_failure_reason=reason,
        )

    def _require_session(self) -> CoordinatorSession:
        if self._session is None:
            raise PublicCycleStateError("TRIAL_NOT_STARTED")
        return self._session

    def start_trial(self, initial_snapshot: RuntimeStateSnapshot, trial_context: ActiveTrialContext) -> TrialStartResult:
        if self._session is not None:
            raise PublicCycleStateError("TRIAL_ALREADY_STARTED")
        if initial_snapshot.trial_id != trial_context.trial_id or initial_snapshot.map_identity != trial_context.expected_map_identity or initial_snapshot.cycle_index != trial_context.initial_cycle_index:
            raise PublicCycleStateError("TRIAL_START_IDENTITY_MISMATCH")
        self.active_runner.startup()
        self.deadline_tracker.start()
        deadline = self.deadline_tracker.observe(RuntimePhase.START_ADMISSION.value)
        admission = self.start_admission.evaluate(initial_snapshot)
        route_event = PublicCycleEvent.INITIAL_SAFE if admission.status == CertificateStatus.PASS else PublicCycleEvent.INITIAL_REPAIR_REQUIRED
        route = self.supervisor.route_transition(
            route_event,
            self._routing_context(RuntimePhase.START_ADMISSION, deadline),
        )
        routes = (route,)
        if route.status != RouteResolutionStatus.RESOLVED:
            self._session = CoordinatorSession(trial_context.trial_id, trial_context.expected_map_identity, trial_context.initial_cycle_index, TrialSessionStatus.BLOCKED)
            return TrialStartResult(trial_context.trial_id, admission.status, False, True, route.reason, admission, None, (PublicCyclePhase.START_ADMISSION, PublicCyclePhase.TRIAL_BLOCKED_AT_ADMISSION), routes)
        if admission.status != CertificateStatus.PASS:
            repair_event = PublicCycleEvent.REPAIR_FAIL if admission.status == CertificateStatus.FAIL else PublicCycleEvent.REPAIR_UNKNOWN
            repair_route = self.supervisor.route_transition(
                repair_event,
                self._routing_context(RuntimePhase.REPAIR, deadline),
            )
            routes += (repair_route,)
            self._session = CoordinatorSession(trial_context.trial_id, trial_context.expected_map_identity, trial_context.initial_cycle_index, TrialSessionStatus.BLOCKED)
            return TrialStartResult(trial_context.trial_id, admission.status, False, True, admission.reason, admission, None, (PublicCyclePhase.START_ADMISSION, PublicCyclePhase.TRIAL_BLOCKED_AT_ADMISSION), routes)
        diagnostic = self.diagnostic_r0.inspect(initial_snapshot)
        r0_route = self.supervisor.route_transition(
            PublicCycleEvent.R0_DIAGNOSTIC_COMPLETE,
            self._routing_context(RuntimePhase.RUNTIME_CURRENT_ROLE, deadline),
        )
        routes += (r0_route,)
        ready = r0_route.status == RouteResolutionStatus.RESOLVED and r0_route.destination_phase == RuntimePhase.L1
        self._session = CoordinatorSession(trial_context.trial_id, trial_context.expected_map_identity, trial_context.initial_cycle_index, TrialSessionStatus.READY if ready else TrialSessionStatus.BLOCKED)
        return TrialStartResult(
            trial_context.trial_id,
            CertificateStatus.PASS if ready else CertificateStatus.UNKNOWN,
            ready,
            not ready,
            diagnostic.reason if ready else r0_route.reason,
            admission,
            diagnostic,
            (PublicCyclePhase.START_ADMISSION, PublicCyclePhase.R0_DIAGNOSTIC, PublicCyclePhase.TRIAL_READY if ready else PublicCyclePhase.TRIAL_BLOCKED_AT_ADMISSION),
            routes,
        )

    def run_cycle(self, snapshot: RuntimeStateSnapshot, cycle_context: ActiveCycleRequest) -> ActiveCycleResult:
        session = self._require_session()
        if session.status != TrialSessionStatus.READY:
            raise PublicCycleStateError("TRIAL_NOT_READY")
        if cycle_context.trial_id != session.trial_id or snapshot.trial_id != session.trial_id or cycle_context.cycle_index != session.next_cycle_index or snapshot.cycle_index != session.next_cycle_index or snapshot.map_identity != session.map_identity:
            raise PublicCycleStateError("CYCLE_OR_SNAPSHOT_IDENTITY_MISMATCH")
        self.deadline_tracker.start()
        first_deadline = self.deadline_tracker.observe(PublicCyclePhase.CYCLE_BEGIN.value)
        token = self.backup_token_store.current()
        backup_evidence = self.backup_token_store.validate(snapshot, self.registry)
        backup_valid = backup_evidence.status == CertificateStatus.PASS
        backup_action = None
        if backup_valid and token is not None and token.current_action is not None:
            vector, action_id = token.current_action
            backup_action = self.supervisor.make_retained_backup_action(vector, action_id)
        context = ActiveCycleContext(
            trial_id=snapshot.trial_id,
            cycle_index=snapshot.cycle_index,
            snapshot_id=snapshot.identity.value,
            state_id=snapshot.identity.value,
            authority_identity=self.registry.transition_table_identity,
            deadline_identity=first_deadline.profile_identity,
            phase=PublicCyclePhase.CYCLE_BEGIN,
            phase_history=(PublicCyclePhase.CYCLE_BEGIN,),
            deadline_observations=(first_deadline,),
            backup_validation=backup_evidence,
            backup_action=backup_action,
        )
        seen: set[tuple[str, str, str, str, str, bool, bool]] = set()
        l1_value, error = self._safe_call(self.l1_runtime.evaluate_cycle, snapshot)
        if error:
            route_context = self._routing_context(RuntimePhase.L1, first_deadline, backup_present=token is not None, backup_valid=backup_valid)
            context, _ = self._route(context, PublicCycleEvent.STAGE_EXCEPTION, route_context, seen)
            return self._blocked_result(context, error)
        context = self._advance(context, PublicCyclePhase.L1_IMMEDIATE_CERTIFICATION, l1_result=l1_value)
        context, deadline = self._observe(context, "PRIMARY_PROPOSAL_ADMISSION")
        l1_event = self._l1_event(l1_value.status, l1_value.reason)
        context, route = self._route(
            context,
            l1_event,
            self._routing_context(RuntimePhase.L1, deadline, backup_present=token is not None, backup_valid=backup_valid, reason_scope=self._reason_scope(l1_value.reason)),
            seen,
        )
        if route.status != RouteResolutionStatus.RESOLVED:
            return self._blocked_result(context, route.reason)

        candidate: Candidate | None = None
        certified_candidate: Candidate | None = None
        l2_result = None
        l3_result = None
        terminal_result = None
        alternative_candidates: tuple[Candidate, ...] | None = None
        alternative_index = 0
        attempt_index = 0

        while True:
            destination = route.destination_phase
            if destination == RuntimePhase.PRIMARY_PROPOSAL:
                context = self._advance(context, PublicCyclePhase.PRIMARY_PROPOSAL)
                proposal, error = self._safe_call(self.primary_proposal.propose, snapshot, cycle_context.desired_reference)
                if error:
                    context, route = self._route(context, PublicCycleEvent.STAGE_EXCEPTION, self._routing_context(RuntimePhase.PRIMARY_PROPOSAL, deadline, backup_present=token is not None, backup_valid=backup_valid), seen)
                    return self._blocked_result(context, error)
                candidate = proposal.candidate if proposal.status == CertificateStatus.PASS else None
                binding = None
                if candidate is not None:
                    binding = self.l1_runtime.bind_attempt(l1_value, candidate, attempt_index)
                    attempt_index += 1
                context = replace(context, primary_candidate=candidate, primary_binding=binding)
                event = PublicCycleEvent.PRIMARY_AVAILABLE if candidate is not None else PublicCycleEvent.NO_CANDIDATE
                context, route = self._route(context, event, self._routing_context(RuntimePhase.PRIMARY_PROPOSAL, deadline, candidate=candidate, backup_present=token is not None, backup_valid=backup_valid), seen)

            elif destination == RuntimePhase.C0:
                if candidate is None:
                    return self._blocked_result(context, "C0_WITHOUT_CANDIDATE")
                phase = PublicCyclePhase.PRIMARY_C0 if candidate.role == CandidateRole.PRIMARY else PublicCyclePhase.ALTERNATIVE_C0
                context = self._advance(context, phase)
                c0_result, error = self._safe_call(self.c0_admission.evaluate, candidate, snapshot)
                if error:
                    context, route = self._route(context, PublicCycleEvent.STAGE_EXCEPTION, self._routing_context(RuntimePhase.C0, deadline, candidate=candidate, backup_present=token is not None, backup_valid=backup_valid), seen)
                    return self._blocked_result(context, error)
                if candidate.role == CandidateRole.PRIMARY:
                    context = replace(context, primary_c0=c0_result)
                event = self._c0_event(c0_result.status, c0_result.reason)
                allow_alt = backup_valid and deadline.status == DeadlineStatus.OPEN
                context, route = self._route(context, event, self._routing_context(RuntimePhase.C0, deadline, candidate=candidate, backup_present=token is not None, backup_valid=backup_valid, alternative_search_allowed=allow_alt, reason_scope=self._reason_scope(c0_result.reason)), seen)

            elif destination == RuntimePhase.L2:
                if candidate is None:
                    return self._blocked_result(context, "L2_WITHOUT_CANDIDATE")
                phase = PublicCyclePhase.PRIMARY_L2 if candidate.role == CandidateRole.PRIMARY else PublicCyclePhase.ALTERNATIVE_L2
                context = self._advance(context, phase)
                l2_result, error = self._safe_call(self.l2_runtime.evaluate, snapshot, candidate)
                if error:
                    context, route = self._route(context, PublicCycleEvent.STAGE_EXCEPTION, self._routing_context(RuntimePhase.L2, deadline, candidate=candidate, backup_present=token is not None, backup_valid=backup_valid), seen)
                    return self._blocked_result(context, error)
                if candidate.role == CandidateRole.PRIMARY:
                    context = replace(context, primary_l2=l2_result)
                event = self._l2_event(l2_result.status, l2_result.reason)
                if l2_result.status == CertificateStatus.PASS:
                    context, deadline = self._observe(context, "L3_DISCOVERY_ADMISSION")
                allow_alt = backup_valid and deadline.status == DeadlineStatus.OPEN
                context, route = self._route(context, event, self._routing_context(RuntimePhase.L2, deadline, candidate=candidate, backup_present=token is not None, backup_valid=backup_valid, alternative_search_allowed=allow_alt, reason_scope=self._reason_scope(l2_result.reason)), seen)

            elif destination == RuntimePhase.L3:
                if candidate is None or l2_result is None:
                    return self._blocked_result(context, "L3_WITHOUT_MATCHING_L2")
                phase = PublicCyclePhase.PRIMARY_L3 if candidate.role == CandidateRole.PRIMARY else PublicCyclePhase.ALTERNATIVE_L3
                context = self._advance(context, phase)
                l3_result, error = self._safe_call(self.l3_runtime.evaluate, snapshot, candidate, l2_result)
                if error:
                    context, route = self._route(context, PublicCycleEvent.STAGE_EXCEPTION, self._routing_context(RuntimePhase.L3, deadline, candidate=candidate, backup_present=token is not None, backup_valid=backup_valid), seen)
                    return self._blocked_result(context, error)
                if candidate.role == CandidateRole.PRIMARY:
                    context = replace(context, primary_l3=l3_result)
                if l3_result.status == CertificateStatus.PASS:
                    certified_candidate = candidate
                event = self._l3_event(l3_result.status, l3_result.reason)
                allow_alt = backup_valid and deadline.status == DeadlineStatus.OPEN
                context, route = self._route(context, event, self._routing_context(RuntimePhase.L3, deadline, candidate=candidate, backup_present=token is not None, backup_valid=backup_valid, alternative_search_allowed=allow_alt, navigation_ready=l3_result.status == CertificateStatus.PASS, reason_scope=self._reason_scope(l3_result.reason)), seen)

            elif destination == RuntimePhase.ALT_SEARCH:
                context = self._advance(context, PublicCyclePhase.ALTERNATIVE_ELIGIBILITY)
                context, deadline = self._observe(context, "ALTERNATIVE_SOURCE_QUERY_ADMISSION")
                if deadline.status != DeadlineStatus.OPEN:
                    candidate = None
                    context, route = self._route(context, PublicCycleEvent.DEADLINE_GUARD, self._routing_context(RuntimePhase.ALT_SEARCH, deadline, backup_present=token is not None, backup_valid=backup_valid), seen)
                else:
                    context = self._advance(context, PublicCyclePhase.ALTERNATIVE_SOURCE_QUERY)
                    if alternative_candidates is None:
                        inventory, error = self._safe_call(self.alternative_provider.enumerate, snapshot)
                        if error:
                            context, route = self._route(context, PublicCycleEvent.STAGE_EXCEPTION, self._routing_context(RuntimePhase.ALT_SEARCH, deadline, backup_present=token is not None, backup_valid=backup_valid), seen)
                            return self._blocked_result(context, error)
                        alternative_candidates = inventory.candidates if inventory.status == "ALT_AVAILABLE" else ()
                    if alternative_index < len(alternative_candidates):
                        candidate = alternative_candidates[alternative_index]
                        alternative_index += 1
                        binding = self.l1_runtime.bind_attempt(l1_value, candidate, attempt_index)
                        attempt_index += 1
                        context = replace(context, alternative_attempts=context.alternative_attempts + (candidate.identity,))
                        context, route = self._route(context, PublicCycleEvent.ALT_AVAILABLE, self._routing_context(RuntimePhase.ALT_SEARCH, deadline, candidate=candidate, backup_present=token is not None, backup_valid=backup_valid), seen)
                    else:
                        candidate = None
                        context, route = self._route(context, PublicCycleEvent.ALT_EXHAUSTED, self._routing_context(RuntimePhase.ALT_SEARCH, deadline, backup_present=token is not None, backup_valid=backup_valid), seen)

            elif destination == RuntimePhase.ARBITRATION:
                context = self._advance(context, PublicCyclePhase.BACKUP_VALIDATION)
                context = self._advance(context, PublicCyclePhase.ARBITRATION)
                context, deadline = self._observe(context, "FINAL_COMMIT_GUARD")
                navigation_timely = certified_candidate is not None and l3_result is not None and deadline.status == DeadlineStatus.OPEN
                routing_candidate = certified_candidate if navigation_timely else None
                arbitration_context = self._routing_context(
                    RuntimePhase.ARBITRATION,
                    deadline,
                    candidate=routing_candidate,
                    backup_present=token is not None,
                    backup_valid=backup_valid,
                    navigation_ready=navigation_timely,
                    terminal_evaluated=terminal_result is not None,
                    terminal_ready=terminal_result is not None and terminal_result.status == CertificateStatus.PASS and terminal_result.eligible,
                )
                context, route = self._route(context, PublicCycleEvent.ARBITRATE, arbitration_context, seen)
                if route.status != RouteResolutionStatus.RESOLVED:
                    return self._blocked_result(context, route.reason)
                if route.destination_phase == RuntimePhase.TERMINAL_EVALUATION:
                    continue
                decision = self.supervisor.arbitrate(snapshot, routing_candidate, l3_result if routing_candidate is not None else None, backup_action, backup_valid, terminal_result, deadline)
                if decision.rule_id != route.rule_id:
                    return self._blocked_result(context, "ROUTING_ARBITRATION_IDENTITY_MISMATCH")
                context = replace(context, final_supervisor_decision=decision)
                if route.destination_phase == RuntimePhase.BACKUP_EXECUTION:
                    context, route = self._route(context, PublicCycleEvent.EXECUTE_RETAINED_BACKUP, self._routing_context(RuntimePhase.BACKUP_EXECUTION, deadline, backup_present=token is not None, backup_valid=backup_valid), seen)
                elif route.destination_phase == RuntimePhase.ASSURANCE_BOUNDARY:
                    return self._commit_or_boundary(context, snapshot, decision, boundary=True)

            elif destination == RuntimePhase.TERMINAL_EVALUATION:
                context = self._advance(context, PublicCyclePhase.TERMINAL_EVALUATION)
                context, deadline = self._observe(context, "TERMINAL_EVALUATION_ADMISSION")
                terminal_result, error = self._safe_call(self.terminal_runtime.evaluate, snapshot, True, cycle_context.expected_terminal_ref)
                if error:
                    context, route = self._route(context, PublicCycleEvent.STAGE_EXCEPTION, self._routing_context(RuntimePhase.TERMINAL_EVALUATION, deadline, backup_present=token is not None, backup_valid=backup_valid, terminal_evaluated=True), seen)
                    return self._blocked_result(context, error)
                context = replace(context, terminal_result=terminal_result)
                terminal_event = self._terminal_event(terminal_result.status, terminal_result.eligible)
                context, route = self._route(context, terminal_event, self._routing_context(RuntimePhase.TERMINAL_EVALUATION, deadline, backup_present=token is not None, backup_valid=backup_valid, terminal_evaluated=True, terminal_ready=terminal_result.status == CertificateStatus.PASS and terminal_result.eligible), seen)
                if route.status == RouteResolutionStatus.RESOLVED and route.destination_phase in {RuntimePhase.COMMIT, RuntimePhase.ASSURANCE_BOUNDARY}:
                    decision = self.supervisor.arbitrate(snapshot, None, None, backup_action, backup_valid, terminal_result, deadline)
                    expected_rule = "ARB_TERMINAL" if route.destination_phase == RuntimePhase.COMMIT else "ARB_BOUNDARY"
                    if decision.rule_id != expected_rule:
                        return self._blocked_result(context, "TERMINAL_ARBITRATION_IDENTITY_MISMATCH")
                    context = replace(context, final_supervisor_decision=decision)
                    if route.destination_phase == RuntimePhase.ASSURANCE_BOUNDARY:
                        return self._commit_or_boundary(context, snapshot, decision, boundary=True)

            elif destination == RuntimePhase.COMMIT:
                decision = context.final_supervisor_decision
                if decision is None:
                    return self._blocked_result(context, "COMMIT_WITHOUT_SUPERVISOR_DECISION")
                return self._commit_or_boundary(context, snapshot, decision, boundary=False)

            elif destination == RuntimePhase.ASSURANCE_BOUNDARY:
                decision = context.final_supervisor_decision
                if decision is None:
                    decision = self.supervisor.arbitrate(snapshot, None, None, backup_action, backup_valid, terminal_result, deadline)
                    context = replace(context, final_supervisor_decision=decision)
                return self._commit_or_boundary(context, snapshot, decision, boundary=True)

            else:
                return self._blocked_result(context, "UNSUPPORTED_ROUTED_DESTINATION")

            if route.status != RouteResolutionStatus.RESOLVED:
                return self._blocked_result(context, route.reason)

    def _commit_or_boundary(self, context: ActiveCycleContext, snapshot: RuntimeStateSnapshot, decision, boundary: bool) -> ActiveCycleResult:
        phase = PublicCyclePhase.ASSURANCE_BOUNDARY if boundary else PublicCyclePhase.COMMIT
        context = self._advance(context, phase)
        before = len(self.active_runner.trace_writer.records)
        receipt = self.active_runner.commit_active_decision(snapshot, decision)
        after = len(self.active_runner.trace_writer.records)
        if after != before + 1:
            self._session = replace(self._require_session(), status=TrialSessionStatus.BLOCKED)
            raise PublicCycleStateError("TRACE_OUTCOME_CARDINALITY_VIOLATION")
        context = replace(context, commit_receipt=receipt, trace_ref=self._trace_ref())
        context = self._advance(context, PublicCyclePhase.TRACE_APPEND)
        committed = receipt is not None and receipt.committed
        if committed:
            context = self._advance(context, PublicCyclePhase.CYCLE_COMPLETE)
            self._session = replace(self._require_session(), next_cycle_index=snapshot.cycle_index + 1)
        else:
            self._session = replace(self._require_session(), status=TrialSessionStatus.BLOCKED)
        reason = decision.reason if receipt is None or receipt.committed else receipt.reason
        return self._result(context, decision, committed, boundary or not decision.allows_commit, reason)

    def finalize_trial(self):
        session = self._require_session()
        if session.status == TrialSessionStatus.FINALIZED:
            raise PublicCycleStateError("TRIAL_ALREADY_FINALIZED")
        lock = self.active_runner.finalize_trace()
        self._session = replace(session, status=TrialSessionStatus.FINALIZED)
        return lock

    @staticmethod
    def _reason_scope(reason: str) -> str:
        value = reason.upper()
        if any(token in value for token in ("MAP", "AUTHORITY", "IDENTITY", "ALIGNMENT")):
            return "GLOBAL_AUTHORITY_OR_EVIDENCE"
        if any(token in value for token in ("EXCEPTION", "HEALTH", "NONFINITE")):
            return "INFRASTRUCTURE_HEALTH"
        return "CANDIDATE_LOCAL_COMPUTATION"

    @classmethod
    def _l1_event(cls, status: CertificateStatus, reason: str) -> PublicCycleEvent:
        if status == CertificateStatus.PASS:
            return PublicCycleEvent.L1_PASS
        if status == CertificateStatus.FAIL:
            return PublicCycleEvent.L1_FAIL
        scope = cls._reason_scope(reason)
        if scope == "GLOBAL_AUTHORITY_OR_EVIDENCE":
            return PublicCycleEvent.L1_UNKNOWN_GLOBAL
        if scope == "INFRASTRUCTURE_HEALTH":
            return PublicCycleEvent.L1_UNKNOWN_HEALTH
        return PublicCycleEvent.L1_UNKNOWN_UNRESOLVED

    @classmethod
    def _c0_event(cls, status: CertificateStatus, reason: str) -> PublicCycleEvent:
        if status == CertificateStatus.PASS:
            return PublicCycleEvent.C0_PASS
        if status == CertificateStatus.FAIL:
            return PublicCycleEvent.C0_FAIL_LOCAL
        return PublicCycleEvent.C0_UNKNOWN_GLOBAL if cls._reason_scope(reason) == "GLOBAL_AUTHORITY_OR_EVIDENCE" else PublicCycleEvent.C0_UNKNOWN_LOCAL

    @classmethod
    def _l2_event(cls, status: CertificateStatus, reason: str) -> PublicCycleEvent:
        if status == CertificateStatus.PASS:
            return PublicCycleEvent.L2_PASS
        if status == CertificateStatus.FAIL:
            return PublicCycleEvent.L2_FAIL
        return PublicCycleEvent.L2_UNKNOWN_GLOBAL if cls._reason_scope(reason) == "GLOBAL_AUTHORITY_OR_EVIDENCE" else PublicCycleEvent.L2_UNKNOWN_LOCAL

    @classmethod
    def _l3_event(cls, status: CertificateStatus, reason: str) -> PublicCycleEvent:
        if status == CertificateStatus.PASS:
            return PublicCycleEvent.L3_WITNESS_FOUND
        if status == CertificateStatus.FAIL:
            return PublicCycleEvent.L3_WITNESS_ABSENT
        return PublicCycleEvent.L3_UNKNOWN_GLOBAL if cls._reason_scope(reason) == "GLOBAL_AUTHORITY_OR_EVIDENCE" else PublicCycleEvent.L3_UNKNOWN_LOCAL

    @staticmethod
    def _terminal_event(status: CertificateStatus, eligible: bool) -> PublicCycleEvent:
        if status == CertificateStatus.PASS and eligible:
            return PublicCycleEvent.TERMINAL_MEMBER_ELIGIBLE
        if status == CertificateStatus.UNKNOWN:
            return PublicCycleEvent.TERMINAL_UNKNOWN
        return PublicCycleEvent.TERMINAL_MEMBER_NOT_ELIGIBLE
