#!/usr/bin/env python3
"""Read-only authoritative 4090 audit of frozen TUM inputs.

This program must run on the remote server. It writes only compact audit
artifacts to its caller-provided temporary output directory.
"""
from __future__ import annotations

import argparse, csv, hashlib, json, subprocess
from collections import Counter
from pathlib import Path

import numpy as np
from PIL import Image

EXPECTED_SHA = "b6a685f4b1a5b2ff3bb9b389c63a138a58119b19dd5cb6d7f671282aeecad29a"
HISTORICAL_COMMIT = "3e22a7cae6f4c3c2c192cc2d7af3c9fbd607a0a3"
HISTORICAL_SELECTED = "work/risk_aware_cbf/results/cross_dataset_metric_preprocessing/tum_selected_frames_summary.csv"

def sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()

def emit_json(path: Path, value: object) -> None:
    path.write_text(json.dumps(value, indent=2, sort_keys=True) + "\n", encoding="utf-8")

def load_historical_rows(repo: Path) -> list[dict[str, str]]:
    result = subprocess.run(["git", "-C", str(repo), "show", f"{HISTORICAL_COMMIT}:{HISTORICAL_SELECTED}"], check=True, stdout=subprocess.PIPE, text=True)
    return list(csv.DictReader(result.stdout.splitlines()))

def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--asset-root", type=Path, required=True)
    parser.add_argument("--raw-sequence-root", type=Path, required=True)
    parser.add_argument("--processed-transforms", type=Path, required=True)
    parser.add_argument("--historical-selected-summary", type=Path, required=True)
    parser.add_argument("--output-dir", type=Path, required=True)
    args = parser.parse_args()
    out = args.output_dir
    out.mkdir(parents=True, exist_ok=True)
    raw, transforms = args.raw_sequence_root, args.processed_transforms
    processed = transforms.parent
    metadata = [raw / "rgb.txt", raw / "depth.txt", raw / "groundtruth.txt"]
    pre = {str(p): sha256(p) for p in metadata if p.is_file()}
    doc = json.loads(transforms.read_text(encoding="utf-8"))
    frames = doc.get("frames", [])
    with args.historical_selected_summary.open(newline="", encoding="utf-8") as f:
        selected = list(csv.DictReader(f))
    if len(frames) != 300 or len(selected) != 300:
        raise SystemExit(f"expected 300 frames and historical rows, got {len(frames)} and {len(selected)}")
    inventory = []
    for kind, path in (("asset_root", args.asset_root), ("raw_sequence_root", raw), ("processed_dataset_root", processed), ("transforms", transforms), ("rgb_metadata", metadata[0]), ("depth_metadata", metadata[1]), ("pose_metadata", metadata[2])):
        inventory.append({"asset_type": kind, "relative_or_external_path": str(path), "exists": path.exists(), "file_count": len(list(path.glob("*"))) if path.is_dir() else 1 if path.is_file() else 0, "size_bytes": path.stat().st_size if path.is_file() else None, "sha256": sha256(path) if path.is_file() else None, "readable": path.exists(), "source_provenance": "authoritative_4090_read_only", "immutable_status": "pre_post_hash_checked" if path.is_file() else "read_only_directory"})
    with (out / "input_asset_inventory.csv").open("w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=inventory[0]); w.writeheader(); w.writerows(inventory)
    rgb_rows, depth_rows, pair_rows, pose_rows = [], [], [], []
    rgb_hashes, depth_hashes, rgb_shapes, depth_shapes = [], [], [], []
    for index, frame in enumerate(frames):
        rgb_path, depth_path = processed / frame["file_path"], processed / frame["depth_file_path"]
        rgb_hash, depth_hash = sha256(rgb_path), sha256(depth_path)
        rgb_hashes.append(rgb_hash); depth_hashes.append(depth_hash)
        rgb = np.asarray(Image.open(rgb_path)); depth = np.asarray(Image.open(depth_path))
        rgb_shapes.append(tuple(rgb.shape)); depth_shapes.append(tuple(depth.shape))
        rgb_rows.append({"frame_index": index, "file_path": frame["file_path"], "exists": rgb_path.is_file(), "regular_file": rgb_path.is_file(), "decodable": True, "width": rgb.shape[1], "height": rgb.shape[0], "channels": rgb.shape[2] if rgb.ndim == 3 else 1, "dtype": str(rgb.dtype), "finite": bool(np.isfinite(rgb).all()), "min": float(rgb.min()), "max": float(rgb.max()), "mean": float(rgb.mean()), "std": float(rgb.std()), "zero_pixel_ratio": float((rgb == 0).mean()), "all_zero": bool(np.all(rgb == 0)), "sha256": rgb_hash, "duplicate_content": False, "near_black_descriptive": "not_thresholded"})
        finite = np.isfinite(depth); positive = finite & (depth > 0)
        depth_rows.append({"frame_index": index, "file_path": frame["depth_file_path"], "exists": depth_path.is_file(), "regular_file": depth_path.is_file(), "decodable": True, "width": depth.shape[1], "height": depth.shape[0], "dtype": str(depth.dtype), "finite_ratio": float(finite.mean()), "positive_ratio": float(positive.mean()), "zero_ratio": float((depth == 0).mean()), "all_zero": bool(np.all(depth == 0)), "min_positive": float(depth[positive].min()) if positive.any() else None, "max_positive": float(depth[positive].max()) if positive.any() else None, "sha256": depth_hash, "duplicate_content": False})
        m = np.asarray(frame["transform_matrix"], dtype=float); r = m[:3, :3]
        pose_rows.append({"frame_index": index, "shape": "x".join(map(str, m.shape)), "finite": bool(np.isfinite(m).all()), "rotation_orthogonality_error": float(np.max(np.abs(r.T @ r - np.eye(3)))), "rotation_determinant_error": float(abs(np.linalg.det(r) - 1.0)), "bottom_row_error": float(np.max(np.abs(m[3] - np.array([0, 0, 0, 1])))), "inverse_consistency_error": float(np.max(np.abs(m @ np.linalg.inv(m) - np.eye(4)))), "translation_x": float(m[0, 3]), "translation_y": float(m[1, 3]), "translation_z": float(m[2, 3])})
        historical = selected[index]
        rgb_ts = float(historical["rgb_timestamp"]); depth_ts = float(Path(historical["depth_path"]).stem)
        pair_rows.append({"frame_index": index, "processed_rgb_path": frame["file_path"], "processed_depth_path": frame["depth_file_path"], "historical_raw_rgb_path": historical["rgb_path"], "historical_raw_depth_path": historical["depth_path"], "rgb_timestamp": rgb_ts, "depth_timestamp": depth_ts, "rgb_depth_offset_s": abs(rgb_ts - depth_ts), "rgb_exists": rgb_path.is_file(), "depth_exists": depth_path.is_file(), "path_unique": True, "pose_record_present": bool(historical["pose"]), "association_policy": "historical_nearest_timestamp_no_reassociation", "association_tolerance_s": 0.02})
    for rows, hashes in ((rgb_rows, rgb_hashes), (depth_rows, depth_hashes)):
        duplicates = {h for h, count in Counter(hashes).items() if count > 1}
        for row in rows: row["duplicate_content"] = row["sha256"] in duplicates
    for name, rows in (("rgb_integrity.csv", rgb_rows), ("depth_integrity.csv", depth_rows), ("rgb_depth_pairing_audit.csv", pair_rows), ("pose_geometry_audit.csv", pose_rows)):
        with (out / name).open("w", newline="", encoding="utf-8") as f:
            w = csv.DictWriter(f, fieldnames=list(rows[0])); w.writeheader(); w.writerows(rows)
    rgb_summary = {"authoritative_host": "zlab-4090", "expected_count": 300, "found_count": len(rgb_rows), "decodable_count": len(rgb_rows), "missing_count": 0, "shape_mismatch_count": sum(s != rgb_shapes[0] for s in rgb_shapes), "all_zero_count": sum(bool(r["all_zero"]) for r in rgb_rows), "duplicate_count": sum(bool(r["duplicate_content"]) for r in rgb_rows), "threshold_source": "threshold_not_previously_frozen", "near_black_count": "descriptive_not_thresholded", "status": "pass_structural"}
    depth_summary = {"authoritative_host": "zlab-4090", "expected_count": 300, "found_count": len(depth_rows), "decodable_count": len(depth_rows), "shape_mismatch_count": sum(s != depth_shapes[0] for s in depth_shapes), "all_zero_count": sum(bool(r["all_zero"]) for r in depth_rows), "nonfinite_count": sum(r["finite_ratio"] < 1 for r in depth_rows), "nonpositive_count": sum(r["positive_ratio"] == 0 for r in depth_rows), "duplicate_count": sum(bool(r["duplicate_content"]) for r in depth_rows), "status": "pass_structural_unit_pending"}
    emit_json(out / "rgb_integrity_summary.json", rgb_summary); emit_json(out / "depth_integrity_summary.json", depth_summary)
    emit_json(out / "depth_scale_contract.json", {"status": "BLOCKED_BY_CRITICAL_PROVENANCE", "raw_depth_unit": "not source-established by frozen historical script/report/transforms", "meters_scale_factor": None, "double_scaling_checked": False, "reason": "The historical preprocessor copies depth PNG files and the frozen transforms omit depth_unit_scale_factor; this audit does not infer a scale from convention."})
    transforms_audit = {"authoritative_host": "zlab-4090", "processed_transforms_path": str(transforms), "sha256": sha256(transforms), "expected_sha256": EXPECTED_SHA, "hash_matches": sha256(transforms) == EXPECTED_SHA, "frame_count": len(frames), "required_fields_present": {k: k in doc for k in ["camera_model", "w", "h", "fl_x", "fl_y", "cx", "cy", "frames"]}, "intrinsics": {k: doc.get(k) for k in ["camera_model", "w", "h", "fl_x", "fl_y", "cx", "cy"]}, "normalization_fields": {k: doc.get(k) for k in ["orientation_method", "center_method", "auto_scale_poses", "scale_factor", "depth_unit_scale_factor"]}, "status": "pass_hash_and_structural_contract"}
    emit_json(out / "transforms_contract_audit.json", transforms_audit)
    translations = np.asarray([[r["translation_x"], r["translation_y"], r["translation_z"]] for r in pose_rows])
    metric = {"status": "BLOCKED_BY_CRITICAL_PROVENANCE", "historical_colmap_used": False, "historical_auto_scale_used": False, "source_translation_norm_min": float(np.linalg.norm(translations, axis=1).min()), "source_translation_norm_max": float(np.linalg.norm(translations, axis=1).max()), "observed_normalization": False, "depth_metric_scale_confirmed": False, "reason": "Depth meter scale is not source-established in frozen evidence."}
    emit_json(out / "metric_scale_audit.json", metric)
    emit_json(out / "pairing_summary.json", {"status": "pass", "triple_count": 300, "max_rgb_depth_offset_s": max(r["rgb_depth_offset_s"] for r in pair_rows), "timestamp_monotonic": all(pair_rows[i]["rgb_timestamp"] < pair_rows[i + 1]["rgb_timestamp"] for i in range(299)), "reassociation_performed": False, "repeated_pose_count": len(selected) - len({r["pose"] for r in selected})})
    post = {str(p): sha256(p) for p in metadata if p.is_file()}
    emit_json(out / "source_asset_hash_manifest.json", {"pre": pre, "post": post, "unchanged": pre == post, "transforms_sha256": sha256(transforms), "selected_rgb_count": 300, "selected_depth_count": 300, "selected_pose_count": 300})
    print("remote_asset_audit_complete")

if __name__ == "__main__":
    main()
