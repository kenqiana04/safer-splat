"""Create deterministic, train-only metric point-to-plane targets from the frozen parser."""
from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path

import imageio.v3 as iio
import numpy as np
import yaml


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for block in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def target_for_depth(raw_path: Path, fx: float, fy: float, cx: float, cy: float) -> tuple[np.ndarray, np.ndarray, np.ndarray]:
    depth = iio.imread(raw_path).astype(np.float32) * 0.0002
    h, w = depth.shape
    uu, vv = np.meshgrid(np.arange(w, dtype=np.float32), np.arange(h, dtype=np.float32))
    points = np.stack(((uu - cx) / fx * depth, (vv - cy) / fy * depth, depth), axis=-1)
    center, left, right, up, down = depth[1:-1, 1:-1], depth[1:-1, :-2], depth[1:-1, 2:], depth[:-2, 1:-1], depth[2:, 1:-1]
    valid_neighbors = (center > 0) & (left > 0) & (right > 0) & (up > 0) & (down > 0)
    threshold = np.maximum(0.05, 0.05 * center)
    continuous = np.maximum.reduce((np.abs(left-center), np.abs(right-center), np.abs(up-center), np.abs(down-center))) <= threshold
    vx, vy = points[1:-1, 2:] - points[1:-1, :-2], points[2:, 1:-1] - points[:-2, 1:-1]
    normal_inner = np.cross(vx, vy)
    norm = np.linalg.norm(normal_inner, axis=-1, keepdims=True)
    normal_inner = normal_inner / np.maximum(norm, np.finfo(np.float32).tiny)
    normal_inner[normal_inner[..., 2] > 0.0] *= -1.0
    rays = np.stack(((uu[1:-1, 1:-1]-cx)/fx, (vv[1:-1, 1:-1]-cy)/fy, np.ones_like(center)), axis=-1)
    factor_inner = np.sum(normal_inner * rays, axis=-1)
    valid_inner = valid_neighbors & continuous & np.isfinite(normal_inner).all(axis=-1) & (np.abs(factor_inner) >= 0.10)
    factor = np.zeros((h, w), dtype=np.float32); normal = np.zeros((h, w, 3), dtype=np.float32); valid = np.zeros((h, w), dtype=np.uint8)
    factor[1:-1, 1:-1] = factor_inner; normal[1:-1, 1:-1] = normal_inner; valid[1:-1, 1:-1] = valid_inner
    return factor, normal, valid


def parse_outputs(config_path: Path, split: str):
    config = yaml.load(config_path.read_text(encoding="utf-8"), Loader=yaml.UnsafeLoader)
    outputs = config.pipeline.datamanager.dataparser.setup().get_dataparser_outputs(split=split)
    metadata = outputs.metadata
    return list(outputs.image_filenames), list(metadata["depth_filenames"]), outputs.cameras


def build(config_path: Path, out: Path, split: str) -> dict:
    image_files, depth_files, cameras = parse_outputs(config_path, split)
    expected = 240 if split == "train" else 60
    if len(image_files) != expected or len(depth_files) != expected:
        raise RuntimeError(f"{split.upper()}_FRAME_CONTRACT_MISMATCH:{len(image_files)}:{len(depth_files)}")
    out.mkdir(parents=True, exist_ok=True)
    fx, fy, cx, cy = (float(cameras.fx[0]), float(cameras.fy[0]), float(cameras.cx[0]), float(cameras.cy[0]))
    records=[]
    for index, (image, depth) in enumerate(zip(image_files, depth_files)):
        factor, normal, valid = target_for_depth(Path(depth), fx, fy, cx, cy)
        file=out/f"{index:06d}.npz"; np.savez_compressed(file, plane_factor=factor, surface_normal=normal, surface_valid=valid)
        records.append({"index": index, "file": file.name, "sha256": sha256_file(file), "image": str(image), "depth": str(depth), "depth_sha256": sha256_file(Path(depth)), "valid_fraction": float(valid.mean())})
    return {"split": split, "frame_count": len(records), "frames": records, "frame_sequence_sha256": hashlib.sha256("\n".join(item["image"] for item in records).encode()).hexdigest(), "files_sha256": hashlib.sha256("\n".join(item["sha256"] for item in records).encode()).hexdigest(), "valid_fraction": float(np.mean([item["valid_fraction"] for item in records])), "intrinsics": {"fx":fx,"fy":fy,"cx":cx,"cy":cy}, "no_eval_leakage": split == "train", "evaluation_only": split == "test", "contract": f"{expected} frozen {split} parser outputs only; depth factor/mask/normals created from raw metric depth"}


def main() -> None:
    parser=argparse.ArgumentParser(); parser.add_argument("--config",type=Path,required=True); parser.add_argument("--out",type=Path,required=True); parser.add_argument("--manifest",type=Path,required=True); parser.add_argument("--split",choices=("train","test"),default="train"); args=parser.parse_args()
    first=build(args.config,args.out,args.split); alternate=args.out.parent/(args.out.name+"_repeat")
    second=build(args.config,alternate,args.split)
    if first["frame_sequence_sha256"] != second["frame_sequence_sha256"] or first["files_sha256"] != second["files_sha256"]:
        raise RuntimeError("BLOCKED_BY_SURFACE_TARGET_GENERATION:NONDETERMINISTIC")
    first["double_build_exact"] = True
    args.manifest.write_text(json.dumps(first,indent=2,sort_keys=True)+"\n",encoding="utf-8")
    print(json.dumps(first,sort_keys=True))


if __name__ == "__main__": main()
