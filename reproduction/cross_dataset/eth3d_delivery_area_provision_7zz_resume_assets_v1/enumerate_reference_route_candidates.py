#!/usr/bin/env python3
"""Enumerate deterministic route candidates from the frozen reference PRM."""

from __future__ import annotations

import hashlib
import heapq
import json
import math
from collections import defaultdict
from pathlib import Path

import numpy as np
import trimesh

from build_reference_prm import group_images, ideal_support, load_mesh, make_scene
from colmap_text import camera_center, read_cameras, read_images
from reference_route_geometry import certified_segment_mesh_clearance
from task_config import QUARANTINE, TASK_ROOT


SEED = 20260804
ROBOT_RADIUS = 0.10
NONMAP_RESERVE = 0.23526279441628825
MAX_CANDIDATES = 320


def dijkstra(adjacency, source):
    distance = {source: 0.0}
    previous = {}
    queue = [(0.0, source)]
    while queue:
        current, node = heapq.heappop(queue)
        if current != distance.get(node):
            continue
        for neighbor, weight in adjacency[node]:
            proposal = current + weight
            if proposal < distance.get(neighbor, math.inf):
                distance[neighbor], previous[neighbor] = proposal, node
                heapq.heappush(queue, (proposal, neighbor))
    return distance, previous


def path_to(previous, source, target):
    if target == source:
        return [source]
    if target not in previous:
        return None
    path = [target]
    while path[-1] != source:
        path.append(previous[path[-1]])
    return list(reversed(path))


def turning_segments(points) -> int:
    count = 0
    for index in range(1, len(points) - 1):
        first, second = points[index] - points[index - 1], points[index + 1] - points[index]
        denominator = np.linalg.norm(first) * np.linalg.norm(second)
        if denominator <= 1e-12:
            continue
        angle = math.degrees(math.acos(max(-1.0, min(1.0, float(np.dot(first, second) / denominator)))))
        count += int(angle >= 1.0)
    return count


def edge_samples(a, b, spacing=0.05):
    distance = float(np.linalg.norm(b - a))
    count = max(1, int(math.ceil(distance / spacing)))
    return [a + (b - a) * (index / count) for index in range(count + 1)]


def main() -> None:
    graph = json.loads((TASK_ROOT / "routes" / "reference_prm_graph_full.json").read_text(encoding="utf-8"))
    nodes = {row["id"]: row for row in graph["nodes"]}
    edge_by_pair = {}
    adjacency = defaultdict(list)
    for edge in graph["edges"]:
        pair = tuple(sorted((edge["a"], edge["b"])))
        edge_by_pair[pair] = edge
        adjacency[edge["a"]].append((edge["b"], edge["planning_cost"]))
        adjacency[edge["b"]].append((edge["a"], edge["planning_cost"]))
    model = QUARANTINE / "delivery_area_rig_undistorted" / "delivery_area" / "rig_calibration_undistorted"
    cameras, images = read_cameras(model / "cameras.txt"), read_images(model / "images.txt")
    groups = group_images(images)
    split = json.loads((TASK_ROOT / "split" / "pose_block_split_v1.json").read_text(encoding="utf-8"))
    train_groups = {group: groups[group] for group in split["TRAIN"]}
    group_centers = {group: np.mean([camera_center(image) for image in value], axis=0) for group, value in groups.items()}
    mesh = load_mesh(QUARANTINE / "delivery_area_rig_occlusion" / "delivery_area" / "occlusion" / "surface_mesh.ply")
    scene = make_scene(mesh)
    node_ids = sorted(nodes)
    pair_order = sorted(((hashlib.sha256(f"{SEED}:{first}:{second}".encode("ascii")).hexdigest(), first, second)
                         for pos, first in enumerate(node_ids) for second in node_ids[pos + 1:]))
    dijkstra_cache = {}
    edge_known_cache = {}
    candidates = []
    blocked_count = 0
    for pair_hash, start, goal in pair_order:
        if len(candidates) >= MAX_CANDIDATES and blocked_count >= 100:
            break
        if start not in dijkstra_cache:
            dijkstra_cache[start] = dijkstra(adjacency, start)
        distances, previous = dijkstra_cache[start]
        path = path_to(previous, start, goal)
        if not path or len(path) < 4:
            continue
        points = np.asarray([nodes[node]["point_m"] for node in path], dtype=np.float64)
        turns = turning_segments(points)
        if turns < 2:
            continue
        edge_clearances, known = [], True
        for first, second in zip(path[:-1], path[1:]):
            pair = tuple(sorted((first, second)))
            edge = edge_by_pair[pair]
            edge_clearances.append(edge["certified_reference_clearance_lower_bound_m"])
            if pair not in edge_known_cache:
                samples = edge_samples(np.asarray(nodes[first]["point_m"]), np.asarray(nodes[second]["point_m"]))
                edge_known_cache[pair] = all(ideal_support(point, train_groups, group_centers, cameras, scene)["primary"]
                                                   for point in samples)
            if not edge_known_cache[pair]:
                known = False
                break
        if not known:
            continue
        min_clearance = float(min(edge_clearances))
        b_map = min_clearance - NONMAP_RESERVE
        if b_map <= 0:
            continue
        direct_clearance, direct_clearance_capped = certified_segment_mesh_clearance(
            mesh, points[0], points[-1], ROBOT_RADIUS)
        blocked = not direct_clearance_capped and direct_clearance <= ROBOT_RADIUS
        blocked_count += int(blocked)
        candidates.append({
            "pair_hash": pair_hash, "start_node": start, "goal_node": goal,
            "node_ids": path, "points_m": points.tolist(), "path_node_count": len(path),
            "path_length_m": float(sum(edge_by_pair[tuple(sorted((first, second)))]["length_m"]
                                       for first, second in zip(path[:-1], path[1:]))),
            "planning_cost": float(distances[goal]),
            "planning_cost_contract": "edge_length_plus_inverse_reference_residual_budget",
            "turning_segment_count": turns,
            "minimum_reference_center_clearance_m": min_clearance,
            "B_map_available_m": b_map, "direct_segment_clearance_m": direct_clearance,
            "path_clearance_is_certified_lower_bound": True,
            "direct_segment_clearance_is_conservative_lower_bound": direct_clearance_capped,
            "direct_segment_clearance_certification_cap_m": ROBOT_RADIUS,
            "blocked_straight_line": blocked, "ideal_unknown_primary_route_tube_support": True,
            "candidate_map_access": False,
        })
    payload = {"status": "PASS" if len(candidates) >= 30 else "FAIL", "candidate_count": len(candidates),
               "blocked_candidate_count": blocked_count, "candidates": candidates}
    if payload["status"] != "PASS":
        raise RuntimeError(f"INSUFFICIENT_ROUTE_CANDIDATES {len(candidates)}")
    (TASK_ROOT / "routes" / "reference_route_candidates_full.json").write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print("PASS_ROUTE_CANDIDATES", len(candidates), blocked_count)


if __name__ == "__main__":
    main()
