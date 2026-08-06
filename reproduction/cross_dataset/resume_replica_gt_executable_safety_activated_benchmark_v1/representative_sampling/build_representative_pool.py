#!/usr/bin/env python3
"""Select the method-independent representative holdout by frozen strata and hashes."""
from __future__ import annotations

import collections
import math
import sys
from pathlib import Path
from typing import Any

import numpy as np

TASK_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(TASK_ROOT))

from common import read_json, sha256_json, write_csv, write_json
from runtime_core import ReplicaMeshOracle, ReplicaRuntime, physically_admissible, representative_candidates
from task_config import (
    MAP_ROOT, MESH_ORACLE, REFERENCE_MESH, REPRESENTATIVE_TARGET,
    ROUTE_REGISTRY, TASK_ROOT, V_BOUND,
)


def point_key(point: list[float]) -> str:
    return sha256_json([float(value) for value in point])


def stratum(record: dict[str, Any]) -> tuple[str, ...]:
    return (
        str(record["route_id"]), str(record["source_type"]),
        f"{float(record['velocity_magnitude']):.3f}",
        str(record["spatial_quartile"]),
        "ZERO" if record["zero_velocity"] else "NONZERO",
    )


def balanced_select(records: list[dict[str, Any]], target: int) -> list[dict[str, Any]]:
    buckets: dict[tuple[str, ...], list[dict[str, Any]]] = collections.defaultdict(list)
    for record in records:
        buckets[stratum(record)].append(record)
    for values in buckets.values():
        values.sort(key=lambda item: item["candidate_id"])
    # Canonical hash orders strata, avoiding route-list order as a hidden score.
    keys = sorted(buckets, key=lambda key: sha256_json(list(key)))
    selected = []
    while len(selected) < target:
        progressed = False
        for key in keys:
            if buckets[key] and len(selected) < target:
                selected.append(buckets[key].pop(0))
                progressed = True
        if not progressed:
            break
    return selected


def main() -> None:
    routes = read_json(Path(ROUTE_REGISTRY))["routes"]
    candidates = representative_candidates(routes)
    runtime = ReplicaRuntime(Path(MAP_ROOT))
    oracle = ReplicaMeshOracle(Path(MESH_ORACLE), Path(REFERENCE_MESH), TASK_ROOT / "runtime_work/prelock_reference")
    unique_points = {point_key(item["position_m"]): np.asarray(item["position_m"], dtype=np.float64) for item in candidates}
    unique_goals = {point_key(item["goal_m"]): np.asarray(item["goal_m"], dtype=np.float64) for item in candidates}
    point_distances = dict(zip(unique_points, oracle.points(unique_points.values(), "representative_starts")))
    goal_distances = dict(zip(unique_goals, oracle.points(unique_goals.values(), "representative_goals")))
    accesses = [
        {"cohort": "REPRESENTATIVE_HOLDOUT", "access": "START_POINT_PHYSICAL_ADMISSIBILITY", "point_sha256": key, "distance_m": value, "allowed_fields_only": True}
        for key, value in point_distances.items()
    ] + [
        {"cohort": "REPRESENTATIVE_HOLDOUT", "access": "GOAL_POINT_PHYSICAL_ADMISSIBILITY", "point_sha256": key, "distance_m": value, "allowed_fields_only": True}
        for key, value in goal_distances.items()
    ]
    admissible = []
    map_unavailable = 0
    for item in candidates:
        p_distance = point_distances[point_key(item["position_m"])]
        g_distance = goal_distances[point_key(item["goal_m"])]
        finite = all(math.isfinite(float(value)) for value in (*item["position_m"], *item["velocity_m_per_s"], *item["goal_m"]))
        velocity_valid = max(abs(float(value)) for value in item["velocity_m_per_s"]) <= V_BOUND + 1.0e-12
        map_query = runtime.point_result(np.asarray(item["position_m"], dtype=np.float64))
        map_valid = map_query.status.value == "FINITE"
        map_unavailable += int(not map_valid)
        if finite and velocity_valid and map_valid and physically_admissible(p_distance, g_distance):
            value = dict(item)
            value.update({
                "cohort": "REPRESENTATIVE_HOLDOUT",
                "group": None,
                "state_id": item["candidate_id"],
                "physical_start_clearance_m": p_distance,
                "physical_goal_clearance_m": g_distance,
                "selection_stage_predicate_count": 0,
                "selection_method_run_count": 0,
                "selection_future_reference_outcome_count": 0,
                "selection_progress_read_count": 0,
                "selection_runtime_input_count": 0,
            })
            value["registry_record_sha256"] = sha256_json(value)
            admissible.append(value)
    selected = balanced_select(admissible, min(REPRESENTATIVE_TARGET, len(admissible)))
    selected.sort(key=lambda item: item["state_id"])
    registry = {
        "registry_id": "REPLICA_GT_EXECUTABLE_SAFETY_REPRESENTATIVE_HOLDOUT_REGISTRY_V1",
        "cohort": "REPRESENTATIVE_HOLDOUT",
        "selection_locked": False,
        "pool_shortfall": len(admissible) < REPRESENTATIVE_TARGET,
        "state_count": len(selected),
        "states": selected,
    }
    registry["registry_content_sha256"] = sha256_json(registry)
    write_json(TASK_ROOT / "registry/representative_holdout_registry_v1.json", registry)
    write_csv(TASK_ROOT / "registry/representative_holdout_registry_v1.csv", selected)
    write_json(TASK_ROOT / "representative_sampling/pool_summary.json", {
        "status": "PASS_REPRESENTATIVE_METHOD_INDEPENDENT_SELECTION",
        "candidate_pool_count": len(candidates),
        "physical_and_map_valid_count": len(admissible),
        "map_unavailable_count": map_unavailable,
        "representative_registry_count": len(selected),
        "pool_shortfall": len(admissible) < REPRESENTATIVE_TARGET,
        "stage_predicate_selection_count": 0,
        "method_selection_run_count": 0,
        "future_reference_outcome_selection_count": 0,
        "progress_selection_count": 0,
        "runtime_selection_count": 0,
    })
    log_path = TASK_ROOT / "reference/reference_prelock_access_log.json"
    prior = read_json(log_path) if log_path.exists() else {"allowed_scope": "PHYSICAL_ADMISSIBILITY_ONLY", "future_outcome_read_count": 0, "accesses": []}
    prior["accesses"].extend(accesses)
    prior["access_count"] = len(prior["accesses"])
    prior["future_outcome_read_count"] = 0
    write_json(log_path, prior)
    print("PASS_REPRESENTATIVE_METHOD_INDEPENDENT_SELECTION", len(candidates), len(admissible), len(selected))


if __name__ == "__main__":
    main()
