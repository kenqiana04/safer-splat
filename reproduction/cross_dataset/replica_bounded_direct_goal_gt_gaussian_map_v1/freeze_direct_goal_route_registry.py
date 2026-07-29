#!/usr/bin/env python3
from __future__ import annotations

import argparse
import hashlib
import json
from collections import defaultdict
from pathlib import Path

import numpy as np

from replica_mesh_collision_oracle import point_query, run_oracle, segment_query

RADIUS = 0.10
EPSILON = 0.01
CLEARANCE_MIN = RADIUS + 2 * EPSILON
STRATA = [("TIGHT", "SHORT"), ("TIGHT", "MEDIUM"), ("TIGHT", "LONG"),
          ("MODERATE", "SHORT"), ("MODERATE", "MEDIUM"), ("MODERATE", "LONG"),
          ("OPEN", "SHORT"), ("OPEN", "MEDIUM"), ("OPEN", "LONG")]


def sha(text: str) -> str:
    return hashlib.sha256(text.encode("utf-8")).hexdigest()


def clearance_stratum(gap: float) -> str | None:
    if 0.02 <= gap < 0.08:
        return "TIGHT"
    if 0.08 <= gap < 0.20:
        return "MODERATE"
    if gap >= 0.20:
        return "OPEN"
    return None


def length_stratum(length: float) -> str | None:
    if 0.40 <= length < 0.80:
        return "SHORT"
    if 0.80 <= length < 1.20:
        return "MEDIUM"
    if 1.20 <= length <= 2.00:
        return "LONG"
    return None


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--backend", type=Path, required=True)
    parser.add_argument("--mesh", type=Path, required=True)
    parser.add_argument("--input-identity", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    identity = json.loads(args.input_identity.read_text(encoding="utf-8"))
    locs = [{"id": row["id"], "p": np.asarray(row["camera_center_m"], dtype=np.float64)} for row in identity["camera_centers"]]
    point_rows = run_oracle(args.backend, args.mesh, [point_query(x["p"]) for x in locs], args.output.with_suffix(".endpoints.txt"))
    endpoint = {loc["id"]: {"distance": float(row[1]), "closest": [float(row[2]), float(row[3]), float(row[4])]} for loc, row in zip(locs, point_rows)}
    pre = []
    for i, a in enumerate(locs):
        for b in locs[i + 1:]:
            if endpoint[a["id"]]["distance"] < CLEARANCE_MIN or endpoint[b["id"]]["distance"] < CLEARANCE_MIN:
                continue
            length = float(np.linalg.norm(a["p"] - b["p"]))
            if not 0.40 <= length <= 2.00:
                continue
            direction = sha(f"REPLICA_DIRECT_GOAL_DIRECTION_V1:{a['id']}:{b['id']}")
            start, goal = (a, b) if int(direction[-1], 16) % 2 == 0 else (b, a)
            pre.append((start, goal, length, direction))
    rows = run_oracle(args.backend, args.mesh, [segment_query(a["p"], b["p"]) for a, b, _, _ in pre], args.output.with_suffix(".segments.txt"))
    buckets: dict[tuple[str, str], list[dict[str, object]]] = defaultdict(list)
    for (start, goal, length, direction), row in zip(pre, rows):
        distance = float(row[1]); gap = distance - RADIUS
        c_stratum, l_stratum = clearance_stratum(gap), length_stratum(length)
        if distance < CLEARANCE_MIN or c_stratum is None or l_stratum is None:
            continue
        route_hash = sha(f"REPLICA_DIRECT_GOAL_ROUTE_V1:{start['id']}:{goal['id']}")
        buckets[(c_stratum, l_stratum)].append({
            "route_id": route_hash, "start_id": start["id"], "goal_id": goal["id"],
            "start_m": start["p"].tolist(), "goal_m": goal["p"].tolist(), "length_m": length,
            "segment_mesh_distance_m": distance, "clearance_gap_m": gap,
            "clearance_stratum": c_stratum, "length_stratum": l_stratum,
            "direction_sha256": direction, "initial_velocity_m_per_s": [0, 0, 0], "goal_velocity_m_per_s": [0, 0, 0],
            "start_mesh_closest_point_m": endpoint[start["id"]]["closest"], "goal_mesh_closest_point_m": endpoint[goal["id"]]["closest"],
        })
    for values in buckets.values():
        values.sort(key=lambda x: str(x["route_id"]))
    selected: list[dict[str, object]] = []
    start_use: dict[str, int] = defaultdict(int); goal_use: dict[str, int] = defaultdict(int)
    cursor = {key: 0 for key in STRATA}
    while len(selected) < 100:
        progressed = False
        for key in STRATA:
            values = buckets.get(key, [])
            while cursor[key] < len(values):
                row = values[cursor[key]]; cursor[key] += 1
                start_id, goal_id = str(row["start_id"]), str(row["goal_id"])
                if start_use[start_id] >= 5 or goal_use[goal_id] >= 5:
                    continue
                selected.append(row); start_use[start_id] += 1; goal_use[goal_id] += 1; progressed = True
                break
            if len(selected) == 100:
                break
        if not progressed:
            break
    if len(selected) < 60:
        raise SystemExit("BLOCKED_BY_REPLICA_DIRECT_GOAL_ROUTE_REGISTRY_INSUFFICIENT")
    for index, row in enumerate(selected):
        row["execution_order"] = index
        row["subset"] = "diagnostic" if index < 20 else "formal"
    strata_counts = {f"{a}_{b}": len(buckets.get((a, b), [])) for a, b in STRATA}
    output = {
        "status": "PASS", "route_count": len(selected), "candidate_pair_count_before_mesh_segment_gate": len(pre),
        "route_generation_authority": "official_mesh_only", "navmesh_path_controller_count": 0, "gaussian_map_query_count": 0,
        "r_robot_m": RADIUS, "epsilon_base_m": EPSILON, "minimum_mesh_distance_m": CLEARANCE_MIN,
        "strata_candidate_counts": strata_counts, "start_usage": dict(sorted(start_use.items())), "goal_usage": dict(sorted(goal_use.items())),
        "routes": selected,
    }
    args.output.write_text(json.dumps(output, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    raw = args.output.read_bytes();
    output["registry_sha256"] = hashlib.sha256(raw).hexdigest()
    args.output.write_text(json.dumps(output, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(f"ROUTE_REGISTRY_PASS routes={len(selected)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
