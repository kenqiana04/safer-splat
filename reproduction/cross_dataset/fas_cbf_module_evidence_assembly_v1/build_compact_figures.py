#!/usr/bin/env python3
"""Render compact, data-derived figures for the frozen evidence package."""
from __future__ import annotations

import matplotlib.pyplot as plt
import numpy as np

from evidence_common import TASK, load_json

OUT = TASK / "figures"


def finish(name: str, title: str) -> None:
    plt.title(title, loc="left", fontsize=11, weight="bold")
    plt.tight_layout()
    plt.savefig(OUT / name, dpi=160, bbox_inches="tight")
    plt.close()


def bars(name: str, title: str, labels: list[str], values: list[float], color: str = "#2f6f9f", ylabel: str = "count") -> None:
    plt.figure(figsize=(7.0, 3.7))
    plot = plt.bar(labels, values, color=color)
    for bar, value in zip(plot, values):
        plt.text(bar.get_x() + bar.get_width() / 2, value, f"{value:g}", ha="center", va="bottom", fontsize=8)
    plt.ylabel(ylabel)
    plt.xticks(rotation=22, ha="right")
    finish(name, title)


def text_panel(name: str, title: str, lines: list[str]) -> None:
    plt.figure(figsize=(8.0, 4.2))
    plt.axis("off")
    plt.text(0.03, 0.93, "\n".join(lines), va="top", family="DejaVu Sans", fontsize=10, wrap=True)
    finish(name, title)


def heatmap(name: str, title: str, matrix: np.ndarray, rows: list[str], cols: list[str]) -> None:
    plt.figure(figsize=(8.0, 4.5))
    plt.imshow(matrix, cmap="Blues", vmin=0, vmax=max(1, int(matrix.max())))
    for i in range(matrix.shape[0]):
        for j in range(matrix.shape[1]):
            plt.text(j, i, str(int(matrix[i, j])), ha="center", va="center", fontsize=8)
    plt.xticks(range(len(cols)), cols, rotation=24, ha="right")
    plt.yticks(range(len(rows)), rows)
    plt.colorbar(label="evidence count")
    finish(name, title)


def main() -> int:
    OUT.mkdir(parents=True, exist_ok=True)
    sources = load_json("source_inventory/source_inventory.json")["sources"]
    modules = load_json("module_matrices/module_evidence_matrix.json")["modules"]
    claims = load_json("claim_audit/claim_evidence_matrix.json")["claims"]
    role_rows = load_json("module_matrices/dataset_map_role_matrix.json")["roles"]
    decision = load_json("minimal_remaining_experiment/minimal_remaining_experiment.json")
    polarity = [sum(row["polarity"] == label for row in sources) for label in ("positive", "negative", "structural")]
    activity = [sum(row["activity"] == label for row in sources) for label in ("active", "shadow", "static", "formal", "diagnostic")]
    bars("research_scope_and_claim_boundary.png", "Frozen evidence scope: source result types", ["positive", "negative", "structural"], polarity, "#496e3a")
    bars("dataset_and_map_role_matrix.png", "Dataset/map-role evidence inventory", [row["map_role"].replace("_", "\n") for row in role_rows], [row["evidence_count"] for row in role_rows], "#8d6e63")
    bars("evidence_provenance_flow.png", "Evidence provenance by map role", [row["map_role"].split("_")[-1] for row in role_rows], [row["evidence_count"] for row in role_rows], "#5e81ac")
    heatmap("module_evidence_strength_matrix.png", "Module evidence strength by layer", np.array([[int(row[key]) for key in ("implemented", "mechanism_supported", "configuration_specific_supported", "efficiency_supported", "structural_boundary_supported")] for row in modules]), [row["module_id"] for row in modules], ["impl", "mechanism", "config", "efficiency", "boundary"])
    bars("start_safe_evidence_summary.png", "Start-Safe verified repairs", ["natural", "active-set", "synthetic", "Replica static"], [8, 8, 120, 30], "#4c956c", "verified states/trials")
    bars("constraint_efficiency_evidence_summary.png", "Stonehenge Risk-Aware V1 efficiency", ["constraints baseline", "constraints bestD", "runtime baseline", "runtime bestD"], [505.5866495, 252.2219893, 63.07919365, 40.44284326], "#bc6c25", "constraints or ms")
    bars("dt_evidence_taxonomy.png", "DT risk taxonomy: dense-flight detections", ["H1 margin", "H2 margin", "H3 margin", "ETH3D endpoint unsafe"], [463, 488, 519, 0], "#9b5de5")
    bars("recovery_evidence_summary.png", "Predictive recovery: configuration-specific activations", ["H3 success", "H2 tuned success", "Replica success", "HCE contexts"], [236, 193, 45, 201], "#0077b6")
    bars("negative_and_structural_results.png", "Retained negative and structural boundaries", ["V4B correction success", "trial20 failures", "ETH3D strict H3 states"], [0, 34, 0], "#c1121f")
    bars("replica_vs_eth3d_roles.png", "Replica GT benchmark versus ETH3D learned-map carrier", ["Replica admissible routes", "Replica M4 recovery", "ETH3D projectable", "ETH3D G3 endpoint unsafe"], [99, 45, 42049, 0], "#3a86ff")
    bars("active_vs_shadow_vs_static_evidence.png", "Evidence activity boundary", ["active", "shadow", "static", "formal", "diagnostic"], activity, "#ffbe0b")
    status_order = ["CONFIGURATION_SPECIFIC", "PARTIALLY_SUPPORTED", "PROHIBITED"]
    bars("claim_to_evidence_matrix.png", "Claim audit statuses", status_order, [sum(row["status"] == status for row in claims) for status in status_order], "#8338ec", "claim count")
    compat = load_json("config_compatibility/cohort_overlap_audit.json")
    text_panel("configuration_compatibility.png", "Configuration compatibility rule", ["No cross-map pooled effect sizes.", "No nested horizon subtraction.", "No original/post-repair pooling.", "No HCE/full100 pooled inference.", f"Status: {compat['status']}"])
    text_panel("cohort_overlap_and_independence.png", "Cohort overlap and independence", ["Trial57 remains inside original flight history.", "H1/H2/H3 are nested step counts.", "HCE is an activated selected cohort.", "TUM shadow and intervention stay separate."])
    text_panel("full_stack_superiority_gap.png", "Full-stack superiority evidence gap", ["Replica: 99/99 map-admissible route success for all methods.", "ETH3D: strict H3 endpoint-unsafe/QP-feasible state count = 0.", "No same-map, fully activated paired superiority evidence.", "Global superiority claim: prohibited."])
    text_panel("paper_experiment_architecture.png", "Paper experiment architecture", ["E1 map roles", "E2 Start-Safe", "E3 constraint/efficiency", "E4 DT taxonomy", "E5 predictive recovery", "E6 external validity and limits"])
    text_panel("minimal_remaining_experiment_decision.png", "Minimal remaining experiment decision", ["Case B: module-wise evidence is sufficient for paper framing.", "No new experiment authorized in this task.", "A future global-superiority claim needs separately authorized,", "one-map, outcome-blind, fully activated paired evidence."])
    text_panel("final_decision.png", "Final decision", [decision["FINAL_STATUS"], decision["FINAL_DECISION"], decision["ONLY_NEXT_TASK"]])
    expected = 18
    if len(list(OUT.glob("*.png"))) != expected:
        raise RuntimeError("figure count mismatch")
    print(f"PASS_COMPACT_FIGURES count={expected}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
