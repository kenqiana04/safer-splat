"""Evaluate the exported Gaussian-SLAM submaps with its native renderer."""
from __future__ import annotations

import argparse
import json
from pathlib import Path


def mean(items: list[float]) -> float:
    return float(sum(items) / len(items))


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--repo", type=Path, required=True)
    parser.add_argument("--run", type=Path, required=True)
    parser.add_argument("--eval-adapter", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    if not (args.run / "submaps" / "final_submap.ckpt").is_file():
        raise RuntimeError("GAUSSIAN_SLAM_FINAL_SUBMAP_MISSING")

    import sys
    sys.path.insert(0, str(args.repo))
    import numpy as np
    import torch
    import torch.nn as nn
    from src.entities.datasets import TUM_RGBD
    from src.entities.gaussian_model import GaussianModel
    from src.utils.utils import get_render_settings, render_gaussian_model
    from pytorch_msssim import ms_ssim
    import lpips

    # Each completed submap is already saved by the official loop.  The
    # task-owned export hook records only the otherwise-unpersisted final live
    # submap; concatenating their global-coordinate Gaussian tensors changes no
    # parameter and calls the release renderer unchanged.
    checkpoints = sorted((args.run / "submaps").glob("*.ckpt"))
    params = [torch.load(path, map_location="cpu")["gaussian_params"] for path in checkpoints]
    fields = ("xyz", "features_dc", "features_rest", "scaling", "rotation", "opacity")
    merged = {field: torch.cat([part[field] for part in params], dim=0).cuda() for field in fields}
    model = GaussianModel(3)
    model._xyz = nn.Parameter(merged["xyz"], requires_grad=False)
    model._features_dc = nn.Parameter(merged["features_dc"], requires_grad=False)
    model._features_rest = nn.Parameter(merged["features_rest"], requires_grad=False)
    model._scaling = nn.Parameter(merged["scaling"], requires_grad=False)
    model._rotation = nn.Parameter(merged["rotation"], requires_grad=False)
    model._opacity = nn.Parameter(merged["opacity"], requires_grad=False)

    dataset_cfg = {"input_path": str(args.eval_adapter), "frame_limit": 61,
                   "H": 480, "W": 640, "fx": 517.3, "fy": 516.5,
                   "cx": 318.6, "cy": 255.3, "crop_edge": 50,
                   "depth_scale": 5000.0,
                   "distortion": [0.2624, -0.9531, -0.0054, 0.0026, 1.1633]}
    dataset = TUM_RGBD(dataset_cfg)
    if len(dataset) != 61:
        raise RuntimeError(f"EVAL_ANCHOR_CONTRACT_MISMATCH:{len(dataset)}")
    perceptual = lpips.LPIPS(net="alex").cpu().eval()
    records: list[dict] = []
    bins: dict[str, list[dict]] = {"near_lt_1m": [], "mid_1m_to_3m": [], "far_ge_3m": []}
    with torch.no_grad():
        for index in range(1, 61):
            _, color_np, depth_np, c2w = dataset[index]
            color = torch.from_numpy(color_np).permute(2, 0, 1).float().cuda() / 255.0
            depth = torch.from_numpy(depth_np).float().cuda()
            rendered = render_gaussian_model(model, get_render_settings(dataset.width, dataset.height, dataset.intrinsics, np.linalg.inv(c2w)))
            pred = rendered["depth"].squeeze(0)
            valid = (depth > 0) & (pred > 0) & torch.isfinite(pred)
            if not bool(valid.any()):
                raise RuntimeError(f"NO_VALID_OVERLAP:{index}")
            gt, estimate = depth[valid], pred[valid]
            ratio = torch.maximum(gt / estimate, estimate / gt)
            rgb_pred, rgb_gt = rendered["color"].cpu(), color.cpu()
            mse = ((rgb_pred - rgb_gt) ** 2).mean()
            row = {"valid": int(valid.sum()), "absrel": float((torch.abs(estimate - gt) / gt).mean()),
                   "sqrel": float((((estimate - gt) ** 2) / gt).mean()),
                   "rmse": float(torch.sqrt(((estimate - gt) ** 2).mean())),
                   "rmselog": float(torch.sqrt(((torch.log(estimate) - torch.log(gt)) ** 2).mean())),
                   "delta1": float((ratio < 1.25).float().mean()), "delta2": float((ratio < 1.25 ** 2).float().mean()),
                   "delta3": float((ratio < 1.25 ** 3).float().mean()), "ratio": float((estimate / gt).mean()),
                   "psnr": float(-10 * torch.log10(mse)), "ssim": float(ms_ssim(rgb_pred[None], rgb_gt[None], data_range=1.0, size_average=True)),
                   "lpips": float(perceptual(rgb_pred[None] * 2 - 1, rgb_gt[None] * 2 - 1).item())}
            records.append(row)
            for label, mask in (("near_lt_1m", gt < 1), ("mid_1m_to_3m", (gt >= 1) & (gt < 3)), ("far_ge_3m", gt >= 3)):
                if bool(mask.any()):
                    local_ratio = ratio[mask]
                    local_est, local_gt = estimate[mask], gt[mask]
                    bins[label].append({"valid": int(mask.sum()), "absrel": float((torch.abs(local_est - local_gt) / local_gt).mean()),
                                        "rmse": float(torch.sqrt(((local_est - local_gt) ** 2).mean())),
                                        "delta1": float((local_ratio < 1.25).float().mean())})
    keys = ("valid", "absrel", "sqrel", "rmse", "rmselog", "delta1", "delta2", "delta3", "ratio", "psnr", "ssim", "lpips")
    summary = {key: mean([row[key] for row in records]) for key in keys}
    range_summary = {label: ({key: mean([row[key] for row in rows]) for key in ("valid", "absrel", "rmse", "delta1")} if rows else {"status": "NO_VALID_PIXELS"}) for label, rows in bins.items()}
    output = {"status": "PASS", "method": "GAUSSIAN_SLAM_GTPOSE_MAP_ONLY", "frame_count": 60,
              "anchor_excluded": True, "submap_checkpoint_count": len(checkpoints), "gaussian_count": int(model.get_size()),
              "native_depth_semantics": "official Gaussian-SLAM native rasterizer depth output", "raw_metric_depth": True,
              "sim3": False, "scale_fitting": False, "per_frame_alignment": False,
              "range_bins_m": {"near_lt_1m": [0, 1], "mid_1m_to_3m": [1, 3], "far_ge_3m": [3, None]},
              "range_metrics": range_summary, **summary}
    args.output.write_text(json.dumps(output, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(json.dumps(output, sort_keys=True))


if __name__ == "__main__":
    main()
