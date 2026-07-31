#!/usr/bin/env python3
"""Independent raw-depth to frozen ARKit-mesh metric-coordinate audit."""
from __future__ import annotations

import argparse
import csv
import math
from pathlib import Path

import numpy as np
import trimesh
from PIL import Image

from arkitscenes_common import atomic_json, sha256_file


DEPTH_SCALE_M_PER_UNIT = 0.001


def pose(row: dict[str, str]) -> np.ndarray:
    return np.asarray([[float(row[f"c2w_{i}{j}"]) for j in range(4)] for i in range(4)])


def points_for_frame(root: Path, row: dict[str, str], maximum: int = 2048) -> np.ndarray:
    depth = np.asarray(Image.open(root / row["depth"]), dtype=np.float64) * DEPTH_SCALE_M_PER_UNIT
    confidence = np.asarray(Image.open(root / row["confidence"]), dtype=np.uint8)
    mask = (depth > 0.0) & (confidence == 2)
    y, x = np.nonzero(mask)
    if len(x) == 0:
        return np.empty((0, 3))
    step = max(1, math.ceil(len(x) / maximum))
    x, y = x[::step], y[::step]
    z = depth[y, x]
    camera = np.column_stack(((x - float(row["cx"])) * z / float(row["fx"]),
                              (y - float(row["cy"])) * z / float(row["fy"]), z, np.ones_like(z)))
    return (pose(row) @ camera.T).T[:, :3]


def summary(values: np.ndarray) -> dict[str, float]:
    return {"median_m": float(np.median(values)), "p95_m": float(np.percentile(values, 95)),
            "p99_m": float(np.percentile(values, 99)), "max_m": float(np.max(values))}


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--task-root", type=Path, required=True)
    parser.add_argument("--candidate-root", type=Path, required=True)
    parser.add_argument("--video-id", required=True)
    args = parser.parse_args()
    task, root = args.task_root.resolve(), args.candidate_root.resolve()
    manifest = task / "frame_join" / args.video_id / "arkitscenes_joined_frame_manifest.csv"
    with manifest.open(newline="", encoding="utf-8") as handle:
        joined = list(csv.DictReader(handle))
    if len(joined) < 64:
        raise RuntimeError("BLOCKED_BY_ARKITSCENES_DATA_OR_COORDINATE_CONTRACT: fewer than 64 joined frames")
    indices = np.linspace(0, len(joined) - 1, 64, dtype=int)
    chosen = [joined[index] for index in indices]
    mesh_path = root / f"{args.video_id}_3dod_mesh.ply"
    mesh = trimesh.load(mesh_path, process=False, force="mesh")
    if not isinstance(mesh, trimesh.Trimesh) or len(mesh.vertices) == 0 or not np.isfinite(mesh.vertices).all():
        raise RuntimeError("BLOCKED_BY_ARKITSCENES_DATA_OR_COORDINATE_CONTRACT: invalid official ARKit mesh")
    all_distances: list[np.ndarray] = []
    per_frame: list[dict[str, object]] = []
    for row in chosen:
        points = points_for_frame(root, row)
        if len(points) == 0 or not np.isfinite(points).all():
            continue
        _, distances, _ = trimesh.proximity.closest_point(mesh, points)
        distances = np.asarray(distances, dtype=np.float64)
        if not np.isfinite(distances).all():
            continue
        all_distances.append(distances)
        per_frame.append({"timestamp": row["timestamp"], "point_count": int(len(distances)),
                          "median_m": float(np.median(distances)), "p95_m": float(np.percentile(distances, 95))})
    if not all_distances:
        raise RuntimeError("BLOCKED_BY_ARKITSCENES_DATA_OR_COORDINATE_CONTRACT: no finite depth-to-mesh distances")
    distances = np.concatenate(all_distances)
    metric = summary(distances)
    frame_pass_fraction = sum(item["median_m"] <= 0.10 for item in per_frame) / len(per_frame)
    status = "COORDINATE_AUDIT_PASS" if (metric["median_m"] <= 0.05 and metric["p95_m"] <= 0.15 and
                                          metric["p99_m"] <= 0.30 and frame_pass_fraction >= 0.80) else "BLOCKED_BY_ARKITSCENES_DATA_OR_COORDINATE_CONTRACT"
    result = {"status": status, "video_id": args.video_id, "depth_scale_m_per_unit": DEPTH_SCALE_M_PER_UNIT,
              "mesh_sha256": sha256_file(mesh_path), "joined_manifest_sha256": sha256_file(manifest),
              "mesh_vertices": int(len(mesh.vertices)), "mesh_faces": int(len(mesh.faces)),
              "sampled_frames": len(chosen), "finite_distance_frames": len(per_frame), "distance_metrics": metric,
              "frame_median_le_0_10_fraction": frame_pass_fraction,
              "scale_discrepancy_check": "direct 0.001 m/mm raw-depth conversion only; no ICP, Sim3, pose or scale fitting",
              "per_frame": per_frame}
    output = task / "coordinate_audit" / args.video_id
    validation = output / "arkit_mesh_coordinate_validation.json"
    atomic_json(validation, result)
    atomic_json(output / "arkitscenes_coordinate_contract.json", {
        "status": status, "camera_to_world": "official trajectory inverse as frozen in joined manifest",
        "depth_scale_m_per_unit": DEPTH_SCALE_M_PER_UNIT, "mesh_frame": "official ARKit reconstruction mesh",
        "prohibited": ["ICP", "Sim3", "pose_scale_fitting", "automatic_scale_or_center"],
        "validation_sha256": sha256_file(validation),
    })
    print(status, f"median={metric['median_m']:.6f}", f"p95={metric['p95_m']:.6f}", f"p99={metric['p99_m']:.6f}")
    return 0 if status == "COORDINATE_AUDIT_PASS" else 2


if __name__ == "__main__":
    raise SystemExit(main())
