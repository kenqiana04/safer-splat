#!/usr/bin/env python3
"""Fail-closed raw-asset structural validation before frame/coordinate work."""
from __future__ import annotations

import argparse
from pathlib import Path

import numpy as np
from PIL import Image

from arkitscenes_common import atomic_json, sha256_file, tree_sha256


def images(path: Path) -> list[Path]:
    return sorted(item for item in path.rglob("*") if item.suffix.lower() in {".png", ".jpg", ".jpeg"})


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--task-root", type=Path, required=True)
    parser.add_argument("--candidate-root", type=Path, required=True)
    parser.add_argument("--video-id", required=True)
    args = parser.parse_args()
    root = args.candidate_root.resolve()
    task = args.task_root.resolve()
    needed = {
        "mesh": root / f"{args.video_id}_3dod_mesh.ply",
        "trajectory": root / "lowres_wide.traj",
        "confidence": root / "confidence",
        "depth": root / "lowres_depth",
        "rgb": root / "lowres_wide",
        "intrinsics": root / "lowres_wide_intrinsics",
    }
    existing = {name: path.exists() for name, path in needed.items()}
    result: dict[str, object] = {"video_id": args.video_id, "candidate_root": str(root), "exists": existing,
                                 "candidate_tree_sha256": tree_sha256(root) if root.is_dir() else None}
    status = "ASSET_VALIDATION_PASS"
    try:
        if not all(existing.values()):
            raise ValueError("required raw asset missing")
        rgb, depth, confidence = images(needed["rgb"]), images(needed["depth"]), images(needed["confidence"])
        intrinsics = sorted(item for item in needed["intrinsics"].rglob("*") if item.is_file())
        result.update({"rgb_count": len(rgb), "depth_count": len(depth), "confidence_count": len(confidence),
                       "intrinsics_count": len(intrinsics), "mesh_sha256": sha256_file(needed["mesh"]),
                       "trajectory_sha256": sha256_file(needed["trajectory"])})
        if not rgb or not depth or not confidence or not intrinsics:
            raise ValueError("empty required raw asset directory")
        first_depth = np.asarray(Image.open(depth[0]))
        first_confidence = np.asarray(Image.open(confidence[0]))
        first_rgb = np.asarray(Image.open(rgb[0]))
        values = np.unique(first_confidence)
        result.update({"first_rgb_shape": list(first_rgb.shape), "first_depth_shape": list(first_depth.shape),
                       "first_depth_dtype": str(first_depth.dtype), "first_confidence_shape": list(first_confidence.shape),
                       "first_confidence_dtype": str(first_confidence.dtype), "first_confidence_values": values.tolist()})
        if first_depth.dtype != np.uint16:
            raise ValueError("lowres_depth is not uint16 millimetres")
        if first_confidence.dtype != np.uint8 or not set(values.tolist()).issubset({0, 1, 2}):
            raise ValueError("confidence is not uint8 values subset 0/1/2")
        if not np.isfinite(first_depth).all() or first_rgb.ndim != 3:
            raise ValueError("unreadable RGB or depth data")
    except Exception as error:
        status = "BLOCKED_BY_ARKITSCENES_SCENE_PRECHECK"
        result["error"] = f"{type(error).__name__}: {error}"
    result["status"] = status
    atomic_json(task / "candidate_precheck" / f"asset_validation_{args.video_id}.json", result)
    print(status)
    return 0 if status == "ASSET_VALIDATION_PASS" else 2


if __name__ == "__main__":
    raise SystemExit(main())
