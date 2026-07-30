#!/usr/bin/env python3
"""Read-only semantic audit of the frozen PR #65 progress field."""
from __future__ import annotations

import argparse
import csv
from pathlib import Path


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--csv", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    with args.csv.open(encoding="utf-8", newline="") as handle:
        rows = list(csv.DictReader(handle))
    progress = [float(row["progress_m"]) for row in rows if row["status"] != "MAP_GEOMETRY_BLOCKED"]
    if not progress:
        raise RuntimeError("PR65 progress audit requires map-admissible records")
    args.output.write_text(
        "# PR #65 Progress Field Semantic Audit\n\n"
        "`progress_m` is goal-distance reduction in metres: `||p0-goal|| - ||pT-goal||`. "
        "It is neither normalized progress nor path length. The frozen reported median 1.0137 therefore has unit metres.\n\n"
        "Recommended paper label: `goal_distance_reduction_m` (retain the old raw value unchanged).\n",
        encoding="utf-8", newline="\n")
    print(f"rows={len(rows)} map_admissible={len(progress)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
