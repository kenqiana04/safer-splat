"""Shared immutable-data helpers for the ARKitScenes depth-confidence audit."""

from __future__ import annotations

import csv
import ctypes
import hashlib
import json
from pathlib import Path
from typing import Iterable

import imageio.v2 as imageio
import numpy as np


SCENE = "48018874"
SEED = 20260730
TRAIN_SHA256 = "167066916ce1a3281ac754dfdeec37ada9f5b0e31227c731c94cebb698a2a6e3"
HELDOUT_SHA256 = "7b65f741e901690f2a723579d75200eebe7b9e77b0cd57c030d4a14d0474c0c7"
MASKS = {
    "M0_RAW_POSITIVE": lambda confidence: np.ones(confidence.shape, dtype=bool),
    "M1_CONFIDENCE_GE1": lambda confidence: confidence >= 1,
    "M2_CONFIDENCE_EQ2": lambda confidence: confidence == 2,
}
GEOMETRY_GATES = {"median_m": 0.05, "p95_m": 0.15, "p99_m": 0.30}
NO_EXECUTION = {
    "download": 0,
    "environment_creation": 0,
    "environment_modification": 0,
    "smoke": 0,
    "mapper": 0,
    "optimizer_step": 0,
    "training": 0,
    "checkpoint": 0,
    "map": 0,
    "nvs": 0,
    "learned_map_clearance": 0,
    "g0": 0,
    "variant": 0,
    "controller": 0,
}


def sha256_bytes(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def stable_digest(value: object) -> str:
    return sha256_bytes(json.dumps(value, sort_keys=True, separators=(",", ":"), allow_nan=False).encode("utf-8"))


def write_json(path: Path, value: object) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(value, indent=2, sort_keys=True, allow_nan=False) + "\n", encoding="utf-8")


def load_manifest(path: Path, expected_sha256: str, expected_split: str, expected_count: int) -> list[dict[str, str]]:
    data = path.read_bytes()
    if sha256_bytes(data) != expected_sha256:
        raise RuntimeError(f"noncanonical raw-byte manifest: {path}")
    rows = list(csv.DictReader(data.decode("utf-8").splitlines()))
    if len(rows) != expected_count:
        raise RuntimeError(f"unexpected {expected_split} row count: {len(rows)}")
    if any(row["video_id"] != SCENE or row["split"] != expected_split for row in rows):
        raise RuntimeError(f"scene/split contamination in {path}")
    return rows


def under(root: Path, relative: str) -> Path:
    candidate = (root / relative).resolve()
    try:
        candidate.relative_to(root.resolve())
    except ValueError as exc:
        raise RuntimeError(f"path escapes immutable asset root: {relative}") from exc
    if not candidate.is_file():
        raise FileNotFoundError(candidate)
    return candidate


def load_depth_confidence(asset_root: Path, row: dict[str, str]) -> tuple[np.ndarray, np.ndarray]:
    depth = np.asarray(imageio.imread(under(asset_root, row["depth"])))
    confidence = np.asarray(imageio.imread(under(asset_root, row["confidence"])))
    expected = (int(row["height"]), int(row["width"]))
    if depth.shape != expected or confidence.shape != expected:
        raise RuntimeError(f"depth/confidence shape mismatch for {row['timestamp']}: {depth.shape}/{confidence.shape}/{expected}")
    return depth, confidence


def pose_from_row(row: dict[str, str]) -> np.ndarray:
    pose = np.array([[float(row[f"c2w_{r}{c}"]) for c in range(4)] for r in range(4)], dtype=np.float64)
    if not np.isfinite(pose).all() or not np.allclose(pose[3], [0, 0, 0, 1], atol=1e-8):
        raise RuntimeError(f"invalid C2W for {row['timestamp']}")
    return pose


def intrinsics_from_row(row: dict[str, str]) -> np.ndarray:
    return np.array(
        [[float(row["fx"]), 0.0, float(row["cx"])], [0.0, float(row["fy"]), float(row["cy"])], [0.0, 0.0, 1.0]],
        dtype=np.float64,
    )


def world_points(row: dict[str, str], y: np.ndarray, x: np.ndarray, depth_raw: np.ndarray) -> tuple[np.ndarray, np.ndarray]:
    z = depth_raw[y, x].astype(np.float64) * 0.001
    k = intrinsics_from_row(row)
    camera = np.column_stack(((x - k[0, 2]) * z / k[0, 0], (y - k[1, 2]) * z / k[1, 1], z))
    c2w = pose_from_row(row)
    world = (c2w[:3, :3] @ camera.T).T + c2w[:3, 3]
    return world.astype(np.float32), z.astype(np.float32)


def rays_world(row: dict[str, str], y: np.ndarray, x: np.ndarray) -> np.ndarray:
    k = intrinsics_from_row(row)
    c2w = pose_from_row(row)
    directions_camera = np.column_stack(((x - k[0, 2]) / k[0, 0], (y - k[1, 2]) / k[1, 1], np.ones(len(x))))
    directions_world = (c2w[:3, :3] @ directions_camera.T).T
    origins = np.repeat(c2w[None, :3, 3], len(x), axis=0)
    return np.column_stack((origins, directions_world)).astype(np.float32)


def quantiles(values: np.ndarray) -> dict[str, float | int]:
    finite = np.isfinite(values)
    clean = values[finite]
    if clean.size == 0:
        return {
            "count": 0,
            "median_m": 0.0,
            "p90_m": 0.0,
            "p95_m": 0.0,
            "p99_m": 0.0,
            "max_m": 0.0,
            "nonfinite": int(values.size),
        }
    return {
        "count": int(clean.size),
        "median_m": float(np.quantile(clean, 0.50)),
        "p90_m": float(np.quantile(clean, 0.90)),
        "p95_m": float(np.quantile(clean, 0.95)),
        "p99_m": float(np.quantile(clean, 0.99)),
        "max_m": float(clean.max()),
        "nonfinite": int(values.size - clean.size),
    }


def write_csv(path: Path, fieldnames: list[str], rows: Iterable[dict[str, object]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=fieldnames, lineterminator="\n")
        writer.writeheader()
        writer.writerows(rows)


def zstd_compress(data: bytes, level: int = 9) -> bytes:
    """Compress with the system libzstd without modifying the frozen environment."""
    lib = ctypes.CDLL("libzstd.so")
    lib.ZSTD_compressBound.argtypes = [ctypes.c_size_t]
    lib.ZSTD_compressBound.restype = ctypes.c_size_t
    lib.ZSTD_compress.argtypes = [ctypes.c_void_p, ctypes.c_size_t, ctypes.c_void_p, ctypes.c_size_t, ctypes.c_int]
    lib.ZSTD_compress.restype = ctypes.c_size_t
    lib.ZSTD_isError.argtypes = [ctypes.c_size_t]
    lib.ZSTD_isError.restype = ctypes.c_uint
    lib.ZSTD_getErrorName.argtypes = [ctypes.c_size_t]
    lib.ZSTD_getErrorName.restype = ctypes.c_char_p
    source = ctypes.create_string_buffer(data)
    capacity = lib.ZSTD_compressBound(len(data))
    destination = ctypes.create_string_buffer(capacity)
    size = lib.ZSTD_compress(destination, capacity, source, len(data), level)
    if lib.ZSTD_isError(size):
        raise RuntimeError(lib.ZSTD_getErrorName(size).decode("utf-8"))
    return destination.raw[:size]
