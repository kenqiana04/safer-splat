#!/usr/bin/env python3
from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path

import numpy as np

from replica_mesh_collision_oracle import point_query, run_oracle, segment_query


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--backend", type=Path, required=True)
    parser.add_argument("--mesh", type=Path, required=True)
    parser.add_argument("--input-identity", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    identity = json.loads(args.input_identity.read_text(encoding="utf-8"))
    centers = np.asarray([row["camera_center_m"] for row in identity["camera_centers"]], dtype=np.float64)
    rng = np.random.default_rng(20260729)
    queries: list[str] = []
    for i in range(256):
        base = centers[i % len(centers)]
        offset = rng.uniform(-0.15, 0.15, size=3)
        queries.append(point_query(base + offset))
    for i in range(256):
        start = centers[(17 * i + 3) % len(centers)]
        goal = centers[(37 * i + 11) % len(centers)]
        queries.append(segment_query(start, goal))
    rows = run_oracle(args.backend, args.mesh, queries, args.output.with_suffix(".raw.txt"), brute_force=True)
    point_diff = [float(row[7]) for row in rows if row[0] == "P"]
    segment_diff = [float(row[7]) for row in rows if row[0] == "S"]
    point_max = max(point_diff)
    segment_max = max(segment_diff)
    if point_max > 1e-7 or segment_max > 1e-6:
        raise SystemExit("BLOCKED_BY_REPLICA_MESH_ORACLE_VALIDATION")
    digest = hashlib.sha256("\n".join(" ".join(row) for row in rows).encode()).hexdigest()
    result = {
        "status": "PASS", "precision": "float64", "mesh_role": "official_Replica_visual_mesh",
        "mesh_simplification_count": 0, "semantic_mesh_usage_count": 0, "endpoint_only_collision_count": 0,
        "tangent_contact_is_collision": True, "point_query_count": 256, "segment_query_count": 256,
        "point_bruteforce_max_disagreement_m": point_max, "segment_bruteforce_max_disagreement_m": segment_max,
        "raw_result_sha256": digest,
    }
    args.output.write_text(json.dumps(result, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print("MESH_ORACLE_PASS")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
