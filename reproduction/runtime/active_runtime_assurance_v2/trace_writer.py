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

    @property
    def records(self) -> tuple[TraceStepRecord, ...]:
        return tuple(self._records)

    def append(self, record: TraceStepRecord) -> None:
        if self._lock is not None:
            raise TraceFinalizedError("TRACE_ALREADY_FINALIZED")
        if record.trial_id != self.trial_id:
            raise ValueError("TRIAL_IDENTITY_MISMATCH")
        keys = {str(key).lower() for key, _ in record.facts}
        if keys & FORBIDDEN_FACT_KEYS:
            raise ValueError("SCIENTIFIC_OUTCOME_FIELD_FORBIDDEN")
        self._records.append(record)

    def finalize(self) -> TrialTraceLock:
        if self._lock is not None:
            return self._lock
        lines = [canonical_json(record) for record in self._records]
        trace_sha = canonical_sha256(tuple(lines))
        self._lock = TrialTraceLock(TraceIdentity("trace:sha256:" + trace_sha), self.trial_id, len(lines), trace_sha, self.schema_identity, True)
        if self.output_directory is not None:
            self.output_directory.mkdir(parents=True, exist_ok=True)
            (self.output_directory / "runtime_trace.jsonl").write_text("".join(line + "\n" for line in lines), encoding="utf-8", newline="\n")
            (self.output_directory / "runtime_trace_lock.json").write_text(json.dumps({"identity": self._lock.identity.value, "trial_id": self._lock.trial_id, "record_count": self._lock.record_count, "trace_sha256": self._lock.trace_sha256, "schema_identity": self._lock.schema_identity, "locked_before_evaluation": True}, indent=2, sort_keys=True) + "\n", encoding="utf-8", newline="\n")
        return self._lock
