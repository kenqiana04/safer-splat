#!/usr/bin/env python3
"""Run the frozen activated candidate generator and online stage predicates."""
from __future__ import annotations

import argparse
import collections
import itertools
import math
import sys
import time
from pathlib import Path
from typing import Any

import numpy as np

TASK_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(TASK_ROOT))

from common import read_json, sha256_json, write_csv, write_json
from runtime_core import ReplicaMeshOracle, ReplicaRuntime, iter_activated_candidates, physically_admissible
from task_config import (
    CANDIDATE_SEARCH_LIMIT, CANDIDATE_SEARCH_SMOKE_LIMIT, GROUP_MINIMUMS,
    GROUP_TARGETS, MAP_ROOT, MESH_ORACLE, REFERENCE_MESH, ROUTE_REGISTRY,
    TASK_ROOT,
)


def position_key(values: list[float] | np.ndarray) -> str:
    return sha256_json([float(value) for value in values])


def stratum(record: dict[str, Any]) -> tuple[str, ...]:
    horizon = record.get("primary_backup_horizon")
    if horizon is None:
        horizon_band = "NONE"
    elif horizon <= 5:
        horizon_band = "H00_05"
    elif horizon <= 10:
        horizon_band = "H06_10"
    else:
        horizon_band = "H11_20"
    return (
        str(record["state"]["source_type"]),
        str(record["state"]["velocity_direction_type"]),
        f"{float(record['state']['velocity_magnitude']):.3f}",
        horizon_band,
        str(record.get("b3_selected_candidate") or "NONE"),
    )


def balanced_select(records: list[dict[str, Any]], target: int) -> list[dict[str, Any]]:
    buckets: dict[tuple[str, ...], list[dict[str, Any]]] = collections.defaultdict(list)
    for record in records:
        buckets[stratum(record)].append(record)
    for values in buckets.values():
        values.sort(key=lambda item: item["state_goal_hash"])
    selected: list[dict[str, Any]] = []
    keys = sorted(buckets)
    while len(selected) < target:
        progressed = False
        for key in keys:
            if buckets[key] and len(selected) < target:
                selected.append(buckets[key].pop(0))
                progressed = True
        if not progressed:
            break
    return selected


def quota_case(counts: dict[str, int]) -> str:
    if all(counts[group] >= target for group, target in GROUP_TARGETS.items()):
        return "A1_ALL_TARGETS_MET"
    if all(counts[group] >= minimum for group, minimum in GROUP_MINIMUMS.items()):
        return "A2_ALL_MINIMUMS_MET_STRUCTURAL_SHORTFALL"
    if counts["G3"] < GROUP_MINIMUMS["G3"] and counts["G1"] >= GROUP_MINIMUMS["G1"] and counts["G2"] >= GROUP_MINIMUMS["G2"]:
        return "A3_GATE_FOCUSED_DIRECTIONAL_RESCUE_GAP"
    if counts["G1"] < GROUP_MINIMUMS["G1"] and (counts["G2"] >= GROUP_MINIMUMS["G2"] or counts["G3"] >= GROUP_MINIMUMS["G3"]):
        return "A4_BACKUP_FOCUSED_SEGMENT_GAP"
    return "A5_STRUCTURAL_ACTIVATION_LIMIT"


def compact_stage(record: dict[str, Any]) -> dict[str, Any]:
    state = record["state"]
    result = {
        "cohort": "ACTIVATED",
        "group": record["group"],
        "state_id": record["state_goal_hash"],
        "position_m": state["position_m"],
        "velocity_m_per_s": state["velocity_m_per_s"],
        "goal_m": state["goal_m"],
        "route_id": state["route_id"],
        "route_execution_order": state["route_execution_order"],
        "route_subset": state["route_subset"],
        "source_type": state["source_type"],
        "route_fraction": state["route_fraction"],
        "velocity_direction_type": state["velocity_direction_type"],
        "velocity_magnitude": state["velocity_magnitude"],
        "surface_clearance_offset_m": state["surface_clearance_offset_m"],
        "surface_tangent_offset_m": state["surface_tangent_offset_m"],
        "represented_primitive_id": state["represented_primitive_id"],
        "physical_start_clearance_m": state["physical_start_clearance_m"],
        "physical_goal_clearance_m": state["physical_goal_clearance_m"],
        "u_nom": record["u_nom"],
        "u_filtered": record["u_filtered"],
        "current_status": record["current_status"],
        "current_h": record["current_h"],
        "endpoint_diagnostic_pass": record["endpoint_diagnostic_pass"],
        "segment_safe": record["segment_safe"],
        "segment_unsafe": record["segment_unsafe"],
        "segment_lower_bound": record["segment_lower_bound"],
        "terminal": record["terminal"],
        "primary_backup_pass": record["primary_backup_pass"],
        "primary_backup_horizon": record["primary_backup_horizon"],
        "b2_status": record["b2_status"],
        "b3_status": record["b3_status"],
        "b3_directional_rescue": record["b3_directional_rescue"],
        "b3_selected_candidate": record["b3_selected_candidate"],
        "directional_slot_states": record["directional_slot_states"],
        "selection_reference_future_read_count": 0,
        "selection_formal_method_run_count": 0,
        "selection_progress_read_count": 0,
        "selection_runtime_input_count": 0,
    }
    result["registry_record_sha256"] = sha256_json(result)
    return result


def run(mode: str, limit: int) -> dict[str, Any]:
    started = time.perf_counter()
    routes = read_json(Path(ROUTE_REGISTRY))["routes"]
    runtime = ReplicaRuntime(Path(MAP_ROOT))
    oracle = ReplicaMeshOracle(Path(MESH_ORACLE), Path(REFERENCE_MESH), TASK_ROOT / "runtime_work/prelock_reference")
    groups: dict[str, list[dict[str, Any]]] = {group: [] for group in GROUP_TARGETS}
    funnel = collections.Counter()
    access_rows: list[dict[str, Any]] = []
    point_cache: dict[str, float] = {}
    goal_cache: dict[str, float] = {}
    generator = itertools.islice(iter_activated_candidates(routes, runtime), limit)
    batch_size = 2000
    processed = 0
    target_complete = False
    while processed < limit and not target_complete:
        batch = list(itertools.islice(generator, batch_size))
        if not batch:
            break
        funnel["generated"] += len(batch)
        unique_points: dict[str, np.ndarray] = {}
        unique_goals: dict[str, np.ndarray] = {}
        for item in batch:
            pkey = position_key(item["position_m"])
            gkey = position_key(item["goal_m"])
            if pkey not in point_cache:
                unique_points.setdefault(pkey, np.asarray(item["position_m"], dtype=np.float64))
            if gkey not in goal_cache:
                unique_goals.setdefault(gkey, np.asarray(item["goal_m"], dtype=np.float64))
        point_distances = oracle.points(unique_points.values(), f"{mode}_start_{processed:06d}")
        goal_distances = oracle.points(unique_goals.values(), f"{mode}_goal_{processed:06d}")
        for (key, point), distance in zip(unique_points.items(), point_distances):
            point_cache[key] = distance
            access_rows.append({"cohort": "ACTIVATED", "phase": mode, "access": "START_POINT_PHYSICAL_ADMISSIBILITY", "point_sha256": key, "distance_m": distance, "allowed_fields_only": True})
        for (key, point), distance in zip(unique_goals.items(), goal_distances):
            goal_cache[key] = distance
            access_rows.append({"cohort": "ACTIVATED", "phase": mode, "access": "GOAL_POINT_PHYSICAL_ADMISSIBILITY", "point_sha256": key, "distance_m": distance, "allowed_fields_only": True})
        for item in batch:
            processed += 1
            p_distance = point_cache[position_key(item["position_m"])]
            g_distance = goal_cache[position_key(item["goal_m"])]
            if not physically_admissible(p_distance, g_distance):
                continue
            funnel["physical_valid"] += 1
            item["physical_start_clearance_m"] = p_distance
            item["physical_goal_clearance_m"] = g_distance
            result = runtime.evaluate_stage(item)
            funnel["stage_predicate"] += 1
            if result["current_status"] == "FINITE":
                funnel["map_valid"] += 1
            if result["current_feasible"]:
                funnel["current_feasible"] += 1
            else:
                funnel["current_infeasible"] += 1
            if result["endpoint_diagnostic_pass"]:
                funnel["endpoint_diagnostic_pass"] += 1
            if result["segment_safe"]:
                funnel["segment_safe"] += 1
            if result["segment_unsafe"]:
                funnel["segment_unsafe"] += 1
            if result["primary_backup_pass"]:
                funnel["primary_backup_pass"] += 1
            elif result["segment_safe"] and result["current_feasible"]:
                funnel["primary_backup_fail"] += 1
            funnel["B3_alternative_available"] += int(result["directional_available_count"] > 0)
            funnel["B3_alternative_certified"] += int(result["b3_directional_rescue"])
            funnel["terminal"] += int(result["terminal"])
            if result["group"] in groups and len(groups[result["group"]]) < max(4 * GROUP_TARGETS[result["group"]], GROUP_MINIMUMS[result["group"]]):
                groups[result["group"]].append(result)
            if mode == "full" and all(len(groups[group]) >= target for group, target in GROUP_TARGETS.items()):
                target_complete = True
                break
        print("ACTIVATED_PROGRESS", mode, processed, {key: len(value) for key, value in groups.items()}, flush=True)

    raw_counts = {group: len(records) for group, records in groups.items()}
    case = quota_case(raw_counts)
    selected = []
    for group, target in GROUP_TARGETS.items():
        selected.extend(compact_stage(record) for record in balanced_select(groups[group], min(target, len(groups[group]))))
    selected.sort(key=lambda item: (list(GROUP_TARGETS).index(item["group"]), item["state_id"]))
    registry_payload = {
        "registry_id": "REPLICA_GT_EXECUTABLE_SAFETY_ACTIVATED_REGISTRY_V1",
        "cohort": "ACTIVATED",
        "selection_locked": False,
        "quota_case": case,
        "state_count": len(selected),
        "group_counts": dict(collections.Counter(item["group"] for item in selected)),
        "states": selected,
    }
    registry_payload["registry_content_sha256"] = sha256_json(registry_payload)
    summary = {
        "status": "PASS_ACTIVATED_SEARCH_SMOKE" if mode == "smoke" else "PASS_ACTIVATED_SEARCH_COMPLETE",
        "mode": mode,
        "search_limit": limit,
        "stopped_after_target_completion": target_complete,
        "activated_candidate_generation_count": processed,
        "activated_physical_valid_count": int(funnel["physical_valid"]),
        "activated_stage_predicate_count": int(funnel["stage_predicate"]),
        "funnel": dict(funnel),
        "raw_group_counts": raw_counts,
        "selected_group_counts": registry_payload["group_counts"],
        "quota_case": case,
        "prelock_future_reference_read_count": 0,
        "prelock_formal_method_run_count": 0,
        "prelock_physical_reference_access_count": len(access_rows),
        "runtime_s": time.perf_counter() - started,
    }
    if mode == "smoke":
        write_json(TASK_ROOT / "activated_generation/activated_search_smoke_summary.json", summary)
        write_json(TASK_ROOT / "reference/reference_prelock_access_log_smoke.json", {"allowed_scope": "PHYSICAL_ADMISSIBILITY_ONLY", "future_outcome_read_count": 0, "access_count": len(access_rows), "accesses": access_rows})
    else:
        write_json(TASK_ROOT / "activated_generation/search_summary.json", summary)
        write_json(TASK_ROOT / "activated_generation/group_activation_counts.json", {"raw": raw_counts, "selected": registry_payload["group_counts"], "quota_case": case})
        write_json(TASK_ROOT / "registry/activated_registry_v1.json", registry_payload)
        write_csv(TASK_ROOT / "registry/activated_registry_v1.csv", selected)
        write_json(TASK_ROOT / "reference/reference_prelock_access_log.json", {"allowed_scope": "PHYSICAL_ADMISSIBILITY_ONLY", "future_outcome_read_count": 0, "access_count": len(access_rows), "accesses": access_rows})
    return summary


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--mode", choices=("smoke", "full"), required=True)
    args = parser.parse_args()
    limit = CANDIDATE_SEARCH_SMOKE_LIMIT if args.mode == "smoke" else CANDIDATE_SEARCH_LIMIT
    summary = run(args.mode, limit)
    print(summary["status"], summary["activated_candidate_generation_count"], summary["quota_case"])


if __name__ == "__main__":
    main()
