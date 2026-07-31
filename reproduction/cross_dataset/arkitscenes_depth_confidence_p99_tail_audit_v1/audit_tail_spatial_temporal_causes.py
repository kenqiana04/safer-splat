#!/usr/bin/env python3
"""Official-pose temporal attribution and evidence-only root-cause labelling."""

from __future__ import annotations

import argparse
import math
from pathlib import Path

import imageio.v2 as imageio
import numpy as np

from audit_common import TRAIN_SHA256, intrinsics_from_row, load_depth_confidence, load_manifest, pose_from_row, under, world_points, write_csv, write_json


def motion(previous: dict[str, str], current: dict[str, str]) -> dict[str, float]:
    a = pose_from_row(previous)
    b = pose_from_row(current)
    relative = np.linalg.inv(a) @ b
    cos_angle = np.clip((np.trace(relative[:3, :3]) - 1.0) / 2.0, -1.0, 1.0)
    return {
        "translation_m": float(np.linalg.norm(relative[:3, 3])),
        "rotation_deg": float(np.degrees(np.arccos(cos_angle))),
    }


def neighbor_evidence(
    current_index: int,
    neighbor_index: int,
    rows: list[dict[str, str]],
    asset_root: Path,
    y: np.ndarray,
    x: np.ndarray,
    depth: np.ndarray,
    rng: np.random.Generator,
) -> dict[str, object]:
    if len(y) > 4096:
        chosen = rng.choice(len(y), size=4096, replace=False)
        y = y[chosen]
        x = x[chosen]
    world, _ = world_points(rows[current_index], y, x, depth)
    w2c = np.linalg.inv(pose_from_row(rows[neighbor_index]))
    camera = (w2c[:3, :3] @ world.astype(np.float64).T).T + w2c[:3, 3]
    k = intrinsics_from_row(rows[neighbor_index])
    projected_x = np.rint(k[0, 0] * camera[:, 0] / camera[:, 2] + k[0, 2]).astype(int)
    projected_y = np.rint(k[1, 1] * camera[:, 1] / camera[:, 2] + k[1, 2]).astype(int)
    neighbor_depth, _ = load_depth_confidence(asset_root, rows[neighbor_index])
    in_view = (
        (camera[:, 2] > 0)
        & (projected_x >= 0)
        & (projected_x < neighbor_depth.shape[1])
        & (projected_y >= 0)
        & (projected_y < neighbor_depth.shape[0])
    )
    valid_indices = np.flatnonzero(in_view)
    sampled_neighbor_depth = np.zeros(len(camera), dtype=np.float64)
    sampled_neighbor_depth[valid_indices] = neighbor_depth[projected_y[valid_indices], projected_x[valid_indices]].astype(np.float64) * 0.001
    valid = in_view & (sampled_neighbor_depth > 0)
    residual = sampled_neighbor_depth[valid] - camera[valid, 2]
    rgb_difference = None
    if np.any(valid):
        rgb_current = np.asarray(imageio.imread(under(asset_root, rows[current_index]["rgb"]))).astype(np.float64) / 255.0
        rgb_neighbor = np.asarray(imageio.imread(under(asset_root, rows[neighbor_index]["rgb"]))).astype(np.float64) / 255.0
        source_rgb = rgb_current[y[valid], x[valid], :3]
        target_rgb = rgb_neighbor[projected_y[valid], projected_x[valid], :3]
        rgb_difference = float(np.mean(np.abs(source_rgb - target_rgb)))
    return {
        "neighbor_index": neighbor_index,
        "neighbor_timestamp": rows[neighbor_index]["timestamp"],
        "sampled_tail_pixels": int(len(y)),
        "valid_reprojection_count": int(valid.sum()),
        "supported_count": int(np.count_nonzero(np.abs(residual) <= 0.10)),
        "occlusion_ambiguous_count": int(np.count_nonzero(residual < -0.10)),
        "inconsistent_count": int(np.count_nonzero(residual > 0.10)),
        "median_abs_depth_residual_m": float(np.median(np.abs(residual))) if residual.size else None,
        "rgb_mean_abs_difference": rgb_difference,
    }


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--manifest", type=Path, required=True)
    parser.add_argument("--asset-root", type=Path, required=True)
    parser.add_argument("--cache-root", type=Path, required=True)
    parser.add_argument("--concentration", type=Path, required=True)
    parser.add_argument("--output-root", type=Path, required=True)
    args = parser.parse_args()
    rows = load_manifest(args.manifest, TRAIN_SHA256, "TRAIN", 214)
    concentration = __import__("json").loads(args.concentration.read_text(encoding="utf-8"))
    top20 = [int(value) for value in concentration["top20_frames_by_gt_030"]]
    rng = np.random.default_rng(20260730)
    temporal_rows: list[dict[str, object]] = []
    cause_rows: list[dict[str, object]] = []
    for index in top20:
        data = np.load(args.cache_root / f"frame_{index:03d}.npz")
        distance = data["distance_m"].astype(np.float64)
        tail = distance > 0.30
        y = data["y"][tail].astype(int)
        x = data["x"][tail].astype(int)
        depth, confidence_image = load_depth_confidence(args.asset_root.resolve(), rows[index])
        conf = data["confidence"][tail]
        ray = data["ray_class"][tail]
        border = np.minimum.reduce([x / 256.0, (255 - x) / 256.0, y / 192.0, (191 - y) / 192.0])
        depth_values = data["depth_raw"][tail].astype(np.float64) * 0.001
        neighbors = [candidate for candidate in (index - 2, index - 1, index + 1, index + 2) if 0 <= candidate < len(rows)]
        evidences = [neighbor_evidence(index, candidate, rows, args.asset_root.resolve(), y, x, depth, rng) for candidate in neighbors]
        valid = sum(int(item["valid_reprojection_count"]) for item in evidences)
        supported = sum(int(item["supported_count"]) for item in evidences)
        occlusion = sum(int(item["occlusion_ambiguous_count"]) for item in evidences)
        inconsistent = sum(int(item["inconsistent_count"]) for item in evidences)
        if valid == 0:
            category = "NO_NEIGHBOR_SUPPORT"
        elif supported / valid >= 0.25:
            category = "TEMPORALLY_SUPPORTED"
        elif occlusion / valid >= 0.50:
            category = "OCCLUSION_AMBIGUOUS"
        else:
            category = "TEMPORALLY_INCONSISTENT"
        rgb_values = [item["rgb_mean_abs_difference"] for item in evidences if item["rgb_mean_abs_difference"] is not None]
        motion_record = motion(rows[max(0, index - 1)], rows[index]) if index > 0 else {"translation_m": 0.0, "rotation_deg": 0.0}
        temporal_rows.append(
            {
                "frame_index": index,
                "timestamp": rows[index]["timestamp"],
                "group": int(rows[index]["v1_group_id"]),
                "tail_pixel_count": int(tail.sum()),
                "category": category,
                "valid_reprojection_count": valid,
                "supported_fraction": float(supported / valid) if valid else 0.0,
                "occlusion_ambiguous_fraction": float(occlusion / valid) if valid else 0.0,
                "inconsistent_fraction": float(inconsistent / valid) if valid else 0.0,
                "rgb_temporal_mean_abs_difference": float(np.mean(rgb_values)) if rgb_values else None,
                "motion_translation_m": motion_record["translation_m"],
                "motion_rotation_deg": motion_record["rotation_deg"],
                "neighbor_evidence": evidences,
            }
        )
        labels = []
        if np.mean(conf == 0) >= 0.50:
            labels.append("CONFIDENCE_ZERO_OR_LOW")
        if np.mean(ray == 0) >= 0.50:
            labels.append("MESH_COVERAGE_GAP")
        if np.mean(ray == 1) >= 0.25:
            labels.append("SENSOR_BEHIND_MESH")
        if np.mean(ray == 2) >= 0.25:
            labels.append("SENSOR_IN_FRONT_OF_MESH")
        if np.mean(border <= 0.10) >= 0.50:
            labels.append("IMAGE_BORDER")
        if np.mean(depth_values > 4.0) >= 0.50:
            labels.append("LONG_RANGE")
        if category == "TEMPORALLY_INCONSISTENT":
            labels.append("TEMPORAL_INCONSISTENCY")
        if np.mean(ray == 4) >= 0.20:
            labels.append("POSE_INTRINSICS_LOCAL_SUSPECT")
        rgb_temporal = float(np.mean(rgb_values)) if rgb_values else 0.0
        if category == "TEMPORALLY_INCONSISTENT" and rgb_temporal > 0.15:
            labels.append("DYNAMIC_OR_TRANSIENT_SUSPECT")
        if not labels:
            labels.append("UNEXPLAINED")
        cause_rows.append(
            {
                "frame_index": index,
                "timestamp": rows[index]["timestamp"],
                "group": int(rows[index]["v1_group_id"]),
                "tail_pixel_count": int(tail.sum()),
                "tail_confidence_0_fraction": float(np.mean(conf == 0)),
                "tail_no_mesh_hit_fraction": float(np.mean(ray == 0)),
                "tail_sensor_behind_fraction": float(np.mean(ray == 1)),
                "tail_sensor_in_front_fraction": float(np.mean(ray == 2)),
                "tail_border_le_10pct_fraction": float(np.mean(border <= 0.10)),
                "tail_depth_gt_4m_fraction": float(np.mean(depth_values > 4.0)),
                "temporal_category": category,
                "rgb_temporal_mean_abs_difference": rgb_temporal,
                "labels": ";".join(labels),
            }
        )
    temporal_summary = {
        "status": "PASS_TOP20_OFFICIAL_POSE_TEMPORAL_ATTRIBUTION",
        "top_frame_count": len(temporal_rows),
        "category_counts": {
            category: sum(row["category"] == category for row in temporal_rows)
            for category in ("TEMPORALLY_SUPPORTED", "TEMPORALLY_INCONSISTENT", "OCCLUSION_AMBIGUOUS", "NO_NEIGHBOR_SUPPORT")
        },
        "no_pose_optimization": True,
        "heldout_used": False,
    }
    cause_summary = {
        "status": "PASS_EVIDENCE_BOUNDED_TAIL_CAUSE_REGISTRY",
        "top_frame_count": len(cause_rows),
        "label_frame_counts": {
            label: sum(label in row["labels"].split(";") for row in cause_rows)
            for label in (
                "CONFIDENCE_ZERO_OR_LOW",
                "CONFIDENCE_ALIGNMENT_SUSPECT",
                "CONFIDENCE_READER_FAILURE",
                "MESH_COVERAGE_GAP",
                "SENSOR_BEHIND_MESH",
                "SENSOR_IN_FRONT_OF_MESH",
                "IMAGE_BORDER",
                "LONG_RANGE",
                "TEMPORAL_INCONSISTENCY",
                "POSE_INTRINSICS_LOCAL_SUSPECT",
                "DYNAMIC_OR_TRANSIENT_SUSPECT",
                "UNEXPLAINED",
            )
        },
        "dynamic_claim_rule": "suspect label only when temporal inconsistency and RGB temporal mean absolute difference >0.15",
    }
    fields = [key for key in temporal_rows[0].keys() if key != "neighbor_evidence"]
    write_csv(args.output_root / "tail_temporal_frame_registry.csv", fields, [{k: row[k] for k in fields} for row in temporal_rows])
    write_json(args.output_root / "tail_temporal_consistency.json", {"summary": temporal_summary, "frames": temporal_rows})
    write_csv(args.output_root / "tail_cause_registry.csv", list(cause_rows[0].keys()), cause_rows)
    write_json(args.output_root / "tail_cause_summary.json", cause_summary)

    index = 78
    data = np.load(args.cache_root / f"frame_{index:03d}.npz")
    tail = data["distance_m"] > 0.30
    index78 = {
        "frame_index": index,
        "timestamp": rows[index]["timestamp"],
        "group": int(rows[index]["v1_group_id"]),
        "positive_depth_pixels": int(len(data["distance_m"])),
        "confidence_counts": {str(value): int(np.count_nonzero(data["confidence"] == value)) for value in (0, 1, 2)},
        "distance_median_m": float(np.median(data["distance_m"])),
        "distance_p95_m": float(np.quantile(data["distance_m"], 0.95)),
        "distance_p99_m": float(np.quantile(data["distance_m"], 0.99)),
        "distance_max_m": float(np.max(data["distance_m"])),
        "tail_gt_030_fraction": float(np.mean(tail)),
        "tail_no_mesh_hit_fraction": float(np.mean(data["ray_class"][tail] == 0)) if np.any(tail) else 0.0,
        "tail_sensor_behind_fraction": float(np.mean(data["ray_class"][tail] == 1)) if np.any(tail) else 0.0,
        "tail_sensor_in_front_fraction": float(np.mean(data["ray_class"][tail] == 2)) if np.any(tail) else 0.0,
        "frame_deleted": False,
    }
    write_json(args.output_root / "index_78_evidence.json", index78)
    print(temporal_summary["status"])
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
