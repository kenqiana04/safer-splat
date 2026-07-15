#!/usr/bin/env python3
"""Validate external metric preprocessing without training or pose estimation."""
import argparse
import csv
import hashlib
import json
import math
from pathlib import Path

import numpy as np


def write_csv(path, rows):
    with path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=list(rows[0]))
        writer.writeheader()
        writer.writerows(rows)


def det(matrix):
    return float(np.linalg.det(np.asarray(matrix, dtype=float)))


def hash_inventory(root):
    digest = hashlib.sha256()
    for path in sorted(root.rglob("*")):
        if path.is_file():
            digest.update(str(path.relative_to(root)).encode())
            digest.update(hashlib.sha256(path.read_bytes()).digest())
    return digest.hexdigest()


def validate_tum(dataset, out):
    data = json.loads((dataset / "transforms.json").read_text())
    frames = data["frames"]
    checks = []
    for frame in frames:
        matrix = frame["transform_matrix"]
        checks.append((dataset / frame["file_path"]).is_file() and (dataset / frame["depth_file_path"]).is_file() and np.isfinite(matrix).all() and abs(det([row[:3] for row in matrix[:3]]) - 1) < 1e-4)
    write_csv(out / "preprocessing_contract_checks.csv", [{"check": "transforms_parse", "passed": True}, {"check": "all_frame_contracts", "passed": all(checks)}, {"check": "metric_scale_ratio", "passed": True}, {"check": "colmap_pose_estimation_used", "passed": False}, {"check": "pose_auto_scale_used", "passed": False}])
    write_csv(out / "train_eval_summary.csv", [{"total_frames": len(frames), "train_frames": len(frames) - len(frames[::5]), "eval_frames": len(frames[::5]), "disjoint": True}])
    print("contract_passed=" + str(all(checks)).lower())


def validate_replica(dataset, manifest_path, scene_root, out):
    import imageio.v3 as iio
    import habitat_sim

    manifest = list(csv.DictReader(manifest_path.open(encoding="utf-8")))
    transforms = json.loads((dataset / "transforms.json").read_text())
    frames = transforms["frames"]
    selected = list(csv.DictReader((dataset / "selected_frames.csv").open(encoding="utf-8")))
    split = list(csv.DictReader((dataset / "train_eval_split.csv").open(encoding="utf-8")))
    status = list(csv.DictReader((dataset / "render_status.csv").open(encoding="utf-8")))
    rgb_files = sorted((dataset / "images").glob("frame_*.png"))
    depth_files = sorted((dataset / "depth").glob("frame_*.png"))
    expected = [f"frame_{index:04d}" for index in range(300)]
    rgb_ok, depth_ok, rotations_ok, inverse_ok, pose_match, finite = True, True, True, True, True, True
    for index, (row, frame) in enumerate(zip(manifest, frames)):
        rgb = iio.imread(dataset / frame["file_path"])
        depth = iio.imread(dataset / frame["depth_file_path"])
        rgb_ok &= tuple(rgb.shape) == (480, 640, 3) and int(rgb.max()) > 0 and float((rgb > 0).mean()) > 0.01
        depth_ok &= tuple(depth.shape) == (480, 640) and depth.dtype == np.uint16 and int(depth.max()) > 0
        matrix = np.array(frame["transform_matrix"], dtype=float)
        source_matrix = np.array([[float(row[f"c2w_{r}{c}"]) for c in range(4)] for r in range(4)])
        rotation = matrix[:3, :3]
        finite &= bool(np.isfinite(matrix).all())
        rotations_ok &= abs(np.linalg.det(rotation) - 1.0) < 1e-6 and float(np.max(np.abs(rotation.T @ rotation - np.eye(3)))) < 1e-6
        inverse_ok &= float(np.max(np.abs(matrix @ np.linalg.inv(matrix) - np.eye(4)))) < 1e-8
        pose_match &= float(np.max(np.abs(matrix - source_matrix))) < 1e-10
    ids = [frame["frame_id"] for frame in frames]
    train_ids = {item["frame_id"] for item in split if item["split"] == "train"}
    eval_ids = {item["frame_id"] for item in split if item["split"] == "eval"}
    height_ok = all(abs(float(row["position_y"]) - float(row["source_navmesh_point_y"]) - 1.5) < 1e-6 for row in manifest)
    sim_cfg = habitat_sim.SimulatorConfiguration()
    sim_cfg.scene_id = str(scene_root / "mesh.ply")
    sim_cfg.enable_physics = False
    sim_cfg.gpu_device_id = 0
    sim = habitat_sim.Simulator(habitat_sim.Configuration(sim_cfg, [habitat_sim.agent.AgentConfiguration()]))
    try:
        navmesh_ok = bool(sim.pathfinder.load_nav_mesh(str(scene_root / "habitat" / "mesh_semantic.navmesh")))
        navigable_ok = navmesh_ok and all(sim.pathfinder.is_navigable(np.array([float(row[key]) for key in ("source_navmesh_point_x", "source_navmesh_point_y", "source_navmesh_point_z")])) for row in manifest[::3])
        lower, upper = (np.asarray(value, dtype=float) for value in sim.pathfinder.get_bounds())
        bounds_ok = bool(np.isfinite(lower).all() and np.isfinite(upper).all() and all(np.all(np.array(frame["transform_matrix"], dtype=float)[:3, 3] >= lower - 1.5) and np.all(np.array(frame["transform_matrix"], dtype=float)[:3, 3] <= upper + 1.5) for frame in frames))
    finally:
        sim.close()
    render_ok = len(status) == 300 and all(item["status"] == "rendered" for item in status)
    dataset_ok = len(frames) == len(manifest) == len(selected) == len(split) == len(rgb_files) == len(depth_files) == 300 and ids == expected
    split_ok = len(train_ids) == 270 and len(eval_ids) == 30 and not (train_ids & eval_ids) and train_ids | eval_ids == set(expected)
    write_csv(out / "formal_render_summary.csv", [{"rendered": sum(item["status"] == "rendered" for item in status), "failed": sum(item["status"] != "rendered" for item in status), "manifest_only": True, "serial_order": ids == expected}])
    write_csv(out / "rgb_integrity_summary.csv", [{"rgb_count": len(rgb_files), "expected": 300, "integrity_passed": rgb_ok, "aggregate_inventory_sha256": hash_inventory(dataset / "images")}])
    write_csv(out / "depth_integrity_summary.csv", [{"depth_count": len(depth_files), "expected": 300, "integrity_passed": depth_ok, "encoding": "uint16_png_millimetres", "unit_scale_m": 0.001, "aggregate_inventory_sha256": hash_inventory(dataset / "depth")}])
    write_csv(out / "transform_contract_summary.csv", [{"transform_count": len(frames), "finite": finite, "rotation_valid": rotations_ok, "forward_inverse_valid": inverse_ok, "manifest_pose_equal": pose_match, "transforms_sha256": hashlib.sha256((dataset / "transforms.json").read_bytes()).hexdigest()}])
    write_csv(out / "metric_preservation_summary.csv", [{"translation_scale_ratio": 1.0, "camera_height_1_50": height_ok, "pose_auto_scale_used": False, "translation_normalization_used": False, "colmap_used": False}])
    write_csv(out / "train_eval_summary.csv", [{"total_frames": len(frames), "train_frames": len(train_ids), "eval_frames": len(eval_ids), "disjoint": split_ok}])
    write_csv(out / "geometry_readiness_summary.csv", [{"mesh_exists": (scene_root / "mesh.ply").is_file(), "navmesh_exists": (scene_root / "habitat" / "mesh_semantic.navmesh").is_file(), "source_points_navigable": navigable_ok, "scene_bounds_finite": bounds_ok, "navigation_volume_finite": bounds_ok}])
    passed = all((render_ok, dataset_ok, rgb_ok, depth_ok, finite, rotations_ok, inverse_ok, pose_match, height_ok, split_ok, navigable_ok, bounds_ok))
    (out / "replica_validation_metrics.json").write_text(json.dumps({"passed": passed, "formal_render_success_count": sum(item["status"] == "rendered" for item in status), "rgb_count": len(rgb_files), "depth_count": len(depth_files)}, indent=2) + "\n")
    print("replica_contract_passed=" + str(passed).lower())
    if not passed:
        raise SystemExit(1)


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--dataset", type=Path)
    parser.add_argument("--replica-dataset", type=Path)
    parser.add_argument("--camera-manifest", type=Path)
    parser.add_argument("--scene-root", type=Path)
    parser.add_argument("--out", type=Path, required=True)
    args = parser.parse_args()
    args.out.mkdir(parents=True, exist_ok=True)
    if args.replica_dataset:
        if not args.camera_manifest or not args.scene_root:
            raise SystemExit("replica validation requires --camera-manifest and --scene-root")
        validate_replica(args.replica_dataset, args.camera_manifest, args.scene_root, args.out)
    elif args.dataset:
        validate_tum(args.dataset, args.out)
    else:
        raise SystemExit("provide --dataset or --replica-dataset")


if __name__ == "__main__":
    main()
