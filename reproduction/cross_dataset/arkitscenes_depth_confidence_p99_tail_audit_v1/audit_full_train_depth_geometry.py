#!/usr/bin/env python3
"""Full 214-frame M0/M1/M2 geometry audit against the official ARKit mesh."""

from __future__ import annotations

import argparse
import json
from pathlib import Path

import numpy as np
import open3d as o3d
import trimesh

from audit_common import (
    MASKS,
    SEED,
    TRAIN_SHA256,
    intrinsics_from_row,
    load_depth_confidence,
    load_manifest,
    pose_from_row,
    quantiles,
    rays_world,
    stable_digest,
    world_points,
    write_csv,
    write_json,
)


RAY_CLASS = {
    0: "NO_MESH_RAY_HIT",
    1: "SENSOR_BEHIND_MESH",
    2: "SENSOR_IN_FRONT_OF_MESH",
    3: "RAY_AGREEMENT",
    4: "POINT_DISTANCE_ONLY_DISAGREEMENT",
}


def build_scene(mesh_path: Path):
    legacy = o3d.io.read_triangle_mesh(str(mesh_path))
    if legacy.is_empty() or len(legacy.triangles) == 0:
        raise RuntimeError("official ARKit mesh is empty")
    scene = o3d.t.geometry.RaycastingScene()
    scene.add_triangles(o3d.t.geometry.TriangleMesh.from_legacy(legacy))
    tri = trimesh.load_mesh(str(mesh_path), process=False)
    if not isinstance(tri, trimesh.Trimesh) or len(tri.faces) == 0:
        raise RuntimeError("independent trimesh loader did not produce a triangle mesh")
    return legacy, scene, tri


def deterministic_engine_points(rows: list[dict[str, str]], asset_root: Path) -> np.ndarray:
    rng = np.random.default_rng(SEED)
    pieces: list[np.ndarray] = []
    for frame_index in np.linspace(0, len(rows) - 1, 16, dtype=int):
        depth, _ = load_depth_confidence(asset_root, rows[int(frame_index)])
        yx = np.argwhere(depth > 0)
        chosen = yx[rng.choice(len(yx), size=32, replace=False)]
        world, _ = world_points(rows[int(frame_index)], chosen[:, 0], chosen[:, 1], depth)
        pieces.append(world)
    return np.concatenate(pieces, axis=0)


def validate_engine(scene, tri: trimesh.Trimesh, points: np.ndarray) -> dict[str, object]:
    o3d_distance = scene.compute_distance(o3d.core.Tensor(points.astype(np.float32))).numpy().astype(np.float64)
    closest, trimesh_distance, primitive = trimesh.proximity.closest_point(tri, points.astype(np.float64))
    recomputed = np.linalg.norm(points.astype(np.float64) - closest, axis=1)
    difference = np.abs(o3d_distance - trimesh_distance)
    result = {
        "status": "PASS_EXACT_POINT_TO_TRIANGLE_SURFACE_DISTANCE",
        "point_count": int(len(points)),
        "primary": "Open3D RaycastingScene.compute_distance point-to-triangle surface distance",
        "independent": "trimesh.proximity.closest_point R-tree triangle query",
        "independent_primitive_count": int(len(np.unique(primitive))),
        "open3d_vs_trimesh_max_abs_difference_m": float(difference.max()),
        "trimesh_reported_vs_recomputed_max_abs_difference_m": float(np.max(np.abs(trimesh_distance - recomputed))),
        "tolerance_m": 1e-6,
        "nearest_vertex_substitution": False,
        "all_finite": bool(np.isfinite(o3d_distance).all() and np.isfinite(trimesh_distance).all()),
    }
    if not result["all_finite"] or result["open3d_vs_trimesh_max_abs_difference_m"] > 1e-6:
        result["status"] = "FAIL_POINT_TO_MESH_ENGINE_VALIDATION"
    result["deterministic_sha256"] = stable_digest({k: v for k, v in result.items() if k != "deterministic_sha256"})
    return result


def classify_ray(sensor_z: np.ndarray, mesh_z: np.ndarray, distance: np.ndarray) -> np.ndarray:
    classes = np.full(sensor_z.shape, 3, dtype=np.uint8)
    no_hit = ~np.isfinite(mesh_z)
    residual = sensor_z - mesh_z
    classes[no_hit] = 0
    classes[(~no_hit) & (residual > 0.10)] = 1
    classes[(~no_hit) & (residual < -0.10)] = 2
    point_only = (~no_hit) & (np.abs(residual) <= 0.10) & (distance > 0.30)
    classes[point_only] = 4
    return classes


def frame_payload(row: dict[str, str], frame_index: int, asset_root: Path, scene) -> tuple[dict[str, np.ndarray], dict[str, float]]:
    depth, confidence = load_depth_confidence(asset_root, row)
    y, x = np.nonzero(depth > 0)
    world, sensor_z = world_points(row, y, x, depth)
    distance = scene.compute_distance(o3d.core.Tensor(world)).numpy().astype(np.float32)
    ray_result = scene.cast_rays(o3d.core.Tensor(rays_world(row, y, x)))
    mesh_z = ray_result["t_hit"].numpy().astype(np.float32)
    ray_class = classify_ray(sensor_z, mesh_z, distance)

    c2w = pose_from_row(row)
    w2c = np.linalg.inv(c2w)
    k = intrinsics_from_row(row)
    sensor_z64 = depth[y, x].astype(np.float64) * 0.001
    camera_exact = np.column_stack(
        ((x - k[0, 2]) * sensor_z64 / k[0, 0], (y - k[1, 2]) * sensor_z64 / k[1, 1], sensor_z64)
    )
    world_exact = (c2w[:3, :3] @ camera_exact.T).T + c2w[:3, 3]
    camera_roundtrip = (w2c[:3, :3] @ world_exact.T).T + w2c[:3, 3]
    u2 = k[0, 0] * camera_roundtrip[:, 0] / camera_roundtrip[:, 2] + k[0, 2]
    v2 = k[1, 1] * camera_roundtrip[:, 1] / camera_roundtrip[:, 2] + k[1, 2]
    reprojection = np.sqrt((u2 - x) ** 2 + (v2 - y) ** 2)
    depth_unit_error = np.max(np.abs(camera_roundtrip[:, 2] - depth[y, x].astype(np.float64) * 0.001))
    payload = {
        "frame_index": np.full(len(x), frame_index, dtype=np.uint16),
        "y": y.astype(np.uint16),
        "x": x.astype(np.uint16),
        "depth_raw": depth[y, x].astype(np.uint16),
        "confidence": confidence[y, x].astype(np.uint8),
        "distance_m": distance,
        "mesh_z_m": mesh_z,
        "ray_class": ray_class,
    }
    checks = {
        "reprojection_max_px": float(reprojection.max()),
        "depth_unit_max_error_m": float(depth_unit_error),
        "nonfinite_distance": int(np.count_nonzero(~np.isfinite(distance))),
        "positive_pixel_count": int(len(x)),
    }
    return payload, checks


def mask_global_metrics(distance: np.ndarray, confidence: np.ndarray, mask_name: str, frame_index: np.ndarray) -> dict[str, object]:
    selection = MASKS[mask_name](confidence)
    values = distance[selection]
    metrics = quantiles(values)
    metrics.update(
        {
            "valid_pixel_count": int(selection.sum()),
            "retained_fraction_vs_m0": float(selection.mean()),
            "fraction_gt_0_10": float(np.mean(values > 0.10)) if values.size else 0.0,
            "fraction_gt_0_20": float(np.mean(values > 0.20)) if values.size else 0.0,
            "fraction_gt_0_30": float(np.mean(values > 0.30)) if values.size else 0.0,
            "fraction_gt_0_50": float(np.mean(values > 0.50)) if values.size else 0.0,
            "top1_percent_pixel_count": int(np.count_nonzero(values >= np.quantile(values, 0.99))) if values.size else 0,
        }
    )
    frame_medians = []
    for idx in range(214):
        frame_values = distance[selection & (frame_index == idx)]
        if frame_values.size:
            frame_medians.append(float(np.median(frame_values)))
    metrics["frames_median_le_0_10_fraction"] = float(np.mean(np.asarray(frame_medians) <= 0.10)) if frame_medians else 0.0
    metrics["geometry_gates"] = {
        "median_le_0_05": metrics["median_m"] <= 0.05,
        "p95_le_0_15": metrics["p95_m"] <= 0.15,
        "p99_le_0_30": metrics["p99_m"] <= 0.30,
        "frames_median_le_0_10_fraction_ge_0_80": metrics["frames_median_le_0_10_fraction"] >= 0.80,
        "nonfinite_zero": metrics["nonfinite"] == 0,
    }
    metrics["geometry_pass"] = all(metrics["geometry_gates"].values())
    return metrics


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--manifest", type=Path, required=True)
    parser.add_argument("--asset-root", type=Path, required=True)
    parser.add_argument("--output-root", type=Path, required=True)
    args = parser.parse_args()
    rows = load_manifest(args.manifest, TRAIN_SHA256, "TRAIN", 214)
    asset_root = args.asset_root.resolve()
    output_root = args.output_root.resolve()
    cache_root = output_root / "tmp" / "full_frame_cache"
    cache_root.mkdir(parents=True, exist_ok=True)
    mesh_path = asset_root / "48018874_3dod_mesh.ply"
    legacy, scene, tri = build_scene(mesh_path)

    engine_points = deterministic_engine_points(rows, asset_root)
    engine = validate_engine(scene, tri, engine_points)
    write_json(output_root / "distance_engine_validation.json", engine)
    if not engine["status"].startswith("PASS"):
        print(engine["status"])
        return 2

    payloads: list[dict[str, np.ndarray]] = []
    frame_checks: list[dict[str, object]] = []
    for index, row in enumerate(rows):
        payload, checks = frame_payload(row, index, asset_root, scene)
        np.savez_compressed(cache_root / f"frame_{index:03d}.npz", **payload)
        payloads.append(payload)
        frame_checks.append({"index": index, "timestamp": row["timestamp"], **checks})
        if index % 20 == 0 or index == len(rows) - 1:
            print(f"GEOMETRY_PROGRESS={index + 1}/{len(rows)}", flush=True)

    arrays = {key: np.concatenate([payload[key] for payload in payloads]) for key in payloads[0]}
    distance = arrays["distance_m"]
    confidence = arrays["confidence"]
    frame_index = arrays["frame_index"]
    global_metrics = {name: mask_global_metrics(distance, confidence, name, frame_index) for name in MASKS}

    m0_threshold = float(np.quantile(distance, 0.99))
    m0_top = distance >= m0_threshold
    per_frame_rows: list[dict[str, object]] = []
    for index, row in enumerate(rows):
        frame_sel = frame_index == index
        m0_count = int(frame_sel.sum())
        frame_top_count = int(np.count_nonzero(frame_sel & m0_top))
        for mask_name in MASKS:
            selected = frame_sel & MASKS[mask_name](confidence)
            values = distance[selected]
            q = quantiles(values)
            conf_frame = confidence[frame_sel]
            per_frame_rows.append(
                {
                    "mask": mask_name,
                    "index": index,
                    "timestamp": row["timestamp"],
                    "keyframe_index": int(row["keyframe_index"]),
                    "group": int(row["v1_group_id"]),
                    "valid_pixel_count": int(selected.sum()),
                    "retained_fraction": float(selected.sum() / m0_count) if m0_count else 0.0,
                    "median_m": q["median_m"],
                    "p90_m": q["p90_m"],
                    "p95_m": q["p95_m"],
                    "p99_m": q["p99_m"],
                    "max_m": q["max_m"],
                    "fraction_gt_0_30": float(np.mean(values > 0.30)) if values.size else 0.0,
                    "global_top1_contribution": float(frame_top_count / np.count_nonzero(m0_top)) if mask_name == "M0_RAW_POSITIVE" else 0.0,
                    "confidence_0_fraction_m0": float(np.mean(conf_frame == 0)) if m0_count else 0.0,
                    "confidence_1_fraction_m0": float(np.mean(conf_frame == 1)) if m0_count else 0.0,
                    "confidence_2_fraction_m0": float(np.mean(conf_frame == 2)) if m0_count else 0.0,
                    "zero_valid_depth": int(selected.sum()) == 0,
                }
            )

    groups = sorted({int(row["v1_group_id"]) for row in rows})
    per_group_rows: list[dict[str, object]] = []
    for group in groups:
        indices = np.asarray([idx for idx, row in enumerate(rows) if int(row["v1_group_id"]) == group], dtype=np.uint16)
        group_sel = np.isin(frame_index, indices)
        m0_count = int(group_sel.sum())
        for mask_name in MASKS:
            selected = group_sel & MASKS[mask_name](confidence)
            values = distance[selected]
            q = quantiles(values)
            valid_frames = sum(1 for idx in indices if np.any(selected & (frame_index == idx)))
            per_group_rows.append(
                {
                    "mask": mask_name,
                    "group": group,
                    "frame_count": int(len(indices)),
                    "frame_coverage": float(valid_frames / len(indices)),
                    "valid_pixel_count": int(selected.sum()),
                    "retained_fraction": float(selected.sum() / m0_count) if m0_count else 0.0,
                    "median_m": q["median_m"],
                    "p95_m": q["p95_m"],
                    "p99_m": q["p99_m"],
                    "zero_valid_frame_count": int(len(indices) - valid_frames),
                }
            )

    per_frame_fields = list(per_frame_rows[0].keys())
    per_group_fields = list(per_group_rows[0].keys())
    write_csv(output_root / "full_train_per_frame_metrics.csv", per_frame_fields, per_frame_rows)
    write_csv(output_root / "full_train_per_group_metrics.csv", per_group_fields, per_group_rows)
    cache_records = [
        {
            "index": i,
            "path": str((cache_root / f"frame_{i:03d}.npz").relative_to(output_root)),
            "positive_pixels": int(frame_checks[i]["positive_pixel_count"]),
        }
        for i in range(len(rows))
    ]
    registry = {
        "status": "PASS_SHARED_FULL_PIXEL_REGISTRY",
        "mode": "FULL_ALL_POSITIVE_DEPTH_PIXELS",
        "sampling_seed_if_needed": SEED,
        "sampling_used": False,
        "per_frame_cap_if_sampling": 16384,
        "all_masks_share_identical_m0_registry": True,
        "frame_count": len(rows),
        "positive_pixel_count": int(len(distance)),
        "cache_records": cache_records,
        "cache_not_for_git": True,
    }
    registry["deterministic_sha256"] = stable_digest({k: v for k, v in registry.items() if k != "deterministic_sha256"})
    write_json(output_root / "shared_pixel_registry.json", registry)
    result = {
        "status": "PASS_FULL_TRAIN_M0_M1_M2_GEOMETRY_AUDIT",
        "scene": "48018874",
        "frame_count": len(rows),
        "evaluation_mode": registry["mode"],
        "official_mesh_vertices": int(len(legacy.vertices)),
        "official_mesh_triangles": int(len(legacy.triangles)),
        "global": global_metrics,
        "m0_top1_threshold_m": m0_threshold,
        "reprojection_max_px": float(max(record["reprojection_max_px"] for record in frame_checks)),
        "depth_unit_max_error_m": float(max(record["depth_unit_max_error_m"] for record in frame_checks)),
        "nonfinite": int(sum(record["nonfinite_distance"] for record in frame_checks)),
        "frame_checks": frame_checks,
        "ray_class_names": RAY_CLASS,
    }
    if result["reprojection_max_px"] > 1e-5 or result["depth_unit_max_error_m"] > 1e-6 or result["nonfinite"] != 0:
        result["status"] = "FAIL_FULL_TRAIN_GEOMETRY_IMPLEMENTATION_CHECK"
    result["deterministic_sha256"] = stable_digest({k: v for k, v in result.items() if k not in {"deterministic_sha256", "frame_checks"}})
    write_json(output_root / "full_train_mask_metrics.json", result)
    print(result["status"])
    print("DETERMINISTIC_SHA256=" + result["deterministic_sha256"])
    for name, metrics in global_metrics.items():
        print(name, metrics["valid_pixel_count"], metrics["median_m"], metrics["p95_m"], metrics["p99_m"], metrics["max_m"])
    return 0 if result["status"].startswith("PASS") else 2


if __name__ == "__main__":
    raise SystemExit(main())
