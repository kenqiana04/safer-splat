"""Additive canonical identity evidence ledger and trace augmentation."""

from __future__ import annotations

from dataclasses import replace
from typing import Any

from reproduction.runtime.active_runtime_assurance_v2.runtime_types import TraceStepRecord
from reproduction.runtime.active_runtime_assurance_v2.trace_writer import TraceWriter


CERT_EXEC_STATE_IDENTITY_MATCH = "CERT_EXEC_STATE_IDENTITY_MATCH"
CERT_EXEC_STATE_IDENTITY_MISMATCH = "CERT_EXEC_STATE_IDENTITY_MISMATCH"


class CanonicalIdentityLedger:
    """Task-local observational evidence; it has no routing or action authority."""

    def __init__(self) -> None:
        self._cycles: dict[tuple[str, int], dict[str, Any]] = {}
        self._scoped_cycles: dict[
            tuple[str, int], dict[str, dict[str, tuple[tuple[str, Any], ...]]]
        ] = {}

    def record(self, trial_id: str, cycle_index: int, **facts: Any) -> None:
        key = (str(trial_id), int(cycle_index))
        current = self._cycles.setdefault(key, {})
        for name, value in facts.items():
            if name in self._scoped_cycles.get(key, {}):
                raise RuntimeError(f"CANONICAL_EVIDENCE_NAMESPACE_COLLISION:{name}")
            if name in current and current[name] != value:
                raise RuntimeError(f"CANONICAL_EVIDENCE_REWRITE_FORBIDDEN:{name}")
            current[name] = value

    def record_scoped(
        self,
        trial_id: str,
        cycle_index: int,
        namespace: str,
        scope_key: str,
        **payload: Any,
    ) -> None:
        """Record deterministic observational evidence for one immutable scope.

        Identical writes are idempotent. A conflicting write to the same scope
        is rejected; evidence from different candidate scopes can coexist.
        """

        namespace_v, scope_v = str(namespace), str(scope_key)
        if not namespace_v or not scope_v:
            raise ValueError("CANONICAL_SCOPED_EVIDENCE_IDENTITY_REQUIRED")
        key = (str(trial_id), int(cycle_index))
        if namespace_v in self._cycles.get(key, {}):
            raise RuntimeError(f"CANONICAL_EVIDENCE_NAMESPACE_COLLISION:{namespace_v}")
        canonical_payload = tuple(sorted(payload.items()))
        namespace_store = self._scoped_cycles.setdefault(key, {}).setdefault(namespace_v, {})
        if scope_v in namespace_store and namespace_store[scope_v] != canonical_payload:
            raise RuntimeError(
                f"CANONICAL_SCOPED_EVIDENCE_REWRITE_FORBIDDEN:{namespace_v}:{scope_v}"
            )
        namespace_store[scope_v] = canonical_payload

    def facts(self, trial_id: str, cycle_index: int) -> tuple[tuple[str, Any], ...]:
        key = (str(trial_id), int(cycle_index))
        flat = tuple(sorted(self._cycles.get(key, {}).items()))
        scoped = tuple(
            (namespace, tuple((scope, scopes[scope]) for scope in sorted(scopes)))
            for namespace, scopes in sorted(self._scoped_cycles.get(key, {}).items())
        )
        return flat + scoped

    def snapshot(self) -> dict[str, dict[str, Any]]:
        keys = sorted(set(self._cycles) | set(self._scoped_cycles))
        return {
            f"{trial}:{cycle}": dict(self.facts(trial, cycle))
            for trial, cycle in keys
        }


class CanonicalEvidenceTraceWriter(TraceWriter):
    """Preserves TraceWriter semantics while adding observational identity facts."""

    def __init__(self, trial_id: str, output_directory, ledger: CanonicalIdentityLedger) -> None:
        super().__init__(trial_id, output_directory, "EVALUATION_TRACE_SCHEMA_V2_CERT_EXEC_IDENTITY_V1")
        self._canonical_ledger = ledger

    def append(self, record: TraceStepRecord) -> None:
        additions = self._canonical_ledger.facts(record.trial_id, record.cycle_index)
        super().append(replace(record, facts=record.facts + additions))
