#!/usr/bin/env python3
"""Freeze a spatially grouped ARKitScenes TRAIN/HELDOUT split before mapping."""
from __future__ import annotations

import argparse
import csv
import hashlib
import math
import os
from pathlib import Path

import numpy as np

from arkitscenes_common import atomic_json, sha256_file


SEED = 20260730


def pose(row: dict[str, str]) -> np.ndarray:
    return np.asarray([[float(row[f"c2w_{i}{j}"]) for j in range(4)] for i in range(4)])


def rotation_deg(a: np.ndarray, b: np.ndarray) -> float:
    value = (np.trace(a[:3, :3].T @ b[:3, :3]) - 1.0) / 2.0
    return math.degrees(math.acos(float(np.clip(value, -1.0, 1.0))))


def group_hash(video_id: str, group_id: int) -> str:
    return hashlib.sha256(f"ARKITSCENES_GROUP_SPLIT_V1:{video_id}:{group_id}".encode("utf-8")).hexdigest()


def subset(groups: list[dict[str, object]], target: int) -> tuple[int, ...] | None:
    states: dict[int, tuple[int, ...]] = {0: ()}
    for index, group in enumerate(groups):
        size = len(group["members"])
        for count, selected in sorted(list(states.items()), reverse=True):
            next_count = count + size
            if next_count > target:
                continue
            candidate = selected + (index,)
            if next_count not in states or candidate < states[next_count]:
                states[next_count] = candidate
    return states.get(target)


def write_csv(path: Path, rows: list[dict[str, str]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary = path.with_suffix(path.suffix + ".tmp")
    with temporary.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=list(rows[0]))
        writer.writeheader()
        writer.writerows(rows)
    os.replace(temporary, path)


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--task-root", type=Path, required=True)
    parser.add_argument("--candidate-root", type=Path, required=True)
    parser.add_argument("--video-id", required=True)
    args = parser.parse_args()
    task, candidate_root = args.task_root.resolve(), args.candidate_root.resolve()
    joined_path = task / "frame_join" / args.video_id / "arkitscenes_joined_frame_manifest.csv"
    with joined_path.open(newline="", encoding="utf-8") as handle:
        rows = sorted(csv.DictReader(handle), key=lambda item: float(item["timestamp"]))
    matrices = [pose(row) for row in rows]
    keyframe_indices = [0]
    for index in range(1, len(rows)):
        previous = matrices[keyframe_indices[-1]]
        translation = float(np.linalg.norm(matrices[index][:3, 3] - previous[:3, 3]))
        if translation >= 0.08 or rotation_deg(previous, matrices[index]) >= 8.0:
            keyframe_indices.append(index)
    if len(keyframe_indices) > 600:
        selected = [keyframe_indices[0]]
        remaining = keyframe_indices[1:]
        while len(selected) < 600:
            candidate = max(remaining, key=lambda item: min(np.linalg.norm(matrices[item][:3, 3] - matrices[other][:3, 3]) for other in selected))
            selected.append(candidate)
            remaining.remove(candidate)
        keyframe_indices = sorted(selected)
    keyframes = [rows[index] for index in keyframe_indices]
    keyposes = [matrices[index] for index in keyframe_indices]
    parent = list(range(len(keyframes)))
    def find(value: int) -> int:
        while parent[value] != value:
            parent[value] = parent[parent[value]]
            value = parent[value]
        return value
    def union(left: int, right: int) -> None:
        left, right = find(left), find(right)
        if left != right:
            parent[right] = left
    for left in range(len(keyframes)):
        for right in range(left + 1, len(keyframes)):
            if (abs(float(keyframes[left]["timestamp"]) - float(keyframes[right]["timestamp"])) <= 2.0 and
                    np.linalg.norm(keyposes[left][:3, 3] - keyposes[right][:3, 3]) <= 0.15 and
                    rotation_deg(keyposes[left], keyposes[right]) <= 15.0):
                union(left, right)
    components: dict[int, list[int]] = {}
    for index in range(len(keyframes)):
        components.setdefault(find(index), []).append(index)
    groups = [{"group_id": group_id, "members": members, "hash": group_hash(args.video_id, group_id)}
              for group_id, members in enumerate(sorted(components.values(), key=lambda item: min(item)))]
    groups.sort(key=lambda item: item["hash"])
    train_groups = subset(groups, 240)
    remaining = [group for index, group in enumerate(groups) if train_groups is None or index not in train_groups]
    heldout_groups = subset(remaining, 60) if train_groups is not None else None
    train_indices = {member for index in train_groups or () for member in groups[index]["members"]}
    heldout_indices = {member for index in heldout_groups or () for member in remaining[index]["members"]}
    train = [keyframes[index] | {"split": "TRAIN"} for index in sorted(train_indices)]
    heldout = [keyframes[index] | {"split": "HELDOUT"} for index in sorted(heldout_indices)]
    exact = len(train) == 240 and len(heldout) == 60
    status = "FRAME_SPLIT_PASS" if exact else "BLOCKED_BY_ARKITSCENES_DATA_OR_COORDINATE_CONTRACT"
    output = task / "frame_split" / args.video_id
    if train:
        write_csv(output / "arkitscenes_train_manifest.csv", train)
    if heldout:
        write_csv(output / "arkitscenes_heldout_manifest.csv", heldout)
    train_rgb_depth = {(sha256_file(candidate_root / row["rgb"]), sha256_file(candidate_root / row["depth"])) for row in train}
    heldout_rgb_depth = {(sha256_file(candidate_root / row["rgb"]), sha256_file(candidate_root / row["depth"])) for row in heldout}
    checks = {"filename_overlap": sorted({row["rgb"] for row in train} & {row["rgb"] for row in heldout}),
              "pose_timestamp_overlap": sorted({row["pose_timestamp"] for row in train} & {row["pose_timestamp"] for row in heldout}),
              "rgb_depth_duplicate_hash_overlap": sorted(train_rgb_depth & heldout_rgb_depth),
              "rgb_depth_duplicate_hash_checked": True}
    contract = {"status": status, "video_id": args.video_id, "seed": SEED, "joined_manifest_sha256": sha256_file(joined_path),
                "keyframe_count": len(keyframes), "group_count": len(groups), "group_sizes": [len(group["members"]) for group in groups],
                "group_contract": "connected iff camera-center<=0.15m AND orientation geodesic<=15deg AND timestamp delta<=2.0s",
                "keyframe_contract": "first then translation>=0.08m OR rotation>=8deg; deterministic farthest-pose downsample only above 600",
                "train_count": len(train), "heldout_count": len(heldout), "checks": checks,
                "train_manifest_sha256": sha256_file(output / "arkitscenes_train_manifest.csv") if train else None,
                "heldout_manifest_sha256": sha256_file(output / "arkitscenes_heldout_manifest.csv") if heldout else None}
    atomic_json(output / "arkitscenes_frame_split_contract.json", contract)
    print(status, f"keyframes={len(keyframes)}", f"groups={len(groups)}", f"train={len(train)}", f"heldout={len(heldout)}")
    return 0 if status == "FRAME_SPLIT_PASS" else 2


if __name__ == "__main__":
    raise SystemExit(main())
