"""Fixed-frame raw metric/RGB/Gaussian evaluation for a nonformal E3 candidate."""
from __future__ import annotations

import argparse
import csv
import importlib.util
import json
import math
import sys
from pathlib import Path

import imageio.v3 as iio
import numpy as np
import torch


def load_launcher(path: Path):
    spec = importlib.util.spec_from_file_location("sweep_launch", path)
    if spec is None or spec.loader is None:
        raise RuntimeError(f"LAUNCHER_LOAD_FAILED:{path}")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def depth_metrics(gt: np.ndarray, pred: np.ndarray) -> dict[str, object]:
    valid = (gt > 0) & np.isfinite(gt) & np.isfinite(pred) & (pred > 0)
    if not valid.any():
        return {"overlap": 0, "absrel": float("nan"), "sqrel": float("nan"), "rmse": float("nan"), "rmse_log": float("nan"), "d1": float("nan"), "d2": float("nan"), "d3": float("nan"), "ratio": np.empty(0, dtype=np.float32)}
    g, p = gt[valid], pred[valid]
    ratio = p / g
    threshold = np.maximum(ratio, 1.0 / ratio)
    return {"overlap": int(valid.sum()), "absrel": float(np.mean(np.abs(p - g) / g)), "sqrel": float(np.mean((p - g) ** 2 / g)), "rmse": float(np.sqrt(np.mean((p - g) ** 2))), "rmse_log": float(np.sqrt(np.mean((np.log(p) - np.log(g)) ** 2))), "d1": float(np.mean(threshold < 1.25)), "d2": float(np.mean(threshold < 1.25 ** 2)), "d3": float(np.mean(threshold < 1.25 ** 3)), "ratio": ratio.astype(np.float32)}


def gaussian_summary(model) -> dict[str, object]:
    means = model.means.detach()
    raw_scales = model.scales.detach()
    scales = torch.exp(raw_scales)
    quats = model.quats.detach()
    qnorm = torch.linalg.vector_norm(quats, dim=-1)
    opacities = torch.sigmoid(model.opacities.detach())
    finite_means = torch.isfinite(means).all(dim=-1)
    invalid_scale = (~torch.isfinite(scales).all(dim=-1)) | (scales <= 0).any(dim=-1)
    bad_quat = (~torch.isfinite(quats).all(dim=-1)) | (qnorm <= 0)
    nonfinite = ~(finite_means & torch.isfinite(raw_scales).all(dim=-1) & torch.isfinite(quats).all(dim=-1) & torch.isfinite(opacities).all(dim=-1))
    return {"gaussian_count": int(means.shape[0]), "nonfinite_gaussian_count": int(nonfinite.sum().item()), "invalid_scale_count": int(invalid_scale.sum().item()), "bad_quaternion_count": int(bad_quat.sum().item()), "opacity_min": float(opacities.min().item()), "opacity_max": float(opacities.max().item()), "map_bbox_min": means.min(dim=0).values.detach().cpu().tolist(), "map_bbox_max": means.max(dim=0).values.detach().cpu().tolist(), "invalid_covariance_count": int((invalid_scale | bad_quat).sum().item()), "coordinate_transform": "none", "extra_global_scale": False}


def finite_json(value):
    if isinstance(value, dict): return {str(k): finite_json(v) for k, v in value.items()}
    if isinstance(value, (list, tuple)): return [finite_json(v) for v in value]
    if isinstance(value, float) and not math.isfinite(value): return None
    return value


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--source-root", type=Path, required=True)
    parser.add_argument("--launcher", type=Path, required=True)
    parser.add_argument("--candidate-id", required=True)
    parser.add_argument("--checkpoint", type=Path, required=True)
    parser.add_argument("--steps", type=int, required=True)
    parser.add_argument("--late-lambda", type=float, required=True)
    parser.add_argument("--lock-step", type=int, required=True)
    parser.add_argument("--beta-m", type=float, required=True)
    parser.add_argument("--out", type=Path, required=True)
    args = parser.parse_args()
    if not args.checkpoint.is_file(): raise SystemExit(f"CHECKPOINT_MISSING:{args.checkpoint}")
    sys.path.insert(0, str(args.source_root))
    launcher = load_launcher(args.launcher)
    config = launcher.prepare_config(args.source_root, args.candidate_id, args.out / "ephemeral_eval_config", args.steps, args.late_lambda, args.lock_step, args.beta_m)
    config.load_dir = None; config.load_checkpoint = None; config.load_step = None
    pipeline = config.pipeline.setup(device="cuda:0", test_mode="test", world_size=1, local_rank=0)
    payload = torch.load(args.checkpoint, map_location="cpu")
    pipeline.load_state_dict(payload["pipeline"], strict=True)
    pipeline.eval()
    outputs = pipeline.datamanager.eval_dataset._dataparser_outputs
    depth_files = outputs.metadata["depth_filenames"]
    rows, ratios = [], []
    with torch.no_grad():
        for eval_index in range(len(pipeline.datamanager.fixed_indices_eval_dataloader)):
            camera, batch = pipeline.datamanager.fixed_indices_eval_dataloader[eval_index]
            camera = camera.to(pipeline.device)
            rendered = pipeline.model.get_outputs_for_camera(camera)
            prediction = rendered["depth"].squeeze(-1).detach().float().cpu().numpy()
            image_index = int(batch["image_idx"])
            ground_truth = iio.imread(depth_files[image_index]).astype(np.float32) * .0002
            item = depth_metrics(ground_truth, prediction)
            rows.append({"eval_index": eval_index, "image_idx": image_index, "depth_path": str(depth_files[image_index]), "valid_gt": int((ground_truth > 0).sum()), **{k: v for k, v in item.items() if k != "ratio"}})
            ratios.append(item["ratio"])
    weights = np.asarray([row["overlap"] for row in rows], dtype=np.float64)
    if not weights.any(): raise RuntimeError("EVALUATION_NO_VALID_DEPTH_OVERLAP")
    combined_ratio = np.concatenate(ratios)
    rgb = pipeline.get_average_eval_image_metrics()
    summary = {"candidate_id": args.candidate_id, "checkpoint": str(args.checkpoint), "checkpoint_step": int(payload["step"]), "frame_count": len(rows), "depth_semantic": "expected_depth_from_splatfacto_RGB+ED; raw metric comparison; no Sim(3), global scale, per-frame scale, or outcome-based filtering", "valid_overlap_pixel_count": int(weights.sum()), "valid_overlap_ratio": float(weights.sum() / sum(row["valid_gt"] for row in rows)), "AbsRel": float(np.average([row["absrel"] for row in rows], weights=weights)), "SqRel": float(np.average([row["sqrel"] for row in rows], weights=weights)), "RMSE": float(np.sqrt(np.average(np.square([row["rmse"] for row in rows]), weights=weights))), "RMSE_log": float(np.sqrt(np.average(np.square([row["rmse_log"] for row in rows]), weights=weights))), "delta1": float(np.average([row["d1"] for row in rows], weights=weights)), "delta2": float(np.average([row["d2"] for row in rows], weights=weights)), "delta3": float(np.average([row["d3"] for row in rows], weights=weights)), "median_predicted_over_gt_ratio": float(np.median(combined_ratio)), "rgb_metrics": finite_json(rgb), "gaussian": gaussian_summary(pipeline.model), "parameters": launcher.contract(config), "formal_training": False}
    args.out.mkdir(parents=True, exist_ok=True)
    with (args.out / "depth_metrics_per_frame.csv").open("w", newline="", encoding="utf-8") as destination:
        writer = csv.DictWriter(destination, fieldnames=list(rows[0])); writer.writeheader(); writer.writerows(rows)
    (args.out / "candidate_metrics.json").write_text(json.dumps(finite_json(summary), indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(json.dumps(finite_json(summary), sort_keys=True))


if __name__ == "__main__":
    main()
