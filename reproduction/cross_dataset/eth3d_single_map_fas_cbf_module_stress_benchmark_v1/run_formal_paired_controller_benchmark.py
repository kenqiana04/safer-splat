#!/usr/bin/env python3
"""Run smoke or formal paired controller comparisons on the frozen registry."""

from __future__ import annotations

import argparse
import json
import math
import os
import time
import traceback
from pathlib import Path

import numpy as np

from eth3d_controller_core import (CANDIDATE_BUDGET, GOAL_TOLERANCE_M,
    METHODS, LearnedEllipsoidMap, ReferenceMeshOracle, atomic_json,
    nominal_control, sha256_file, sha256_json)
from fas_cbf_modules import (DT, DT_MARGIN, RECOVERY_HORIZON, UMAX,
    feasibility_aware_rows, integrate, project_start_safe,
    recovery_desired_library, solve_bounded_qp, verify_discrete_step)


RUNTIME_DT_SAMPLES = 5


def jsonable(value):
    if isinstance(value, np.ndarray): return value.tolist()
    if isinstance(value, np.generic): return value.item()
    if isinstance(value, dict): return {str(k): jsonable(v) for k, v in value.items()}
    if isinstance(value, (list, tuple)): return [jsonable(v) for v in value]
    return value


def method_uses_start_safe(method: str) -> bool:
    return method != METHODS[0]


def method_uses_feasibility(method: str) -> bool:
    return method in METHODS[2:]


def method_uses_dt(method: str) -> bool:
    return method in METHODS[3:]


def method_uses_recovery(method: str) -> bool:
    return method == METHODS[4]


def finite_query(result: dict) -> bool:
    return bool(np.all(result["finite"]) and np.isfinite(result["h"]).all())


def active_rows(learned: LearnedEllipsoidMap, query: dict, velocity: np.ndarray,
                method: str) -> tuple[np.ndarray, np.ndarray, np.ndarray, dict]:
    a, b = learned.cbf_rows(query, velocity)
    ids = query["candidate_ids"]
    if method_uses_feasibility(method):
        return feasibility_aware_rows(a, b, query["h"], ids)
    return a, b, ids, {"input_constraint_count": int(len(ids)),
                       "forced_candidate_count": 0,
                       "provably_redundant_count": 0,
                       "output_constraint_count": int(len(ids)),
                       "hidden_relaxation_count": 0, "same_control_bounds": True}


def cached_min_h(learned: LearnedEllipsoidMap, initial_position: np.ndarray,
                 initial_h: float, timing: list[float]):
    cache = {np.asarray(initial_position, dtype=np.float64).tobytes(): float(initial_h)}
    def query(point: np.ndarray) -> float:
        key = np.asarray(point, dtype=np.float64).tobytes()
        if key not in cache:
            started = time.perf_counter(); cache[key] = learned.min_h(point)
            timing.append(time.perf_counter() - started)
        return cache[key]
    return query


def predictive_recovery(learned: LearnedEllipsoidMap, position: np.ndarray,
                        velocity: np.ndarray, goal: np.ndarray,
                        a: np.ndarray, b: np.ndarray, u_des: np.ndarray,
                        initial_h: float, timing: list[float]) -> dict:
    """Fixed H=3 candidate library; reference geometry is intentionally absent."""
    options = []
    for ordinal, desired in enumerate(recovery_desired_library(u_des, velocity)):
        qp = solve_bounded_qp(a, b, desired, velocity)
        if qp.control is None: continue
        p, v = np.asarray(position).copy(), np.asarray(velocity).copy()
        minimum = initial_h; passed = True
        for _ in range(RECOVERY_HORIZON):
            p, v = integrate(p, v, qp.control)
            started = time.perf_counter(); value = learned.min_h(p)
            timing.append(time.perf_counter() - started)
            minimum = min(minimum, value)
            if not math.isfinite(value) or value < DT_MARGIN:
                passed = False; break
        if passed:
            score = (-minimum, float(np.linalg.norm(p - goal)),
                     float(np.linalg.norm(qp.control - u_des)), ordinal)
            options.append((score, qp, minimum))
    if not options:
        return {"success": False, "control": None, "minimum_h": None,
                "candidate_count": len(recovery_desired_library(u_des, velocity))}
    _, qp, minimum = min(options, key=lambda item: item[0])
    return {"success": True, "control": qp.control, "minimum_h": float(minimum),
            "candidate_count": len(recovery_desired_library(u_des, velocity))}


def run_scenario(learned: LearnedEllipsoidMap, oracle: ReferenceMeshOracle,
                 scenario: dict, method: str, identity: dict) -> dict:
    start_wall = time.perf_counter()
    original_start = np.asarray(scenario["start_m"], dtype=np.float64)
    position = original_start.copy()
    velocity = np.asarray(scenario["initial_velocity_mps"], dtype=np.float64)
    goal = np.asarray(scenario["goal_m"], dtype=np.float64)
    projection = {"attempted": False, "success": None, "classification": "NOT_APPLICABLE",
                  "distance_m": 0.0, "initial_min_h": None, "final_min_h": None}
    timing = {key: [] for key in ("query", "qp", "verifier", "recovery", "controller")}
    if method_uses_start_safe(method):
        projection_started = time.perf_counter()
        projected = project_start_safe(position, learned.query)
        timing["controller"].append(time.perf_counter() - projection_started)
        projection = {"attempted": projected["classification"] != "SAFE",
                      "success": bool(projected["accepted"]),
                      "classification": projected["classification"],
                      "distance_m": float(projected["displacement_m"]),
                      "initial_min_h": float(projected["initial_min_h"]),
                      "final_min_h": float(projected["final_min_h"]),
                      "fallback": projected["fallback"]}
        if not projected["accepted"]:
            oracle_result = oracle.evaluate([position])
            return {**identity, "scenario_id": scenario["scenario_id"], "group": scenario["group"],
                    "method": method, "status": "START_STATE_REJECTED", "steps": 0,
                    "projection": projection, **oracle_result, "progress_m": 0.0,
                    "completion": False, "deadlock": True, "qp_infeasible": 0,
                    "wall_seconds": time.perf_counter() - start_wall,
                    "reference_oracle_controller_input_count": 0}
        position = np.asarray(projected["position"], dtype=np.float64)
    trajectory = [position.copy()]
    controls: list[np.ndarray] = []
    desired_controls: list[np.ndarray] = []
    active_counts: list[int] = []; forced_counts: list[int] = []
    query_candidate_counts: list[int] = []; query_h_values: list[float] = []
    qp_infeasible = fallback_count = 0
    dt_checks = dt_triggers = endpoint_only_misses = segment_risk_events = 0
    recovery_triggers = recovery_success = recovery_failure = recovery_steps = 0
    unknown_encounters = 0; deadline_misses = 0
    status = None; status_subtype = ""
    for step in range(1, int(scenario["max_steps"]) + 1):
        controller_started = time.perf_counter()
        query_started = time.perf_counter(); query = learned.query(position)
        timing["query"].append(time.perf_counter() - query_started)
        if not finite_query(query):
            status, status_subtype = "NUMERICAL_FAILURE", "NONFINITE_MAP_QUERY"; break
        min_h = float(np.min(query["h"])); query_h_values.append(min_h)
        query_candidate_counts.append(len(query["candidate_ids"]))
        try:
            a, b, _, reduction = active_rows(learned, query, velocity, method)
        except Exception as exc:
            status, status_subtype = "NUMERICAL_FAILURE", type(exc).__name__; break
        active_counts.append(int(len(b))); forced_counts.append(int(reduction["forced_candidate_count"]))
        u_des = nominal_control(position, velocity, goal); desired_controls.append(u_des.copy())
        qp_started = time.perf_counter(); qp = solve_bounded_qp(a, b, u_des, velocity)
        timing["qp"].append(time.perf_counter() - qp_started)
        if qp.control is None:
            qp_infeasible += 1; status, status_subtype = "QP_INFEASIBLE", qp.status; break
        control = np.asarray(qp.control, dtype=np.float64)
        if method_uses_dt(method):
            dt_checks += 1; verifier_started = time.perf_counter()
            min_h_fn = cached_min_h(learned, position, min_h, timing["query"])
            verified = verify_discrete_step(position, velocity, control, min_h_fn,
                                            samples=RUNTIME_DT_SAMPLES)
            timing["verifier"].append(time.perf_counter() - verifier_started)
            endpoint_only_misses += int(verified["endpoint_only_miss"])
            if not verified["passed"]:
                dt_triggers += 1; segment_risk_events += 1
                if not method_uses_recovery(method):
                    status, status_subtype = "DT_VERIFICATION_BLOCKED", "SEGMENT_OR_ENDPOINT_RISK"; break
            if method_uses_recovery(method):
                predicted_p, predicted_v = position.copy(), velocity.copy(); predicted_min = min_h
                for _ in range(RECOVERY_HORIZON):
                    predicted_p, predicted_v = integrate(predicted_p, predicted_v, control)
                    predicted_min = min(predicted_min, min_h_fn(predicted_p))
                trigger = (not verified["passed"]) or predicted_min < DT_MARGIN
                if trigger:
                    recovery_triggers += 1; recovery_started = time.perf_counter()
                    recovery = predictive_recovery(learned, position, velocity, goal,
                                                   a, b, u_des, min_h, timing["query"])
                    timing["recovery"].append(time.perf_counter() - recovery_started)
                    if not recovery["success"]:
                        recovery_failure += 1; fallback_count += 1
                        status, status_subtype = "RECOVERY_FAILED", "NO_H3_SAFE_CANDIDATE"; break
                    control = np.asarray(recovery["control"], dtype=np.float64)
                    recovery_success += 1; recovery_steps += 1
        next_position, next_velocity = integrate(position, velocity, control)
        if not np.isfinite(next_position).all() or not np.isfinite(next_velocity).all():
            status, status_subtype = "NUMERICAL_FAILURE", "NONFINITE_STATE"; break
        if np.max(np.abs(next_velocity)) > 0.10 + 1e-7 or np.max(np.abs(control)) > UMAX + 1e-7:
            status, status_subtype = "BOUND_VIOLATION", "FROZEN_BOX"; break
        position, velocity = next_position, next_velocity
        trajectory.append(position.copy()); controls.append(control.copy())
        controller_elapsed = time.perf_counter() - controller_started
        timing["controller"].append(controller_elapsed)
        deadline_misses += int(controller_elapsed > DT)
        line = goal - original_start; denominator = float(line @ line)
        fraction = float(np.clip(((position - original_start) @ line) / max(denominator, 1e-12), 0.0, 1.0))
        closest = original_start + fraction * line
        if np.linalg.norm(position - closest) > 0.15:
            unknown_encounters += 1; status, status_subtype = "UNKNOWN_STOP", "OUTSIDE_FROZEN_SUPPORTED_CORRIDOR"; break
        if np.linalg.norm(position - goal) <= GOAL_TOLERANCE_M and np.linalg.norm(velocity) <= 0.03:
            status, status_subtype = "SUCCESS", "STOPPED_GOAL"; break
    if status is None: status, status_subtype = "TIMEOUT", "MAX_STEPS"
    oracle_result = oracle.evaluate(trajectory)
    if oracle_result["reference_collision"]:
        status, status_subtype = "REFERENCE_COLLISION", "INDEPENDENT_MESH_ORACLE"
    final = trajectory[-1]
    initial_goal_distance = float(np.linalg.norm(original_start - goal))
    progress = initial_goal_distance - float(np.linalg.norm(final - goal))
    control_array = np.asarray(controls, dtype=np.float64) if controls else np.empty((0, 3))
    deltas = np.diff(control_array, axis=0) if len(control_array) > 1 else np.empty((0, 3))
    delta_norm = np.linalg.norm(deltas, axis=1) if len(deltas) else np.asarray([])
    jerk = deltas / DT if len(deltas) else np.empty((0, 3))
    jerk_norm = np.linalg.norm(jerk, axis=1) if len(jerk) else np.asarray([])
    controller_times = np.asarray(timing["controller"], dtype=np.float64)
    result = {
        **identity, "scenario_id": scenario["scenario_id"], "group": scenario["group"],
        "method": method, "seed": scenario["seed"], "start_m": scenario["start_m"],
        "goal_m": scenario["goal_m"], "initial_velocity_mps": scenario["initial_velocity_mps"],
        "status": status, "status_subtype": status_subtype, "steps": len(controls),
        "completion": status == "SUCCESS", "progress_m": progress,
        "path_length_m": float(np.sum(np.linalg.norm(np.diff(np.asarray(trajectory), axis=0), axis=1))) if len(trajectory)>1 else 0.0,
        "min_map_h": min(query_h_values) if query_h_values else projection.get("initial_min_h"),
        "unknown_encounters": unknown_encounters, "projection": projection,
        "qp_infeasible": qp_infeasible, "infeasible_steps": qp_infeasible,
        "fallback_count": fallback_count,
        "forced_candidate_events": int(np.sum(np.asarray(forced_counts) > 0)),
        "forced_candidate_count_mean": float(np.mean(forced_counts)) if forced_counts else 0.0,
        "active_constraints_mean": float(np.mean(active_counts)) if active_counts else 0.0,
        "active_constraints_p95": float(np.percentile(active_counts, 95)) if active_counts else 0.0,
        "active_constraints_max": max(active_counts, default=0),
        "candidate_count_mean": float(np.mean(query_candidate_counts)) if query_candidate_counts else 0.0,
        "dt_checks": dt_checks, "dt_triggers": dt_triggers,
        "endpoint_only_misses": endpoint_only_misses, "segment_risk_events": segment_risk_events,
        "recovery_triggers": recovery_triggers, "recovery_success": recovery_success,
        "recovery_failure": recovery_failure, "recovery_steps": recovery_steps,
        "post_recovery_progress_m": progress if recovery_success else None,
        "deadlock": status in {"QP_INFEASIBLE", "DT_VERIFICATION_BLOCKED", "RECOVERY_FAILED", "TIMEOUT"},
        "runtime_mean_s": float(np.mean(controller_times)) if len(controller_times) else 0.0,
        "runtime_p95_s": float(np.percentile(controller_times, 95)) if len(controller_times) else 0.0,
        "runtime_max_s": float(np.max(controller_times)) if len(controller_times) else 0.0,
        "deadline_miss_count": deadline_misses,
        "timing_seconds": timing,
        "control_delta_mean": float(np.mean(delta_norm)) if len(delta_norm) else 0.0,
        "control_delta_p95": float(np.percentile(delta_norm, 95)) if len(delta_norm) else 0.0,
        "control_delta_max": float(np.max(delta_norm)) if len(delta_norm) else 0.0,
        "control_tv": float(np.sum(delta_norm)),
        "jerk_rms": float(np.sqrt(np.mean(jerk_norm ** 2))) if len(jerk_norm) else 0.0,
        "jerk_p95": float(np.percentile(jerk_norm, 95)) if len(jerk_norm) else 0.0,
        "jerk_max": float(np.max(jerk_norm)) if len(jerk_norm) else 0.0,
        "intervention_switches": int(np.sum(np.linalg.norm(control_array - np.asarray(desired_controls[:len(control_array)]), axis=1) > 1e-6)) if len(control_array) else 0,
        "active_set_switch_rate": float(np.mean(np.diff(active_counts) != 0)) if len(active_counts) > 1 else 0.0,
        **oracle_result, "reference_oracle_controller_input_count": 0,
        "map_mutation_count": 0, "post_qp_clip_count": 0,
        "wall_seconds": time.perf_counter() - start_wall,
    }
    return jsonable(result)


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--mode", choices=("smoke", "formal"), required=True)
    parser.add_argument("--task-root", type=Path, required=True)
    parser.add_argument("--canonical-root", type=Path, required=True)
    parser.add_argument("--source-root", type=Path, required=True)
    parser.add_argument("--controller-snapshot", type=Path, required=True)
    parser.add_argument("--registry", type=Path, required=True)
    parser.add_argument("--reference-mesh", type=Path, required=True)
    args = parser.parse_args()
    if os.environ.get("CUDA_VISIBLE_DEVICES") != "1": raise RuntimeError("physical GPU 1 pin required")
    registry = json.loads(args.registry.read_text(encoding="utf-8"))
    scenarios = registry["scenarios"]
    if args.mode == "smoke":
        selected = [row for group in sorted({row["group"] for row in scenarios})
                    for row in [item for item in scenarios if item["group"] == group][:2]]
        output_root = args.task_root / "smoke_controller"
    else:
        selected = scenarios; output_root = args.task_root / "formal_controller"
    output_root.mkdir(parents=True, exist_ok=True); (output_root / "results").mkdir(exist_ok=True)
    identity = {
        "map_ply_sha256": "927734a2339a3f2710640065b0893eaae162cc0144ac67e2f377bcff2e71ae34",
        "canonical_tree_sha256": "06c1ff17d2ed5eb184b6a9699a3a32da431a1460840431a3effe76d5f03b9ee3",
        "scenario_registry_sha256": registry["registry_sha256"],
        "source_commit": "54c035f7834b564019656c3e3fcc3646292f727d",
        "benchmark_config_sha256": sha256_json({"methods": METHODS, "dt": DT,
            "candidate_budget": CANDIDATE_BUDGET, "dt_margin": DT_MARGIN,
            "runtime_dt_samples": RUNTIME_DT_SAMPLES, "recovery_horizon": RECOVERY_HORIZON,
            "max_steps": 200, "control_bound": 0.1, "velocity_bound": 0.1}),
    }
    manifest_path = output_root / "run_manifest.json"
    expected = len(selected) * len(METHODS)
    manifest = {"mode": args.mode, "state": "RUNNING", "expected_run_count": expected,
                "terminal_run_count": 0, "failure_infrastructure_count": 0,
                "identity": identity, "methods": list(METHODS),
                "scenario_ids": [row["scenario_id"] for row in selected],
                "reference_oracle_controller_input_count": 0}
    atomic_json(manifest_path, manifest)
    learned = LearnedEllipsoidMap(args.canonical_root, args.source_root,
                                  args.controller_snapshot)
    oracle = ReferenceMeshOracle(args.reference_mesh)
    terminal = 0
    for scenario in selected:
        for method in METHODS:
            trial_id = f"{scenario['scenario_id']}__{method}"
            output = output_root / "results" / f"{trial_id}.json"
            marker = output_root / "results" / f"{trial_id}.complete.json"
            if marker.exists() and output.exists():
                old = json.loads(output.read_text(encoding="utf-8"))
                if json.loads(marker.read_text(encoding="utf-8"))["sha256"] != sha256_json(old):
                    raise RuntimeError(f"completed result identity mismatch: {trial_id}")
                terminal += 1; continue
            try:
                result = run_scenario(learned, oracle, scenario, method, identity)
            except Exception as exc:  # terminal scientific preservation, never hidden retry
                result = {**identity, "scenario_id": scenario["scenario_id"],
                          "group": scenario["group"], "method": method,
                          "status": "NUMERICAL_FAILURE", "status_subtype": type(exc).__name__,
                          "error": repr(exc), "traceback": traceback.format_exc(),
                          "reference_oracle_controller_input_count": 0,
                          "map_mutation_count": 0}
            atomic_json(output, result); atomic_json(marker, {"trial_id": trial_id,
                                                               "sha256": sha256_json(result)})
            terminal += 1; manifest["terminal_run_count"] = terminal
            manifest["last_trial_id"] = trial_id; atomic_json(manifest_path, manifest)
            print(json.dumps({"terminal": terminal, "expected": expected,
                              "trial_id": trial_id, "status": result["status"]}), flush=True)
    manifest["state"] = "COMPLETED"; manifest["terminal_run_count"] = terminal
    manifest["map_sha_after"] = sha256_file(Path("/disk1/zlab/cross_dataset_maps/eth3d_delivery_area_official_3dgs_v1/point_cloud/iteration_30000/point_cloud.ply"))
    atomic_json(manifest_path, manifest)
    print(json.dumps({"status": f"PASS_{args.mode.upper()}_CONTROLLER_MATRIX",
                      "terminal": terminal, "expected": expected}, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
