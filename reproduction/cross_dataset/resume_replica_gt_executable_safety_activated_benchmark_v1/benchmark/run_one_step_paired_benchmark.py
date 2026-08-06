#!/usr/bin/env python3
"""Locked-registry one-step paired benchmark with post-lock reference evaluation."""
from __future__ import annotations

import argparse
import collections
import json
import math
import sys
import time
from pathlib import Path
from typing import Any

import numpy as np

TASK_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(TASK_ROOT))

from common import read_json, sha256_file, sha256_json, write_csv, write_json
from runtime_core import ReplicaMeshOracle, ReplicaRuntime
from task_config import (
    DT, MAP_ROOT, METHODS, MESH_ORACLE, REFERENCE_MESH, ROBOT_RADIUS,
    SLOT_IDS, TASK_ROOT,
)


def require_lock() -> tuple[dict, dict, dict]:
    lock = read_json(TASK_ROOT / "registry/registry_lock.json")
    activated = read_json(TASK_ROOT / "registry/activated_registry_v1.json")
    representative = read_json(TASK_ROOT / "registry/representative_holdout_registry_v1.json")
    if lock["status"] != "IMMUTABLY_LOCKED_BEFORE_FORMAL_AND_FUTURE_REFERENCE_OUTCOMES":
        raise SystemExit("REGISTRY_NOT_LOCKED")
    if sha256_file(TASK_ROOT / "registry/activated_registry_v1.json") != lock["activated_sha256"]:
        raise SystemExit("ACTIVATED_REGISTRY_CHANGED_AFTER_LOCK")
    if sha256_file(TASK_ROOT / "registry/representative_holdout_registry_v1.json") != lock["representative_sha256"]:
        raise SystemExit("REPRESENTATIVE_REGISTRY_CHANGED_AFTER_LOCK")
    return lock, activated, representative


def smoke_states(activated: dict, representative: dict) -> list[dict[str, Any]]:
    values = []
    by_group: dict[str, list[dict[str, Any]]] = collections.defaultdict(list)
    for state in activated["states"]:
        by_group[state["group"]].append(state)
    for group in sorted(by_group):
        values.extend(sorted(by_group[group], key=lambda item: item["state_id"])[:2])
    values.extend(sorted(representative["states"], key=lambda item: item["state_id"])[:8])
    return values


def summarize(records: list[dict[str, Any]]) -> list[dict[str, Any]]:
    buckets: dict[tuple[str, str, str], list[dict[str, Any]]] = collections.defaultdict(list)
    for record in records:
        buckets[(record["method"], record["cohort"], str(record.get("postlock_group") or "UNCLASSIFIED"))].append(record)
    result = []
    for (method, cohort, group), values in sorted(buckets.items()):
        count = len(values)
        result.append({
            "method": method,
            "cohort": cohort,
            "group": group,
            "state_count": count,
            "commit_count": sum(item["committed"] for item in values),
            "commit_rate": sum(item["committed"] for item in values) / count,
            "primary_commit_count": sum(item["selected_candidate"] == "PRIMARY-CBF-FILTERED" for item in values),
            "directional_selection_count": sum(item["selected_candidate"] in SLOT_IDS for item in values),
            "deterministic_braking_count": sum(str(item["selected_candidate"] or "").startswith("brake-") for item in values),
            "terminal_action_count": sum(item["semantic_status"] == "CERTIFIED_TERMINAL_ACTION" for item in values),
            "fail_closed_count": sum(not item["committed"] for item in values),
            "deadline_miss_count": sum(item["deadline_miss"] for item in values),
            "reference_collision_count": sum(item["reference_immediate_swept_collision"] for item in values),
            "reference_safe_but_rejected_count": sum(item["reference_safe_but_rejected"] for item in values),
            "represented_false_safe_count": sum(item["represented_false_safe"] for item in values),
            "mean_progress_m": sum(float(item["progress_m"]) for item in values) / count,
            "mean_runtime_s": sum(float(item["total_runtime_s"]) for item in values) / count,
        })
    return result


def run(mode: str, resume_infrastructure: bool = False) -> dict[str, Any]:
    lock, activated, representative = require_lock()
    if activated["quota_case"] == "A5_STRUCTURAL_ACTIVATION_LIMIT":
        raise SystemExit("NO_REPLICA_GT_STATE_SET_SUFFICIENTLY_ACTIVATES_CORE_V1_GATES")
    states = smoke_states(activated, representative) if mode == "smoke" else activated["states"] + representative["states"]
    runtime = ReplicaRuntime(Path(MAP_ROOT))
    oracle = ReplicaMeshOracle(Path(MESH_ORACLE), Path(REFERENCE_MESH), TASK_ROOT / "runtime_work/postlock_reference")
    formal_marker = TASK_ROOT / "benchmark/formal_attempt.json"
    if mode == "formal":
        if formal_marker.exists():
            marker = read_json(formal_marker)
            forbidden_outputs = [
                TASK_ROOT / "benchmark/one_step_records.csv",
                TASK_ROOT / "benchmark/paired_method_summary.csv",
            ]
            if not resume_infrastructure:
                raise SystemExit("FORMAL_ATTEMPT_ALREADY_EXISTS_NO_RETRY")
            if marker.get("status") != "FORMAL_ATTEMPT_INFRASTRUCTURE_INTERRUPTED":
                raise SystemExit("FORMAL_ATTEMPT_NOT_RESUMABLE")
            if marker.get("formal_attempt_count") != 1 or any(path.exists() for path in forbidden_outputs):
                raise SystemExit("FORMAL_ATTEMPT_RESUME_BOUNDARY_VIOLATION")
            marker.update({
                "status": "FORMAL_ATTEMPT_RESUMED_SAME_MANIFEST",
                "infrastructure_resume_count": int(marker.get("infrastructure_resume_count", 0)) + 1,
            })
            write_json(formal_marker, marker)
        else:
            if resume_infrastructure:
                raise SystemExit("FORMAL_ATTEMPT_RESUME_MARKER_MISSING")
            write_json(formal_marker, {
                "status": "FORMAL_ATTEMPT_STARTED",
                "formal_attempt_count": 1,
                "infrastructure_failure_count": 0,
                "infrastructure_resume_count": 0,
                "activated_registry_sha256": lock["activated_sha256"],
                "representative_registry_sha256": lock["representative_sha256"],
                "method_order": list(METHODS),
            })

    state_context = {}
    reference_segments = []
    for state in states:
        stage = runtime.evaluate_stage(state)
        position = np.asarray(state["position_m"], dtype=np.float64)
        velocity = np.asarray(state["velocity_m_per_s"], dtype=np.float64)
        endpoint = position + DT * velocity
        reference_segments.append((position, endpoint))
        state_context[state["state_id"]] = {"stage": stage, "endpoint": endpoint}
    reference_distances = oracle.segments(reference_segments, f"one_step_{mode}")
    reference_by_state = {state["state_id"]: distance for state, distance in zip(states, reference_distances)}

    records = []
    for state_index, state in enumerate(states):
        context = state_context[state["state_id"]]
        group = state.get("group") or context["stage"].get("group")
        position = np.asarray(state["position_m"], dtype=np.float64)
        goal = np.asarray(state["goal_m"], dtype=np.float64)
        reference_distance = reference_by_state[state["state_id"]]
        reference_collision = reference_distance <= ROBOT_RADIUS
        for method in METHODS:
            decision = runtime.method_decision(method, state)
            control = None if decision.get("control") is None else np.asarray(decision["control"], dtype=np.float64)
            endpoint = context["endpoint"]
            progress = float(np.linalg.norm(position - goal) - np.linalg.norm(endpoint - goal)) if decision["committed"] else 0.0
            represented_safe = bool(context["stage"]["segment_safe"])
            method_has_segment_gate = method != "B0_CURRENT_CBF_ONLY"
            represented_false_safe = bool(decision["committed"] and method_has_segment_gate and not represented_safe)
            record = dict(decision)
            record.update({
                "formal_attempt": mode == "formal",
                "cohort": state["cohort"],
                "prelock_group": state.get("group"),
                "postlock_group": group,
                "position_m": state["position_m"],
                "velocity_m_per_s": state["velocity_m_per_s"],
                "goal_m": state["goal_m"],
                "reference_min_clearance_m": reference_distance,
                "reference_immediate_swept_collision": reference_collision,
                "represented_segment_safe": represented_safe,
                "represented_segment_violation": not represented_safe,
                "represented_false_safe": represented_false_safe,
                "map_reference_disagreement": represented_safe == reference_collision,
                "reference_safe_but_rejected": bool(not reference_collision and not decision["committed"]),
                "reference_collision_after_commit": bool(reference_collision and decision["committed"]),
                "progress_m": progress,
                "control_deviation_from_primary": None if control is None or decision["u_filtered"] is None else float(np.linalg.norm(control - np.asarray(decision["u_filtered"]))),
                "candidate_exhaustion": "FROZEN_LIBRARY" in str(decision["typed_reason"]) or "BACKUP_WITNESS_NOT_FOUND" in str(decision["semantic_status"]),
                "reference_online_read_count": 0,
            })
            records.append(record)
        if state_index % 20 == 0:
            print("ONE_STEP_PROGRESS", mode, state_index, len(states), flush=True)

    shared_mismatches = 0
    by_state: dict[str, list[dict[str, Any]]] = collections.defaultdict(list)
    for record in records:
        by_state[record["state_id"]].append(record)
    for values in by_state.values():
        shared_mismatches += int(len({item["shared_input_hash"] for item in values}) != 1)
    if shared_mismatches:
        raise SystemExit("BLOCKED_BY_RESUMED_METHOD_CONTRACT_MISMATCH")

    summary = summarize(records)
    result = {
        "status": "PASS_BENCHMARK_SMOKE" if mode == "smoke" else "PASS_FORMAL_ONE_STEP_PAIRED_BENCHMARK",
        "mode": mode,
        "state_count": len(states),
        "one_step_method_run_count": len(records),
        "shared_input_mismatch_count": shared_mismatches,
        "reference_offline_query_count": len(reference_segments),
        "reference_online_read_count": 0,
        "represented_false_safe_count": sum(item["represented_false_safe"] for item in records),
        "deadline_miss_count": sum(item["deadline_miss"] for item in records),
    }
    if mode == "smoke":
        write_json(TASK_ROOT / "runtime_work/benchmark_smoke/one_step_summary.json", result)
        write_csv(TASK_ROOT / "runtime_work/benchmark_smoke/one_step_records.csv", records)
    else:
        write_csv(TASK_ROOT / "benchmark/one_step_records.csv", records)
        write_csv(TASK_ROOT / "benchmark/paired_method_summary.csv", summary)
        write_csv(TASK_ROOT / "reference/offline_reference_results.csv", [
            {"state_id": state["state_id"], "cohort": state["cohort"], "group": state.get("group"), "immediate_min_distance_m": reference_by_state[state["state_id"]], "immediate_swept_collision": reference_by_state[state["state_id"]] <= ROBOT_RADIUS}
            for state in states
        ])
        write_json(TASK_ROOT / "benchmark/timing_by_method_cohort_group.json", {"summaries": summary})
        write_json(TASK_ROOT / "benchmark/deadline_audit.json", {
            "deadline_s": DT,
            "semantic_status_separate": True,
            "deadline_miss_count": result["deadline_miss_count"],
            "method_run_count": len(records),
            "deadline_miss_rate": result["deadline_miss_count"] / len(records) if records else 0.0,
        })
        write_json(TASK_ROOT / "reference/reference_oracle_access_log.json", {
            "status": "PASS_POST_LOCK_OFFLINE_REFERENCE_ONLY",
            "registry_locked_before_first_access": True,
            "controller_exposure_count": 0,
            "online_reference_read_count": 0,
            "one_step_segment_query_count": len(reference_segments),
            "query_batch_sha256": sha256_json(reference_segments),
        })
        marker = read_json(formal_marker)
        marker.update({"status": "FORMAL_ONE_STEP_COMPLETED", "one_step_method_run_count": len(records), "output_sha256": sha256_file(TASK_ROOT / "benchmark/one_step_records.csv")})
        write_json(formal_marker, marker)
    print(result["status"], len(states), len(records), result["represented_false_safe_count"])
    return result


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--mode", choices=("smoke", "formal"), required=True)
    parser.add_argument("--resume-infrastructure", action="store_true")
    arguments = parser.parse_args()
    run(arguments.mode, arguments.resume_infrastructure)


if __name__ == "__main__":
    main()
