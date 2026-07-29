#!/usr/bin/env python3
"""Aggregate three fresh static G0 probes against the frozen four-scene reference."""
from __future__ import annotations

import argparse
import hashlib
import json
import statistics
from pathlib import Path


def file_sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--profile", required=True)
    parser.add_argument("--official-reference", type=Path, required=True)
    parser.add_argument("--run", type=Path, action="append", required=True)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    if len(args.run) != 3:
        raise SystemExit("exactly three independent run JSON files are required")

    runs = [json.loads(path.read_text(encoding="utf-8")) for path in args.run]
    reference = json.loads(args.official_reference.read_text(encoding="utf-8"))
    official = [
        item for item in reference["scenes"]
        if item.get("status") == "OFFICIAL_SCENE_READY_FOR_MULTISCENE_BENCHMARK"
    ]
    runtimes = [float(item["runtime_seconds"]) for item in official]
    active = [item["active_index_sha256"] for item in runs]
    maps = [item["canonical_means_sha256"] for item in runs]
    run_seconds = [float(item["runtime_s"]) for item in runs]
    median_s = statistics.median(run_seconds)
    slowest_s = max(runtimes)
    limit_s = 2.0 * slowest_s
    checks = {
        "fresh_repeat_count_is_three": len(runs) == 3,
        "official_ready_scene_count_is_four": len(official) == 4,
        "all_runs_pass": all(item["status"] == "PASS" for item in runs),
        "active_gaussian_indices_repeatable": len(set(active)) == 1,
        "canonical_map_sha_repeatable": len(set(maps)) == 1,
        "all_no_map_mutation": all(item["map_mutation_count"] == 0 for item in runs),
        "all_peak_gpu_le_12_gib": all(item["peak_gpu_bytes"] <= 12 * 1024**3 for item in runs),
        "median_runtime_le_two_x_official_slowest": median_s <= limit_s,
    }
    passed = all(checks.values())
    result = {
        "status": "PASS" if passed else "FAIL",
        "profile": args.profile,
        "checks": checks,
        "per_run": [
            {
                "path": str(path),
                "sha256": file_sha256(path),
                "runtime_s": item["runtime_s"],
                "peak_gpu_bytes": item["peak_gpu_bytes"],
                "active_index_sha256": item["active_index_sha256"],
                "canonical_means_sha256": item["canonical_means_sha256"],
            }
            for path, item in zip(args.run, runs)
        ],
        "median_runtime_s": median_s,
        "p95_runtime_s": max(run_seconds),
        "official_reference_path": str(args.official_reference),
        "official_reference_sha256": file_sha256(args.official_reference),
        "official_ready_scene_runtime_s": runtimes,
        "official_four_scene_slowest_runtime_s": slowest_s,
        "runtime_limit_s": limit_s,
        "active_index_sha256": active[0],
        "canonical_means_sha256": maps[0],
    }
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(result, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(f"GT_GAUSSIAN_SAFER_G0_{result['status']} profile={args.profile}")
    return 0 if passed else 3


if __name__ == "__main__":
    raise SystemExit(main())
