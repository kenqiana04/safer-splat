"""Shared deterministic contracts for frozen historical L2/H1 replay."""
from __future__ import annotations

import csv
import hashlib
import json
import os
from pathlib import Path
from typing import Any, Iterable


TASK_ROOT = Path(__file__).resolve().parent
REPO_ROOT = TASK_ROOT.parents[2]
PR94_HEAD = "9bffdd2db585974ee61684cebfc99229aa52c47c"
PR94_BRANCH = "l2-h1-shadow-certifier-v1"
DT = 0.05
ROBOT_CONTRACT_SHA256 = "5fad9c0773673ead60cd3f5229525d01a8fdf563de070f06dceecff190b8b223"

PR87_ROOT = REPO_ROOT / "reproduction/cross_dataset/resume_replica_gt_executable_safety_activated_benchmark_v1"
PR89_ROOT = REPO_ROOT / "reproduction/cross_dataset/core_v1_cross_environment_activation_portability_audit_v1"
PR90_ROOT = REPO_ROOT / "reproduction/causal_audit/core_v1_representative_shortfall_causal_decomposition_v1"
PR94_ROOT = REPO_ROOT / "reproduction/shadow/l2_h1_shadow_certifier_v1"

MAPS = {
    "E1_REPLICA_GT_FINE": {
        "snapshot_id": "3b318a98a454ec5c36410b3c41dfb3dd4a25b7b5a1899f1f2c939fbf24ad0e55",
        "content_sha256": "3b318a98a454ec5c36410b3c41dfb3dd4a25b7b5a1899f1f2c939fbf24ad0e55",
        "backend_identity": "EXACT_ANALYTIC_SPHERE_SEGMENT_MINIMUM",
        "backend_class": "EXACT_ANALYTIC",
        "primitive_family": "ISOTROPIC_SPHERE",
        "authority_origin": "FROZEN_COMPOSITE_MAP_SNAPSHOT_ID",
    },
    "E5_STONEHENGE_SAFER": {
        "snapshot_id": "ac14f5ced354c93f26cf92404540712eff65bd02554d9e9ed0332508e290382d",
        "content_sha256": "ac14f5ced354c93f26cf92404540712eff65bd02554d9e9ed0332508e290382d",
        "backend_identity": "CONSERVATIVE_SIGNED_DISTANCE_LIPSCHITZ_INTERVAL",
        "backend_class": "CONSERVATIVE_LOWER_BOUND",
        "primitive_family": "ANISOTROPIC_ELLIPSOID",
        "authority_origin": "FROZEN_STATIC_CHECKPOINT_SHA256",
    },
    "E6_FLIGHT_SAFER": {
        "snapshot_id": "8e7499a0d68405065b0effb7022b635ef3fbe50a53b69f5f25165260c8a493e6",
        "content_sha256": "8e7499a0d68405065b0effb7022b635ef3fbe50a53b69f5f25165260c8a493e6",
        "backend_identity": "CONSERVATIVE_SIGNED_DISTANCE_LIPSCHITZ_INTERVAL",
        "backend_class": "CONSERVATIVE_LOWER_BOUND",
        "primitive_family": "ANISOTROPIC_ELLIPSOID",
        "authority_origin": "FROZEN_STATIC_CHECKPOINT_SHA256",
    },
}


def canonical_bytes(value: Any) -> bytes:
    return json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=False, allow_nan=False).encode("utf-8")


def sha256_bytes(value: bytes) -> str:
    return hashlib.sha256(value).hexdigest()


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def atomic_write_bytes(path: Path, payload: bytes) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary = path.with_suffix(path.suffix + ".tmp")
    temporary.write_bytes(payload)
    os.replace(temporary, path)


def write_json(path: Path, value: Any) -> None:
    atomic_write_bytes(path, json.dumps(value, sort_keys=True, indent=2, ensure_ascii=False, allow_nan=False).encode("utf-8") + b"\n")


def write_jsonl(path: Path, rows: Iterable[dict[str, Any]]) -> None:
    payload = b"".join(canonical_bytes(row) + b"\n" for row in rows)
    atomic_write_bytes(path, payload)


def write_csv(path: Path, rows: list[dict[str, Any]], fields: list[str] | None = None) -> None:
    if fields is None:
        fields = []
        for row in rows:
            for key in row:
                if key not in fields:
                    fields.append(key)
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary = path.with_suffix(path.suffix + ".tmp")
    with temporary.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=fields, lineterminator="\n", extrasaction="ignore")
        writer.writeheader()
        writer.writerows(rows)
    os.replace(temporary, path)


def read_csv(path: Path) -> list[dict[str, str]]:
    with path.open("r", encoding="utf-8", newline="") as handle:
        return list(csv.DictReader(handle))


def read_json(path: Path) -> Any:
    return json.loads(path.read_text(encoding="utf-8"))


def parse_json_field(value: str | None) -> Any:
    if value is None or not value.strip():
        return None
    return json.loads(value)


def parse_bool(value: Any) -> bool:
    return str(value).strip().lower() == "true"


def parse_float(value: Any) -> float | None:
    if value is None or str(value).strip() == "":
        return None
    return float(value)


def vector_or_none(value: Any) -> list[float] | None:
    if value is None or value == "":
        return None
    parsed = parse_json_field(value) if isinstance(value, str) else value
    if not isinstance(parsed, list) or len(parsed) != 3:
        return None
    try:
        return [float(item) for item in parsed]
    except (TypeError, ValueError):
        return None


def candidate_numeric_hash(vector: list[float] | None) -> str | None:
    return None if vector is None else sha256_bytes(canonical_bytes(vector))


def stable_row_id(payload: dict[str, Any]) -> str:
    return sha256_bytes(canonical_bytes(payload))


def relative(path: Path) -> str:
    return path.relative_to(REPO_ROOT).as_posix()
