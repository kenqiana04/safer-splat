#!/usr/bin/env python3
"""Fresh-process Habitat pre-render diagnostic for V3 candidate locations."""
from __future__ import annotations

import argparse
import hashlib
import json
import os
import subprocess
import sys
from pathlib import Path
from typing import Any, Dict, List

import numpy as np

from _v3_common import NAVMESH, ROOT, SCENE_ROOT, atomic_json, ensure_server_root, load_json, sha256_path


def probe_hash(location_hash: str) -> str:
    return hashlib.sha256(("REPLICA_V3_HABITAT_PROBE:" + location_hash).encode("utf-8")).hexdigest()


def observation_metrics(rgb: np.ndarray, depth: np.ndarray) -> Dict[str, Any]:
    rgb3 = rgb[:, :, :3]
    rgb_nonzero = float((rgb3 > 0).mean())
    finite = np.isfinite(depth)
    positive = depth > 0
    finite_positive = depth[positive & finite]
    return {
        "rgb_shape": list(rgb.shape), "rgb_dtype": str(rgb.dtype), "rgb_min": int(rgb.min()), "rgb_max": int(rgb.max()), "rgb_nonzero_fraction": rgb_nonzero, "rgb_mean": float(rgb3.mean()), "rgb_std": float(rgb3.std()), "v1_rgb_black_classification": not (int(rgb.max()) > 0 and rgb_nonzero > 0.01),
        "depth_shape": list(depth.shape), "depth_dtype": str(depth.dtype), "depth_finite_fraction": float(finite.mean()), "depth_zero_fraction": float((depth == 0).mean()), "depth_positive_fraction": float(positive.mean()), "depth_min_positive_m": float(finite_positive.min()) if finite_positive.size else None, "depth_median_positive_m": float(np.median(finite_positive)) if finite_positive.size else None, "depth_max_m": float(depth[finite].max()) if finite.any() else None, "v1_depth_all_zero_classification": not bool(positive.any()),
    }


def _view_pass(metrics: Dict[str, Any]) -> bool:
    rgb_shape_ok = metrics["rgb_shape"] == [480, 640, 4] and metrics["rgb_dtype"] == "uint8"
    depth_shape_ok = metrics["depth_shape"] == [480, 640] and metrics["depth_dtype"] in {"float32", "float64"}
    return bool(rgb_shape_ok and metrics["rgb_max"] > 0 and metrics["rgb_nonzero_fraction"] >= .05 and depth_shape_ok and metrics["depth_finite_fraction"] == 1.0 and metrics["depth_positive_fraction"] >= .10 and metrics["depth_max_m"] is not None and metrics["depth_max_m"] > 0)


def one(candidate_id: str) -> None:
    import habitat_sim
    import quaternion
    poses = [pose for pose in load_json(ROOT / "candidate_poses" / "candidate_pose_inventory.json")["poses"] if pose["candidate_id"] == candidate_id]
    if len(poses) != 3:
        raise RuntimeError("candidate_pose_not_three_yaws")
    poses.sort(key=lambda item: item["yaw_slot"])
    result_path = ROOT / "habitat_preprobe" / "captures" / (candidate_id + ".json")
    result_path.parent.mkdir(parents=True, exist_ok=True)
    configuration = habitat_sim.SimulatorConfiguration()
    configuration.scene_id = str(SCENE_ROOT / "mesh.ply")
    configuration.gpu_device_id = 0
    configuration.enable_physics = False
    agent_config = habitat_sim.agent.AgentConfiguration()
    sensors = []
    for uuid, sensor_type in (("rgba", habitat_sim.SensorType.COLOR), ("depth", habitat_sim.SensorType.DEPTH)):
        spec = habitat_sim.CameraSensorSpec()
        spec.uuid = uuid
        spec.sensor_type = sensor_type
        spec.sensor_subtype = habitat_sim.SensorSubType.PINHOLE
        spec.resolution = [480, 640]
        spec.position = [0.0, 1.50, 0.0]
        spec.hfov = 90.0
        spec.near = 0.05
        spec.far = 20.0
        sensors.append(spec)
    agent_config.sensor_specifications = sensors
    simulator = habitat_sim.Simulator(habitat_sim.Configuration(configuration, [agent_config]))
    views: List[Dict[str, Any]] = []
    try:
        if not simulator.pathfinder.load_nav_mesh(str(NAVMESH)):
            raise RuntimeError("official_navmesh_load_failed")
        agent = simulator.initialize_agent(0)
        for pose in poses:
            state = agent.get_state()
            state.position = np.asarray(pose["source_navmesh_position"], dtype=np.float32)
            qx, qy, qz, qw = pose["quaternion_xyzw"]
            state.rotation = np.quaternion(qw, qx, qy, qz)
            agent.set_state(state)
            observations = simulator.get_sensor_observations()
            if "rgba" not in observations or "depth" not in observations:
                raise RuntimeError("observation_key_error")
            metrics = observation_metrics(observations["rgba"].astype(np.uint8), observations["depth"].astype(np.float32))
            views.append({"frame_id": f"{candidate_id}_yaw_{pose['yaw_slot']}", "candidate_id": candidate_id, "location_hash": pose["location_hash"], "yaw_slot": pose["yaw_slot"], "yaw_offset_deg": pose["yaw_offset_deg"], "metrics": metrics, "status": "HABITAT_VIEW_PREQUALIFICATION_PASS" if _view_pass(metrics) else "HABITAT_VIEW_PREQUALIFICATION_FAIL"})
        payload = {"candidate_id": candidate_id, "location_hash": poses[0]["location_hash"], "source_navmesh_position": poses[0]["source_navmesh_position"], "fresh_os_subprocess": True, "fresh_simulator": True, "scene_id": str(SCENE_ROOT / "mesh.ply"), "navmesh": str(NAVMESH), "camera_model": {"resolution": [640, 480], "hfov_deg": 90.0, "near_m": .05, "far_m": 20.0, "camera_height_m": 1.50}, "views": views, "status": "HABITAT_LOCATION_TRIPLET_PASS" if all(view["status"] == "HABITAT_VIEW_PREQUALIFICATION_PASS" for view in views) else "HABITAT_LOCATION_TRIPLET_FAIL"}
    except Exception as error:
        payload = {"candidate_id": candidate_id, "fresh_os_subprocess": True, "fresh_simulator": True, "status": "HABITAT_LOCATION_SENSOR_ERROR", "error": type(error).__name__ + ":" + str(error), "views": views}
    finally:
        simulator.close()
    atomic_json(result_path, payload)
    if payload["status"] == "HABITAT_LOCATION_SENSOR_ERROR":
        raise SystemExit(payload["status"])


def run_all() -> None:
    ensure_server_root()
    independent = load_json(ROOT / "independent_coverage" / "independent_candidate_coverage_summary.json")
    qualifying = [item for item in independent["locations"] if item["status"] == "INDEPENDENT_LOCATION_TRIPLET_PASS"]
    qualifying.sort(key=lambda item: probe_hash(item["location_hash"]))
    if len(qualifying) < 120:
        raise SystemExit("BLOCKED_BY_REPLICA_V3_INSUFFICIENT_DIRECT_ASSET_COVERAGE_POOL")
    captures = ROOT / "habitat_preprobe" / "captures"
    captures.mkdir(parents=True, exist_ok=True)
    existing = {path.stem for path in captures.glob("candidate_*.json")}
    stages = [("stage_1", min(160, len(qualifying))), ("stage_2", min(240, len(qualifying))), ("stage_3", min(320, len(qualifying)))]
    stage_rows = []
    env = {**os.environ, "CUDA_VISIBLE_DEVICES": "1", "PYTHONNOUSERSITE": "1", "PYTHONDONTWRITEBYTECODE": "1"}
    executed: List[str] = []
    for name, upper in stages:
        target = qualifying[:upper]
        for item in target:
            candidate_id = item["candidate_id"]
            if candidate_id in existing:
                continue
            process = subprocess.run([sys.executable, __file__, "--one", candidate_id], env=env, capture_output=True, text=True)
            log = ROOT / "logs" / ("habitat_" + candidate_id + ".log")
            log.write_text(process.stdout + "\n--- STDERR ---\n" + process.stderr, encoding="utf-8")
            if process.returncode != 0 or not (captures / (candidate_id + ".json")).exists():
                raise RuntimeError("habitat_preprobe_subprocess_failure:" + candidate_id)
            existing.add(candidate_id)
            executed.append(candidate_id)
        results = [load_json(captures / (item["candidate_id"] + ".json")) for item in target]
        passes = sum(result["status"] == "HABITAT_LOCATION_TRIPLET_PASS" for result in results)
        stage_rows.append({"stage": name, "target_location_count": len(target), "newly_executed_location_count": len([item for item in target if item["candidate_id"] in executed]), "evaluated_location_count": len(results), "triplet_pass_location_count": passes, "executed": True})
        if passes >= 120:
            break
    all_results = [load_json(captures / (item["candidate_id"] + ".json")) for item in qualifying if (captures / (item["candidate_id"] + ".json")).exists()]
    habitat_passes = [item for item in all_results if item["status"] == "HABITAT_LOCATION_TRIPLET_PASS"]
    status = "PASS_REPLICA_V3_HABITAT_PREPROBE" if len(habitat_passes) >= 120 else "BLOCKED_BY_REPLICA_V3_INSUFFICIENT_HABITAT_QUALIFIED_LOCATION_POOL"
    payload = {"status": status, "probe_order_hash": "SHA256(REPLICA_V3_HABITAT_PROBE:location_hash)", "maximum_habitat_preprobe_locations": 320, "fresh_os_subprocess_and_fresh_simulator_per_location": True, "stages": stage_rows, "total_habitat_probe_locations": len(all_results), "total_habitat_probe_views": sum(len(item.get("views", [])) for item in all_results), "habitat_triplet_pass_location_count": len(habitat_passes), "results": all_results, "capture_json_server_only": str(captures)}
    atomic_json(ROOT / "habitat_preprobe" / "habitat_preprobe_summary.json", payload)
    if status != "PASS_REPLICA_V3_HABITAT_PREPROBE":
        raise SystemExit(status)


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--one")
    parser.add_argument("--run", action="store_true")
    args = parser.parse_args()
    if bool(args.one) == args.run:
        raise SystemExit("choose_one_or_run")
    one(args.one) if args.one else run_all()
