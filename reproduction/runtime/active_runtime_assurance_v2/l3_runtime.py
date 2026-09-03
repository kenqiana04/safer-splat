"""L3 sufficient-witness adapter that only prepares immutable bundles."""

from __future__ import annotations

from typing import Callable

from .authority_registry import AuthorityRegistry
from .runtime_types import Candidate, CertificateStatus, L2Result, L3Result, PreparedBackupBundle, RuntimeStateSnapshot, canonical_sha256


class L3Runtime:
    def __init__(self, witness_builder: Callable[..., tuple[CertificateStatus, object, str | None, str]], registry: AuthorityRegistry) -> None:
        self._builder = witness_builder
        self._registry = registry

    def evaluate(self, snapshot: RuntimeStateSnapshot, candidate: Candidate, l2_result: L2Result) -> L3Result:
        if l2_result.status != CertificateStatus.PASS or l2_result.candidate_identity != candidate.identity:
            return L3Result(CertificateStatus.UNKNOWN, "L3_NOT_REACHED_WITHOUT_MATCHING_L2_PASS", candidate.identity, None, None)
        try:
            status, tail_actions, terminal_ref, reason = self._builder(snapshot, candidate)
        except Exception as exc:
            return L3Result(CertificateStatus.UNKNOWN, f"L3_BACKEND_EXCEPTION:{type(exc).__name__}", candidate.identity, None, None)
        if status != CertificateStatus.PASS:
            return L3Result(status, str(reason), candidate.identity, None, "l3-evidence:sha256:" + canonical_sha256({"candidate": candidate.identity, "reason": reason}))
        bundle = PreparedBackupBundle.create(
            candidate,
            snapshot,
            tail_actions,
            self._registry.geometry.identity.value,
            self._registry.actuator.identity.value,
            self._registry.dynamics.identity.value,
            terminal_ref,
        )
        return L3Result(CertificateStatus.PASS, str(reason), candidate.identity, bundle, "l3-evidence:sha256:" + canonical_sha256(bundle))
