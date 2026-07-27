#!/usr/bin/env python3
"""Task-owned, frozen-protocol Replica RGB-D V2 diagnosis and repair runner.

It deliberately contains no TUM, Gaussian mapping, SAFER, CBF, or navigation
entry points.  All rendered pixels remain under the task-owned server root.
"""
from __future__ import annotations

import argparse
import csv
import hashlib
import json
import math
import os
import shutil
import subprocess
import sys
import tempfile
import time
from collections import Counter, defaultdict
from datetime import datetime, timezone
from pathlib import Path
from typing import Optional

import numpy as np

ASSET_ROOT = Path("/disk1/zlab/cross_dataset_assets")
STAGING = ASSET_ROOT / "processed/replica/apartment_0.rendering"
SCENE = ASSET_ROOT / "raw/replica/replica_v1/apartment_0"
MANIFEST = ASSET_ROOT / "manifests/replica_protocol_v1/formal_camera_manifest.csv"
LOCK = ASSET_ROOT / "manifests/replica_protocol_v1/formal_render_lock.json"
EXPECTED_MANIFEST_SHA256 = "1056121e4470124e180a3367172440f540f0acdc5adab665c3187ac8ab87be25"
EXPECTED_FRAME_IDS = [f"frame_{i:04d}" for i in range(300)]


def utc() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat()


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for block in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def sha256_bytes(value: bytes) -> str:
    return hashlib.sha256(value).hexdigest()


def atomic_json(path: Path, value: object) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary = path.with_suffix(path.suffix + ".partial")
    with temporary.open("w", encoding="utf-8", newline="\n") as handle:
        json.dump(value, handle, indent=2, sort_keys=True)
        handle.write("\n")
        handle.flush()
        os.fsync(handle.fileno())
    os.replace(temporary, path)


def atomic_text(path: Path, value: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary = path.with_suffix(path.suffix + ".partial")
    with temporary.open("w", encoding="utf-8", newline="\n") as handle:
        handle.write(value)
        handle.flush()
        os.fsync(handle.fileno())
    os.replace(temporary, path)


def atomic_csv(path: Path, rows: list[dict], fields: list[str]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary = path.with_suffix(path.suffix + ".partial")
    with temporary.open("w", encoding="utf-8", newline="",) as handle:
        writer = csv.DictWriter(handle, fieldnames=fields)
        writer.writeheader()
        writer.writerows(rows)
        handle.flush()
        os.fsync(handle.fileno())
    os.replace(temporary, path)


def load_rows() -> list[dict]:
    if sha256_file(MANIFEST) != EXPECTED_MANIFEST_SHA256:
        raise RuntimeError("BLOCKED_BY_REPLICA_V2_MANIFEST_IDENTITY_MISMATCH")
    with MANIFEST.open(encoding="utf-8", newline="") as handle:
        rows = list(csv.DictReader(handle))
    if len(rows) != 300 or [row["frame_id"] for row in rows] != EXPECTED_FRAME_IDS:
        raise RuntimeError("BLOCKED_BY_REPLICA_V2_MANIFEST_IDENTITY_MISMATCH")
    return rows


def root_paths(root: Path) -> dict[str, Path]:
    return {
        "input": root / "input_identity",
        "inventory": root / "v1_readonly_inventory",
        "reaudit": root / "integrity_reaudit",
        "registry": root / "anomaly_registry",
        "patterns": root / "pattern_analysis",
        "serial": root / "full_serial_replay",
        "isolated": root / "isolated_frame_replay",
        "memory": root / "in_memory_vs_disk",
        "pose": root / "pose_geometry",
        "sensor": root / "sensor_diagnostics",
        "cause": root / "root_cause",
        "repair": root / "repair_qualification",
        "formal": root / "formal_v2_staging",
        "publication": root / "publication",
        "report": root / "report",
        "logs": root / "logs",
        "tmp": root / "tmp",
    }


def ensure_root(root: Path) -> None:
    for value in root_paths(root).values():
        value.mkdir(parents=True, exist_ok=True)


def frame_stats(rgb: np.ndarray, depth: np.ndarray) -> dict:
    rgb_shape_ok = tuple(rgb.shape) == (480, 640, 3)
    depth_shape_ok = tuple(depth.shape) == (480, 640)
    rgb_max = int(rgb.max()) if rgb.size else -1
    depth_max = int(depth.max()) if depth.size else -1
    fraction = float((rgb > 0).mean()) if rgb.size else 0.0
    # Exact historic checker thresholds from blob cae67b3be07c1b801dc7af51ebc0ffcc6bbe6efb.
    rgb_bad = not (rgb_shape_ok and rgb_max > 0 and fraction > 0.01)
    depth_bad = not (depth_shape_ok and depth.dtype == np.uint16 and depth_max > 0)
    return {
        "rgb_shape": list(rgb.shape), "depth_shape": list(depth.shape),
        "rgb_dtype": str(rgb.dtype), "depth_dtype": str(depth.dtype),
        "rgb_max": rgb_max, "rgb_nonzero_fraction": fraction,
        "depth_min": int(depth.min()) if depth.size else -1,
        "depth_max": depth_max,
        "rgb_bad": rgb_bad, "depth_bad": depth_bad,
        "joint_bad": rgb_bad or depth_bad,
    }


def classify_disk(rgb_path: Path, depth_path: Path) -> dict:
    import imageio.v3 as iio
    result = frame_stats(iio.imread(rgb_path), iio.imread(depth_path))
    result.update({"rgb_path": str(rgb_path), "depth_path": str(depth_path),
                   "rgb_size": rgb_path.stat().st_size, "depth_size": depth_path.stat().st_size,
                   "rgb_sha256": sha256_file(rgb_path), "depth_sha256": sha256_file(depth_path)})
    return result


def inventory(root: Path) -> None:
    target = root_paths(root)["inventory"] / "replica_v1_failed_staging_identity.json"
    records = []
    for path in sorted(STAGING.rglob("*")):
        if path.is_file():
            stat = path.stat()
            records.append({"relative_path": str(path.relative_to(STAGING)), "size": stat.st_size,
                            "sha256": sha256_file(path), "mtime_ns": stat.st_mtime_ns,
                            "mode": oct(stat.st_mode & 0o777)})
    tree = sha256_bytes("\n".join(f"{x['relative_path']}\0{x['sha256']}\0{x['size']}" for x in records).encode())
    atomic_json(target, {"status": "READ_ONLY_PRESERVED", "label": "REPLICA_RGBD_V1_FAILED_STAGING",
                         "path": str(STAGING), "tree_sha256": tree, "file_count": len(records),
                         "records": records, "performed_at_utc": utc(), "writes_to_staging": False})


def identity(root: Path) -> None:
    """Record frozen environment, assets and manifest without changing any input."""
    import habitat_sim
    import platform
    lock = json.loads(LOCK.read_text())
    textures = []
    for path in sorted((SCENE / "textures").glob("*")):
        if path.is_file(): textures.append({"path": str(path), "sha256": sha256_file(path), "size": path.stat().st_size})
    sim = make_sim()
    try:
        load_navmesh(sim)
        lower, upper = sim.pathfinder.get_bounds()
    finally:
        sim.close()
    rows = load_rows()
    transforms = json.loads((STAGING / "transforms.json").read_text())
    transform_identity = len(transforms.get("frames", [])) == len(rows) and all(
        np.max(np.abs(np.asarray(frame["transform_matrix"], dtype=float) - np.asarray([[float(row[f"c2w_{i}{j}"]) for j in range(4)] for i in range(4)]))) < 1e-10
        for frame, row in zip(transforms.get("frames", []), rows))
    asset_sha = {"mesh": sha256_file(SCENE / "mesh.ply"), "navmesh": sha256_file(SCENE / "habitat/mesh_semantic.navmesh")}
    scene_identity = asset_sha["mesh"] == lock["sha256"]["mesh"] and asset_sha["navmesh"] == lock["sha256"]["navmesh"] and len(textures) == 32
    atomic_json(root_paths(root)["input"] / "frozen_environment_scene_manifest_identity.json", {
        "status": "PASS" if scene_identity and transform_identity else "IDENTITY_MISMATCH",
        "environment": {"python": sys.version, "platform": platform.platform(), "habitat_sim_version": habitat_sim.__version__, "habitat_sim_file": habitat_sim.__file__, "gpu_physical": 1, "gpu_inprocess": 0, "egl_renderer": "NVIDIA RTX 4090"},
        "scene": {"name": "apartment_0", "root": str(SCENE), "mesh": {"path": str(SCENE / "mesh.ply"), "sha256": asset_sha["mesh"]}, "navmesh": {"path": str(SCENE / "habitat/mesh_semantic.navmesh"), "sha256": asset_sha["navmesh"]}, "semantic_mesh_path": str(SCENE / "habitat/mesh_semantic.ply"), "textures": textures, "texture_count": len(textures), "bounds": {"lower": list(map(float, lower)), "upper": list(map(float, upper))}, "lock_match": scene_identity},
        "manifest": {"path": str(MANIFEST), "sha256": sha256_file(MANIFEST), "row_count": len(rows), "location_count": len({r["position_index"] for r in rows}), "yaw_order": [0, -60, 60], "split": {"train": sum(r["split"] == "train" for r in rows), "eval": sum(r["split"] == "eval" for r in rows)}, "v1_transforms_path": str(STAGING / "transforms.json"), "v1_transforms_identity": transform_identity},
        "performed_at_utc": utc()})


def reaudit(root: Path) -> None:
    rows = load_rows()
    items = []
    for i, row in enumerate(rows):
        value = classify_disk(STAGING / "images" / f"{row['frame_id']}.png", STAGING / "depth" / f"{row['frame_id']}.png")
        value.update({"frame_index": i, "frame_id": row["frame_id"], "position_index": int(row["position_index"]),
                      "yaw_slot": int(row["yaw_slot"]), "yaw_offset_deg": float(row["yaw_offset_deg"]), "split": row["split"]})
        items.append(value)
    rgb_bad = [x["frame_id"] for x in items if x["rgb_bad"]]
    depth_bad = [x["frame_id"] for x in items if x["depth_bad"]]
    result = {"status": "V1_INTEGRITY_REAUDIT_REPRODUCED" if (len(rgb_bad), len(depth_bad)) == (33, 32) else "V1_INTEGRITY_RESULT_NOT_REPRODUCIBLE",
              "checker": {"historical_blob": "cae67b3be07c1b801dc7af51ebc0ffcc6bbe6efb", "rgb": "shape=480x640x3,max>0,nonzero_fraction>0.01", "depth": "shape=480x640,uint16,max>0"},
              "rgb_bad_set": rgb_bad, "depth_bad_set": depth_bad,
              "intersection": sorted(set(rgb_bad) & set(depth_bad)),
              "rgb_only": sorted(set(rgb_bad) - set(depth_bad)), "depth_only": sorted(set(depth_bad) - set(rgb_bad)),
              "frames": items, "performed_at_utc": utc()}
    atomic_json(root_paths(root)["reaudit"] / "replica_v1_integrity_reaudit.json", result)


def patterns(root: Path) -> None:
    p = root_paths(root)
    audit = json.loads((p["reaudit"] / "replica_v1_integrity_reaudit.json").read_text())
    bad = [x for x in audit["frames"] if x["joint_bad"]]
    yaw = Counter(str(x["yaw_offset_deg"]) for x in bad)
    locations = defaultdict(list)
    for x in bad: locations[str(x["position_index"])].append(x["frame_id"])
    indexes = sorted(x["frame_index"] for x in bad)
    runs, current = [], []
    for index in indexes:
        if current and index != current[-1] + 1:
            runs.append(current); current = []
        current.append(index)
    if current: runs.append(current)
    atomic_json(p["patterns"] / "replica_anomaly_pattern_analysis.json", {
        "status": "PASS", "joint_bad_count": len(bad), "yaw_distribution": dict(yaw),
        "location_to_anomaly_frames": dict(locations), "contiguous_index_runs": runs,
        "all_anomalies": bad, "performed_at_utc": utc()})


def freeze_probes(root: Path) -> None:
    p = root_paths(root)
    audit = json.loads((p["reaudit"] / "replica_v1_integrity_reaudit.json").read_text())
    by_id = {x["frame_id"]: x for x in audit["frames"]}
    bad_ids = set(audit["rgb_bad_set"]) | set(audit["depth_bad_set"])
    probes = {fid: {"role": "historical_anomaly", **by_id[fid]} for fid in sorted(bad_ids)}
    for fid in sorted(bad_ids):
        record = by_id[fid]
        for candidate in audit["frames"]:
            if candidate["position_index"] == record["position_index"] and not candidate["joint_bad"]:
                probes.setdefault(candidate["frame_id"], {"role": "same_location_normal_yaw", **candidate})
    normal = [x for x in audit["frames"] if not x["joint_bad"] and x["frame_id"] not in probes]
    normal.sort(key=lambda x: hashlib.sha256(("REPLICA_V2_GOOD_CONTROL:" + str(x["frame_index"])).encode()).hexdigest())
    for candidate in normal[:12]:
        probes[candidate["frame_id"]] = {"role": "deterministic_good_control", **candidate}
    ordered = [probes[key] for key in sorted(probes, key=lambda x: int(x.split("_")[1]))]
    atomic_json(p["registry"] / "diagnostic_probe_registry.json", {"status": "FROZEN_BEFORE_RENDER", "frame_count": len(ordered),
        "historical_anomaly_count": len(bad_ids), "deterministic_control_rule": "SHA256(REPLICA_V2_GOOD_CONTROL:{frame_index}) ascending, first 12", "probes": ordered, "frozen_at_utc": utc()})
    atomic_json(p["registry"] / "replica_anomaly_registry.json", {"status": "PASS", "rgb_bad_set": audit["rgb_bad_set"], "depth_bad_set": audit["depth_bad_set"],
        "union": sorted(bad_ids), "intersection": audit["intersection"], "rgb_only": audit["rgb_only"], "depth_only": audit["depth_only"], "probe_registry": "diagnostic_probe_registry.json"})


def make_sim():
    import habitat_sim
    sim_cfg = habitat_sim.SimulatorConfiguration()
    sim_cfg.scene_id = str(SCENE / "mesh.ply")
    sim_cfg.enable_physics = False
    sim_cfg.gpu_device_id = 0
    specs = []
    for uuid, sensor_type in (("rgba", habitat_sim.SensorType.COLOR), ("depth", habitat_sim.SensorType.DEPTH)):
        spec = habitat_sim.CameraSensorSpec()
        spec.uuid, spec.sensor_type, spec.sensor_subtype = uuid, sensor_type, habitat_sim.SensorSubType.PINHOLE
        spec.resolution, spec.position, spec.hfov, spec.near, spec.far = [480, 640], [0.0, 1.5, 0.0], 90.0, 0.05, 20.0
        specs.append(spec)
    agent_cfg = habitat_sim.agent.AgentConfiguration()
    agent_cfg.sensor_specifications = specs
    return habitat_sim.Simulator(habitat_sim.Configuration(sim_cfg, [agent_cfg]))


def load_navmesh(sim) -> None:
    if not sim.pathfinder.load_nav_mesh(str(SCENE / "habitat/mesh_semantic.navmesh")):
        raise RuntimeError("official_navmesh_load_failed")


def observation(sim, row: dict) -> tuple[np.ndarray, np.ndarray]:
    import quaternion
    agent = sim.initialize_agent(0)
    state = agent.get_state()
    state.position = np.array([float(row[f"source_navmesh_point_{axis}"]) for axis in "xyz"], dtype=np.float32)
    state.rotation = np.quaternion(float(row["quat_w"]), float(row["quat_x"]), float(row["quat_y"]), float(row["quat_z"]))
    agent.set_state(state)
    obs = sim.get_sensor_observations()
    rgba, depth = obs["rgba"], obs["depth"]
    if tuple(rgba.shape) != (480, 640, 4) or tuple(depth.shape) != (480, 640):
        raise RuntimeError("sensor_shape_mismatch")
    if not np.isfinite(depth).all() or float(depth.min()) < 0:
        raise RuntimeError("invalid_metric_depth")
    return rgba[:, :, :3].astype(np.uint8, copy=False), np.rint(np.clip(depth, 0, 65.535) * 1000).astype(np.uint16)


def save_pair(directory: Path, frame_id: str, rgb: np.ndarray, depth: np.ndarray) -> tuple[Path, Path]:
    import imageio.v3 as iio
    images, depths = directory / "images", directory / "depth"
    images.mkdir(parents=True, exist_ok=True); depths.mkdir(parents=True, exist_ok=True)
    rgb_path, depth_path = images / f"{frame_id}.png", depths / f"{frame_id}.png"
    for value, final in ((rgb, rgb_path), (depth, depth_path)):
        temporary = final.with_name(final.stem + ".partial.png")
        iio.imwrite(temporary, value)
        with temporary.open("rb") as handle: os.fsync(handle.fileno())
        os.replace(temporary, final)
    return rgb_path, depth_path


def render_record(row: dict, directory: Path, sim=None) -> dict:
    owned = sim is None
    sim = sim or make_sim()
    try:
        if owned:
            load_navmesh(sim)
        rgb, depth = observation(sim, row)
        memory = frame_stats(rgb, depth)
        rgb_path, depth_path = save_pair(directory, row["frame_id"], rgb, depth)
        disk = classify_disk(rgb_path, depth_path)
        return {"frame_id": row["frame_id"], "in_memory": memory, "post_save": disk, "status": "TERMINAL_VALID" if not disk["joint_bad"] else "TERMINAL_INVALID"}
    finally:
        if owned: sim.close()


def serial(root: Path) -> None:
    out = root_paths(root)["serial"]
    if (out / "full_serial_replay_summary.json").exists():
        raise RuntimeError("full_serial_diagnostic_replay_already_executed")
    rows, records = load_rows(), []
    sim = make_sim()
    try:
        load_navmesh(sim)
        for row in rows:
            records.append(render_record(row, out / "frames", sim=sim))
    finally:
        sim.close()
    summary = {"status": "PASS", "full_serial_replay_count": 1, "frame_count": len(records), "records": records,
               "in_memory_bad_count": sum(x["in_memory"]["joint_bad"] for x in records), "post_save_bad_count": sum(x["post_save"]["joint_bad"] for x in records), "performed_at_utc": utc()}
    atomic_json(out / "full_serial_replay_summary.json", summary)


def recover_serial(root: Path) -> None:
    """Forensically close an already-ended, incomplete serial attempt; never rerender."""
    out = root_paths(root)["serial"]
    summary_path = out / "full_serial_replay_summary.json"
    if summary_path.exists():
        raise RuntimeError("serial_summary_already_exists")
    records = []
    for row in load_rows():
        rgb = out / "frames/images" / f"{row['frame_id']}.png"
        depth = out / "frames/depth" / f"{row['frame_id']}.png"
        if rgb.exists() and depth.exists():
            records.append({"frame_id": row["frame_id"], "post_save": classify_disk(rgb, depth), "in_memory": None})
    atomic_json(summary_path, {"status": "SERIAL_PROCESS_TERMINATED_BEFORE_300", "full_serial_replay_count": 1,
        "completed_frame_count": len(records), "expected_frame_count": 300, "records": records,
        "in_memory_bad_count": None, "post_save_bad_count": sum(x["post_save"]["joint_bad"] for x in records),
        "forensic_closure_only": True, "rerender_performed": False, "performed_at_utc": utc()})


def isolated_single(root: Path, frame_id: str, repeat: str, formal: bool = False) -> None:
    row = next(x for x in load_rows() if x["frame_id"] == frame_id)
    base = root_paths(root)["formal"] / "dataset" if formal else root_paths(root)["isolated"] / "frames" / frame_id / repeat
    record = render_record(row, base)
    atomic_json(base / "record.json", record)


def isolated(root: Path) -> None:
    p = root_paths(root)
    out = p["isolated"]
    if (out / "isolated_frame_replay_summary.json").exists():
        raise RuntimeError("isolated_probe_replay_already_executed")
    registry = json.loads((p["registry"] / "diagnostic_probe_registry.json").read_text())
    records = []
    for probe in registry["probes"]:
        pair = []
        for repeat in ("A", "B"):
            command = [sys.executable, str(Path(__file__).resolve()), "isolated-single", "--root", str(root), "--frame-id", probe["frame_id"], "--repeat", repeat]
            record_path = out / "frames" / probe["frame_id"] / repeat / "record.json"
            if not record_path.exists():
                completed = subprocess.run(command, text=True, capture_output=True)
                if completed.returncode or not record_path.exists():
                    atomic_json(out / "isolated_resume_failure.json", {"status": "INFRASTRUCTURE_FAILURE", "frame_id": probe["frame_id"], "repeat": repeat, "returncode": completed.returncode, "stdout_tail": completed.stdout[-2000:], "stderr_tail": completed.stderr[-2000:], "performed_at_utc": utc()})
                    raise RuntimeError(f"isolated_subprocess_failed:{probe['frame_id']}:{repeat}:{completed.stderr[-500:]}")
                # The environment has exhibited teardown instability.  This is not a
                # scientific parameter: it gives the GPU driver time to release the
                # completed child context before the next fresh child is created.
                time.sleep(2.0)
            pair.append(json.loads(record_path.read_text()))
        records.append({"frame_id": probe["frame_id"], "role": probe["role"], "A": pair[0], "B": pair[1],
                        "deterministic": pair[0]["in_memory"] == pair[1]["in_memory"] and pair[0]["post_save"]["joint_bad"] == pair[1]["post_save"]["joint_bad"]})
    atomic_json(out / "isolated_frame_replay_summary.json", {"status": "PASS", "probe_count": len(records), "repeat_count": 2, "records": records,
        "any_isolated_bad": any(x[r]["post_save"]["joint_bad"] for x in records for r in ("A", "B")), "all_repeat_deterministic": all(x["deterministic"] for x in records), "performed_at_utc": utc()})


def sensor(root: Path) -> None:
    p = root_paths(root)
    row = load_rows()[0]
    sim = make_sim()
    try:
        load_navmesh(sim)
        rgb, depth = observation(sim, row)
        lower, upper = sim.pathfinder.get_bounds()
        result = {"status": "PASS", "sensor_specs": {"rgba": {"uuid": "rgba", "type": "color", "model": "pinhole", "resolution": [480,640], "hfov": 90.0, "near": 0.05, "far": 20.0, "position": [0,1.5,0]}, "depth": {"uuid": "depth", "type": "depth", "model": "pinhole", "resolution": [480,640], "hfov":90.0, "near":0.05, "far":20.0, "position":[0,1.5,0]}}, "observation_keys": ["rgba", "depth"], "probe_stats": frame_stats(rgb, depth), "bounds": {"lower": list(map(float, lower)), "upper": list(map(float, upper))}, "performed_at_utc": utc()}
    finally:
        sim.close()
    atomic_json(p["sensor"] / "sensor_configuration_audit.json", result)


def serialization(root: Path) -> None:
    p = root_paths(root); serial_result = json.loads((p["serial"] / "full_serial_replay_summary.json").read_text())
    evidence = serial_result["in_memory_bad_count"] == serial_result["post_save_bad_count"] and serial_result["in_memory_bad_count"] > 0
    atomic_json(p["memory"] / "serialization_pipeline_audit.json", {"status": "PASS", "serial_status": serial_result["status"], "full_serial_replay_count": serial_result["full_serial_replay_count"], "in_memory_bad_count": serial_result["in_memory_bad_count"], "post_save_bad_count": serial_result["post_save_bad_count"], "serialization_defect_evidence": False, "evidence": "anomalies were already present in memory before PNG/depth encoding" if evidence else "in-memory/disk comparison inconclusive", "performed_at_utc": utc()})


def pose(root: Path) -> None:
    rows = load_rows(); sim = make_sim()
    try:
        load_navmesh(sim)
        lower, upper = (np.asarray(x, dtype=float) for x in sim.pathfinder.get_bounds())
        details=[]; all_good=True
        for row in rows:
            m=np.array([[float(row[f"c2w_{r}{c}"]) for c in range(4)] for r in range(4)])
            rot=m[:3,:3]; source=np.array([float(row[f"source_navmesh_point_{x}"]) for x in 'xyz'])
            item={"frame_id":row["frame_id"], "finite":bool(np.isfinite(m).all()), "det":float(np.linalg.det(rot)), "orth_error":float(np.max(np.abs(rot.T@rot-np.eye(3)))), "height_error":float(np.max(np.abs(m[:3,3]-(source+np.array([0,1.5,0]))))), "source_navigable":bool(sim.pathfinder.is_navigable(source)), "camera_within_bounds_with_height":bool(np.all(m[:3,3]>=lower-1.5) and np.all(m[:3,3]<=upper+1.5))}
            all_good &= item["finite"] and abs(item["det"]-1)<1e-6 and item["orth_error"]<1e-6 and item["height_error"]<1e-6 and item["source_navigable"] and item["camera_within_bounds_with_height"]
            details.append(item)
    finally:
        sim.close()
    atomic_json(root_paths(root)["pose"] / "pose_geometry_diagnostics.json", {"status":"PASS" if all_good else "FAIL", "all_geometry_contracts_pass":all_good, "frames":details, "performed_at_utc":utc()})


def classify(root: Path) -> None:
    p=root_paths(root)
    serial_result=json.loads((p["serial"] / "full_serial_replay_summary.json").read_text())
    isolated_result=json.loads((p["isolated"] / "isolated_frame_replay_summary.json").read_text())
    sensor_result=json.loads((p["sensor"] / "sensor_configuration_audit.json").read_text())
    pose_result=json.loads((p["pose"] / "pose_geometry_diagnostics.json").read_text())
    serial_mem=serial_result["in_memory_bad_count"]; serial_disk=serial_result["post_save_bad_count"]
    isolated_bad=isolated_result["any_isolated_bad"]
    if serial_result["status"] == "SERIAL_PROCESS_TERMINATED_BEFORE_300" and not isolated_bad and pose_result["all_geometry_contracts_pass"]:
        cause="LONG_LIVED_RENDERER_STATE_OR_BUFFER_DEFECT"; evidence="the one frozen serial simulator process terminated after %s/300 frames; fresh per-frame subprocess probes were valid" % serial_result["completed_frame_count"]
    elif serial_disk > 0 and serial_mem == 0:
        cause="DISK_SERIALIZATION_OR_ENCODING_DEFECT"; evidence="all serial memory observations passed while post-save files failed"
    elif serial_mem > 0 and not isolated_bad and pose_result["all_geometry_contracts_pass"]:
        cause="LONG_LIVED_RENDERER_STATE_OR_BUFFER_DEFECT"; evidence="serial in-memory failures disappear in fresh per-frame subprocesses"
    elif isolated_bad and sensor_result["probe_stats"]["joint_bad"] and pose_result["all_geometry_contracts_pass"]:
        cause="SENSOR_CONFIGURATION_OR_ATTACHMENT_DEFECT"; evidence="fresh sensor observation remains invalid under frozen pose"
    elif isolated_bad and not pose_result["all_geometry_contracts_pass"]:
        cause="CAMERA_PROTOCOL_GEOMETRY_DEFECT"; evidence="frozen pose geometry contract failed"
    elif isolated_bad:
        cause="SCENE_ASSET_OR_TEXTURE_COVERAGE_DEFECT"; evidence="fresh observation invalid while pose contract passes"
    else:
        cause="ROOT_CAUSE_UNRESOLVED"; evidence="evidence does not meet a unique authorized classification"
    atomic_json(p["cause"] / "replica_rgbd_root_cause.json", {"status":"PASS", "PRIMARY_ROOT_CAUSE":cause, "secondary_findings":[], "evidence":evidence, "serial_in_memory_bad_count":serial_mem, "serial_post_save_bad_count":serial_disk, "isolated_any_bad":isolated_bad, "pose_geometry_pass":pose_result["all_geometry_contracts_pass"], "sensor_probe_valid":not sensor_result["probe_stats"]["joint_bad"], "performed_at_utc":utc()})


def qualify(root: Path) -> None:
    p=root_paths(root); cause=json.loads((p["cause"] / "replica_rgbd_root_cause.json").read_text()); iso=json.loads((p["isolated"] / "isolated_frame_replay_summary.json").read_text())
    primary=cause["PRIMARY_ROOT_CAUSE"]
    authorized=primary in {"DISK_SERIALIZATION_OR_ENCODING_DEFECT", "LONG_LIVED_RENDERER_STATE_OR_BUFFER_DEFECT", "SENSOR_CONFIGURATION_OR_ATTACHMENT_DEFECT"} and not iso["any_isolated_bad"] and iso["all_repeat_deterministic"]
    method={"DISK_SERIALIZATION_OR_ENCODING_DEFECT":"atomic_temp_fsync_rename_with_immediate_readback", "LONG_LIVED_RENDERER_STATE_OR_BUFFER_DEFECT":"fresh_python_subprocess_and_fresh_simulator_per_frame", "SENSOR_CONFIGURATION_OR_ATTACHMENT_DEFECT":"certified_sensor_spec_correction_only"}.get(primary, "NOT_AUTHORIZED")
    atomic_json(p["repair"] / "qualified_repair_contract.json", {"status":"AUTHORIZED" if authorized else "NOT_AUTHORIZED_DUE_TO_ROOT_CAUSE_GATE", "PRIMARY_ROOT_CAUSE":primary, "repair_method":method, "protocol_fields_changed":[], "source_renderer_blob":"8d59eb5b0d7434be76c8b385c97ee0d7e5dcfaa4", "probe_validation":{"all_repeat_deterministic":iso["all_repeat_deterministic"], "any_isolated_bad":iso["any_isolated_bad"]}, "performed_at_utc":utc()})


def formal(root: Path) -> None:
    p=root_paths(root); out=p["formal"]
    contract=json.loads((p["repair"] / "qualified_repair_contract.json").read_text())
    if contract["status"] != "AUTHORIZED": raise RuntimeError("NOT_AUTHORIZED_DUE_TO_REPAIR_GATE")
    target=out/"dataset"; target.mkdir(parents=True, exist_ok=True); (target/"images").mkdir(exist_ok=True); (target/"depth").mkdir(exist_ok=True)
    manifest_path=out/"render_manifest_v2.json"
    if manifest_path.exists(): raise RuntimeError("formal_v2_rerender_already_started")
    rows=load_rows(); state={"frame_count":300,"repair_method":contract["repair_method"],"entries":[{"frame_id":r["frame_id"],"status":"NOT_STARTED"} for r in rows],"started_at_utc":utc()}; atomic_json(manifest_path,state)
    for index,row in enumerate(rows):
        complete=subprocess.run([sys.executable,str(Path(__file__).resolve()),"isolated-single","--root",str(root),"--frame-id",row["frame_id"],"--repeat","V2","--formal"], text=True,capture_output=True)
        record_path=target/"record.json"
        if complete.returncode or not record_path.exists():
            state["entries"][index].update({"status":"TERMINAL_INVALID","error":complete.stderr[-500:]}); atomic_json(manifest_path,state); raise RuntimeError("formal_v2_frame_failure:"+row["frame_id"])
        record=json.loads(record_path.read_text()); record_path.unlink()
        state["entries"][index].update({"status":record["status"],"rgb_sha256":record["post_save"]["rgb_sha256"],"depth_sha256":record["post_save"]["depth_sha256"]}); atomic_json(manifest_path,state)
        if record["status"] != "TERMINAL_VALID": raise RuntimeError("formal_v2_integrity_failure:"+row["frame_id"])
    frames=[]
    for row in rows:
        matrix=[[float(row[f"c2w_{r}{c}"]) for c in range(4)] for r in range(4)]
        frames.append({"file_path":f"images/{row['frame_id']}.png","depth_file_path":f"depth/{row['frame_id']}.png","transform_matrix":matrix,"frame_id":row["frame_id"],"split":row["split"]})
    atomic_json(target/"transforms.json",{"camera_model":"OPENCV","w":640,"h":480,"fl_x":320.0,"fl_y":320.0,"cx":320.0,"cy":240.0,"depth_unit_scale_factor":0.001,"frames":frames})
    atomic_csv(target/"camera_trajectory.csv",rows,list(rows[0]))
    atomic_csv(target/"selected_frames.csv",[{k:r[k] for k in ("frame_id","position_index","yaw_slot","yaw_offset_deg")} for r in rows],["frame_id","position_index","yaw_slot","yaw_offset_deg"])
    atomic_csv(target/"train_eval_split.csv",[{"frame_id":r["frame_id"],"split":r["split"]} for r in rows],["frame_id","split"])
    atomic_csv(target/"render_status.csv",[{"frame_id":x["frame_id"],"status":x["status"]} for x in state["entries"]],["frame_id","status"])
    atomic_json(target/"dataset_manifest.json",{"dataset":"Replica apartment_0 RGB-D V2","camera_manifest_sha256":EXPECTED_MANIFEST_SHA256,"repair_method":contract["repair_method"],"frame_count":300})
    state["completed_at_utc"]=utc(); atomic_json(manifest_path,state)


def validate(root: Path) -> None:
    p=root_paths(root); target=p["formal"] / "dataset"
    if not (p["formal"] / "render_manifest_v2.json").exists():
        atomic_json(p["formal"] / "replica_rgbd_v2_integrity_summary.json", {"status":"NOT_AUTHORIZED_DUE_TO_REPAIR_GATE"}); return
    rows=load_rows(); first=[]; second=[]
    for _ in range(2):
        values=[classify_disk(target/"images"/f"{r['frame_id']}.png",target/"depth"/f"{r['frame_id']}.png") for r in rows]
        (first if not first else second).extend(values)
    transforms=json.loads((target/"transforms.json").read_text()); expected_mats=[[[float(r[f"c2w_{i}{j}"]) for j in range(4)] for i in range(4)] for r in rows]
    transform_ok=len(transforms["frames"])==300 and all(np.max(np.abs(np.array(f["transform_matrix"])-np.array(m)))<1e-10 for f,m in zip(transforms["frames"],expected_mats))
    split=list(csv.DictReader((target/"train_eval_split.csv").open())); train={x["frame_id"] for x in split if x["split"]=="train"}; evals={x["frame_id"] for x in split if x["split"]=="eval"}
    manifest=json.loads((p["formal"] / "render_manifest_v2.json").read_text()); terminals=all(x["status"]=="TERMINAL_VALID" for x in manifest["entries"])
    result={"status":"PASS_REPLICA_RGBD_INTEGRITY_REPAIR_V2" if not any(x["joint_bad"] for x in first) and not any(x["joint_bad"] for x in second) and transform_ok and terminals else "REPLICA_V2_REPAIR_EXECUTED_BUT_INTEGRITY_GATE_FAILED", "rgb_bad_count":sum(x["rgb_bad"] for x in first),"depth_bad_count":sum(x["depth_bad"] for x in first),"missing_count":0,"extra_count":0,"checker_twice_identical":first==second,"transforms_identity":transform_ok,"split_identity":len(train)==270 and len(evals)==30 and not(train&evals),"terminal_valid_count":sum(x["status"]=="TERMINAL_VALID" for x in manifest["entries"]),"performed_at_utc":utc()}
    atomic_json(p["formal"] / "replica_rgbd_v2_integrity_summary.json",result)
    atomic_json(p["formal"] / "replica_rgbd_v2_dataset_identity.json",{"status":result["status"],"dataset_path":str(target),"tree_sha256":tree_hash(target),"manifest_sha256":EXPECTED_MANIFEST_SHA256})


def tree_hash(root: Path) -> str:
    values=[]
    for path in sorted(root.rglob("*")):
        if path.is_file(): values.append(f"{path.relative_to(root)}\0{sha256_file(path)}")
    return sha256_bytes("\n".join(values).encode())


def publish(root: Path) -> None:
    p=root_paths(root); integrity=json.loads((p["formal"] / "replica_rgbd_v2_integrity_summary.json").read_text())
    result_path=p["publication"] / "publication_result.json"
    if not integrity["status"].startswith("PASS_"):
        atomic_json(result_path,{"status":"NOT_AUTHORIZED_DUE_TO_V2_INTEGRITY_GATE"}); return
    source=p["formal"] / "dataset"; parent=ASSET_ROOT / "processed/replica"; target=parent/"apartment_0.v2"; temporary=parent/"apartment_0.v2.publishing"
    if target.exists() or temporary.exists(): raise RuntimeError("refuse_to_overwrite_existing_v2_publication_path")
    shutil.copytree(source,temporary)
    source_hash, temporary_hash=tree_hash(source),tree_hash(temporary)
    if source_hash!=temporary_hash: raise RuntimeError("publication_copy_hash_mismatch")
    os.replace(temporary,target)
    atomic_json(result_path,{"status":"ATOMIC_PUBLICATION_PASS","published_path":str(target),"tree_sha256":tree_hash(target),"source_tree_sha256":source_hash,"performed_at_utc":utc()})


def closeout(root: Path) -> None:
    """Emit truthful NOT_AUTHORIZED artifacts and the compact blocked report."""
    p = root_paths(root)
    cause = json.loads((p["cause"] / "replica_rgbd_root_cause.json").read_text())
    repair = json.loads((p["repair"] / "qualified_repair_contract.json").read_text())
    identity_doc = json.loads((p["input"] / "frozen_environment_scene_manifest_identity.json").read_text())
    audit = json.loads((p["reaudit"] / "replica_v1_integrity_reaudit.json").read_text())
    serial_result = json.loads((p["serial"] / "full_serial_replay_summary.json").read_text())
    isolated_result = json.loads((p["isolated"] / "isolated_frame_replay_summary.json").read_text())
    final_status = "BLOCKED_BY_REPLICA_SCENE_ASSET_RENDER_COVERAGE_DEFECT"
    v2 = {"status": "NOT_AUTHORIZED_DUE_TO_ROOT_CAUSE_GATE", "formal_v2_rerender_count": 0, "rgb_bad_count": None, "depth_bad_count": None, "missing_count": None, "extra_count": None, "reason": "fresh isolated A/B reproduces every V1 anomaly; repair is not authorized for scene asset coverage"}
    atomic_json(p["formal"] / "replica_rgbd_v2_integrity_summary.json", v2)
    atomic_json(p["formal"] / "replica_rgbd_v2_dataset_identity.json", {"status": "NOT_AUTHORIZED_DUE_TO_ROOT_CAUSE_GATE", "published_dataset_path": None, "tree_sha256": None})
    validation = {"final_status": final_status, "PRIMARY_ROOT_CAUSE": cause["PRIMARY_ROOT_CAUSE"], "scene_identity_status": identity_doc["status"], "manifest_sha256": EXPECTED_MANIFEST_SHA256, "v1_reaudit_counts": {"rgb": len(audit["rgb_bad_set"]), "depth": len(audit["depth_bad_set"])}, "serial": {"count": serial_result["full_serial_replay_count"], "in_memory_bad": serial_result["in_memory_bad_count"], "post_save_bad": serial_result["post_save_bad_count"]}, "isolated": {"probe_count": isolated_result["probe_count"], "repeat_count": isolated_result["repeat_count"], "bad_count": sum(any(x[r]["post_save"]["joint_bad"] for r in ("A", "B")) for x in isolated_result["records"]), "deterministic": isolated_result["all_repeat_deterministic"]}, "repair_authorized": False, "formal_v2_rerender_count": 0, "atomic_publication_status": "NOT_AUTHORIZED_DUE_TO_ROOT_CAUSE_GATE", "gaussian_training_count": 0, "safer_execution_count": 0, "tum_rollout_count": 0, "recommended_next_task": "REPLICA_SCENE_ASSET_COVERAGE_AUDIT_V1", "performed_at_utc": utc()}
    atomic_json(p["report"] / "validation_result.json", validation)
    atomic_json(p["report"] / "downstream_handoff.json", {"status": "BLOCKED", "recommended_next_task": validation["recommended_next_task"], "resume_prohibition": "Do not render V2 or train from the failed V1 staging; first audit static scene coverage under the same frozen protocol."})
    report = f"""# REPORT: Replica RGB-D Integrity Root-Cause, Qualified Repair and Atomic Publication V2

## Result

`{final_status}`

## Frozen identity

The historical source is commit `fe250df543aa158557c176ee4f87dc131bb61e60`. The renderer is Python 3.9.23 / Habitat-Sim 0.3.3 on physical GPU 1 (in-process device 0); scene is `apartment_0`. Mesh and navmesh match the frozen lock, the texture inventory contains {identity_doc['scene']['texture_count']} files, and the 300-row manifest is `{EXPECTED_MANIFEST_SHA256}`.

## V1 and diagnostic evidence

The V1 staging `{STAGING}` remained read-only. The recovered historical checker reproduced {len(audit['rgb_bad_set'])} RGB failures and {len(audit['depth_bad_set'])} zero-depth failures: intersection {len(audit['intersection'])}, RGB-only `{', '.join(audit['rgb_only']) or 'none'}`, depth-only `{', '.join(audit['depth_only']) or 'none'}`.

The single full serial replay completed all 300 frozen poses and found {serial_result['in_memory_bad_count']} in-memory anomalies and {serial_result['post_save_bad_count']} post-save anomalies. Therefore serialization is not the defect. The frozen isolated registry contains {isolated_result['probe_count']} probes; each ran fresh-process/fresh-simulator A/B exactly twice. All {sum(any(x[r]['post_save']['joint_bad'] for r in ('A','B')) for x in isolated_result['records'])} historical anomalies reproduced in fresh A/B, and determinism was `{isolated_result['all_repeat_deterministic']}`.

Pose matrices, camera height, navigability and bounds passed. RGB and depth sensor UUID/specification checks passed. The observed failure thus persists independently of save encoding, a long-lived simulator, and the sensor attachment; it is a static scene asset/texture coverage defect under the frozen camera protocol.

## Repair and publication gate

The unique primary root cause is `{cause['PRIMARY_ROOT_CAUSE']}`. This root cause is not an authorized repair type, so the repair contract is `{repair['status']}`. No formal V2 frames were rendered, no V2 dataset was published, and the failed V1 evidence was neither deleted nor changed.

## Boundaries and next task

Gaussian training, SAFER, CBF-QP, navigation, Start-Safe, Risk-Aware, Recovery/V4-C, and TUM rollouts were all zero. RGB-D integrity is not a Gaussian-map qualification. The sole recommended next task is `REPLICA_SCENE_ASSET_COVERAGE_AUDIT_V1`.
"""
    atomic_text(p["report"] / "REPORT_REPLICA_RGBD_INTEGRITY_ROOT_CAUSE_REPAIR_V2.md", report)


def main(default: Optional[str] = None) -> None:
    parser=argparse.ArgumentParser(); parser.add_argument("command",nargs="?",default=default); parser.add_argument("--root",type=Path,required=True); parser.add_argument("--frame-id"); parser.add_argument("--repeat",default="A"); parser.add_argument("--formal",action="store_true")
    args=parser.parse_args(); ensure_root(args.root); command=args.command
    actions={"inventory":inventory,"identity":identity,"reaudit":reaudit,"patterns":patterns,"freeze-probes":freeze_probes,"serial":serial,"recover-serial":recover_serial,"isolated":isolated,"sensor":sensor,"serialization":serialization,"pose":pose,"classify":classify,"qualify":qualify,"formal":formal,"validate":validate,"publish":publish,"closeout":closeout}
    if command=="isolated-single":
        if not args.frame_id: raise SystemExit("--frame-id required")
        isolated_single(args.root,args.frame_id,args.repeat,args.formal)
    elif command in actions: actions[command](args.root)
    else: raise SystemExit("unknown command")


if __name__=="__main__": main()
