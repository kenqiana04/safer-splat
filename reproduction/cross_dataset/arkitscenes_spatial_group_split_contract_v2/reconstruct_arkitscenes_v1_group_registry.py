#!/usr/bin/env python3
"""Reconstruct immutable V1 keyframes and spatial connected components."""
from __future__ import annotations

import argparse
import json
from pathlib import Path

from arkitscenes_split_v2_common import (atomic_csv, atomic_json, identity_row, pose, read_csv,
    reconstruct_v1, rotation_deg, sha256_file, tree_sha256, v1_path)

EXPECTED_SIZES = {"42899163": [30, 4, 3, 136], "48018874": [16, 1, 16, 24, 9, 11, 24, 18, 9, 2, 94, 1, 42]}


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--task-root", type=Path, required=True)
    parser.add_argument("--v1-root", type=Path, required=True)
    parser.add_argument("--video-id", required=True)
    args = parser.parse_args()
    joined = v1_path(args.v1_root, f"frame_join/{args.video_id}/arkitscenes_joined_frame_manifest.csv")
    contract_path = v1_path(args.v1_root, f"frame_split/{args.video_id}/arkitscenes_frame_split_contract.json")
    rows = read_csv(joined)
    keyframes, groups = reconstruct_v1(rows, args.video_id)
    group_for_index = {member: group for group in groups for member in group["members"]}
    registry_rows: list[dict[str, object]] = []
    for index, row in enumerate(keyframes):
        matrix = pose(row)
        group = group_for_index[index]
        registry_rows.append(row | {"keyframe_index": index, "camera_center_x": f"{matrix[0,3]:.12f}", "camera_center_y": f"{matrix[1,3]:.12f}", "camera_center_z": f"{matrix[2,3]:.12f}", "v1_group_id": group["group_id"], "v1_group_hash": group["group_hash"], "v1_group_member_count": len(group["members"])})
    destination = args.task_root / "group_reconstruction" / args.video_id
    fields = list(rows[0]) + ["keyframe_index", "camera_center_x", "camera_center_y", "camera_center_z", "v1_group_id", "v1_group_hash", "v1_group_member_count"]
    atomic_csv(destination / "arkitscenes_v1_group_registry.csv", registry_rows, fields)
    registry = {"video_id": args.video_id, "joined_manifest_sha256": sha256_file(joined), "keyframe_count": len(keyframes), "groups": groups, "keyframes": [{"keyframe_index": index} | identity_row(row) | {"v1_group_id": group_for_index[index]["group_id"], "v1_group_hash": group_for_index[index]["group_hash"]} for index, row in enumerate(keyframes)]}
    atomic_json(destination / "arkitscenes_v1_group_registry.json", registry)
    contract = json.loads(contract_path.read_text(encoding="utf-8"))
    sizes = [len(group["members"]) for group in groups]
    valid = (len(keyframes) == int(contract["keyframe_count"]) and len(groups) == int(contract["group_count"]) and sizes == list(contract["group_sizes"]) and sizes == EXPECTED_SIZES[args.video_id] and sha256_file(joined) == str(contract["joined_manifest_sha256"]))
    validation = {"status": "V1_GROUP_RECONSTRUCTION_PASS" if valid else "BLOCKED_BY_ARKITSCENES_V1_GROUP_RECONSTRUCTION_MISMATCH", "video_id": args.video_id, "keyframe_count": len(keyframes), "group_count": len(groups), "group_sizes_hash_order": sizes, "joined_manifest_sha256": sha256_file(joined), "v1_contract_group_sizes": contract["group_sizes"], "registry_sha256": sha256_file(destination / "arkitscenes_v1_group_registry.json"), "registry_tree_sha256": tree_sha256(destination, ["arkitscenes_v1_group_registry.csv", "arkitscenes_v1_group_registry.json"]), "edge_contract": "timestamp<=2.0s AND center<=0.15m AND orientation<=15deg", "random_calls": 0}
    atomic_json(destination / "reconstruction_validation.json", validation)
    if not valid:
        raise SystemExit(validation["status"])
    print(validation["status"], args.video_id, validation["registry_tree_sha256"])
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
