#!/usr/bin/env python3
"""Serially render only poses supplied by a locked Replica camera manifest."""
import argparse
import csv
import hashlib
import json
import math
from pathlib import Path

import numpy as np


def digest(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def write_csv(path, rows, fields=None):
    fields = fields or list(rows[0])
    with Path(path).open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=fields)
        writer.writeheader()
        writer.writerows(rows)


def verify_lock(lock):
    for name, path in lock["paths"].items():
        if digest(path) != lock["sha256"][name]:
            raise RuntimeError("blocked_by_preregistered_artifact_mutation:" + name)


def make_sim(scene_root, gpu_device):
    import habitat_sim

    sim_cfg = habitat_sim.SimulatorConfiguration()
    sim_cfg.scene_id = str(scene_root / "mesh.ply")
    sim_cfg.enable_physics = False
    sim_cfg.gpu_device_id = gpu_device
    agent_cfg = habitat_sim.agent.AgentConfiguration()
    specs = []
    for uuid, sensor_type in (("rgba", habitat_sim.SensorType.COLOR), ("depth", habitat_sim.SensorType.DEPTH)):
        spec = habitat_sim.CameraSensorSpec()
        spec.uuid = uuid
        spec.sensor_type = sensor_type
        spec.sensor_subtype = habitat_sim.SensorSubType.PINHOLE
        spec.resolution = [480, 640]
        spec.position = [0.0, 1.5, 0.0]
        spec.hfov = 90.0
        spec.near = 0.05
        spec.far = 20.0
        specs.append(spec)
    agent_cfg.sensor_specifications = specs
    return habitat_sim.Simulator(habitat_sim.Configuration(sim_cfg, [agent_cfg]))


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--manifest", type=Path, required=True)
    parser.add_argument("--lock", type=Path, required=True)
    parser.add_argument("--scene-root", type=Path, required=True)
    parser.add_argument("--output-root", type=Path, required=True)
    parser.add_argument("--gpu-device", type=int, default=0)
    args = parser.parse_args()
    if args.output_root.exists() and any(args.output_root.iterdir()):
        raise SystemExit("refuse to overwrite nonempty formal rendering directory")
    lock = json.loads(args.lock.read_text(encoding="utf-8"))
    verify_lock(lock)
    rows = list(csv.DictReader(args.manifest.open(encoding="utf-8")))
    expected = [f"frame_{index:04d}" for index in range(300)]
    if len(rows) != 300 or [row["frame_id"] for row in rows] != expected:
        raise SystemExit("blocked_by_camera_manifest_contract")
    args.output_root.mkdir(parents=True, exist_ok=False)
    images = args.output_root / "images"
    depths = args.output_root / "depth"
    images.mkdir()
    depths.mkdir()

    import imageio.v3 as iio
    import quaternion

    sim = make_sim(args.scene_root, args.gpu_device)
    statuses = []
    try:
        if not sim.pathfinder.load_nav_mesh(str(args.scene_root / "habitat" / "mesh_semantic.navmesh")):
            raise RuntimeError("official_navmesh_load_failed")
        agent = sim.initialize_agent(0)
        frames = []
        for index, row in enumerate(rows):
            try:
                state = agent.get_state()
                state.position = np.array([float(row["source_navmesh_point_x"]), float(row["source_navmesh_point_y"]), float(row["source_navmesh_point_z"])], dtype=np.float32)
                state.rotation = np.quaternion(float(row["quat_w"]), float(row["quat_x"]), float(row["quat_y"]), float(row["quat_z"]))
                agent.set_state(state)
                observation = sim.get_sensor_observations()
                rgba, depth = observation["rgba"], observation["depth"]
                if tuple(rgba.shape) != (480, 640, 4) or tuple(depth.shape) != (480, 640):
                    raise RuntimeError("sensor_shape_mismatch")
                if not np.isfinite(depth).all() or float(depth.min()) < 0.0:
                    raise RuntimeError("invalid_metric_depth")
                iio.imwrite(images / f"{row['frame_id']}.png", rgba[:, :, :3].astype(np.uint8))
                depth_mm = np.rint(np.clip(depth, 0.0, 65.535) * 1000.0).astype(np.uint16)
                iio.imwrite(depths / f"{row['frame_id']}.png", depth_mm)
                matrix = [[float(row[f"c2w_{r}{c}"]) for c in range(4)] for r in range(4)]
                frames.append({"file_path": f"images/{row['frame_id']}.png", "depth_file_path": f"depth/{row['frame_id']}.png", "transform_matrix": matrix, "frame_id": row["frame_id"], "split": row["split"]})
                statuses.append({"frame_id": row["frame_id"], "status": "rendered", "rgb_path": f"images/{row['frame_id']}.png", "depth_path": f"depth/{row['frame_id']}.png", "depth_min_m": float(depth.min()), "depth_max_m": float(depth.max())})
            except Exception as exc:
                statuses.append({"frame_id": row["frame_id"], "status": "failed", "rgb_path": "", "depth_path": "", "depth_min_m": "", "depth_max_m": "", "exception": type(exc).__name__ + ": " + str(exc)})
                write_csv(args.output_root / "render_status.csv", statuses, ["frame_id", "status", "rgb_path", "depth_path", "depth_min_m", "depth_max_m", "exception"])
                raise RuntimeError("blocked_by_formal_rendering:" + row["frame_id"]) from exc
        transforms = {"camera_model": "OPENCV", "w": 640, "h": 480, "fl_x": 320.0, "fl_y": 320.0, "cx": 320.0, "cy": 240.0, "depth_unit_scale_factor": 0.001, "frames": frames}
        (args.output_root / "transforms.json").write_text(json.dumps(transforms, indent=2) + "\n", encoding="utf-8")
        write_csv(args.output_root / "camera_trajectory.csv", rows)
        write_csv(args.output_root / "selected_frames.csv", [{"frame_id": row["frame_id"], "position_index": row["position_index"], "yaw_slot": row["yaw_slot"], "yaw_offset_deg": row["yaw_offset_deg"]} for row in rows])
        write_csv(args.output_root / "train_eval_split.csv", [{"frame_id": row["frame_id"], "split": row["split"]} for row in rows])
        (args.output_root / "metric_scale_contract.json").write_text(json.dumps({"depth_encoding": "uint16_png_millimetres", "depth_unit_scale_factor_m": 0.001, "translation_scale_ratio": 1.0, "pose_auto_scale_used": False, "translation_normalization_used": False}, indent=2) + "\n", encoding="utf-8")
        (args.output_root / "coordinate_transform_contract.json").write_text(json.dumps({"camera_convention": "nerfstudio_opengl_c2w", "T_nerfstudio_from_habitat_camera": "identity", "pose_source": "frozen_manifest", "colmap_used": False}, indent=2) + "\n", encoding="utf-8")
        lower, upper = sim.pathfinder.get_bounds()
        (args.output_root / "navigation_volume_contract.json").write_text(json.dumps({"lower": list(map(float, lower)), "upper": list(map(float, upper)), "finite": bool(np.isfinite(np.asarray(lower)).all() and np.isfinite(np.asarray(upper)).all())}, indent=2) + "\n", encoding="utf-8")
        manifest = {"frame_count": 300, "rgb_count": 300, "depth_count": 300, "camera_manifest_sha256": digest(args.manifest), "mesh_sha256": lock["sha256"]["mesh"], "navmesh_sha256": lock["sha256"]["navmesh"], "rendered_serially": True, "replacement_frames_used": False}
        (args.output_root / "geometry_manifest.json").write_text(json.dumps(manifest, indent=2) + "\n", encoding="utf-8")
        (args.output_root / "dataset_manifest.json").write_text(json.dumps({"dataset": "Replica apartment_0", "protocol_version": "G0.5E-v1", "files": {name: digest(args.output_root / name) for name in ("transforms.json", "selected_frames.csv", "train_eval_split.csv", "metric_scale_contract.json", "coordinate_transform_contract.json", "geometry_manifest.json")}}, indent=2) + "\n", encoding="utf-8")
        write_csv(args.output_root / "render_status.csv", statuses, ["frame_id", "status", "rgb_path", "depth_path", "depth_min_m", "depth_max_m", "exception"])
        print("formal_render_success_count=300")
    finally:
        sim.close()


if __name__ == "__main__":
    main()
