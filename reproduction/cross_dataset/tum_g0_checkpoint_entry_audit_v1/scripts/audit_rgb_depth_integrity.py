#!/usr/bin/env python3
"""Record non-fabricated blocked per-frame audit schemas when raw assets are unavailable."""
from pathlib import Path
import csv

ROOT = Path(__file__).resolve().parents[1]
for name, fields, row in (
    ("rgb_integrity.csv", ["rgb_expected_count", "rgb_found_count", "rgb_decodable_count", "rgb_missing_count", "rgb_shape_mismatch_count", "rgb_all_zero_count", "rgb_duplicate_count", "rgb_hash_status", "near_black_descriptive_count", "threshold_source", "status"], {"rgb_expected_count": 300, "rgb_found_count": "not_audited", "rgb_decodable_count": "not_audited", "rgb_missing_count": "not_audited", "rgb_shape_mismatch_count": "not_audited", "rgb_all_zero_count": "not_audited", "rgb_duplicate_count": "not_audited", "rgb_hash_status": "not_computed_asset_unavailable", "near_black_descriptive_count": "not_computed", "threshold_source": "threshold_not_previously_frozen", "status": "blocked_by_asset_unavailable"}),
    ("depth_integrity.csv", ["depth_expected_count", "depth_found_count", "depth_decodable_count", "depth_missing_count", "depth_all_zero_count", "depth_positive_finite_ratio", "depth_unit", "depth_scale_factor", "status"], {"depth_expected_count": 300, "depth_found_count": "not_audited", "depth_decodable_count": "not_audited", "depth_missing_count": "not_audited", "depth_all_zero_count": "not_audited", "depth_positive_finite_ratio": "not_audited", "depth_unit": "unresolved_asset_and_source_config_unavailable", "depth_scale_factor": "unresolved", "status": "blocked_by_asset_unavailable"}),
):
    with (ROOT / name).open("w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=fields); w.writeheader(); w.writerow(row)
print("integrity_audits=blocked_asset_unavailable")
