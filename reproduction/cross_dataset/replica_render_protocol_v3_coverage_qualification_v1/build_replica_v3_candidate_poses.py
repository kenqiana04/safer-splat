#!/usr/bin/env python3
"""Construct hash-yawed V1-convention poses for all V3 navmesh candidates."""
from __future__ import annotations

import math

import numpy as np

from _v3_common import ROOT, atomic_json, base_yaw, c2w_from_yaw, ensure_server_root, load_json, quaternion_xyzw, sha256_path


def main() -> None:
    ensure_server_root()
    candidates = load_json(ROOT / "candidate_locations" / "candidate_location_inventory.json")["candidates"]
    poses = []
    for candidate in candidates:
        nav = np.asarray(candidate["position"], dtype=np.float64)
        camera = nav + np.asarray((0.0, 1.50, 0.0), dtype=np.float64)
        base = base_yaw(candidate["location_hash"])
        for slot, offset in enumerate((0, -60, 60)):
            yaw = (base + offset) % 360.0
            matrix = c2w_from_yaw(camera, yaw)
            rotation = matrix[:3, :3]
            quaternion = quaternion_xyzw(rotation)
            valid = bool(np.isfinite(matrix).all() and np.isfinite(quaternion).all() and abs(float(np.linalg.det(rotation)) - 1.0) < 1e-9 and np.max(np.abs(rotation.T @ rotation - np.eye(3))) < 1e-9)
            if not valid:
                raise RuntimeError("candidate_pose_contract_failure")
            poses.append({
                "candidate_id": candidate["candidate_id"], "location_hash": candidate["location_hash"], "source_navmesh_position": [float(value) for value in nav], "camera_world_position": [float(value) for value in camera], "base_yaw_deg": base, "yaw_slot": slot, "yaw_offset_deg": offset, "final_yaw_deg": yaw, "quaternion_xyzw": quaternion, "c2w": [[float(value) for value in row] for row in matrix], "rotation_determinant": float(np.linalg.det(rotation)), "orthogonality_max_abs_error": float(np.max(np.abs(rotation.T @ rotation - np.eye(3)))), "translation_scale": 1.0,
            })
    per_location = {candidate["candidate_id"]: [pose for pose in poses if pose["candidate_id"] == candidate["candidate_id"]] for candidate in candidates}
    if any(len(group) != 3 or any(group[index]["yaw_offset_deg"] != (0, -60, 60)[index] for index in range(3)) for group in per_location.values()):
        raise RuntimeError("three_yaw_pose_contract_failure")
    payload = {"status": "PASS_REPLICA_V3_CANDIDATE_POSE_CONTRACT", "candidate_location_count": len(candidates), "candidate_view_count": len(poses), "camera_height_m": 1.50, "yaw_offsets_deg": [0, -60, 60], "v1_convention": "habitat_y_up_agent_quaternion_and_nerfstudio_opengl_c2w", "poses": poses}
    path = ROOT / "candidate_poses" / "candidate_pose_inventory.json"
    atomic_json(path, payload)
    atomic_json(ROOT / "candidate_poses" / "candidate_pose_summary.json", {key: value for key, value in payload.items() if key != "poses"} | {"candidate_pose_inventory_sha256": sha256_path(path)})


if __name__ == "__main__":
    main()
