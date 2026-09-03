"""Initial I0a full-query admission; no repair algorithm is introduced."""

from __future__ import annotations

from typing import Callable

from .authority_registry import AuthorityRegistry
from .runtime_types import CertificateStatus, EvidenceResult, RuntimeStateSnapshot, StartAdmissionResult


class StartAdmission:
    def __init__(self, full_query: Callable[[tuple[float, float, float], str, float], EvidenceResult], registry: AuthorityRegistry, repair_available: bool = False) -> None:
        self._full_query = full_query
        self._registry = registry
        self._repair_available = bool(repair_available)
        if self._repair_available:
            raise ValueError("I0B_REPAIR_NOT_AUTHORIZED")

    def evaluate(self, snapshot: RuntimeStateSnapshot) -> StartAdmissionResult:
        if snapshot.map_identity != self._registry.map_identity:
            return StartAdmissionResult(CertificateStatus.UNKNOWN, "MAP_IDENTITY_MISMATCH", snapshot.identity, "none", False)
        try:
            result = self._full_query(snapshot.position, snapshot.map_identity, self._registry.geometry.certification_effective_radius_m)
        except Exception as exc:
            return StartAdmissionResult(CertificateStatus.UNKNOWN, f"CURRENT_QUERY_EXCEPTION:{type(exc).__name__}", snapshot.identity, "none", False)
        return StartAdmissionResult(result.status, result.reason, snapshot.identity, result.evidence_identity, False)
