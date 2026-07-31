#!/usr/bin/env python3
"""Deterministic helpers for the ARKitScenes V2 split-only contract."""
from __future__ import annotations

import csv
import hashlib
import json
import math
import os
from pathlib import Path
from typing import Any

import numpy as np

SEED = 20260730
KEYFRAME_TRANSLATION_M = 0.08
KEYFRAME_ROTATION_DEG = 8.0
GROUP_TIME_S = 2.0
GROUP_CENTER_M = 0.15
GROUP_ROTATION_DEG = 15.0


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def canonical_bytes(value: Any) -> bytes:
    return (json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=True) + "\n").encode("utf-8")


def atomic_json(path: Path, value: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary = path.with_suffix(path.suffix + ".tmp")
    temporary.write_bytes(canonical_bytes(value))
    os.replace(temporary, path)


def atomic_csv(path: Path, rows: list[dict[str, Any]], fieldnames: list[str]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary = path.with_suffix(path.suffix + ".tmp")
    with temporary.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=fieldnames, extrasaction="raise")
        writer.writeheader()
        writer.writerows(rows)
    os.replace(temporary, path)


def read_csv(path: Path) -> list[dict[str, str]]:
    with path.open(newline="", encoding="utf-8") as handle:
        return list(csv.DictReader(handle))


def pose(row: dict[str, str]) -> np.ndarray:
    return np.asarray([[float(row[f"c2w_{i}{j}"]) for j in range(4)] for i in range(4)], dtype=np.float64)


def rotation_deg(a: np.ndarray, b: np.ndarray) -> float:
    value = float(np.clip((np.trace(a[:3, :3].T @ b[:3, :3]) - 1.0) / 2.0, -1.0, 1.0))
    return math.degrees(math.acos(value))


def group_hash(video_id: str, group_id: int) -> str:
    return hashlib.sha256(f"ARKITSCENES_GROUP_SPLIT_V1:{video_id}:{group_id}".encode("utf-8")).hexdigest()


def reconstruct_v1(rows: list[dict[str, str]], video_id: str) -> tuple[list[dict[str, str]], list[dict[str, Any]]]:
    """Reproduce V1 selection and component ordering byte-for-byte in semantics."""
    rows = sorted(rows, key=lambda item: float(item["timestamp"]))
    matrices = [pose(row) for row in rows]
    keyframe_indices = [0]
    for index in range(1, len(rows)):
        previous = matrices[keyframe_indices[-1]]
        translation = float(np.linalg.norm(matrices[index][:3, 3] - previous[:3, 3]))
        if translation >= KEYFRAME_TRANSLATION_M or rotation_deg(previous, matrices[index]) >= KEYFRAME_ROTATION_DEG:
            keyframe_indices.append(index)
    if len(keyframe_indices) > 600:
        selected = [keyframe_indices[0]]
        remaining = keyframe_indices[1:]
        while len(selected) < 600:
            candidate = max(remaining, key=lambda item: min(float(np.linalg.norm(matrices[item][:3, 3] - matrices[other][:3, 3])) for other in selected))
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
            if (abs(float(keyframes[left]["timestamp"]) - float(keyframes[right]["timestamp"])) <= GROUP_TIME_S
                    and float(np.linalg.norm(keyposes[left][:3, 3] - keyposes[right][:3, 3])) <= GROUP_CENTER_M
                    and rotation_deg(keyposes[left], keyposes[right]) <= GROUP_ROTATION_DEG):
                union(left, right)
    components: dict[int, list[int]] = {}
    for index in range(len(keyframes)):
        components.setdefault(find(index), []).append(index)
    groups = [{"group_id": group_id, "members": members, "group_hash": group_hash(video_id, group_id)}
              for group_id, members in enumerate(sorted(components.values(), key=lambda item: min(item)))]
    groups.sort(key=lambda item: str(item["group_hash"]))
    return keyframes, groups


def group_dp(groups: list[dict[str, Any]]) -> dict[int, tuple[str, ...]]:
    """Return a count to lexicographically smallest hash tuple map."""
    states: dict[int, tuple[str, ...]] = {0: ()}
    for group in sorted(groups, key=lambda item: str(item["group_hash"])):
        size = len(group["members"])
        group_id = str(group["group_hash"])
        for count, selected in sorted(list(states.items()), reverse=True):
            next_count = count + size
            candidate = selected + (group_id,)
            if next_count not in states or candidate < states[next_count]:
                states[next_count] = candidate
    return states


def tree_sha256(root: Path, names: list[str] | None = None) -> str:
    digest = hashlib.sha256()
    files = [root / name for name in names] if names is not None else sorted(path for path in root.rglob("*") if path.is_file())
    for path in sorted(files, key=lambda item: item.relative_to(root).as_posix()):
        relative = path.relative_to(root).as_posix().encode("utf-8")
        digest.update(len(relative).to_bytes(8, "big")); digest.update(relative)
        payload = path.read_bytes()
        digest.update(len(payload).to_bytes(8, "big")); digest.update(payload)
    return digest.hexdigest()


def v1_path(v1_root: Path, relative: str) -> Path:
    if relative.startswith("arkitscenes_download_manifest_"):
        return v1_root / "download" / relative
    return v1_root / relative


def identity_row(row: dict[str, str]) -> dict[str, str]:
    return {key: row[key] for key in ("rgb", "depth", "confidence", "intrinsics", "pose_timestamp", "timestamp")}
