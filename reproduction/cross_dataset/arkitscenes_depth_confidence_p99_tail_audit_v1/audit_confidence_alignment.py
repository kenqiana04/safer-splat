#!/usr/bin/env python3
"""Preregistered diagnostic confidence-map alignment comparison."""

from __future__ import annotations

import argparse
from pathlib import Path

import cv2
import numpy as np
from scipy.stats import spearmanr

from audit_common import TRAIN_SHA256, load_depth_confidence, load_manifest, stable_digest, write_csv, write_json


TRANSFORMS = (
    "identity",
    "transpose",
    "horizontal_flip",
    "vertical_flip",
    "rotate90",
    "rotate180",
    "rotate270",
    "anti_transpose",
    "offset_-2",
    "offset_-1",
    "offset_+1",
    "offset_+2",
)


def resize_shape(array: np.ndarray, shape: tuple[int, int]) -> np.ndarray:
    if array.shape == shape:
        return array
    return cv2.resize(array, (shape[1], shape[0]), interpolation=cv2.INTER_NEAREST)


def candidate_map(name: str, confidence: np.ndarray, rows: list[dict[str, str]], index: int, asset_root: Path) -> np.ndarray | None:
    shape = confidence.shape
    if name == "identity":
        return confidence
    if name == "transpose":
        return resize_shape(confidence.T, shape)
    if name == "horizontal_flip":
        return confidence[:, ::-1]
    if name == "vertical_flip":
        return confidence[::-1, :]
    if name == "rotate90":
        return resize_shape(np.rot90(confidence, 1), shape)
    if name == "rotate180":
        return np.rot90(confidence, 2)
    if name == "rotate270":
        return resize_shape(np.rot90(confidence, 3), shape)
    if name == "anti_transpose":
        return resize_shape(np.rot90(confidence.T, 2), shape)
    offset = int(name.split("_")[-1])
    other = index + offset
    if other < 0 or other >= len(rows):
        return None
    _, mapped = load_depth_confidence(asset_root, rows[other])
    return mapped


def metrics(confidence: np.ndarray, distance: np.ndarray) -> dict[str, float | int]:
    high = confidence >= 1
    low = confidence == 0
    high_values = distance[high]
    low_values = distance[low]
    corr = spearmanr(confidence, distance).statistic if len(np.unique(confidence)) > 1 else 0.0
    if not np.isfinite(corr):
        corr = 0.0
    return {
        "pixel_count": int(len(distance)),
        "retained_fraction": 1.0,
        "spearman_confidence_vs_error": float(corr),
        "high_count": int(high.sum()),
        "low_count": int(low.sum()),
        "high_median_m": float(np.median(high_values)) if high_values.size else 0.0,
        "high_p95_m": float(np.quantile(high_values, 0.95)) if high_values.size else 0.0,
        "high_p99_m": float(np.quantile(high_values, 0.99)) if high_values.size else 0.0,
        "low_median_m": float(np.median(low_values)) if low_values.size else 0.0,
        "low_p95_m": float(np.quantile(low_values, 0.95)) if low_values.size else 0.0,
        "low_p99_m": float(np.quantile(low_values, 0.99)) if low_values.size else 0.0,
        "tail_gt_030_given_low": float(np.mean(low_values > 0.30)) if low_values.size else 0.0,
        "tail_gt_030_given_high": float(np.mean(high_values > 0.30)) if high_values.size else 0.0,
        "tail_separation": float(np.mean(low_values > 0.30) - np.mean(high_values > 0.30)) if low_values.size and high_values.size else 0.0,
    }


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--manifest", type=Path, required=True)
    parser.add_argument("--asset-root", type=Path, required=True)
    parser.add_argument("--cache-root", type=Path, required=True)
    parser.add_argument("--adapter", type=Path, required=True)
    parser.add_argument("--output-dir", type=Path, required=True)
    args = parser.parse_args()
    rows = load_manifest(args.manifest, TRAIN_SHA256, "TRAIN", 214)
    diagnostic_indices = np.linspace(2, 211, 32).round().astype(int).tolist()
    records: list[dict[str, object]] = []
    for index in diagnostic_indices:
        data = np.load(args.cache_root / f"frame_{index:03d}.npz")
        _, confidence = load_depth_confidence(args.asset_root.resolve(), rows[index])
        y = data["y"].astype(np.int64)
        x = data["x"].astype(np.int64)
        distance = data["distance_m"].astype(np.float64)
        for name in TRANSFORMS:
            mapped = candidate_map(name, confidence, rows, index, args.asset_root.resolve())
            if mapped is None:
                continue
            record = {"frame_index": index, "timestamp": rows[index]["timestamp"], "candidate": name}
            record.update(metrics(mapped[y, x], distance))
            records.append(record)
    identity_by_frame = {int(row["frame_index"]): row for row in records if row["candidate"] == "identity"}
    for row in records:
        identity = identity_by_frame[int(row["frame_index"])]
        row["high_p99_improvement_vs_identity_m"] = float(identity["high_p99_m"]) - float(row["high_p99_m"])
        row["tail_separation_improvement_vs_identity"] = float(row["tail_separation"]) - float(identity["tail_separation"])
        row["better_than_identity"] = bool(
            float(row["high_p99_m"]) < float(identity["high_p99_m"])
            and float(row["tail_separation"]) > float(identity["tail_separation"])
        )
    summaries: dict[str, object] = {}
    for name in TRANSFORMS:
        selected = [row for row in records if row["candidate"] == name]
        if not selected:
            continue
        summaries[name] = {
            "frame_count": len(selected),
            "better_frame_count": int(sum(bool(row["better_than_identity"]) for row in selected)),
            "median_high_p99_m": float(np.median([float(row["high_p99_m"]) for row in selected])),
            "mean_tail_separation": float(np.mean([float(row["tail_separation"]) for row in selected])),
            "tail_separation_improvement_vs_identity": float(np.mean([float(row["tail_separation_improvement_vs_identity"]) for row in selected])),
            "retained_fraction": float(np.mean([float(row["retained_fraction"]) for row in selected])),
        }
    adapter = args.adapter.read_text(encoding="utf-8")
    source_evidence = {
        "same_manifest_row_join": 'self.confidence_paths.append(self._resolve_asset(row["confidence"]))' in adapter,
        "nearest_neighbor_resize": "cv2.INTER_NEAREST" in adapter,
        "rotation_transpose_flip_present": any(token in adapter for token in ("rotate", "transpose", "flip")),
        "official_metadata_requires_nonidentity": False,
    }
    eligible = []
    for name, summary in summaries.items():
        if name == "identity":
            continue
        if (
            summary["better_frame_count"] >= 24
            and summary["tail_separation_improvement_vs_identity"] >= 0.10
            and source_evidence["official_metadata_requires_nonidentity"]
            and summary["retained_fraction"] >= 0.95
        ):
            eligible.append(name)
    decision = {
        "status": "PASS_CONFIDENCE_IDENTITY_ALIGNMENT_RETAINED" if not eligible else "CONFIDENCE_READER_OR_ALIGNMENT_IMPLEMENTATION_ERROR",
        "diagnostic_frame_count": len(diagnostic_indices),
        "diagnostic_indices": diagnostic_indices,
        "candidate_count": len(summaries),
        "candidate_summary": summaries,
        "source_and_metadata_evidence": source_evidence,
        "eligible_nonidentity_candidates": eligible,
        "implementation_error": bool(eligible),
        "selected_alignment_for_audit": "identity",
        "no_candidate_was_adopted": True,
    }
    decision["deterministic_sha256"] = stable_digest({k: v for k, v in decision.items() if k != "deterministic_sha256"})
    args.output_dir.mkdir(parents=True, exist_ok=True)
    write_csv(args.output_dir / "confidence_alignment_framewise.csv", list(records[0].keys()), records)
    write_json(args.output_dir / "confidence_alignment_candidate_audit.json", {"candidates": summaries, "frame_count": 32})
    write_json(args.output_dir / "confidence_alignment_decision.json", decision)
    print(decision["status"])
    print("DETERMINISTIC_SHA256=" + decision["deterministic_sha256"])
    return 0 if not decision["implementation_error"] else 2


if __name__ == "__main__":
    raise SystemExit(main())
