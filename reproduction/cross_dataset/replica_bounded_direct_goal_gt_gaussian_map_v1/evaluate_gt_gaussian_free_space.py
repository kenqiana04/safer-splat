#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
from pathlib import Path

import numpy as np

from canonical_gaussian_safety_map_adapter import CanonicalGaussianSafetyMapAdapter
from replica_mesh_collision_oracle import point_query, run_oracle


def stats(values: np.ndarray) -> dict[str, float]:
    return {"median": float(np.median(values)), "p95": float(np.percentile(values, 95)), "p99": float(np.percentile(values, 99)), "max": float(np.max(values))}


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--backend", type=Path, required=True)
    parser.add_argument("--mesh", type=Path, required=True)
    parser.add_argument("--routes", type=Path, required=True)
    parser.add_argument("--map-dir", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    adapter = CanonicalGaussianSafetyMapAdapter(args.map_dir)
    registry = json.loads(args.routes.read_text(encoding="utf-8"))
    rows = registry["routes"]
    retained = []; all_endpoint_points = []; free_points = []
    for route in rows:
        a = np.asarray(route["start_m"], dtype=np.float64); b = np.asarray(route["goal_m"], dtype=np.float64)
        endpoint_clearance, _ = adapter.point_clearance(np.stack((a, b)))
        segment_clearance = adapter.segment_clearance(a, b)
        keep = bool(np.all(endpoint_clearance > .11) and segment_clearance > .11)
        route["map_endpoint_clearance_m"] = endpoint_clearance.tolist(); route["map_segment_clearance_m"] = segment_clearance
        route["map_status"] = "RETAINED" if keep else "MAP_GEOMETRY_BLOCKED"; retained.append(keep)
        all_endpoint_points.extend((a, b))
        t = (np.arange(1000, dtype=np.float64) + .5) / 1000.0
        free_points.append(a[None, :] + t[:, None] * (b - a)[None, :])
    samples = np.concatenate(free_points, axis=0)
    mesh_rows = run_oracle(args.backend, args.mesh, [point_query(p) for p in samples], args.output.with_suffix(".mesh_samples.txt"))
    mesh_distance = np.asarray([float(row[1]) for row in mesh_rows])
    map_clearance, _ = adapter.point_clearance(samples)
    map_distance = map_clearance + adapter.sphere_radius_m
    intrusion = np.maximum(0.0, mesh_distance - map_distance)
    formal = np.asarray([r["subset"] == "formal" for r in rows], dtype=bool); kept = np.asarray(retained, dtype=bool)
    strata = {}
    for label in ("TIGHT", "MODERATE", "OPEN"):
        mask = np.asarray([r["clearance_stratum"] == label for r in rows], dtype=bool)
        strata[label] = {"total": int(mask.sum()), "retained": int((mask & kept).sum()), "retained_ratio": float((mask & kept).sum() / mask.sum()) if mask.any() else 0.0}
    result = {"status": "PASS" if kept.mean() >= .80 and kept[formal].mean() >= .80 and all(x["retained_ratio"] >= .50 for x in strata.values()) else "FAIL", "route_count": len(rows), "retained_count": int(kept.sum()), "retained_ratio": float(kept.mean()), "formal_retained_ratio": float(kept[formal].mean()), "strata": strata, "free_space_sample_count": int(len(samples)), "intrusion_m": stats(intrusion), "no_nonfinite": bool(np.isfinite(intrusion).all()), "routes": rows}
    args.output.write_text(json.dumps(result, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(result["status"])
    return 0 if result["status"] == "PASS" else 1


if __name__ == "__main__":
    raise SystemExit(main())
