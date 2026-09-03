"""Additive adapter around the existing PD-to-Clarabel proposal path."""

from __future__ import annotations

from typing import Callable, Iterable

from .runtime_types import CandidateRole, CertificateStatus, ProposalResult, RuntimeStateSnapshot, all_finite, make_candidate


class PrimaryProposalAdapter:
    def __init__(self, proposal_solver: Callable[[RuntimeStateSnapshot, tuple[float, float, float]], tuple[bool, Iterable[float] | None, str]], controller_identity: str) -> None:
        self._solver = proposal_solver
        self._controller_identity = str(controller_identity)

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
        candidate = make_candidate(vector, CandidateRole.PRIMARY, "PRIMARY_NATIVE_CBF_QP", self._controller_identity, snapshot)
        return ProposalResult(CertificateStatus.PASS, str(reason) or "QP_SOLVED", candidate, u_des)  # type: ignore[arg-type]
