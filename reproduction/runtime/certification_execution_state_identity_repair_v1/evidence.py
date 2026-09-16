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

    def record(self, trial_id: str, cycle_index: int, **facts: Any) -> None:
        key = (str(trial_id), int(cycle_index))
        current = self._cycles.setdefault(key, {})
        for name, value in facts.items():
            if name in current and current[name] != value:
                raise RuntimeError(f"CANONICAL_EVIDENCE_REWRITE_FORBIDDEN:{name}")
            current[name] = value

    def facts(self, trial_id: str, cycle_index: int) -> tuple[tuple[str, Any], ...]:
        return tuple(sorted(self._cycles.get((str(trial_id), int(cycle_index)), {}).items()))

    def snapshot(self) -> dict[str, dict[str, Any]]:
        return {f"{trial}:{cycle}": dict(values) for (trial, cycle), values in sorted(self._cycles.items())}


class CanonicalEvidenceTraceWriter(TraceWriter):
    """Preserves TraceWriter semantics while adding observational identity facts."""

    def __init__(self, trial_id: str, output_directory, ledger: CanonicalIdentityLedger) -> None:
        super().__init__(trial_id, output_directory, "EVALUATION_TRACE_SCHEMA_V2_CERT_EXEC_IDENTITY_V1")
        self._canonical_ledger = ledger

    def append(self, record: TraceStepRecord) -> None:
        additions = self._canonical_ledger.facts(record.trial_id, record.cycle_index)
        super().append(replace(record, facts=record.facts + additions))
