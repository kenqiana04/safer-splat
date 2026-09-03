"""V2 H1 wrapper with explicit PR #108 geometry injection."""

from __future__ import annotations

from typing import Callable

from .authority_registry import AuthorityRegistry
from .runtime_types import Candidate, CertificateStatus, EvidenceResult, L2Result, RuntimeStateSnapshot, canonical_sha256


class L2Runtime:
    def __init__(self, segment_backend: Callable[..., EvidenceResult], registry: AuthorityRegistry) -> None:
        self._backend = segment_backend
        self._registry = registry

    def evaluate(self, snapshot: RuntimeStateSnapshot, candidate: Candidate) -> L2Result:
        p_k1 = tuple(p + snapshot.dt * v for p, v in zip(snapshot.position, snapshot.velocity))
        p_k2 = tuple(p + 2.0 * snapshot.dt * v + snapshot.dt * snapshot.dt * u for p, v, u in zip(snapshot.position, snapshot.velocity, candidate.vector))
        segment_id = "h1-segment:sha256:" + canonical_sha256({"start": p_k1, "end": p_k2, "candidate": candidate.identity, "closed": True})
        if candidate.provenance.state_identity != snapshot.identity or snapshot.map_identity != self._registry.map_identity:
            evidence = EvidenceResult(CertificateStatus.UNKNOWN, "L2_AUTHORITY_OR_ALIGNMENT_MISMATCH", "none")
        else:
            try:
                evidence = self._backend(p_k1, p_k2, snapshot.map_identity, self._registry.geometry.certification_effective_radius_m, self._registry.geometry.rho_seg_m)
            except Exception as exc:
                evidence = EvidenceResult(CertificateStatus.UNKNOWN, f"L2_BACKEND_EXCEPTION:{type(exc).__name__}", "none")
        return L2Result.create(evidence.status, evidence.reason, candidate.identity, p_k1, p_k2, segment_id, evidence.evidence_identity)
