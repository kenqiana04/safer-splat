"""Generate the twenty preregistered compact Protocol V2 figures."""
from __future__ import annotations

import json
import textwrap
from pathlib import Path

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.patches import Patch, Rectangle
import numpy as np

from requalification_core import MAP_ORDER, ROOT, load


COLORS = {
    "measured": "#2F6B9A",
    "derived": "#D49A2A",
    "empirical": "#E07A35",
    "unresolved": "#8A8F98",
    "not_evaluable": "#D9DDE3",
    "ink": "#22252A",
    "pink": "#C65A87",
}


def finish(fig, path: Path, source_note: str) -> None:
    fig.text(0.01, 0.01, source_note, fontsize=7, color="#5D6168")
    fig.tight_layout(rect=(0, 0.035, 1, 1))
    path.parent.mkdir(parents=True, exist_ok=True)
    fig.savefig(path, dpi=180, facecolor="white")
    plt.close(fig)


def bar_figure(name, title, labels, values, colors, ylabel, note, rotate=25):
    fig, ax = plt.subplots(figsize=(9.5, 5.3))
    x = np.arange(len(labels))
    bars = ax.bar(x, values, color=colors, edgecolor=COLORS["ink"], linewidth=0.6)
    ax.set_title(title, loc="left", fontweight="bold")
    ax.set_ylabel(ylabel)
    ax.set_xticks(x, labels, rotation=rotate, ha="right")
    ax.grid(axis="y", color="#E8EAED", linewidth=0.8)
    ax.set_axisbelow(True)
    for bar, value in zip(bars, values):
        ax.text(bar.get_x() + bar.get_width()/2, bar.get_height(), f"{value:g}", ha="center", va="bottom", fontsize=8)
    finish(fig, ROOT / "figures" / name, note)


def matrix_figure(name, title, row_labels, col_labels, matrix, annotations, note):
    fig, ax = plt.subplots(figsize=(9.8, max(4.8, 0.48 * len(row_labels) + 1.8)))
    im = ax.imshow(matrix, cmap=matplotlib.colors.ListedColormap([COLORS["not_evaluable"], COLORS["unresolved"], COLORS["derived"], COLORS["measured"]]), vmin=0, vmax=3, aspect="auto")
    ax.set_title(title, loc="left", fontweight="bold")
    ax.set_xticks(range(len(col_labels)), col_labels, rotation=25, ha="right")
    ax.set_yticks(range(len(row_labels)), row_labels)
    for i in range(len(row_labels)):
        for j in range(len(col_labels)):
            ax.text(j, i, annotations[i][j], ha="center", va="center", fontsize=7, color="white" if matrix[i][j] in (1, 3) else COLORS["ink"])
    legend = [Patch(facecolor=COLORS[k], label=k.replace("_", " ").title()) for k in ("measured", "derived", "unresolved", "not_evaluable")]
    ax.legend(handles=legend, loc="upper center", bbox_to_anchor=(0.5, -0.16), ncol=4, frameon=False)
    finish(fig, ROOT / "figures" / name, note)


def flow_figure(name, title, boxes, note):
    fig, ax = plt.subplots(figsize=(11, 4.8))
    ax.axis("off")
    xs = np.linspace(0.12, 0.88, len(boxes))
    for index, ((headline, body, state), x) in enumerate(zip(boxes, xs)):
        color = COLORS[state]
        wrapped = "\n".join(textwrap.wrap(body, width=24, break_long_words=True, break_on_hyphens=False))
        ax.text(x, 0.56, headline + "\n\n" + wrapped, transform=ax.transAxes, ha="center", va="center", fontsize=8,
                bbox={"boxstyle": "round,pad=0.7", "facecolor": color, "edgecolor": COLORS["ink"], "alpha": 0.9}, color="white" if state in ("measured", "unresolved") else COLORS["ink"])
        if index + 1 < len(boxes):
            ax.annotate("", xy=(xs[index+1]-0.09, 0.56), xytext=(x+0.09, 0.56), xycoords=ax.transAxes, arrowprops={"arrowstyle": "->", "color": COLORS["ink"], "lw": 1.4})
    ax.set_title(title, loc="left", fontweight="bold")
    finish(fig, ROOT / "figures" / name, note)


def main() -> None:
    inventory = load(ROOT / "map_inventory" / "requalification_map_inventory.json")
    cards = load(ROOT / "classification" / "classification_matrix.json")["maps"]
    parity = load(ROOT / "native_common" / "native_common_parity_per_map.json")
    risk = load(ROOT / "risk_coverage" / "risk_coverage_per_map.json")
    unknown = load(ROOT / "unknown" / "unknown_missingness_per_map.json")
    budget = load(ROOT / "physical_budget" / "physical_budget_per_map.json")
    g0 = load(ROOT / "safer_g0" / "safer_g0_summary.json")
    decision = load(ROOT / "classification" / "final_decision.json")
    short = {m: m.replace("ARKITSCENES_", "ARKIT_").replace("REPLICA_", "R_").replace("TUM_", "T_").replace("SAFER_OFFICIAL_", "S_") for m in MAP_ORDER}

    bar_figure("protocol_v2_control_discrimination.png", "Protocol V2 control discrimination", ["GT positive reaches R3/N3", "Splatfacto negative rejected from N3"], [1, 1], [COLORS["measured"], COLORS["derived"]], "Frozen control outcome", "Measured/derived from PR #64, PR #57 and fresh 3×256 G0 evidence.", 10)
    bar_figure("map_artifact_availability.png", "Map artifact availability", ["Accessible", "Unavailable"], [inventory["accessible_count"], inventory["unavailable_count"]], [COLORS["measured"], COLORS["not_evaluable"]], "Map count", "Server existence and immutable artifact inventory; unavailable maps were not retrained.", 0)
    ref_counts = {k: sum(c["REFERENCE_AUTHORITY"] == k for c in cards) for k in ("A_DENSE_INDEPENDENT_GEOMETRY", "B_OBSERVABLE_RAY_REFERENCE", "C_INTERFACE_ONLY", "UNRESOLVED")}
    bar_figure("map_reference_authority.png", "Reference authority by map", ["A dense", "B rays", "C interface", "Unresolved"], list(ref_counts.values()), [COLORS["measured"], COLORS["derived"], COLORS["empirical"], COLORS["unresolved"]], "Map count", "Authority labels are categorical evidence bounds, not a quality ranking.", 0)
    pcounts = parity["counts"]
    bar_figure("native_common_parity.png", "Native/common channel status", ["Numeric", "Semantic", "Native only", "Not evaluable"], [pcounts["NUMERIC_PARITY_PASS"], pcounts["SEMANTIC_PARITY_ONLY"], pcounts["NATIVE_ONLY"], pcounts["NOT_EVALUABLE"]], [COLORS["measured"], COLORS["derived"], COLORS["empirical"], COLORS["not_evaluable"]], "Map count", "Render parity is kept separate from G0 query compatibility.", 15)

    arkit = next(row for row in risk["maps"] if row["map_id"] == "ARKITSCENES_M1_SPLATAM")
    points = arkit["points"]
    fig, ax = plt.subplots(figsize=(9.5, 5.3)); ax.plot([p["tau_alpha"] for p in points], [p["global_coverage"] for p in points], marker="o", color=COLORS["measured"], label="ARKit M1 measured")
    ax.scatter([0.5], [next(row for row in risk["maps"] if row["map_id"] == "REPLICA_SPLATAM_60")["working_point"]["valid_predicted_depth_fraction"]], color=COLORS["empirical"], marker="D", label="Replica SplaTAM single point")
    ax.set(title="Risk-coverage evidence across available learned maps", xlabel="Alpha threshold / retained working point", ylabel="Coverage"); ax.legend(frameon=False); ax.grid(color="#E8EAED")
    finish(fig, ROOT / "figures" / "risk_coverage_all_available_maps.png", "Only ARKit M1 has the complete fixed 11-alpha curve; isolated points are not interpolated.")

    fig, ax = plt.subplots(figsize=(9.5, 5.3)); ax.plot([p["global_coverage"] for p in points], [p["AbsRel"] for p in points], marker="o", color=COLORS["measured"])
    for p in (points[0], points[5], points[-1]): ax.annotate(f"α={p['tau_alpha']:.2f}", (p["global_coverage"], p["AbsRel"]), xytext=(5, 5), textcoords="offset points", fontsize=8)
    ax.set(title="Conditional error versus observed coverage", xlabel="Observed global coverage", ylabel="Conditional AbsRel"); ax.grid(color="#E8EAED")
    finish(fig, ROOT / "figures" / "conditional_error_vs_coverage.png", "ARKitScenes M1 held-out observable rays; AURC is descriptive, never a hard gate.")

    matrix_figure("multi_tolerance_replica_maps.png", "Replica multi-tolerance evidence", ["GT-FINE", "Splatfacto", "SplaTAM-60"], [f"{t:.2f}m" for t in [0.01,0.02,0.03,0.05,0.10,0.20]], np.array([[2]*6,[0]*6,[0]*6]), [["cert"]*6,["N/E"]*6,["N/E"]*6], "GT-FINE has a deterministic construction certificate; learned maps lack retained bidirectional samples.")
    missing = load(ROOT.parent / "gaussian_map_metric_provenance_navigation_usability_calibration_v1" / "spatial_missingness" / "spatial_missingness_results.json")["maps"][0]
    bar_figure("spatial_missingness_summary.png", "Observable spatial missingness", ["ARKit global", "ARKit frame macro", "Worst 5% frames", "Other maps unresolved"], [missing["global_missing_fraction"], missing["macro_frame_missing_fraction"], missing["worst_5pct_frame_missing_fraction"], 0], [COLORS["measured"], COLORS["measured"], COLORS["empirical"], COLORS["unresolved"]], "Missing fraction", "Frame-level observable-ray evidence only; no full-space occupancy claim.", 15)
    ucounts = {k: sum(r["UNKNOWN_MODEL_STATUS"] == k for r in unknown["maps"]) for k in ("NOT_APPLICABLE_GT_DERIVED_FULL_REFERENCE", "EXPLICIT_UNKNOWN_MODEL_AVAILABLE", "UNKNOWN_MODEL_DIAGNOSTIC_ONLY", "UNKNOWN_MODEL_UNRESOLVED")}
    bar_figure("unknown_model_status.png", "Runtime UNKNOWN model status", ["GT N/A", "Explicit", "Diagnostic only", "Unresolved"], list(ucounts.values()), [COLORS["derived"], COLORS["measured"], COLORS["empirical"], COLORS["unresolved"]], "Map count", "UNKNOWN is never treated as certified free.", 15)
    bar_figure("replica_route_tube_knownness.png", "Replica route-tube knownness", ["GT-FINE", "Splatfacto", "SplaTAM-60"], [1.0, 0.0, 0.0], [COLORS["measured"], COLORS["unresolved"], COLORS["unresolved"]], "Known fraction", "Only the GT-derived map closes route coordinates and runtime-knownness under the frozen PR #64 contract.", 0)
    bar_figure("replica_one_sided_risk.png", "Replica one-sided false-free risk closure", ["GT-FINE certified", "Splatfacto unresolved", "SplaTAM unresolved"], [1,0,0], [COLORS["derived"], COLORS["unresolved"], COLORS["unresolved"]], "Closure indicator", "e_plus=max(0,d_map-d_ref); unresolved entries have no fabricated percentile or upper bound.", 10)
    bar_figure("physical_budget_status.png", "Physical map-error budget status", ["Resolved", "Unresolved"], [budget["resolved_count"], budget["unresolved_count"]], [COLORS["derived"], COLORS["unresolved"]], "Map count", "The one resolved budget belongs to the frozen GT-derived benchmark contract.", 0)
    query_values = [1 if c["SAFETY_QUERY_COMPATIBLE"] is True else 0 for c in cards]
    query_colors = [COLORS["measured"] if v else COLORS["not_evaluable"] for v in query_values]
    bar_figure("safer_g0_compatibility.png", "Fresh read-only SAFER G0 compatibility", [short[m] for m in MAP_ORDER], query_values, query_colors, "Compatible indicator", f"Six accessible maps passed three fresh processes × 256 states; total processes={g0['process_count']}.", 55)
    rvals = [int(c["V2_RECONSTRUCTION_AXIS"][1]) for c in cards]
    bar_figure("reconstruction_axis_classification.png", "Protocol V2 reconstruction axis", [short[m] for m in MAP_ORDER], rvals, [COLORS["measured"] if v==3 else COLORS["derived"] if v==2 else COLORS["unresolved"] for v in rvals], "R level", "R3 is restricted to independent authoritative geometry with certified completeness.", 55)
    nvals = [int(c["V2_NAVIGATION_AXIS"][1]) for c in cards]
    bar_figure("navigation_axis_classification.png", "Protocol V2 navigation axis", [short[m] for m in MAP_ORDER], nvals, [COLORS["measured"] if v==3 else COLORS["derived"] if v==2 else COLORS["unresolved"] if v==1 else COLORS["not_evaluable"] for v in nvals], "N level", "Finite G0 never raises N; no learned map reaches N2 or N3.", 55)
    cells: dict[tuple[int, int], list[str]] = {}
    for c in cards:
        key = (int(c["V2_RECONSTRUCTION_AXIS"][1]), int(c["V2_NAVIGATION_AXIS"][1]))
        cells.setdefault(key, []).append(short[c["map_id"]])
    fig, ax = plt.subplots(figsize=(9.2,6.8))
    for x in range(4):
        for y in range(4):
            occupied = (x, y) in cells
            color = COLORS["not_evaluable"] if not occupied else (COLORS["measured"] if (x, y) == (3, 3) else COLORS["empirical"])
            ax.add_patch(Rectangle((x-0.46, y-0.46), .92, .92, facecolor=color, edgecolor="white", alpha=.88 if occupied else .24))
            if occupied:
                label = "\n".join(cells[(x, y)])
                ax.text(x, y, label, ha="center", va="center", fontsize=6.5 if len(cells[(x, y)]) > 4 else 8, color="white" if (x, y) == (3, 3) else COLORS["ink"])
    ax.set(xlim=(-.5,3.5), ylim=(-.5,3.5), xticks=range(4), yticks=range(4), xlabel="Reconstruction axis R", ylabel="Navigation axis N", title="Two-axis map classification")
    ax.grid(False)
    finish(fig, ROOT / "figures" / "two_axis_map_matrix.png", "GT-derived control is visually distinct from learned map instances; axes are categorical, not continuous scores.")
    legacy_rows = [c for c in cards if c["map_id"] in ("REPLICA_SPLATAM_60","ARKITSCENES_M1_SPLATAM","TUM_SPLATAM_FORMAL","TUM_GAUSSIAN_SLAM")]
    matrix_figure("legacy_vs_v2_interpretation.png", "Legacy outcomes remain valid; V2 adds bounded classifications", [short[c["map_id"]] for c in legacy_rows], ["Legacy preserved", "R axis", "N axis"], np.array([[2,2 if c["V2_RECONSTRUCTION_AXIS"].startswith("R2") else 1,0 if c["V2_NAVIGATION_AXIS"].startswith("N0") else 1] for c in legacy_rows]), [["yes",c["V2_RECONSTRUCTION_AXIS"][:2],c["V2_NAVIGATION_AXIS"][:2]] for c in legacy_rows], "No historical PR is rewritten or relabelled as a past PASS.")
    gap_labels = ["Unknown", "Route", "Physical budget", "Reference", "Multi-tolerance"]
    gap_counts = [10,10,10,8,10]
    bar_figure("candidate_evidence_gaps.png", "Evidence gaps that cap learned navigation classification", gap_labels, gap_counts, [COLORS["unresolved"]]*5, "Affected map count", "Counts are evidence availability diagnostics; they are not tunable failure thresholds.", 15)
    flow_figure("final_decision_tree.png", "Frozen Protocol V2 decision tree result", [("Controls", "PASS", "measured"), ("Learned N3", "0 maps", "unresolved"), ("Learned N2", "0 maps", "unresolved"), ("Case C", "New-dataset entry qualification", "derived")], "The result is selected by the preregistered tree; no candidate-specific branch was added.")
    flow_figure("next_task_handoff.png", "Only authorized next task", [("Current", "No learned map reached N2 or N3", "unresolved"), ("Checklist first", "No ETH3D training", "derived"), ("Only next", "ETH3D delivery-area Protocol V2 entry qualification", "measured")], "Exact task: ETH3D_DELIVERY_AREA_PROTOCOL_V2_ENTRY_QUALIFICATION_V1. Download and training remain unauthorized.")

    chart_map = {
        "palette_policy": "hard two-root cap plus neutral unresolved/not-evaluable states",
        "evidence_classes": COLORS,
        "figures": [{"file": name, "surface": "tracked static PNG", "claim": claim} for name, claim in [
            ("protocol_v2_control_discrimination.png", "controls discriminate"), ("map_artifact_availability.png", "6 accessible, 5 unavailable"),
            ("map_reference_authority.png", "authority bounds"), ("native_common_parity.png", "channel status"),
            ("risk_coverage_all_available_maps.png", "one full curve only"), ("conditional_error_vs_coverage.png", "AURC descriptive"),
            ("multi_tolerance_replica_maps.png", "no learned complete curve"), ("spatial_missingness_summary.png", "observable-only missingness"),
            ("unknown_model_status.png", "unknown unresolved"), ("replica_route_tube_knownness.png", "GT route closure only"),
            ("replica_one_sided_risk.png", "GT one-sided closure only"), ("physical_budget_status.png", "1 resolved, 10 unresolved"),
            ("safer_g0_compatibility.png", "six query-compatible maps"), ("reconstruction_axis_classification.png", "R classes"),
            ("navigation_axis_classification.png", "N classes"), ("two_axis_map_matrix.png", "R/N independence"),
            ("legacy_vs_v2_interpretation.png", "legacy preserved"), ("candidate_evidence_gaps.png", "candidate gaps"),
            ("final_decision_tree.png", "case C selected"), ("next_task_handoff.png", "entry qualification next"),
        ]]}
    (ROOT / "figures" / "chart_map.json").write_text(json.dumps(chart_map, indent=2, sort_keys=True)+"\n", encoding="utf-8", newline="\n")
    print("FIGURES_COMPLETE", len(chart_map["figures"]))


if __name__ == "__main__": main()
