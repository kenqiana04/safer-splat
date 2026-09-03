"""Once-per-cycle immediate closed-segment certification and attempt binding."""

from __future__ import annotations

from typing import Callable

from .authority_registry import AuthorityRegistry
from .runtime_types import (
    AttemptIdentity,
    Candidate,
    CertificateStatus,
    EvidenceResult,
    L1AttemptBinding,
    L1CycleResult,
    RuntimeStateSnapshot,
    canonical_sha256,
)


class L1Runtime:
    def __init__(self, segment_backend: Callable[..., EvidenceResult], registry: AuthorityRegistry) -> None:
        self._backend = segment_backend
        self._registry = registry
        self._cache: dict[tuple[str, int], L1CycleResult] = {}

    def evaluate_cycle(self, snapshot: RuntimeStateSnapshot) -> L1CycleResult:
        key = (snapshot.identity.value, snapshot.cycle_index)
        if key in self._cache:
            return self._cache[key]
        start = snapshot.position
        end = tuple(p + snapshot.dt * v for p, v in zip(snapshot.position, snapshot.velocity))
        segment_id = "segment:sha256:" + canonical_sha256({"start": start, "end": end, "closed": True, "state": snapshot.identity})
        if snapshot.map_identity != self._registry.map_identity:
            evidence = EvidenceResult(CertificateStatus.UNKNOWN, "MAP_IDENTITY_MISMATCH", "none")
        else:
            try:
                evidence = self._backend(start, end, snapshot.map_identity, self._registry.geometry.certification_effective_radius_m, self._registry.geometry.rho_seg_m)
            except Exception as exc:
                evidence = EvidenceResult(CertificateStatus.UNKNOWN, f"L1_BACKEND_EXCEPTION:{type(exc).__name__}", "none")
        result_id = "l1-cycle:sha256:" + canonical_sha256({"state": snapshot.identity, "segment": segment_id, "evidence": evidence})
        result = L1CycleResult(result_id, evidence.status, evidence.reason, snapshot.identity, segment_id, start, end, evidence.evidence_identity)
        self._cache[key] = result
        return result

    def bind_attempt(self, cycle_result: L1CycleResult, candidate: Candidate, attempt_index: int) -> L1AttemptBinding:
        material = {"cycle_result": cycle_result.identity, "candidate": candidate.identity, "state": cycle_result.state_identity, "segment": cycle_result.segment_identity, "attempt_index": int(attempt_index)}
        return L1AttemptBinding(AttemptIdentity("attempt:sha256:" + canonical_sha256(material)), cycle_result.identity, candidate.identity, cycle_result.state_identity, cycle_result.segment_identity)
