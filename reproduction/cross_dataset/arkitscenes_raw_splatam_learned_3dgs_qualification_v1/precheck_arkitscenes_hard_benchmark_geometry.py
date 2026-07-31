#!/usr/bin/env python3
"""Read-only, deterministic future-benchmark existence precheck on official mesh."""
from __future__ import annotations

import argparse
import csv
import hashlib
import heapq
import math
from pathlib import Path

import numpy as np
import trimesh
from PIL import Image

from arkitscenes_common import atomic_json, sha256_file


VOXEL_M = 0.05
ROBOT_RADIUS_M = 0.10
EPSILON_BASE_M = 0.01
V_MAX_MPS = 0.10
U_MAX_MPS2 = 0.10
FREE_CLEARANCE_M = ROBOT_RADIUS_M + EPSILON_BASE_M
BRAKING_DISTANCE_M = V_MAX_MPS ** 2 / (2.0 * U_MAX_MPS2)
SEED = 20260730


def matrix(row: dict[str, str]) -> np.ndarray:
    return np.asarray([[float(row[f"c2w_{i}{j}"]) for j in range(4)] for i in range(4)])


def key(point: np.ndarray) -> tuple[int, int, int]:
    return tuple(np.rint(point / VOXEL_M).astype(int).tolist())


def point(cell: tuple[int, int, int]) -> np.ndarray:
    return np.asarray(cell, dtype=np.float64) * VOXEL_M


def line_cells(a: np.ndarray, b: np.ndarray, spacing: float = VOXEL_M) -> list[tuple[int, int, int]]:
    count = max(2, int(math.ceil(float(np.linalg.norm(b - a)) / spacing)) + 1)
    return [key(a * (1.0 - t) + b * t) for t in np.linspace(0.0, 1.0, count)]


def distances(mesh: trimesh.Trimesh, values: np.ndarray) -> np.ndarray:
    output: list[np.ndarray] = []
    for chunk in np.array_split(values, max(1, math.ceil(len(values) / 2048))):
        if len(chunk):
            _, result, _ = trimesh.proximity.closest_point(mesh, chunk)
            output.append(np.asarray(result, dtype=np.float64))
    return np.concatenate(output) if output else np.empty(0)


def swept_blocked(mesh: trimesh.Trimesh, a: np.ndarray, b: np.ndarray) -> bool:
    cells = line_cells(a, b, spacing=VOXEL_M / 2.0)
    return bool(np.any(distances(mesh, np.asarray([point(cell) for cell in cells])) < ROBOT_RADIUS_M))


def line_is_free(mesh: trimesh.Trimesh, a: np.ndarray, b: np.ndarray) -> bool:
    cells = line_cells(a, b, spacing=VOXEL_M / 2.0)
    return bool(np.all(distances(mesh, np.asarray([point(cell) for cell in cells])) >= FREE_CLEARANCE_M))


def astar(free: set[tuple[int, int, int]], start: tuple[int, int, int], goal: tuple[int, int, int]) -> list[tuple[int, int, int]] | None:
    if start not in free or goal not in free:
        return None
    queue: list[tuple[float, int, tuple[int, int, int]]] = [(0.0, 0, start)]
    came: dict[tuple[int, int, int], tuple[int, int, int]] = {}
    score = {start: 0.0}
    visited = 0
    while queue and visited < 100000:
        _, _, current = heapq.heappop(queue)
        visited += 1
        if current == goal:
            path = [current]
            while current in came:
                current = came[current]
                path.append(current)
            return list(reversed(path))
        for delta in ((1, 0, 0), (-1, 0, 0), (0, 1, 0), (0, -1, 0), (0, 0, 1), (0, 0, -1)):
            neighbor = (current[0] + delta[0], current[1] + delta[1], current[2] + delta[2])
            if neighbor not in free:
                continue
            candidate = score[current] + 1.0
            if candidate >= score.get(neighbor, float("inf")):
                continue
            came[neighbor] = current
            score[neighbor] = candidate
            heuristic = float(np.linalg.norm(np.asarray(neighbor) - np.asarray(goal)))
            heapq.heappush(queue, (candidate + heuristic, visited, neighbor))
    return None


def turns(path: list[tuple[int, int, int]]) -> int:
    directions = [tuple(np.asarray(b) - np.asarray(a)) for a, b in zip(path, path[1:])]
    return sum(current != previous for previous, current in zip(directions, directions[1:]))


def sample_visible_free(mesh: trimesh.Trimesh, rows: list[dict[str, str]], root: Path) -> tuple[set[tuple[int, int, int]], list[tuple[int, int, int]]]:
    free: set[tuple[int, int, int]] = set()
    trajectory: list[tuple[int, int, int]] = []
    selected = [rows[index] for index in np.linspace(0, len(rows) - 1, 64, dtype=int)]
    centers = [matrix(row)[:3, 3] for row in rows]
    center_clearances = distances(mesh, np.asarray(centers))
    for center, clearance in zip(centers, center_clearances):
        if clearance >= FREE_CLEARANCE_M:
            trajectory.append(key(center))
    for first, second in zip(rows, rows[1:]):
        a, b = matrix(first)[:3, 3], matrix(second)[:3, 3]
        if line_is_free(mesh, a, b):
            free.update(line_cells(a, b))
    for row in selected:
        transform = matrix(row)
        center = transform[:3, 3]
        depth = np.asarray(Image.open(root / row["depth"]), dtype=np.float64) * 0.001
        confidence = np.asarray(Image.open(root / row["confidence"]), dtype=np.uint8)
        y, x = np.nonzero((depth > FREE_CLEARANCE_M) & (confidence == 2))
        for u, v in zip(x[::16], y[::16]):
            z = depth[v, u]
            surface_camera = np.asarray([(u - float(row["cx"])) * z / float(row["fx"]),
                                         (v - float(row["cy"])) * z / float(row["fy"]), z, 1.0])
            surface_world = (transform @ surface_camera)[:3]
            stop = center + (surface_world - center) * max(0.0, 1.0 - FREE_CLEARANCE_M / z)
            free.update(line_cells(center, stop))
    free.update(trajectory)
    return free, trajectory


def stable_pairs(cells: list[tuple[int, int, int]], limit: int) -> list[tuple[tuple[int, int, int], tuple[int, int, int]]]:
    ordered = sorted(cells, key=lambda item: hashlib.sha256(f"{SEED}:{item}".encode()).hexdigest())
    pairs: list[tuple[tuple[int, int, int], tuple[int, int, int]]] = []
    for index, start in enumerate(ordered):
        for offset in (17, 43, 89, 157, 251):
            if len(ordered) <= offset:
                continue
            end = ordered[(index + offset) % len(ordered)]
            if start != end:
                pairs.append((start, end))
                if len(pairs) >= limit:
                    return pairs
    return pairs


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--task-root", type=Path, required=True)
    parser.add_argument("--candidate-root", type=Path, required=True)
    parser.add_argument("--video-id", required=True)
    args = parser.parse_args()
    task, root = args.task_root.resolve(), args.candidate_root.resolve()
    with (task / "frame_join" / args.video_id / "arkitscenes_joined_frame_manifest.csv").open(newline="", encoding="utf-8") as handle:
        rows = list(csv.DictReader(handle))
    mesh_path = root / f"{args.video_id}_3dod_mesh.ply"
    mesh = trimesh.load(mesh_path, process=False, force="mesh")
    free, trajectory = sample_visible_free(mesh, rows, root)
    free_trajectory = [cell for cell in trajectory if cell in free]
    candidates = stable_pairs(free_trajectory, 3000)
    blocked_reachable: list[dict[str, object]] = []
    multiturn: list[dict[str, object]] = []
    for start, end in candidates:
        if len(blocked_reachable) >= 20 and len(multiturn) >= 10:
            break
        a, b = point(start), point(end)
        if not swept_blocked(mesh, a, b):
            continue
        route = astar(free, start, end)
        if route is None:
            continue
        record = {"start_voxel": start, "goal_voxel": end, "route_voxels": len(route), "turn_count": turns(route)}
        if len(blocked_reachable) < 20:
            blocked_reachable.append(record)
        if record["turn_count"] >= 2 and len(multiturn) < 10:
            route_clearance = distances(mesh, np.asarray([point(cell) for cell in route[::max(1, len(route)//128)]]))
            if len(route_clearance) and float(np.min(route_clearance)) <= 0.20:
                multiturn.append(record | {"route_min_mesh_clearance_m": float(np.min(route_clearance))})
    keys = sorted(free, key=lambda item: hashlib.sha256(f"states:{SEED}:{item}".encode()).hexdigest())[:12000]
    candidate_points = np.asarray([point(cell) for cell in keys])
    clearance = distances(mesh, candidate_points)
    braking = []
    stress = []
    for cell, value in zip(keys, clearance):
        margin = float(value) - FREE_CLEARANCE_M - BRAKING_DISTANCE_M
        if FREE_CLEARANCE_M < value < FREE_CLEARANCE_M + BRAKING_DISTANCE_M and len(braking) < 20:
            braking.append({"voxel": cell, "mesh_clearance_m": float(value), "braking_margin_m": margin})
        if FREE_CLEARANCE_M < value <= 0.20 and len(stress) < 20:
            stress.append({"voxel": cell, "mesh_clearance_m": float(value)})
    counts = {"blocked_straight_astar_reachable_pairs": len(blocked_reachable), "positive_clearance_braking_insufficient_states": len(braking),
              "near_obstacle_sampled_data_stress_states": len(stress), "multiturn_narrow_pairs": len(multiturn)}
    status = "HARD_BENCHMARK_GEOMETRY_PRECHECK_PASS" if (counts["blocked_straight_astar_reachable_pairs"] >= 20 and
                                                            counts["positive_clearance_braking_insufficient_states"] >= 20 and
                                                            counts["near_obstacle_sampled_data_stress_states"] >= 20 and
                                                            counts["multiturn_narrow_pairs"] >= 10) else "BLOCKED_BY_ARKITSCENES_SCENE_PRECHECK"
    result = {"status": status, "video_id": args.video_id, "voxel_m": VOXEL_M, "seed": SEED,
              "robot_contract": {"radius_m": ROBOT_RADIUS_M, "epsilon_base_m": EPSILON_BASE_M, "dt_s": 0.05, "vmax_componentwise_mps": V_MAX_MPS, "umax_componentwise_mps2": U_MAX_MPS2},
              "observable_area_contract": "free voxels are only camera-trajectory cells and depth-visible ray cells ending before official mesh depth", "mesh_sha256": sha256_file(mesh_path),
              "free_voxel_count": len(free), "candidate_pair_count": len(candidates), "counts": counts,
              "blocked_straight_astar_reachable_pairs": blocked_reachable, "braking_insufficient_states": braking,
              "sampled_data_stress_states": stress, "multiturn_narrow_pairs": multiturn,
              "controller_benchmark_count": 0}
    atomic_json(task / "candidate_precheck" / args.video_id / "future_hard_benchmark_precheck.json", result)
    print(status, counts)
    return 0 if status == "HARD_BENCHMARK_GEOMETRY_PRECHECK_PASS" else 2


if __name__ == "__main__":
    raise SystemExit(main())
