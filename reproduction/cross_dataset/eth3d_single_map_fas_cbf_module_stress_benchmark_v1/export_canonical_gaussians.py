#!/usr/bin/env python3
"""Deterministically export every formal 3DGS Gaussian to canonical arrays."""

from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path

import numpy as np
from plyfile import PlyData


SH_C0 = 0.28209479177387814


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for chunk in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def write_npy(path: Path, value: np.ndarray) -> None:
    with path.open("wb") as stream:
        np.lib.format.write_array(stream, np.ascontiguousarray(value), allow_pickle=False)


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--source-ply", type=Path, required=True)
    parser.add_argument("--source-checkpoint", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--source-commit", required=True)
    parser.add_argument("--seed", type=int, required=True)
    args = parser.parse_args()
    if args.output.exists():
        raise RuntimeError(f"fresh export output already exists: {args.output}")
    args.output.mkdir(parents=True)

    vertex = PlyData.read(args.source_ply)["vertex"].data
    names = set(vertex.dtype.names or ())
    required = {
        "x", "y", "z", "opacity",
        "scale_0", "scale_1", "scale_2",
        "rot_0", "rot_1", "rot_2", "rot_3",
        "f_dc_0", "f_dc_1", "f_dc_2",
    }
    if not required.issubset(names):
        raise RuntimeError(f"formal PLY properties missing: {sorted(required - names)}")

    def columns(prefix: str) -> list[str]:
        return sorted(
            (name for name in names if name.startswith(prefix)),
            key=lambda name: int(name.rsplit("_", 1)[1]),
        )

    means = np.stack([vertex[name] for name in ("x", "y", "z")], axis=1).astype("<f4")
    log_scales = np.stack([vertex[name] for name in columns("scale_")], axis=1).astype("<f4")
    scales = np.exp(log_scales.astype(np.float64)).astype("<f4")
    rotations_raw = np.stack([vertex[name] for name in columns("rot_")], axis=1).astype("<f4")
    rotation_norm = np.linalg.norm(rotations_raw.astype(np.float64), axis=1, keepdims=True)
    rotations_unit = (rotations_raw.astype(np.float64) / rotation_norm).astype("<f4")
    opacity_logits = np.asarray(vertex["opacity"], dtype="<f4").reshape(-1, 1)
    opacity = (1.0 / (1.0 + np.exp(-opacity_logits.astype(np.float64)))).astype("<f4")
    features_dc = np.stack([vertex[name] for name in columns("f_dc_")], axis=1).astype("<f4")
    features_rest = np.stack([vertex[name] for name in columns("f_rest_")], axis=1).astype("<f4")
    colors_dc = np.clip(SH_C0 * features_dc.astype(np.float64) + 0.5, 0.0, 1.0).astype("<f4")
    source_index = np.arange(means.shape[0], dtype="<i8")

    arrays = {
        "means_world_m.npy": means,
        "log_scales.npy": log_scales,
        "scales_linear_m.npy": scales,
        "rotations_raw_wxyz.npy": rotations_raw,
        "rotations_unit_wxyz.npy": rotations_unit,
        "opacity_logits.npy": opacity_logits,
        "opacity.npy": opacity,
        "features_dc.npy": features_dc,
        "features_rest.npy": features_rest,
        "colors_dc.npy": colors_dc,
        "source_index.npy": source_index,
    }
    for filename, value in arrays.items():
        write_npy(args.output / filename, value)

    metadata = {
        "schema_version": 1,
        "source_frontend": "OFFICIAL_3DGS_COLMAP_RGB_ONLY",
        "source_commit": args.source_commit,
        "source_iteration": 30000,
        "source_seed": args.seed,
        "source_ply_sha256": sha256(args.source_ply),
        "source_checkpoint_sha256": sha256(args.source_checkpoint),
        "coordinate_frame": "ETH3D_DELIVERY_AREA_COLMAP_WORLD",
        "units": "meter",
        "quaternion_order": "wxyz",
        "scale_representation": "linear_principal_axis_standard_deviation_meter",
        "opacity_representation": "sigmoid_of_official_logit",
        "sh_degree": 3,
        "gaussian_count": int(means.shape[0]),
        "row_order": "unchanged_from_official_iteration_30000_ply",
        "filtering_count": 0,
        "post_export_pruning_count": 0,
        "frame_transform_count": 0,
        "scale_repair_count": 0,
    }
    metadata_path = args.output / "metadata.json"
    metadata_path.write_text(
        json.dumps(metadata, indent=2, sort_keys=True) + "\n", encoding="utf-8"
    )
    payload_paths = sorted([metadata_path, *(args.output / name for name in arrays)])
    records = [
        {
            "path": path.name,
            "sha256": sha256(path),
            "size": path.stat().st_size,
            "dtype": str(np.load(path, mmap_mode="r").dtype) if path.suffix == ".npy" else None,
            "shape": list(np.load(path, mmap_mode="r").shape) if path.suffix == ".npy" else None,
        }
        for path in payload_paths
    ]
    tree_payload = "".join(f"{item['path']}\0{item['sha256']}\0{item['size']}\n" for item in records)
    tree_sha256 = hashlib.sha256(tree_payload.encode("utf-8")).hexdigest()
    manifest = {
        "schema_version": 1,
        "status": "PASS_CANONICAL_EXPORT",
        "tree_sha256": tree_sha256,
        "files": records,
    }
    manifest_path = args.output / "manifest.json"
    manifest_path.write_text(
        json.dumps(manifest, indent=2, sort_keys=True) + "\n", encoding="utf-8"
    )
    print("CANONICAL_EXPORT_PASS")
    print(json.dumps({"gaussian_count": means.shape[0], "tree_sha256": tree_sha256, "manifest_sha256": sha256(manifest_path)}, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
