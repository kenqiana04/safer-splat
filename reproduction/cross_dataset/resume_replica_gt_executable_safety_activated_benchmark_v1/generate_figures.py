#!/usr/bin/env python3
"""Generate the 32 preregistered compact figures from frozen formal outputs."""
from __future__ import annotations

import csv
import json
import sys
from collections import Counter, defaultdict
from pathlib import Path
from typing import Any

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np

TASK_ROOT = Path(__file__).resolve().parent
sys.path.insert(0, str(TASK_ROOT))
from common import read_json
from task_config import METHODS, SLOT_IDS

SHORT = {method: method.split("_")[0] for method in METHODS}
COLORS = ["#4c78a8", "#f58518", "#54a24b", "#e45756"]


def rows(path: Path) -> list[dict[str, str]]:
    with path.open("r", encoding="utf-8", newline="") as handle:
        return list(csv.DictReader(handle))


def boolean(value: Any) -> bool:
    return str(value).lower() == "true"


def number(value: Any, default: float = 0.0) -> float:
    if value in (None, "", "None", "null"):
        return default
    return float(value)


def finish(fig: plt.Figure, name: str, evidence_label: str) -> None:
    fig.text(0.01, 0.012, evidence_label, fontsize=7, color="#444444", weight="bold")
    fig.text(0.99, 0.012, "CONFIGURATION-SPECIFIC | NOT A DEPLOYMENT CLAIM", ha="right", fontsize=7, color="#666666")
    fig.tight_layout(rect=(0, 0.045, 1, 1))
    fig.savefig(TASK_ROOT / "figures" / name, dpi=120, bbox_inches="tight", facecolor="white")
    plt.close(fig)


def text_figure(name: str, title: str, blocks: list[tuple[str, str]], label: str) -> None:
    fig, ax = plt.subplots(figsize=(9, 5))
    ax.axis("off")
    ax.set_title(title, fontsize=15, weight="bold", pad=16)
    y = 0.82
    for heading, body in blocks:
        ax.text(0.05, y, heading, fontsize=11, weight="bold", color="#1f4e79", transform=ax.transAxes)
        ax.text(0.05, y - 0.07, body, fontsize=10, wrap=True, transform=ax.transAxes)
        y -= 0.22
    finish(fig, name, label)


def bar_figure(name: str, title: str, labels: list[str], values: list[float], ylabel: str, evidence: str, colors: list[str] | None = None) -> None:
    fig, ax = plt.subplots(figsize=(9, 5))
    bars = ax.bar(np.arange(len(values)), values, color=colors or COLORS[:len(values)])
    ax.set_xticks(np.arange(len(labels)), labels, rotation=20, ha="right")
    ax.set_ylabel(ylabel)
    ax.set_title(title, weight="bold")
    ax.grid(axis="y", alpha=0.25)
    for bar, value in zip(bars, values):
        ax.text(bar.get_x() + bar.get_width() / 2, bar.get_height(), f"{value:.3g}", ha="center", va="bottom", fontsize=8)
    finish(fig, name, evidence)


def main() -> None:
    (TASK_ROOT / "figures").mkdir(parents=True, exist_ok=True)
    one = rows(TASK_ROOT / "benchmark/one_step_records.csv")
    episodes = rows(TASK_ROOT / "benchmark/episode_summary.csv")
    paired = rows(TASK_ROOT / "benchmark/paired_method_summary.csv")
    effects = rows(TASK_ROOT / "statistics/effect_sizes.csv")
    tests = rows(TASK_ROOT / "statistics/paired_tests.csv")
    search = read_json(TASK_ROOT / "activated_generation/search_summary.json")
    activated = read_json(TASK_ROOT / "registry/activated_registry_v1.json")
    representative = read_json(TASK_ROOT / "registry/representative_holdout_registry_v1.json")
    prevalence = read_json(TASK_ROOT / "audits/representative_prevalence_audit.json")
    decision = read_json(TASK_ROOT / "statistics/project_decision_gates.json")
    hypotheses = read_json(TASK_ROOT / "statistics/hypothesis_status.json")

    text_figure("scientific_question_and_falsification.png", "Can FAS-CBF Core V1 survive a preregistered falsification test?", [
        ("Existence", "Do segment and backup gates activate on frozen states?"),
        ("Recovery", "Does the six-slot library recover certified controls when B2 cannot?"),
        ("Relevance", "Do these mechanisms appear in a method-independent representative holdout?"),
        ("Falsification", "A weak representative gate prevents broad replacement claims even when activated mechanisms pass."),
    ], "ACTIVATED MECHANISM EVIDENCE + REPRESENTATIVE HOLDOUT")

    text_figure("pr84_pr85_pr86_lineage.png", "Frozen scientific lineage", [
        ("PR #84", "Unified executable safety certifier | 04ebca2b..."),
        ("PR #85", "Replica GT activated qualification | 7afef383..."),
        ("PR #86", "Nested B0-B3 method matrix + six slots | d4f20f44..."),
    ], "REPRESENTED-MAP CERTIFICATE")

    matrix = np.array([[1, 0, 0, 0], [1, 1, 0, 0], [1, 1, 1, 0], [1, 1, 1, 1]])
    fig, ax = plt.subplots(figsize=(8, 5)); ax.imshow(matrix, cmap="Blues", vmin=0, vmax=1)
    ax.set_xticks(range(4), ["Current", "Segment", "Terminal/backup", "6-slot alternatives"], rotation=18, ha="right")
    ax.set_yticks(range(4), ["B0", "B1", "B2", "B3"]); ax.set_title("Strictly nested B0-B3 method matrix", weight="bold")
    for i in range(4):
        for j in range(4): ax.text(j, i, "ON" if matrix[i, j] else "-", ha="center", va="center", color="white" if matrix[i, j] else "#555")
    finish(fig, "nested_B0_B3_method_matrix.png", "REPRESENTED-MAP CERTIFICATE")

    text_figure("activated_vs_representative_design.png", "Two cohorts answer different questions", [
        ("ACTIVATED", "Stage-predicate states; supports existence and mechanism only."),
        ("REPRESENTATIVE_HOLDOUT", "Method-independent route/hash sample; supports prevalence and utility."),
        ("Separation", "No pooling, no future reference outcomes during selection, immutable lock before methods."),
    ], "ACTIVATED MECHANISM EVIDENCE | REPRESENTATIVE HOLDOUT")

    funnel_keys = ["generated", "physical_valid", "current_feasible", "segment_safe", "primary_backup_fail", "B3_alternative_certified"]
    bar_figure("activated_stage_funnel.png", "Activated search funnel", funnel_keys, [search["funnel"].get(k, 0) for k in funnel_keys], "candidate count", "ACTIVATED MECHANISM EVIDENCE", ["#4c78a8"] * len(funnel_keys))
    groups = ["G0", "G1", "G2", "G3", "G4", "G5"]
    bar_figure("activated_group_counts.png", "Activated registry counts", groups, [activated["group_counts"].get(g, 0) for g in groups], "locked states", "ACTIVATED MECHANISM EVIDENCE", ["#54a24b"] * 6)

    source_counts = Counter(item["source_type"] for item in activated["states"])
    bar_figure("activated_registry_composition.png", "Activated registry source composition", list(source_counts), list(source_counts.values()), "states", "ACTIVATED MECHANISM EVIDENCE")
    text_figure("representative_sampling_pipeline.png", "Representative sampling pipeline", [
        ("Generate", "Frozen route nodes/edges x velocity lattice."),
        ("Physical gate", "Finite inputs, velocity bound, current map validity, start/goal mesh clearance."),
        ("Select", "Balanced strata ordered by canonical SHA; no stage, method, progress, runtime, or future outcome."),
        ("Lock", "160 states; three fresh-process byte-identical rebuilds."),
    ], "REPRESENTATIVE HOLDOUT")
    rep_source = Counter(item["source_type"] for item in representative["states"])
    bar_figure("representative_registry_composition.png", "Representative holdout source composition", list(rep_source), list(rep_source.values()), "states", "REPRESENTATIVE HOLDOUT")

    g1 = [r for r in one if r["cohort"] == "ACTIVATED" and r["postlock_group"] == "G1" and r["method"] == METHODS[1]]
    bar_figure("G1_endpoint_vs_segment_examples.png", "G1: endpoint diagnostic passes while swept segment rejects", [f"state {i+1}" for i in range(min(8, len(g1)))], [number(r["segment_lower_bound"]) for r in g1[:8]], "represented segment lower bound", "ACTIVATED MECHANISM EVIDENCE | REPRESENTED-MAP CERTIFICATE", ["#e45756"] * min(8, len(g1)))
    g2 = [r for r in one if r["cohort"] == "ACTIVATED" and r["postlock_group"] == "G2"]
    g2_rates = [sum(boolean(r["committed"]) for r in g2 if r["method"] == m) / 20 for m in METHODS]
    bar_figure("G2_primary_backup_fail_examples.png", "G2: terminal/backup gate adds discrimination", [SHORT[m] for m in METHODS], g2_rates, "commit rate", "ACTIVATED MECHANISM EVIDENCE")
    g3 = [r for r in one if r["cohort"] == "ACTIVATED" and r["postlock_group"] == "G3"]
    g3_rates = [sum(boolean(r["committed"]) for r in g3 if r["method"] == m) / 20 for m in METHODS]
    bar_figure("G3_directional_rescue_examples.png", "G3: B3 recovers certified control after B2 failure", [SHORT[m] for m in METHODS], g3_rates, "commit rate", "ACTIVATED MECHANISM EVIDENCE", COLORS)
    slots = Counter(r["selected_candidate"] for r in one if r["selected_candidate"] in SLOT_IDS)
    bar_figure("selected_directional_slot_distribution.png", "Selected directional slot distribution", [key.replace("ALT-", "") for key in SLOT_IDS], [slots.get(key, 0) for key in SLOT_IDS], "selections", "ACTIVATED MECHANISM EVIDENCE")

    for cohort, filename, evidence in (("ACTIVATED", "one_step_status_matrix_activated.png", "ACTIVATED MECHANISM EVIDENCE"), ("REPRESENTATIVE_HOLDOUT", "one_step_status_matrix_representative.png", "REPRESENTATIVE HOLDOUT")):
        groups_here = sorted({r["postlock_group"] for r in one if r["cohort"] == cohort})
        data = np.zeros((len(METHODS), len(groups_here)))
        for i, method in enumerate(METHODS):
            for j, group in enumerate(groups_here):
                values = [r for r in one if r["cohort"] == cohort and r["method"] == method and r["postlock_group"] == group]
                data[i, j] = sum(boolean(r["committed"]) for r in values) / len(values)
        fig, ax = plt.subplots(figsize=(8, 5)); im = ax.imshow(data, cmap="RdYlGn", vmin=0, vmax=1)
        ax.set_xticks(range(len(groups_here)), groups_here); ax.set_yticks(range(4), [SHORT[m] for m in METHODS]); ax.set_title(f"One-step commit matrix: {cohort}", weight="bold")
        for i in range(data.shape[0]):
            for j in range(data.shape[1]): ax.text(j, i, f"{data[i,j]:.2f}", ha="center", va="center")
        fig.colorbar(im, ax=ax, label="commit rate"); finish(fig, filename, evidence)

    commit_labels, commit_values = [], []
    for group in groups:
        for method in (METHODS[0], METHODS[3]):
            values = [r for r in one if r["cohort"] == "ACTIVATED" and r["postlock_group"] == group and r["method"] == method]
            commit_labels.append(f"{group}-{SHORT[method]}"); commit_values.append(sum(boolean(r["committed"]) for r in values) / len(values))
    bar_figure("commit_rate_by_group.png", "Activated commit rate by group (B0 vs B3)", commit_labels, commit_values, "commit rate", "ACTIVATED MECHANISM EVIDENCE", [COLORS[0], COLORS[3]] * 6)
    prev = prevalence["prevalence"]
    bar_figure("gate_activation_prevalence_representative.png", "Representative gate and outcome prevalence", [r["metric"] for r in prev], [r["rate"] for r in prev], "rate", "REPRESENTATIVE HOLDOUT", ["#4c78a8"] * len(prev))

    reason_counts = Counter((r["cohort"], r["typed_reason"]) for r in one if not boolean(r["committed"]))
    top_reasons = reason_counts.most_common(10)
    bar_figure("fail_closed_reason_by_cohort.png", "Top fail-closed typed reasons", [f"{c[:3]}:{reason[:20]}" for (c, reason), _ in top_reasons], [count for _, count in top_reasons], "method-record count", "ACTIVATED MECHANISM EVIDENCE | REPRESENTATIVE HOLDOUT", ["#e45756"] * len(top_reasons))

    bounds = [number(r["segment_lower_bound"]) for r in one if r["segment_lower_bound"] not in ("", "None", "null")]
    fig, ax = plt.subplots(figsize=(9, 5)); ax.hist(bounds, bins=30, color="#4c78a8"); ax.axvline(0, color="#e45756", linestyle="--"); ax.set_title("Represented immediate-segment certificate bounds", weight="bold"); ax.set_xlabel("lower bound"); ax.set_ylabel("records"); finish(fig, "represented_segment_bounds.png", "REPRESENTED-MAP CERTIFICATE")
    collision_values = [sum(boolean(r["reference_collision_after_commit"]) for r in one if r["method"] == m) for m in METHODS]
    bar_figure("reference_swept_collision_by_method.png", "Offline reference immediate collisions after commit", [SHORT[m] for m in METHODS], collision_values, "collision method-records", "OFFLINE REFERENCE ONLY", COLORS)
    disagreement = Counter((r["cohort"] for r in one if boolean(r["map_reference_disagreement"])))
    bar_figure("map_reference_disagreement.png", "Represented-map vs offline-reference disagreement", ["ACTIVATED", "REPRESENTATIVE"], [disagreement["ACTIVATED"], disagreement["REPRESENTATIVE_HOLDOUT"]], "method-records", "REPRESENTED-MAP CERTIFICATE | OFFLINE REFERENCE ONLY")

    labels, vals = [], []
    for group in ("G0", "G1", "G2", "G3"):
        for method in METHODS:
            values = [number(r["progress_m"]) for r in one if r["cohort"] == "ACTIVATED" and r["postlock_group"] == group and r["method"] == method]
            labels.append(f"{group}-{SHORT[method]}"); vals.append(float(np.mean(values)))
    bar_figure("progress_by_method_group.png", "One-step progress by activated group", labels, vals, "mean progress (m)", "ACTIVATED MECHANISM EVIDENCE")
    rep_progress = [float(np.mean([number(r["progress_m"]) for r in episodes if r["cohort"] == "REPRESENTATIVE_HOLDOUT" and r["method"] == m])) for m in METHODS]
    bar_figure("progress_representative.png", "Representative bounded-rollout progress", [SHORT[m] for m in METHODS], rep_progress, "mean progress (m)", "REPRESENTATIVE HOLDOUT | LOGICAL-TIME ROLLOUT", COLORS)
    terminal = Counter((r["method"], r["episode_terminal_reason"]) for r in episodes)
    reasons = sorted({reason for _, reason in terminal})
    fig, ax = plt.subplots(figsize=(9, 5)); bottom = np.zeros(4)
    for reason in reasons:
        values = np.array([terminal[(m, reason)] for m in METHODS]); ax.bar(range(4), values, bottom=bottom, label=reason); bottom += values
    ax.set_xticks(range(4), [SHORT[m] for m in METHODS]); ax.set_ylabel("episodes"); ax.set_title("Bounded logical-rollout terminal reasons", weight="bold"); ax.legend(fontsize=7); finish(fig, "rollout_terminal_reasons.png", "LOGICAL-TIME ROLLOUT")
    over = [sum(boolean(r["reference_safe_but_rejected"]) for r in one if r["cohort"] == "REPRESENTATIVE_HOLDOUT" and r["method"] == m) for m in METHODS]
    bar_figure("over_rejection_reference_safe.png", "Reference-safe but rejected: representative holdout", [SHORT[m] for m in METHODS], over, "states", "REPRESENTATIVE HOLDOUT | OFFLINE REFERENCE ONLY", COLORS)

    component_names = ["current_query_and_filter", "segment", "alternative_generation", "backup_certification", "terminal_certification"]
    component_means = []
    for method in METHODS:
        parsed = [json.loads(r["component_timing"]) for r in one if r["method"] == method]
        component_means.append([float(np.mean([number(item.get(name)) for item in parsed])) for name in component_names])
    fig, ax = plt.subplots(figsize=(9, 5)); bottom = np.zeros(4)
    for index, name in enumerate(component_names):
        values = np.array([row[index] for row in component_means]); ax.bar(range(4), values, bottom=bottom, label=name); bottom += values
    ax.axhline(0.05, color="#e45756", linestyle="--", label="50 ms"); ax.set_xticks(range(4), [SHORT[m] for m in METHODS]); ax.set_ylabel("mean seconds"); ax.set_title("Runtime component breakdown", weight="bold"); ax.legend(fontsize=7); finish(fig, "runtime_component_breakdown.png", "RUNTIME DIAGNOSTIC")
    miss = [sum(boolean(r["deadline_miss"]) for r in one if r["method"] == m) / 260 for m in METHODS]
    bar_figure("deadline_miss_rate.png", "50 ms deadline miss rate", [SHORT[m] for m in METHODS], miss, "miss rate", "RUNTIME DIAGNOSTIC", COLORS)

    binary_effects = [r for r in effects if r["effect"] == "PAIRED_BINARY_RATE_DIFFERENCE_B_MINUS_A"]
    bar_figure("paired_effect_sizes.png", "Preregistered paired binary effect sizes", [r["hypothesis"] for r in binary_effects], [number(r["estimate"]) for r in binary_effects], "rate difference (B-A)", "PROJECT DECISION THRESHOLD", ["#4c78a8"] * len(binary_effects))
    status_score = [1 if str(hypotheses[f"H{i}"]).startswith(("SUPPORTED", "NO_G0")) else 0 for i in range(1, 8)]
    bar_figure("hypothesis_status_H1_H7.png", "Preregistered H1-H7 outcome status", [f"H{i}" for i in range(1, 8)], status_score, "supported / documented", "PROJECT DECISION THRESHOLD", ["#54a24b" if v else "#f58518" for v in status_score])
    gates = [decision["scientific_mechanism_gate"], decision["active_utility_gate"], decision["representative_relevance_gate"], decision["reference_no_adverse_regression"]]
    bar_figure("project_go_no_go_decision.png", "Frozen project gates", ["mechanism", "active utility", "representative relevance", "no adverse reference"], [int(v) for v in gates], "gate pass", "PROJECT DECISION THRESHOLD", ["#54a24b" if v else "#e45756" for v in gates])
    text_figure("claim_boundary.png", "Claim boundary after formal results", [
        ("Supported", "Configuration-specific activated gate existence and G3 directional rescue; zero represented false-safe."),
        ("Not supported", "Broad prevalence, collision superiority, real-time readiness, deployment, or cross-map generalization."),
        ("Separation", "Represented-map certificates and offline-reference geometry remain distinct evidence layers."),
    ], "ACTIVATED MECHANISM EVIDENCE | REPRESENTATIVE HOLDOUT | OFFLINE REFERENCE ONLY")
    text_figure("final_decision.png", "Final preregistered decision: Case C", [
        ("FINAL STATUS", decision["final_status"]),
        ("FINAL DECISION", decision["final_decision"]),
        ("ONLY NEXT TASK", decision["only_next_task"]),
    ], "PROJECT DECISION THRESHOLD")

    expected = {
        "scientific_question_and_falsification.png", "pr84_pr85_pr86_lineage.png", "nested_B0_B3_method_matrix.png",
        "activated_vs_representative_design.png", "activated_stage_funnel.png", "activated_group_counts.png",
        "activated_registry_composition.png", "representative_sampling_pipeline.png", "representative_registry_composition.png",
        "G1_endpoint_vs_segment_examples.png", "G2_primary_backup_fail_examples.png", "G3_directional_rescue_examples.png",
        "selected_directional_slot_distribution.png", "one_step_status_matrix_activated.png", "one_step_status_matrix_representative.png",
        "commit_rate_by_group.png", "gate_activation_prevalence_representative.png", "fail_closed_reason_by_cohort.png",
        "represented_segment_bounds.png", "reference_swept_collision_by_method.png", "map_reference_disagreement.png",
        "progress_by_method_group.png", "progress_representative.png", "rollout_terminal_reasons.png",
        "over_rejection_reference_safe.png", "runtime_component_breakdown.png", "deadline_miss_rate.png",
        "paired_effect_sizes.png", "hypothesis_status_H1_H7.png", "project_go_no_go_decision.png",
        "claim_boundary.png", "final_decision.png",
    }
    actual = {path.name for path in (TASK_ROOT / "figures").glob("*.png")}
    if actual != expected:
        raise SystemExit(f"FIGURE_SET_MISMATCH missing={expected-actual} extra={actual-expected}")
    print("PASS_32_REQUIRED_FIGURES", len(actual))


if __name__ == "__main__":
    main()
