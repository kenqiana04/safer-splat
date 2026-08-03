#!/usr/bin/env python3
"""Freeze deterministic HELDOUT, clearance, and static-G0 evaluation inputs."""

from __future__ import annotations

import argparse
import csv
import hashlib
import json
from pathlib import Path

import imageio.v2 as imageio
import numpy as np
import open3d as o3d


SEED = 20260730


def sha(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def rows(path: Path) -> list[dict[str, str]]:
    with path.open("r", encoding="utf-8", newline="") as handle:
        return list(csv.DictReader(handle))


def pose(row: dict[str, str]) -> np.ndarray:
    return np.array([[float(row[f"c2w_{i}{j}"]) for j in range(4)] for i in range(4)], dtype=np.float64)


def asset(root: Path, relative: str) -> Path:
    path = (root / relative).resolve()
    path.relative_to(root.resolve())
    if not path.is_file():
        raise FileNotFoundError(path)
    return path


def ray_points(records: list[dict[str, str]], root: Path, world_from_apple: np.ndarray, rng: np.random.Generator, *, per_frame: int, free: bool) -> np.ndarray:
    result: list[np.ndarray] = []
    for row in records:
        depth = np.asarray(imageio.imread(asset(root, row["depth"])), dtype=np.float64) / 1000.0
        confidence = np.asarray(imageio.imread(asset(root, row["confidence"])))
        valid = np.argwhere((depth > 0) & (confidence >= 1))
        if len(valid) == 0:
            continue
        choice = valid[rng.choice(len(valid), size=min(per_frame, len(valid)), replace=False)]
        y, x = choice[:, 0], choice[:, 1]
        z_surface = depth[y, x]
        if free:
            upper = np.maximum(0.06, z_surface - 0.15)
            z = rng.uniform(0.05, 1.0, len(choice)) * upper
        else:
            z = z_surface
        fx, fy, cx, cy = (float(row[key]) for key in ("fx", "fy", "cx", "cy"))
        camera = np.column_stack(((x - cx) / fx * z, (y - cy) / fy * z, z, np.ones(len(z))))
        apple = (pose(row) @ camera.T).T
        relative = (world_from_apple @ apple.T).T[:, :3]
        result.append(relative)
    return np.concatenate(result, axis=0) if result else np.empty((0, 3), dtype=np.float64)


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--train", type=Path, required=True)
    parser.add_argument("--heldout", type=Path, required=True)
    parser.add_argument("--asset-root", type=Path, required=True)
    parser.add_argument("--mesh", type=Path, required=True)
    parser.add_argument("--output-dir", type=Path, required=True)
    args = parser.parse_args()
    train, heldout = rows(args.train), rows(args.heldout)
    if len(train) != 214 or len(heldout) != 53:
        raise RuntimeError("frozen split row count changed")
    rng = np.random.default_rng(SEED)
    world_from_apple = np.linalg.inv(pose(train[0]))

    mesh = o3d.io.read_triangle_mesh(str(args.mesh))
    if mesh.is_empty():
        raise RuntimeError("Apple authority mesh unavailable")
    mesh.transform(world_from_apple)
    mesh.compute_triangle_normals()
    tensor_mesh = o3d.t.geometry.TriangleMesh.from_legacy(mesh)
    scene = o3d.t.geometry.RaycastingScene()
    scene.add_triangles(tensor_mesh)

    o3d.utility.random.seed(SEED)
    surface = np.asarray(mesh.sample_points_uniformly(number_of_points=70000).points, dtype=np.float64)
    normals_pc = mesh.sample_points_uniformly(number_of_points=70000, use_triangle_normal=True)
    # Keep point/normal correspondence from one deterministic sample call.
    surface = np.asarray(normals_pc.points, dtype=np.float64)
    normals = np.asarray(normals_pc.normals, dtype=np.float64)
    offsets = rng.uniform(-0.25, 0.25, len(surface))
    near = surface + normals * offsets[:, None]
    near_distance = np.asarray(scene.compute_distance(o3d.core.Tensor(near.astype(np.float32))).numpy(), dtype=np.float64)
    near = near[near_distance <= 0.250001][:60000]
    if len(near) < 60000:
        raise RuntimeError("insufficient deterministic near-surface samples")
    near_distance = np.asarray(scene.compute_distance(o3d.core.Tensor(near.astype(np.float32))).numpy(), dtype=np.float64)

    free_candidates = ray_points(train, args.asset_root, world_from_apple, rng, per_frame=420, free=True)
    free_distance = np.asarray(scene.compute_distance(o3d.core.Tensor(free_candidates.astype(np.float32))).numpy(), dtype=np.float64)
    free_points = free_candidates[free_distance >= 0.11]
    if len(free_points) < 60000:
        low, high = np.asarray(mesh.get_axis_aligned_bounding_box().min_bound), np.asarray(mesh.get_axis_aligned_bounding_box().max_bound)
        uniform = rng.uniform(low, high, size=(240000, 3))
        uniform_distance = np.asarray(scene.compute_distance(o3d.core.Tensor(uniform.astype(np.float32))).numpy(), dtype=np.float64)
        free_points = np.concatenate((free_points, uniform[uniform_distance >= 0.25]), axis=0)
    free_points = free_points[:60000]
    if len(free_points) < 60000:
        raise RuntimeError("insufficient deterministic free-space samples")

    heldout_rays = ray_points(heldout, args.asset_root, world_from_apple, rng, per_frame=566, free=False)[:30000]
    camera_centres = np.stack([(world_from_apple @ pose(row))[:3, 3] for row in heldout], axis=0)
    hard = np.concatenate((near[np.argsort(np.abs(near_distance[:len(near)] - 0.11))[:2048]], camera_centres), axis=0)

    points = np.concatenate((free_points, near, heldout_rays, hard), axis=0)
    classes = np.concatenate((
        np.full(len(free_points), 0, dtype=np.int16),
        np.full(len(near), 1, dtype=np.int16),
        np.full(len(heldout_rays), 2, dtype=np.int16),
        np.full(len(hard), 3, dtype=np.int16),
    ))
    rounded = np.round(points, 7)
    _, unique = np.unique(rounded, axis=0, return_index=True)
    unique = np.sort(unique)
    points, classes = points[unique], classes[unique]
    if len(points) < 120000:
        raise RuntimeError("deduplicated clearance registry below 120000")

    args.output_dir.mkdir(parents=True, exist_ok=True)
    registry = args.output_dir / "clearance_registry.npz"
    np.savez(registry, points_m=points.astype(np.float64), class_code=classes,
             class_names=np.array(["free_space", "mesh_near_surface_0_0p25m", "heldout_rays", "hard_state"]))

    selected: list[int] = []
    for code in range(4):
        candidates = np.flatnonzero(classes == code)
        selected.extend(candidates[np.linspace(0, len(candidates) - 1, 64, dtype=int)].tolist())
    g0_points = points[np.array(selected[:256], dtype=np.int64)]
    g0 = args.output_dir / "g0_query_registry.npz"
    np.savez(g0, points_m=g0_points.astype(np.float64), source_index=np.array(selected[:256], dtype=np.int64),
             radius_m=np.array([0.10]), epsilon_base_m=np.array([0.01]))
    spec = {
        "status": "PASS_PREMAPPING_EVALUATION_REGISTRY_FREEZE",
        "seed": SEED,
        "coordinate_frame": "SplaTAM metric world: inv(first TRAIN Apple C2W) @ Apple world",
        "world_from_apple": world_from_apple.tolist(),
        "heldout_manifest_sha256": sha(args.heldout),
        "heldout_frame_count": len(heldout),
        "heldout_invisible_to_mapper": True,
        "depth_primary": "GT_depth>0 and confidence>=1",
        "depth_secondary": "GT_depth>0 and confidence==2 (report only)",
        "gaussian_depth": "camera-z alpha-composited expected depth; opacity>=0.5 valid; no fill",
        "depth_gates": {"coverage_min": 0.95, "absrel_max": 0.20, "delta1_min": 0.75, "median_ratio_min": 0.80, "median_ratio_max": 1.25, "nonfinite_max": 0},
        "clearance_counts": {"free_space": int((classes == 0).sum()), "near_surface": int((classes == 1).sum()), "heldout_rays": int((classes == 2).sum()), "hard": int((classes == 3).sum()), "total_deduplicated": len(points)},
        "clearance_registry_sha256": sha(registry),
        "g0_query_count": 256,
        "g0_registry_sha256": sha(g0),
        "mesh_sha256": sha(args.mesh),
        "controller_count": 0,
    }
    (args.output_dir / "registry_freeze.json").write_text(json.dumps(spec, indent=2, sort_keys=True) + "\n", encoding="utf-8", newline="\n")
    print(spec["status"])


if __name__ == "__main__":
    main()
