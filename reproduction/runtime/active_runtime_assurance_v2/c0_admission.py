"""Frozen C0 candidate/provenance/actuator admission; no clipping."""

from __future__ import annotations

from .authority_registry import AuthorityRegistry
from .bounded_recovery import RecoverySourceGrant, SOURCE as RECOVERY_SOURCE
from .runtime_types import C0Result, Candidate, CertificateStatus, RuntimeStateSnapshot, all_finite


class C0Admission:
    def __init__(self, registry: AuthorityRegistry) -> None:
        self._registry = registry

    def evaluate(self, candidate: Candidate, snapshot: RuntimeStateSnapshot,
                 recovery_grant: RecoverySourceGrant | None = None) -> C0Result:
        authority = self._registry.actuator.identity.value
        if len(candidate.vector) != 3 or not all_finite(candidate.vector):
            return C0Result(CertificateStatus.UNKNOWN, "CANDIDATE_NONFINITE_OR_WRONG_DIMENSION", candidate.identity, candidate.vector, authority)
        if candidate.provenance.state_identity != snapshot.identity or candidate.provenance.map_identity != snapshot.map_identity:
            return C0Result(CertificateStatus.UNKNOWN, "CANDIDATE_STATE_OR_MAP_IDENTITY_MISMATCH", candidate.identity, candidate.vector, authority)
        if candidate.provenance.source_type == RECOVERY_SOURCE and (
            recovery_grant is None or not recovery_grant.matches(snapshot, self._registry)
            or candidate.provenance.controller_identity != recovery_grant.identity
            or candidate.role.value != "ALTERNATIVE"
        ):
            return C0Result(CertificateStatus.FAIL, "RECOVERY_SOURCE_UNAUTHORIZED", candidate.identity, candidate.vector, authority)
        if not candidate.provenance.lawful:
            return C0Result(CertificateStatus.FAIL, "SOURCE_INVALID", candidate.identity, candidate.vector, authority)
        if any(value < low or value > high for value, low, high in zip(candidate.vector, self._registry.actuator.u_min, self._registry.actuator.u_max)):
            return C0Result(CertificateStatus.FAIL, "F_ACTUATOR_ADMISSIBILITY_LOCAL", candidate.identity, candidate.vector, authority)
        return C0Result(CertificateStatus.PASS, "C0_PASS", candidate.identity, candidate.vector, authority)
