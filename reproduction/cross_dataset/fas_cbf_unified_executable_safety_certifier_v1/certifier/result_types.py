"""Immutable, deterministic, JSON-serializable certification contracts."""
from __future__ import annotations

from dataclasses import asdict, dataclass, field, is_dataclass
from enum import Enum
import json
import math
from typing import Any


def _jsonable(value: Any) -> Any:
    if isinstance(value, Enum):
        return value.value
    if is_dataclass(value):
        return {k: _jsonable(v) for k, v in asdict(value).items()}
    if isinstance(value, dict):
        return {str(k): _jsonable(v) for k, v in value.items()}
    if isinstance(value, (tuple, list)):
        return [_jsonable(v) for v in value]
    return value


class Serializable:
    def to_dict(self) -> dict[str, Any]:
        return _jsonable(self)

    def to_json(self) -> str:
        return json.dumps(self.to_dict(), sort_keys=True, separators=(",", ":"), allow_nan=False)


class BarrierStatus(str, Enum):
    FINITE = "FINITE"
    UNKNOWN = "UNKNOWN"
    NONFINITE = "NONFINITE"
    ERROR = "ERROR"


class ExecutableStatus(str, Enum):
    CERTIFIED_NOMINAL_CONTROL = "CERTIFIED_NOMINAL_CONTROL"
    CERTIFIED_ALTERNATIVE_CONTROL = "CERTIFIED_ALTERNATIVE_CONTROL"
    CERTIFIED_BACKUP_CONTROL = "CERTIFIED_BACKUP_CONTROL"
    CERTIFIED_TERMINAL_ACTION = "CERTIFIED_TERMINAL_ACTION"
    FAIL_CLOSED_ACTUATOR_VIOLATION = "FAIL_CLOSED_ACTUATOR_VIOLATION"
    FAIL_CLOSED_CURRENT_CBF_INFEASIBLE = "FAIL_CLOSED_CURRENT_CBF_INFEASIBLE"
    FAIL_CLOSED_IMMEDIATE_SEGMENT_UNSAFE = "FAIL_CLOSED_IMMEDIATE_SEGMENT_UNSAFE"
    FAIL_CLOSED_BACKUP_WITNESS_NOT_FOUND_IN_FROZEN_LIBRARY = "FAIL_CLOSED_BACKUP_WITNESS_NOT_FOUND_IN_FROZEN_LIBRARY"
    FAIL_CLOSED_NOT_CERTIFIED_WITHIN_BUDGET = "FAIL_CLOSED_NOT_CERTIFIED_WITHIN_BUDGET"
    NOT_EVALUABLE_MAP_QUERY_UNKNOWN = "NOT_EVALUABLE_MAP_QUERY_UNKNOWN"
    NOT_EVALUABLE_MAP_QUERY_NONFINITE = "NOT_EVALUABLE_MAP_QUERY_NONFINITE"
    SOLVER_FAILED_NOT_SCIENTIFICALLY_CLASSIFIED = "SOLVER_FAILED_NOT_SCIENTIFICALLY_CLASSIFIED"
    INFRASTRUCTURE_FAILURE = "INFRASTRUCTURE_FAILURE"


class SegmentStatus(str, Enum):
    CERTIFIED_SAFE = "CERTIFIED_SAFE"
    CERTIFIED_UNSAFE = "CERTIFIED_UNSAFE"
    NOT_CERTIFIED_WITHIN_BUDGET = "NOT_CERTIFIED_WITHIN_BUDGET"
    MAP_QUERY_UNKNOWN = "MAP_QUERY_UNKNOWN"
    MAP_QUERY_NONFINITE = "MAP_QUERY_NONFINITE"
    MAP_SNAPSHOT_MISMATCH = "MAP_SNAPSHOT_MISMATCH"
    ERROR = "ERROR"


@dataclass(frozen=True)
class State(Serializable):
    position: tuple[float, float, float]
    velocity: tuple[float, float, float]
    timestamp: float
    map_snapshot_id: str

    @property
    def finite(self) -> bool:
        return len(self.position) == 3 and len(self.velocity) == 3 and all(
            math.isfinite(float(v)) for v in (*self.position, *self.velocity, self.timestamp)
        )


@dataclass(frozen=True)
class Control(Serializable):
    acceleration: tuple[float, float, float]
    source: str
    candidate_id: str

    @property
    def finite(self) -> bool:
        return len(self.acceleration) == 3 and all(math.isfinite(float(v)) for v in self.acceleration)


@dataclass(frozen=True)
class ActuatorBounds(Serializable):
    u_min: tuple[float, float, float]
    u_max: tuple[float, float, float]
    v_min: tuple[float, float, float]
    v_max: tuple[float, float, float]
    dt: float

    @property
    def valid(self) -> bool:
        values = (*self.u_min, *self.u_max, *self.v_min, *self.v_max, self.dt)
        return (
            all(len(v) == 3 for v in (self.u_min, self.u_max, self.v_min, self.v_max))
            and all(math.isfinite(float(v)) for v in values)
            and self.dt > 0.0
            and all(lo <= 0.0 <= hi for lo, hi in zip(self.u_min, self.u_max))
            and all(lo <= hi for lo, hi in zip(self.u_min, self.u_max))
            and all(lo <= hi for lo, hi in zip(self.v_min, self.v_max))
        )


@dataclass(frozen=True)
class BarrierQueryResult(Serializable):
    status: BarrierStatus
    h: float | None
    gradient: tuple[float, float, float] | None
    hessian: tuple[tuple[float, float, float], ...] | None
    active_gaussian_ids: tuple[int, ...]
    map_snapshot_id: str
    semantics: str = "GAUSSIAN_BARRIER_PROXY_NOT_METRIC_CLEARANCE"
    query_scope: str = "FULL"
    reason_code: str = ""
    signed_distance: float | None = None
    evaluated_gaussian_count: int = 0


@dataclass(frozen=True)
class ActuatorCertificate(Serializable):
    certified: bool
    reason_code: str
    actual_control: Control | None
    original_candidate_id: str
    componentwise_checks: tuple[bool, bool, bool]


@dataclass(frozen=True)
class CurrentFeasibilityCertificate(Serializable):
    certified: bool
    reason_code: str
    full_query: BarrierQueryResult
    reduced_query_used: bool
    full_query_postcheck_performed: bool
    reference_online_read_count: int = 0
    candidate_control_checked: bool = False
    candidate_constraint_mode: str = "MAP_FEASIBILITY_ONLY"
    max_full_constraint_residual: float | None = None


@dataclass(frozen=True)
class SegmentCertificate(Serializable):
    status: SegmentStatus
    certified: bool
    lower_bound: float | None
    witness_time_or_interval: tuple[float, float] | float | None
    method: str
    exact_or_conservative: str
    map_snapshot_id: str
    evaluated_gaussian_count: int
    reason_code: str
    node_count: int = 0
    endpoint_only_fallback: bool = False


@dataclass(frozen=True)
class TerminalCertificate(Serializable):
    certified: bool
    terminal_state: State
    zero_hold_certified: bool
    assumptions: tuple[str, ...]
    reason_code: str
    velocity_tolerance: float
    zero_hold_segment: SegmentCertificate | None = None


@dataclass(frozen=True)
class BackupWitness(Serializable):
    certified: bool
    initial_candidate_control: Control
    backup_controls: tuple[Control, ...]
    states: tuple[State, ...]
    per_segment_certificates: tuple[SegmentCertificate, ...]
    terminal_certificate: TerminalCertificate | None
    horizon: int
    map_snapshot_id: str
    reason_code: str


@dataclass(frozen=True)
class RejectedCandidate(Serializable):
    candidate_id: str
    source: str
    reason_code: str
    stage: str


@dataclass(frozen=True)
class ExecutableSafetyResult(Serializable):
    status: ExecutableStatus
    committed_control_or_none: Control | None
    actuator_certificate: ActuatorCertificate | None
    cbf_certificate: CurrentFeasibilityCertificate | None
    segment_certificate: SegmentCertificate | None
    backup_witness: BackupWitness | None
    rejected_candidates: tuple[RejectedCandidate, ...]
    fail_closed_reason: str | None
    scientific_state: str
    infrastructure_state: str
    timing: dict[str, float]
    immutable_identities: dict[str, str]
    next_state_machine_state: str = "NEXT_CYCLE_DIAGNOSIS"


AUTHORIZED_STATUS_VALUES = tuple(status.value for status in ExecutableStatus)
