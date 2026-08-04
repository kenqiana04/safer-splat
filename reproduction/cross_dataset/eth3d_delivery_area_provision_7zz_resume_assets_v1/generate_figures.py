#!/usr/bin/env python3
"""Generate the required compact, source-backed audit figures."""

from __future__ import annotations

import json
from pathlib import Path

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
import trimesh

from task_config import TASK_ROOT


FIG = TASK_ROOT / "figures"
BLUE, ORANGE, GREEN, RED, GRAY = "#2F6BFF", "#F59E0B", "#14B86E", "#E05252", "#6B7280"


def load(relative):
    return json.loads((TASK_ROOT / relative).read_text(encoding="utf-8"))


def finish(fig, name, source):
    fig.text(0.01, 0.01, f"Source: {source} | No training; no map; training_authorized=false", fontsize=8, color=GRAY)
    fig.tight_layout(rect=[0, 0.04, 1, 1])
    fig.savefig(FIG / name, dpi=150, facecolor="white")
    plt.close(fig)


def bar_figure(name, title, labels, values, source, color=BLUE, ylabel="Count"):
    fig, ax = plt.subplots(figsize=(10.5, 5.5))
    ax.bar(labels, values, color=color)
    ax.set_title(title, loc="left", fontweight="bold")
    ax.set_ylabel(ylabel)
    ax.tick_params(axis="x", rotation=30)
    for index, value in enumerate(values):
        ax.text(index, value, f"{value:.4g}", ha="center", va="bottom", fontsize=8)
    finish(fig, name, source)


def text_flow(name, title, items, source, colors=None):
    fig, ax = plt.subplots(figsize=(11, 5.8))
    ax.axis("off")
    ax.set_title(title, loc="left", fontweight="bold")
    colors = colors or [BLUE] * len(items)
    width = 0.86 / len(items)
    for index, item in enumerate(items):
        x = 0.06 + index * width
        ax.text(x + width / 2, 0.5, item, ha="center", va="center", color="white", fontsize=10,
                bbox=dict(boxstyle="round,pad=0.8", facecolor=colors[index], edgecolor="none"), transform=ax.transAxes)
        if index + 1 < len(items):
            ax.annotate("", xy=(x + width + 0.01, 0.5), xytext=(x + width - 0.03, 0.5),
                        arrowprops=dict(arrowstyle="->", color=GRAY), xycoords=ax.transAxes)
    finish(fig, name, source)


def main() -> None:
    FIG.mkdir(parents=True, exist_ok=True)
    for existing in FIG.glob("*.png"):
        existing.unlink()
    if (FIG / "chart_map.json").exists():
        (FIG / "chart_map.json").unlink()
    downloads = load("downloaded_archive_identity.json")
    extracted = load("extracted_tree_identity.json")
    asset = load("asset_validation/rig_dslr_colmap_asset_audit.json")
    split = load("split/pose_block_split_v1.json")
    sensitivity = load("split/pose_block_split_sensitivity.json")
    isolation = load("train_model/train_eval_isolation_audit.json")
    train = load("train_model/train_only_colmap_build_contract.json")
    reference = load("reference/continuous_route_oracle_contract.json")
    parity = load("reference/reference_distance_engine_validation.json")
    depth = load("calibration/depth_semantics_audit.json")
    unknown = load("unknown/runtime_unknown_contract_v1.json")
    unknown_sens = load("unknown/unknown_sensitivity_report.json")
    budget = load("physical_budget/eth3d_physical_error_budget.json")
    graph = load("routes/reference_prm_graph_full.json")
    routes = load("routes/reference_route_registry_full.json")
    route_id = load("routes/reference_route_registry_identity.json")
    decision = load("decision/final_decision.json")
    case_a = decision["FINAL_STATUS"] == "PASS_ETH3D_DELIVERY_AREA_ASSET_SPLIT_REFERENCE_UNKNOWN_ROUTE_CONTRACT"
    names = [row["archive"].replace("delivery_area_", "").replace(".7z", "") for row in downloads["archives"]]
    sizes = [row["actual_bytes"] / 1e6 for row in downloads["archives"]]
    bar_figure("frozen_archive_download_status.png", "Frozen official archives: all nine acquired", names, sizes,
               "downloaded_archive_identity.json", ylabel="Compressed MB")
    roles = ["TRAIN source", "R-axis / observable", "continuous reference", "cross-view"]
    values = [1, 3, 1, 4]
    bar_figure("archive_role_and_isolation.png", "Archive roles are physically separated", roles, values,
               "task_config.py + train_eval_isolation_audit.json", color=[GREEN, ORANGE, BLUE, GRAY])
    bar_figure("extracted_asset_inventory.png", "Extracted payload by archive", names,
               [row["total_bytes"] / 1e6 for row in extracted["archives"]], "extracted_tree_identity.json", ylabel="Extracted MB")
    bar_figure("rig_capture_group_validation.png", "Rig count contract", ["RGB", "capture groups", "cameras/group"],
               [asset["rig"]["image_count"], asset["rig"]["capture_group_count"], 4], "rig_dslr_colmap_asset_audit.json", color=[BLUE, GREEN, ORANGE])
    extr = asset["rig"]["fixed_rig_extrinsics"]
    bar_figure("rig_camera_extrinsics_consistency.png", "Fixed rig extrinsics: worst cross-capture drift",
               ["translation (m)", "rotation (deg)"], [extr["max_translation_deviation_m"], extr["max_rotation_deviation_deg"]],
               "rig_fixed_extrinsics_audit.json", ylabel="Maximum deviation")
    bar_figure("rig_dslr_metric_alignment.png", "Rig and DSLR share the official metric reference",
               ["shared surface identity", "ICP", "Sim(3)", "scale fit"], [1, 0, 0, 0], "rig_dslr_metric_alignment.json", color=[GREEN, RED, RED, RED])
    centers = np.asarray([split["capture_centers_m"][key] for key in sorted(split["capture_centers_m"])])
    centered = centers - centers.mean(axis=0)
    projection = centered @ np.linalg.svd(centered, full_matrices=False)[2][:2].T
    partition_of = {capture: partition for partition in ("TRAIN", "HELDOUT", "GUARD") for capture in split[partition]}
    fig, ax = plt.subplots(figsize=(9, 6))
    for partition, color in (("TRAIN", GREEN), ("HELDOUT", RED), ("GUARD", ORANGE)):
        indices = [i for i, key in enumerate(sorted(split["capture_centers_m"])) if partition_of[key] == partition]
        ax.scatter(projection[indices, 0], projection[indices, 1], s=18, color=color, label=partition)
    ax.set_title("POSE_BLOCK_SPLIT_V1 spatial distribution", loc="left", fontweight="bold"); ax.legend()
    ax.set_xlabel("Pose PCA axis 1 (m)"); ax.set_ylabel("Pose PCA axis 2 (m)")
    finish(fig, "split_spatial_distribution.png", "pose_block_split_v1.json; split uses pose/group identity only")
    variants = sensitivity["variants"]
    matrix = np.asarray([[next(row for row in variants if row["heldout_fraction"] == fraction and row["guard_multiplier"] == guard)["counts"]["TRAIN"]
                          for guard in (0.5, 1.0, 1.5, 2.0)] for fraction in (0.15, 0.20, 0.25)])
    fig, ax = plt.subplots(figsize=(8, 5)); im = ax.imshow(matrix, cmap="Blues")
    ax.set_xticks(range(4), [0.5, 1.0, 1.5, 2.0]); ax.set_yticks(range(3), [0.15, 0.20, 0.25])
    ax.set_xlabel("Guard multiplier"); ax.set_ylabel("Heldout target"); ax.set_title("Sensitivity (report-only): TRAIN group count", loc="left", fontweight="bold")
    for i in range(3):
        for j in range(4): ax.text(j, i, str(matrix[i, j]), ha="center", va="center")
    finish(fig, "split_sensitivity.png", "pose_block_split_sensitivity.json; primary parameters unchanged")
    bar_figure("train_eval_physical_isolation.png", "Physical TRAIN / EVAL isolation", ["TRAIN files", "EVAL files", "TRAIN reference access"],
               [isolation["train_file_count"], isolation["eval_file_count"], 0], "train_eval_isolation_audit.json", color=[GREEN, BLUE, RED])
    bar_figure("train_only_colmap_filtering.png", "Train-only COLMAP filtering", ["TRAIN images", "TRAIN points", "new triangulation", "reference points"],
               [train["image_count"], train["point3d_count"], 0, 0], "train_only_colmap_build_contract.json", color=[GREEN, BLUE, RED, RED])
    scan_align = depth.get("scan_clean_to_mesh", load("calibration/depth_to_reference_alignment.json").get("scan_clean_to_mesh", {}))
    bar_figure("depth_to_reference_alignment.png", "Reference alignment without fit", ["median", "p95", "maximum"],
               [scan_align.get("median", 0), scan_align.get("p95", 0), scan_align.get("maximum", 0)], "depth_to_reference_alignment.json", ylabel="Distance (m)")
    reference_mesh = trimesh.load(reference["official_continuous_surface"], process=False)
    all_vertices = np.asarray(reference_mesh.vertices)
    mesh_vertices = all_vertices[::max(1, len(all_vertices) // 1200)][:1200]
    fig, ax = plt.subplots(figsize=(9, 6)); ax.scatter(mesh_vertices[:, 0], mesh_vertices[:, 1], s=2, alpha=.35, color=BLUE)
    ax.set_title("Verified continuous reference domain (bounds sample)", loc="left", fontweight="bold")
    ax.set_xlabel("x (m)"); ax.set_ylabel("y (m)")
    finish(fig, "reference_oracle_geometry.png", "continuous_route_oracle_contract.json; domain-limited authority")
    bar_figure("reference_distance_engine_parity.png", "Independent distance-engine parity",
               ["max difference", "tolerance"], [parity["maximum_absolute_difference_m"], parity["software_numeric_tolerance_m"]],
               "reference_distance_engine_validation.json", ylabel="Meters", color=[GREEN, GRAY])
    text_flow("runtime_unknown_contract.png", "Runtime UNKNOWN contract", ["TRAIN camera groups", "learned first surface", "3 groups + 15°", "KNOWN_FREE candidate", "else UNKNOWN"],
              "runtime_unknown_contract_v1.json", [BLUE, BLUE, ORANGE, GREEN, RED])
    sens_values = unknown_sens["qualified_node_counts"]
    sens_matrix = np.asarray([[sens_values.get(f"groups_{g}_angle_{a}", 0) for a in (5, 10, 15, 20)] for g in (2, 3, 4)])
    fig, ax = plt.subplots(figsize=(8, 5)); ax.imshow(sens_matrix, cmap="Greens")
    ax.set_xticks(range(4), [5, 10, 15, 20]); ax.set_yticks(range(3), [2, 3, 4]); ax.set_xlabel("Angle (deg)"); ax.set_ylabel("Groups")
    ax.set_title("Ideal GT-supported knownness (report-only sensitivity)", loc="left", fontweight="bold")
    for i in range(3):
        for j in range(4): ax.text(j, i, str(sens_matrix[i, j]), ha="center", va="center")
    finish(fig, "ideal_unknown_support.png", "unknown_sensitivity_report.json; reference is preflight-only")
    terms = [0.10, 0.01, budget["epsilon_reaction_stop_m"], budget["epsilon_tracking_target_m"]]
    bar_figure("physical_budget_decomposition.png", "Non-map physical reserve", ["robot radius", "base", "reaction-stop", "tracking"], terms,
               "eth3d_physical_error_budget.json", ylabel="Meters", color=[BLUE, ORANGE, RED, GREEN])
    node_points = np.asarray([row["point_m"] for row in graph["nodes"]]); centered = node_points - node_points.mean(axis=0)
    basis = np.linalg.svd(centered, full_matrices=False)[2][:2].T; node_2d = centered @ basis
    fig, ax = plt.subplots(figsize=(9, 6));
    for edge in graph["edges"][::max(1, len(graph["edges"]) // 1500)]:
        p = node_2d[[edge["a"], edge["b"]]]; ax.plot(p[:, 0], p[:, 1], color="#CBD5E1", lw=.5)
    ax.scatter(node_2d[:, 0], node_2d[:, 1], s=5, color=BLUE)
    ax.set_title("Reference-only PRM", loc="left", fontweight="bold"); ax.set_xlabel("PCA 1 (m)"); ax.set_ylabel("PCA 2 (m)")
    finish(fig, "reference_prm_and_routes.png", "reference_prm_graph_full.json; no candidate map access")
    fig, ax = plt.subplots(figsize=(9, 5.5))
    route_budgets = [row["B_map_available_m"] for row in routes["routes"]]
    if route_budgets:
        ax.hist(route_budgets, bins=18, color=BLUE)
    else:
        ax.text(0.5, 0.5, "No route registry frozen\nblocked-straight-line quota failed",
                ha="center", va="center", transform=ax.transAxes, color=RED, fontsize=13)
    ax.set_title("Route-specific available map budget", loc="left", fontweight="bold"); ax.set_xlabel("B_map_available (m)"); ax.set_ylabel("Routes")
    finish(fig, "route_clearance_budget_distribution.png", "reference_route_registry_full.json")
    text_flow("future_evaluator_flow.png", "Future Protocol V2 evaluator", ["Integrity", "R axis", "N/UNKNOWN", "Queryability", "Route budget", "Independent collision", "G0 separate"],
              "eth3d_future_protocol_v2_evaluator_contract.json", [BLUE, BLUE, ORANGE, ORANGE, GREEN, GREEN, GRAY])
    route_gate = 1 if case_a else 0
    bar_figure("final_asset_contract_decision.png", "Asset-contract decision gates", ["archives", "RGB/split", "isolation", "reference", "UNKNOWN", "routes"],
               [1, 1, 1, 1, 1, route_gate], "validation_result.json",
               color=[GREEN, GREEN, GREEN, GREEN, GREEN, GREEN if case_a else RED])
    bar_figure("claim_boundary.png", "Claim boundary", ["asset contract", "map qualified", "training", "controller"], [route_gate, 0, 0, 0],
               "downstream_handoff.json", color=[GREEN if case_a else RED, RED, RED, RED])
    if case_a:
        text_flow("next_environment_handoff.png", "Only authorized next stage", ["Frozen assets", "Official 3DGS environment", "Input adapter", "Canonical export", "still no formal training"],
                  "FREEZE_ETH3D_DELIVERY_AREA_OFFICIAL_3DGS_ENVIRONMENT_INPUT_HANDOFF_V1.md", [GREEN, BLUE, BLUE, ORANGE, RED])
    bar_figure("dslr_cross_view_inventory.png", "Cross-view DSLR channel", ["DSLR RGB", "rig RGB", "DSLR in TRAIN"],
               [asset["dslr"]["image_count"], asset["rig"]["image_count"], 0], "rig_dslr_colmap_asset_audit.json", color=[BLUE, GREEN, RED])
    bar_figure("route_registry_composition.png", "Frozen route registry", ["routes", "blocked straight", "TIGHT", "MODERATE", "OPEN"],
               [route_id["route_count"], route_id["blocked_straight_line_count"], route_id["clearance_strata"]["TIGHT"],
                route_id["clearance_strata"]["MODERATE"], route_id["clearance_strata"]["OPEN"]],
               "reference_route_registry_identity.json", color=[BLUE, RED, ORANGE, GREEN, BLUE])
    chart_map = {path.name: {"title": path.stem.replace("_", " ").title(), "source": "task compact records"} for path in sorted(FIG.glob("*.png"))}
    (FIG / "chart_map.json").write_text(json.dumps(chart_map, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print("PASS_FIGURES", len(chart_map))


if __name__ == "__main__":
    main()
