#!/usr/bin/env python3
from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path

import numpy as np

from replica_mesh_collision_oracle import point_query, run_oracle


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--backend", type=Path, required=True)
    parser.add_argument("--mesh", type=Path, required=True)
    parser.add_argument("--routes", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    routes = json.loads(args.routes.read_text(encoding="utf-8"))["routes"]
    unique: dict[str, dict[str, object]] = {}
    for route in routes:
        unique.setdefault(str(route["start_id"]), route)
    chosen = []
    for start_id in sorted(unique, key=lambda x: hashlib.sha256(f"REPLICA_START_SAFE_V1:{x}".encode()).hexdigest()):
        route = unique[start_id]
        p = np.asarray(route["start_m"], dtype=np.float64)
        q = np.asarray(route["start_mesh_closest_point_m"], dtype=np.float64)
        n = p - q
        length = float(np.linalg.norm(n))
        if length <= 1e-12:
            continue
        n /= length
        candidates = [("NEAR_SAFE", 0.105), ("CONTACT", 0.100), ("UNSAFE", 0.095)]
        points = [q + n * distance for _, distance in candidates]
        values = run_oracle(args.backend, args.mesh, [point_query(x) for x in points], args.output.with_suffix(f".{len(chosen):02d}.txt"))
        measured = [float(row[1]) for row in values]
        if any(abs(value - target) > 1e-5 for value, (_, target) in zip(measured, candidates)):
            continue
        for (label, target), point, value in zip(candidates, points, measured):
            chosen.append({"source_start_id": start_id, "classification": label, "position_m": point.tolist(), "velocity_m_per_s": [0, 0, 0], "target_center_to_mesh_distance_m": target, "verified_center_to_mesh_distance_m": value})
        if len(chosen) == 30:
            break
    if len(chosen) != 30:
        raise SystemExit("BLOCKED_BY_REPLICA_DIRECT_GOAL_ROUTE_REGISTRY_INSUFFICIENT")
    result = {"status": "PASS", "state_count": 30, "near_safe_count": 10, "contact_count": 10, "unsafe_count": 10, "gaussian_map_query_count": 0, "states": chosen}
    args.output.write_text(json.dumps(result, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    result["registry_sha256"] = hashlib.sha256(args.output.read_bytes()).hexdigest()
    args.output.write_text(json.dumps(result, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print("START_SAFE_REGISTRY_PASS")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
