#!/usr/bin/env python3
"""Freeze V3's qualified 300-frame manifest without rendering output images."""
from __future__ import annotations

import csv
from pathlib import Path
from typing import Any, Dict, List

import numpy as np

from _v3_common import EXPECTED, ROOT, atomic_json, ensure_server_root, load_json, sha256_path


def main() -> None:
    ensure_server_root()
    contract_path = ROOT / "protocol_freeze" / "REPLICA_RENDER_PROTOCOL_V3_CONTRACT.json"
    registry_path = ROOT / "final_location_selection" / "selected_v3_location_registry.json"
    split_path = ROOT / "final_manifest" / "replica_v3_location_split.json"
    poses = load_json(ROOT / "candidate_poses" / "candidate_pose_inventory.json")["poses"]
    independent = load_json(ROOT / "independent_coverage" / "independent_candidate_coverage_summary.json")["views"]
    habitat = load_json(ROOT / "habitat_preprobe" / "habitat_preprobe_summary.json")["results"]
    pose_index = {(item["candidate_id"], item["yaw_slot"]): item for item in poses}
    independent_index = {item["frame_id"]: item for item in independent}
    habitat_index = {view["frame_id"]: view for result in habitat for view in result.get("views", [])}
    registry = load_json(registry_path)["selected_locations"]
    split = {item["candidate_id"]: item for item in load_json(split_path)["locations"]}
    rows: List[Dict[str, Any]] = []
    for location in registry:
        split_row = split[location["candidate_id"]]
        for slot, offset in enumerate((0, -60, 60)):
            pose = pose_index[(location["candidate_id"], slot)]
            identifier = f"{location['candidate_id']}_yaw_{slot}"
            direct, probe = independent_index[identifier], habitat_index[identifier]
            if direct["status"] != "INDEPENDENT_VIEW_COVERAGE_PASS" or probe["status"] != "HABITAT_VIEW_PREQUALIFICATION_PASS":
                raise RuntimeError("manifest_attempted_with_unqualified_view")
            matrix = np.asarray(pose["c2w"], dtype=np.float64)
            if not np.isfinite(matrix).all() or abs(float(np.linalg.det(matrix[:3, :3])) - 1.0) > 1e-9:
                raise RuntimeError("manifest_pose_contract_failure")
            frame_index = len(rows)
            rows.append({
                "frame_index": frame_index, "frame_id": f"frame_{frame_index:04d}", "location_id": split_row["location_id"], "source_candidate_id": location["candidate_id"], "location_hash": location["location_hash"], "source_navmesh_position": pose["source_navmesh_position"], "camera_world_position": pose["camera_world_position"], "base_yaw_deg": pose["base_yaw_deg"], "yaw_slot": slot, "yaw_offset_deg": offset, "final_yaw_deg": pose["final_yaw_deg"], "quaternion_xyzw": pose["quaternion_xyzw"], "camera_to_world": pose["c2w"], "split": split_row["split"], "independent_valid_hit_fraction": direct["valid_near_far_hit_fraction"], "independent_front_facing_fraction": direct["front_facing_hit_fraction"], "habitat_rgb_nonzero_fraction": probe["metrics"]["rgb_nonzero_fraction"], "habitat_depth_positive_fraction": probe["metrics"]["depth_positive_fraction"], "qualification_status": "INDEPENDENT_AND_HABITAT_TRIPLET_QUALIFIED", "scene_id": "apartment_0", "mesh_sha256": EXPECTED["mesh_sha256"], "navmesh_sha256": EXPECTED["navmesh_sha256"], "protocol_contract_sha256": sha256_path(contract_path), "selected_registry_sha256": sha256_path(registry_path), "planned_output_identity": f"pre_render_not_published/{frame_index:04d}",
            })
    if len(rows) != 300 or len({item["location_id"] for item in rows}) != 100 or sum(item["split"] == "train" for item in rows) != 270 or sum(item["split"] == "eval" for item in rows) != 30:
        raise RuntimeError("manifest_count_contract_failure")
    output = ROOT / "final_manifest"
    csv_path = output / "formal_camera_manifest_v3.csv"
    fields = ["frame_index", "frame_id", "location_id", "source_candidate_id", "location_hash", "source_navmesh_position", "camera_world_position", "base_yaw_deg", "yaw_slot", "yaw_offset_deg", "final_yaw_deg", "quaternion_xyzw", "camera_to_world", "split", "independent_valid_hit_fraction", "independent_front_facing_fraction", "habitat_rgb_nonzero_fraction", "habitat_depth_positive_fraction", "qualification_status", "scene_id", "mesh_sha256", "navmesh_sha256", "protocol_contract_sha256", "selected_registry_sha256", "planned_output_identity"]
    with csv_path.open("w", encoding="utf-8", newline="") as stream:
        writer = csv.DictWriter(stream, fieldnames=fields)
        writer.writeheader()
        for row in rows:
            writer.writerow({key: __import__("json").dumps(value, separators=(",", ":")) if isinstance(value, list) else value for key, value in row.items()})
    json_path = output / "formal_camera_manifest_v3.json"
    atomic_json(json_path, {"protocol": "NEW_PREQUALIFIED_REPLICA_RENDER_PROTOCOL_V3", "frame_count": len(rows), "location_count": 100, "frames": rows})
    transforms_path = output / "transforms_v3.json"
    atomic_json(transforms_path, {"camera_model": "PINHOLE", "w": 640, "h": 480, "fl_x": 320.0, "fl_y": 320.0, "cx": 319.5, "cy": 239.5, "camera_convention": "nerfstudio_opengl_c2w", "colmap_used": False, "auto_scale_used": False, "normalization_used": False, "frames": [{"frame_id": row["frame_id"], "location_id": row["location_id"], "split": row["split"], "transform_matrix": row["camera_to_world"]} for row in rows]})
    pose_sha = __import__("hashlib").sha256(__import__("json").dumps([row["camera_to_world"] for row in rows], separators=(",", ":"), ensure_ascii=True).encode("utf-8")).hexdigest()
    identity = {"protocol": "NEW_PREQUALIFIED_REPLICA_RENDER_PROTOCOL_V3", "formal_render_executed": False, "publication_executed": False, "training_executed": False, "safer_executed": False, "frame_count": 300, "location_count": 100, "csv_sha256": sha256_path(csv_path), "manifest_json_sha256": sha256_path(json_path), "transforms_sha256": sha256_path(transforms_path), "pose_array_sha256": pose_sha, "split_sha256": sha256_path(split_path), "selected_registry_sha256": sha256_path(registry_path), "protocol_contract_sha256": sha256_path(contract_path), "mesh_sha256": EXPECTED["mesh_sha256"], "navmesh_sha256": EXPECTED["navmesh_sha256"]}
    identity_path = output / "replica_protocol_v3_identity.json"
    # A file cannot contain its own byte SHA-256 without a circular identity.
    # The complete artifact-file SHA is computed by the validator and report.
    atomic_json(identity_path, identity)


if __name__ == "__main__":
    main()
