#!/usr/bin/env python3
"""Run V3 frozen-manifest 30-frame A/B fresh-process repeatability probes."""
from __future__ import annotations

import argparse
import hashlib
import os
import subprocess
import sys
from pathlib import Path
from typing import Any, Dict, List

import numpy as np

from _v3_common import NAVMESH, ROOT, SCENE_ROOT, atomic_json, ensure_server_root, load_json


def frame_hash(frame_id: str) -> str:
    return hashlib.sha256(("REPLICA_V3_REPEATABILITY:" + frame_id).encode("utf-8")).hexdigest()


def classify(rgb: np.ndarray, depth: np.ndarray) -> Dict[str, Any]:
    rgb3 = rgb[:, :, :3]
    finite = np.isfinite(depth)
    positive = depth > 0
    metrics = {"rgb_shape": list(rgb.shape), "rgb_dtype": str(rgb.dtype), "rgb_max": int(rgb.max()), "rgb_nonzero_fraction": float((rgb3 > 0).mean()), "depth_shape": list(depth.shape), "depth_dtype": str(depth.dtype), "depth_finite_fraction": float(finite.mean()), "depth_positive_fraction": float(positive.mean()), "depth_max_m": float(depth[finite].max()) if finite.any() else None, "rgb_raw_sha256": hashlib.sha256(rgb.tobytes()).hexdigest(), "depth_raw_sha256": hashlib.sha256(depth.tobytes()).hexdigest()}
    passed = bool(metrics["rgb_shape"] == [480, 640, 4] and metrics["rgb_dtype"] == "uint8" and metrics["rgb_max"] > 0 and metrics["rgb_nonzero_fraction"] >= .05 and metrics["depth_shape"] == [480, 640] and metrics["depth_dtype"] in {"float32", "float64"} and metrics["depth_finite_fraction"] == 1.0 and metrics["depth_positive_fraction"] >= .10 and metrics["depth_max_m"] is not None and metrics["depth_max_m"] > 0)
    return {"metrics": metrics, "classification": "HABITAT_VIEW_PREQUALIFICATION_PASS" if passed else "HABITAT_VIEW_PREQUALIFICATION_FAIL"}


def one(frame_id: str, repeat: str) -> None:
    import habitat_sim
    import quaternion
    manifest = load_json(ROOT / "final_manifest" / "formal_camera_manifest_v3.json")["frames"]
    frame = next((item for item in manifest if item["frame_id"] == frame_id), None)
    if frame is None:
        raise RuntimeError("unknown_frozen_frame")
    configuration = habitat_sim.SimulatorConfiguration()
    configuration.scene_id = str(SCENE_ROOT / "mesh.ply")
    configuration.gpu_device_id = 0
    configuration.enable_physics = False
    agent_config = habitat_sim.agent.AgentConfiguration()
    specs = []
    for uuid, sensor_type in (("rgba", habitat_sim.SensorType.COLOR), ("depth", habitat_sim.SensorType.DEPTH)):
        spec = habitat_sim.CameraSensorSpec(); spec.uuid = uuid; spec.sensor_type = sensor_type; spec.sensor_subtype = habitat_sim.SensorSubType.PINHOLE; spec.resolution = [480, 640]; spec.position = [0., 1.5, 0.]; spec.hfov = 90.; spec.near = .05; spec.far = 20.; specs.append(spec)
    agent_config.sensor_specifications = specs
    simulator = habitat_sim.Simulator(habitat_sim.Configuration(configuration, [agent_config]))
    try:
        if not simulator.pathfinder.load_nav_mesh(str(NAVMESH)):
            raise RuntimeError("official_navmesh_load_failed")
        agent = simulator.initialize_agent(0)
        state = agent.get_state()
        state.position = np.asarray(frame["source_navmesh_position"], dtype=np.float32)
        qx, qy, qz, qw = frame["quaternion_xyzw"]
        state.rotation = np.quaternion(qw, qx, qy, qz)
        agent.set_state(state)
        observations = simulator.get_sensor_observations()
        result = {"frame_id": frame_id, "repeat": repeat, "fresh_os_subprocess": True, "fresh_simulator": True, "pose_identity": {"camera_to_world": frame["camera_to_world"], "quaternion_xyzw": frame["quaternion_xyzw"]}, **classify(observations["rgba"].astype(np.uint8), observations["depth"].astype(np.float32))}
    finally:
        simulator.close()
    path = ROOT / "repeatability_probe" / "captures" / repeat / (frame_id + ".json")
    atomic_json(path, result)


def run_all() -> None:
    ensure_server_root()
    manifest = load_json(ROOT / "final_manifest" / "formal_camera_manifest_v3.json")["frames"]
    selected = sorted(manifest, key=lambda item: frame_hash(item["frame_id"]))[:30]
    if len(selected) != 30:
        raise RuntimeError("repeatability_frame_selection_count")
    env = {**os.environ, "CUDA_VISIBLE_DEVICES": "1", "PYTHONNOUSERSITE": "1", "PYTHONDONTWRITEBYTECODE": "1"}
    for repeat in ("A", "B"):
        for frame in selected:
            output = ROOT / "repeatability_probe" / "captures" / repeat / (frame["frame_id"] + ".json")
            process = subprocess.run([sys.executable, __file__, "--one", frame["frame_id"], "--repeat", repeat], env=env, capture_output=True, text=True)
            log = ROOT / "logs" / ("repeat_" + repeat + "_" + frame["frame_id"] + ".log")
            log.write_text(process.stdout + "\n--- STDERR ---\n" + process.stderr, encoding="utf-8")
            if process.returncode != 0 or not output.exists():
                raise RuntimeError("repeatability_subprocess_failure:" + frame["frame_id"] + ":" + repeat)
    results = []
    for frame in selected:
        a = load_json(ROOT / "repeatability_probe" / "captures" / "A" / (frame["frame_id"] + ".json"))
        b = load_json(ROOT / "repeatability_probe" / "captures" / "B" / (frame["frame_id"] + ".json"))
        same = a["classification"] == b["classification"] and a["pose_identity"] == b["pose_identity"]
        results.append({"frame_id": frame["frame_id"], "yaw_offset_deg": frame["yaw_offset_deg"], "split": frame["split"], "repeat_a": a, "repeat_b": b, "classification_agreement": same})
    a_pass = sum(item["repeat_a"]["classification"] == "HABITAT_VIEW_PREQUALIFICATION_PASS" for item in results)
    b_pass = sum(item["repeat_b"]["classification"] == "HABITAT_VIEW_PREQUALIFICATION_PASS" for item in results)
    disagreements = sum(not item["classification_agreement"] for item in results)
    status = "PASS_REPLICA_V3_FROZEN_MANIFEST_REPEATABILITY" if a_pass == b_pass == 30 and disagreements == 0 else "BLOCKED_BY_REPLICA_V3_FROZEN_MANIFEST_REPEATABILITY_FAILURE"
    atomic_json(ROOT / "repeatability_probe" / "repeatability_probe_summary.json", {"status": status, "repeatability_probe_count": 30, "fresh_subprocess_and_simulator_per_repeat": True, "repeat_a_pass_count": a_pass, "repeat_b_pass_count": b_pass, "a_b_disagreement_count": disagreements, "selected_yaw_offsets": sorted({item["yaw_offset_deg"] for item in selected}), "selected_splits": sorted({item["split"] for item in selected}), "results": results})
    if status != "PASS_REPLICA_V3_FROZEN_MANIFEST_REPEATABILITY":
        raise SystemExit(status)


if __name__ == "__main__":
    parser = argparse.ArgumentParser(); parser.add_argument("--one"); parser.add_argument("--repeat", choices=("A", "B")); parser.add_argument("--run", action="store_true"); args = parser.parse_args()
    if args.run == bool(args.one) or (args.one and not args.repeat):
        raise SystemExit("choose_run_or_one_with_repeat")
    one(args.one, args.repeat) if args.one else run_all()
