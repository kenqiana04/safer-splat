#!/usr/bin/env python3
"""Generate and repeat-check V3 navmesh candidates without coverage filtering."""
from __future__ import annotations

import argparse
import math
from pathlib import Path
from typing import Any, Dict, List

import numpy as np

from _v3_common import NAVMESH, ROOT, SCENE_ROOT, atomic_json, ensure_server_root, load_json, location_hash, position_text, sha256_path, sha256_text


def _finite_point(value: Any) -> bool:
    return bool(np.isfinite(np.asarray(value, dtype=np.float64)).all())


def _record_samples() -> List[Dict[str, Any]]:
    import habitat_sim
    configuration = habitat_sim.SimulatorConfiguration()
    configuration.scene_id = str(SCENE_ROOT / "mesh.ply")
    configuration.gpu_device_id = 0
    configuration.enable_physics = False
    simulator = habitat_sim.Simulator(habitat_sim.Configuration(configuration, [habitat_sim.agent.AgentConfiguration()]))
    try:
        pathfinder = simulator.pathfinder
        if not pathfinder.load_nav_mesh(str(NAVMESH)):
            raise RuntimeError("official_navmesh_load_failed")
        pathfinder.seed(20260728)
        bounds = pathfinder.get_bounds()
        lower, upper = np.asarray(bounds[0], dtype=np.float64), np.asarray(bounds[1], dtype=np.float64)
        records: List[Dict[str, Any]] = []
        for index in range(2048):
            status = "ok"
            try:
                position = np.asarray(pathfinder.get_random_navigable_point(), dtype=np.float64)
                finite = _finite_point(position)
                navigable = bool(finite and pathfinder.is_navigable(position))
                snap = np.asarray(pathfinder.snap_point(position), dtype=np.float64) if finite else np.asarray((math.nan,) * 3)
                snap_finite = _finite_point(snap)
                snap_distance = float(np.linalg.norm(position - snap)) if finite and snap_finite else None
                in_bounds = bool(finite and np.all(position >= lower) and np.all(position <= upper))
                island = None
                try:
                    island = int(pathfinder.get_island(position))
                except (AttributeError, RuntimeError, TypeError):
                    island = None
            except Exception as error:  # retain exact raw-call outcome rather than retrying
                position = np.asarray((math.nan,) * 3)
                snap = np.asarray((math.nan,) * 3)
                finite = navigable = snap_finite = in_bounds = False
                snap_distance = None
                island = None
                status = "error:" + type(error).__name__
            records.append({
                "raw_sample_index": index,
                "position": [float(value) for value in position],
                "finite": finite,
                "navigable": navigable,
                "snap_position": [float(value) for value in snap],
                "snap_finite": snap_finite,
                "snap_distance_m": snap_distance,
                "island_index": island,
                "in_scene_bounds": in_bounds,
                "source_call_status": status,
                "scene_bounds": [[float(value) for value in lower], [float(value) for value in upper]],
            })
        return records
    finally:
        simulator.close()


def _unique(records: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    valid = []
    for record in records:
        if record["finite"] and record["navigable"] and record["snap_finite"] and record["in_scene_bounds"]:
            point = record["position"]
            digest = location_hash(point)
            valid.append({"raw_sample_index": record["raw_sample_index"], "position": point, "rounded_position": position_text(point), "location_hash": digest, "snap_distance_m": record["snap_distance_m"], "island_index": record["island_index"]})
    valid.sort(key=lambda item: (item["location_hash"], item["raw_sample_index"]))
    selected: List[Dict[str, Any]] = []
    for item in valid:
        point = np.asarray(item["position"], dtype=np.float64)
        if all(float(np.linalg.norm(point - np.asarray(kept["position"], dtype=np.float64))) >= 0.05 for kept in selected):
            selected.append(item)
    selected = selected[:1024]
    for index, item in enumerate(selected):
        item["candidate_id"] = f"candidate_{index:04d}"
    return selected


def _array_identity(items: List[Dict[str, Any]]) -> Dict[str, Any]:
    positions = [[item["location_hash"], item["rounded_position"]] for item in items]
    encoded = __import__("json").dumps(positions, separators=(",", ":"), ensure_ascii=True)
    return {"position_array_sha256": sha256_text(encoded), "location_hash_set_sha256": sha256_text("".join(sorted(item["location_hash"] for item in items))), "positions": positions}


def run_once(run_id: int) -> None:
    ensure_server_root()
    records = _record_samples()
    unique = _unique(records)
    raw_path = ROOT / "raw_navmesh_candidates" / f"raw_candidates_run{run_id}.json"
    inventory_path = ROOT / "candidate_locations" / f"candidate_inventory_run{run_id}.json"
    atomic_json(raw_path, {"run_id": run_id, "raw_call_count": len(records), "records": records, "raw_file_sha256": None})
    raw = load_json(raw_path)
    raw["raw_file_sha256"] = sha256_path(raw_path)
    atomic_json(raw_path, raw)
    atomic_json(inventory_path, {"run_id": run_id, "unique_candidate_locations": len(unique), "candidates": unique, "identity": _array_identity(unique)})


def compare() -> None:
    ensure_server_root()
    first = load_json(ROOT / "candidate_locations" / "candidate_inventory_run1.json")
    second = load_json(ROOT / "candidate_locations" / "candidate_inventory_run2.json")
    first_identity, second_identity = first["identity"], second["identity"]
    equal = first_identity == second_identity and first["candidates"] == second["candidates"]
    raw = load_json(ROOT / "raw_navmesh_candidates" / "raw_candidates_run1.json")
    accepted = sum(1 for record in raw["records"] if record["finite"] and record["navigable"] and record["snap_finite"] and record["in_scene_bounds"])
    status = "PASS_DETERMINISTIC_REPLICA_V3_NAVMESH_CANDIDATES"
    if len(first["candidates"]) < 400:
        status = "BLOCKED_BY_REPLICA_V3_INSUFFICIENT_NAVMESH_CANDIDATES"
    elif not equal:
        status = "BLOCKED_BY_REPLICA_V3_CANDIDATE_GENERATION_NONDETERMINISM"
    summary = {
        "status": status,
        "candidate_seed": 20260728,
        "raw_navmesh_sample_count": 2048,
        "finite_navigable_snap_valid_in_bounds_count": accepted,
        "unique_candidate_location_count": len(first["candidates"]),
        "maximum_unique_candidate_locations": 1024,
        "deduplication_radius_m": 0.05,
        "candidate_repeatability": equal,
        "candidate_position_array_sha256": first_identity["position_array_sha256"],
        "candidate_location_hash_set_sha256": first_identity["location_hash_set_sha256"],
        "raw_run1_sha256": sha256_path(ROOT / "raw_navmesh_candidates" / "raw_candidates_run1.json"),
        "raw_run2_sha256": sha256_path(ROOT / "raw_navmesh_candidates" / "raw_candidates_run2.json"),
        "candidate_inventory_server_only": str(ROOT / "candidate_locations" / "candidate_inventory_run1.json"),
    }
    atomic_json(ROOT / "raw_navmesh_candidates" / "raw_navmesh_candidate_summary.json", summary)
    atomic_json(ROOT / "candidate_locations" / "candidate_location_inventory.json", first)
    if status != "PASS_DETERMINISTIC_REPLICA_V3_NAVMESH_CANDIDATES":
        raise SystemExit(status)


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--run-id", type=int, choices=(1, 2))
    parser.add_argument("--compare", action="store_true")
    args = parser.parse_args()
    if args.compare == (args.run_id is not None):
        raise SystemExit("choose_exactly_one_of_run_id_or_compare")
    compare() if args.compare else run_once(args.run_id)
