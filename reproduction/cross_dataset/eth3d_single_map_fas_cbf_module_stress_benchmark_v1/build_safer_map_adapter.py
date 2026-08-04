#!/usr/bin/env python3
"""Freeze the read-only canonical-array contract consumed by SAFER/FAS-CBF."""

from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path

import numpy as np


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for chunk in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--canonical-root", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    root = args.canonical_root.resolve(strict=True)
    manifest = json.loads((root / "manifest.json").read_text(encoding="utf-8"))
    arrays = {
        "means": root / "means_world_m.npy",
        "scales": root / "scales_linear_m.npy",
        "rotations": root / "rotations_unit_wxyz.npy",
        "opacity": root / "opacity.npy",
        "colors": root / "colors_dc.npy",
        "source_index": root / "source_index.npy",
    }
    loaded = {name: np.load(path, mmap_mode="r") for name, path in arrays.items()}
    count = loaded["means"].shape[0]
    if any(value.shape[0] != count for value in loaded.values()):
        raise RuntimeError("SAFER adapter arrays do not share row identity")
    if not np.isfinite(loaded["means"]).all() or not np.isfinite(loaded["scales"]).all():
        raise RuntimeError("SAFER adapter geometry is nonfinite")
    if not (loaded["scales"] > 0).all():
        raise RuntimeError("SAFER adapter contains nonpositive scale")
    record = {
        "schema_version": 1,
        "status": "PASS_SAFER_CANONICAL_MAP_ADAPTER",
        "adapter_semantics": "READ_ONLY_ANISOTROPIC_ELLIPSOID_UNION",
        "canonical_root": str(root),
        "canonical_tree_sha256": manifest["tree_sha256"],
        "gaussian_count": count,
        "coordinate_frame": "ETH3D_DELIVERY_AREA_COLMAP_WORLD",
        "units": "meter",
        "quaternion_order": "wxyz",
        "covariance_semantics": "R @ diag(scales**2) @ R.T",
        "distance_semantics": "existing SAFER ball-to-ellipsoid signed squared-distance field",
        "array_contract": {
            name: {
                "path": str(path),
                "sha256": sha256(path),
                "shape": list(loaded[name].shape),
                "dtype": str(loaded[name].dtype),
            }
            for name, path in arrays.items()
        },
        "filtering_count": 0,
        "opacity_threshold": None,
        "scale_repair_count": 0,
        "frame_transform_count": 0,
        "core_code_modification_count": 0,
    }
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(
        json.dumps(record, indent=2, sort_keys=True) + "\n", encoding="utf-8"
    )
    print("SAFER_MAP_ADAPTER_PASS")
    print(json.dumps(record, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
