#!/usr/bin/env python3
"""Build the frozen, method-independent ETH3D stress scenario registry."""

from __future__ import annotations

import argparse
import hashlib
import json
from collections import defaultdict
from pathlib import Path

import numpy as np

from eth3d_controller_core import (CANDIDATE_BUDGET, DT, MAX_STEPS,
                                   LearnedEllipsoidMap, atomic_json,
                                   nominal_control, sha256_json)


SEED = 20260804
GROUPS = ("G0_SAFE_CONTROL", "G1_START_SAFE_BOUNDARY", "G2_FEASIBILITY_DENSE",
          "G3_SAMPLED_DATA_GAP", "G4_PREDICTIVE_RECOVERY")


def normalized(value: np.ndarray) -> np.ndarray:
    norm = float(np.linalg.norm(value))
    return value / norm if norm > 1e-12 else np.asarray([1.0, 0.0, 0.0])


def choose_goal(node_id: int, start: np.ndarray, direction: np.ndarray,
                nodes: dict[int, dict], adjacency: dict[int, list[int]]) -> np.ndarray:
    choices = adjacency[node_id]
    if not choices:
        raise RuntimeError(f"node {node_id} has no frozen graph neighbor")
    direction = normalized(direction)
    scored = []
    for other in choices:
        point = np.asarray(nodes[other]["point_m"], dtype=np.float64)
        vector = point - start
        score = float(normalized(vector) @ direction)
        scored.append((-score, -float(np.linalg.norm(vector)), other, point))
    return min(scored, key=lambda row: row[:3])[3]


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--canonical-root", type=Path, required=True)
    parser.add_argument("--source-root", type=Path, required=True)
    parser.add_argument("--controller-snapshot", type=Path, required=True)
    parser.add_argument("--prm-graph", type=Path, required=True)
    parser.add_argument("--output-dir", type=Path, required=True)
    args = parser.parse_args()
    args.output_dir.mkdir(parents=True, exist_ok=True)
    graph = json.loads(args.prm_graph.read_text(encoding="utf-8"))
    nodes = {int(row["id"]): row for row in graph["nodes"]}
    adjacency: dict[int, list[int]] = defaultdict(list)
    for edge in graph["edges"]:
        adjacency[int(edge["a"])].append(int(edge["b"]))
        adjacency[int(edge["b"])].append(int(edge["a"]))
    learned = LearnedEllipsoidMap(args.canonical_root, args.source_root,
                                  args.controller_snapshot)
    diagnostics = []
    query_cache: dict[int, dict] = {}
    for node_id in sorted(nodes):
        point = np.asarray(nodes[node_id]["point_m"], dtype=np.float64)
        query = learned.query(point)
        finite = bool(np.all(query["finite"]))
        if not finite:
            continue
        h = query["h"]; gradient = query["grad"]
        active = h <= 0.02
        active_grad = gradient[active]
        if len(active_grad) >= 3:
            unit = active_grad / np.maximum(np.linalg.norm(active_grad, axis=1, keepdims=True), 1e-12)
            singular = np.linalg.svd(unit, compute_uv=False)
            directional_rank = int(np.sum(singular > 1e-3))
            directional_balance = float(singular[-1] / max(singular[0], 1e-12))
        else:
            directional_rank, directional_balance = len(active_grad), 0.0
        minimum_index = int(np.argmin(h))
        diagnostics.append({
            "node_id": node_id, "point_m": point.tolist(),
            "min_map_h": float(h[minimum_index]),
            "min_candidate_id": int(query["candidate_ids"][minimum_index]),
            "nearest_obstacle_direction": normalized(-gradient[minimum_index]).tolist(),
            "near_active_count": int(np.sum(active)),
            "forced_candidate_count": int(np.sum(h <= 0.005)),
            "directional_rank": directional_rank,
            "directional_balance": directional_balance,
            "reference_clearance_m": float(nodes[node_id]["reference_clearance_m"]),
            "unknown_support_group_count": int(nodes[node_id]["ideal_support"]["support_group_count"]),
            "unknown_primary": bool(nodes[node_id]["ideal_support"]["primary"]),
            "query_finite": finite,
        })
        query_cache[node_id] = query
    if len(diagnostics) < 70:
        raise RuntimeError("fewer than 70 finite-query PRM nodes")
    by_id = {row["node_id"]: row for row in diagnostics}
    selected: dict[str, list[dict]] = {group: [] for group in GROUPS}

    def take(group: str, ordered: list[dict], count: int = 20) -> None:
        group_used = {row["node_id"] for row in selected[group]}
        for row in ordered:
            if row["node_id"] in group_used or not adjacency[row["node_id"]]:
                continue
            selected[group].append(row); group_used.add(row["node_id"])
            if len(selected[group]) == count:
                break

    g0 = [row for row in diagnostics if row["min_map_h"] >= 0.01 and row["unknown_primary"]]
    take("G0_SAFE_CONTROL", sorted(g0, key=lambda row: (-row["min_map_h"], row["node_id"])))

    unsafe = [row for row in diagnostics if row["min_map_h"] < 0.0]
    near = [row for row in diagnostics if row["min_map_h"] >= 0.0]
    take("G1_START_SAFE_BOUNDARY", sorted(unsafe, key=lambda row: (abs(row["min_map_h"]), row["node_id"])), 10)
    remaining = 20 - len(selected["G1_START_SAFE_BOUNDARY"])
    if remaining:
        for row in sorted(near, key=lambda item: (abs(item["min_map_h"]), item["node_id"])):
            if row["node_id"] in {item["node_id"] for item in selected["G1_START_SAFE_BOUNDARY"]} or not adjacency[row["node_id"]]: continue
            selected["G1_START_SAFE_BOUNDARY"].append(row)
            if len(selected["G1_START_SAFE_BOUNDARY"]) == 20: break

    dense = sorted(diagnostics, key=lambda row: (-row["near_active_count"],
                                                   -row["directional_rank"],
                                                   -row["directional_balance"], row["node_id"]))
    take("G2_FEASIBILITY_DENSE", dense)

    gap_candidates = []
    for row in sorted(diagnostics, key=lambda item: (abs(item["min_map_h"]), item["node_id"]))[:160]:
        if row["min_map_h"] < 0.0 or not adjacency[row["node_id"]]: continue
        start = np.asarray(row["point_m"]); direction = np.asarray(row["nearest_obstacle_direction"])
        velocity = 0.10 * direction
        endpoint_h = learned.min_h(start + DT * velocity)
        if not np.isfinite(endpoint_h): continue
        candidate = dict(row); candidate["one_step_endpoint_h"] = endpoint_h
        candidate["sampled_gap_score"] = float(row["min_map_h"] - endpoint_h)
        gap_candidates.append(candidate)
    take("G3_SAMPLED_DATA_GAP", sorted(gap_candidates,
         key=lambda row: (-row["sampled_gap_score"], row["one_step_endpoint_h"], row["node_id"])))

    recovery_candidates = []
    for row in sorted(diagnostics, key=lambda item: (abs(item["min_map_h"]), item["node_id"]))[:220]:
        if row["min_map_h"] < 0.0 or not adjacency[row["node_id"]]: continue
        start = np.asarray(row["point_m"]); direction = np.asarray(row["nearest_obstacle_direction"])
        velocity = 0.075 * direction
        goal = choose_goal(row["node_id"], start, direction, nodes, adjacency)
        p, v = start.copy(), velocity.copy(); horizon_values = []
        for _ in range(3):
            u = nominal_control(p, v, goal)
            p, v = p + DT * v, v + DT * u
            horizon_values.append(learned.min_h(p))
        if not np.isfinite(horizon_values).all() or horizon_values[0] < 0.0: continue
        candidate = dict(row); candidate["nominal_horizon_h"] = [float(v) for v in horizon_values]
        candidate["predictive_drop_score"] = float(row["min_map_h"] - min(horizon_values))
        recovery_candidates.append(candidate)
    take("G4_PREDICTIVE_RECOVERY", sorted(recovery_candidates,
         key=lambda row: (-row["predictive_drop_score"], min(row["nominal_horizon_h"]), row["node_id"])))

    scenarios = []
    for group in GROUPS:
        for ordinal, row in enumerate(selected[group]):
            start = np.asarray(row["point_m"], dtype=np.float64)
            obstacle_direction = np.asarray(row["nearest_obstacle_direction"], dtype=np.float64)
            if group == "G0_SAFE_CONTROL": velocity = np.zeros(3); goal_direction = -obstacle_direction
            elif group == "G1_START_SAFE_BOUNDARY": velocity = 0.10 * obstacle_direction; goal_direction = obstacle_direction
            elif group == "G2_FEASIBILITY_DENSE": velocity = np.zeros(3); goal_direction = obstacle_direction
            elif group == "G3_SAMPLED_DATA_GAP": velocity = 0.10 * obstacle_direction; goal_direction = obstacle_direction
            else: velocity = 0.075 * obstacle_direction; goal_direction = obstacle_direction
            goal = choose_goal(row["node_id"], start, goal_direction, nodes, adjacency)
            scenario_id = f"{group[:2]}_{ordinal:02d}_{row['node_id']:03d}"
            scenarios.append({
                "scenario_id": scenario_id, "group": group, "group_ordinal": ordinal,
                "source_node_id": row["node_id"], "start_m": start.tolist(),
                "goal_m": goal.tolist(), "initial_velocity_mps": velocity.tolist(),
                "seed": int.from_bytes(hashlib.sha256(f"{SEED}:{scenario_id}".encode()).digest()[:8], "big"),
                "dt": DT, "max_steps": MAX_STEPS, "candidate_budget": CANDIDATE_BUDGET,
                "generation_diagnostics": row,
                "reference_used_for_generation_only": True,
                "controller_rollout_metric_read_count": 0,
            })
    registry_core = {
        "schema_version": 1, "id": "ETH3D_FAS_CBF_STRESS_SCENARIO_REGISTRY_V1",
        "seed": SEED, "method_independent": True, "scenarios": scenarios,
        "group_counts": {group: sum(row["group"] == group for row in scenarios) for group in GROUPS},
        "source_prm_graph_sha256": hashlib.sha256(args.prm_graph.read_bytes()).hexdigest(),
        "map_query_candidate_budget": CANDIDATE_BUDGET,
        "controller_rollout_result_read_count": 0,
    }
    registry = dict(registry_core)
    registry["registry_sha256"] = sha256_json(registry_core)
    registry["status"] = ("PASS_FROZEN_100_SCENARIO_REGISTRY" if len(scenarios) == 100
                          else "SCENARIO_ACTIVATION_INSUFFICIENT")
    atomic_json(args.output_dir / "scenario_static_diagnostics.json", diagnostics)
    atomic_json(args.output_dir / "scenario_registry.json", registry)
    atomic_json(args.output_dir / "scenario_generation_summary.json", {
        "status": registry["status"], "scenario_count": len(scenarios),
        "group_counts": registry["group_counts"], "registry_sha256": registry["registry_sha256"],
        "finite_query_node_count": len(diagnostics), "map_mutation_count": 0,
        "reference_controller_input_count": 0, "rollout_result_read_count": 0,
    })
    print(json.dumps({"status": registry["status"], "count": len(scenarios),
                      "groups": registry["group_counts"],
                      "sha256": registry["registry_sha256"]}, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
