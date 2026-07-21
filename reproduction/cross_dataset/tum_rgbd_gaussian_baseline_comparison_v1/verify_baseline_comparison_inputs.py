"""Freeze the exact PR #38 parser split into a portable RGB-D frame registry."""
from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path


EXPECTED_TRANSFORMS = "b6a685f4b1a5b2ff3bb9b389c63a138a58119b19dd5cb6d7f671282aeecad29a"


def sha256(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as f:
        for block in iter(lambda: f.read(1024 * 1024), b""):
            h.update(block)
    return h.hexdigest()


def split_paths(summary: dict) -> list[tuple[Path, Path]]:
    frames = summary.get("frames", [])
    return [(Path(x["image"]), Path(x["depth"])) for x in frames]


def main() -> None:
    p = argparse.ArgumentParser()
    p.add_argument("--transforms", type=Path, required=True)
    p.add_argument("--train-summary", type=Path, required=True)
    p.add_argument("--eval-summary", type=Path, required=True)
    p.add_argument("--registry", type=Path, required=True)
    p.add_argument("--summary", type=Path, required=True)
    args = p.parse_args()
    if sha256(args.transforms) != EXPECTED_TRANSFORMS:
        raise RuntimeError("TRANSFORMS_SHA_MISMATCH")
    transforms = json.loads(args.transforms.read_text(encoding="utf-8"))
    train_summary, eval_summary = (json.loads(x.read_text(encoding="utf-8")) for x in (args.train_summary, args.eval_summary))
    train_paths, eval_paths = split_paths(train_summary), split_paths(eval_summary)
    if len(transforms["frames"]) != 300 or len(train_paths) != 240 or len(eval_paths) != 60:
        raise RuntimeError("FRAME_COUNT_CONTRACT_MISMATCH")
    by_image = {str(Path(frame["file_path"]).name): (idx, frame) for idx, frame in enumerate(transforms["frames"])}
    seen, groups = set(), []
    for label, pairs in (("train", train_paths), ("eval", eval_paths)):
        records = []
        for image, depth in pairs:
            key = image.name
            if key not in by_image:
                raise RuntimeError(f"IMAGE_NOT_IN_TRANSFORMS:{key}")
            frame_index, frame = by_image[key]
            if frame_index in seen:
                raise RuntimeError(f"SPLIT_OVERLAP:{frame_index}")
            seen.add(frame_index)
            expected_depth = Path(frame["depth_file_path"]).name
            if expected_depth != depth.name:
                raise RuntimeError(f"DEPTH_PAIR_MISMATCH:{key}")
            records.append({"frame_index": frame_index, "image": str(image), "depth": str(depth),
                            "rgb_sha256": sha256(image), "depth_sha256": sha256(depth),
                            "transform_matrix": frame["transform_matrix"]})
        groups.append(records)
    if len(seen) != 300:
        raise RuntimeError("SPLIT_NOT_EXHAUSTIVE")
    intrinsics = {k: transforms[k] for k in ("fl_x", "fl_y", "cx", "cy", "w", "h")}
    train_records, eval_records = groups
    registry = {"status": "PASS", "transforms_path": str(args.transforms), "transforms_sha256": EXPECTED_TRANSFORMS,
                "depth_scale": 0.0002, "intrinsics": intrinsics, "total_frames": 300,
                "train_indices": [x["frame_index"] for x in train_records], "eval_indices": [x["frame_index"] for x in eval_records],
                "train_frames": train_records, "eval_frames": eval_records}
    registry["train_indices_sha256"] = hashlib.sha256("\n".join(map(str, registry["train_indices"])).encode()).hexdigest()
    registry["eval_indices_sha256"] = hashlib.sha256("\n".join(map(str, registry["eval_indices"])).encode()).hexdigest()
    args.registry.write_text(json.dumps(registry, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    compact = {k: registry[k] for k in ("status", "transforms_path", "transforms_sha256", "depth_scale", "intrinsics", "total_frames", "train_indices_sha256", "eval_indices_sha256")}
    compact.update({"train_count": len(train_records), "eval_count": len(eval_records), "split_disjoint": True, "split_exhaustive": True,
                    "registry_sha256": sha256(args.registry)})
    args.summary.write_text(json.dumps(compact, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(json.dumps(compact, sort_keys=True))


if __name__ == "__main__":
    main()
