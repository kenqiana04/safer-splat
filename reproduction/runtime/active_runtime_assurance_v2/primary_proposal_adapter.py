"""Additive adapter around the existing PD-to-Clarabel proposal path."""

from __future__ import annotations

import struct
from typing import Callable, Iterable

from .runtime_types import CandidateRole, CertificateStatus, ProposalResult, RuntimeStateSnapshot, all_finite, make_candidate


SOURCE_SCALAR_CONTRACT_IEEE754_BINARY32 = "IEEE754_BINARY32"


def _as_ieee754_binary32(value: float) -> float:
    return struct.unpack("!f", struct.pack("!f", float(value)))[0]


class PrimaryProposalAdapter:
    def __init__(
        self,
        proposal_solver: Callable[[RuntimeStateSnapshot, tuple[float, float, float]], tuple[bool, Iterable[float] | None, str]],
        controller_identity: str,
        *,
        actuator_bounds: tuple[Iterable[float], Iterable[float]] | None = None,
        source_scalar_contract: str | None = None,
    ) -> None:
        self._solver = proposal_solver
        self._controller_identity = str(controller_identity)
        if (actuator_bounds is None) != (source_scalar_contract is None):
            raise ValueError("SOURCE_SCALAR_CONTRACT_CONFIGURATION_INCOMPLETE")
        if source_scalar_contract is not None and source_scalar_contract != SOURCE_SCALAR_CONTRACT_IEEE754_BINARY32:
            raise ValueError("SOURCE_SCALAR_CONTRACT_UNSUPPORTED")
        self._source_scalar_contract = source_scalar_contract
        self._actuator_bounds: tuple[tuple[float, ...], tuple[float, ...]] | None = None
        if actuator_bounds is not None:
            lower = tuple(float(value) for value in actuator_bounds[0])
            upper = tuple(float(value) for value in actuator_bounds[1])
            if len(lower) != 3 or len(upper) != 3 or not all_finite((*lower, *upper)):
                raise ValueError("ACTUATOR_BOUND_CONFIGURATION_INVALID")
            self._actuator_bounds = (lower, upper)

    def _canonicalize_exact_source_boundary_representations(self, vector: tuple[float, ...]) -> tuple[float, ...]:
        if self._actuator_bounds is None or self._source_scalar_contract != SOURCE_SCALAR_CONTRACT_IEEE754_BINARY32:
            return vector
        lower, upper = self._actuator_bounds
        canonical = []
        for value, low, high in zip(vector, lower, upper):
            low32 = _as_ieee754_binary32(low)
            high32 = _as_ieee754_binary32(high)
            if low32 != low and value == low32:
                canonical.append(low)
            elif high32 != high and value == high32:
                canonical.append(high)
            else:
                canonical.append(value)
        return tuple(canonical)

    def propose(self, snapshot: RuntimeStateSnapshot, desired_reference: Iterable[float]) -> ProposalResult:
        u_des = tuple(float(value) for value in desired_reference)
        if len(u_des) != 3 or not all_finite(u_des):
            return ProposalResult(CertificateStatus.UNKNOWN, "DESIRED_REFERENCE_INVALID", None, (0.0, 0.0, 0.0))
        try:
            success, raw, reason = self._solver(snapshot, u_des)  # injected fake or exact frozen solver adapter
        except Exception as exc:
            return ProposalResult(CertificateStatus.UNKNOWN, f"QP_SOLVER_EXCEPTION:{type(exc).__name__}", None, u_des)  # type: ignore[arg-type]
        if not success:
            return ProposalResult(CertificateStatus.FAIL, "QP_SOLVER_FAILED", None, u_des)  # type: ignore[arg-type]
        if raw is None:
            return ProposalResult(CertificateStatus.UNKNOWN, "QP_RESULT_MISSING", None, u_des)  # type: ignore[arg-type]
        vector = tuple(float(value) for value in raw)
        if len(vector) != 3 or not all_finite(vector):
            return ProposalResult(CertificateStatus.UNKNOWN, "QP_RESULT_NONFINITE_OR_WRONG_DIMENSION", None, u_des)  # type: ignore[arg-type]
        vector = self._canonicalize_exact_source_boundary_representations(vector)
        candidate = make_candidate(vector, CandidateRole.PRIMARY, "PRIMARY_NATIVE_CBF_QP", self._controller_identity, snapshot)
        return ProposalResult(CertificateStatus.PASS, str(reason) or "QP_SOLVED", candidate, u_des)  # type: ignore[arg-type]
