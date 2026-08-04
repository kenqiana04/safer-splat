#!/usr/bin/env python3
"""Audit the frozen ETH3D RGB/COLMAP payload and freeze POSE_BLOCK_SPLIT_V1."""

from __future__ import annotations

import hashlib
import csv
import json
import math
from collections import Counter, defaultdict
from pathlib import Path

import numpy as np
from PIL import Image

from colmap_text import (camera_center, camera_to_world, read_cameras, read_images,
                         read_points3d, rotation_angle_deg, sha256_file)
from task_config import QUARANTINE, TASK_ROOT


SEED = 20260804
MAIN_HELDOUT = 0.20
MAIN_REGIONS = 5
MAIN_GUARD_MULTIPLIER = 1.0


def canonical_sha(value) -> str:
    return hashlib.sha256(json.dumps(value, sort_keys=True, separators=(",", ":")).encode("utf-8")).hexdigest()


def save(path: Path, value) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(value, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def model_root(archive_stem: str, calibration_name: str) -> Path:
    path = QUARANTINE / archive_stem / "delivery_area" / calibration_name
    for name in ("cameras.txt", "images.txt", "points3D.txt"):
        if not (path / name).is_file():
            raise RuntimeError(f"MISSING_COLMAP_COMPONENT {path / name}")
    return path


def image_root(archive_stem: str) -> Path:
    path = QUARANTINE / archive_stem / "delivery_area" / "images"
    if not path.is_dir():
        raise RuntimeError(f"MISSING_IMAGE_ROOT {path}")
    return path


def validate_images(root: Path, images: dict, cameras: dict) -> dict:
    seen_hashes = defaultdict(list)
    missing, unreadable, dimension_mismatch = [], [], []
    for image in images.values():
        path = root / image["name"]
        if not path.is_file():
            missing.append(image["name"])
            continue
        seen_hashes[sha256_file(path)].append(image["name"])
        try:
            with Image.open(path) as handle:
                handle.verify()
            with Image.open(path) as handle:
                size = handle.size
        except Exception as exc:
            unreadable.append({"name": image["name"], "error": repr(exc)})
            continue
        camera = cameras[image["camera_id"]]
        if size != (camera["width"], camera["height"]):
            dimension_mismatch.append({"name": image["name"], "image_size": size,
                                       "camera_size": [camera["width"], camera["height"]]})
    duplicate_groups = [names for names in seen_hashes.values() if len(names) > 1]
    return {
        "expected_records": len(images), "existing_files": len(images) - len(missing),
        "missing": missing, "unreadable": unreadable,
        "dimension_mismatch": dimension_mismatch,
        "unique_byte_sha256_count": len(seen_hashes), "duplicate_byte_groups": duplicate_groups,
        "status": "PASS" if not (missing or unreadable or dimension_mismatch or duplicate_groups) else "FAIL",
    }


def split_capture_name(name: str) -> tuple:
    path = Path(name)
    folder = path.parent.name
    if "images_rig_cam" not in folder or not folder.endswith("_undistorted"):
        raise RuntimeError(f"UNEXPECTED_RIG_IMAGE_NAME {name}")
    camera_label = folder[len("images_rig_"):-len("_undistorted")]
    return path.stem, camera_label


def group_rig(images: dict) -> dict:
    groups = defaultdict(list)
    for image in images.values():
        capture, camera = split_capture_name(image["name"])
        item = dict(image)
        item["capture"] = capture
        item["camera_label"] = camera
        groups[capture].append(item)
    return dict(groups)


def fixed_rig_audit(groups: dict) -> dict:
    labels = sorted({image["camera_label"] for group in groups.values() for image in group})
    reference = labels[0]
    relative = defaultdict(list)
    for capture in sorted(groups):
        by_label = {image["camera_label"]: image for image in groups[capture]}
        if set(by_label) != set(labels):
            raise RuntimeError(f"INCOMPLETE_RIG_CAPTURE {capture} {sorted(by_label)}")
        world_from_ref = camera_to_world(by_label[reference])
        ref_from_world = np.linalg.inv(world_from_ref)
        for label in labels:
            relative[label].append(ref_from_world @ camera_to_world(by_label[label]))
    per_camera = {}
    for label in labels:
        anchor = relative[label][0]
        translation_errors = [float(np.linalg.norm(value[:3, 3] - anchor[:3, 3])) for value in relative[label]]
        rotation_errors = [rotation_angle_deg(anchor[:3, :3].T @ value[:3, :3]) for value in relative[label]]
        per_camera[label] = {
            "max_translation_deviation_m": max(translation_errors),
            "max_rotation_deviation_deg": max(rotation_errors),
        }
    max_t = max(value["max_translation_deviation_m"] for value in per_camera.values())
    max_r = max(value["max_rotation_deviation_deg"] for value in per_camera.values())
    return {"reference_camera": reference, "camera_labels": labels, "per_camera": per_camera,
            "max_translation_deviation_m": max_t, "max_rotation_deviation_deg": max_r,
            "status": "PASS" if max_t <= 1e-4 and max_r <= 1e-3 else "FAIL"}


def capture_centers(groups: dict) -> dict:
    return {capture: np.mean([camera_center(image) for image in group], axis=0)
            for capture, group in groups.items()}


def nearest_neighbor_median(centers: dict) -> float:
    array = np.stack([centers[key] for key in sorted(centers)])
    distance = np.linalg.norm(array[:, None, :] - array[None, :, :], axis=-1)
    np.fill_diagonal(distance, np.inf)
    return float(np.median(np.min(distance, axis=1)))


def tie_hash(capture: str) -> str:
    return hashlib.sha256(capture.encode("ascii")).hexdigest()


def farthest_anchors(centers: dict, count: int) -> list:
    ordered = sorted(centers, key=lambda value: (tie_hash(value), value))
    anchors = [ordered[0]]
    while len(anchors) < count:
        candidates = []
        for capture in ordered:
            if capture in anchors:
                continue
            minimum = min(float(np.linalg.norm(centers[capture] - centers[a])) for a in anchors)
            candidates.append((-minimum, tie_hash(capture), capture))
        anchors.append(min(candidates)[2])
    return anchors


def build_split(centers: dict, heldout_fraction: float, guard_multiplier: float) -> dict:
    anchors = farthest_anchors(centers, MAIN_REGIONS)
    target = int(math.ceil(len(centers) * heldout_fraction))
    heldout = list(anchors)
    heldout_region = {anchor: anchor for anchor in anchors}
    while len(heldout) < target:
        progress = False
        for anchor in anchors:
            if len(heldout) >= target:
                break
            remaining = [capture for capture in centers if capture not in heldout]
            if not remaining:
                break
            selected = min(remaining, key=lambda capture: (
                float(np.linalg.norm(centers[capture] - centers[anchor])), tie_hash(capture), capture))
            heldout.append(selected)
            heldout_region[selected] = anchor
            progress = True
        if not progress:
            raise RuntimeError("POSE_BLOCK_HELDOUT_GROWTH_STALLED")
    heldout = sorted(set(heldout))
    radius = guard_multiplier * nearest_neighbor_median(centers)
    guard = sorted(capture for capture in centers if capture not in heldout and
                   min(float(np.linalg.norm(centers[capture] - centers[h])) for h in heldout) < radius)
    train = sorted(set(centers) - set(heldout) - set(guard))
    return {
        "algorithm": "POSE_BLOCK_SPLIT_V1", "seed": SEED,
        "target_heldout_fraction": heldout_fraction, "target_region_count": MAIN_REGIONS,
        "guard_radius_multiplier": guard_multiplier,
        "median_nn_center_distance_m": nearest_neighbor_median(centers),
        "guard_radius_m": radius, "sha_anchor": anchors[0], "farthest_point_anchors": anchors,
        "group_identity_sha256": {capture: tie_hash(capture) for capture in sorted(centers)},
        "heldout_region_anchor": {capture: heldout_region[capture] for capture in sorted(heldout_region)},
        "TRAIN": train, "HELDOUT": heldout, "GUARD": guard,
        "counts": {"TRAIN": len(train), "HELDOUT": len(heldout), "GUARD": len(guard)},
    }


def main() -> None:
    rig_model_path = model_root("delivery_area_rig_undistorted", "rig_calibration_undistorted")
    dslr_model_path = model_root("delivery_area_dslr_undistorted", "dslr_calibration_undistorted")
    rig_cameras, dslr_cameras = read_cameras(rig_model_path / "cameras.txt"), read_cameras(dslr_model_path / "cameras.txt")
    rig_images, dslr_images = read_images(rig_model_path / "images.txt"), read_images(dslr_model_path / "images.txt")
    rig_points, dslr_points = read_points3d(rig_model_path / "points3D.txt"), read_points3d(dslr_model_path / "points3D.txt")
    if set(camera["model"] for camera in list(rig_cameras.values()) + list(dslr_cameras.values())) - {"PINHOLE", "SIMPLE_PINHOLE"}:
        raise RuntimeError("UNSUPPORTED_CAMERA_MODEL")
    if any(not np.isfinite(np.r_[image["qvec"], image["tvec"]]).all() for image in list(rig_images.values()) + list(dslr_images.values())):
        raise RuntimeError("NONFINITE_POSE")
    groups = group_rig(rig_images)
    group_sizes = Counter(len(group) for group in groups.values())
    if len(rig_images) != 948 or len(groups) != 237 or group_sizes != Counter({4: 237}):
        raise RuntimeError(f"RIG_COUNT_CONTRACT_FAILURE {len(rig_images)} {len(groups)} {group_sizes}")
    if len(dslr_images) != 44:
        raise RuntimeError(f"DSLR_COUNT_CONTRACT_FAILURE {len(dslr_images)}")
    rig_image_audit = validate_images(image_root("delivery_area_rig_undistorted"), rig_images, rig_cameras)
    dslr_image_audit = validate_images(image_root("delivery_area_dslr_undistorted"), dslr_images, dslr_cameras)
    rig_extrinsics = fixed_rig_audit(groups)
    if rig_image_audit["status"] != "PASS" or dslr_image_audit["status"] != "PASS" or rig_extrinsics["status"] != "PASS":
        raise RuntimeError("RGB_OR_RIG_GEOMETRY_AUDIT_FAILURE")
    all_track_ids = {image_id for point in rig_points.values() for image_id, _ in point["track"]}
    if not all_track_ids.issubset(rig_images):
        raise RuntimeError("RIG_POINT_TRACK_REFERENCES_UNKNOWN_IMAGE")
    dslr_track_ids = {image_id for point in dslr_points.values() for image_id, _ in point["track"]}
    if not dslr_track_ids.issubset(dslr_images):
        raise RuntimeError("DSLR_POINT_TRACK_REFERENCES_UNKNOWN_IMAGE")
    for label, points in (("rig", rig_points), ("dslr", dslr_points)):
        if any(not np.isfinite(np.r_[point["xyz"], point["error"]]).all() or
               any(channel < 0 or channel > 255 for channel in point["rgb"]) for point in points.values()):
            raise RuntimeError(f"NONFINITE_OR_INVALID_SPARSE_POINT {label}")
    centers = capture_centers(groups)
    split = build_split(centers, MAIN_HELDOUT, MAIN_GUARD_MULTIPLIER)
    split["capture_centers_m"] = {key: [float(x) for x in centers[key]] for key in sorted(centers)}
    split["split_sha256"] = canonical_sha({key: split[key] for key in ("algorithm", "seed", "target_heldout_fraction",
                                                                         "target_region_count", "guard_radius_multiplier",
                                                                         "sha_anchor", "farthest_point_anchors", "TRAIN", "HELDOUT", "GUARD")})
    train_fraction = len(split["TRAIN"]) / len(centers)
    heldout_fraction = len(split["HELDOUT"]) / len(centers)
    guard_fraction = len(split["GUARD"]) / len(centers)
    min_train_heldout = min(float(np.linalg.norm(centers[train] - centers[heldout]))
                            for train in split["TRAIN"] for heldout in split["HELDOUT"])
    if not (0.15 <= heldout_fraction <= 0.25 and train_fraction >= 0.60 and guard_fraction <= 0.25):
        raise RuntimeError(f"POSE_BLOCK_SPLIT_FRACTION_GATE {train_fraction} {heldout_fraction} {guard_fraction}")
    if min_train_heldout < split["guard_radius_m"]:
        raise RuntimeError(f"POSE_BLOCK_SPLIT_DISTANCE_GATE {min_train_heldout} {split['guard_radius_m']}")
    train_camera_ids = {image["camera_id"] for capture in split["TRAIN"] for image in groups[capture]}
    if train_camera_ids != set(rig_cameras):
        raise RuntimeError(f"TRAIN_CAMERA_COVERAGE_FAILURE {sorted(train_camera_ids)}")
    if len(set(split["heldout_region_anchor"].values())) < 3:
        raise RuntimeError("HELDOUT_REGION_COUNT_FAILURE")
    split["fraction_validation"] = {"TRAIN": train_fraction, "HELDOUT": heldout_fraction, "GUARD": guard_fraction}
    split["min_train_heldout_center_distance_m"] = min_train_heldout
    split["partition_overlap_counts"] = {"group": 0, "image": 0, "same_capture_cross_partition": 0}
    split["train_camera_ids"] = sorted(train_camera_ids)
    sensitivity = []
    for fraction in (0.15, 0.20, 0.25):
        for guard in (0.5, 1.0, 1.5, 2.0):
            variant = build_split(centers, fraction, guard)
            sensitivity.append({"heldout_fraction": fraction, "guard_multiplier": guard, "counts": variant["counts"],
                                "identity_sha256": canonical_sha({k: variant[k] for k in ("TRAIN", "HELDOUT", "GUARD")})})
    record = {
        "status": "PASS_RIG_DSLR_ASSET_AUDIT",
        "selected_modality": "LOW_RES_MANY_VIEW_RIG_RGB_ONLY",
        "fallback_triggered": False,
        "rig": {"image_count": len(rig_images), "capture_group_count": len(groups),
                "camera_count": len(rig_cameras), "group_size_histogram": dict(group_sizes),
                "camera_models": sorted({camera["model"] for camera in rig_cameras.values()}),
                "sparse_point_count": len(rig_points), "image_audit": rig_image_audit,
                "fixed_rig_extrinsics": rig_extrinsics},
        "dslr": {"image_count": len(dslr_images), "camera_count": len(dslr_cameras),
                 "camera_models": sorted({camera["model"] for camera in dslr_cameras.values()}),
                 "sparse_point_count": len(dslr_points), "image_audit": dslr_image_audit,
                 "role": "CROSS_VIEW_EVALUATION_ONLY"},
        "sparse_point_provenance": "OFFICIAL_COLMAP_IMAGE_TRIANGULATION_WITH_IMAGE_TRACKS",
        "laser_scan_used_for_sparse_points": False,
        "pose_convention": "COLMAP_WORLD_TO_CAMERA_QVEC_TVEC",
        "official_metric_world_transform_applied_by_task": False,
        "icp_count": 0, "sim3_count": 0, "scale_repair_count": 0,
    }
    save(TASK_ROOT / "asset_validation" / "rig_dslr_colmap_asset_audit.json", record)
    save(TASK_ROOT / "calibration" / "rig_fixed_extrinsics_audit.json", rig_extrinsics)
    save(TASK_ROOT / "split" / "pose_block_split_v1.json", split)
    save(TASK_ROOT / "split" / "pose_block_split_v1_contract.json", split)
    save(TASK_ROOT / "split" / "final_split_identity.json", {
        "status": "PASS", "split_sha256": split["split_sha256"], "counts": split["counts"]})
    for partition in ("TRAIN", "HELDOUT", "GUARD"):
        with (TASK_ROOT / "split" / f"final_{partition.lower()}_group_manifest.csv").open("w", newline="", encoding="utf-8") as stream:
            writer = csv.writer(stream)
            writer.writerow(["capture_group", "group_identity_sha256", "center_x_m", "center_y_m", "center_z_m"])
            for capture in split[partition]:
                writer.writerow([capture, split["group_identity_sha256"][capture], *split["capture_centers_m"][capture]])
    save(TASK_ROOT / "split" / "pose_block_split_sensitivity.json", {
        "status": "REPORT_ONLY_MAIN_SPLIT_UNCHANGED", "main_split_sha256": split["split_sha256"], "variants": sensitivity})
    save(TASK_ROOT / "split" / "source_model_paths.json", {
        "rig_model": str(rig_model_path), "dslr_model": str(dslr_model_path),
        "rig_image_root": str(image_root("delivery_area_rig_undistorted")),
        "dslr_image_root": str(image_root("delivery_area_dslr_undistorted"))})
    print("PASS_RIG_DSLR_SPLIT", split["counts"], split["split_sha256"])


if __name__ == "__main__":
    main()
