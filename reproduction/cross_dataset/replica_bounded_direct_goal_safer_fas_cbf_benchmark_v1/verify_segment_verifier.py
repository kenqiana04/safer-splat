#!/usr/bin/env python3
"""Fresh-process exact segment verifier qualification against full brute force."""
from __future__ import annotations

import argparse
import json
from pathlib import Path

import numpy as np

from benchmark_core import FineSphereMap, atomic_json, sha256_json


def main() -> int:
    parser = argparse.ArgumentParser(); parser.add_argument("--root", type=Path, required=True); parser.add_argument("--tag", required=True)
    args = parser.parse_args(); root = args.root.resolve()
    config = json.loads((root / "frozen_inputs.json").read_text(encoding="utf-8"))
    routes = json.loads(Path(config["route_registry_path"]).read_text(encoding="utf-8"))["routes"]
    rng = np.random.default_rng(20260730)
    segments: list[tuple[np.ndarray, np.ndarray]] = []
    for route in routes:
        segments.append((np.asarray(route["start_m"], dtype=np.float64), np.asarray(route["goal_m"], dtype=np.float64)))
    while len(segments) < 256:
        first, second = rng.integers(0, len(routes), size=2)
        a = np.asarray(routes[int(first)]["start_m"], dtype=np.float64)
        b = np.asarray(routes[int(second)]["goal_m"], dtype=np.float64)
        mix_a, mix_b = rng.random(), rng.random()
        segments.append((a + mix_a * (b-a), a + mix_b * (b-a)))
    map_geometry = FineSphereMap(Path(config["map_dir"]))
    rows = []
    maximum = 0.0
    for index, (start, end) in enumerate(segments):
        exact, _, candidate_count = map_geometry.exact_segment_cg(start, end)
        brute = map_geometry.brute_segment_cg(start, end)
        error = abs(exact - brute); maximum = max(maximum, error)
        rows.append({"index": index, "exact_cg": exact, "brute_cg": brute, "abs_error": error,
                     "branch_bound_candidates": candidate_count})
    output = {"tag": args.tag, "segment_count": len(rows), "max_abs_error_m": maximum,
              "status": "PASS" if maximum <= 1e-6 else "FAIL", "rows": rows}
    output["result_sha256"] = sha256_json(output)
    path = root / "preflight" / f"segment_verifier_{args.tag}.json"; atomic_json(path, output)
    print(json.dumps({"status": output["status"], "max_abs_error_m": maximum, "output": str(path)}, sort_keys=True))
    return 0 if output["status"] == "PASS" else 1


if __name__ == "__main__":
    raise SystemExit(main())
