"""Read-only adapter to the frozen PR #84 segment backends; no geometry lives here."""
from __future__ import annotations

import sys
from typing import Any

import numpy as np

from shadow_contract import (
    CONSERVATIVE_ELLIPSOID_IDENTITY,
    DENSE_DIAGNOSTIC_IDENTITY,
    ENDPOINT_FALLBACK_ENABLED,
    EXACT_SPHERE_IDENTITY,
    FORMAL_BACKEND_CLASSES,
    FORMAL_THRESHOLD,
    FROZEN_BACKEND_ROOT,
)
from shadow_types import FrozenBackendObservation, FrozenMapQueryContext, RobotMarginContract, ShadowL2Status

if str(FROZEN_BACKEND_ROOT) not in sys.path:
    sys.path.insert(0, str(FROZEN_BACKEND_ROOT))

from certifier.result_types import SegmentCertificate, SegmentStatus  # noqa: E402
from certifier.segment_backends.analytic_primitive import ExactSphereSegmentBackend  # noqa: E402,F401
from certifier.segment_backends.conservative_interval import ConservativeSignedDistanceIntervalBackend  # noqa: E402,F401
from certifier.segment_backends.sampled_diagnostic import SampledDiagnosticBackend  # noqa: E402,F401


def _diagnose(context: FrozenMapQueryContext, start: np.ndarray, end: np.ndarray, expected_snapshot_id: str, robot: RobotMarginContract) -> dict[str, Any]:
    diagnostic = context.diagnostic_backend
    if diagnostic is None:
        return {"available": False, "authority": "DIAGNOSTIC_ONLY", "result": None}
    try:
        certificate = diagnostic.diagnose(
            start,
            end,
            context.actual_map_snapshot_id,
            expected_snapshot_id,
            robot.effective_radius_m,
            robot.rho_seg,
        )
        return {
            "available": True,
            "authority": "DIAGNOSTIC_ONLY",
            "backend_identity": getattr(diagnostic, "method", None),
            "status": certificate.status.value,
            "reason_code": certificate.reason_code,
            "value": certificate.lower_bound,
            "sample_count": getattr(diagnostic, "samples", None),
            "formal_authority": False,
        }
    except Exception as exc:  # diagnostic failure cannot alter formal status
        return {
            "available": True,
            "authority": "DIAGNOSTIC_ONLY",
            "backend_identity": getattr(diagnostic, "method", None),
            "status": "DIAGNOSTIC_ERROR",
            "reason_code": type(exc).__name__,
            "value": None,
            "formal_authority": False,
        }


def _unknown(context: FrozenMapQueryContext, reason: str, diagnostic: dict[str, Any] | None = None, certificate: SegmentCertificate | None = None) -> FrozenBackendObservation:
    return FrozenBackendObservation(
        status=ShadowL2Status.UNKNOWN,
        reason_code=reason,
        backend_identity=context.backend_identity,
        backend_class=context.backend_class,
        formal_certificate_kind=None if certificate is None else certificate.exact_or_conservative,
        formal_backend_status=None if certificate is None else certificate.status.value,
        formal_backend_reason=None if certificate is None else certificate.reason_code,
        formal_value_or_bound=None if certificate is None else certificate.lower_bound,
        formal_threshold=None if certificate is None else FORMAL_THRESHOLD,
        witness_time_or_interval=None if certificate is None else certificate.witness_time_or_interval,
        evaluated_primitive_count=None if certificate is None else certificate.evaluated_gaussian_count,
        diagnostic_only_fields=diagnostic or {"available": False, "authority": "DIAGNOSTIC_ONLY", "result": None},
        endpoint_fallback_enabled=ENDPOINT_FALLBACK_ENABLED,
    )


def certify_with_frozen_backend(
    context: FrozenMapQueryContext,
    start: np.ndarray,
    end: np.ndarray,
    expected_snapshot_id: str,
    expected_snapshot_sha256: str | None,
    robot: RobotMarginContract,
) -> FrozenBackendObservation:
    """Call the frozen backend on the full H1 segment and map its typed result."""
    if not context.query_context_resolved:
        return _unknown(context, "MAP_QUERY_CONTEXT_UNRESOLVED")
    if context.snapshot_is_stale:
        return _unknown(context, "MAP_SNAPSHOT_STALE")
    if context.actual_map_snapshot_id != expected_snapshot_id:
        return _unknown(context, "MAP_SNAPSHOT_MISMATCH")
    if expected_snapshot_sha256 is not None:
        if context.actual_map_snapshot_sha256 is None:
            return _unknown(context, "MAP_HASH_UNAVAILABLE")
        if context.actual_map_snapshot_sha256 != expected_snapshot_sha256:
            return _unknown(context, "MAP_HASH_MISMATCH")
    if context.formal_backend is None:
        return _unknown(context, "FORMAL_BACKEND_UNAVAILABLE")
    actual_method = getattr(context.formal_backend, "method", None)
    if actual_method != context.backend_identity:
        return _unknown(context, "FORMAL_BACKEND_IDENTITY_MISMATCH")
    if actual_method == DENSE_DIAGNOSTIC_IDENTITY or actual_method not in FORMAL_BACKEND_CLASSES:
        return _unknown(context, "UNSUPPORTED_FORMAL_BACKEND")
    frozen_types = {
        EXACT_SPHERE_IDENTITY: ExactSphereSegmentBackend,
        CONSERVATIVE_ELLIPSOID_IDENTITY: ConservativeSignedDistanceIntervalBackend,
    }
    if type(context.formal_backend) is not frozen_types[actual_method]:
        return _unknown(context, "FROZEN_BACKEND_SYMBOL_MISMATCH")
    if context.backend_class != FORMAL_BACKEND_CLASSES[actual_method]:
        return _unknown(context, "FORMAL_BACKEND_CLASS_MISMATCH")
    try:
        certificate = context.formal_backend.certify(
            np.asarray(start, dtype=np.float64),
            np.asarray(end, dtype=np.float64),
            context.actual_map_snapshot_id,
            expected_snapshot_id,
            robot.effective_radius_m,
            robot.rho_seg,
        )
    except Exception:
        return _unknown(context, "BACKEND_EXCEPTION")
    diagnostic = _diagnose(context, start, end, expected_snapshot_id, robot)
    if certificate.endpoint_only_fallback:
        return _unknown(context, "ENDPOINT_FALLBACK_FORBIDDEN", diagnostic, certificate)
    if certificate.method != actual_method:
        return _unknown(context, "FORMAL_BACKEND_IDENTITY_MISMATCH", diagnostic, certificate)
    if certificate.status == SegmentStatus.CERTIFIED_SAFE:
        if not certificate.certified:
            return _unknown(context, "INCONSISTENT_FORMAL_SAFE_CERTIFICATE", diagnostic, certificate)
        status, reason = ShadowL2Status.PASS, "FORMAL_SEGMENT_SAFE"
    elif certificate.status == SegmentStatus.CERTIFIED_UNSAFE:
        status, reason = ShadowL2Status.FAIL, "FORMAL_SEGMENT_UNSAFE"
    else:
        reason_map = {
            SegmentStatus.NOT_CERTIFIED_WITHIN_BUDGET: "CERTIFICATE_BUDGET_EXHAUSTED",
            SegmentStatus.MAP_QUERY_UNKNOWN: "MAP_QUERY_UNKNOWN",
            SegmentStatus.MAP_QUERY_NONFINITE: "MAP_QUERY_NONFINITE",
            SegmentStatus.MAP_SNAPSHOT_MISMATCH: "MAP_SNAPSHOT_MISMATCH",
            SegmentStatus.ERROR: "BACKEND_ERROR",
        }
        return _unknown(context, reason_map.get(certificate.status, "UNRESOLVED_BACKEND_STATUS"), diagnostic, certificate)
    return FrozenBackendObservation(
        status=status,
        reason_code=reason,
        backend_identity=actual_method,
        backend_class=context.backend_class,
        formal_certificate_kind=certificate.exact_or_conservative,
        formal_backend_status=certificate.status.value,
        formal_backend_reason=certificate.reason_code,
        formal_value_or_bound=certificate.lower_bound,
        formal_threshold=FORMAL_THRESHOLD,
        witness_time_or_interval=certificate.witness_time_or_interval,
        evaluated_primitive_count=certificate.evaluated_gaussian_count,
        diagnostic_only_fields=diagnostic,
        endpoint_fallback_enabled=ENDPOINT_FALLBACK_ENABLED,
    )


__all__ = [
    "ExactSphereSegmentBackend",
    "ConservativeSignedDistanceIntervalBackend",
    "SampledDiagnosticBackend",
    "SegmentStatus",
    "certify_with_frozen_backend",
]
