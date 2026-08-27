"""Typed, immutable, deterministic contracts for the shadow-only L2/H1 certifier."""
from __future__ import annotations

from dataclasses import asdict, dataclass, field, is_dataclass
from enum import Enum
import json
from typing import Any


def _jsonable(value: Any) -> Any:
    if isinstance(value, Enum):
        return value.value
    if is_dataclass(value):
        return {key: _jsonable(item) for key, item in asdict(value).items()}
    if isinstance(value, dict):
        return {str(key): _jsonable(item) for key, item in value.items()}
    if isinstance(value, (tuple, list)):
        return [_jsonable(item) for item in value]
    return value


class ShadowSerializable:
    def to_dict(self) -> dict[str, Any]:
        return _jsonable(self)

    def to_json(self) -> str:
        return json.dumps(self.to_dict(), sort_keys=True, separators=(",", ":"), allow_nan=False)


class ShadowL2Status(str, Enum):
    PASS = "PASS"
    FAIL = "FAIL"
    UNKNOWN = "UNKNOWN"


@dataclass(frozen=True)
class ShadowState(ShadowSerializable):
    p_k: tuple[float, ...]
    v_k: tuple[float, ...]
    state_id: str | None = None
    dt: float = 0.05


@dataclass(frozen=True)
class ShadowCandidate(ShadowSerializable):
    u_k: tuple[float, ...]
    candidate_id: str | None = None


@dataclass(frozen=True)
class ExpectedMapSnapshot(ShadowSerializable):
    snapshot_id: str
    content_sha256: str | None = None


@dataclass(frozen=True)
class RobotMarginContract(ShadowSerializable):
    robot_radius_m: float
    margin_m: float
    effective_radius_m: float
    rho_seg: float
    contract_sha256: str
    source_path: str


@dataclass(frozen=True)
class FrozenMapQueryContext:
    formal_backend: object
    actual_map_snapshot_id: str
    backend_identity: str
    backend_class: str
    diagnostic_backend: object | None = None
    primitive_family: str = "UNKNOWN"
    actual_map_snapshot_sha256: str | None = None
    snapshot_is_stale: bool = False
    query_context_resolved: bool = True


@dataclass(frozen=True)
class H1Propagation(ShadowSerializable):
    p_k1: tuple[float, float, float]
    v_k1: tuple[float, float, float]
    p_k2: tuple[float, float, float]


@dataclass(frozen=True)
class FrozenBackendObservation(ShadowSerializable):
    status: ShadowL2Status
    reason_code: str
    backend_identity: str
    backend_class: str
    formal_certificate_kind: str | None
    formal_backend_status: str | None
    formal_backend_reason: str | None
    formal_value_or_bound: float | None
    formal_threshold: float | None
    witness_time_or_interval: tuple[float, float] | float | None
    evaluated_primitive_count: int | None
    diagnostic_only_fields: dict[str, Any]
    endpoint_fallback_enabled: bool = False


@dataclass(frozen=True)
class ShadowL2Result(ShadowSerializable):
    status: ShadowL2Status
    reason_code: str
    candidate_id: str | None
    state_id: str | None
    p_k: tuple[float, ...] | None
    v_k: tuple[float, ...] | None
    u_k: tuple[float, ...] | None
    dt: float | None
    p_k1: tuple[float, float, float] | None
    p_k2: tuple[float, float, float] | None
    segment_start: tuple[float, float, float] | None
    segment_end: tuple[float, float, float] | None
    expected_map_snapshot_id: str | None
    actual_map_snapshot_id: str | None
    expected_map_snapshot_sha256: str | None
    actual_map_snapshot_sha256: str | None
    backend_identity: str | None
    backend_class: str | None
    formal_certificate_kind: str | None
    formal_backend_status: str | None
    formal_backend_reason: str | None
    formal_value_or_bound: float | None
    formal_threshold: float | None
    diagnostic_only_fields: dict[str, Any]
    diagnostic_available: bool
    diagnostic_result: dict[str, Any] | None
    contract_version: str
    robot_margin_contract_sha256: str | None
    endpoint_fallback_enabled: bool
    semantic_fail_closed: bool
    l2_reached: bool | None
    l2_candidate_evaluated: bool
    l2_status: str
    schema_version: str = "L2_H1_SHADOW_LOG_SCHEMA_V1"
    shadow_only: bool = field(default=True, init=False)
    controller_authority: bool = field(default=False, init=False)
    execution_authority: bool = field(default=False, init=False)
    candidate_selection_authority: bool = field(default=False, init=False)
    alternative_search_authority: bool = field(default=False, init=False)
    backup_authority: bool = field(default=False, init=False)
    terminal_authority: bool = field(default=False, init=False)
    fail_close_authority: bool = field(default=False, init=False)
    controller_intervention: bool = field(default=False, init=False)
    runtime_intervention: bool = field(default=False, init=False)
