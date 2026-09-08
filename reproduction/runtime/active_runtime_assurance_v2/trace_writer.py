"""Append-only runtime facts and immutable lock; no outcome evaluator."""

from __future__ import annotations

import json
from pathlib import Path

from .runtime_errors import TraceFinalizedError
from .runtime_types import TraceIdentity, TraceStepRecord, TrialTraceLock, canonical_json, canonical_sha256


FORBIDDEN_FACT_KEYS = {"collision", "success", "progress", "outcome", "goal_reached_metric"}


class TraceWriter:
    def __init__(self, trial_id: str, output_directory: Path | None = None, schema_identity: str = "EVALUATION_TRACE_SCHEMA_V2") -> None:
        self.trial_id = str(trial_id)
        self.output_directory = None if output_directory is None else Path(output_directory)
        self.schema_identity = str(schema_identity)
        self._records: list[TraceStepRecord] = []
        self._lock: TrialTraceLock | None = None
        self._records_frozen = False
        self._frozen_lines: tuple[str, ...] | None = None
        self._frozen_trace_sha256: str | None = None
        self._finalization_failure_reason: str | None = None

    @property
    def records(self) -> tuple[TraceStepRecord, ...]:
        return tuple(self._records)

    @property
    def frozen_trace_sha256(self) -> str | None:
        return self._frozen_trace_sha256

    @property
    def finalization_failure_reason(self) -> str | None:
        return self._finalization_failure_reason

    def append(self, record: TraceStepRecord) -> None:
        if self._lock is not None or self._records_frozen:
            raise TraceFinalizedError("TRACE_RECORD_SET_FROZEN")
        if record.trial_id != self.trial_id:
            raise ValueError("TRIAL_IDENTITY_MISMATCH")
        keys = {str(key).lower() for key, _ in record.facts}
        if keys & FORBIDDEN_FACT_KEYS:
            raise ValueError("SCIENTIFIC_OUTCOME_FIELD_FORBIDDEN")
        self._records.append(record)

    def finalize(self) -> TrialTraceLock:
        if self._lock is not None:
            return self._lock
        current_lines = tuple(canonical_json(record) for record in self._records)
        current_sha = canonical_sha256(current_lines)
        if self._records_frozen:
            if current_lines != self._frozen_lines or current_sha != self._frozen_trace_sha256:
                self._finalization_failure_reason = "TRACE_FINALIZATION_RETRY_IDENTITY_MISMATCH"
                raise TraceFinalizedError(self._finalization_failure_reason)
        else:
            self._records_frozen = True
            self._frozen_lines = current_lines
            self._frozen_trace_sha256 = current_sha
        candidate_lock = TrialTraceLock(
            TraceIdentity("trace:sha256:" + current_sha), self.trial_id, len(current_lines),
            current_sha, self.schema_identity, True,
        )
        try:
            self._persist(current_lines, candidate_lock)
        except Exception as exc:
            self._finalization_failure_reason = f"TRACE_FINALIZATION_INCOMPLETE:{type(exc).__name__}"
            raise
        self._lock = candidate_lock
        self._finalization_failure_reason = None
        return candidate_lock

    def _persist(self, lines: tuple[str, ...], candidate_lock: TrialTraceLock) -> None:
        """Perform configured writes; this is not an fsync or crash-durability contract."""
        if self.output_directory is None:
            return
        self.output_directory.mkdir(parents=True, exist_ok=True)
        (self.output_directory / "runtime_trace.jsonl").write_text("".join(line + "\n" for line in lines), encoding="utf-8", newline="\n")
        (self.output_directory / "runtime_trace_lock.json").write_text(
            json.dumps({"identity": candidate_lock.identity.value, "trial_id": candidate_lock.trial_id, "record_count": candidate_lock.record_count, "trace_sha256": candidate_lock.trace_sha256, "schema_identity": candidate_lock.schema_identity, "locked_before_evaluation": True}, indent=2, sort_keys=True) + "\n",
            encoding="utf-8", newline="\n",
        )
