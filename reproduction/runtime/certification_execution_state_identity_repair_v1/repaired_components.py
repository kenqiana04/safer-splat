"""Additive repaired runtime components; frozen policy owners remain unchanged."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Callable

from reproduction.runtime.active_runtime_assurance_v2.authority_registry import AuthorityRegistry
from reproduction.runtime.active_runtime_assurance_v2.backup_token_store import BackupTokenStore
from reproduction.runtime.active_runtime_assurance_v2.l3_runtime import L3Runtime
from reproduction.runtime.active_runtime_assurance_v2.plant_commit import PlantCommitAdapter
from reproduction.runtime.active_runtime_assurance_v2.runtime_errors import CommitAuthorityViolation, TokenLifecycleViolation
from reproduction.runtime.active_runtime_assurance_v2.runtime_types import (
    AttemptIdentity,
    BundleIdentity,
    Candidate,
    CandidateIdentity,
    CertificateStatus,
    EvidenceResult,
    L1AttemptBinding,
    L1CycleResult,
    L2Result,
    L3Result,
    RuntimeStateSnapshot,
    StateIdentity,
    TokenLifecycle,
    canonical_sha256,
)

from .canonical_transition import CanonicalExecutionTransition, NEUTRAL_ACTION
from .evidence import (
    CERT_EXEC_STATE_IDENTITY_MATCH,
    CERT_EXEC_STATE_IDENTITY_MISMATCH,
    CanonicalIdentityLedger,
)


class CanonicalL1Runtime:
    """Once-per-cycle L1 using the execution-equivalent immediate endpoint."""

    def __init__(self, segment_backend: Callable[..., EvidenceResult], registry: AuthorityRegistry, transition: CanonicalExecutionTransition, ledger: CanonicalIdentityLedger) -> None:
        self._backend = segment_backend
        self._registry = registry
        self._transition = transition
        self._ledger = ledger
        self._cache: dict[tuple[str, int], L1CycleResult] = {}

    def evaluate_cycle(self, snapshot: RuntimeStateSnapshot) -> L1CycleResult:
        key = (snapshot.identity.value, snapshot.cycle_index)
        if key in self._cache:
            return self._cache[key]
        start = snapshot.position
        end = self._transition.immediate_position(snapshot.state, snapshot.dt)
        segment_id = self._transition.segment_identity(
            start, end, snapshot.map_identity,
            self._registry.geometry.certification_effective_radius_m,
            self._registry.geometry.rho_seg_m,
        )
        if snapshot.map_identity != self._registry.map_identity:
            evidence = EvidenceResult(CertificateStatus.UNKNOWN, "MAP_IDENTITY_MISMATCH", "none")
        else:
            try:
                evidence = self._backend(start, end, snapshot.map_identity, self._registry.geometry.certification_effective_radius_m, self._registry.geometry.rho_seg_m)
            except Exception as exc:
                evidence = EvidenceResult(CertificateStatus.UNKNOWN, f"L1_BACKEND_EXCEPTION:{type(exc).__name__}", "none")
        result_id = "l1-cycle:sha256:" + canonical_sha256({"state": snapshot.identity, "segment": segment_id, "evidence": evidence, "transition": self._transition.identity.value})
        result = L1CycleResult(result_id, evidence.status, evidence.reason, snapshot.identity, segment_id, start, end, evidence.evidence_identity)
        self._cache[key] = result
        self._ledger.record(
            snapshot.trial_id,
            snapshot.cycle_index,
            canonical_transition_arithmetic_identity=self._transition.identity.value,
            canonical_pre_state_identity=self._transition.state_identity(snapshot.state),
            canonical_l1_endpoint_identity=self._transition.position_identity(end),
            canonical_l1_segment_identity=segment_id,
            canonical_l1_status=evidence.status.value,
            canonical_l1_reason=evidence.reason,
            canonical_l1_evidence_identity=evidence.evidence_identity,
        )
        return result

    def bind_attempt(self, cycle_result: L1CycleResult, candidate: Candidate, attempt_index: int) -> L1AttemptBinding:
        material = {"cycle_result": cycle_result.identity, "candidate": candidate.identity, "state": cycle_result.state_identity, "segment": cycle_result.segment_identity, "attempt_index": int(attempt_index)}
        return L1AttemptBinding(AttemptIdentity("attempt:sha256:" + canonical_sha256(material)), cycle_result.identity, candidate.identity, cycle_result.state_identity, cycle_result.segment_identity)


class CanonicalL2Runtime:
    """L2/H1 using sequential canonical execution transitions."""

    def __init__(self, segment_backend: Callable[..., EvidenceResult], registry: AuthorityRegistry, transition: CanonicalExecutionTransition, ledger: CanonicalIdentityLedger) -> None:
        self._backend = segment_backend
        self._registry = registry
        self._transition = transition
        self._ledger = ledger

    def evaluate(self, snapshot: RuntimeStateSnapshot, candidate: Candidate) -> L2Result:
        first, second = self._transition.two_step(snapshot.state, candidate.vector, snapshot.dt, NEUTRAL_ACTION)
        p_k1 = first.post_state[:3]
        p_k2 = second.post_state[:3]
        segment_id = self._transition.segment_identity(
            p_k1, p_k2, snapshot.map_identity,
            self._registry.geometry.certification_effective_radius_m,
            self._registry.geometry.rho_seg_m,
        )
        if candidate.provenance.state_identity != snapshot.identity or snapshot.map_identity != self._registry.map_identity:
            evidence = EvidenceResult(CertificateStatus.UNKNOWN, "L2_AUTHORITY_OR_ALIGNMENT_MISMATCH", "none")
        else:
            try:
                evidence = self._backend(p_k1, p_k2, snapshot.map_identity, self._registry.geometry.certification_effective_radius_m, self._registry.geometry.rho_seg_m)
            except Exception as exc:
                evidence = EvidenceResult(CertificateStatus.UNKNOWN, f"L2_BACKEND_EXCEPTION:{type(exc).__name__}", "none")
        result = L2Result.create(evidence.status, evidence.reason, candidate.identity, p_k1, p_k2, segment_id, evidence.evidence_identity)
        self._ledger.record(
            snapshot.trial_id,
            snapshot.cycle_index,
            canonical_l2_x_k1_identity=first.post_state_identity,
            canonical_l2_p_k1_identity=self._transition.position_identity(p_k1),
            canonical_l2_x_k2_identity=second.post_state_identity,
            canonical_l2_p_k2_identity=self._transition.position_identity(p_k2),
            canonical_l2_segment_identity=segment_id,
            canonical_l2_status=evidence.status.value,
            canonical_l2_reason=evidence.reason,
            canonical_l2_evidence_identity=evidence.evidence_identity,
            canonical_selected_candidate_identity=candidate.identity.value,
        )
        return result


class CanonicalPositionFirstForwardEulerDoubleIntegrator:
    """Certifier adapter delegating authoritative discrete propagation to T_exec."""

    identity = "POSITION_FIRST_FORWARD_EULER_DOUBLE_INTEGRATOR_V1_CANONICAL_EXECUTION_IDENTITY_V1"

    def __init__(self, bounds: Any, transition: CanonicalExecutionTransition) -> None:
        if not bounds.valid:
            raise ValueError("INVALID_ACTUATOR_BOUNDS")
        self.bounds = bounds
        self.canonical_transition = transition

    def transition(self, state: Any, control: Any) -> Any:
        if not state.finite or not control.finite:
            raise ValueError("NONFINITE_DYNAMICS_INPUT")
        vector = (*state.position, *state.velocity)
        post = self.canonical_transition.transition(vector, control.acceleration, self.bounds.dt)
        return type(state)(post[:3], post[3:], float(state.timestamp + self.bounds.dt), state.map_snapshot_id)

    def interval_state(self, state: Any, control: Any, tau: float) -> Any:
        if tau < 0.0 or tau > self.bounds.dt:
            raise ValueError("TAU_OUT_OF_INTERVAL")
        vector = (*state.position, *state.velocity)
        post = self.canonical_transition.transition(vector, control.acceleration, float(tau))
        return type(state)(post[:3], post[3:], float(state.timestamp + tau), state.map_snapshot_id)

    def segment_endpoints(self, state: Any) -> tuple[tuple[float, float, float], tuple[float, float, float]]:
        vector = (*state.position, *state.velocity)
        return state.position, self.canonical_transition.immediate_position(vector, self.bounds.dt)


@dataclass(frozen=True)
class CanonicalWitnessMaterial:
    status: CertificateStatus
    tail_actions: tuple[tuple[tuple[float, float, float], str], ...]
    terminal_ref: str | None
    reason: str
    predicted_states: tuple[tuple[float, ...], ...]
    segment_identities: tuple[str, ...]


@dataclass(frozen=True)
class CanonicalPreparedBackupBundle:
    identity: BundleIdentity
    source_candidate_identity: CandidateIdentity
    tail_actions: tuple[tuple[tuple[float, float, float], str], ...]
    state_identity: StateIdentity
    map_identity: str
    geometry_identity: str
    actuator_identity: str
    dynamics_identity: str
    terminal_evidence_reference: str | None
    expected_activation_state_identity: StateIdentity
    canonical_transition_identity: str
    dtype_device_identity: str
    predicted_state_identities: tuple[str, ...]
    action_identity_sequence: tuple[str, ...]
    certified_segment_identities: tuple[str, ...]
    lifecycle: str = TokenLifecycle.PREPARED_UNCOMMITTED.value


class CanonicalL3Runtime(L3Runtime):
    def __init__(self, witness_builder: Callable[..., CanonicalWitnessMaterial], registry: AuthorityRegistry, transition: CanonicalExecutionTransition, ledger: CanonicalIdentityLedger) -> None:
        self._builder = witness_builder
        self._registry = registry
        self._transition = transition
        self._ledger = ledger

    def evaluate(self, snapshot: RuntimeStateSnapshot, candidate: Candidate, l2_result: L2Result) -> L3Result:
        if l2_result.status != CertificateStatus.PASS or l2_result.candidate_identity != candidate.identity:
            return L3Result(CertificateStatus.UNKNOWN, "L3_NOT_REACHED_WITHOUT_MATCHING_L2_PASS", candidate.identity, None, None)
        try:
            material = self._builder(snapshot, candidate)
        except Exception as exc:
            return L3Result(CertificateStatus.UNKNOWN, f"L3_BACKEND_EXCEPTION:{type(exc).__name__}", candidate.identity, None, None)
        evidence_identity = "l3-evidence:sha256:" + canonical_sha256(material)
        if material.status != CertificateStatus.PASS:
            return L3Result(material.status, material.reason, candidate.identity, None, evidence_identity)
        activation_vector = self._transition.transition(snapshot.state, candidate.vector, snapshot.dt)
        expected_snapshot = RuntimeStateSnapshot.create(snapshot.trial_id, snapshot.cycle_index + 1, activation_vector, snapshot.goal, snapshot.map_identity, snapshot.dt)
        predicted_ids = tuple(self._transition.state_identity(state) for state in material.predicted_states)
        actions = tuple((tuple(float(v) for v in vector), str(action_id)) for vector, action_id in material.tail_actions)
        action_ids = (candidate.identity.value,) + tuple(action_id for _, action_id in actions)
        bundle_material = {
            "candidate": candidate.identity,
            "state": snapshot.identity,
            "map": snapshot.map_identity,
            "tail_actions": actions,
            "expected_activation": expected_snapshot.identity,
            "transition": self._transition.identity,
            "predicted_states": predicted_ids,
            "segments": material.segment_identities,
            "terminal_ref": material.terminal_ref,
        }
        bundle = CanonicalPreparedBackupBundle(
            BundleIdentity("bundle:sha256:" + canonical_sha256(bundle_material)),
            candidate.identity,
            actions,
            snapshot.identity,
            snapshot.map_identity,
            self._registry.geometry.identity.value,
            self._registry.actuator.identity.value,
            self._registry.dynamics.identity.value,
            material.terminal_ref,
            expected_snapshot.identity,
            self._transition.identity.value,
            self._transition.identity.device_backend,
            predicted_ids,
            action_ids,
            material.segment_identities,
        )
        self._ledger.record(
            snapshot.trial_id,
            snapshot.cycle_index,
            canonical_l3_bundle_identity=bundle.identity.value,
            canonical_l3_predicted_chain_identity="canonical-chain:sha256:" + canonical_sha256(predicted_ids),
            canonical_l3_expected_activation_state_identity=expected_snapshot.identity.value,
        )
        return L3Result(CertificateStatus.PASS, material.reason, candidate.identity, bundle, evidence_identity)  # type: ignore[arg-type]


class CanonicalStartAdmission:
    def __init__(self, delegate: Any, transition: CanonicalExecutionTransition, ledger: CanonicalIdentityLedger) -> None:
        self._delegate = delegate
        self._transition = transition
        self._ledger = ledger

    def evaluate(self, snapshot: RuntimeStateSnapshot):
        result = self._delegate.evaluate(snapshot)
        self._ledger.record(
            snapshot.trial_id,
            snapshot.cycle_index,
            canonical_start_state_identity=self._transition.state_identity(snapshot.state),
            canonical_start_arithmetic_identity=self._transition.identity.value,
        )
        return result


class CanonicalBackupTokenStore(BackupTokenStore):
    def __init__(self, transition: CanonicalExecutionTransition, ledger: CanonicalIdentityLedger) -> None:
        super().__init__()
        self._transition = transition
        self._ledger = ledger
        self._validated_snapshots: dict[str, RuntimeStateSnapshot] = {}

    def validate(self, snapshot: RuntimeStateSnapshot, registry: AuthorityRegistry) -> EvidenceResult:
        result = super().validate(snapshot, registry)
        if result.status == CertificateStatus.PASS:
            token = self.current()
            if token is None or token.expected_state_identity != snapshot.identity:
                return EvidenceResult(CertificateStatus.UNKNOWN, CERT_EXEC_STATE_IDENTITY_MISMATCH, "none")
            self._validated_snapshots[snapshot.identity.value] = snapshot
            self._ledger.record(snapshot.trial_id, snapshot.cycle_index, canonical_backup_state_identity_status=CERT_EXEC_STATE_IDENTITY_MATCH)
        return result

    def activate_after_navigation_commit(self, receipt: Any, bundle_identity: BundleIdentity):
        bundle = self._prepared.get(bundle_identity.value)
        if bundle is None:
            raise TokenLifecycleViolation("PREPARED_BUNDLE_NOT_FOUND")
        expected = getattr(bundle, "expected_activation_state_identity", None)
        if receipt.post_state is None or expected is None or receipt.post_state.identity != expected:
            raise TokenLifecycleViolation(CERT_EXEC_STATE_IDENTITY_MISMATCH)
        return super().activate_after_navigation_commit(receipt, bundle_identity)

    def consume_after_backup_commit(self, receipt: Any):
        token = self.current()
        if token is None or token.current_action is None:
            raise TokenLifecycleViolation("NO_ACTIVE_BACKUP_TOKEN")
        snapshot = self._validated_snapshots.get(token.expected_state_identity.value)
        if snapshot is None:
            raise TokenLifecycleViolation(CERT_EXEC_STATE_IDENTITY_MISMATCH)
        expected_vector = self._transition.transition(snapshot.state, token.current_action[0], snapshot.dt)
        expected = RuntimeStateSnapshot.create(snapshot.trial_id, snapshot.cycle_index + 1, expected_vector, snapshot.goal, snapshot.map_identity, snapshot.dt)
        if receipt.post_state is None or receipt.post_state.identity != expected.identity:
            raise TokenLifecycleViolation(CERT_EXEC_STATE_IDENTITY_MISMATCH)
        return super().consume_after_backup_commit(receipt)


class ContinuityGuardedPlantCommitAdapter(PlantCommitAdapter):
    """Pre-commit bundle guard plus post-commit bitwise evidence."""

    def __init__(self, registry: AuthorityRegistry, transition: CanonicalExecutionTransition, ledger: CanonicalIdentityLedger) -> None:
        super().__init__(registry, transition.transition)
        self.canonical_transition = transition
        self._ledger = ledger

    def commit(self, decision: Any, snapshot: RuntimeStateSnapshot, selected_action: Any):
        expected_vector = self.canonical_transition.transition(snapshot.state, selected_action.vector, snapshot.dt)
        expected_snapshot = RuntimeStateSnapshot.create(snapshot.trial_id, snapshot.cycle_index + 1, expected_vector, snapshot.goal, snapshot.map_identity, snapshot.dt)
        bundle = getattr(decision, "prepared_bundle", None)
        expected_bundle_state = getattr(bundle, "expected_activation_state_identity", expected_snapshot.identity)
        if expected_bundle_state != expected_snapshot.identity:
            self._ledger.record(snapshot.trial_id, snapshot.cycle_index, cert_exec_state_identity_status=CERT_EXEC_STATE_IDENTITY_MISMATCH)
            raise CommitAuthorityViolation(CERT_EXEC_STATE_IDENTITY_MISMATCH)
        receipt = super().commit(decision, snapshot, selected_action)
        if receipt.committed:
            if receipt.post_state is None or not self.canonical_transition.bitwise_equal(expected_vector, receipt.post_state.state):
                self._ledger.record(snapshot.trial_id, snapshot.cycle_index, cert_exec_state_identity_status=CERT_EXEC_STATE_IDENTITY_MISMATCH)
                raise CommitAuthorityViolation(CERT_EXEC_STATE_IDENTITY_MISMATCH)
            self._ledger.record(
                snapshot.trial_id,
                snapshot.cycle_index,
                canonical_actual_post_state_identity=self.canonical_transition.state_identity(receipt.post_state.state),
                cert_exec_state_identity_status=CERT_EXEC_STATE_IDENTITY_MATCH,
            )
        return receipt
