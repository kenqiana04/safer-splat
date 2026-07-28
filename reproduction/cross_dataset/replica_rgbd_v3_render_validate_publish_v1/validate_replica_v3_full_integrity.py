#!/usr/bin/env python3
"""Re-read every formal V3 RGB-D file and enforce Gate A plus coverage margins."""
from __future__ import annotations

import argparse
from pathlib import Path

import imageio.v3 as iio
import numpy as np

from _common import ROOT, atomic_json, load_json
from validate_replica_v3_frame import depth_stats, frame_valid, rgb_stats


def main(output: Path) -> None:
    staging = ROOT / "formal_staging"
    frames = load_json(staging / "formal_camera_manifest_v3.json")["frames"]
    expected = {row["frame_id"] for row in frames}
    rgb_paths = {path.stem: path for path in (staging / "images").glob("*.png")}
    depth_paths = {path.stem: path for path in (staging / "depth").glob("*.png")}
    details, bad = [], []
    for row in frames:
        frame_id = row["frame_id"]
        if frame_id not in rgb_paths or frame_id not in depth_paths:
            bad.append({"frame_id": frame_id, "reason": "missing"}); continue
        try:
            rgb = iio.imread(rgb_paths[frame_id]); encoded_depth = iio.imread(depth_paths[frame_id])
            metric_depth = encoded_depth.astype(np.float32) * .001
            rs, ds = rgb_stats(rgb), depth_stats(metric_depth)
            valid = frame_valid(rs, ds) and encoded_depth.dtype == np.uint16
            details.append({"frame_id": frame_id, "location_id": row["location_id"], "split": row["split"], "yaw_offset_deg": row["yaw_offset_deg"], "rgb": rs, "depth": ds, "encoded_depth_dtype": str(encoded_depth.dtype), "valid": valid})
            if not valid: bad.append({"frame_id": frame_id, "reason": "format_or_coverage"})
        except Exception as error:
            bad.append({"frame_id": frame_id, "reason": type(error).__name__})
    rgb_extra, depth_extra = sorted(set(rgb_paths) - expected), sorted(set(depth_paths) - expected)
    pairing = sum((frame_id in rgb_paths) != (frame_id in depth_paths) for frame_id in expected)
    rgb_nonzero = [item["rgb"]["nonzero_fraction"] for item in details]
    depth_positive = [item["depth"]["positive_fraction"] for item in details]
    summary = {"status": "PASS" if not bad and not rgb_extra and not depth_extra and pairing == 0 and len(details) == 300 else "FAIL", "frame_count": len(frames), "rgb_file_count": len(rgb_paths), "depth_file_count": len(depth_paths), "rgb_readable_count": len(details), "depth_readable_count": len(details), "rgb_shape_dtype_correct_count": sum(item["rgb"]["shape"] == [480, 640, 3] and item["rgb"]["dtype"] == "uint8" for item in details), "depth_shape_dtype_correct_count": sum(item["depth"]["shape"] == [480, 640] and item["encoded_depth_dtype"] == "uint16" for item in details), "rgb_v1_bad_count": sum(item["rgb"]["v1_black"] for item in details), "depth_v1_all_zero_count": sum(item["depth"]["v1_all_zero"] for item in details), "rgb_v3_threshold_failure_count": sum(item["rgb"]["v3_threshold_failure"] for item in details), "depth_v3_threshold_failure_count": sum(item["depth"]["v3_threshold_failure"] for item in details), "depth_nonfinite_file_count": sum(item["depth"]["finite_fraction"] != 1.0 for item in details), "missing_frame_count": len(bad), "rgb_extra": rgb_extra, "depth_extra": depth_extra, "duplicate_path_count": 0, "pairing_error_count": pairing, "minimum_rgb_nonzero_fraction": min(rgb_nonzero) if rgb_nonzero else None, "minimum_depth_positive_fraction": min(depth_positive) if depth_positive else None, "frames_within_0_01_rgb_threshold": sum(value < .06 for value in rgb_nonzero), "frames_within_0_01_depth_threshold": sum(value < .11 for value in depth_positive), "formal_pass_count": sum(item["valid"] for item in details), "bad_frames": bad, "details_server_only": str(ROOT / "full_integrity" / "frame_integrity_detail.json")}
    atomic_json(ROOT / "full_integrity" / "frame_integrity_detail.json", {"frames": details})
    atomic_json(output, summary)
    preprobe = load_json(ROOT / "input_identity" / "preprobe_summary.json") if (ROOT / "input_identity" / "preprobe_summary.json").exists() else {"results": []}
    preprobe_by_frame = {view["frame_id"]: view for result in preprobe.get("results", []) for view in result.get("views", [])}
    manifest_by_frame = {row["frame_id"]: row for row in frames}
    compared = [(item, preprobe_by_frame.get(manifest_by_frame[item["frame_id"]]["source_candidate_id"] + "_yaw_" + str(manifest_by_frame[item["frame_id"]]["yaw_slot"]))) for item in details]
    compared = [(item, probe) for item, probe in compared if probe is not None]
    atomic_json(ROOT / "full_integrity" / "replica_rgbd_v3_coverage_margin_summary.json", {"status": "PASS" if summary["status"] == "PASS" else "FAIL", "formal_frame_count": len(details), "minimum_formal_rgb_nonzero_fraction": summary["minimum_rgb_nonzero_fraction"], "minimum_formal_depth_positive_fraction": summary["minimum_depth_positive_fraction"], "frames_within_0_01_rgb_threshold": summary["frames_within_0_01_rgb_threshold"], "frames_within_0_01_depth_threshold": summary["frames_within_0_01_depth_threshold"], "preprobe_compared_frame_count": len(compared), "preprobe_pass_formal_fail_count": sum(probe["status"] == "HABITAT_VIEW_PREQUALIFICATION_PASS" and not item["valid"] for item, probe in compared), "formal_pass_count": summary["formal_pass_count"], "mean_preprobe_to_formal_rgb_delta": float(np.mean([item["rgb"]["nonzero_fraction"] - probe["metrics"]["rgb_nonzero_fraction"] for item, probe in compared])) if compared else None, "mean_preprobe_to_formal_depth_delta": float(np.mean([item["depth"]["positive_fraction"] - probe["metrics"]["depth_positive_fraction"] for item, probe in compared])) if compared else None, "rgb_nonzero_by_yaw": {str(yaw): [item["rgb"]["nonzero_fraction"] for item in details if item["yaw_offset_deg"] == yaw] for yaw in (0, -60, 60)}, "depth_positive_by_yaw": {str(yaw): [item["depth"]["positive_fraction"] for item in details if item["yaw_offset_deg"] == yaw] for yaw in (0, -60, 60)}})
    if summary["status"] != "PASS":
        raise SystemExit("REPLICA_RGBD_V3_FORMAL_RENDER_INTEGRITY_GATE_FAILED")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(); parser.add_argument("--output", type=Path, default=ROOT / "full_integrity" / "replica_rgbd_v3_file_integrity_summary.json"); args = parser.parse_args(); main(args.output)
