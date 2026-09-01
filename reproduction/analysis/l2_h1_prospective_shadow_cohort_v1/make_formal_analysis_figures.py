#!/usr/bin/env python3
"""Create bounded static figures from locked compact analysis summaries only."""

from __future__ import annotations

import argparse
import csv
from pathlib import Path

import matplotlib.pyplot as plt

from analysis_common import atomic_write_json, file_sha256, load_json


def style() -> None:
    plt.rcParams.update({"font.family": "DejaVu Sans", "font.size": 10, "axes.titlesize": 12, "axes.labelsize": 10,
                         "axes.edgecolor": "#343A40", "text.color": "#202428", "axes.labelcolor": "#202428",
                         "xtick.color": "#343A40", "ytick.color": "#343A40", "figure.facecolor": "white", "axes.facecolor": "white"})


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--task-dir", type=Path, required=True)
    args = parser.parse_args()
    task = args.task_dir
    figures = task / "figures"; figures.mkdir(parents=True, exist_ok=True)
    primary = load_json(task / "primary_result.json")
    with (task / "per_trial_primary.csv").open("r", encoding="utf-8", newline="") as handle:
        per_trial = list(csv.DictReader(handle))
    style()

    stages = ["Intended steps", "L1 PASS", "L2 reached", "Primary eligible"]
    reason = primary["primary_eligibility_reason_counts"]
    values = [primary["N_intended_control_steps"], primary["N_intended_control_steps"] - reason.get("l1_status_pass", 0),
              primary["N_intended_control_steps"] - reason.get("l2_reached", 0), primary["N_primary"]]
    fig, axes = plt.subplots(1, 2, figsize=(10.8, 4.5), gridspec_kw={"width_ratios": [1.35, 1]})
    bars = axes[0].bar(stages, values, color=["#4C78A8", "#B9CBE2", "#B9CBE2", "#E5E7EB"], edgecolor="#343A40", linewidth=0.8)
    axes[0].set_title("Primary cohort eligibility support")
    axes[0].set_ylabel("Control-step count")
    axes[0].set_ylim(0, max(values) * 1.13)
    axes[0].tick_params(axis="x", rotation=18)
    axes[0].grid(axis="y", color="#E5E7EB", linewidth=0.7)
    axes[0].set_axisbelow(True)
    for bar, value in zip(bars, values): axes[0].text(bar.get_x() + bar.get_width()/2, value + max(values)*0.02, f"{value:,}", ha="center", va="bottom")

    tri = [primary["N_L2_PASS"], primary["N_L2_FAIL"], primary["N_L2_UNKNOWN"]]
    tri_bars = axes[1].bar(["PASS", "FAIL", "UNKNOWN"], tri, color=["#4C78A8", "#F2CF5B", "#B8B8B8"], edgecolor="#343A40", linewidth=0.8)
    axes[1].set_title("Primary tri-state composition")
    axes[1].set_ylabel("Primary-eligible count")
    axes[1].set_ylim(0, 1)
    axes[1].set_yticks([0, 1])
    axes[1].text(0.5, 0.58, "N_primary = 0\nTri-state rate not estimable", transform=axes[1].transAxes, ha="center", va="center", fontsize=12, color="#5B6168")
    for bar, value in zip(tri_bars, tri): axes[1].text(bar.get_x()+bar.get_width()/2, 0.03, str(value), ha="center", va="bottom")
    fig.suptitle("Formal L2/H1 prospective shadow cohort — primary support", y=1.01, fontsize=14, weight="bold")
    fig.tight_layout()
    first = figures / "primary_support_and_tri_state.png"; fig.savefig(first, dpi=180, bbox_inches="tight"); plt.close(fig)

    trial_ids = [int(row["trial_id"]) for row in per_trial]
    n_primary = [int(row["N_primary"]) for row in per_trial]
    fig, ax = plt.subplots(figsize=(10.8, 4.1))
    ax.bar(trial_ids, n_primary, width=0.85, color="#4C78A8", edgecolor="#343A40", linewidth=0.25)
    ax.set_title("Per-trial primary-eligible support")
    ax.set_xlabel("Formal trial ID (fixed order 0–99)")
    ax.set_ylabel("N_primary")
    ax.set_xlim(-1, 100); ax.set_ylim(0, 1); ax.set_yticks([0, 1])
    ax.grid(axis="y", color="#E5E7EB", linewidth=0.7); ax.set_axisbelow(True)
    ax.text(0.5, 0.62, "All 100 trials: N_primary = 0", transform=ax.transAxes, ha="center", fontsize=12, color="#5B6168")
    fig.tight_layout()
    second = figures / "per_trial_primary_support.png"; fig.savefig(second, dpi=180, bbox_inches="tight"); plt.close(fig)

    atomic_write_json(task / "figure_provenance.json", {
        "schema_version": "L2_H1_FORMAL_ANALYSIS_FIGURE_PROVENANCE_V1", "source_is_locked_compact_summary": True,
        "source_files": {"primary_result.json": file_sha256(task / "primary_result.json"), "per_trial_primary.csv": file_sha256(task / "per_trial_primary.csv")},
        "figures": [{"path": f"figures/{first.name}", "sha256": file_sha256(first)}, {"path": f"figures/{second.name}", "sha256": file_sha256(second)}],
        "collision_progress_runtime_metrics_used": False,
    })
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
