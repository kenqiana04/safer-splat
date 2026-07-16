#!/usr/bin/env python3
"""Emit blocked geometry/scale evidence rather than infer it from historical summaries."""
from pathlib import Path
import csv, json

ROOT = Path(__file__).resolve().parents[1]
with (ROOT / "pose_geometry_audit.csv").open("w", newline="", encoding="utf-8") as f:
    fields = ["expected_pose_count", "audited_pose_count", "rotation_orthogonality_max", "rotation_determinant_error_max", "bottom_row_error_max", "coordinate_convention", "status"]
    w = csv.DictWriter(f, fieldnames=fields); w.writeheader(); w.writerow({"expected_pose_count": 300, "audited_pose_count": 0, "rotation_orthogonality_max": "not_computed_asset_unavailable", "rotation_determinant_error_max": "not_computed_asset_unavailable", "bottom_row_error_max": "not_computed_asset_unavailable", "coordinate_convention": "historical script constructs camera-to-world from TUM groundtruth quaternion/translation; current transforms unavailable", "status": "blocked_by_asset_unavailable"})
metric = {"status": "blocked_by_asset_unavailable", "historical_contract": {"colmap_pose_estimation_used": False, "pose_auto_scale_used": False, "metric_scale_ratio": True}, "observed_translation_scale_ratio": None, "normalization_observed": None, "depth_unit_scale": "unresolved"}
(ROOT / "metric_scale_audit.json").write_text(json.dumps(metric, indent=2, sort_keys=True) + "\n", encoding="utf-8")
print("pose_geometry=blocked_asset_unavailable")
