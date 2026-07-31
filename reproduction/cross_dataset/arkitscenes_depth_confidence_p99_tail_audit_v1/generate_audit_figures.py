#!/usr/bin/env python3
"""Generate the 15 preregistered compact evidence figures."""

from __future__ import annotations

import argparse
import json
from pathlib import Path

import imageio.v2 as imageio
import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd

from audit_common import TRAIN_SHA256, load_depth_confidence, load_manifest, under


BOUNDARY = "NO MAPPER | NO TRAINING | NO LEARNED MAP | NO FRAME DELETION | NO THRESHOLD RELAXATION"
COLORS = {"M0_RAW_POSITIVE": "#4c78a8", "M1_CONFIDENCE_GE1": "#f58518", "M2_CONFIDENCE_EQ2": "#54a24b"}


def finish(fig, path: Path) -> None:
    fig.text(0.5, 0.01, BOUNDARY, ha="center", va="bottom", fontsize=7, color="#7a1f1f")
    fig.tight_layout(rect=(0, 0.04, 1, 1))
    fig.savefig(path, dpi=150)
    plt.close(fig)


def bar_from_mapping(title: str, mapping: dict[str, dict[str, float]], value: str, path: Path) -> None:
    fig, ax = plt.subplots(figsize=(8, 4.5))
    labels = list(mapping)
    values = [mapping[label][value] for label in labels]
    ax.bar(labels, values, color="#4c78a8")
    ax.set_title(title)
    ax.tick_params(axis="x", rotation=25)
    ax.set_ylabel(value)
    finish(fig, path)


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--manifest", type=Path, required=True)
    parser.add_argument("--asset-root", type=Path, required=True)
    parser.add_argument("--cache-root", type=Path, required=True)
    parser.add_argument("--output-root", type=Path, required=True)
    args = parser.parse_args()
    root = args.output_root.resolve()
    figures = root / "figures"
    figures.mkdir(parents=True, exist_ok=True)
    rows = load_manifest(args.manifest, TRAIN_SHA256, "TRAIN", 214)
    geometry = json.loads((root / "full_train_mask_metrics.json").read_text(encoding="utf-8"))
    supervision = json.loads((root / "mask_supervision_structure.json").read_text(encoding="utf-8"))
    concentration = json.loads((root / "p99_tail_concentration.json").read_text(encoding="utf-8"))
    ray = json.loads((root / "mesh_ray_coverage_metrics.json").read_text(encoding="utf-8"))
    spatial = json.loads((root / "tail_spatial_factorization.json").read_text(encoding="utf-8"))
    depth = json.loads((root / "tail_depth_range_factorization.json").read_text(encoding="utf-8"))
    temporal = json.loads((root / "tail_temporal_consistency.json").read_text(encoding="utf-8"))
    causes = json.loads((root / "tail_cause_summary.json").read_text(encoding="utf-8"))
    decision = json.loads((root / "decision" / "decision.json").read_text(encoding="utf-8"))
    per_frame = pd.read_csv(root / "full_train_per_frame_metrics.csv")

    fig, ax = plt.subplots(figsize=(8, 4.5))
    x = np.arange(3)
    width = 0.24
    masks = list(geometry["global"])
    for offset, key in enumerate(("median_m", "p95_m", "p99_m")):
        ax.bar(x + (offset - 1) * width, [geometry["global"][mask][key] for mask in masks], width, label=key)
    ax.axhline(0.30, color="red", linestyle="--", linewidth=1, label="p99 gate 0.30 m")
    ax.set_xticks(x, [name.split("_")[0] for name in masks])
    ax.set_ylabel("metres")
    ax.set_title("M0/M1/M2 full-TRAIN global quantiles")
    ax.legend()
    finish(fig, figures / "m0_m1_m2_global_quantiles.png")

    fig, ax = plt.subplots(figsize=(7, 4.5))
    for mask in masks:
        ax.scatter(geometry["global"][mask]["retained_fraction_vs_m0"], geometry["global"][mask]["p99_m"], s=90, label=mask)
    ax.axhline(0.30, color="red", linestyle="--")
    ax.axvline(0.30, color="gray", linestyle=":")
    ax.set_xlabel("retention vs M0")
    ax.set_ylabel("p99 point-to-mesh error (m)")
    ax.set_title("Retention versus geometry")
    ax.legend(fontsize=7)
    finish(fig, figures / "mask_retention_vs_geometry.png")

    fig, axes = plt.subplots(2, 1, figsize=(10, 6), sharex=True)
    for mask in masks:
        frame = per_frame[per_frame["mask"] == mask]
        axes[0].plot(frame["index"], frame["median_m"], label=mask, color=COLORS[mask], linewidth=1)
        axes[1].plot(frame["index"], frame["p99_m"], label=mask, color=COLORS[mask], linewidth=1)
    axes[0].axhline(0.10, color="red", linestyle="--"); axes[0].set_ylabel("median m")
    axes[1].axhline(0.30, color="red", linestyle="--"); axes[1].set_ylabel("p99 m"); axes[1].set_xlabel("TRAIN frame index")
    axes[0].set_title("Per-frame median and p99")
    axes[0].legend(fontsize=7, ncol=3)
    finish(fig, figures / "per_frame_median_p99.png")

    frame_tail = pd.read_csv(root / "p99_tail_frame_contribution.csv")
    top = frame_tail[frame_tail["tail"] == "TAIL_GT_030"].nlargest(20, "tail_pixel_count")
    fig, ax = plt.subplots(figsize=(10, 4.5))
    ax.bar(top["frame_index"].astype(str), top["tail_pixel_count"], color="#e45756")
    ax.set_title("Top-20 frame contributions to M0 error >0.30 m")
    ax.set_xlabel("frame index"); ax.set_ylabel("tail pixels"); ax.tick_params(axis="x", rotation=45)
    finish(fig, figures / "tail_frame_concentration.png")

    bar_from_mapping("M0 >0.30 m tail confidence distribution", spatial["confidence"], "fraction", figures / "tail_confidence_distribution.png")
    bar_from_mapping("M0 >0.30 m tail depth range", depth["depth_bins"], "fraction", figures / "tail_depth_range_distribution.png")
    bar_from_mapping("M0 >0.30 m tail image-border bands", spatial["image_border_bands"], "fraction", figures / "tail_image_border_distribution.png")

    classes = ray["M0_RAW_POSITIVE"]["classes"]
    bar_from_mapping("Mesh-ray classes for M0 error >0.30 m", classes, "fraction", figures / "mesh_ray_coverage_tail.png")

    temporal_counts = temporal["summary"]["category_counts"]
    fig, ax = plt.subplots(figsize=(8, 4.5))
    ax.bar(list(temporal_counts), list(temporal_counts.values()), color="#72b7b2")
    ax.set_title("Top-20 tail-frame temporal consistency"); ax.set_ylabel("frames"); ax.tick_params(axis="x", rotation=20)
    finish(fig, figures / "temporal_consistency_tail.png")

    fig, ax = plt.subplots(figsize=(10, 4.5))
    groups = sorted(supervision["masks"]["M1_CONFIDENCE_GE1"]["groups"], key=int)
    xx = np.arange(len(groups)); width = 0.35
    for offset, mask in enumerate(("M1_CONFIDENCE_GE1", "M2_CONFIDENCE_EQ2")):
        ax.bar(xx + (offset - 0.5) * width, [supervision["masks"][mask]["groups"][group]["retained_fraction"] for group in groups], width, label=mask)
    ax.axhline(0.20, color="red", linestyle="--")
    ax.set_xticks(xx, groups); ax.set_xlabel("TRAIN group"); ax.set_ylabel("retained fraction"); ax.set_title("Group supervision coverage"); ax.legend(fontsize=7)
    finish(fig, figures / "group_supervision_coverage.png")

    fig, ax = plt.subplots(figsize=(10, 3.8))
    for mask in ("M1_CONFIDENCE_GE1", "M2_CONFIDENCE_EQ2"):
        zeros = supervision["masks"][mask]["zero_valid_frame_indices"]
        ax.scatter(zeros, [mask.split("_")[0]] * len(zeros), label=mask, s=28)
    ax.set_xlim(-1, 214); ax.set_title("Zero-valid frame timeline"); ax.set_xlabel("TRAIN frame index"); ax.legend(fontsize=7)
    finish(fig, figures / "zero_valid_frame_timeline.png")

    top_indices = concentration["top20_frames_by_gt_030"][:6]
    fig, axes = plt.subplots(len(top_indices), 3, figsize=(10, 2.4 * len(top_indices)))
    for row_number, index in enumerate(top_indices):
        rgb = np.asarray(imageio.imread(under(args.asset_root.resolve(), rows[index]["rgb"])))
        _, conf = load_depth_confidence(args.asset_root.resolve(), rows[index])
        cached = np.load(args.cache_root / f"frame_{index:03d}.npz")
        error = np.full(conf.shape, np.nan, dtype=np.float32)
        error[cached["y"], cached["x"]] = cached["distance_m"]
        axes[row_number, 0].imshow(rgb); axes[row_number, 0].set_title(f"#{index} RGB")
        axes[row_number, 1].imshow(conf, vmin=0, vmax=2, cmap="viridis"); axes[row_number, 1].set_title("confidence")
        axes[row_number, 2].imshow(error, vmin=0, vmax=0.6, cmap="magma"); axes[row_number, 2].set_title("point-to-mesh m")
        for axis in axes[row_number]: axis.axis("off")
    finish(fig, figures / "top_anomaly_evidence_montage.png")

    labels = causes["label_frame_counts"]
    fig, ax = plt.subplots(figsize=(10, 5))
    ax.barh(list(labels), list(labels.values()), color="#b279a2")
    ax.set_title("Evidence-bounded root-cause labels across top-20 frames"); ax.set_xlabel("frames")
    finish(fig, figures / "root_cause_summary.png")

    fig, ax = plt.subplots(figsize=(11, 4.5)); ax.axis("off")
    text = "Preregistered decision hierarchy\n\nImplementation error -> M0 -> M1 -> M2 -> zero semantics -> mesh coverage -> close route\n\n" + decision["FINAL_STATUS"] + "\n" + decision["FINAL_DECISION"]
    ax.text(0.5, 0.55, text, ha="center", va="center", fontsize=12, bbox={"boxstyle": "round", "facecolor": "#eef4fb"})
    finish(fig, figures / "decision_tree_result.png")

    fig, ax = plt.subplots(figsize=(10, 4.5)); ax.axis("off")
    claims = "ALLOWED\n- full-TRAIN data geometry and confidence association\n- reference-mesh coverage attribution\n- candidate data-validity recommendation\n\nPROHIBITED\n- learned map exists\n- confidence improves a trained map\n- frame deletion\n- controller/SAFER result\n- relaxed metric gate"
    ax.text(0.5, 0.55, claims, ha="center", va="center", fontsize=12, family="monospace", bbox={"boxstyle": "round", "facecolor": "#fff7e6"})
    finish(fig, figures / "claim_boundary.png")
    print("PASS_15_AUDIT_FIGURES")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
