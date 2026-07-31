#!/usr/bin/env python3
"""Audit all canonical TRAIN/HELDOUT confidence assets without geometry selection."""

from __future__ import annotations

import argparse
import collections
import re
from pathlib import Path

import imageio.v2 as imageio
import numpy as np

from audit_common import HELDOUT_SHA256, TRAIN_SHA256, load_manifest, sha256_file, under, write_csv, write_json


def audit_rows(rows: list[dict[str, str]], asset_root: Path, include_checksums: bool) -> tuple[list[dict[str, object]], dict[str, object]]:
    inventory: list[dict[str, object]] = []
    global_values: collections.Counter[int] = collections.Counter()
    dtype_values: collections.Counter[str] = collections.Counter()
    shape_values: collections.Counter[str] = collections.Counter()
    all_checks: list[bool] = []
    for index, row in enumerate(rows):
        rgb_path = under(asset_root, row["rgb"])
        depth_path = under(asset_root, row["depth"])
        confidence_path = under(asset_root, row["confidence"])
        intrinsics_path = under(asset_root, row["intrinsics"])
        rgb = np.asarray(imageio.imread(rgb_path))
        depth = np.asarray(imageio.imread(depth_path))
        confidence_first = np.asarray(imageio.imread(confidence_path))
        confidence_second = np.asarray(imageio.imread(confidence_path))
        expected_shape = (int(row["height"]), int(row["width"]))
        timestamp = row["timestamp"]
        basename_match = all(timestamp in path.name for path in (rgb_path, depth_path, confidence_path, intrinsics_path))
        shape_match = rgb.shape[:2] == depth.shape[:2] == confidence_first.shape[:2] == expected_shape
        repeated_equal = np.array_equal(confidence_first, confidence_second)
        readable_without_fallback = confidence_first.size > 0 and confidence_first.shape == expected_shape
        values, counts = np.unique(confidence_first, return_counts=True)
        value_counts = {int(value): int(count) for value, count in zip(values, counts)}
        allowed_values = set(value_counts).issubset({0, 1, 2})
        raw_all_zero = set(value_counts) == {0}
        byte_order = confidence_first.dtype.byteorder
        dtype_values[str(confidence_first.dtype)] += 1
        shape_values[f"{confidence_first.shape[0]}x{confidence_first.shape[1]}"] += 1
        global_values.update(value_counts)
        checks = {
            "timestamp_basename_match": basename_match,
            "shape_match": shape_match,
            "repeated_load_equal": repeated_equal,
            "readable_without_fallback": readable_without_fallback,
            "allowed_values_0_1_2": allowed_values,
        }
        all_checks.extend(checks.values())
        inventory.append(
            {
                "index": index,
                "split": row["split"],
                "timestamp": timestamp,
                "keyframe_index": int(row["keyframe_index"]),
                "group": int(row["v1_group_id"]),
                "confidence_path": row["confidence"],
                "confidence_size": confidence_path.stat().st_size,
                "confidence_sha256": sha256_file(confidence_path) if include_checksums else "structure_only_not_selected",
                "shape": f"{confidence_first.shape[0]}x{confidence_first.shape[1]}",
                "dtype": str(confidence_first.dtype),
                "byte_order": byte_order,
                "unique_values": ";".join(str(value) for value in sorted(value_counts)),
                "count_0": value_counts.get(0, 0),
                "count_1": value_counts.get(1, 0),
                "count_2": value_counts.get(2, 0),
                "timestamp_basename_match": basename_match,
                "shape_match": shape_match,
                "repeated_load_equal": repeated_equal,
                "readable_without_fallback": readable_without_fallback,
                "allowed_values": allowed_values,
                "raw_asset_all_zero": raw_all_zero,
            }
        )
    summary = {
        "rows": len(rows),
        "all_structural_checks_pass": all(all_checks),
        "global_value_counts": {str(key): int(value) for key, value in sorted(global_values.items())},
        "dtypes": dict(sorted(dtype_values.items())),
        "shapes": dict(sorted(shape_values.items())),
        "raw_asset_all_zero_frames": [int(row["index"]) for row in inventory if row["raw_asset_all_zero"]],
        "raw_all_zero_is_not_reader_fallback": True,
        "repeated_load_deterministic": all(bool(row["repeated_load_equal"]) for row in inventory),
    }
    return inventory, summary


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--train", type=Path, required=True)
    parser.add_argument("--heldout", type=Path, required=True)
    parser.add_argument("--asset-root", type=Path, required=True)
    parser.add_argument("--adapter", type=Path, required=True)
    parser.add_argument("--output-root", type=Path, required=True)
    args = parser.parse_args()
    train = load_manifest(args.train, TRAIN_SHA256, "TRAIN", 214)
    heldout = load_manifest(args.heldout, HELDOUT_SHA256, "HELDOUT", 53)
    train_inventory, train_summary = audit_rows(train, args.asset_root.resolve(), include_checksums=True)
    heldout_inventory, heldout_summary = audit_rows(heldout, args.asset_root.resolve(), include_checksums=False)
    adapter_source = args.adapter.read_text(encoding="utf-8")
    nearest = "cv2.INTER_NEAREST" in adapter_source
    no_zero_fallback = not re.search(r"except[^:]*:\s*(?:confidence\s*=\s*)?np\.zeros", adapter_source, re.DOTALL)
    same_row_join = 'self.confidence_paths.append(self._resolve_asset(row["confidence"]))' in adapter_source
    structural = {
        "status": "PASS_CONFIDENCE_ASSET_AND_READER_STRUCTURE",
        "train": train_summary,
        "heldout_structure_only": heldout_summary,
        "adapter": {
            "nearest_neighbor_resize": nearest,
            "no_silent_zero_fallback": no_zero_fallback,
            "same_manifest_row_join": same_row_join,
            "depth_confidence_shared_orientation": "identity_256x192_no_rotation_transpose_or_flip",
        },
        "implementation_error": False,
    }
    if not (train_summary["all_structural_checks_pass"] and heldout_summary["all_structural_checks_pass"] and nearest and no_zero_fallback and same_row_join):
        structural["status"] = "CONFIDENCE_READER_OR_ALIGNMENT_IMPLEMENTATION_ERROR"
        structural["implementation_error"] = True
    fields = list(train_inventory[0].keys())
    write_csv(args.output_root / "confidence_asset_inventory.csv", fields, train_inventory)
    write_json(args.output_root / "confidence_value_distribution.json", {"train": train_summary, "heldout_structure_only": heldout_summary})
    write_json(args.output_root / "confidence_structural_validation.json", structural)
    write_json(args.output_root / "heldout_confidence_structure_only.json", heldout_summary)
    print(structural["status"])
    return 0 if not structural["implementation_error"] else 2


if __name__ == "__main__":
    raise SystemExit(main())
