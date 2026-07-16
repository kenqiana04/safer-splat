#!/usr/bin/env python3
"""Record the immutable transforms contract without reconstructing a missing file."""
from pathlib import Path
import json

ROOT = Path(__file__).resolve().parents[1]
expected = "b6a685f4b1a5b2ff3bb9b389c63a138a58119b19dd5cb6d7f671282aeecad29a"
data = {"status": "blocked_by_asset_unavailable", "expected_transforms_sha256": expected, "observed_transforms_sha256": None, "hash_matches": None, "top_level_required_fields": ["camera_model", "w", "h", "fl_x", "fl_y", "cx", "cy", "frames"], "historical_intrinsics": {"camera_model": "OPENCV", "w": 640, "h": 480, "fl_x": 517.3, "fl_y": 516.5, "cx": 318.6, "cy": 255.3}, "historical_frame_count": 300, "no_transforms_generated": True}
(ROOT / "transforms_contract_audit.json").write_text(json.dumps(data, indent=2, sort_keys=True) + "\n", encoding="utf-8")
print("transforms=unavailable")
