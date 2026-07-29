#!/usr/bin/env python3
from __future__ import annotations

import argparse
import hashlib
import json
import subprocess
from pathlib import Path

import numpy as np


PROFILES = {"COARSE": 0.08, "MEDIUM": 0.04, "FINE": 0.02}


def file_sha(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--backend", type=Path, required=True)
    parser.add_argument("--mesh", type=Path, required=True)
    parser.add_argument("--profile", choices=sorted(PROFILES), required=True)
    parser.add_argument("--output-dir", type=Path, required=True)
    args = parser.parse_args()
    args.output_dir.mkdir(parents=True, exist_ok=True)
    subprocess.run([str(args.backend), str(args.mesh), str(PROFILES[args.profile]), str(args.output_dir)], check=True)
    raw = json.loads((args.output_dir / "voxelizer_raw_summary.json").read_text(encoding="utf-8"))
    names = ["means_world_m.npy", "scales_linear_m.npy", "quaternions_wxyz.npy", "opacities_probability.npy", "colors_rgb.npy", "voxel_indices_int64.npy"]
    arrays = {name: np.load(args.output_dir / name, mmap_mode="r") for name in names}
    count = int(arrays["means_world_m.npy"].shape[0])
    payload_bytes = sum((args.output_dir / name).stat().st_size for name in names)
    scale = np.asarray(arrays["scales_linear_m.npy"])
    quat = np.asarray(arrays["quaternions_wxyz.npy"])
    idx = np.asarray(arrays["voxel_indices_int64.npy"])
    resource = {
        "gaussian_count_positive": count > 0,
        "gaussian_count": count,
        "gaussian_count_limit": 2_500_000,
        "payload_bytes": payload_bytes,
        "payload_limit_bytes": 4 * 1024**3,
        "finite_arrays": bool(np.isfinite(scale).all() and np.isfinite(quat).all()),
        "positive_scales": bool((scale > 0).all()),
        "normalized_quaternion_max_abs_error": float(np.max(np.abs(np.linalg.norm(quat, axis=1) - 1.0))),
        "duplicate_voxel_count": int(idx.shape[0] - np.unique(idx, axis=0).shape[0]),
    }
    resource["status"] = "PASS" if all((resource["gaussian_count_positive"], count <= resource["gaussian_count_limit"], payload_bytes <= resource["payload_limit_bytes"], resource["finite_arrays"], resource["positive_scales"], resource["duplicate_voxel_count"] == 0, resource["normalized_quaternion_max_abs_error"] <= 1e-6, raw["source_primitive_loss"] == 0)) else "FAIL"
    result = {
        "status": resource["status"], "profile": args.profile, "voxel_size_m": PROFILES[args.profile],
        "construction": "CONSERVATIVE_SURFACE_VOXEL_GAUSSIAN_MAP", "full_official_mesh": True,
        "route_cropped": False, "controller_dependent": False, "sphere_scale_semantics": "linear_m",
        "opacity_semantics": "probability", "color_fallback": [0.5, 0.5, 0.5], "raw": raw,
        "canonical_arrays": {name: {"sha256": file_sha(args.output_dir / name), "bytes": (args.output_dir / name).stat().st_size, "shape": list(arrays[name].shape), "dtype": str(arrays[name].dtype)} for name in names},
        "canonical_tree_sha256": hashlib.sha256("\n".join(f"{name}:{file_sha(args.output_dir / name)}" for name in names).encode()).hexdigest(),
        "resource": resource,
    }
    (args.output_dir / "profile_build_summary.json").write_text(json.dumps(result, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(f"PROFILE_BUILD_{result['status']} count={count}")
    return 0 if result["status"] == "PASS" else 3


if __name__ == "__main__":
    raise SystemExit(main())
