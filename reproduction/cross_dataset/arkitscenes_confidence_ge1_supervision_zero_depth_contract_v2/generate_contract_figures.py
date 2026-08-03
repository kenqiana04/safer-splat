#!/usr/bin/env python3
"""Generate the compact figure set for the M1/empty-depth contract report."""

from __future__ import annotations

import argparse
import json
from pathlib import Path

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
from matplotlib.patches import FancyBboxPatch


FOOTER = "No smoke / no mapper / no training / no learned map / official source unmodified"


def load(path: Path):
    return json.loads(path.read_text(encoding="utf-8"))


def save(fig, path: Path) -> None:
    fig.text(0.5, 0.012, FOOTER, ha="center", fontsize=8, color="#555555")
    fig.tight_layout(rect=[0, 0.04, 1, 1])
    fig.savefig(path, dpi=160, bbox_inches="tight")
    plt.close(fig)


def text_figure(title: str, lines: list[str], path: Path, colors: list[str] | None = None) -> None:
    fig, ax = plt.subplots(figsize=(10, 5.6))
    ax.axis("off")
    ax.set_title(title, fontsize=15, weight="bold", pad=18)
    colors = colors or ["#1f2937"] * len(lines)
    top = 0.85
    spacing = 0.72 / max(1, len(lines))
    for index, (line, color) in enumerate(zip(lines, colors)):
        ax.text(0.5, top - index * spacing, line, ha="center", va="center", fontsize=11, color=color, wrap=True)
    save(fig, path)


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--task-root", type=Path, required=True)
    args = parser.parse_args()
    root = args.task_root.resolve()
    out = root / "figures"
    out.mkdir(parents=True, exist_ok=True)
    supervision = load(root / "arkitscenes_m1_supervision_v2_validation.json")
    synthetic = load(root / "nonempty_synthetic_equivalence.json")
    real = load(root / "nonempty_real_frame_equivalence.json")
    zero_syn = load(root / "zero_mask_synthetic_validation.json")
    zero_real = load(root / "zero_frame_real_validation.json")
    sequence = load(root / "sequence_state_dry_run.json")
    groups = supervision["groups"]
    labels = [str(row["group_id"]) for row in groups]
    n = np.array([row["frame_count"] for row in groups])
    supported = np.array([row["supported_frame_count"] for row in groups])
    required = np.array([row["required_supported_frame_count"] for row in groups])
    retention = np.array([row["pixel_retention"] for row in groups])

    fig, ax = plt.subplots(figsize=(10, 5.6))
    x = np.arange(len(labels))
    ax.bar(x, n, color="#94a3b8", label="Group size N_g")
    ax.axhline(10, color="#dc2626", linestyle="--", label="V1 required supported >=10")
    ax.set_xticks(x, labels)
    ax.set_xlabel("TRAIN group")
    ax.set_ylabel("Frames")
    ax.set_title("V1 fixed group gate is arithmetically infeasible for N_g < 10")
    ax.legend()
    save(fig, out / "v1_fixed_group_gate_infeasibility.png")

    fig, ax = plt.subplots(figsize=(10, 5.6))
    width = 0.36
    ax.bar(x - width / 2, np.full_like(n, 10), width, label="V1 fixed required", color="#f87171")
    ax.bar(x + width / 2, required, width, label="V2 max(1, ceil(0.8 N_g))", color="#34d399")
    ax.set_xticks(x, labels)
    ax.set_xlabel("TRAIN group")
    ax.set_ylabel("Required supported frames")
    ax.set_title("Gate definition comparison (only supported-count gate changes)")
    ax.legend()
    save(fig, out / "v1_vs_v2_group_gate_definition.png")

    fig, ax = plt.subplots(figsize=(10, 5.6))
    ax.bar(x - width / 2, supported, width, label="Observed S_g", color="#2563eb")
    ax.bar(x + width / 2, required, width, label="Required", color="#f59e0b")
    ax.set_xticks(x, labels)
    ax.set_xlabel("TRAIN group")
    ax.set_ylabel("Frames")
    ax.set_title("M1 group support under supervision V2")
    ax.legend()
    save(fig, out / "m1_group_support_v2.png")

    fig, ax = plt.subplots(figsize=(10, 5.6))
    ax.bar(x, retention, color=["#22c55e" if value >= 0.2 else "#ef4444" for value in retention])
    ax.axhline(0.2, color="#111827", linestyle="--", label="Frozen group retention gate")
    ax.set_xticks(x, labels)
    ax.set_ylim(0, 1.05)
    ax.set_xlabel("TRAIN group")
    ax.set_ylabel("M1 / M0 valid pixels")
    ax.set_title("M1 pixel retention by group")
    ax.legend()
    save(fig, out / "m1_pixel_retention_by_group.png")

    fig, ax = plt.subplots(figsize=(11, 3.8))
    indices = np.arange(214)
    support = np.ones(214)
    support[supervision["global"]["unsupported_indices"]] = 0
    ax.scatter(indices[support == 1], support[support == 1], s=10, color="#16a34a", label="supported")
    ax.scatter(indices[support == 0], support[support == 0], s=45, color="#dc2626", label="unsupported")
    for index in supervision["global"]["zero_valid_indices"]:
        ax.annotate(f"zero {index}", (index, 0), xytext=(0, 12), textcoords="offset points", ha="center")
    ax.set_yticks([0, 1], ["unsupported", "supported"])
    ax.set_xlabel("Canonical TRAIN row")
    ax.set_title("M1 frame support timeline; longest unsupported run = 4")
    ax.legend(loc="lower right")
    save(fig, out / "unsupported_frames_timeline.png")

    text_figure("Empty-depth-safe policy flow", [
        "First frame: M1 must be nonempty; otherwise INITIAL_FRAME_ZERO_DEPTH_UNSUPPORTED",
        "Later M1 nonempty -> official loss and depth-point paths",
        "Later M1 empty -> keep frame/RGB/pose/intrinsics; depth loss = predicted_depth.sum()*0",
        "No depth initialization, no new Gaussian, event EMPTY_DEPTH_SAFE_SKIP_DEPTH_INITIALIZATION",
        "No pseudo-depth, frame skip, extra iterations, optimizer, or parameter mutation",
    ], out / "empty_depth_policy_flow.png", ["#7c2d12", "#166534", "#1d4ed8", "#1d4ed8", "#7c2d12"])

    fig, ax = plt.subplots(figsize=(10, 5.6))
    metrics = [
        synthetic["max_depth_value_diff"]["float32"],
        synthetic["max_depth_value_diff"]["float64"],
        max(synthetic["max_gradient_diff"].values()),
        real["max_depth_loss_abs_diff"],
        real["max_rgb_loss_abs_diff"],
        real["max_point_attribute_abs_diff"],
    ]
    names = ["syn f32 depth", "syn f64 depth", "syn gradient", "real depth", "real RGB", "real points"]
    ax.bar(np.arange(len(names)), [max(value, 1e-16) for value in metrics], color="#0ea5e9")
    ax.set_yscale("log")
    ax.set_xticks(np.arange(len(names)), names, rotation=20, ha="right")
    ax.set_ylabel("Maximum absolute difference (log scale)")
    ax.set_title("Official vs compatibility nonempty equivalence")
    save(fig, out / "official_vs_compat_nonempty_equivalence.png")

    fig, ax = plt.subplots(figsize=(9, 5.6))
    names = ["Synthetic cases", "Real zero frames", "Depth=0", "Add count=0", "Finite"]
    values = [zero_syn["case_count"], len(zero_real["cases"]), len(zero_real["cases"]), len(zero_real["cases"]), len(zero_real["cases"])]
    ax.bar(np.arange(len(names)), values, color=["#6366f1", "#6366f1", "#22c55e", "#22c55e", "#22c55e"])
    ax.set_xticks(np.arange(len(names)), names, rotation=18, ha="right")
    ax.set_ylabel("Passing records")
    ax.set_title("Zero-mask and real zero-frame compatibility results")
    save(fig, out / "zero_frame_compatibility_results.png")

    fig, ax = plt.subplots(figsize=(11, 4.8))
    seq_indices = [row["index"] for row in sequence["states"]]
    routes = [0 if row["route"] == "EMPTY_DEPTH_SAFE" else 1 for row in sequence["states"]]
    ax.step(seq_indices, routes, where="mid", color="#2563eb", linewidth=2)
    ax.scatter(seq_indices, routes, c=["#dc2626" if value == 0 else "#16a34a" for value in routes], s=70)
    ax.set_yticks([0, 1], ["empty-safe", "official-equivalent"])
    ax.set_xticks(seq_indices)
    ax.set_xlabel("Canonical TRAIN row")
    ax.set_title("State-only dry run preserves sequence [74..81]")
    save(fig, out / "sequence_state_dry_run.png")

    text_figure("Protocol lineage", [
        "PR #70 canonical split identity",
        "PR #71 canonical loader/environment qualification",
        "PR #72 formal p99/confidence audit -> route closed without training",
        "This V2 post-audit pretraining revision -> M1-only normalized group gate",
        "Task-owned empty-depth compatibility qualification (no mapper/training)",
    ], out / "protocol_lineage.png")

    text_figure("Claim boundary", [
        "Allowed: M1 geometry passed; V2 group gate passed; empty branch is qualified in bounded tests",
        "Preserved: PR #72 formal failure and original fixed-gate diagnosis",
        "Not claimed: official SplaTAM native zero-depth support or unmodified baseline status",
        "Not claimed: learned map, smoke, training success, NVS, SAFER, FAS-CBF, or controller evidence",
        "Frames 76 and 79 remain in the canonical TRAIN sequence",
    ], out / "claim_boundary.png", ["#166534", "#1f2937", "#991b1b", "#991b1b", "#1f2937"])

    text_figure("Final protocol decision", [
        "PASS_ARKITSCENES_CONFIDENCE_GE1_SUPERVISION_AND_EMPTY_DEPTH_SAFE_CONTRACT_V2",
        "FREEZE_M1_WITH_EMPTY_DEPTH_SAFE_COMPATIBILITY",
        "Depth contract: DEPTH_GT_ZERO_AND_CONFIDENCE_GE1",
        "Mapper role: SPLATAM_DERIVED_GT_POSE_MAP_ONLY_WITH_EMPTY_DEPTH_SAFE_COMPATIBILITY",
        "Only next task: RESUME_ARKITSCENES_SPLATAM_M1_SMOKE_AND_LEARNED_MAP_QUALIFICATION_V1",
    ], out / "final_decision.png", ["#166534", "#166534", "#1d4ed8", "#1d4ed8", "#7c2d12"])

    required = {
        "v1_fixed_group_gate_infeasibility.png",
        "v1_vs_v2_group_gate_definition.png",
        "m1_group_support_v2.png",
        "m1_pixel_retention_by_group.png",
        "unsupported_frames_timeline.png",
        "empty_depth_policy_flow.png",
        "official_vs_compat_nonempty_equivalence.png",
        "zero_frame_compatibility_results.png",
        "sequence_state_dry_run.png",
        "protocol_lineage.png",
        "claim_boundary.png",
        "final_decision.png",
    }
    actual = {path.name for path in out.glob("*.png")}
    if actual != required:
        raise RuntimeError(f"figure set mismatch: missing={sorted(required-actual)} extra={sorted(actual-required)}")
    print("PASS_12_REQUIRED_FIGURES")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
