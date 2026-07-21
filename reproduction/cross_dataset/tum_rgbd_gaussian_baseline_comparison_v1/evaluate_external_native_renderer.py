"""Compute fixed-60 raw SplaTAM metrics with its official native renderer."""
from __future__ import annotations

import argparse
import json
from pathlib import Path


def mean(rows: list[dict], key: str) -> float:
    return float(sum(row[key] for row in rows) / len(rows))


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--method", choices=("splatam",), required=True)
    parser.add_argument("--repo", type=Path, required=True)
    parser.add_argument("--params", type=Path, required=True)
    parser.add_argument("--eval-adapter", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    if not args.params.is_file() or not args.eval_adapter.is_dir():
        raise RuntimeError("NATIVE_INPUT_MISSING")
    import sys
    sys.path.insert(0, str(args.repo))
    import numpy as np
    import torch
    # PyTorch 1.12 nvFuser asks NVRTC for an Ada-incompatible architecture.
    # Disable only that JIT fusion route; the release rasterizer stays CUDA.
    torch._C._jit_set_profiling_executor(False)
    torch._C._jit_set_profiling_mode(False)
    torch._C._jit_override_can_fuse_on_gpu(False)
    from datasets.gradslam_datasets import TUMDataset, load_dataset_config
    from diff_gaussian_rasterization import GaussianRasterizer as Renderer
    from utils.gs_helpers import params2depthplussilhouette, params2rendervar
    from utils.recon_helpers import setup_camera
    from pytorch_msssim import ms_ssim
    import lpips
    cfg = load_dataset_config(args.repo / "configs/data/TUM/freiburg1_room.yaml")
    dataset = TUMDataset(cfg, str(args.eval_adapter.parent), args.eval_adapter.name, start=0, end=-1, stride=1,
                         desired_height=480, desired_width=640, device="cuda:0", relative_pose=True)
    if len(dataset) != 61:
        raise RuntimeError(f"EVAL_ANCHOR_CONTRACT_MISMATCH:{len(dataset)}")
    raw = np.load(args.params)
    params = {key: torch.tensor(raw[key], device="cuda:0", dtype=torch.float32) for key in raw.files
              if key not in {"intrinsics", "w2c", "org_width", "org_height", "gt_w2c_all_frames"}}
    perceptual = lpips.LPIPS(net="alex").cpu().eval()
    rows: list[dict] = []
    bins: dict[str, list[dict]] = {"near_lt_1m": [], "mid_1m_to_3m": [], "far_ge_3m": []}
    with torch.no_grad():
        for index in range(1, 61):
            color, depth, intrinsics, pose = dataset[index]
            color = color.permute(2, 0, 1) / 255.0
            depth = depth.permute(2, 0, 1)
            w2c = torch.linalg.inv(pose)
            camera = setup_camera(color.shape[2], color.shape[1], intrinsics[:3, :3].cpu().numpy(), w2c.cpu().numpy())
            image, _, _ = Renderer(raster_settings=camera)(**params2rendervar(params))
            depth_silhouette, _, _ = Renderer(raster_settings=camera)(**params2depthplussilhouette(params, w2c))
            prediction = depth_silhouette[0:1]
            valid = (depth > 0) & (prediction > 0) & torch.isfinite(prediction)
            if not bool(valid.any()):
                raise RuntimeError(f"NO_VALID_OVERLAP:{index}")
            gt, estimate = depth[valid], prediction[valid]
            ratio = torch.maximum(gt / estimate, estimate / gt)
            rendered_rgb, gt_rgb = image.cpu(), color.cpu()
            mse = ((rendered_rgb - gt_rgb) ** 2).mean()
            row = {"valid": int(valid.sum()), "absrel": float((torch.abs(estimate - gt) / gt).mean()),
                   "sqrel": float((((estimate - gt) ** 2) / gt).mean()), "rmse": float(torch.sqrt(((estimate - gt) ** 2).mean())),
                   "rmselog": float(torch.sqrt(((torch.log(estimate) - torch.log(gt)) ** 2).mean())),
                   "delta1": float((ratio < 1.25).float().mean()), "delta2": float((ratio < 1.25 ** 2).float().mean()),
                   "delta3": float((ratio < 1.25 ** 3).float().mean()), "ratio": float((estimate / gt).mean()),
                   "psnr": float(-10 * torch.log10(mse)), "ssim": float(ms_ssim(rendered_rgb[None], gt_rgb[None], data_range=1.0, size_average=True)),
                   "lpips": float(perceptual(rendered_rgb[None] * 2 - 1, gt_rgb[None] * 2 - 1).item())}
            rows.append(row)
            for label, selector in (("near_lt_1m", gt < 1), ("mid_1m_to_3m", (gt >= 1) & (gt < 3)), ("far_ge_3m", gt >= 3)):
                if bool(selector.any()):
                    local_gt, local_estimate, local_ratio = gt[selector], estimate[selector], ratio[selector]
                    bins[label].append({"valid": int(selector.sum()), "absrel": float((torch.abs(local_estimate - local_gt) / local_gt).mean()),
                                        "rmse": float(torch.sqrt(((local_estimate - local_gt) ** 2).mean())),
                                        "delta1": float((local_ratio < 1.25).float().mean())})
    keys = ("valid", "absrel", "sqrel", "rmse", "rmselog", "delta1", "delta2", "delta3", "ratio", "psnr", "ssim", "lpips")
    ranges = {label: ({key: mean(values, key) for key in ("valid", "absrel", "rmse", "delta1")} if values else {"status": "NO_VALID_PIXELS"}) for label, values in bins.items()}
    output = {"status": "PASS", "method": "SPLATAM_GTPOSE_MAP_ONLY", "frame_count": 60, "anchor_excluded": True,
              "native_depth_semantics": "alpha-composited expected camera-z from the official depth-plus-silhouette raster pass",
              "raw_metric_depth": True, "sim3": False, "scale_fitting": False, "per_frame_alignment": False,
              "range_bins_m": {"near_lt_1m": [0, 1], "mid_1m_to_3m": [1, 3], "far_ge_3m": [3, None]},
              "range_metrics": ranges, **{key: mean(rows, key) for key in keys}}
    args.output.write_text(json.dumps(output, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(json.dumps(output, sort_keys=True))


if __name__ == "__main__":
    main()
