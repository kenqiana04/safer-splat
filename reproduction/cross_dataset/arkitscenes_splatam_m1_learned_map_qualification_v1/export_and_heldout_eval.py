#!/usr/bin/env python3
"""Canonical export and frozen 53-frame HELDOUT render/depth evaluation."""

from __future__ import annotations

import argparse
import csv
import hashlib
import json
import math
from pathlib import Path
import sys

import imageio.v2 as imageio
import numpy as np
import torch


def sha(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def tree_sha(root: Path) -> str:
    digest = hashlib.sha256()
    for path in sorted(p for p in root.rglob("*") if p.is_file()):
        digest.update(path.relative_to(root).as_posix().encode())
        digest.update(bytes.fromhex(sha(path)))
    return digest.hexdigest()


def load_rows(path: Path) -> list[dict[str, str]]:
    with path.open("r", encoding="utf-8", newline="") as handle:
        return list(csv.DictReader(handle))


def pose(row: dict[str, str]) -> np.ndarray:
    return np.array([[float(row[f"c2w_{i}{j}"]) for j in range(4)] for i in range(4)], dtype=np.float64)


def canonical_arrays(params_path: Path) -> dict[str, np.ndarray]:
    with np.load(params_path, allow_pickle=True) as archive:
        raw = {key: archive[key] for key in archive.files}
    means = np.asarray(raw["means3D"], dtype=np.float32)
    log_scales = np.asarray(raw["log_scales"], dtype=np.float32)
    if log_scales.ndim != 2 or log_scales.shape[1] not in (1, 3):
        raise RuntimeError("unsupported SplaTAM log-scale shape")
    scales = np.exp(log_scales)
    if scales.shape[1] == 1:
        scales = np.repeat(scales, 3, axis=1)
    quats = np.asarray(raw["unnorm_rotations"], dtype=np.float32)
    quats /= np.maximum(np.linalg.norm(quats, axis=1, keepdims=True), np.finfo(np.float32).tiny)
    logits = np.asarray(raw["logit_opacities"], dtype=np.float32)
    opacities = 1.0 / (1.0 + np.exp(-logits.astype(np.float64)))
    result = {
        "means_world_m": means,
        "scales_linear_m": scales.astype(np.float32),
        "quaternions_wxyz": quats,
        "opacities_probability": opacities.astype(np.float32),
        "colors_rgb": np.asarray(raw["rgb_colors"], dtype=np.float32),
        "source_gaussian_id": np.arange(len(means), dtype=np.int64),
        "source_frame_id": np.full(len(means), -1, dtype=np.int32),
        "source_pixel_id": np.full(len(means), -1, dtype=np.int32),
    }
    return result


def export(params_path: Path, output: Path) -> dict:
    if output.exists():
        raise RuntimeError(f"export output already exists: {output}")
    output.mkdir(parents=True)
    arrays = canonical_arrays(params_path)
    for name, array in arrays.items():
        np.save(output / f"{name}.npy", array, allow_pickle=False)
    count = len(arrays["means_world_m"])
    gates = {
        "gaussian_count_positive": count > 0,
        "counts_equal": len({len(array) for array in arrays.values()}) == 1,
        "all_finite": all(np.isfinite(array).all() for array in arrays.values()),
        "scale_positive": bool((arrays["scales_linear_m"] > 0).all()),
        "quaternion_normalized": bool(np.allclose(np.linalg.norm(arrays["quaternions_wxyz"], axis=1), 1.0, atol=1e-5)),
        "opacity_probability": bool(((arrays["opacities_probability"] >= 0) & (arrays["opacities_probability"] <= 1)).all()),
        "source_gaussian_id_unique": len(np.unique(arrays["source_gaussian_id"])) == count,
        "no_filter_recenter_scale_repair": True,
    }
    metadata = {
        "status": "PASS_CANONICAL_SPLATAM_M1_EXPORT" if all(gates.values()) else "BLOCKED_BY_ARKITSCENES_M1_CANONICAL_EXPORT",
        "gates": gates,
        "gaussian_count": count,
        "coordinate_frame": "metric SplaTAM world anchored at first TRAIN camera; no recenter, scale, ICP, or Sim3",
        "scale_conversion": "exp(log_scales) exactly once; isotropic channel repeated to xyz",
        "quaternion_order": "WXYZ normalized",
        "opacity_conversion": "sigmoid(logit_opacities) exactly once; no opacity filtering",
        "source_frame_pixel_availability": "unavailable after official densification; -1 sentinels retained; unique source_gaussian_id provided",
        "arrays": {name: {"shape": list(array.shape), "dtype": str(array.dtype), "sha256": sha(output / f"{name}.npy")} for name, array in arrays.items()},
    }
    (output / "canonical_export_metadata.json").write_text(json.dumps(metadata, indent=2, sort_keys=True) + "\n", encoding="utf-8", newline="\n")
    if not all(gates.values()):
        raise SystemExit(2)
    metadata["tree_sha256"] = tree_sha(output)
    return metadata


def asset(root: Path, relative: str) -> Path:
    path = (root / relative).resolve()
    path.relative_to(root.resolve())
    if not path.is_file():
        raise FileNotFoundError(path)
    return path


def summarize_depth(pred: np.ndarray, gt: np.ndarray, conf: np.ndarray, alpha: np.ndarray, conf_threshold: int) -> dict:
    target = (gt > 0) & (conf >= conf_threshold)
    valid = target & (alpha >= 0.5) & np.isfinite(pred) & (pred > 0)
    count, supported = int(target.sum()), int(valid.sum())
    if supported == 0:
        return {"target_count": count, "supported_count": 0, "coverage": 0.0, "absrel": float("inf"), "delta1": 0.0, "median_pred_gt_ratio": float("nan"), "nonfinite_count": int((target & ~np.isfinite(pred)).sum())}
    p, g = pred[valid], gt[valid]
    ratio = p / g
    symmetric = np.maximum(ratio, 1.0 / np.maximum(ratio, 1e-12))
    return {
        "target_count": count,
        "supported_count": supported,
        "coverage": supported / count,
        "absrel": float(np.mean(np.abs(p - g) / g)),
        "delta1": float(np.mean(symmetric < 1.25)),
        "median_pred_gt_ratio": float(np.median(ratio)),
        "nonfinite_count": int((target & ~np.isfinite(pred)).sum()),
        "pred_sum": float(p.sum()),
        "gt_sum": float(g.sum()),
        "absrel_sum": float(np.sum(np.abs(p - g) / g)),
        "delta1_count": int((symmetric < 1.25).sum()),
        "ratios": ratio,
    }


def evaluate(params_path: Path, runtime: Path, train_manifest: Path, heldout_manifest: Path, asset_root: Path, output: Path) -> dict:
    sys.path.insert(0, str(runtime))
    from utils.recon_helpers import setup_camera
    from utils.gs_helpers import params2rendervar, params2depthplussilhouette, loss_fn_alex
    from utils.slam_external import calc_psnr
    from pytorch_msssim import ms_ssim
    from diff_gaussian_rasterization import GaussianRasterizer as Renderer

    train, heldout = load_rows(train_manifest), load_rows(heldout_manifest)
    if len(train) != 214 or len(heldout) != 53:
        raise RuntimeError("frozen split count changed")
    world_from_apple = np.linalg.inv(pose(train[0]))
    with np.load(params_path, allow_pickle=True) as archive:
        params = {key: torch.as_tensor(archive[key], dtype=torch.float32, device="cuda:0") for key in ("means3D", "rgb_colors", "unnorm_rotations", "logit_opacities", "log_scales")}
    before_hash = hashlib.sha256(b"".join(params[key].detach().cpu().numpy().tobytes() for key in sorted(params))).hexdigest()
    per_frame: list[dict] = []
    primary_parts: list[dict] = []
    secondary_parts: list[dict] = []
    output.mkdir(parents=True, exist_ok=True)
    with torch.no_grad():
        for index, row in enumerate(heldout):
            rgb = np.asarray(imageio.imread(asset(asset_root, row["rgb"])), dtype=np.float32) / 255.0
            gt = np.asarray(imageio.imread(asset(asset_root, row["depth"])), dtype=np.float32) / 1000.0
            conf = np.asarray(imageio.imread(asset(asset_root, row["confidence"])))
            height, width = gt.shape
            if rgb.shape[:2] != (height, width):
                raise RuntimeError("HELDOUT RGB/depth shape mismatch")
            k = np.array([[float(row["fx"]), 0, float(row["cx"])], [0, float(row["fy"]), float(row["cy"])], [0, 0, 1]], dtype=np.float32)
            c2w = world_from_apple @ pose(row)
            w2c = np.linalg.inv(c2w).astype(np.float32)
            cam = setup_camera(width, height, k, w2c)
            w2c_t = torch.as_tensor(w2c, device="cuda:0")
            im, _, _ = Renderer(raster_settings=cam)(**params2rendervar(params))
            depth_sil, _, _ = Renderer(raster_settings=cam)(**params2depthplussilhouette(params, w2c_t))
            alpha_t = depth_sil[1].clamp_min(1e-8)
            expected_depth_t = depth_sil[0] / alpha_t
            gt_rgb_t = torch.as_tensor(rgb, device="cuda:0").permute(2, 0, 1)
            psnr = float(calc_psnr(im, gt_rgb_t).mean().item())
            ssim = float(ms_ssim(im.unsqueeze(0).cpu(), gt_rgb_t.unsqueeze(0).cpu(), data_range=1.0, size_average=True).item())
            lpips = float(loss_fn_alex(torch.clamp(im.unsqueeze(0), 0, 1), torch.clamp(gt_rgb_t.unsqueeze(0), 0, 1)).item())
            pred = expected_depth_t.cpu().numpy(); alpha = depth_sil[1].cpu().numpy()
            primary = summarize_depth(pred, gt, conf, alpha, 1)
            secondary = summarize_depth(pred, gt, conf, alpha, 2)
            primary_parts.append(primary); secondary_parts.append(secondary)
            per_frame.append({"heldout_index": index, "timestamp": row["timestamp"], "width": width, "height": height, "psnr": psnr, "ssim": ssim, "lpips": lpips,
                              "primary": {k: v for k, v in primary.items() if k != "ratios"}, "secondary": {k: v for k, v in secondary.items() if k != "ratios"}})

    def aggregate(parts: list[dict]) -> dict:
        target = sum(x["target_count"] for x in parts); supported = sum(x["supported_count"] for x in parts)
        ratios = np.concatenate([x["ratios"] for x in parts if "ratios" in x])
        return {"target_count": target, "supported_count": supported, "coverage": supported / target,
                "absrel": sum(x.get("absrel_sum", 0) for x in parts) / supported,
                "delta1": sum(x.get("delta1_count", 0) for x in parts) / supported,
                "median_pred_gt_ratio": float(np.median(ratios)),
                "nonfinite_count": sum(x["nonfinite_count"] for x in parts)}

    primary, secondary = aggregate(primary_parts), aggregate(secondary_parts)
    nvs = {key: float(np.mean([row[key] for row in per_frame])) for key in ("psnr", "ssim", "lpips")}
    after_hash = hashlib.sha256(b"".join(params[key].detach().cpu().numpy().tobytes() for key in sorted(params))).hexdigest()
    gates = {
        "heldout_all_53": len(per_frame) == 53,
        "render_size_correct": all(row["width"] == 256 and row["height"] == 192 for row in per_frame),
        "nvs_finite": all(math.isfinite(row[key]) for row in per_frame for key in ("psnr", "ssim", "lpips")),
        "map_unmodified": before_hash == after_hash,
        "primary_coverage": primary["coverage"] >= 0.95,
        "primary_absrel": primary["absrel"] <= 0.20,
        "primary_delta1": primary["delta1"] >= 0.75,
        "primary_scale_ratio": 0.80 <= primary["median_pred_gt_ratio"] <= 1.25,
        "primary_nonfinite": primary["nonfinite_count"] == 0,
    }
    scale = primary["median_pred_gt_ratio"]
    scale_issue = any(0.8 * factor <= scale <= 1.25 * factor for factor in (0.001, 0.01, 0.1, 10.0, 100.0, 1000.0))
    status = "PASS_HELDOUT_NVS_AND_METRIC_DEPTH" if all(gates.values()) else ("MAP_COORDINATE_OR_SCALE_FAILURE" if scale_issue else "NO_ARKITSCENES_M1_LEARNED_GAUSSIAN_MAP_QUALIFIED_UNDER_FROZEN_CONTRACT")
    result = {"status": status, "pass": all(gates.values()), "gates": gates, "primary_confidence_ge1": primary, "secondary_confidence_eq2_report_only": secondary,
              "nvs_all_53": nvs, "per_frame": per_frame, "gaussian_depth": "camera-z alpha-composited conditional expected depth; valid alpha>=0.5; no fill",
              "heldout_mapper_access_count": 0, "map_parameter_sha256_before": before_hash, "map_parameter_sha256_after": after_hash}
    (output / "heldout_evaluation.json").write_text(json.dumps(result, indent=2, sort_keys=True) + "\n", encoding="utf-8", newline="\n")
    print(status)
    return result


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--params", type=Path, required=True)
    parser.add_argument("--runtime", type=Path, required=True)
    parser.add_argument("--train", type=Path, required=True)
    parser.add_argument("--heldout", type=Path, required=True)
    parser.add_argument("--asset-root", type=Path, required=True)
    parser.add_argument("--export-a", type=Path, required=True)
    parser.add_argument("--export-b", type=Path, required=True)
    parser.add_argument("--evaluation-output", type=Path, required=True)
    args = parser.parse_args()
    first, second = export(args.params, args.export_a), export(args.params, args.export_b)
    if first["tree_sha256"] != second["tree_sha256"]:
        raise SystemExit("BLOCKED_BY_ARKITSCENES_M1_CANONICAL_EXPORT: fresh tree mismatch")
    comparison = {"status": "PASS_TWO_FRESH_CANONICAL_EXPORTS_IDENTICAL", "tree_sha256": first["tree_sha256"], "first": first, "second": second}
    args.evaluation_output.mkdir(parents=True, exist_ok=True)
    (args.evaluation_output / "export_determinism.json").write_text(json.dumps(comparison, indent=2, sort_keys=True) + "\n", encoding="utf-8", newline="\n")
    result = evaluate(args.params, args.runtime, args.train, args.heldout, args.asset_root, args.evaluation_output)
    if not result["pass"]:
        raise SystemExit(3)


if __name__ == "__main__":
    main()

