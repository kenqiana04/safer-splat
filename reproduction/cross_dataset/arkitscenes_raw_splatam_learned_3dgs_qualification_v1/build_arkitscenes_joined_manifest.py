#!/usr/bin/env python3
"""Freeze Apple's documented/raw-loader RGB-D-confidence-intrinsics-pose join."""
from __future__ import annotations

import argparse
import csv
import math
import os
from pathlib import Path

import numpy as np
from PIL import Image

from arkitscenes_common import atomic_json, sha256_file


def timestamp(path: Path, video_id: str) -> float:
    prefix = f"{video_id}_"
    if not path.name.startswith(prefix):
        raise ValueError(f"unexpected asset name: {path.name}")
    return float(path.name[len(prefix):].rsplit(".", 1)[0])


def rodrigues(axis_angle: np.ndarray) -> np.ndarray:
    theta = float(np.linalg.norm(axis_angle))
    if theta == 0.0:
        return np.eye(3)
    axis = axis_angle / theta
    skew = np.array([[0.0, -axis[2], axis[1]], [axis[2], 0.0, -axis[0]], [-axis[1], axis[0], 0.0]])
    return np.eye(3) + math.sin(theta) * skew + (1.0 - math.cos(theta)) * (skew @ skew)


def parse_trajectory(path: Path) -> list[tuple[float, np.ndarray]]:
    result: list[tuple[float, np.ndarray]] = []
    for line_number, line in enumerate(path.read_text(encoding="utf-8").splitlines(), 1):
        values = [float(value) for value in line.split()]
        if len(values) != 7 or not np.isfinite(values).all():
            raise ValueError(f"nonfinite or malformed trajectory line {line_number}")
        world_to_pose = np.eye(4)
        world_to_pose[:3, :3] = rodrigues(np.asarray(values[1:4]))
        world_to_pose[:3, 3] = np.asarray(values[4:7])
        result.append((values[0], np.linalg.inv(world_to_pose)))
    if not result:
        raise ValueError("empty trajectory")
    return result


def parse_intrinsics(path: Path) -> tuple[int, int, float, float, float, float]:
    values = [float(value) for value in path.read_text(encoding="utf-8").split()]
    if len(values) != 6 or not np.isfinite(values).all():
        raise ValueError(f"malformed intrinsics: {path}")
    width, height = int(values[0]), int(values[1])
    return width, height, *values[2:]


def choose_intrinsics(table: dict[float, Path], value: float) -> tuple[float, Path] | None:
    for candidate in (value, round(value - 0.001, 3), round(value + 0.001, 3)):
        if candidate in table:
            return candidate, table[candidate]
    return None


def choose_pose(entries: list[tuple[float, np.ndarray]], value: float) -> tuple[float, np.ndarray] | None:
    exact = round(value, 3)
    matches = [(abs(ts - exact), ts, pose) for ts, pose in entries if abs(ts - exact) < 0.005]
    if not matches:
        return None
    _, ts, pose = min(matches, key=lambda item: (item[0], item[1]))
    return ts, pose


def write_csv(path: Path, rows: list[dict[str, object]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary = path.with_suffix(path.suffix + ".tmp")
    fields = list(rows[0]) if rows else ["video_id", "timestamp"]
    with temporary.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=fields)
        writer.writeheader()
        writer.writerows(rows)
    os.replace(temporary, path)


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--task-root", type=Path, required=True)
    parser.add_argument("--candidate-root", type=Path, required=True)
    parser.add_argument("--video-id", required=True)
    parser.add_argument("--apple-source", type=Path, required=True)
    args = parser.parse_args()
    root, task, source = args.candidate_root.resolve(), args.task_root.resolve(), args.apple_source.resolve()
    image_dirs = {name: root / name for name in ("lowres_wide", "lowres_depth", "confidence")}
    tables = {name: {timestamp(path, args.video_id): path for path in directory.glob("*.png")} for name, directory in image_dirs.items()}
    intrinsics = {timestamp(path, args.video_id): path for path in (root / "lowres_wide_intrinsics").glob("*.pincam")}
    trajectory = parse_trajectory(root / "lowres_wide.traj")
    rows: list[dict[str, object]] = []
    skipped = {"missing_rgb": 0, "missing_confidence": 0, "missing_intrinsics": 0, "missing_pose": 0, "dimension_or_decode": 0}
    for value in sorted(tables["lowres_depth"]):
        rgb, confidence = tables["lowres_wide"].get(value), tables["confidence"].get(value)
        if rgb is None:
            skipped["missing_rgb"] += 1
            continue
        if confidence is None:
            skipped["missing_confidence"] += 1
            continue
        intrinsic_choice, pose_choice = choose_intrinsics(intrinsics, value), choose_pose(trajectory, value)
        if intrinsic_choice is None:
            skipped["missing_intrinsics"] += 1
            continue
        if pose_choice is None:
            skipped["missing_pose"] += 1
            continue
        intrinsic_ts, intrinsic_path = intrinsic_choice
        pose_ts, pose = pose_choice
        try:
            width, height, fx, fy, cx, cy = parse_intrinsics(intrinsic_path)
            rgb_shape = np.asarray(Image.open(rgb)).shape
            depth_shape = np.asarray(Image.open(tables["lowres_depth"][value])).shape
            confidence_shape = np.asarray(Image.open(confidence)).shape
            if rgb_shape[:2] != depth_shape or depth_shape != confidence_shape or (width, height) != (rgb_shape[1], rgb_shape[0]):
                raise ValueError("raw image/intrinsics dimensions disagree")
        except Exception:
            skipped["dimension_or_decode"] += 1
            continue
        row: dict[str, object] = {
            "video_id": args.video_id, "timestamp": f"{value:.3f}",
            "rgb": rgb.relative_to(root).as_posix(), "depth": tables["lowres_depth"][value].relative_to(root).as_posix(),
            "confidence": confidence.relative_to(root).as_posix(), "intrinsics": intrinsic_path.relative_to(root).as_posix(),
            "pose_timestamp": f"{pose_ts:.8f}", "pose_delta_s": f"{abs(pose_ts - round(value, 3)):.8f}",
            "intrinsics_timestamp": f"{intrinsic_ts:.3f}", "intrinsics_delta_s": f"{abs(intrinsic_ts-value):.3f}",
            "width": width, "height": height, "fx": fx, "fy": fy, "cx": cx, "cy": cy,
        }
        row.update({f"c2w_{i}{j}": f"{pose[i, j]:.12g}" for i in range(4) for j in range(4)})
        rows.append(row)
    output = task / "frame_join" / args.video_id
    manifest = output / "arkitscenes_joined_frame_manifest.csv"
    write_csv(manifest, rows)
    status = "FRAME_JOIN_PASS" if len(rows) >= 300 else "BLOCKED_BY_ARKITSCENES_DATA_OR_COORDINATE_CONTRACT"
    loader = source / "threedod" / "benchmark_scripts" / "utils" / "tenFpsDataLoader.py"
    contract = {
        "status": status, "video_id": args.video_id, "joined_frame_count": len(rows), "skipped": skipped,
        "raw_sync_contract": "exact RGB/depth/confidence timestamp; intrinsic exact then -0.001 then +0.001 seconds",
        "pose_contract": "official trajectory rounded-to-0.001 lookup; deterministic nearest tie-break; abs(delta)<0.005; no interpolation or extrapolation",
        "pose_direction": "camera_to_world; official loader returns inv(world_to_pose) as Rt",
        "depth_unit": "uint16 millimetres; later conversion factor=0.001 m/mm",
        "official_loader": str(loader), "official_loader_sha256": sha256_file(loader),
        "trajectory_sha256": sha256_file(root / "lowres_wide.traj"), "joined_manifest_sha256": sha256_file(manifest),
    }
    atomic_json(output / "arkitscenes_frame_join_contract.json", contract)
    audit = output / "arkitscenes_pose_convention_audit.md"
    audit.write_text("# ARKitScenes pose and join convention audit\n\n"
                     "The frozen Apple DATA.md specifies axis-angle radians and translation in metres. "
                     "The frozen Apple `TrajStringToMatrix` constructs world-to-pose then returns its inverse, "
                     "therefore the joined manifest stores camera-to-world matrices. Matching uses the official "
                     "loader's depth-led exact RGB/depth/confidence timestamps, intrinsic +/-1 ms fallback, and "
                     "trajectory 1 ms indexing with a strict <5 ms pose tolerance; no interpolation or extrapolation.\n", encoding="utf-8")
    print(status, f"joined={len(rows)}")
    return 0 if status == "FRAME_JOIN_PASS" else 2


if __name__ == "__main__":
    raise SystemExit(main())
