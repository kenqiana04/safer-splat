#!/usr/bin/env python3
"""Record a blocked pairing audit when the immutable source manifests are absent."""
from pathlib import Path
import csv

ROOT = Path(__file__).resolve().parents[1]
fields = ["expected_rgb_count", "expected_depth_count", "expected_pose_count", "audited_triple_count", "association_policy", "maximum_time_difference_s", "timestamp_order", "duplicate_timestamp_count", "missing_pair_count", "repeated_pose_count", "train_eval_split_status", "status"]
row = {"expected_rgb_count": 300, "expected_depth_count": 300, "expected_pose_count": 300, "audited_triple_count": 0, "association_policy": "historical nearest timestamp; no reassociation in this audit", "maximum_time_difference_s": 0.02, "timestamp_order": "not_audited_asset_unavailable", "duplicate_timestamp_count": "not_audited", "missing_pair_count": "not_audited", "repeated_pose_count": "not_audited", "train_eval_split_status": "historical 240/60 disjoint; source transforms unavailable", "status": "blocked_by_asset_unavailable"}
with (ROOT / "rgb_depth_pairing_audit.csv").open("w", newline="", encoding="utf-8") as f:
    w = csv.DictWriter(f, fieldnames=fields); w.writeheader(); w.writerow(row)
print("pairing=blocked_asset_unavailable")
