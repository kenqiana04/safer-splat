"""Canonical serialization, hashing, and atomic task-owned writes."""
from __future__ import annotations

import csv
import hashlib
import json
import os
from dataclasses import asdict, is_dataclass
from enum import Enum
from pathlib import Path
from typing import Any, Iterable


def jsonable(value: Any) -> Any:
    try:
        import numpy as np
        if isinstance(value, np.ndarray):
            return value.tolist()
        if isinstance(value, np.generic):
            return value.item()
    except ImportError:
        pass
    if isinstance(value, Enum):
        return value.value
    if is_dataclass(value):
        return jsonable(asdict(value))
    if hasattr(value, "to_dict"):
        return jsonable(value.to_dict())
    if isinstance(value, dict):
        return {str(key): jsonable(item) for key, item in value.items()}
    if isinstance(value, (list, tuple)):
        return [jsonable(item) for item in value]
    return value


def canonical_json_bytes(value: Any) -> bytes:
    return json.dumps(jsonable(value), sort_keys=True, separators=(",", ":"), ensure_ascii=False, allow_nan=False).encode("utf-8")


def sha256_bytes(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def sha256_json(value: Any) -> str:
    return sha256_bytes(canonical_json_bytes(value))


def sha256_file(path: Path | str) -> str:
    digest = hashlib.sha256()
    with Path(path).open("rb") as handle:
        for block in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def atomic_write_bytes(path: Path, data: bytes) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    # A short sibling name keeps Windows task paths below legacy MAX_PATH while
    # retaining same-filesystem atomic replacement semantics.
    temporary = path.parent / f".t{os.getpid()}"
    temporary.write_bytes(data)
    os.replace(temporary, path)


def write_json(path: Path, value: Any) -> None:
    atomic_write_bytes(path, json.dumps(jsonable(value), sort_keys=True, indent=2, ensure_ascii=False, allow_nan=False).encode("utf-8") + b"\n")


def write_text(path: Path, text: str) -> None:
    atomic_write_bytes(path, text.rstrip("\n").encode("utf-8") + b"\n")


def write_csv(path: Path, rows: Iterable[dict[str, Any]], fieldnames: list[str] | None = None) -> None:
    rows = list(rows)
    if fieldnames is None:
        fieldnames = list(rows[0]) if rows else []
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary = path.with_name(path.name + f".tmp.{os.getpid()}")
    with temporary.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=fieldnames, extrasaction="ignore", lineterminator="\n")
        writer.writeheader()
        writer.writerows([{key: json.dumps(jsonable(value), separators=(",", ":"), ensure_ascii=False) if isinstance(value, (dict, list, tuple)) else value for key, value in row.items()} for row in rows])
    os.replace(temporary, path)


def read_json(path: Path | str) -> Any:
    return json.loads(Path(path).read_text(encoding="utf-8"))
