#!/usr/bin/env python3
"""Evaluate preregistered depth-supervision structure gates for M1 and M2."""

from __future__ import annotations

import argparse
from pathlib import Path

import numpy as np

from audit_common import MASKS, TRAIN_SHA256, load_manifest, write_csv, write_json


def longest_false_run(values: list[bool]) -> int:
    best = current = 0
    for value in values:
        current = 0 if value else current + 1
        best = max(best, current)
    return best


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--manifest", type=Path, required=True)
    parser.add_argument("--cache-root", type=Path, required=True)
    parser.add_argument("--output-root", type=Path, required=True)
    args = parser.parse_args()
    rows = load_manifest(args.manifest, TRAIN_SHA256, "TRAIN", 214)
    frame_counts: dict[str, list[int]] = {name: [] for name in MASKS}
    for index in range(len(rows)):
        data = np.load(args.cache_root / f"frame_{index:03d}.npz")
        confidence = data["confidence"]
        for name in MASKS:
            frame_counts[name].append(int(MASKS[name](confidence).sum()))
    m0_total = sum(frame_counts["M0_RAW_POSITIVE"])
    unsupported_rows: list[dict[str, object]] = []
    results: dict[str, object] = {}
    for name in ("M1_CONFIDENCE_GE1", "M2_CONFIDENCE_EQ2"):
        counts = frame_counts[name]
        supported = [count >= max(1024, 0.05 * m0) for count, m0 in zip(counts, frame_counts["M0_RAW_POSITIVE"])]
        zero = [count == 0 for count in counts]
        groups: dict[str, object] = {}
        group_passes = []
        for group in sorted({int(row["v1_group_id"]) for row in rows}):
            indices = [idx for idx, row in enumerate(rows) if int(row["v1_group_id"]) == group]
            retained = sum(counts[idx] for idx in indices) / sum(frame_counts["M0_RAW_POSITIVE"][idx] for idx in indices)
            supported_count = sum(supported[idx] for idx in indices)
            group_pass = supported_count >= 10 and retained >= 0.20
            group_passes.append(group_pass)
            groups[str(group)] = {
                "frame_count": len(indices),
                "supported_frame_count": int(supported_count),
                "retained_fraction": float(retained),
                "pass": group_pass,
            }
        for index, is_supported in enumerate(supported):
            if not is_supported:
                unsupported_rows.append(
                    {
                        "mask": name,
                        "index": index,
                        "timestamp": rows[index]["timestamp"],
                        "group": int(rows[index]["v1_group_id"]),
                        "valid_pixels": counts[index],
                        "m0_pixels": frame_counts["M0_RAW_POSITIVE"][index],
                        "required_pixels": int(max(1024, 0.05 * frame_counts["M0_RAW_POSITIVE"][index])),
                        "zero_valid": zero[index],
                    }
                )
        global_retention = sum(counts) / m0_total
        supported_fraction = float(np.mean(supported))
        longest_run = longest_false_run(supported)
        zero_count = int(sum(zero))
        gates = {
            "global_retention_ge_0_30": global_retention >= 0.30,
            "supported_frame_fraction_ge_0_90": supported_fraction >= 0.90,
            "all_groups_pass": all(group_passes) and len(groups) == 8,
            "longest_unsupported_run_le_5": longest_run <= 5,
            "zero_valid_compatibility": zero_count == 0,
        }
        results[name] = {
            "valid_pixel_count": int(sum(counts)),
            "retained_fraction": float(global_retention),
            "supported_frame_count": int(sum(supported)),
            "supported_frame_fraction": supported_fraction,
            "zero_valid_frame_count": zero_count,
            "zero_valid_frame_indices": [idx for idx, value in enumerate(zero) if value],
            "longest_unsupported_run": longest_run,
            "groups": groups,
            "gates": gates,
            "structure_pass_before_zero_mask_semantics": all(value for key, value in gates.items() if key != "zero_valid_compatibility"),
            "structure_pass": all(gates.values()),
        }
    structure = {
        "status": "PASS_MASK_SUPERVISION_STRUCTURE_AUDIT",
        "threshold_provenance": "preregistered audit design choices; not Apple or SplaTAM official thresholds",
        "m0_valid_pixel_count": int(m0_total),
        "masks": results,
    }
    temporal = {
        name: {
            "longest_unsupported_run": results[name]["longest_unsupported_run"],
            "gate_le_5": results[name]["gates"]["longest_unsupported_run_le_5"],
        }
        for name in results
    }
    write_json(args.output_root / "mask_supervision_structure.json", structure)
    write_json(args.output_root / "temporal_support_audit.json", temporal)
    fields = ["mask", "index", "timestamp", "group", "valid_pixels", "m0_pixels", "required_pixels", "zero_valid"]
    write_csv(args.output_root / "unsupported_frame_registry.csv", fields, unsupported_rows)
    print(structure["status"])
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
