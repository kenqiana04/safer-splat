#!/usr/bin/env python3
"""Fail-closed validator for the independently checked surface-distance record."""

import argparse
import json
from pathlib import Path


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--record", type=Path, required=True)
    args = parser.parse_args()
    record = json.loads(args.record.read_text(encoding="utf-8"))
    passed = (
        record["status"] == "PASS_EXACT_POINT_TO_TRIANGLE_SURFACE_DISTANCE"
        and record["point_count"] >= 512
        and record["open3d_vs_trimesh_max_abs_difference_m"] <= 1e-6
        and record["nearest_vertex_substitution"] is False
        and record["all_finite"] is True
    )
    print("PASS_DISTANCE_ENGINE_VALIDATION" if passed else "FAIL_DISTANCE_ENGINE_VALIDATION")
    return 0 if passed else 2


if __name__ == "__main__":
    raise SystemExit(main())
