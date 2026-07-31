#!/usr/bin/env python3
"""Independent no-leakage validator; it never calls the primary allocation script."""
from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path

import numpy as np

from arkitscenes_split_v2_common import (GROUP_CENTER_M, GROUP_ROTATION_DEG, GROUP_TIME_S,
    atomic_json, pose, read_csv, reconstruct_v1, rotation_deg, sha256_file)


def independent_dp(groups: list[dict[str, object]]) -> dict[int, tuple[str, ...]]:
    states: dict[int, tuple[str, ...]] = {0: ()}
    for group in sorted(groups, key=lambda item: str(item["group_hash"])):
        size = len(group["members"])
        token = str(group["group_hash"])
        for count, selected in sorted(list(states.items()), reverse=True):
            candidate = selected + (token,)
            if count + size not in states or candidate < states[count + size]: states[count + size] = candidate
    return states


def sha(path: Path) -> str: return sha256_file(path)


def stats(rows: list[dict[str, str]]) -> dict[str, object]:
    centers = np.asarray([pose(row)[:3, 3] for row in rows], dtype=np.float64)
    times = np.asarray([float(row["timestamp"]) for row in rows], dtype=np.float64)
    return {"count": len(rows), "bbox_min": centers.min(axis=0).round(12).tolist(), "bbox_max": centers.max(axis=0).round(12).tolist(), "trajectory_span_m": float(np.linalg.norm(centers.max(axis=0)-centers.min(axis=0))), "timestamp_span_s": float(times.max()-times.min())}


def main() -> int:
    parser = argparse.ArgumentParser(); parser.add_argument("--task-root", type=Path, required=True); parser.add_argument("--v1-root", type=Path, required=True); args = parser.parse_args()
    split_root = args.task_root / "v2_split"; contract = json.loads((split_root / "arkitscenes_spatial_group_split_contract_v2.json").read_text(encoding="utf-8"))
    train, heldout = read_csv(split_root / "arkitscenes_train_manifest_v2.csv"), read_csv(split_root / "arkitscenes_heldout_manifest_v2.csv")
    original = read_csv(args.v1_root / "frame_join" / "48018874" / "arkitscenes_joined_frame_manifest.csv")
    rebuilt_keyframes, rebuilt_groups = reconstruct_v1(original, "48018874")
    registry = json.loads((args.task_root / "group_reconstruction" / "48018874" / "arkitscenes_v1_group_registry.json").read_text(encoding="utf-8"))
    registry_groups_match = rebuilt_groups == registry["groups"]
    states = independent_dp(rebuilt_groups); n = len(rebuilt_keyframes); target = int((0.20*n)+0.5)
    feasible = [(abs(count-target), count, values) for count, values in states.items() if 40 <= count <= 60 and n-count >= 200]
    expected_score = min(feasible) if feasible else None
    actual_selected = tuple(sorted({row["v1_group_hash"] for row in heldout}))
    actual_score = (abs(len(heldout)-target), len(heldout), actual_selected)
    all_keyframes = set(range(n)); train_indices = {int(row["keyframe_index"]) for row in train}; heldout_indices = {int(row["keyframe_index"]) for row in heldout}
    group_sets = {str(group["group_hash"]): set(int(item) for item in group["members"]) for group in rebuilt_groups}
    fragmented = [token for token, members in group_sets.items() if not (members <= train_indices or members <= heldout_indices)]
    identity_overlaps = {"frame_index": sorted(train_indices & heldout_indices), "filename": sorted({row["rgb"] for row in train} & {row["rgb"] for row in heldout}), "pose_timestamp": sorted({row["pose_timestamp"] for row in train} & {row["pose_timestamp"] for row in heldout}), "group_hash": sorted({row["v1_group_hash"] for row in train} & {row["v1_group_hash"] for row in heldout})}
    data_identity = json.loads((args.v1_root / "data_identity" / "arkitscenes_scene_asset_identity.json").read_text(encoding="utf-8"))
    asset_record = next(item for item in data_identity["published"] if str(item["video_id"]) == "48018874")
    candidates = [Path(asset_record["source"]), Path(asset_record["destination"])]
    asset_root = next((path for path in candidates if path.is_dir()), None)
    if asset_root is None: raise SystemExit("BLOCKED_BY_ARKITSCENES_V1_IDENTITY_OR_GROUP_RECONSTRUCTION_MISMATCH: asset path from record unavailable")
    def hashes(rows: list[dict[str, str]], field: str) -> set[str]: return {sha(asset_root / row[field]) for row in rows}
    identity_overlaps["rgb_sha256"] = sorted(hashes(train, "rgb") & hashes(heldout, "rgb"))
    identity_overlaps["depth_sha256"] = sorted(hashes(train, "depth") & hashes(heldout, "depth"))
    identity_overlaps["confidence_sha256"] = sorted(hashes(train, "confidence") & hashes(heldout, "confidence"))
    cross_edges = 0; min_center = float("inf"); min_rotation = float("inf"); min_time = float("inf")
    for left in train:
        left_pose = pose(left)
        for right in heldout:
            right_pose = pose(right); dt = abs(float(left["timestamp"])-float(right["timestamp"])); center = float(np.linalg.norm(left_pose[:3,3]-right_pose[:3,3])); rotation = rotation_deg(left_pose, right_pose)
            min_time, min_center, min_rotation = min(min_time, dt), min(min_center, center), min(min_rotation, rotation)
            if dt <= GROUP_TIME_S and center <= GROUP_CENTER_M and rotation <= GROUP_ROTATION_DEG: cross_edges += 1
    duplicate_records = len(train)+len(heldout) - len({(row["timestamp"], row["rgb"], row["depth"], row["confidence"]) for row in train+heldout})
    valid = (registry_groups_match and expected_score is not None and actual_score == expected_score and train_indices.isdisjoint(heldout_indices) and train_indices | heldout_indices == all_keyframes and not fragmented and not any(identity_overlaps.values()) and cross_edges == 0 and len(train) >= 200 and 40 <= len(heldout) <= 60 and duplicate_records == 0)
    output = {"status": "V2_SPLIT_VALIDATION_PASS" if valid else "V2_SPLIT_VALIDATION_FAIL", "video_id": "48018874", "registry_groups_match_independent_reconstruction": registry_groups_match, "n_keyframes": n, "train_count": len(train), "heldout_count": len(heldout), "discarded_frame_count": len(all_keyframes - (train_indices | heldout_indices)), "duplicate_record_count": duplicate_records, "fragmented_groups": fragmented, "identity_overlaps": identity_overlaps, "cross_split_group_edge_count": cross_edges, "minimum_cross_split_center_distance_m": min_center, "minimum_cross_split_orientation_difference_deg": min_rotation, "minimum_cross_split_timestamp_difference_s": min_time, "independent_global_optimal_score": [expected_score[0], expected_score[1], list(expected_score[2])] if expected_score else None, "actual_score": [actual_score[0], actual_score[1], list(actual_score[2])], "selected_group_hash_tuple_sha256": hashlib.sha256("\n".join(actual_selected).encode("utf-8")).hexdigest(), "train_statistics": stats(train), "heldout_statistics": stats(heldout), "asset_root_derived_from_v1_record": "source" if asset_root == candidates[0] else "destination", "random_calls": 0, "no_training": True, "no_mapping": True, "no_geometry_result": True}
    atomic_json(args.task_root / "validation" / "validation_result.json", output)
    if not valid: raise SystemExit("V2_SPLIT_VALIDATION_FAIL")
    print(output["status"], output["selected_group_hash_tuple_sha256"])
    return 0


if __name__ == "__main__": raise SystemExit(main())
