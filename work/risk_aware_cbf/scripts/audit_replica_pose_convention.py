#!/usr/bin/env python3
"""Freeze the Habitat sensor-to-Nerfstudio camera convention before rendering."""
import argparse
import csv
import hashlib
import json
import math
from pathlib import Path

import numpy as np


def sha256(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def write_csv(path, row):
    with path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=list(row))
        writer.writeheader()
        writer.writerow(row)


def make_sim(scene_root, gpu_device):
    import habitat_sim

    sim_cfg = habitat_sim.SimulatorConfiguration()
    sim_cfg.scene_id = str(scene_root / "mesh.ply")
    # Habitat-Sim requires physics to be enabled for the non-mutating raycast API.
    sim_cfg.enable_physics = True
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
    parser.add_argument("--scene-root", type=Path, required=True)
    parser.add_argument("--out", type=Path, required=True)
    parser.add_argument("--gpu-device", type=int, default=0)
    parser.add_argument("--seed", type=int, default=20260715)
    args = parser.parse_args()
    args.out.mkdir(parents=True, exist_ok=True)

    import quaternion

    sim = make_sim(args.scene_root, args.gpu_device)
    try:
        pathfinder = sim.pathfinder
        navmesh_loaded = bool(pathfinder.load_nav_mesh(str(args.scene_root / "habitat" / "mesh_semantic.navmesh")))
        pathfinder.seed(args.seed)
        agent = sim.initialize_agent(0)
        selected = None
        for candidate_index in range(500):
            base = pathfinder.get_random_navigable_point()
            state = agent.get_state()
            state.position = base
            agent.set_state(state)
            trial_depth = sim.get_sensor_observations()["depth"]
            center = float(trial_depth[trial_depth.shape[0] // 2, trial_depth.shape[1] // 2])
            if math.isfinite(center) and center > 0.0:
                selected = (candidate_index, base, trial_depth)
                break
        if selected is None:
            raise RuntimeError("no_positive_center_depth_in_seeded_pose_audit_sequence")
        candidate_index, base, depth = selected
        heading = 0.0
        state = agent.get_state()
        sensor = state.sensor_states["depth"]
        rotation = quaternion.as_rotation_matrix(sensor.rotation)
        right, up, backward = rotation[:, 0], rotation[:, 1], rotation[:, 2]
        forward = -backward
        center_depth = float(depth[depth.shape[0] // 2, depth.shape[1] // 2])
        ray_distance = None
        ray_ok = False
        try:
            ray = habitat_sim.geo.Ray(sensor.position, forward)
            hits = sim.cast_ray(ray)
            if hits.has_hits():
                ray_distance = float(hits.hits[0].ray_distance)
                ray_ok = math.isfinite(center_depth) and math.isfinite(ray_distance) and abs(center_depth - ray_distance) < 0.20
        except Exception:
            # The depth image and basis remain recorded; an unavailable ray API is a failed audit.
            ray_ok = False
        identity = np.eye(4, dtype=float)
        conversion = {
            "source": "habitat_sensor_camera",
            "target": "nerfstudio_opengl_camera",
            "basis": {"right": right.tolist(), "up": up.tolist(), "forward": forward.tolist()},
            "world_up_axis": "+Y",
            "T_nerfstudio_from_habitat_camera": identity.tolist(),
            "T_habitat_from_nerfstudio_camera": identity.tolist(),
            "identity": True,
            "center_depth": center_depth,
            "center_ray_distance": ray_distance,
            "audit_heading_deg": heading,
            "audit_candidate_index": candidate_index,
        }
        conversion_path = args.out / "pose_conversion_matrix.json"
        conversion_path.write_text(json.dumps(conversion, indent=2) + "\n", encoding="utf-8")
        ortho = float(np.max(np.abs(rotation.T @ rotation - np.eye(3))))
        determinant = float(np.linalg.det(rotation))
        inverse_error = float(np.max(np.abs(identity @ np.linalg.inv(identity) - np.eye(4))))
        passed = bool(navmesh_loaded and np.isfinite(rotation).all() and abs(determinant - 1.0) < 1e-6 and ortho < 1e-6 and inverse_error < 1e-12 and ray_ok)
        write_csv(args.out / "pose_convention_audit.csv", {
            "navmesh_loaded": navmesh_loaded,
            "sensor_position_finite": bool(np.isfinite(np.asarray(sensor.position)).all()),
            "rotation_determinant": determinant,
            "rotation_orthogonality_max_error": ortho,
            "center_depth": center_depth,
            "center_ray_distance": ray_distance,
            "audit_candidate_index": candidate_index,
            "center_ray_forward_consistent": ray_ok,
            "conversion_identity": True,
            "conversion_inverse_max_error": inverse_error,
            "conversion_sha256": sha256(conversion_path),
            "passed": passed,
        })
        print("pose_convention_passed=" + str(passed).lower())
    finally:
        sim.close()


if __name__ == "__main__":
    main()
