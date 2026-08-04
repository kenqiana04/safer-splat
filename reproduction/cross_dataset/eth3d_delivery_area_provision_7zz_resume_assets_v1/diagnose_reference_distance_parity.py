#!/usr/bin/env python3
"""Diagnose coordinate-conditioning effects without changing frozen queries."""

from __future__ import annotations

import hashlib
import json
from pathlib import Path

import numpy as np
import open3d as o3d
import trimesh

from audit_reference_geometry import load_trimesh
from task_config import QUARANTINE, TASK_ROOT


SEED = 20260804


def scene_for(vertices: np.ndarray, faces: np.ndarray, dtype) -> o3d.t.geometry.RaycastingScene:
    vertex_tensor = o3d.core.Tensor(vertices, dtype=dtype)
    face_tensor = o3d.core.Tensor(faces.astype(np.uint32), dtype=o3d.core.Dtype.UInt32)
    mesh = o3d.t.geometry.TriangleMesh(vertex_tensor, face_tensor)
    scene = o3d.t.geometry.RaycastingScene()
    scene.add_triangles(mesh)
    return scene


def main() -> None:
    surface = QUARANTINE / "delivery_area_rig_occlusion" / "delivery_area" / "occlusion" / "surface_mesh.ply"
    mesh = load_trimesh(surface)
    vertices = np.asarray(mesh.vertices, dtype=np.float64)
    faces = np.asarray(mesh.faces, dtype=np.int64)
    rng = np.random.default_rng(SEED)
    indices = rng.choice(len(mesh.faces), size=256, replace=False)
    triangles = np.asarray(mesh.triangles)[indices]
    centroids = triangles.mean(axis=1)
    normals = np.asarray(mesh.face_normals)[indices]
    offsets = np.linspace(0.002, 0.020, 256, dtype=np.float64)
    queries = centroids + normals * offsets[:, None]
    _, expected, _ = trimesh.proximity.closest_point(mesh, queries)
    query_sha = hashlib.sha256(queries.astype("<f8").tobytes()).hexdigest()
    variants = []
    for label, origin in (
        ("global_float32", np.zeros(3, dtype=np.float64)),
        ("bounds_centered_float32", np.asarray(mesh.bounds, dtype=np.float64).mean(axis=0)),
        ("first_query_centered_float32", queries[0]),
    ):
        scene = scene_for((vertices - origin).astype(np.float32), faces, o3d.core.Dtype.Float32)
        actual = scene.compute_distance(
            o3d.core.Tensor((queries - origin).astype(np.float32), dtype=o3d.core.Dtype.Float32)
        ).numpy().astype(np.float64)
        delta = np.abs(expected - actual)
        variants.append({
            "label": label,
            "origin_m": origin.tolist(),
            "maximum_absolute_difference_m": float(delta.max()),
            "mean_absolute_difference_m": float(delta.mean()),
        })
    try:
        scene = scene_for(vertices, faces, o3d.core.Dtype.Float64)
        actual = scene.compute_distance(
            o3d.core.Tensor(queries, dtype=o3d.core.Dtype.Float64)
        ).numpy().astype(np.float64)
        delta = np.abs(expected - actual)
        variants.append({
            "label": "global_float64",
            "maximum_absolute_difference_m": float(delta.max()),
            "mean_absolute_difference_m": float(delta.mean()),
        })
    except Exception as exc:
        variants.append({"label": "global_float64", "unsupported": True, "error": repr(exc)})
    record = {
        "status": "DIAGNOSTIC_ONLY_FROZEN_QUERY_AND_TOLERANCE_UNCHANGED",
        "query_sha256": query_sha,
        "query_count": 256,
        "tolerance_m": 1e-6,
        "variants": variants,
    }
    path = TASK_ROOT / "reference" / "reference_distance_conditioning_diagnostic.json"
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(record, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(json.dumps(record, sort_keys=True))


if __name__ == "__main__":
    main()
