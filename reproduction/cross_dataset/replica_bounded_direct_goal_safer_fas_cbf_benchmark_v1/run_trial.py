#!/usr/bin/env python3
"""One fresh-process trial for the frozen bounded Replica benchmark."""
from __future__ import annotations

import argparse
import hashlib
import json
import math
import os
import sys
import time
import traceback
from pathlib import Path
from typing import Any

import numpy as np

from benchmark_core import (
    DT, MAX_STEPS, METHODS, ROBOT_RADIUS, UMAX, VMAX, BoundedCBFQPAdapter,
    FineSphereMap, FrozenRiskAwareV1, ReplicaMeshOracle, atomic_json,
    finite_vector, legacy_second_order_cbf_rows, nominal_control,
    parse_oracle_distance, project_start_safe, sha256_json,
)


def jsonable(value: Any) -> Any:
    if isinstance(value, np.ndarray):
        return value.tolist()
    if isinstance(value, np.generic):
        return value.item()
    if isinstance(value, dict):
        return {str(k): jsonable(v) for k, v in value.items()}
    if isinstance(value, (list, tuple)):
        return [jsonable(v) for v in value]
    return value


def trial_seed(method: str, route_id: str) -> int:
    digest = hashlib.sha256(f"REPLICA_BOUNDED_TRIAL_V1:{method}:{route_id}".encode("utf-8")).digest()
    return int.from_bytes(digest[:8], "big", signed=False)


def run_control_step(map_geometry: FineSphereMap, risk: FrozenRiskAwareV1,
                     adapter: BoundedCBFQPAdapter, position: np.ndarray,
                     velocity: np.ndarray, goal: np.ndarray, method: str,
                     desired: np.ndarray | None = None) -> dict[str, Any]:
    t0 = time.perf_counter()
    u_des = nominal_control(position, velocity, goal) if desired is None else np.asarray(desired, dtype=np.float64)
    candidate_start = time.perf_counter()
    if method == "M0_BOUNDED_SAFER":
        ids = map_geometry.potentially_active_ids(position, velocity)
        selection = {
            "candidate_budget": None, "candidate_count_total": int(map_geometry.means.shape[0]),
            "candidate_count_final": int(ids.size), "candidate_count_forced_near": 0,
            "candidate_count_forced_heading": 0, "candidate_count_forced_history": 0,
            "candidate_count_risk_ranked": 0, "fallback_used": False, "fallback_reason": "not_applicable",
            "feature_mode": "not_applicable", "constant_feature_fraction": 0.0,
            "equal_static_score_fraction": 0.0,
        }
    else:
        ids, selection = risk.select(position, u_des)
        if ids is None:
            ids = map_geometry.potentially_active_ids(position, velocity)
            selection = dict(selection)
            selection["candidate_count_final"] = int(ids.size)
            selection["fallback_used"] = True
    candidate_seconds = time.perf_counter() - candidate_start
    map_start = time.perf_counter()
    a_cbf, b_cbf, active_ids = legacy_second_order_cbf_rows(map_geometry, position, velocity, ids)
    map_seconds = time.perf_counter() - map_start
    qp_start = time.perf_counter()
    result = adapter.solve(a_cbf, b_cbf, u_des, velocity)
    qp_seconds = time.perf_counter() - qp_start
    return {
        "u_des": u_des, "ids": active_ids, "a_cbf": a_cbf, "b_cbf": b_cbf,
        "qp": result, "selection": selection,
        "timing": {"candidate": candidate_seconds, "map_query": map_seconds, "qp": qp_seconds,
                   "controller_total": time.perf_counter() - t0},
    }


def verify_candidate(map_geometry: FineSphereMap, position: np.ndarray, velocity: np.ndarray,
                     control: dict[str, Any]) -> dict[str, Any]:
    result = control["qp"]
    if result.control is None:
        return {"passed": False, "reason": "QP_INFEASIBLE", "segment_cg": None, "next_cg": None,
                "cbf_residual": None, "p_next": None, "v_next": None, "candidate_count": 0}
    u = np.asarray(result.control, dtype=np.float64)
    p_next = np.asarray(position, dtype=np.float64) + DT * np.asarray(velocity, dtype=np.float64)
    v_next = np.asarray(velocity, dtype=np.float64) + DT * u
    segment_cg, _, candidates = map_geometry.exact_segment_cg(position, p_next)
    next_cg, _ = map_geometry.point_cg(p_next)
    a_cbf = control["a_cbf"]; b_cbf = control["b_cbf"]
    residual = float(np.max(a_cbf @ u - b_cbf)) if a_cbf.size else -math.inf
    finite = finite_vector(u, 3) and finite_vector(p_next, 3) and finite_vector(v_next, 3)
    bounds = bool(np.max(np.abs(u)) <= UMAX + 1e-7 and np.max(np.abs(v_next)) <= VMAX + 1e-7)
    passed = bool(finite and bounds and residual <= 1e-7 and segment_cg > 1e-6 and next_cg > 1e-6)
    reason = "PASS" if passed else (
        "NONFINITE" if not finite else "BOUND" if not bounds else "CBF_RESIDUAL" if residual > 1e-7
        else "SEGMENT" if segment_cg <= 1e-6 else "ENDPOINT"
    )
    return {"passed": passed, "reason": reason, "segment_cg": float(segment_cg), "next_cg": float(next_cg),
            "cbf_residual": residual, "p_next": p_next, "v_next": v_next, "candidate_count": candidates}


def recovery_desired_library(u_des: np.ndarray, velocity: np.ndarray) -> list[np.ndarray]:
    raw = [np.asarray(u_des, dtype=np.float64), np.zeros(3, dtype=np.float64),
           np.clip(-np.asarray(velocity, dtype=np.float64) / DT, -UMAX, UMAX)]
    for x in (-UMAX, 0.0, UMAX):
        for y in (-UMAX, 0.0, UMAX):
            for z in (-UMAX, 0.0, UMAX):
                raw.append(np.array([x, y, z], dtype=np.float64))
    out: list[np.ndarray] = []
    seen: set[bytes] = set()
    for value in raw:
        key = np.ascontiguousarray(value).tobytes()
        if key not in seen:
            seen.add(key); out.append(value)
    return out


def assess_recovery_candidate(map_geometry: FineSphereMap, risk: FrozenRiskAwareV1,
                              position: np.ndarray, velocity: np.ndarray, goal: np.ndarray,
                              desired: np.ndarray) -> dict[str, Any] | None:
    adapter = BoundedCBFQPAdapter()
    first = run_control_step(map_geometry, risk, adapter, position, velocity, goal,
                             "M1_BOUNDED_RISK_AWARE_V1", desired)
    verified = verify_candidate(map_geometry, position, velocity, first)
    if not verified["passed"]:
        return None
    p = verified["p_next"]; v = verified["v_next"]
    min_clearance = min(float(verified["segment_cg"]), float(verified["next_cg"]))
    total_deviation = float(np.linalg.norm(first["qp"].control - nominal_control(position, velocity, goal)))
    for _ in range(4):
        later = run_control_step(map_geometry, risk, adapter, p, v, goal, "M1_BOUNDED_RISK_AWARE_V1")
        checked = verify_candidate(map_geometry, p, v, later)
        if not checked["passed"]:
            return None
        min_clearance = min(min_clearance, float(checked["segment_cg"]), float(checked["next_cg"]))
        total_deviation += float(np.linalg.norm(later["qp"].control - later["u_des"]))
        p, v = checked["p_next"], checked["v_next"]
    return {"first": first, "verify": verified, "min_clearance": min_clearance,
            "goal_distance": float(np.linalg.norm(p - goal)), "control_deviation": total_deviation}


def nominal_lookahead_minimum(map_geometry: FineSphereMap, risk: FrozenRiskAwareV1,
                              position: np.ndarray, velocity: np.ndarray, goal: np.ndarray) -> float:
    adapter = BoundedCBFQPAdapter(); p = position.copy(); v = velocity.copy(); minimum = math.inf
    for _ in range(5):
        control = run_control_step(map_geometry, risk, adapter, p, v, goal, "M1_BOUNDED_RISK_AWARE_V1")
        checked = verify_candidate(map_geometry, p, v, control)
        if not checked["passed"]:
            return -math.inf
        minimum = min(minimum, float(checked["segment_cg"]), float(checked["next_cg"]))
        p, v = checked["p_next"], checked["v_next"]
    return minimum


def evaluate_mesh(oracle: ReplicaMeshOracle, trajectory: list[dict[str, Any]], name: str) -> dict[str, Any]:
    if not trajectory:
        return {"collision": False, "first_collision_step": None, "minimum_mesh_clearance": None}
    pairs = [(np.asarray(row["position_before"]), np.asarray(row["position_after"])) for row in trajectory]
    rows = oracle.query_segments(pairs, name)
    if len(rows) != len(pairs):
        raise RuntimeError("oracle output/query count mismatch")
    center_distances = [parse_oracle_distance(row) for row in rows]
    clearance = [float(value - ROBOT_RADIUS) for value in center_distances]
    hits = [index for index, value in enumerate(center_distances) if value <= ROBOT_RADIUS]
    if hits:
        hit = hits[0]
        del trajectory[hit + 1:]
        return {"collision": True, "first_collision_step": int(hit + 1),
                "minimum_mesh_clearance": float(min(clearance[:hit + 1]))}
    return {"collision": False, "first_collision_step": None, "minimum_mesh_clearance": float(min(clearance))}


def execute_trial(root: Path, route_index: int, method: str) -> dict[str, Any]:
    config = json.loads((root / "frozen_inputs.json").read_text(encoding="utf-8"))
    routes = json.loads(Path(config["route_registry_path"]).read_text(encoding="utf-8"))["routes"]
    route = routes[route_index]
    route_id = str(route["route_id"])
    trial_id = f"{route_index:03d}_{method}_{route_id[:12]}"
    base = {
        "trial_id": trial_id, "route_index": route_index, "route_id": route_id, "method": method,
        "subset": route["subset"], "length_stratum": route["length_stratum"],
        "clearance_stratum": route["clearance_stratum"], "seed": trial_seed(method, route_id),
        "identity_sha256": config["identity_sha256"], "status": None, "status_subtype": "",
        "mesh_oracle_controller_input_count": 0, "post_qp_clip_count": 0,
        "infeasible_fallback_to_u_des_count": 0, "map_mutation_count": 0, "controller_tuning_count": 0,
        "trajectory_path": None, "completion": "terminal",
    }
    map_geometry = FineSphereMap(Path(config["map_dir"]))
    applicable, direct_cg = map_geometry.map_applicable(np.asarray(route["start_m"]), np.asarray(route["goal_m"]))
    base["direct_route_map_cg"] = float(direct_cg)
    if not applicable:
        base.update({"status": "MAP_GEOMETRY_BLOCKED", "status_subtype": "DIRECT_SEGMENT_FINE_MAP_BLOCKED",
                     "steps": 0, "map_blocked_zero_step": True, "observed_discrete_violation_count": 0,
                     "qp_infeasible_count": 0, "recovery_trigger_count": 0})
        return base
    position = np.asarray(route["start_m"], dtype=np.float64); velocity = np.zeros(3, dtype=np.float64)
    goal = np.asarray(route["goal_m"], dtype=np.float64)
    start_safe: dict[str, Any] = {"applied": method in METHODS[2:], "classification": "NOT_APPLICABLE",
                                  "accepted": None, "displacement": 0.0, "iterations": 0}
    if method in METHODS[2:]:
        start_safe = dict(project_start_safe(map_geometry, position))
        start_safe["applied"] = True
        if not bool(start_safe["accepted"]):
            base.update({"status": "START_STATE_REJECTED", "status_subtype": str(start_safe["classification"]),
                         "steps": 0, "start_safe": start_safe, "map_blocked_zero_step": False,
                         "observed_discrete_violation_count": 0, "qp_infeasible_count": 0,
                         "recovery_trigger_count": 0})
            return base
        position = np.asarray(start_safe["position"], dtype=np.float64)
    risk = FrozenRiskAwareV1(map_geometry); adapter = BoundedCBFQPAdapter()
    trajectory: list[dict[str, Any]] = []; status: str | None = None; subtype = ""
    observed_discrete = 0; qp_infeasible = 0; recovery_triggers = 0; recovery_success = 0; recovery_failed = 0
    timing: dict[str, list[float]] = {k: [] for k in ("candidate", "map_query", "qp", "controller_total", "start_safe", "discrete_verifier", "recovery")}
    candidate_counts: list[int] = []; active_counts: list[int] = []; fallback_count = 0; forced_counts: list[int] = []
    start_wall = time.perf_counter()
    for step in range(1, MAX_STEPS + 1):
        if not finite_vector(position, 3) or not finite_vector(velocity, 3):
            status, subtype = "NUMERICAL_FAILURE", "NONFINITE_STATE"; break
        normal = run_control_step(map_geometry, risk, adapter, position, velocity, goal, method)
        for key, value in normal["timing"].items(): timing[key].append(float(value))
        selection = normal["selection"]; candidate_counts.append(int(selection["candidate_count_final"])); active_counts.append(int(normal["ids"].size))
        forced_counts.append(int(selection.get("candidate_count_forced_near", 0)) + int(selection.get("candidate_count_forced_heading", 0)) + int(selection.get("candidate_count_forced_history", 0)))
        fallback_count += int(bool(selection.get("fallback_used", False)))
        verifier_start = time.perf_counter(); checked = verify_candidate(map_geometry, position, velocity, normal)
        timing["discrete_verifier"].append(time.perf_counter() - verifier_start)
        if not checked["passed"]:
            observed_discrete += 1
        actual = normal
        actual_checked = checked
        if method == "M3_FAS_START_SAFE_DISCRETE" and not checked["passed"]:
            status, subtype = "DISCRETE_VERIFICATION_FAILED", str(checked["reason"]); break
        if method == "M4_FAS_START_SAFE_DISCRETE_RECOVERY":
            recovery_start = time.perf_counter()
            lookahead = nominal_lookahead_minimum(map_geometry, risk, position, velocity, goal)
            trigger = (not checked["passed"]) or normal["qp"].control is None or lookahead < 0.02
            if trigger:
                recovery_triggers += 1
                immediate_cg, _, _ = map_geometry.exact_segment_cg(position, position + DT * velocity)
                if immediate_cg <= 1e-6:
                    timing["recovery"].append(time.perf_counter() - recovery_start)
                    status, subtype = "RECOVERY_FAILED", "UNAVOIDABLE_IMMEDIATE_SEGMENT"; recovery_failed += 1; break
                options: list[tuple[tuple[float, float, float, int], dict[str, Any]]] = []
                for index, desired in enumerate(recovery_desired_library(normal["u_des"], velocity)):
                    item = assess_recovery_candidate(map_geometry, risk, position, velocity, goal, desired)
                    if item is not None:
                        key = (-float(item["min_clearance"]), float(item["goal_distance"]), float(item["control_deviation"]), index)
                        options.append((key, item))
                if not options:
                    timing["recovery"].append(time.perf_counter() - recovery_start)
                    status, subtype = "RECOVERY_FAILED", "NO_VALID_HORIZON_ROLLOUT"; recovery_failed += 1; break
                _, chosen = min(options, key=lambda item: item[0])
                actual, actual_checked = chosen["first"], chosen["verify"]
                recovery_success += 1
            timing["recovery"].append(time.perf_counter() - recovery_start)
        if actual["qp"].control is None:
            status, subtype = "QP_INFEASIBLE", str(actual["qp"].status); qp_infeasible += 1; break
        p_next, v_next = actual_checked["p_next"], actual_checked["v_next"]
        trajectory.append({
            "step": step, "position_before": position.copy(), "velocity_before": velocity.copy(),
            "position_after": p_next.copy(), "velocity_after": v_next.copy(), "u_des": actual["u_des"].copy(),
            "u_actual": actual["qp"].control.copy(), "map_segment_cg": actual_checked["segment_cg"],
            "map_next_cg": actual_checked["next_cg"], "cbf_residual": actual_checked["cbf_residual"],
            "selection": actual["selection"], "active_constraints": int(actual["ids"].size),
            "qp_status": actual["qp"].status,
        })
        position, velocity = p_next, v_next
        if np.linalg.norm(position - goal) <= 0.03 and np.linalg.norm(velocity) <= 0.03:
            status, subtype = "SUCCESS", "STOPPED_GOAL"; break
    if status is None:
        status, subtype = "TIMEOUT", "MAX_STEPS_500"
    mesh = {"collision": False, "first_collision_step": None, "minimum_mesh_clearance": None}
    if trajectory:
        oracle = ReplicaMeshOracle(Path(config["mesh_backend"]), Path(config["mesh_path"]),
                                   root / "oracle_queries" / trial_id)
        mesh = evaluate_mesh(oracle, trajectory, trial_id)
        if mesh["collision"]:
            status, subtype = "COLLISION", "OFFICIAL_MESH_CONTINUOUS_SEGMENT"
    trajectory_path = root / "trajectories" / f"{trial_id}.json"
    atomic_json(trajectory_path, jsonable(trajectory))
    final_position = position if not trajectory else np.asarray(trajectory[-1]["position_after"], dtype=np.float64)
    final_velocity = velocity if not trajectory else np.asarray(trajectory[-1]["velocity_after"], dtype=np.float64)
    base.update({
        "status": status, "status_subtype": subtype, "steps": len(trajectory), "map_blocked_zero_step": False,
        "start_safe": jsonable(start_safe), "final_position_m": final_position.tolist(), "final_velocity_m_per_s": final_velocity.tolist(),
        "final_goal_distance_m": float(np.linalg.norm(final_position - goal)),
        "progress_m": float(np.linalg.norm(np.asarray(route["start_m"]) - goal) - np.linalg.norm(final_position-goal)),
        "success": status == "SUCCESS", "mesh_collision": bool(mesh["collision"]),
        "minimum_mesh_clearance_m": mesh["minimum_mesh_clearance"], "first_mesh_collision_step": mesh["first_collision_step"],
        "minimum_executed_map_cg_m": min((float(x["map_segment_cg"]) for x in trajectory), default=None),
        "observed_discrete_violation_count": observed_discrete, "qp_infeasible_count": qp_infeasible,
        "recovery_trigger_count": recovery_triggers, "recovery_success_count": recovery_success,
        "recovery_failed_count": recovery_failed, "candidate_count_mean": float(np.mean(candidate_counts)) if candidate_counts else 0.0,
        "active_constraints_mean": float(np.mean(active_counts)) if active_counts else 0.0,
        "forced_candidate_count_mean": float(np.mean(forced_counts)) if forced_counts else 0.0,
        "risk_fallback_count": fallback_count, "timing_seconds": {k: values for k, values in timing.items()},
        "wall_seconds": time.perf_counter() - start_wall, "trajectory_path": str(trajectory_path),
    })
    return base


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--root", type=Path, required=True)
    parser.add_argument("--route-index", type=int, required=True)
    parser.add_argument("--method", choices=METHODS, required=True)
    args = parser.parse_args()
    # The process is physically pinned by CUDA_VISIBLE_DEVICES=1; CUDA device 0
    # is touched only for runtime identity and never supplies oracle/controller input.
    if os.environ.get("CUDA_VISIBLE_DEVICES") != "1":
        raise RuntimeError("CUDA_VISIBLE_DEVICES must be exactly 1")
    try:
        import torch
        if not torch.cuda.is_available():
            raise RuntimeError("CUDA 0 unavailable after physical-GPU pinning")
        torch.cuda.set_device(0)
        gpu_name = torch.cuda.get_device_name(0)
    except Exception as exc:
        raise RuntimeError(f"GPU preflight failed: {exc!r}") from exc
    root = args.root.resolve(); result_dir = root / "results"; result_dir.mkdir(parents=True, exist_ok=True)
    config = json.loads((root / "frozen_inputs.json").read_text(encoding="utf-8"))
    routes = json.loads(Path(config["route_registry_path"]).read_text(encoding="utf-8"))["routes"]
    route_id = str(routes[args.route_index]["route_id"])
    trial_id = f"{args.route_index:03d}_{args.method}_{route_id[:12]}"
    try:
        record = execute_trial(root, args.route_index, args.method)
        record["gpu"] = {"cuda_visible_devices": "1", "cuda_device": 0, "name": gpu_name}
    except Exception as exc:
        record = {"trial_id": trial_id, "route_index": args.route_index, "route_id": route_id,
                  "method": args.method, "status": "NUMERICAL_FAILURE", "status_subtype": type(exc).__name__,
                  "error": repr(exc), "traceback": traceback.format_exc(), "completion": "terminal",
                  "identity_sha256": config.get("identity_sha256", ""), "gpu": {"cuda_visible_devices": "1", "cuda_device": 0, "name": gpu_name}}
    record = jsonable(record)
    output = result_dir / f"{trial_id}.json"; atomic_json(output, record)
    marker = result_dir / f"{trial_id}.complete.json"; atomic_json(marker, {"trial_id": trial_id, "sha256": sha256_json(record)})
    print(json.dumps({"trial_id": trial_id, "status": record["status"], "result": str(output)}, sort_keys=True), flush=True)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
