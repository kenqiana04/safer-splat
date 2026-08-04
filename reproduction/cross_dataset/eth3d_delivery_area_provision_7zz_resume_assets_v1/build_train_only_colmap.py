#!/usr/bin/env python3
"""Build one deterministic train-only COLMAP model without invoking COLMAP."""

from __future__ import annotations

import argparse
import json
import os
import shutil
from pathlib import Path

from archive_common import tree_identity
from colmap_text import read_cameras, read_images, read_points3d, write_cameras, write_images, write_points3d
from task_config import QUARANTINE, TASK_ROOT


def safe_reset(path: Path, allowed_root: Path) -> None:
    resolved, root = path.resolve(), allowed_root.resolve()
    if root not in resolved.parents:
        raise RuntimeError(f"UNSAFE_BUILD_RESET {resolved}")
    if path.exists():
        shutil.rmtree(path)
    path.mkdir(parents=True)


def hardlink(source: Path, target: Path) -> None:
    target.parent.mkdir(parents=True, exist_ok=True)
    try:
        os.link(str(source), str(target))
    except OSError:
        shutil.copy2(str(source), str(target))


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--allowed-root", type=Path, required=True)
    args = parser.parse_args()
    safe_reset(args.output, args.allowed_root)
    split = json.loads((TASK_ROOT / "split" / "pose_block_split_v1.json").read_text(encoding="utf-8"))
    train_captures = set(split["TRAIN"])
    source_model = QUARANTINE / "delivery_area_rig_undistorted" / "delivery_area" / "rig_calibration_undistorted"
    source_images = QUARANTINE / "delivery_area_rig_undistorted" / "delivery_area" / "images"
    cameras = read_cameras(source_model / "cameras.txt")
    images = read_images(source_model / "images.txt")
    points = read_points3d(source_model / "points3D.txt")
    train_images = {image_id: image for image_id, image in images.items() if Path(image["name"]).stem in train_captures}
    train_ids = set(train_images)
    filtered_points = {}
    for point_id, point in points.items():
        track = [(image_id, index) for image_id, index in point["track"] if image_id in train_ids]
        if len(track) >= 2:
            item = dict(point)
            item["track"] = track
            filtered_points[point_id] = item
    used_camera_ids = {image["camera_id"] for image in train_images.values()}
    filtered_cameras = {camera_id: camera for camera_id, camera in cameras.items() if camera_id in used_camera_ids}
    model_out = args.output / "sparse" / "0"
    model_out.mkdir(parents=True)
    write_cameras(model_out / "cameras.txt", filtered_cameras)
    write_images(model_out / "images.txt", train_images, set(filtered_points))
    write_points3d(model_out / "points3D.txt", filtered_points)
    for image in train_images.values():
        hardlink(source_images / image["name"], args.output / "images" / image["name"])
    metadata = {
        "status": "PASS_TRAIN_ONLY_COLMAP_BUILD",
        "source": "OFFICIAL_RIG_COLMAP_TEXT_MODEL_FILTERED_WITHOUT_COLMAP_EXECUTION",
        "split_sha256": split["split_sha256"],
        "capture_count": len(train_captures), "image_count": len(train_images),
        "camera_count": len(filtered_cameras), "point3d_count": len(filtered_points),
        "nontrain_image_record_count": 0,
        "points_with_fewer_than_two_train_observations": 0,
        "new_triangulation_count": 0, "colmap_execution_count": 0,
        "reference_point_injection_count": 0,
    }
    (args.output / "TRAIN_ONLY_COLMAP_CONTRACT.json").write_text(json.dumps(metadata, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    (args.output / "SPLIT_IDENTITY.json").write_text(json.dumps({"split_sha256": split["split_sha256"]}, indent=2) + "\n", encoding="utf-8")
    identity = tree_identity(args.output)
    summary = {**metadata, **{key: identity[key] for key in ("tree_sha256", "file_count", "total_bytes")}}
    print(json.dumps(summary, sort_keys=True))


if __name__ == "__main__":
    main()
