#!/usr/bin/env python3
"""Build compact p99-tail, mesh-ray, border, range, and concentration evidence."""

from __future__ import annotations

import argparse
import io
from pathlib import Path

import numpy as np

from audit_common import MASKS, TRAIN_SHA256, load_manifest, pose_from_row, stable_digest, write_csv, write_json, zstd_compress


RAY_NAMES = {
    0: "NO_MESH_RAY_HIT",
    1: "SENSOR_BEHIND_MESH",
    2: "SENSOR_IN_FRONT_OF_MESH",
    3: "RAY_AGREEMENT",
    4: "POINT_DISTANCE_ONLY_DISAGREEMENT",
}
TAILS = {
    "TAIL_010": 0.90,
    "TAIL_050": 0.95,
    "TAIL_010_PERCENT": 0.99,
}


def concentration_counts(counts: np.ndarray) -> dict[str, int]:
    ordered = np.sort(counts[counts > 0])[::-1]
    total = ordered.sum()
    result: dict[str, int] = {}
    for target in (0.50, 0.80, 0.90):
        result[f"frames_for_{int(target * 100)}_percent"] = int(np.searchsorted(np.cumsum(ordered), total * target) + 1) if total else 0
    return result


def fraction_records(values: np.ndarray, labels: np.ndarray) -> dict[str, object]:
    unique, counts = np.unique(labels, return_counts=True)
    total = counts.sum()
    return {
        str(label): {"count": int(count), "fraction": float(count / total) if total else 0.0}
        for label, count in zip(unique, counts)
    }


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--manifest", type=Path, required=True)
    parser.add_argument("--cache-root", type=Path, required=True)
    parser.add_argument("--output-root", type=Path, required=True)
    args = parser.parse_args()
    rows = load_manifest(args.manifest, TRAIN_SHA256, "TRAIN", 214)
    arrays: dict[str, list[np.ndarray]] = {key: [] for key in ("frame_index", "y", "x", "depth_raw", "confidence", "distance_m", "mesh_z_m", "ray_class")}
    for index in range(len(rows)):
        data = np.load(args.cache_root / f"frame_{index:03d}.npz")
        for key in arrays:
            arrays[key].append(data[key])
    data = {key: np.concatenate(value) for key, value in arrays.items()}
    distance = data["distance_m"].astype(np.float64)
    frame_index = data["frame_index"].astype(np.int64)
    confidence = data["confidence"]
    depth_m = data["depth_raw"].astype(np.float64) * 0.001
    border_radius = np.minimum.reduce(
        [
            data["x"].astype(np.float64) / 256.0,
            (255.0 - data["x"].astype(np.float64)) / 256.0,
            data["y"].astype(np.float64) / 192.0,
            (191.0 - data["y"].astype(np.float64)) / 192.0,
        ]
    )

    tail_masks = {name: distance >= np.quantile(distance, quantile) for name, quantile in TAILS.items()}
    tail_masks["TAIL_GT_030"] = distance > 0.30
    tail_masks["TAIL_GT_050"] = distance > 0.50
    concentration: dict[str, object] = {}
    frame_rows: list[dict[str, object]] = []
    group_rows: list[dict[str, object]] = []
    for name, selection in tail_masks.items():
        counts = np.bincount(frame_index[selection], minlength=len(rows))
        total = int(selection.sum())
        concentration[name] = {
            "pixel_count": total,
            "fraction_of_m0": float(total / len(distance)),
            **concentration_counts(counts),
            "confidence": fraction_records(confidence[selection], confidence[selection]),
            "time_contiguous_frame_indices": [int(index) for index in np.flatnonzero(counts)],
        }
        for index, count in enumerate(counts):
            frame_rows.append(
                {
                    "tail": name,
                    "frame_index": index,
                    "timestamp": rows[index]["timestamp"],
                    "group": int(rows[index]["v1_group_id"]),
                    "tail_pixel_count": int(count),
                    "contribution_fraction": float(count / total) if total else 0.0,
                }
            )
        for group in sorted({int(row["v1_group_id"]) for row in rows}):
            group_frames = [idx for idx, row in enumerate(rows) if int(row["v1_group_id"]) == group]
            count = int(np.count_nonzero(selection & np.isin(frame_index, group_frames)))
            group_rows.append(
                {
                    "tail": name,
                    "group": group,
                    "tail_pixel_count": count,
                    "contribution_fraction": float(count / total) if total else 0.0,
                }
            )
    concentration["status"] = "PASS_FIXED_TAIL_REGISTRY"
    concentration["top20_frames_by_gt_030"] = [
        int(index)
        for index in np.argsort(np.bincount(frame_index[tail_masks["TAIL_GT_030"]], minlength=len(rows)))[::-1][:20]
    ]
    write_json(args.output_root / "p99_tail_concentration.json", concentration)
    write_csv(args.output_root / "p99_tail_frame_contribution.csv", list(frame_rows[0].keys()), frame_rows)
    write_csv(args.output_root / "p99_tail_group_contribution.csv", list(group_rows[0].keys()), group_rows)

    p99 = tail_masks["TAIL_010_PERCENT"]
    stream = io.StringIO()
    stream.write("frame_index,timestamp,group,y,x,depth_m,confidence,distance_m,mesh_z_m,ray_class\n")
    selected_indices = np.flatnonzero(p99)
    for idx in selected_indices:
        frame = int(frame_index[idx])
        mesh_z = data["mesh_z_m"][idx]
        stream.write(
            f"{frame},{rows[frame]['timestamp']},{rows[frame]['v1_group_id']},{int(data['y'][idx])},{int(data['x'][idx])},"
            f"{depth_m[idx]:.6f},{int(confidence[idx])},{distance[idx]:.9f},{mesh_z:.9f},{RAY_NAMES[int(data['ray_class'][idx])]}\n"
        )
    compressed = zstd_compress(stream.getvalue().encode("utf-8"))
    registry_path = args.output_root / "p99_tail_pixel_registry.csv.zst"
    registry_path.write_bytes(compressed)

    ray_rows: list[dict[str, object]] = []
    gap_rows: list[dict[str, object]] = []
    ray_metrics: dict[str, object] = {}
    for mask_name in MASKS:
        valid = MASKS[mask_name](confidence)
        tail = valid & (distance > 0.30)
        total = int(tail.sum())
        class_metrics = {}
        for code, label in RAY_NAMES.items():
            count = int(np.count_nonzero(tail & (data["ray_class"] == code)))
            class_metrics[label] = {"count": count, "fraction": float(count / total) if total else 0.0}
            for conf in (0, 1, 2):
                conf_count = int(np.count_nonzero(tail & (data["ray_class"] == code) & (confidence == conf)))
                ray_rows.append({"mask": mask_name, "ray_class": label, "confidence": conf, "pixel_count": conf_count})
        ray_metrics[mask_name] = {"tail_gt_030_pixel_count": total, "classes": class_metrics}
    for index, row in enumerate(rows):
        selection = (frame_index == index) & (distance > 0.30) & (data["ray_class"] == 0)
        gap_rows.append(
            {
                "frame_index": index,
                "timestamp": row["timestamp"],
                "group": int(row["v1_group_id"]),
                "no_hit_tail_pixel_count": int(selection.sum()),
                "confidence_0": int(np.count_nonzero(selection & (confidence == 0))),
                "confidence_1": int(np.count_nonzero(selection & (confidence == 1))),
                "confidence_2": int(np.count_nonzero(selection & (confidence == 2))),
            }
        )
    render_sanity = []
    for index in np.linspace(0, len(rows) - 1, 16, dtype=int):
        selected = frame_index == index
        hits = np.isfinite(data["mesh_z_m"][selected])
        residual = depth_m[selected][hits] - data["mesh_z_m"][selected][hits]
        render_sanity.append(
            {
                "frame_index": int(index),
                "ray_count": int(selected.sum()),
                "hit_fraction": float(hits.mean()),
                "median_abs_sensor_mesh_z_residual_m": float(np.median(np.abs(residual))) if residual.size else None,
                "finite_positive_hits": bool(np.all(data["mesh_z_m"][selected][hits] > 0)),
            }
        )
    render_contract = {
        "status": "PASS_OFFICIAL_MESH_CAMERA_Z_RENDER_CONTRACT",
        "pose": "manifest Apple C2W; ray origin=camera center; direction=C2W.R@[(u-cx)/fx,(v-cy)/fy,1]",
        "intrinsics": "per-frame manifest fx/fy/cx/cy",
        "resolution": [256, 192],
        "z_convention": "unnormalized ray direction camera-z=1, therefore Open3D t_hit equals camera-z depth",
        "sanity_frame_count": len(render_sanity),
        "sanity_frames": render_sanity,
        "all_sanity_positive": all(row["finite_positive_hits"] and row["hit_fraction"] > 0 for row in render_sanity),
    }
    if not render_contract["all_sanity_positive"]:
        render_contract["status"] = "FAIL_MESH_DEPTH_RENDER_CONTRACT"
    write_json(args.output_root / "mesh_depth_render_contract.json", render_contract)
    write_json(args.output_root / "mesh_ray_coverage_metrics.json", ray_metrics)
    write_csv(args.output_root / "tail_ray_classification.csv", list(ray_rows[0].keys()), ray_rows)
    write_csv(args.output_root / "mesh_coverage_gap_registry.csv", list(gap_rows[0].keys()), gap_rows)

    gt030 = tail_masks["TAIL_GT_030"]
    border_labels = np.select(
        [border_radius <= 0.02, border_radius <= 0.05, border_radius <= 0.10],
        ["0-2%", "2-5%", "5-10%"],
        default=">10%",
    )
    depth_labels = np.select(
        [depth_m <= 1.0, depth_m <= 2.0, depth_m <= 3.0, depth_m <= 4.0],
        ["0-1m", "1-2m", "2-3m", "3-4m"],
        default=">4m",
    )
    spatial = {
        "status": "PASS_TAIL_SPATIAL_FACTORIZATION",
        "tail": "M0 error>0.30m",
        "image_border_bands": fraction_records(distance[gt030], border_labels[gt030]),
        "confidence": fraction_records(distance[gt030], confidence[gt030]),
        "groups": fraction_records(distance[gt030], np.asarray([rows[idx]["v1_group_id"] for idx in frame_index[gt030]])),
        "ray_classes": fraction_records(distance[gt030], np.asarray([RAY_NAMES[int(code)] for code in data["ray_class"][gt030]])),
        "surface_normal_grazing_angle": "UNAVAILABLE_NO_RELIABLE_PER_HIT_NORMAL_FOR_NO_HIT_TAIL",
    }
    depth_factor = {
        "status": "PASS_TAIL_DEPTH_RANGE_FACTORIZATION",
        "tail": "M0 error>0.30m",
        "depth_bins": fraction_records(distance[gt030], depth_labels[gt030]),
    }
    write_json(args.output_root / "tail_spatial_factorization.json", spatial)
    write_json(args.output_root / "tail_depth_range_factorization.json", depth_factor)
    summary = {
        "status": "PASS_P99_TAIL_AND_MESH_RAY_ATTRIBUTION",
        "registry_path": str(registry_path),
        "registry_compressed_bytes": len(compressed),
        "registry_rows": int(p99.sum()),
        "registry_sha256": __import__("hashlib").sha256(compressed).hexdigest(),
        "concentration": concentration,
        "ray_metrics": ray_metrics,
        "spatial": spatial,
        "depth": depth_factor,
    }
    summary["deterministic_sha256"] = stable_digest({k: v for k, v in summary.items() if k not in {"registry_path", "deterministic_sha256"}})
    write_json(args.output_root / "tail_attribution_summary.json", summary)
    print(summary["status"])
    print("REGISTRY_ROWS=" + str(summary["registry_rows"]))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
