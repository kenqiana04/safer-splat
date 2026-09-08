"""Immutable typed objects and content identities for Active Runtime V2."""

from __future__ import annotations

import dataclasses
import hashlib
import json
import math
import struct
from dataclasses import dataclass
from enum import Enum
from typing import Any, Mapping


Vector3 = tuple[float, float, float]
Vector6 = tuple[float, float, float, float, float, float]


class CertificateStatus(str, Enum):
    PASS = "PASS"
    FAIL = "FAIL"
    UNKNOWN = "UNKNOWN"


class ActionRole(str, Enum):
    PRIMARY_NAVIGATION = "PRIMARY_NAVIGATION"
    ALTERNATIVE_NAVIGATION = "ALTERNATIVE_NAVIGATION"
    RETAINED_BACKUP = "RETAINED_BACKUP"
    CERTIFIED_TERMINAL = "CERTIFIED_TERMINAL"
    ASSURANCE_BOUNDARY_NO_ACTION = "ASSURANCE_BOUNDARY_NO_ACTION"


class CandidateRole(str, Enum):
    PRIMARY = "PRIMARY"
    ALTERNATIVE = "ALTERNATIVE"


class RuntimeMode(str, Enum):
    REFERENCE_BASELINE = "REFERENCE_BASELINE"
    ACTIVE_HARNESS_BYPASS = "ACTIVE_HARNESS_BYPASS"
    ACTIVE_RUNTIME_ON = "ACTIVE_RUNTIME_ON"


class DeadlineStatus(str, Enum):
    OPEN = "OPEN"
    WARNING = "WARNING"
    EXPIRED = "EXPIRED"


class TokenLifecycle(str, Enum):
    PREPARED_UNCOMMITTED = "PREPARED_UNCOMMITTED"
    ACTIVE = "ACTIVE"
    INVALID = "INVALID"
    EXHAUSTED = "EXHAUSTED"
    RETIRED_SUPERSEDED = "RETIRED_SUPERSEDED"
    ABORTED_PREPARED = "ABORTED_PREPARED"


class CommitTransactionState(str, Enum):
    PREPARED = "PREPARED"
    PLANT_ATTEMPTED = "PLANT_ATTEMPTED"
    PLANT_NOT_COMMITTED = "PLANT_NOT_COMMITTED"
    PLANT_OUTCOME_UNRESOLVED = "PLANT_OUTCOME_UNRESOLVED"
    COMMITTED = "COMMITTED"
    TOKEN_APPLIED = "TOKEN_APPLIED"
    TRACE_RECORDED = "TRACE_RECORDED"
    COMPLETE = "COMPLETE"
    EVIDENCE_INCOMPLETE = "EVIDENCE_INCOMPLETE"
    RECOVERY_REQUIRED = "RECOVERY_REQUIRED"


class PlantOutcome(str, Enum):
    NOT_ATTEMPTED = "NOT_ATTEMPTED"
    NOT_COMMITTED = "NOT_COMMITTED"
    COMMITTED = "COMMITTED"
    UNRESOLVED = "UNRESOLVED"


class TokenMutationStatus(str, Enum):
    NOT_APPLICABLE = "NOT_APPLICABLE"
    UNCHANGED = "UNCHANGED"
    APPLIED = "APPLIED"
    INCOMPLETE = "INCOMPLETE"


class TraceStatus(str, Enum):
    NOT_ATTEMPTED = "NOT_ATTEMPTED"
    RECORDED = "RECORDED"
    INCOMPLETE = "INCOMPLETE"
    FINALIZATION_INCOMPLETE = "FINALIZATION_INCOMPLETE"
    FINALIZED = "FINALIZED"


class EvidenceStatus(str, Enum):
    COMPLETE = "COMPLETE"
    NO_ACTION_COMPLETE = "NO_ACTION_COMPLETE"
    ABORTED_BEFORE_PLANT = "ABORTED_BEFORE_PLANT"
    PLANT_NOT_COMMITTED = "PLANT_NOT_COMMITTED"
    PLANT_OUTCOME_UNRESOLVED = "PLANT_OUTCOME_UNRESOLVED"
    COMMITTED_TOKEN_INCOMPLETE = "COMMITTED_TOKEN_INCOMPLETE"
    COMMITTED_TRACE_INCOMPLETE = "COMMITTED_TRACE_INCOMPLETE"
    NO_ACTION_TRACE_INCOMPLETE = "NO_ACTION_TRACE_INCOMPLETE"
    FINALIZATION_INCOMPLETE = "FINALIZATION_INCOMPLETE"
    RECOVERY_REQUIRED = "RECOVERY_REQUIRED"


class FinalizationStatus(str, Enum):
    FINALIZED = "FINALIZED"
    FINALIZATION_INCOMPLETE = "FINALIZATION_INCOMPLETE"
    RECOVERY_REQUIRED = "RECOVERY_REQUIRED"


class RuntimePhase(str, Enum):
    START_ADMISSION = "START_ADMISSION"
    REPAIR = "REPAIR"
    RUNTIME_CURRENT_ROLE = "RUNTIME_CURRENT_ROLE"
    L1 = "L1"
    PRIMARY_PROPOSAL = "PRIMARY_PROPOSAL"
    C0 = "C0"
    L2 = "L2"
    L3 = "L3"
    ALT_SEARCH = "ALT_SEARCH"
    ARBITRATION = "ARBITRATION"
    BACKUP_EXECUTION = "BACKUP_EXECUTION"
    TERMINAL_EVALUATION = "TERMINAL_EVALUATION"
    COMMIT = "COMMIT"
    ASSURANCE_BOUNDARY = "ASSURANCE_BOUNDARY"


class ReasonScope(str, Enum):
    """Frozen PR #107 reason scopes used as routing evidence."""

    NONE = "NONE"
    CANDIDATE_LOCAL_COMPUTATION = "CANDIDATE_LOCAL_COMPUTATION"
    GLOBAL_AUTHORITY_OR_EVIDENCE = "GLOBAL_AUTHORITY_OR_EVIDENCE"
    INFRASTRUCTURE_HEALTH = "INFRASTRUCTURE_HEALTH"
    UNRESOLVED_SCOPE = "UNRESOLVED_SCOPE"


class StageFailureKind(str, Enum):
    """Failure kinds remain evidence and never grant action authority."""

    STAGE_EXCEPTION = "STAGE_EXCEPTION"
    STAGE_UNKNOWN = "STAGE_UNKNOWN"
    PROVIDER_STATUS_FAILURE = "PROVIDER_STATUS_FAILURE"
    ROUTE_RESOLUTION_FAILURE = "ROUTE_RESOLUTION_FAILURE"
    SERIALIZATION_FAILURE = "SERIALIZATION_FAILURE"
    COMMIT_FAILURE = "COMMIT_FAILURE"


class AlternativeInventoryStatus(str, Enum):
    """Lossless normalization of the unchanged provider status contract."""

    ALT_AVAILABLE = "ALT_AVAILABLE"
    NO_ALTERNATIVE_AVAILABLE = "NO_ALTERNATIVE_AVAILABLE"
    SOURCE_INVALID = "SOURCE_INVALID"
    PROVENANCE_MISSING = "PROVENANCE_MISSING"
    UNRESOLVED_STATUS = "UNRESOLVED_STATUS"


def _canonical(value: Any) -> Any:
    if isinstance(value, Enum):
        return value.value
    if isinstance(value, float):
        return {"__float64_be_hex__": struct.pack(">d", value).hex()}
    if dataclasses.is_dataclass(value):
        return {field.name: _canonical(getattr(value, field.name)) for field in dataclasses.fields(value)}
    if isinstance(value, Mapping):
        return {str(key): _canonical(value[key]) for key in sorted(value, key=str)}
    if isinstance(value, (tuple, list)):
        return [_canonical(item) for item in value]
    if value is None or isinstance(value, (str, int, bool)):
        return value
    raise TypeError(f"unsupported canonical type: {type(value).__name__}")


def canonical_json(value: Any) -> str:
    return json.dumps(_canonical(value), ensure_ascii=False, sort_keys=True, separators=(",", ":"), allow_nan=False)


def canonical_sha256(value: Any) -> str:
    return hashlib.sha256(canonical_json(value).encode("utf-8")).hexdigest()


def _v3(value: Any) -> Vector3:
    result = tuple(float(x) for x in value)
    if len(result) != 3:
        raise ValueError("expected three-vector")
    return result  # type: ignore[return-value]


def _v6(value: Any) -> Vector6:
    result = tuple(float(x) for x in value)
    if len(result) != 6:
        raise ValueError("expected six-vector")
    return result  # type: ignore[return-value]


@dataclass(frozen=True)
class AuthorityIdentity:
    kind: str
    value: str


@dataclass(frozen=True)
class StateIdentity:
    value: str


@dataclass(frozen=True)
class ActionIdentity:
    value: str


@dataclass(frozen=True)
class CandidateIdentity:
    value: str


@dataclass(frozen=True)
class AttemptIdentity:
    value: str


@dataclass(frozen=True)
class BundleIdentity:
    value: str


@dataclass(frozen=True)
class TokenIdentity:
    value: str


@dataclass(frozen=True)
class TraceIdentity:
    value: str


@dataclass(frozen=True)
class RuntimeStateSnapshot:
    trial_id: str
    cycle_index: int
    state: Vector6
    goal: Vector6
    map_identity: str
    dt: float
    identity: StateIdentity

    @property
    def position(self) -> Vector3:
        return self.state[:3]  # type: ignore[return-value]

    @property
    def velocity(self) -> Vector3:
        return self.state[3:]  # type: ignore[return-value]

    @classmethod
    def create(cls, trial_id: str, cycle_index: int, state: Any, goal: Any, map_identity: str, dt: float) -> "RuntimeStateSnapshot":
        state_v, goal_v = _v6(state), _v6(goal)
        material = {"trial_id": str(trial_id), "cycle_index": int(cycle_index), "state": state_v, "goal": goal_v, "map_identity": str(map_identity), "dt": float(dt)}
        return cls(str(trial_id), int(cycle_index), state_v, goal_v, str(map_identity), float(dt), StateIdentity("state:sha256:" + canonical_sha256(material)))


@dataclass(frozen=True)
class CandidateProvenance:
    source_type: str
    controller_identity: str
    creation_timestamp: str
    state_identity: StateIdentity
    map_identity: str
    lawful: bool


@dataclass(frozen=True)
class Candidate:
    identity: CandidateIdentity
    vector: Vector3
    role: CandidateRole
    provenance: CandidateProvenance


def make_candidate(vector: Any, role: CandidateRole, source_type: str, controller_identity: str, snapshot: RuntimeStateSnapshot, creation_timestamp: str | None = None) -> Candidate:
    vec = _v3(vector)
    timestamp = creation_timestamp or f"logical-cycle:{snapshot.cycle_index}"
    provenance = CandidateProvenance(str(source_type), str(controller_identity), timestamp, snapshot.identity, snapshot.map_identity, source_type in {"PRIMARY_NATIVE_CBF_QP", "SOURCE_NATIVE_EXISTING"})
    material = {"vector": vec, "role": role, "provenance": provenance}
    return Candidate(CandidateIdentity("candidate:sha256:" + canonical_sha256(material)), vec, role, provenance)


@dataclass(frozen=True)
class SelectedAction:
    identity: ActionIdentity
    vector: Vector3
    role: ActionRole
    source_identity: str
    authority_references: tuple[str, ...] = ()


def make_action(vector: Any, role: ActionRole, source_identity: str, authority_references: tuple[str, ...] = ()) -> SelectedAction:
    vec = _v3(vector)
    material = {"vector": vec, "role": role, "source_identity": str(source_identity), "authority_references": tuple(authority_references)}
    return SelectedAction(ActionIdentity("action:sha256:" + canonical_sha256(material)), vec, role, str(source_identity), tuple(authority_references))


@dataclass(frozen=True)
class EvidenceResult:
    status: CertificateStatus
    reason: str
    evidence_identity: str


@dataclass(frozen=True)
class StartAdmissionResult:
    status: CertificateStatus
    reason: str
    state_identity: StateIdentity
    evidence_identity: str
    repair_available: bool


@dataclass(frozen=True)
class R0Diagnostic:
    state_identity: StateIdentity
    reason: str
    hard_gate: bool = False
    selection_authority: bool = False
    commit_authority: bool = False


@dataclass(frozen=True)
class ProposalResult:
    status: CertificateStatus
    reason: str
    candidate: Candidate | None
    desired_reference: Vector3


@dataclass(frozen=True)
class L1CycleResult:
    identity: str
    status: CertificateStatus
    reason: str
    state_identity: StateIdentity
    segment_identity: str
    segment_start: Vector3
    segment_end: Vector3
    evidence_identity: str


@dataclass(frozen=True)
class L1AttemptBinding:
    identity: AttemptIdentity
    cycle_result_identity: str
    candidate_identity: CandidateIdentity
    state_identity: StateIdentity
    segment_identity: str


@dataclass(frozen=True)
class C0Result:
    status: CertificateStatus
    reason: str
    candidate_identity: CandidateIdentity
    candidate_vector: Vector3
    actuator_authority_identity: str


@dataclass(frozen=True)
class L2Result:
    identity: str
    status: CertificateStatus
    reason: str
    candidate_identity: CandidateIdentity
    p_k1: Vector3
    p_k2: Vector3
    segment_identity: str
    evidence_identity: str

    @classmethod
    def create(cls, status: CertificateStatus, reason: str, candidate_identity: CandidateIdentity, p_k1: Any, p_k2: Any, segment_identity: str, evidence_identity: str) -> "L2Result":
        a, b = _v3(p_k1), _v3(p_k2)
        material = {"status": status, "reason": reason, "candidate": candidate_identity, "p_k1": a, "p_k2": b, "segment": segment_identity, "evidence": evidence_identity}
        return cls("l2:sha256:" + canonical_sha256(material), status, str(reason), candidate_identity, a, b, str(segment_identity), str(evidence_identity))


@dataclass(frozen=True)
class PreparedBackupBundle:
    identity: BundleIdentity
    source_candidate_identity: CandidateIdentity
    tail_actions: tuple[tuple[Vector3, str], ...]
    state_identity: StateIdentity
    map_identity: str
    geometry_identity: str
    actuator_identity: str
    dynamics_identity: str
    terminal_evidence_reference: str | None
    lifecycle: str = TokenLifecycle.PREPARED_UNCOMMITTED.value

    @classmethod
    def create(cls, candidate: Candidate, snapshot: RuntimeStateSnapshot, tail_actions: Any, geometry_identity: str, actuator_identity: str, dynamics_identity: str, terminal_ref: str | None) -> "PreparedBackupBundle":
        actions = tuple((_v3(vector), str(action_id)) for vector, action_id in tail_actions)
        material = {"candidate": candidate.identity, "state": snapshot.identity, "cycle": snapshot.cycle_index, "map": snapshot.map_identity, "actions": actions, "geometry": geometry_identity, "actuator": actuator_identity, "dynamics": dynamics_identity, "terminal_ref": terminal_ref}
        return cls(BundleIdentity("bundle:sha256:" + canonical_sha256(material)), candidate.identity, actions, snapshot.identity, snapshot.map_identity, geometry_identity, actuator_identity, dynamics_identity, terminal_ref)


@dataclass(frozen=True)
class L3Result:
    status: CertificateStatus
    reason: str
    candidate_identity: CandidateIdentity
    prepared_bundle: PreparedBackupBundle | None
    evidence_identity: str | None


@dataclass(frozen=True)
class RetainedBackupToken:
    identity: TokenIdentity
    bundle: PreparedBackupBundle
    lifecycle: TokenLifecycle
    activation_cycle: int
    cursor: int
    expected_state_identity: StateIdentity
    expected_time_index: int
    invalidation_reason: str | None = None

    @property
    def current_action(self) -> tuple[Vector3, str] | None:
        if self.lifecycle != TokenLifecycle.ACTIVE or self.cursor >= len(self.bundle.tail_actions):
            return None
        return self.bundle.tail_actions[self.cursor]


@dataclass(frozen=True)
class TerminalResult:
    status: CertificateStatus
    reason: str
    eligible: bool
    action: SelectedAction | None
    evidence_identity: str | None


@dataclass(frozen=True)
class DeadlineObservation:
    status: DeadlineStatus
    stage: str
    elapsed: float
    remaining_to_commit_guard: float
    profile_identity: str


@dataclass(frozen=True)
class SupervisorDecision:
    cycle_index: int
    state_identity: StateIdentity
    selected_action: SelectedAction | None
    allows_commit: bool
    reason: str
    rule_id: str
    prepared_bundle: PreparedBackupBundle | None = None


@dataclass(frozen=True)
class CommitReceipt:
    cycle_index: int
    pre_state_identity: StateIdentity
    selected_action_identity: ActionIdentity
    executed_action_identity: ActionIdentity
    exact_vector: Vector3
    action_role: ActionRole
    post_state: RuntimeStateSnapshot | None
    post_state_identity: StateIdentity | None
    committed: bool
    reason: str


@dataclass(frozen=True)
class CommitTransactionResult:
    attempt_identity: str
    transaction_state: CommitTransactionState
    plant_outcome: PlantOutcome
    evidence_status: EvidenceStatus
    token_status: TokenMutationStatus
    trace_status: TraceStatus
    committed: bool | None
    commit_receipt: CommitReceipt | None
    selected_action: SelectedAction | None
    executed_action_identity: ActionIdentity | None
    post_state: RuntimeStateSnapshot | None
    trace_ref: str | None
    recovery_required: bool
    retry_allowed: bool
    typed_failure_reason: str
    state_history: tuple[CommitTransactionState, ...]


@dataclass(frozen=True)
class TraceStepRecord:
    trial_id: str
    cycle_index: int
    state_identity: StateIdentity
    action_role: ActionRole
    selected_action_identity: ActionIdentity | None
    executed_action_identity: ActionIdentity | None
    commit_status: str
    facts: tuple[tuple[str, Any], ...]


@dataclass(frozen=True)
class TrialTraceLock:
    identity: TraceIdentity
    trial_id: str
    record_count: int
    trace_sha256: str
    schema_identity: str
    locked_before_evaluation: bool = True


@dataclass(frozen=True)
class TrialFinalizationResult:
    status: FinalizationStatus
    trace_lock: TrialTraceLock | None
    content_hash: str
    failure_reason: str | None
    retry_allowed: bool
    recovery_required: bool

    @property
    def record_count(self) -> int:
        return 0 if self.trace_lock is None else self.trace_lock.record_count

    @property
    def locked_before_evaluation(self) -> bool:
        return self.trace_lock is not None and self.trace_lock.locked_before_evaluation


@dataclass(frozen=True)
class AlternativeInventoryResult:
    status: str
    candidates: tuple[Candidate, ...]


@dataclass(frozen=True)
class StageFailureEvidence:
    source_phase: RuntimePhase
    stage_name: str
    failure_kind: StageFailureKind
    typed_reason: str
    reason_scope: ReasonScope
    authority_identity: str
    exception_type: str | None = None
    original_reason: str | None = None
    candidate_identity: CandidateIdentity | None = None
    state_identity: StateIdentity | None = None
    trial_id: str | None = None
    cycle_index: int | None = None


@dataclass(frozen=True)
class AlternativeInventoryEvidence:
    status: AlternativeInventoryStatus
    candidate_identities: tuple[CandidateIdentity, ...]
    source_authority: str
    state_identity: StateIdentity
    map_identity: str
    reason_scope: ReasonScope
    original_provider_status: str


# Public-cycle composition types are additive to the PR #116 runtime types.
# They carry orchestration facts only; none owns certificate, routing, action
# selection, plant, or scientific-evaluation authority.


class PublicCyclePhase(str, Enum):
    START_ADMISSION = "START_ADMISSION"
    R0_DIAGNOSTIC = "R0_DIAGNOSTIC"
    TRIAL_READY = "TRIAL_READY"
    TRIAL_BLOCKED_AT_ADMISSION = "TRIAL_BLOCKED_AT_ADMISSION"
    CYCLE_BEGIN = "CYCLE_BEGIN"
    L1_IMMEDIATE_CERTIFICATION = "L1_IMMEDIATE_CERTIFICATION"
    PRIMARY_PROPOSAL = "PRIMARY_PROPOSAL"
    PRIMARY_C0 = "PRIMARY_C0"
    PRIMARY_L2 = "PRIMARY_L2"
    PRIMARY_L3 = "PRIMARY_L3"
    ALTERNATIVE_ELIGIBILITY = "ALTERNATIVE_ELIGIBILITY"
    ALTERNATIVE_SOURCE_QUERY = "ALTERNATIVE_SOURCE_QUERY"
    ALTERNATIVE_C0 = "ALTERNATIVE_C0"
    ALTERNATIVE_L2 = "ALTERNATIVE_L2"
    ALTERNATIVE_L3 = "ALTERNATIVE_L3"
    BACKUP_VALIDATION = "BACKUP_VALIDATION"
    TERMINAL_EVALUATION = "TERMINAL_EVALUATION"
    ARBITRATION = "ARBITRATION"
    COMMIT = "COMMIT"
    TRACE_APPEND = "TRACE_APPEND"
    CYCLE_COMPLETE = "CYCLE_COMPLETE"
    ASSURANCE_BOUNDARY = "ASSURANCE_BOUNDARY"


class PublicCycleEvent(str, Enum):
    # PR #121 public names.
    START_PASS = "START_PASS"
    START_FAIL = "START_FAIL"
    START_UNKNOWN = "START_UNKNOWN"
    PRIMARY_UNAVAILABLE = "PRIMARY_UNAVAILABLE"
    PRIMARY_UNKNOWN = "PRIMARY_UNKNOWN"
    C0_FAIL = "C0_FAIL"
    C0_UNKNOWN = "C0_UNKNOWN"
    L2_UNKNOWN = "L2_UNKNOWN"
    L3_PASS = "L3_PASS"
    L3_FAIL = "L3_FAIL"
    L3_UNKNOWN = "L3_UNKNOWN"
    ALT_ELIGIBLE = "ALT_ELIGIBLE"
    ALT_NOT_ELIGIBLE = "ALT_NOT_ELIGIBLE"
    ALT_UNKNOWN = "ALT_UNKNOWN"
    BACKUP_VALID = "BACKUP_VALID"
    BACKUP_INVALID = "BACKUP_INVALID"
    BACKUP_NONE = "BACKUP_NONE"
    BACKUP_EXHAUSTED = "BACKUP_EXHAUSTED"
    BACKUP_UNKNOWN = "BACKUP_UNKNOWN"
    TERMINAL_READY = "TERMINAL_READY"
    TERMINAL_NOT_READY = "TERMINAL_NOT_READY"
    DEADLINE_OPEN = "DEADLINE_OPEN"
    DEADLINE_WARNING = "DEADLINE_WARNING"
    DEADLINE_EXPIRED = "DEADLINE_EXPIRED"
    DEADLINE_UNKNOWN = "DEADLINE_UNKNOWN"
    COMMIT_SUCCESS = "COMMIT_SUCCESS"
    BOUNDARY = "BOUNDARY"
    # Exact PR #107 observation/result values consumed by the executable table.
    INITIAL_SAFE = "INITIAL_SAFE"
    INITIAL_REPAIR_REQUIRED = "INITIAL_REPAIR_REQUIRED"
    REPAIR_PASS = "REPAIR_PASS"
    REPAIR_FAIL = "REPAIR_FAIL"
    REPAIR_UNKNOWN = "REPAIR_UNKNOWN"
    R0_DIAGNOSTIC_COMPLETE = "R0_DIAGNOSTIC_COMPLETE"
    L1_PASS = "L1_PASS"
    L1_FAIL = "L1_FAIL"
    L1_UNKNOWN_GLOBAL = "L1_UNKNOWN_GLOBAL"
    L1_UNKNOWN_HEALTH = "L1_UNKNOWN_HEALTH"
    L1_UNKNOWN_UNRESOLVED = "L1_UNKNOWN_UNRESOLVED"
    PRIMARY_AVAILABLE = "PRIMARY_AVAILABLE"
    NO_CANDIDATE = "NO_CANDIDATE"
    C0_PASS = "C0_PASS"
    C0_FAIL_LOCAL = "C0_FAIL_LOCAL"
    C0_UNKNOWN_LOCAL = "C0_UNKNOWN_LOCAL"
    C0_UNKNOWN_GLOBAL = "C0_UNKNOWN_GLOBAL"
    L2_PASS = "L2_PASS"
    L2_FAIL = "L2_FAIL"
    L2_UNKNOWN_LOCAL = "L2_UNKNOWN_LOCAL"
    L2_UNKNOWN_GLOBAL = "L2_UNKNOWN_GLOBAL"
    L3_WITNESS_FOUND = "L3_WITNESS_FOUND"
    L3_WITNESS_ABSENT = "L3_WITNESS_ABSENT"
    L3_UNKNOWN_LOCAL = "L3_UNKNOWN_LOCAL"
    L3_UNKNOWN_GLOBAL = "L3_UNKNOWN_GLOBAL"
    ALT_AVAILABLE = "ALT_AVAILABLE"
    ALT_EXHAUSTED = "ALT_EXHAUSTED"
    DEADLINE_GUARD = "DEADLINE_GUARD"
    ARBITRATE = "ARBITRATE"
    EXECUTE_RETAINED_BACKUP = "EXECUTE_RETAINED_BACKUP"
    TERMINAL_MEMBER_ELIGIBLE = "TERMINAL_MEMBER_ELIGIBLE"
    TERMINAL_MEMBER_NOT_ELIGIBLE = "TERMINAL_MEMBER_NOT_ELIGIBLE"
    TERMINAL_UNKNOWN = "TERMINAL_UNKNOWN"
    ROUTING_RULE_MISSING = "ROUTING_RULE_MISSING"
    ROUTING_RULE_AMBIGUOUS = "ROUTING_RULE_AMBIGUOUS"
    STAGE_EXCEPTION = "STAGE_EXCEPTION"
    SERIALIZATION_FAILURE = "SERIALIZATION_FAILURE"
    COMMIT_FAILURE = "COMMIT_FAILURE"


class RouteResolutionStatus(str, Enum):
    RESOLVED = "RESOLVED"
    BLOCKED_MISSING = "BLOCKED_MISSING"
    BLOCKED_AMBIGUOUS = "BLOCKED_AMBIGUOUS"


class TrialSessionStatus(str, Enum):
    NEW = "NEW"
    READY = "READY"
    BLOCKED = "BLOCKED"
    EVIDENCE_INCOMPLETE = "EVIDENCE_INCOMPLETE"
    RECOVERY_REQUIRED = "RECOVERY_REQUIRED"
    FINALIZING = "FINALIZING"
    FINALIZATION_FAILED = "FINALIZATION_FAILED"
    FINALIZED = "FINALIZED"


@dataclass(frozen=True)
class RuntimeRoutingContext:
    """Immutable facts supplied to Supervisor routing.

    The coordinator may only populate observations/evidence that already exist
    in the frozen runtime.  Permission and priority are intentionally absent:
    Supervisor derives those interpretations while resolving the frozen table.
    ``certified_candidate_available`` and ``terminal_evidence_eligible`` are
    evidence facts, not action-selection decisions.
    """

    source_phase: RuntimePhase
    deadline: DeadlineObservation
    authority_identity: str
    candidate_role: CandidateRole | None = None
    candidate_identity: CandidateIdentity | None = None
    candidate_available: bool = False
    retained_backup_present: bool = False
    retained_backup_valid: bool = False
    # Positional compatibility slots retained for PR #116/PR #121 synthetic
    # callers.  They are deliberately named as legacy hints and are ignored
    # by the coordinator; Supervisor may accept them only as a compatibility
    # bridge while callers migrate to the fact fields below.
    legacy_alternative_hint: bool = False
    legacy_navigation_hint: bool = False
    terminal_evaluated: bool = False
    legacy_terminal_hint: bool = False
    reason_scope: str = "NONE"
    certified_candidate_available: bool = False
    terminal_evidence_eligible: bool = False
    repeated_route_state: bool = False
    # Raw state/token provenance is carried for routing audits.  These fields
    # never grant permission and are not read by the coordinator as policy.
    backup_state: str | None = None
    candidate_provenance_identity: str | None = None


@dataclass(frozen=True)
class RoutingDecision:
    status: RouteResolutionStatus
    rule_id: str | None
    source_phase: RuntimePhase
    destination_phase: RuntimePhase | None
    may_start_next_stage: bool
    may_start_new_search: bool
    requires_arbitration: bool
    failure_mapping: str | None
    deadline_interpretation: str
    backup_routing_allowed: bool
    terminal_routing_allowed: bool
    commit_allowed: bool
    reason: str
    # Frozen-row metadata carried end-to-end.  The first thirteen fields above
    # remain source-compatible with PR #116 callers; these additive fields are
    # normative evidence, never recomputed from ``destination_phase``.
    action_authority: str | None = None
    old_backup_retained: bool | None = None
    new_backup_created: bool | None = None
    theorem_interpretation: str | None = None
    observation_result: str | None = None
    guard: str | None = None
    reason_scope: str | None = None
    retained_backup_requirement: str | None = None
    deadline_requirement: str | None = None
    candidate_requirement: str | None = None
    backup_routing_metadata_present: bool = False
    terminal_routing_metadata_present: bool = False


@dataclass(frozen=True)
class ActiveTrialContext:
    trial_id: str
    expected_map_identity: str
    initial_cycle_index: int = 0


@dataclass(frozen=True)
class ActiveCycleRequest:
    trial_id: str
    cycle_index: int
    desired_reference: Vector3
    expected_terminal_ref: str | None = None


@dataclass(frozen=True)
class TrialStartResult:
    trial_id: str
    status: CertificateStatus
    ready: bool
    boundary: bool
    reason: str
    admission_result: StartAdmissionResult
    diagnostic: R0Diagnostic | None
    phase_history: tuple[PublicCyclePhase, ...]
    routing_decisions: tuple[RoutingDecision, ...]


@dataclass(frozen=True)
class ActiveCycleContext:
    trial_id: str
    cycle_index: int
    snapshot_id: str
    state_id: str
    authority_identity: str
    deadline_identity: str
    phase: PublicCyclePhase
    phase_history: tuple[PublicCyclePhase, ...]
    deadline_observations: tuple[DeadlineObservation, ...] = ()
    l1_result: L1CycleResult | None = None
    primary_candidate: Candidate | None = None
    primary_binding: L1AttemptBinding | None = None
    primary_c0: C0Result | None = None
    primary_l2: L2Result | None = None
    primary_l3: L3Result | None = None
    alternative_attempts: tuple[CandidateIdentity, ...] = ()
    backup_validation: EvidenceResult | None = None
    backup_action: SelectedAction | None = None
    terminal_result: TerminalResult | None = None
    routing_decisions: tuple[RoutingDecision, ...] = ()
    final_supervisor_decision: SupervisorDecision | None = None
    commit_receipt: CommitReceipt | None = None
    commit_transaction_result: CommitTransactionResult | None = None
    trace_ref: str | None = None
    stage_failures: tuple[StageFailureEvidence, ...] = ()
    alternative_inventory_evidence: AlternativeInventoryEvidence | None = None


@dataclass(frozen=True)
class ActiveCycleResult:
    trial_id: str
    cycle_index: int
    start_state_id: str
    phase_history: tuple[PublicCyclePhase, ...]
    routing_rule_ids: tuple[str, ...]
    deadline_observations: tuple[DeadlineObservation, ...]
    l1_result: L1CycleResult | None
    candidate_refs: tuple[CandidateIdentity, ...]
    certificate_refs: tuple[str, ...]
    backup_status: str
    terminal_status: str
    final_supervisor_decision: SupervisorDecision | None
    supervisor_reason: str
    action_role: ActionRole | None
    commit_receipt: CommitReceipt | None
    committed: bool
    next_state: RuntimeStateSnapshot | None
    boundary: bool
    trace_ref: str | None
    typed_stop_or_failure_reason: str
    stage_failures: tuple[StageFailureEvidence, ...] = ()
    alternative_inventory_evidence: AlternativeInventoryEvidence | None = None
    commit_transaction_result: CommitTransactionResult | None = None


@dataclass(frozen=True)
class CoordinatorSession:
    trial_id: str
    map_identity: str
    next_cycle_index: int
    status: TrialSessionStatus


def all_finite(values: tuple[float, ...]) -> bool:
    return all(math.isfinite(value) for value in values)
