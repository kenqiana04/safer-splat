#!/usr/bin/env python3
from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path

import numpy as np
from scipy.spatial import cKDTree
import trimesh


def query_union(tree: cKDTree, points: np.ndarray, radius: float) -> tuple[float, int]:
    maximum = 0.0
    uncovered = 0
    for start in range(0, len(points), 200_000):
        dist, _ = tree.query(points[start:start + 200_000], workers=-1)
        residual = np.maximum(0.0, dist - radius)
        maximum = max(maximum, float(residual.max(initial=0.0)))
        uncovered += int(np.count_nonzero(residual > 1e-6))
    return maximum, uncovered


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--mesh", type=Path, required=True)
    parser.add_argument("--map-dir", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    summary = json.loads((args.map_dir / "profile_build_summary.json").read_text(encoding="utf-8"))
    raw = summary["raw"]
    centers = np.load(args.map_dir / "means_world_m.npy", mmap_mode="r")
    radius = float(raw["sphere_scale_m"])
    tree = cKDTree(centers)
    mesh = trimesh.load(args.mesh, process=False, maintain_order=True)
    vertices = np.asarray(mesh.vertices, dtype=np.float64)
    faces = np.asarray(mesh.faces, dtype=np.int64)
    tri = vertices[faces]
    values: dict[str, dict[str, float | int]] = {}
    mx, miss = query_union(tree, vertices, radius); values["all_triangle_vertices"] = {"max_distance_m": mx, "uncovered_count": miss}
    for label, points in (("all_triangle_centroids", tri.mean(axis=1)), ("all_edge_midpoints_01", .5*(tri[:,0]+tri[:,1])), ("all_edge_midpoints_12", .5*(tri[:,1]+tri[:,2])), ("all_edge_midpoints_20", .5*(tri[:,2]+tri[:,0]))):
        mx, miss = query_union(tree, points, radius); values[label] = {"max_distance_m": mx, "uncovered_count": miss}
    areas = 0.5 * np.linalg.norm(np.cross(tri[:,1]-tri[:,0], tri[:,2]-tri[:,0]), axis=1)
    rng = np.random.default_rng(20260729); choose = rng.choice(len(faces), size=1_000_000, replace=True, p=areas/areas.sum())
    r1 = np.sqrt(rng.random(len(choose))); r2 = rng.random(len(choose)); sample_tri = tri[choose]
    sample = (1-r1)[:,None]*sample_tri[:,0] + (r1*(1-r2))[:,None]*sample_tri[:,1] + (r1*r2)[:,None]*sample_tri[:,2]
    mx, miss = query_union(tree, sample, radius); values["area_weighted_mesh_points_1000000"] = {"max_distance_m": mx, "uncovered_count": miss}
    uncovered = int(sum(int(x["uncovered_count"]) for x in values.values()))
    result = {"status": "PASS" if raw["source_primitive_loss"] == 0 and uncovered == 0 else "FAIL", "profile": summary["profile"], "coverage_argument": "Every closed mesh primitive intersects a closed voxel and each voxel is contained in its Gaussian sphere.", "source_primitive_loss": raw["source_primitive_loss"], "checks": values, "total_uncovered_count": uncovered, "seed": 20260729}
    args.output.write_text(json.dumps(result, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(result["status"])
    return 0 if result["status"] == "PASS" else 1


if __name__ == "__main__":
    raise SystemExit(main())
