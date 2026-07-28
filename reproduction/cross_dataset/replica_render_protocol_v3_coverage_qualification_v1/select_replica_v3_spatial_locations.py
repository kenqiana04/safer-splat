#!/usr/bin/env python3
"""Deterministically choose 100 spatially diverse Habitat-qualified V3 locations."""
from __future__ import annotations

import csv
import itertools
import math
from pathlib import Path
from typing import Any, Dict, List

import numpy as np

from _v3_common import ROOT, V1_MANIFEST, atomic_json, ensure_server_root, load_json, sha256_path


def distance(first: Dict[str, Any], second: Dict[str, Any]) -> float:
    return float(np.linalg.norm(np.asarray(first["source_navmesh_position"], dtype=np.float64) - np.asarray(second["source_navmesh_position"], dtype=np.float64)))


def main() -> None:
    ensure_server_root()
    pool = load_json(ROOT / "qualified_location_pool" / "qualified_location_pool_summary.json")["locations"]
    if len(pool) < 120:
        raise SystemExit("BLOCKED_BY_REPLICA_V3_INSUFFICIENT_HABITAT_QUALIFIED_LOCATION_POOL")
    remaining = {item["candidate_id"]: item for item in pool}
    selected = []
    first = min(remaining.values(), key=lambda item: item["location_hash"])
    selected.append({**first, "selection_order": 0, "selection_min_distance_m": None})
    del remaining[first["candidate_id"]]
    while len(selected) < 100:
        choices = []
        for item in remaining.values():
            minimum = min(distance(item, chosen) for chosen in selected)
            choices.append((minimum, item["location_hash"], item))
        maximum = max(item[0] for item in choices)
        contenders = [item for item in choices if abs(item[0] - maximum) <= 1e-12]
        chosen_distance, _, chosen = min(contenders, key=lambda item: item[1])
        if chosen_distance < .10:
            raise SystemExit("BLOCKED_BY_REPLICA_V3_SPATIAL_DIVERSITY_GATE")
        selected.append({**chosen, "selection_order": len(selected), "selection_min_distance_m": chosen_distance})
        del remaining[chosen["candidate_id"]]
    pairwise = [distance(left, right) for left, right in itertools.combinations(selected, 2)]
    cell_size = .5
    cells = {(math.floor(item["source_navmesh_position"][0] / cell_size), math.floor(item["source_navmesh_position"][2] / cell_size)) for item in selected}
    v1_locations = {}
    with V1_MANIFEST.open(encoding="utf-8", newline="") as stream:
        for row in csv.DictReader(stream):
            value = [float(row[f"source_navmesh_point_{axis}"]) for axis in "xyz"]
            v1_locations.setdefault(tuple(round(item, 8) for item in value), value)
    v1 = [{"source_navmesh_position": value} for value in v1_locations.values()]
    overlaps = sum(any(distance(item, old) < 1e-8 for old in v1) for item in selected)
    near_overlaps = sum(any(distance(item, old) < .10 for old in v1) for item in selected)
    payload = {"status": "PASS_REPLICA_V3_SPATIAL_SELECTION", "selection_rule": "hash_tied_greedy_farthest_point", "qualified_location_count": len(pool), "selected_location_count": len(selected), "final_minimum_location_separation_m": min(pairwise), "pairwise_distance_min_m": min(pairwise), "pairwise_distance_median_m": float(np.median(pairwise)), "pairwise_distance_max_m": max(pairwise), "selected_bbox": [[float(min(item["source_navmesh_position"][axis] for item in selected)) for axis in range(3)], [float(max(item["source_navmesh_position"][axis] for item in selected)) for axis in range(3)]], "qualified_pool_bbox": [[float(min(item["source_navmesh_position"][axis] for item in pool)) for axis in range(3)], [float(max(item["source_navmesh_position"][axis] for item in pool)) for axis in range(3)]], "spatial_grid_cell_size_m": cell_size, "unique_xz_grid_cell_count": len(cells), "v1_location_exact_overlap_count": overlaps, "v1_location_near_overlap_count_lt_0_10m": near_overlaps, "selected_locations": selected}
    path = ROOT / "final_location_selection" / "selected_v3_location_registry.json"
    atomic_json(path, payload)
    atomic_json(ROOT / "final_location_selection" / "selection_identity.json", {"selected_registry_sha256": sha256_path(path)})


if __name__ == "__main__":
    main()
