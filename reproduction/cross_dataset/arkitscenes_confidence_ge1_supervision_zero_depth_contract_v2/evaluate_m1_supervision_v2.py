#!/usr/bin/env python3
"""Deterministically evaluate the frozen M1 supervision contract V2."""

from __future__ import annotations

import argparse
import csv
import hashlib
import json
import math
from pathlib import Path
from typing import Any


M0 = "M0_RAW_POSITIVE"
M1 = "M1_CONFIDENCE_GE1"


def canonical_bytes(value: Any) -> bytes:
    return (json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=True) + "\n").encode("utf-8")


def load_csv(path: Path) -> list[dict[str, str]]:
    with path.open("r", encoding="utf-8", newline="") as handle:
        return list(csv.DictReader(handle))


def longest_run(indices: list[int]) -> int:
    best = current = 0
    previous = None
    for index in sorted(indices):
        current = current + 1 if previous is not None and index == previous + 1 else 1
        best = max(best, current)
        previous = index
    return best


def evaluate(prior_root: Path, train_manifest: Path) -> dict[str, Any]:
    frame_rows = load_csv(prior_root / "full_train_per_frame_metrics.csv")
    manifest_rows = load_csv(train_manifest)
    if len(manifest_rows) != 214:
        raise RuntimeError("canonical TRAIN manifest does not contain 214 rows")
    # PR #72's per-frame ``index`` is the canonical TRAIN row number.  The
    # manifest's ``keyframe_index`` is the upstream source-frame identity and
    # is intentionally non-contiguous, so it must not be used as an array key.
    by_index = {index: row for index, row in enumerate(manifest_rows)}
    m0 = {int(row["index"]): row for row in frame_rows if row["mask"] == M0}
    m1 = {int(row["index"]): row for row in frame_rows if row["mask"] == M1}
    if sorted(m0) != list(range(214)) or sorted(m1) != list(range(214)):
        raise RuntimeError("prior per-frame M0/M1 evidence is incomplete")

    unsupported: list[int] = []
    groups: dict[str, dict[str, Any]] = {}
    for index in range(214):
        group = by_index[index]["v1_group_id"]
        group_hash = by_index[index]["v1_group_hash"]
        record = groups.setdefault(group, {
            "group_id": int(group),
            "group_hash": group_hash,
            "frame_indices": [],
            "unsupported_indices": [],
            "m0_positive_pixels": 0,
            "m1_valid_pixels": 0,
            "supported_frame_count": 0,
        })
        if record["group_hash"] != group_hash:
            raise RuntimeError(f"group {group} has inconsistent hashes")
        m0_pixels = int(m0[index]["valid_pixel_count"])
        m1_pixels = int(m1[index]["valid_pixel_count"])
        required_pixels = max(1024, math.ceil(0.05 * m0_pixels))
        supported = m1_pixels >= required_pixels
        record["frame_indices"].append(index)
        record["m0_positive_pixels"] += m0_pixels
        record["m1_valid_pixels"] += m1_pixels
        if supported:
            record["supported_frame_count"] += 1
        else:
            record["unsupported_indices"].append(index)
            unsupported.append(index)

    group_results: list[dict[str, Any]] = []
    for group in sorted(groups, key=lambda value: int(value)):
        record = groups[group]
        n_g = len(record.pop("frame_indices"))
        required = max(1, math.ceil(0.80 * n_g))
        retention = record["m1_valid_pixels"] / record["m0_positive_pixels"]
        supported_gate = record["supported_frame_count"] >= required
        retention_gate = retention >= 0.20
        record.update({
            "frame_count": n_g,
            "required_supported_frame_count": required,
            "pixel_retention": retention,
            "supported_count_gate_pass": supported_gate,
            "pixel_retention_gate_pass": retention_gate,
            "pass": supported_gate and retention_gate,
        })
        group_results.append(record)

    global_m0 = sum(int(m0[i]["valid_pixel_count"]) for i in range(214))
    global_m1 = sum(int(m1[i]["valid_pixel_count"]) for i in range(214))
    supported_count = 214 - len(unsupported)
    global_retention = global_m1 / global_m0
    support_fraction = supported_count / 214
    longest = longest_run(unsupported)
    gates = {
        "global_retention_ge_0_30": global_retention >= 0.30,
        "supported_frame_fraction_ge_0_90": support_fraction >= 0.90,
        "longest_unsupported_run_le_5": longest <= 5,
        "all_group_supported_count_gates": all(row["supported_count_gate_pass"] for row in group_results),
        "all_group_pixel_retention_gates": all(row["pixel_retention_gate_pass"] for row in group_results),
    }
    result: dict[str, Any] = {
        "candidate": M1,
        "definition": "(depth_raw > 0) AND (confidence >= 1)",
        "frame_support_definition": "M1_valid_pixels_frame >= max(1024, 0.05*M0_positive_pixels_frame)",
        "group_supported_count_formula": "S_g >= max(1, ceil(0.80*N_g))",
        "threshold_provenance": "post-audit pretraining protocol revision; not Apple or SplaTAM official thresholds",
        "global": {
            "frame_count": 214,
            "m0_positive_pixels": global_m0,
            "m1_valid_pixels": global_m1,
            "pixel_retention": global_retention,
            "supported_frame_count": supported_count,
            "supported_frame_fraction": support_fraction,
            "unsupported_indices": unsupported,
            "zero_valid_indices": [i for i in range(214) if int(m1[i]["valid_pixel_count"]) == 0],
            "longest_unsupported_run": longest,
        },
        "groups": group_results,
        "gates": gates,
        "pass": all(gates.values()),
        "status": "PASS_ARKITSCENES_M1_SUPERVISION_V2" if all(gates.values()) else "NO_ARKITSCENES_CONFIDENCE_GE1_SUPERVISION_CONTRACT_V2",
    }
    result["decision_digest"] = hashlib.sha256(canonical_bytes(result)).hexdigest()
    return result


def write_csv(path: Path, groups: list[dict[str, Any]]) -> None:
    fields = ["group_id", "group_hash", "frame_count", "supported_frame_count", "required_supported_frame_count", "m0_positive_pixels", "m1_valid_pixels", "pixel_retention", "unsupported_indices", "supported_count_gate_pass", "pixel_retention_gate_pass", "pass"]
    with path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=fields, lineterminator="\n")
        writer.writeheader()
        for group in groups:
            row = dict(group)
            row["unsupported_indices"] = ";".join(str(value) for value in row["unsupported_indices"])
            writer.writerow({key: row[key] for key in fields})


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--prior-root", type=Path, required=True)
    parser.add_argument("--train-manifest", type=Path, required=True)
    parser.add_argument("--output-json", type=Path, required=True)
    parser.add_argument("--output-csv", type=Path, required=True)
    args = parser.parse_args()
    result = evaluate(args.prior_root.resolve(), args.train_manifest.resolve())
    args.output_json.parent.mkdir(parents=True, exist_ok=True)
    args.output_json.write_bytes(canonical_bytes(result))
    write_csv(args.output_csv, result["groups"])
    print(result["status"])
    print(result["decision_digest"])
    return 0 if result["pass"] else 2


if __name__ == "__main__":
    raise SystemExit(main())
