#!/usr/bin/env python3
"""Render exactly one frozen three-yaw V3 location in a fresh Simulator."""
from __future__ import annotations

import argparse
import hashlib
import os
import traceback
from datetime import datetime, timezone

import numpy as np

from _common import EXPECTED, MESH, NAVMESH, ROOT, atomic_json, load_json, sha256_path
from validate_replica_v3_frame import atomic_png, depth_stats, frame_valid, rgb_stats


def row_sha(row):
    return hashlib.sha256(__import__("json").dumps(row, sort_keys=True, separators=(",", ":")).encode("utf-8")).hexdigest()


def main(location_id: str, attempt: int) -> None:
    import habitat_sim
    import quaternion
    manifest = load_json(ROOT / "formal_staging" / "formal_camera_manifest_v3.json")["frames"]
    rows = [row for row in manifest if row["location_id"] == location_id]
    rows.sort(key=lambda row: row["yaw_slot"])
    if len(rows) != 3 or [row["yaw_offset_deg"] for row in rows] != [0, -60, 60]:
        raise RuntimeError("location_manifest_contract_failure")
    configuration = habitat_sim.SimulatorConfiguration(); configuration.scene_id = str(MESH); configuration.enable_physics = False; configuration.gpu_device_id = 0
    agent_configuration = habitat_sim.agent.AgentConfiguration(); specs = []
    for uuid, sensor_type in (("rgba", habitat_sim.SensorType.COLOR), ("depth", habitat_sim.SensorType.DEPTH)):
        spec = habitat_sim.CameraSensorSpec(); spec.uuid = uuid; spec.sensor_type = sensor_type; spec.sensor_subtype = habitat_sim.SensorSubType.PINHOLE; spec.resolution = [480, 640]; spec.position = [0., 1.5, 0.]; spec.hfov = 90.; spec.near = .05; spec.far = 20.; specs.append(spec)
    agent_configuration.sensor_specifications = specs
    simulator = habitat_sim.Simulator(habitat_sim.Configuration(configuration, [agent_configuration]))
    results = []
    try:
        if not simulator.pathfinder.load_nav_mesh(str(NAVMESH)):
            raise RuntimeError("official_navmesh_load_failed")
        agent = simulator.initialize_agent(0)
        for row in rows:
            started = datetime.now(timezone.utc).isoformat()
            state = agent.get_state(); state.position = np.asarray(row["source_navmesh_position"], dtype=np.float32); qx, qy, qz, qw = row["quaternion_xyzw"]; state.rotation = np.quaternion(qw, qx, qy, qz); agent.set_state(state)
            observation = simulator.get_sensor_observations()
            if "rgba" not in observation or "depth" not in observation:
                raise RuntimeError("observation_key_error")
            rgba, metric = observation["rgba"].astype(np.uint8), observation["depth"].astype(np.float32)
            rgb = rgba[:, :, :3]
            if tuple(rgba.shape) != (480, 640, 4) or tuple(metric.shape) != (480, 640) or not np.isfinite(metric).all() or float(metric.min()) < 0:
                raise RuntimeError("observation_shape_or_metric_depth_error")
            memory_rgb, memory_depth = rgb_stats(rgb), depth_stats(metric)
            depth_png = np.rint(np.clip(metric, 0.0, 65.535) * 1000.0).astype(np.uint16)
            rgb_path = ROOT / "formal_staging" / "images" / (row["frame_id"] + ".png")
            depth_path = ROOT / "formal_staging" / "depth" / (row["frame_id"] + ".png")
            disk_rgb, rgb_sha = atomic_png(rgb_path, rgb)
            disk_depth_png, depth_sha = atomic_png(depth_path, depth_png)
            disk_metric = disk_depth_png.astype(np.float32) * .001
            disk_rgb_stats, disk_depth_stats = rgb_stats(disk_rgb), depth_stats(disk_metric)
            depth_error = float(np.max(np.abs(metric - disk_metric)))
            consistent = memory_rgb["v1_black"] == disk_rgb_stats["v1_black"] and memory_rgb["v3_threshold_failure"] == disk_rgb_stats["v3_threshold_failure"] and memory_depth["v1_all_zero"] == disk_depth_stats["v1_all_zero"] and memory_depth["v3_threshold_failure"] == disk_depth_stats["v3_threshold_failure"] and depth_error <= .001001
            terminal = "TERMINAL_VALID" if frame_valid(memory_rgb, memory_depth) and frame_valid(disk_rgb_stats, disk_depth_stats) and consistent else "TERMINAL_INTEGRITY_FAILURE"
            result = {"frame_id": row["frame_id"], "location_id": location_id, "split": row["split"], "yaw_slot": row["yaw_slot"], "yaw_offset_deg": row["yaw_offset_deg"], "status": terminal, "attempt": attempt, "process_id": os.getpid(), "start_utc": started, "end_utc": datetime.now(timezone.utc).isoformat(), "manifest_row_sha256": row_sha(row), "camera_matrix_sha256": hashlib.sha256(__import__("json").dumps(row["camera_to_world"], separators=(",", ":")).encode()).hexdigest(), "sensor": {"resolution": [640, 480], "hfov_deg": 90., "near_m": .05, "far_m": 20., "height_m": 1.5, "gpu_device": 0}, "mesh_sha256": EXPECTED["mesh_sha256"], "navmesh_sha256": EXPECTED["navmesh_sha256"], "memory_rgb": memory_rgb, "memory_depth": memory_depth, "disk_rgb": disk_rgb_stats, "disk_depth": disk_depth_stats, "depth_quantization_max_error_m": depth_error, "rgb_path": str(rgb_path.relative_to(ROOT / "formal_staging")), "depth_path": str(depth_path.relative_to(ROOT / "formal_staging")), "rgb_sha256": rgb_sha, "depth_sha256": depth_sha, "memory_disk_consistent": consistent}
            atomic_json(ROOT / "per_frame_integrity" / (row["frame_id"] + ".json"), result)
            results.append(result)
        terminal = "TERMINAL_COMPLETE" if all(item["status"] == "TERMINAL_VALID" for item in results) else "TERMINAL_INTEGRITY_FAILURE"
        payload = {"location_id": location_id, "attempt": attempt, "fresh_os_subprocess": True, "fresh_simulator": True, "status": terminal, "frames": results}
    except Exception as error:
        payload = {"location_id": location_id, "attempt": attempt, "fresh_os_subprocess": True, "fresh_simulator": True, "status": "FAILED_INFRASTRUCTURE", "exception": type(error).__name__ + ":" + str(error), "traceback": traceback.format_exc(), "frames": results}
    finally:
        simulator.close()
    atomic_json(ROOT / "per_location_status" / (location_id + ".attempt" + str(attempt) + ".json"), payload)
    if payload["status"] == "FAILED_INFRASTRUCTURE":
        raise SystemExit(2)


if __name__ == "__main__":
    parser = argparse.ArgumentParser(); parser.add_argument("--location-id", required=True); parser.add_argument("--attempt", type=int, choices=(1, 2), required=True); args = parser.parse_args(); main(args.location_id, args.attempt)
