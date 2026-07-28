#!/usr/bin/env python3
"""Build the deterministic float64 location MST and shared mapping frame order."""
from __future__ import annotations

import hashlib
import json
import statistics
from collections import defaultdict

import numpy as np

from _common import ROOT, atomic_json, ensure_dirs, load_json, sha256_bytes


def h(location: str) -> str:
    return hashlib.sha256(f"REPLICA_MAPPING_FRONTEND_PILOT_V1:{location}".encode()).hexdigest()


def main() -> None:
    ensure_dirs(); registry_path = ROOT / "pilot_registry" / "replica_frontend_pilot_registry.json"; registry = load_json(registry_path)
    locations = registry["selected_location_ids"]; positions = {key: np.asarray(value, dtype=np.float64) for key, value in registry["selected_location_positions_m"].items()}
    root = min(locations, key=h); visited = {root}; edges = []
    while len(visited) < len(locations):
        candidates = []
        for left in sorted(visited, key=h):
            for right in sorted(set(locations) - visited, key=h):
                distance = float(np.linalg.norm(positions[left] - positions[right]))
                candidates.append((distance, min(h(left), h(right)), max(h(left), h(right)), left, right))
        distance, _, _, left, right = min(candidates); visited.add(right); edges.append({"a": left, "b": right, "distance_m": distance})
    adjacency: dict[str, list[tuple[float, str]]] = defaultdict(list)
    for edge in edges:
        adjacency[edge["a"]].append((edge["distance_m"], edge["b"])); adjacency[edge["b"]].append((edge["distance_m"], edge["a"]))
    preorder: list[str] = []
    def dfs(node: str, parent: str | None) -> None:
        preorder.append(node)
        for _, child in sorted(adjacency[node], key=lambda item: (item[0], h(item[1]))):
            if child != parent: dfs(child, node)
    dfs(root, None)
    mapping_by_location = {frame.split("_")[1] if False else frame: frame for frame in registry["mapping_frame_ids"]}
    # Preserve the frozen mapping view order (yaw 0 then -60) by matching manifest-derived prefixes in registry order.
    frame_to_location = {row["frame_id"]: row["location_id"] for row in load_json(__import__("_common").DATASET / "formal_camera_manifest_v3.json")["frames"]}
    mapping = [frame for location in preorder for frame in registry["mapping_frame_ids"] if frame_to_location[frame] == location]
    holdout = [frame for location in preorder for frame in registry["holdout_frame_ids"] if frame_to_location[frame] == location]
    consecutive = [float(np.linalg.norm(positions[right] - positions[left])) for left, right in zip(preorder, preorder[1:])]
    core = {"status": "PASS", "root_location_id": root, "mst_edges": edges, "total_mst_length_m": float(sum(edge["distance_m"] for edge in edges)), "median_edge_length_m": float(statistics.median(edge["distance_m"] for edge in edges)), "maximum_edge_length_m": float(max(edge["distance_m"] for edge in edges)), "location_preorder": preorder, "mapping_frame_order": mapping, "holdout_frame_order": holdout, "smoke_location_ids": preorder[:8], "smoke_mapping_frame_ids": [frame for location in preorder[:8] for frame in mapping if frame_to_location[frame] == location], "smoke_holdout_frame_ids": [frame for location in preorder[:8] for frame in holdout if frame_to_location[frame] == location], "consecutive_camera_distance_m": consecutive, "yaw_transition": ["0_to_-60"] * 30, "registry_selection_core_sha256": registry["registry_sha256"]}
    core["frame_order_sha256"] = sha256_bytes(json.dumps({"mapping": mapping, "holdout": holdout}, sort_keys=True, separators=(",", ":")).encode())
    if len(mapping) != 60 or len(holdout) != 30 or len(core["smoke_mapping_frame_ids"]) != 16 or len(core["smoke_holdout_frame_ids"]) != 8: raise SystemExit("PILOT_ORDER_COUNT_MISMATCH")
    atomic_json(ROOT / "pilot_registry" / "replica_frontend_map_only_order.json", core)
    registry["smoke_location_ids"] = preorder[:8]; registry["smoke_mapping_frame_ids"] = core["smoke_mapping_frame_ids"]; registry["smoke_holdout_frame_ids"] = core["smoke_holdout_frame_ids"]; registry["map_only_order_sha256"] = core["frame_order_sha256"]; registry["registry_finalization"] = "smoke subset deterministically derived before any frontend launch"; registry["registry_sha256"] = sha256_bytes(json.dumps({key: value for key, value in registry.items() if key != "registry_sha256"}, sort_keys=True, separators=(",", ":")).encode())
    atomic_json(registry_path, registry); print(core["frame_order_sha256"])


if __name__ == "__main__":
    main()
