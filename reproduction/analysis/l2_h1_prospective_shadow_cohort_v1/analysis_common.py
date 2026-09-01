#!/usr/bin/env python3
"""Deterministic helpers for the locked formal scientific analysis."""

from __future__ import annotations

import hashlib
import json
import os
import tempfile
from pathlib import Path
from typing import Any, Iterable, Iterator

DATA_ROLE = "FORMAL_PROSPECTIVE_SHADOW_COHORT_V1"
EXPECTED_PR101_HEAD = "fbd4f3744e8b6d0448644c00cd8fdb1e8295902d"
PROTOCOL_SHA256 = "e8ea8f3fda15ab81664829ea6f71fcb37f772ad613c13f61007856c16117791a"
EXECUTION_LOCK_SHA256 = "5e20a3f0504205e8d65b91033638c5af0909ed741212a04539dcfb37eda08fe2"
COLLECTION_LOCK_SHA256 = "c30adc48099e8d7b90c980d84389cc1fa693cc1f87d3fc519089efb7cb81b756"
RAW_MANIFEST_SHA256 = "d474496716c97f9f8d1596d9cca40983796d06d537b00a8cb4739546d85b8d19"
RESULT_COMMITMENT_FILE_SHA256 = "3beb36d3e409483fa38b9a112e6070098309734045c3d7aae560e54ccd7b3ca2"
ORDERED_RESULT_COMMITMENT_SHA256 = "1f5061412b266a9e58ba35f868734cb5b8478b02cf11b1af0c794be5850e3bff"
MAP_AUTHORITY_ID = "65c2e4a5ccfd71a0fa8d633c207397215dd8206d5f8fb77a731c05bcb0109af3"
TRI_STATES = ("PASS", "FAIL", "UNKNOWN")


def canonical_json_bytes(value: Any) -> bytes:
    return json.dumps(value, ensure_ascii=False, allow_nan=False, sort_keys=True, separators=(",", ":")).encode("utf-8")


def semantic_sha256(value: Any) -> str:
    return hashlib.sha256(canonical_json_bytes(value)).hexdigest()


def file_sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for block in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def load_json(path: Path) -> Any:
    return json.loads(path.read_text(encoding="utf-8"))


def iter_jsonl(path: Path) -> Iterator[dict[str, Any]]:
    with path.open("r", encoding="utf-8") as handle:
        for number, line in enumerate(handle, 1):
            if not line.strip():
                continue
            value = json.loads(line)
            if not isinstance(value, dict):
                raise ValueError(f"{path}:{number}: expected object")
            yield value


def atomic_write_json(path: Path, value: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    payload = json.dumps(value, ensure_ascii=False, allow_nan=False, indent=2, sort_keys=True) + "\n"
    fd, temporary = tempfile.mkstemp(prefix=f".{path.name}.", suffix=".tmp", dir=path.parent)
    try:
        with os.fdopen(fd, "w", encoding="utf-8", newline="\n") as handle:
            handle.write(payload)
            handle.flush()
            os.fsync(handle.fileno())
        os.replace(temporary, path)
    finally:
        if os.path.exists(temporary):
            os.unlink(temporary)


def write_jsonl(path: Path, rows: Iterable[dict[str, Any]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8", newline="\n") as handle:
        for row in rows:
            handle.write(json.dumps(row, ensure_ascii=False, allow_nan=False, sort_keys=True, separators=(",", ":")) + "\n")


def percentile(values: list[float], probability: float) -> float | None:
    if not values:
        return None
    ordered = sorted(float(value) for value in values)
    if len(ordered) == 1:
        return ordered[0]
    position = (len(ordered) - 1) * probability
    lower = int(position)
    upper = min(lower + 1, len(ordered) - 1)
    weight = position - lower
    return ordered[lower] * (1.0 - weight) + ordered[upper] * weight

