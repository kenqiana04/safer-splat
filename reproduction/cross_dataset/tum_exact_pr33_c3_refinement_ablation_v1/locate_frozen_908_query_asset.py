"""Reconstruct the immutable 908-point static SAFER query order.

This is the generator preserved by the later C3 static audit.  It is used here
only to reconstruct the PR #32 point order: all 300 TUM camera centres,
30 fixed camera indices with six signed axis offsets, a 4x4x4 camera-bounds
grid, and four V1R6-map out-of-bounds probes.  It does not select points from
the E3 result or inspect query values.
"""
from __future__ import annotations

import hashlib
import json
from pathlib import Path
from typing import Any

import numpy as np


def sha256_bytes(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def build_frozen_908_points(transforms_path: Path, reference_map_bbox_min: np.ndarray, reference_map_bbox_max: np.ndarray) -> tuple[np.ndarray, list[dict[str, Any]]]:
    """Return the fixed PR #32 order as float32 world-coordinate points."""
    transforms = json.loads(transforms_path.read_text(encoding="utf-8"))
    cameras = np.asarray([frame["transform_matrix"] for frame in transforms["frames"]], dtype=np.float32)[:, :3, 3]
    records: list[dict[str, Any]] = []
    for index, point in enumerate(cameras):
        records.append({"kind": "camera", "source_index": index, "point": point.copy()})
    for index in np.linspace(0, len(cameras) - 1, 30, dtype=int):
        for axis in range(3):
            for magnitude in (0.05, 0.10, 0.20):
                for sign in (-1.0, 1.0):
                    point = cameras[index].copy()
                    point[axis] += sign * magnitude
                    records.append({"kind": "offset", "source_index": int(index), "axis": axis, "magnitude": magnitude, "sign": sign, "point": point})
    grid_axes = [np.linspace(cameras[:, dim].min(), cameras[:, dim].max(), 4, dtype=np.float32) for dim in range(3)]
    for point in np.stack(np.meshgrid(*grid_axes, indexing="ij"), axis=-1).reshape(-1, 3):
        records.append({"kind": "grid", "source_index": -1, "point": point.astype(np.float32, copy=False)})
    extent = reference_map_bbox_max - reference_map_bbox_min
    for signs in ((-1, -1, -1), (-1, 1, 1), (1, -1, 1), (1, 1, -1)):
        point = np.where(np.asarray(signs, dtype=np.int8) < 0, reference_map_bbox_min - 0.10 * extent, reference_map_bbox_max + 0.10 * extent).astype(np.float32)
        records.append({"kind": "out_of_map", "source_index": -1, "signs": list(signs), "point": point})
    points = np.stack([record["point"] for record in records]).astype(np.float32, copy=False)
    if points.shape != (908, 3):
        raise RuntimeError(f"FROZEN_908_QUERY_COUNT_MISMATCH:{points.shape}")
    return points, records


def identity_summary(points: np.ndarray, records: list[dict[str, Any]]) -> dict[str, Any]:
    return {
        "point_count": int(points.shape[0]),
        "shape": list(points.shape),
        "dtype": str(points.dtype),
        "coordinate_frame": "Nerfstudio world coordinates; no axis conversion or E3-dependent rescaling",
        "sha256_float32_c_order": sha256_bytes(np.ascontiguousarray(points).tobytes()),
        "min": points.min(axis=0).astype(float).tolist(),
        "max": points.max(axis=0).astype(float).tolist(),
        "kind_counts": {kind: sum(record["kind"] == kind for record in records) for kind in ("camera", "offset", "grid", "out_of_map")},
        "contains_camera_scene_fixed_probes": True,
        "order_contract": "300 camera centres; fixed np.linspace(0,299,30,dtype=int) axis offsets; C-order 4x4x4 grid; signed out-of-map probes",
    }
