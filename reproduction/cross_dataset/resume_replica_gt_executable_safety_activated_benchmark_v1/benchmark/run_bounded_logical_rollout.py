#!/usr/bin/env python3
"""Bounded logical-time rollout over locked cohorts; reference remains offline."""
from __future__ import annotations

import argparse
import collections
import sys
from pathlib import Path
from typing import Any

import numpy as np

TASK_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(TASK_ROOT))

from common import read_json, sha256_file, sha256_json, write_csv, write_json
from runtime_core import Control, ReplicaMeshOracle, ReplicaRuntime
from task_config import (
    ACTIVATED_ROLLOUT_MAX_STEPS, DT, GOAL_POSITION_TOLERANCE_M,
    GOAL_VELOCITY_TOLERANCE_MPS, MAP_ROOT, METHODS, MESH_ORACLE,
    REFERENCE_MESH, REPRESENTATIVE_ROLLOUT_MAX_STEPS,
    REPRESENTATIVE_ROLLOUT_SUBSET, ROBOT_RADIUS, TASK_ROOT,
)


def select_states(mode: str, activated: dict, representative: dict) -> list[dict[str, Any]]:
    activated_values = [item for item in activated["states"] if item["group"] in {"G0", "G1", "G2", "G3"}]
    if mode == "smoke":
        result = []
        for group in ("G0", "G1", "G2", "G3"):
            candidates = sorted((item for item in activated_values if item["group"] == group), key=lambda item: item["state_id"])
            if candidates:
                result.append(candidates[0])
        return result
    representative_values = sorted(representative["states"], key=lambda item: sha256_json(["REPRESENTATIVE_ROLLOUT_SUBSET", item["state_id"]]))[:REPRESENTATIVE_ROLLOUT_SUBSET]
    return activated_values + representative_values


def main_run(mode: str) -> dict[str, Any]:
    lock = read_json(TASK_ROOT / "registry/registry_lock.json")
    activated = read_json(TASK_ROOT / "registry/activated_registry_v1.json")
    representative = read_json(TASK_ROOT / "registry/representative_holdout_registry_v1.json")
    if sha256_file(TASK_ROOT / "registry/activated_registry_v1.json") != lock["activated_sha256"] or sha256_file(TASK_ROOT / "registry/representative_holdout_registry_v1.json") != lock["representative_sha256"]:
        raise SystemExit("REGISTRY_CHANGED_AFTER_LOCK")
    if mode == "formal":
        marker = read_json(TASK_ROOT / "benchmark/formal_attempt.json")
        if marker["formal_attempt_count"] != 1 or marker["status"] != "FORMAL_ONE_STEP_COMPLETED":
            raise SystemExit("FORMAL_ONE_STEP_BOUNDARY_NOT_SATISFIED")
    states = select_states(mode, activated, representative)
    runtime = ReplicaRuntime(Path(MAP_ROOT))
    oracle = ReplicaMeshOracle(Path(MESH_ORACLE), Path(REFERENCE_MESH), TASK_ROOT / "runtime_work/postlock_reference")
    episodes: dict[str, dict[str, Any]] = {}
    for state in states:
        for method in METHODS:
            episode_id = sha256_json([state["state_id"], method, mode])
            episodes[episode_id] = {
                "episode_id": episode_id,
                "state_id": state["state_id"],
                "method": method,
                "cohort": state["cohort"],
                "group": state.get("group"),
                "position": np.asarray(state["position_m"], dtype=np.float64),
                "velocity": np.asarray(state["velocity_m_per_s"], dtype=np.float64),
                "goal": np.asarray(state["goal_m"], dtype=np.float64),
                "start_goal_distance": float(np.linalg.norm(np.asarray(state["position_m"]) - np.asarray(state["goal_m"]))),
                "max_steps": REPRESENTATIVE_ROLLOUT_MAX_STEPS if state["cohort"] == "REPRESENTATIVE_HOLDOUT" else (5 if mode == "smoke" else ACTIVATED_ROLLOUT_MAX_STEPS),
                "active": True,
                "terminal_reason": None,
                "executed_steps": 0,
                "terminal_action_count": 0,
                "reference_collision": False,
                "represented_violation_count": 0,
                "represented_false_safe_count": 0,
                "runtime_total_s": 0.0,
            }
    step_records = []
    reference_query_count = 0
    maximum = max((episode["max_steps"] for episode in episodes.values()), default=0)
    for step_index in range(maximum):
        pending = []
        for episode in episodes.values():
            if not episode["active"] or step_index >= episode["max_steps"]:
                continue
            state_record = {
                "state_id": episode["state_id"],
                "position_m": episode["position"].tolist(),
                "velocity_m_per_s": episode["velocity"].tolist(),
                "goal_m": episode["goal"].tolist(),
            }
            decision = runtime.method_decision(episode["method"], state_record, timestamp=step_index * DT)
            episode["runtime_total_s"] += float(decision["total_runtime_s"])
            base = {
                "episode_id": episode["episode_id"],
                "state_id": episode["state_id"],
                "method": episode["method"],
                "cohort": episode["cohort"],
                "group": episode["group"],
                "step_index": step_index,
                "position_before_m": episode["position"].tolist(),
                "velocity_before_m_per_s": episode["velocity"].tolist(),
                "semantic_status": decision["semantic_status"],
                "selected_candidate": decision["selected_candidate"],
                "committed": decision["committed"],
                "deadline_miss": decision["deadline_miss"],
                "runtime_s": decision["total_runtime_s"],
                "reference_online_read_count": 0,
            }
            if not decision["committed"]:
                base.update({"position_after_m": episode["position"].tolist(), "velocity_after_m_per_s": episode["velocity"].tolist(), "represented_segment_safe": None, "reference_min_clearance_m": None, "reference_collision": False, "step_terminal_reason": "NO_CERTIFIED_ACTION"})
                step_records.append(base)
                episode["active"] = False
                episode["terminal_reason"] = "NO_CERTIFIED_ACTION"
                continue
            control = np.asarray(decision["control"], dtype=np.float64)
            next_position = episode["position"] + DT * episode["velocity"]
            next_velocity = episode["velocity"] + DT * control
            segment = runtime.segment_certifier.certify(runtime.make_state(state_record, timestamp=step_index * DT), Control(tuple(float(value) for value in control), "ROLLOUT_EXECUTION", str(decision["selected_candidate"])), runtime.map_adapter.map_snapshot_id)
            pending.append((episode, decision, base, next_position, next_velocity, segment))
        if pending:
            distances = oracle.segments(((item[0]["position"], item[3]) for item in pending), f"rollout_{mode}_step_{step_index:02d}")
            reference_query_count += len(distances)
            for (episode, decision, base, next_position, next_velocity, segment), distance in zip(pending, distances):
                collision = distance <= ROBOT_RADIUS
                episode["reference_collision"] = bool(episode["reference_collision"] or collision)
                episode["represented_violation_count"] += int(not segment.certified)
                method_has_segment_gate = episode["method"] != "B0_CURRENT_CBF_ONLY"
                episode["represented_false_safe_count"] += int(method_has_segment_gate and not segment.certified)
                episode["executed_steps"] += 1
                episode["terminal_action_count"] += int(decision["semantic_status"] == "CERTIFIED_TERMINAL_ACTION")
                base.update({
                    "position_after_m": next_position.tolist(),
                    "velocity_after_m_per_s": next_velocity.tolist(),
                    "represented_segment_safe": segment.certified,
                    "represented_segment_lower_bound": segment.lower_bound,
                    "reference_min_clearance_m": distance,
                    "reference_collision": collision,
                    "step_terminal_reason": "REFERENCE_COLLISION" if collision else None,
                })
                step_records.append(base)
                episode["position"] = next_position
                episode["velocity"] = next_velocity
                if collision:
                    episode["active"] = False
                    episode["terminal_reason"] = "REFERENCE_COLLISION"
                elif np.linalg.norm(next_position - episode["goal"]) <= GOAL_POSITION_TOLERANCE_M and np.linalg.norm(next_velocity) <= GOAL_VELOCITY_TOLERANCE_MPS:
                    episode["active"] = False
                    episode["terminal_reason"] = "GOAL_REACHED"
        print("ROLLOUT_PROGRESS", mode, step_index + 1, sum(item["active"] for item in episodes.values()), flush=True)
    summaries = []
    for episode in episodes.values():
        if episode["terminal_reason"] is None:
            episode["terminal_reason"] = "MAX_STEPS"
        final_distance = float(np.linalg.norm(episode["position"] - episode["goal"]))
        progress = episode["start_goal_distance"] - final_distance
        summaries.append({
            "episode_id": episode["episode_id"],
            "state_id": episode["state_id"],
            "method": episode["method"],
            "cohort": episode["cohort"],
            "group": episode["group"],
            "max_steps": episode["max_steps"],
            "executed_steps": episode["executed_steps"],
            "progress_m": progress,
            "positive_progress": progress > 0.0,
            "goal_reached": episode["terminal_reason"] == "GOAL_REACHED",
            "terminal_reached": episode["terminal_action_count"] > 0,
            "terminal_action_count": episode["terminal_action_count"],
            "episode_terminal_reason": episode["terminal_reason"],
            "reference_collision": episode["reference_collision"],
            "represented_segment_violation_count": episode["represented_violation_count"],
            "represented_false_safe_count": episode["represented_false_safe_count"],
            "runtime_total_s": episode["runtime_total_s"],
            "logical_time_s": episode["executed_steps"] * DT,
        })
    result = {
        "status": "PASS_ROLLOUT_SMOKE" if mode == "smoke" else "PASS_FORMAL_BOUNDED_LOGICAL_ROLLOUT",
        "mode": mode,
        "logical_episode_count": len(summaries),
        "logical_control_step_count": len(step_records),
        "reference_offline_segment_query_count": reference_query_count,
        "reference_online_read_count": 0,
        "represented_false_safe_count": sum(item["represented_false_safe_count"] for item in summaries),
    }
    if mode == "smoke":
        write_json(TASK_ROOT / "runtime_work/benchmark_smoke/rollout_summary.json", result)
        write_csv(TASK_ROOT / "runtime_work/benchmark_smoke/rollout_records.csv", step_records)
    else:
        write_csv(TASK_ROOT / "benchmark/rollout_records.csv", step_records)
        write_csv(TASK_ROOT / "benchmark/episode_summary.csv", summaries)
        access = read_json(TASK_ROOT / "reference/reference_oracle_access_log.json")
        access["rollout_segment_query_count"] = reference_query_count
        access["total_post_lock_offline_query_count"] = access["one_step_segment_query_count"] + reference_query_count
        write_json(TASK_ROOT / "reference/reference_oracle_access_log.json", access)
        marker = read_json(TASK_ROOT / "benchmark/formal_attempt.json")
        marker.update({"status": "FORMAL_ATTEMPT_COMPLETED", "logical_episode_count": len(summaries), "logical_control_step_count": len(step_records), "rollout_output_sha256": sha256_file(TASK_ROOT / "benchmark/rollout_records.csv")})
        write_json(TASK_ROOT / "benchmark/formal_attempt.json", marker)
    print(result["status"], len(summaries), len(step_records), result["represented_false_safe_count"])
    return result


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--mode", choices=("smoke", "formal"), required=True)
    arguments = parser.parse_args()
    main_run(arguments.mode)


if __name__ == "__main__":
    main()
