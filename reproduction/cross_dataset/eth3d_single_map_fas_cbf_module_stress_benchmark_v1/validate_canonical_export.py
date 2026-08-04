#!/usr/bin/env python3
"""Validate three fresh canonical exports and freeze their byte identity."""

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
    parser.add_argument("--exports", type=Path, nargs=3, required=True)
    parser.add_argument("--source-ply", type=Path, required=True)
    parser.add_argument("--expected-source-ply-sha256", required=True)
    parser.add_argument("--result", type=Path, required=True)
    args = parser.parse_args()

    manifests = [json.loads((root / "manifest.json").read_text(encoding="utf-8")) for root in args.exports]
    trees = [manifest["tree_sha256"] for manifest in manifests]
    manifest_shas = [sha256(root / "manifest.json") for root in args.exports]
    if len(set(trees)) != 1 or len(set(manifest_shas)) != 1:
        raise RuntimeError(f"fresh export identities differ: trees={trees}, manifests={manifest_shas}")
    source_ply_sha = sha256(args.source_ply)
    if source_ply_sha != args.expected_source_ply_sha256:
        raise RuntimeError("formal source PLY changed across export")

    root = args.exports[0]
    arrays = {
        name: np.load(root / name, mmap_mode="r")
        for name in (
            "means_world_m.npy", "log_scales.npy", "scales_linear_m.npy",
            "rotations_raw_wxyz.npy", "rotations_unit_wxyz.npy",
            "opacity_logits.npy", "opacity.npy", "features_dc.npy",
            "features_rest.npy", "colors_dc.npy", "source_index.npy",
        )
    }
    count = arrays["means_world_m.npy"].shape[0]
    finite = all(np.isfinite(value).all() for name, value in arrays.items() if name != "source_index.npy")
    scales_positive = bool((arrays["scales_linear_m.npy"] > 0).all())
    rotation_norms = np.linalg.norm(arrays["rotations_unit_wxyz.npy"].astype(np.float64), axis=1)
    rotations_valid = bool(np.all(np.isfinite(rotation_norms)) and np.max(np.abs(rotation_norms - 1.0)) <= 1e-5)
    opacity_valid = bool((arrays["opacity.npy"] > 0).all() and (arrays["opacity.npy"] < 1).all())
    source_index_exact = bool(np.array_equal(arrays["source_index.npy"], np.arange(count)))
    if not all((finite, scales_positive, rotations_valid, opacity_valid, source_index_exact, count > 0)):
        raise RuntimeError("canonical parameter gate failed")
    record = {
        "schema_version": 1,
        "status": "PASS_CANONICAL_EXPORT_THREE_FRESH_TREES",
        "fresh_export_count": 3,
        "tree_sha256": trees[0],
        "fresh_tree_sha256_values": trees,
        "manifest_sha256": manifest_shas[0],
        "fresh_manifest_sha256_values": manifest_shas,
        "source_ply_sha256_before_after": source_ply_sha,
        "gaussian_count": count,
        "finite": finite,
        "scales_positive": scales_positive,
        "rotations_valid": rotations_valid,
        "rotation_norm_max_error": float(np.max(np.abs(rotation_norms - 1.0))),
        "opacity_valid": opacity_valid,
        "source_index_exact": source_index_exact,
        "filtering_count": 0,
        "post_export_pruning_count": 0,
    }
    args.result.parent.mkdir(parents=True, exist_ok=True)
    args.result.write_text(
        json.dumps(record, indent=2, sort_keys=True) + "\n", encoding="utf-8"
    )
    print("CANONICAL_EXPORT_VALIDATION_PASS")
    print(json.dumps(record, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
