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
class AlternativeInventoryResult:
    status: str
    candidates: tuple[Candidate, ...]


def all_finite(values: tuple[float, ...]) -> bool:
    return all(math.isfinite(value) for value in values)
