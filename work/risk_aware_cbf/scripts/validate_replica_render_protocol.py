#!/usr/bin/env python3
"""Perform static checks before an external formal camera manifest is created."""
import argparse
import csv
import json
import math
from pathlib import Path

import numpy as np


def write_csv(path, rows, fields=None):
    with path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=fields or list(rows[0]))
        writer.writeheader()
        writer.writerows(rows)


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--protocol", type=Path, required=True)
    parser.add_argument("--preregistration", type=Path, required=True)
    parser.add_argument("--pose-conversion", type=Path, required=True)
    parser.add_argument("--formal-output", type=Path, required=True)
    parser.add_argument("--manifest", type=Path)
    parser.add_argument("--out", type=Path, required=True)
    args = parser.parse_args()
    protocol = args.protocol.read_text(encoding="utf-8") if args.protocol.is_file() else ""
    prereg = list(csv.DictReader(args.preregistration.open(encoding="utf-8"))) if args.preregistration.is_file() else []
    pose = json.loads(args.pose_conversion.read_text(encoding="utf-8")) if args.pose_conversion.is_file() else {}
    row = prereg[0] if prereg else {}
    checks = [
        ("protocol_file_exists", args.protocol.is_file(), str(args.protocol)),
        ("scene_fixed", row.get("scene") == "apartment_0", row.get("scene", "")),
        ("all_seeds_fixed", all(row.get(k) == "20260715" for k in ("random_seed", "numpy_seed", "python_random_seed", "habitat_pathfinder_seed")), "20260715"),
        ("spatial_locations_fixed", row.get("spatial_location_target") == "100", row.get("spatial_location_target", "")),
        ("yaw_order_fixed", row.get("yaw_offsets_deg") == "0;-60;60", row.get("yaw_offsets_deg", "")),
        ("sensor_complete", all(token in protocol for token in ("width `640`", "height `480`", "HFOV `90`", "near `0.05`", "far `20.0`")), "protocol literals"),
        ("height_fixed", row.get("camera_height") == "1.50", row.get("camera_height", "")),
        ("navmesh_fixed", row.get("navmesh") == "official_habitat_mesh_semantic.navmesh", row.get("navmesh", "")),
        ("pose_conversion_complete", bool(pose.get("T_nerfstudio_from_habitat_camera") and pose.get("T_habitat_from_nerfstudio_camera")), "matrix pair"),
        ("formal_output_empty", not args.formal_output.exists() or not any(args.formal_output.iterdir()), str(args.formal_output)),
        ("no_performance_parameters", "performance-driven" not in protocol.lower(), "protocol review"),
    ]
    rows = [{"check": name, "passed": passed, "detail": detail} for name, passed, detail in checks]
    args.out.mkdir(parents=True, exist_ok=True)
    write_csv(args.out / "protocol_contract_checks.csv", rows)
    protocol_passed = all(item[1] for item in checks)
    if args.manifest:
        manifest_rows = list(csv.DictReader(args.manifest.open(encoding="utf-8")))
        expected_ids = [f"frame_{index:04d}" for index in range(300)]
        finite = True
        rotations_ok = True
        quaternions_ok = True
        inverse_ok = True
        height_ok = True
        positions = []
        for item in manifest_rows:
            try:
                matrix = np.array([[float(item[f"c2w_{r}{c}"]) for c in range(4)] for r in range(4)])
                rotation = matrix[:3, :3]
                quat = np.array([float(item[key]) for key in ("quat_x", "quat_y", "quat_z", "quat_w")])
                source = np.array([float(item[key]) for key in ("source_navmesh_point_x", "source_navmesh_point_y", "source_navmesh_point_z")])
                finite &= bool(np.isfinite(matrix).all() and np.isfinite(quat).all() and np.isfinite(source).all())
                rotations_ok &= abs(float(np.linalg.det(rotation)) - 1.0) < 1e-6 and float(np.max(np.abs(rotation.T @ rotation - np.eye(3)))) < 1e-6
                quaternions_ok &= abs(float(np.linalg.norm(quat)) - 1.0) < 1e-6
                inverse_ok &= float(np.max(np.abs(matrix @ np.linalg.inv(matrix) - np.eye(4)))) < 1e-8
                height_ok &= float(np.max(np.abs(matrix[:3, 3] - (source + np.array([0.0, 1.5, 0.0]))))) < 1e-6
                positions.append(source)
            except (KeyError, ValueError, np.linalg.LinAlgError):
                finite = rotations_ok = quaternions_ok = inverse_ok = height_ok = False
        unique_positions = len({tuple(np.round(point, 8)) for point in positions})
        yaw_slots = all(sorted(int(item["yaw_slot"]) for item in manifest_rows if int(item["position_index"]) == index) == [0, 1, 2] for index in range(100))
        train_count = sum(item.get("split") == "train" for item in manifest_rows)
        eval_count = sum(item.get("split") == "eval" for item in manifest_rows)
        metadata_path = args.manifest.parent / "manifest_metadata.json"
        metadata = json.loads(metadata_path.read_text(encoding="utf-8")) if metadata_path.is_file() else {}
        path_spacing = float(metadata.get("path_length", float("nan"))) / 99.0
        manifest_checks = [
            ("formal_rows", len(manifest_rows) == 300, str(len(manifest_rows))),
            ("ordered_unique_frame_ids", [item.get("frame_id") for item in manifest_rows] == expected_ids, "frame_0000_to_frame_0299"),
            ("unique_spatial_positions", unique_positions == 100, str(unique_positions)),
            ("three_yaw_slots_per_position", yaw_slots, "0_1_2"),
            ("train_eval_counts", train_count == 270 and eval_count == 30, f"train={train_count};eval={eval_count}"),
            ("all_values_finite", finite, "matrix_quaternion_source"),
            ("quaternion_norms", quaternions_ok, "unit"),
            ("rotation_matrices", rotations_ok, "det_and_orthogonality"),
            ("forward_inverse_contract", inverse_ok, "c2w_times_w2c"),
            ("camera_height_offset", height_ok, "1.50_on_plus_Y"),
            ("spatial_path_min_spacing", math.isfinite(path_spacing) and path_spacing >= 0.10 - 1e-6, str(path_spacing)),
        ]
        write_csv(args.out / "camera_manifest_contract_checks.csv", [{"check": name, "passed": passed, "detail": detail} for name, passed, detail in manifest_checks])
        write_csv(args.out / "camera_trajectory_statistics.csv", [{"formal_rows": len(manifest_rows), "unique_spatial_positions": unique_positions, "train_frames": train_count, "eval_frames": eval_count, "uniform_path_arclength_spacing": path_spacing}])
        manifest_passed = all(item[1] for item in manifest_checks)
        print("camera_manifest_contract_passed=" + str(manifest_passed).lower())
    else:
        manifest_passed = True
    print("protocol_contract_passed=" + str(protocol_passed).lower())
    if not protocol_passed or not manifest_passed:
        raise SystemExit(1)


if __name__ == "__main__":
    main()
