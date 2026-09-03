"""Terminal membership/certificate/eligibility preparation without selection."""

from __future__ import annotations

from typing import Callable

from .authority_registry import AuthorityRegistry
from .runtime_types import CertificateStatus, EvidenceResult, RuntimeStateSnapshot, TerminalResult


GOAL_HOLD_RUNTIME_ENABLED = False


class TerminalRuntime:
    def __init__(self, membership_predicate: Callable[[RuntimeStateSnapshot], bool], certificate_backend: Callable[[RuntimeStateSnapshot, str, float], EvidenceResult], registry: AuthorityRegistry) -> None:
        self._membership = membership_predicate
        self._backend = certificate_backend
        self._registry = registry

    def evaluate(self, snapshot: RuntimeStateSnapshot, fallback_context: bool, expected_terminal_ref: str | None = None) -> TerminalResult:
        if GOAL_HOLD_RUNTIME_ENABLED or self._registry.terminal.goal_hold_enabled:
            return TerminalResult(CertificateStatus.UNKNOWN, "GOAL_HOLD_RUNTIME_AUTHORITY_INVALID", False, None, None)
        if not fallback_context:
            return TerminalResult(CertificateStatus.FAIL, "TERMINAL_CONTEXT_NOT_ELIGIBLE", False, None, None)
        if snapshot.map_identity != self._registry.map_identity:
            return TerminalResult(CertificateStatus.UNKNOWN, "TERMINAL_MAP_IDENTITY_MISMATCH", False, None, None)
        try:
            if not self._membership(snapshot):
                return TerminalResult(CertificateStatus.FAIL, "TERMINAL_MEMBER_NOT_ELIGIBLE", False, None, None)
            evidence = self._backend(snapshot, snapshot.map_identity, self._registry.geometry.certification_effective_radius_m)
        except Exception as exc:
            return TerminalResult(CertificateStatus.UNKNOWN, f"TERMINAL_EXCEPTION:{type(exc).__name__}", False, None, None)
        if expected_terminal_ref is not None and expected_terminal_ref != evidence.evidence_identity:
            return TerminalResult(CertificateStatus.UNKNOWN, "STALE_TERMINAL_REFERENCE", False, None, evidence.evidence_identity)
        eligible = evidence.status == CertificateStatus.PASS
        return TerminalResult(evidence.status, evidence.reason, eligible, None, evidence.evidence_identity)
