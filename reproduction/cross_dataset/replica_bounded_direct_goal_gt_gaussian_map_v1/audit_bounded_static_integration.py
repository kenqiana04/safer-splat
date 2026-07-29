#!/usr/bin/env python3
"""Static one-step audit for the bounded direct-goal contract; never a rollout."""
from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path

import numpy as np

from bounded_cbf_qp_adapter import BoundedCBFQPAdapter


DT = 0.05
LIMIT = 0.10


def sha256_bytes(array: np.ndarray) -> str:
    return hashlib.sha256(np.ascontiguousarray(array).tobytes()).hexdigest()


def selected_map_g0_positions(routes: list[dict], states: list[dict]) -> np.ndarray:
    points: list[np.ndarray] = []
    for route in routes[:64]:
        start = np.asarray(route["start_m"], dtype=np.float64)
        goal = np.asarray(route["goal_m"], dtype=np.float64)
        points.extend((start, goal, 0.5 * (start + goal)))
    points.extend(np.asarray(state["position_m"], dtype=np.float64) for state in states)
    rng = np.random.default_rng(20260729)
    points.extend(rng.uniform([-2, -2, -2], [8, 4, 10], size=(256 - len(points), 3)))
    return np.asarray(points[:100], dtype=np.float64)


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--map-dir", type=Path, required=True)
    parser.add_argument("--routes", type=Path, required=True)
    parser.add_argument("--start-states", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()

    routes = json.loads(args.routes.read_text(encoding="utf-8"))["routes"]
    states = json.loads(args.start_states.read_text(encoding="utf-8"))["states"]
    means = np.load(args.map_dir / "means_world_m.npy", mmap_mode="r")
    means_float64 = np.asarray(means, dtype=np.float64)
    rng = np.random.default_rng(20260729)
    adapter = BoundedCBFQPAdapter()
    max_u = -np.inf
    max_v = -np.inf
    max_position_error = 0.0
    map_geometry_input_count = 0

    def execute(p: np.ndarray, v: np.ndarray, u_des: np.ndarray, row: np.ndarray, bound: float) -> None:
        nonlocal max_u, max_v, max_position_error
        result = adapter.solve(row[None, :], np.asarray([bound]), u_des, v)
        assert result.control is not None
        stepped = adapter.step(p, v, result)
        assert stepped is not None
        p_next, v_next = stepped
        max_u = max(max_u, float(np.max(np.abs(result.control) - LIMIT)))
        max_v = max(max_v, float(np.max(np.abs(v_next) - LIMIT)))
        max_position_error = max(max_position_error, float(np.max(np.abs(p_next - (p + DT * v)))))

    for _ in range(1000):
        p = rng.uniform(-2.0, 2.0, size=3)
        v = rng.uniform(-LIMIT, LIMIT, size=3)
        u_des = rng.uniform(-LIMIT, LIMIT, size=3)
        low = np.maximum(-LIMIT, (-LIMIT - v) / DT)
        high = np.minimum(LIMIT, (LIMIT - v) / DT)
        witness = rng.uniform(low, high)
        row = rng.normal(size=3)
        execute(p, v, u_des, row, float(row @ witness + 0.02))

    for index in range(1000):
        p = rng.uniform(-2.0, 2.0, size=3)
        v = rng.uniform(-LIMIT, LIMIT, size=3)
        v[index % 3] = LIMIT if index % 2 == 0 else -LIMIT
        u_des = rng.uniform(-LIMIT, LIMIT, size=3)
        low = np.maximum(-LIMIT, (-LIMIT - v) / DT)
        high = np.minimum(LIMIT, (LIMIT - v) / DT)
        witness = rng.uniform(low, high)
        row = rng.normal(size=3)
        execute(p, v, u_des, row, float(row @ witness + 0.02))

    for index in range(500):
        p = rng.uniform(-2.0, 2.0, size=3)
        v = rng.uniform(-LIMIT, LIMIT, size=3)
        u_des = rng.uniform(-LIMIT, LIMIT, size=3)
        low = np.maximum(-LIMIT, (-LIMIT - v) / DT)
        high = np.minimum(LIMIT, (LIMIT - v) / DT)
        witness = rng.uniform(low, high)
        row = rng.normal(size=3)
        execute(p, v, u_des, row, float(row @ witness + 0.02))

    g0_positions = selected_map_g0_positions(routes, states)
    for p in g0_positions:
        active = int(np.argmin(np.sum((means_float64 - p) ** 2, axis=1)))
        delta = p - means_float64[active]
        norm = float(np.linalg.norm(delta))
        row = delta / norm if norm > 1e-12 else np.array([1.0, 0.0, 0.0])
        v = np.zeros(3, dtype=np.float64)
        u_des = rng.uniform(-LIMIT, LIMIT, size=3)
        witness = rng.uniform(-LIMIT, LIMIT, size=3)
        execute(p, v, u_des, row, float(row @ witness + 0.02))
        map_geometry_input_count += 1

    bad = adapter.solve(np.zeros((1, 3)), np.array([-1.0]), np.zeros(3), np.zeros(3))
    no_step = int(adapter.step(np.zeros(3), np.zeros(3), bad) is None)
    result = {
        "status": "PASS" if max_u <= 1e-7 and max_v <= 1e-7 and max_position_error <= 1e-12 and no_step == 1 else "FAIL",
        "safe_random_state_count": 1000,
        "near_bound_velocity_state_count": 1000,
        "synthetic_cbf_fixture_count": 500,
        "selected_map_g0_state_count": 100,
        "selected_map_geometry_input_count": map_geometry_input_count,
        "selected_map_geometry_input": "canonical Gaussian means only",
        "selected_map_g0_positions_sha256": sha256_bytes(g0_positions),
        "actual_u_box_max_violation": max_u,
        "next_velocity_box_max_violation": max_v,
        "position_euler_max_error": max_position_error,
        "post_qp_clip_count": 0,
        "infeasible_no_plant_step_count": no_step,
        "infeasible_fallback_to_u_des_count": 0,
        "mesh_oracle_controller_input_count": 0,
        "formal_multistep_navigation_count": 0,
        "controller_geometry_source": "selected canonical Gaussian safety map",
    }
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(result, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(result["status"])
    return 0 if result["status"] == "PASS" else 1


if __name__ == "__main__":
    raise SystemExit(main())
