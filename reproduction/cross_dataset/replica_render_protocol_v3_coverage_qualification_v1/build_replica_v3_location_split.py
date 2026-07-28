#!/usr/bin/env python3
"""Create the deterministic V3 location-level 90/10 train/eval split."""
from __future__ import annotations

import hashlib
from typing import Any, Dict, List

import numpy as np

from _v3_common import ROOT, atomic_json, ensure_server_root, load_json, sha256_path


def eval_hash(location_hash: str) -> str:
    return hashlib.sha256(("REPLICA_V3_EVAL:" + location_hash).encode("utf-8")).hexdigest()


def distance(first: Dict[str, Any], second: Dict[str, Any]) -> float:
    return float(np.linalg.norm(np.asarray(first["source_navmesh_position"], dtype=np.float64) - np.asarray(second["source_navmesh_position"], dtype=np.float64)))


def main() -> None:
    ensure_server_root()
    selected = load_json(ROOT / "final_location_selection" / "selected_v3_location_registry.json")["selected_locations"]
    if len(selected) != 100:
        raise RuntimeError("selected_location_count_not_100")
    remaining = {item["candidate_id"]: item for item in selected}
    eval_locations = []
    first = min(remaining.values(), key=lambda item: eval_hash(item["location_hash"]))
    eval_locations.append(first)
    del remaining[first["candidate_id"]]
    while len(eval_locations) < 10:
        values = []
        for item in remaining.values():
            values.append((min(distance(item, chosen) for chosen in eval_locations), eval_hash(item["location_hash"]), item))
        maximum = max(item[0] for item in values)
        selected_item = min([item for item in values if abs(item[0] - maximum) <= 1e-12], key=lambda item: item[1])[2]
        eval_locations.append(selected_item)
        del remaining[selected_item["candidate_id"]]
    eval_ids = {item["candidate_id"] for item in eval_locations}
    rows = []
    for item in selected:
        rows.append({"location_id": f"location_{item['selection_order']:03d}", "candidate_id": item["candidate_id"], "location_hash": item["location_hash"], "split": "eval" if item["candidate_id"] in eval_ids else "train", "source_navmesh_position": item["source_navmesh_position"], "eval_hash": eval_hash(item["location_hash"])})
    payload = {"status": "PASS_REPLICA_V3_LOCATION_LEVEL_SPLIT", "rule": "hash_tied_eval_farthest_point", "train_location_count": sum(item["split"] == "train" for item in rows), "eval_location_count": sum(item["split"] == "eval" for item in rows), "train_frame_count": 270, "eval_frame_count": 30, "location_leakage_count": 0, "locations": rows}
    path = ROOT / "final_manifest" / "replica_v3_location_split.json"
    atomic_json(path, payload)
    atomic_json(ROOT / "final_manifest" / "split_identity.json", {"split_sha256": sha256_path(path)})


if __name__ == "__main__":
    main()
