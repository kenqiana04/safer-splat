#!/usr/bin/env python3
"""Compare two fresh canonical Gaussian-map builds without reading a working tree."""
from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path


ARRAY_NAMES = (
    "means_world_m.npy",
    "scales_linear_m.npy",
    "quaternions_wxyz.npy",
    "opacities_probability.npy",
    "colors_rgb.npy",
    "voxel_indices_int64.npy",
)


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--profile", required=True)
    parser.add_argument("--build-a", type=Path, required=True)
    parser.add_argument("--build-b", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()

    checks: dict[str, dict[str, object]] = {}
    for name in ARRAY_NAMES:
        a, b = args.build_a / name, args.build_b / name
        sha_a, sha_b = sha256(a), sha256(b)
        checks[name] = {
            "build_a_sha256": sha_a,
            "build_b_sha256": sha_b,
            "identical": sha_a == sha_b,
        }
    summary_a = json.loads((args.build_a / "profile_build_summary.json").read_text(encoding="utf-8"))
    summary_b = json.loads((args.build_b / "profile_build_summary.json").read_text(encoding="utf-8"))
    tree_a = summary_a["canonical_tree_sha256"]
    tree_b = summary_b["canonical_tree_sha256"]
    passed = all(bool(value["identical"]) for value in checks.values()) and tree_a == tree_b
    result = {
        "status": "PASS" if passed else "FAIL",
        "profile": args.profile,
        "fresh_builds": 2,
        "build_a_canonical_tree_sha256": tree_a,
        "build_b_canonical_tree_sha256": tree_b,
        "canonical_tree_identical": tree_a == tree_b,
        "array_checks": checks,
        "gaussian_count_a": summary_a["resource"]["gaussian_count"],
        "gaussian_count_b": summary_b["resource"]["gaussian_count"],
    }
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(result, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(f"MAP_DETERMINISM_{result['status']} profile={args.profile}")
    return 0 if passed else 3


if __name__ == "__main__":
    raise SystemExit(main())
