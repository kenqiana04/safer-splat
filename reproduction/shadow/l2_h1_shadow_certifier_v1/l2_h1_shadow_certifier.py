"""Specification-faithful, zero-authority L2/H1 shadow certifier."""
from __future__ import annotations

import math
from typing import Any

import numpy as np

from frozen_backend_adapter import certify_with_frozen_backend
from shadow_contract import CONTRACT_VERSION, ENDPOINT_FALLBACK_ENABLED, robot_margin_contract_matches
from shadow_types import (
    ExpectedMapSnapshot,
    FrozenMapQueryContext,
    H1Propagation,
    RobotMarginContract,
    ShadowCandidate,
    ShadowL2Result,
    ShadowL2Status,
    ShadowState,
)


class ShadowContractError(ValueError):
    def __init__(self, reason_code: str) -> None:
        super().__init__(reason_code)
        self.reason_code = reason_code


def _vector3(value: Any, nonfinite_reason: str = "INPUT_NONFINITE") -> np.ndarray:
    try:
        array = np.asarray(value, dtype=np.float64)
    except (TypeError, ValueError, OverflowError) as exc:
        raise ShadowContractError("UNSUPPORTED_REPRESENTATION") from exc
    if array.shape != (3,):
        raise ShadowContractError("INPUT_DIMENSION_MISMATCH")
    if not np.all(np.isfinite(array)):
        raise ShadowContractError(nonfinite_reason)
    return array


def _positive_dt(value: Any) -> float:
    if isinstance(value, bool) or not np.isscalar(value):
        raise ShadowContractError("INVALID_DT")
    try:
        dt = float(value)
    except (TypeError, ValueError, OverflowError) as exc:
        raise ShadowContractError("INVALID_DT") from exc
    if not math.isfinite(dt) or dt <= 0.0:
        raise ShadowContractError("INVALID_DT")
    return dt


def propagate_h1_endpoints(x_k: ShadowState, u_k: ShadowCandidate, dt: float) -> H1Propagation:
    """Frozen position-first Euler H1 endpoints; no u_(k+1) exists in this API."""
    if not isinstance(x_k, ShadowState) or not isinstance(u_k, ShadowCandidate):
        raise ShadowContractError("UNSUPPORTED_REPRESENTATION")
    p_k = _vector3(x_k.p_k)
    v_k = _vector3(x_k.v_k)
    control = _vector3(u_k.u_k)
    step = _positive_dt(dt)
    p_k1 = p_k + step * v_k
    v_k1 = v_k + step * control
    p_k2 = p_k + 2.0 * step * v_k + step * step * control
    return H1Propagation(tuple(map(float, p_k1)), tuple(map(float, v_k1)), tuple(map(float, p_k2)))


def h1_point(x_k: ShadowState, u_k: ShadowCandidate, dt: float, alpha: float) -> tuple[float, float, float]:
    step = _positive_dt(dt)
    try:
        a = float(alpha)
    except (TypeError, ValueError, OverflowError) as exc:
        raise ShadowContractError("INVALID_ALPHA") from exc
    if not math.isfinite(a) or a < 0.0 or a > 1.0:
        raise ShadowContractError("INVALID_ALPHA")
    p_k = _vector3(x_k.p_k); v_k = _vector3(x_k.v_k); control = _vector3(u_k.u_k)
    point = p_k + (1.0 + a) * step * v_k + a * step * step * control
    return tuple(map(float, point))


def _safe_vector(value: Any) -> tuple[float, ...] | None:
    try:
        array = np.asarray(value, dtype=np.float64).reshape(-1)
    except Exception:
        return None
    if not np.all(np.isfinite(array)):
        return None
    return tuple(map(float, array))


def _unknown_result(
    x_k: Any,
    u_k: Any,
    expected: Any,
    context: Any,
    robot: Any,
    reason: str,
    propagation: H1Propagation | None = None,
) -> ShadowL2Result:
    state_id = getattr(x_k, "state_id", None)
    candidate_id = getattr(u_k, "candidate_id", None)
    raw_dt = getattr(x_k, "dt", None)
    try:
        dt = float(raw_dt) if math.isfinite(float(raw_dt)) else None
    except Exception:
        dt = None
    expected_id = getattr(expected, "snapshot_id", None)
    actual_id = getattr(context, "actual_map_snapshot_id", None)
    backend_identity = getattr(context, "backend_identity", None)
    backend_class = getattr(context, "backend_class", None)
    contract_hash = getattr(robot, "contract_sha256", None)
    return ShadowL2Result(
        status=ShadowL2Status.UNKNOWN,
        reason_code=reason,
        candidate_id=candidate_id,
        state_id=state_id,
        p_k=_safe_vector(getattr(x_k, "p_k", None)),
        v_k=_safe_vector(getattr(x_k, "v_k", None)),
        u_k=_safe_vector(getattr(u_k, "u_k", None)),
        dt=dt,
        p_k1=None if propagation is None else propagation.p_k1,
        p_k2=None if propagation is None else propagation.p_k2,
        segment_start=None if propagation is None else propagation.p_k1,
        segment_end=None if propagation is None else propagation.p_k2,
        expected_map_snapshot_id=expected_id,
        actual_map_snapshot_id=actual_id,
        expected_map_snapshot_sha256=getattr(expected, "content_sha256", None),
        actual_map_snapshot_sha256=getattr(context, "actual_map_snapshot_sha256", None),
        backend_identity=backend_identity,
        backend_class=backend_class,
        formal_certificate_kind=None,
        formal_backend_status=None,
        formal_backend_reason=None,
        formal_value_or_bound=None,
        formal_threshold=None,
        diagnostic_only_fields={"available": False, "authority": "DIAGNOSTIC_ONLY", "result": None},
        diagnostic_available=False,
        diagnostic_result=None,
        contract_version=CONTRACT_VERSION,
        robot_margin_contract_sha256=contract_hash,
        endpoint_fallback_enabled=ENDPOINT_FALLBACK_ENABLED,
        semantic_fail_closed=True,
        l2_reached=None,
        l2_candidate_evaluated=True,
        l2_status=ShadowL2Status.UNKNOWN.value,
    )


def l2_h1_shadow_certify(
    x_k: ShadowState,
    u_k: ShadowCandidate,
    expected_map_snapshot: ExpectedMapSnapshot,
    frozen_map_query_context: FrozenMapQueryContext,
    frozen_robot_margin_contract: RobotMarginContract,
) -> ShadowL2Result:
    """Observe and classify only. This function has no actuation or selection output."""
    if not isinstance(expected_map_snapshot, ExpectedMapSnapshot) or not expected_map_snapshot.snapshot_id:
        return _unknown_result(x_k, u_k, expected_map_snapshot, frozen_map_query_context, frozen_robot_margin_contract, "INVALID_EXPECTED_MAP_SNAPSHOT")
    if not isinstance(frozen_map_query_context, FrozenMapQueryContext):
        return _unknown_result(x_k, u_k, expected_map_snapshot, frozen_map_query_context, frozen_robot_margin_contract, "INVALID_MAP_QUERY_CONTEXT")
    if not isinstance(frozen_robot_margin_contract, RobotMarginContract) or not robot_margin_contract_matches(frozen_robot_margin_contract):
        return _unknown_result(x_k, u_k, expected_map_snapshot, frozen_map_query_context, frozen_robot_margin_contract, "ROBOT_MARGIN_CONTRACT_MISMATCH")
    try:
        propagation = propagate_h1_endpoints(x_k, u_k, x_k.dt)
    except ShadowContractError as exc:
        return _unknown_result(x_k, u_k, expected_map_snapshot, frozen_map_query_context, frozen_robot_margin_contract, exc.reason_code)
    observation = certify_with_frozen_backend(
        frozen_map_query_context,
        np.asarray(propagation.p_k1, dtype=np.float64),
        np.asarray(propagation.p_k2, dtype=np.float64),
        expected_map_snapshot.snapshot_id,
        expected_map_snapshot.content_sha256,
        frozen_robot_margin_contract,
    )
    return ShadowL2Result(
        status=observation.status,
        reason_code=observation.reason_code,
        candidate_id=u_k.candidate_id,
        state_id=x_k.state_id,
        p_k=tuple(map(float, x_k.p_k)),
        v_k=tuple(map(float, x_k.v_k)),
        u_k=tuple(map(float, u_k.u_k)),
        dt=float(x_k.dt),
        p_k1=propagation.p_k1,
        p_k2=propagation.p_k2,
        segment_start=propagation.p_k1,
        segment_end=propagation.p_k2,
        expected_map_snapshot_id=expected_map_snapshot.snapshot_id,
        actual_map_snapshot_id=frozen_map_query_context.actual_map_snapshot_id,
        expected_map_snapshot_sha256=expected_map_snapshot.content_sha256,
        actual_map_snapshot_sha256=frozen_map_query_context.actual_map_snapshot_sha256,
        backend_identity=observation.backend_identity,
        backend_class=observation.backend_class,
        formal_certificate_kind=observation.formal_certificate_kind,
        formal_backend_status=observation.formal_backend_status,
        formal_backend_reason=observation.formal_backend_reason,
        formal_value_or_bound=observation.formal_value_or_bound,
        formal_threshold=observation.formal_threshold,
        diagnostic_only_fields=observation.diagnostic_only_fields,
        diagnostic_available=bool(observation.diagnostic_only_fields.get("available", False)),
        diagnostic_result=observation.diagnostic_only_fields if observation.diagnostic_only_fields.get("available", False) else None,
        contract_version=CONTRACT_VERSION,
        robot_margin_contract_sha256=frozen_robot_margin_contract.contract_sha256,
        endpoint_fallback_enabled=observation.endpoint_fallback_enabled,
        semantic_fail_closed=observation.status == ShadowL2Status.UNKNOWN,
        l2_reached=None,
        l2_candidate_evaluated=True,
        l2_status=observation.status.value,
    )


L2_H1_SHADOW_CERTIFY = l2_h1_shadow_certify

__all__ = ["L2_H1_SHADOW_CERTIFY", "h1_point", "l2_h1_shadow_certify", "propagate_h1_endpoints"]
