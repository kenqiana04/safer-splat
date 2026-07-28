#!/usr/bin/env python3
"""Schema-only adapter for the frozen PR #56 common Gaussian renderer."""
from __future__ import annotations

import argparse
import json
import math
import os
import subprocess
import sys
from pathlib import Path

from _common import DATASET, PR56_ROOT, ROOT, atomic_json, load_json, sha256_path, task_env

RENDERER_PYTHON = Path("/disk1/zlab/external_baselines/tum_rgbd_gaussian_v1/envs/tum_gaussian_slam_baseline_v1_conda/bin/python")
RENDERER_REPO = Path("/disk1/zlab/external_baselines/tum_rgbd_gaussian_v1/repos/Gaussian-SLAM_official_archive")


def _inner(stage, regression):
    import imageio.v2 as imageio
    import numpy as np
    import torch
    sys.path.insert(0, str(RENDERER_REPO))
    from src.utils.utils import get_render_settings, render_gaussian_model

    class EmptyModel: pass

    if regression:
        root = PR56_ROOT / "canonical_exports" / "splatam" / "smoke"
        order = load_json(PR56_ROOT / "pilot_registry" / "replica_frontend_map_only_order.json")
        ids = order["smoke_holdout_frame_ids"]
        expected = load_json(PR56_ROOT / "geometry_evaluation" / "splatam_smoke_geometry_evaluation.json")["metrics"]
    else:
        name = "splatfacto_smoke_canonical_export_summary.json" if stage == "smoke" else "splatfacto_pilot_canonical_export_summary.json"
        summary = load_json(ROOT / "canonical_export" / name)
        root = Path(summary["canonical_root"])
        adapters = load_json(ROOT / "pilot_adapter" / "splatfacto_metric_dataset_adapter_identity.json")
        key = "smoke" if stage == "smoke" else "qualification_pilot"
        ids = adapters["adapters"][key]["holdout_frame_ids"]
        expected = None
    means = torch.from_numpy(np.load(root / "means_world_m.npy")).cuda()
    scales = torch.from_numpy(np.load(root / "scales_linear_m.npy")).cuda()
    quats = torch.from_numpy(np.load(root / "quaternions_wxyz.npy")).cuda()
    opacities = torch.from_numpy(np.load(root / "opacities.npy").reshape(-1, 1)).cuda()
    if (root / "appearance.npy").is_file():
        colors = torch.from_numpy(np.clip(np.load(root / "appearance.npy"), 0., 1.)).cuda()
    else:
        sh = np.load(root / "sh_coefficients.npy")
        colors = torch.from_numpy(np.clip(sh[:, 0, :] * .28209479177387814 + .5, 0., 1.)).cuda()
    manifest = {row["frame_id"]: row for row in load_json(DATASET / "formal_camera_manifest_v3.json")["frames"]}
    k = np.array([[320., 0., 319.5], [0., 320., 239.5], [0., 0., 1.]], dtype=np.float64)
    P = np.diag([1., -1., -1., 1.])
    per = []
    for frame_id in ids:
        row = manifest[frame_id]; c2w = np.asarray(row["camera_to_world"], dtype=np.float64); c2w_cv = c2w @ P
        settings = get_render_settings(640, 480, k, np.linalg.inv(c2w_cv), near=.05, far=20., sh_degree=0)
        rendered = render_gaussian_model(EmptyModel(), settings, override_means_3d=means, override_scales=scales, override_rotations=quats, override_opacities=opacities, override_colors=colors)
        depth = rendered["depth"].detach().float().cpu().numpy().squeeze(); color = rendered["color"].detach().float().cpu().numpy().transpose(1, 2, 0)
        gt = np.asarray(imageio.imread(DATASET / "depth" / (frame_id + ".png")), dtype=np.float32) * .001
        gt_rgb = np.asarray(imageio.imread(DATASET / "images" / (frame_id + ".png")), dtype=np.float32) / 255.
        valid_gt = np.isfinite(gt) & (gt > 0) & (gt <= 20.); valid_pred = np.isfinite(depth) & (depth > 0); joint = valid_gt & valid_pred
        coverage = float(joint.sum() / max(1, valid_gt.sum()))
        if joint.any():
            p, g = depth[joint], gt[joint]; ratio = p / g; threshold = np.maximum(ratio, 1. / ratio)
            metrics = {"valid_predicted_depth_fraction": coverage, "absrel": float(np.mean(np.abs(p-g)/g)), "sqrel": float(np.mean((p-g)**2/g)), "rmse": float(np.sqrt(np.mean((p-g)**2))), "rmse_log": float(np.sqrt(np.mean((np.log(np.maximum(p,1e-8))-np.log(g))**2))), "delta1": float(np.mean(threshold < 1.25)), "delta2": float(np.mean(threshold < 1.25**2)), "delta3": float(np.mean(threshold < 1.25**3)), "median_depth_ratio": float(np.median(ratio))}
        else:
            metrics = {key: None for key in ("valid_predicted_depth_fraction", "absrel", "sqrel", "rmse", "rmse_log", "delta1", "delta2", "delta3", "median_depth_ratio")}; metrics["valid_predicted_depth_fraction"] = coverage
        finite_color = np.isfinite(color).all(axis=2); mse = float(np.mean((color[finite_color]-gt_rgb[finite_color])**2)) if finite_color.any() else float("inf")
        a=color.astype(np.float64); b=gt_rgb.astype(np.float64); ma,mb=a.mean(),b.mean(); va,vb=a.var(),b.var(); cab=((a-ma)*(b-mb)).mean(); ssim=float(((2*ma*mb+.01**2)*(2*cab+.03**2))/((ma*ma+mb*mb+.01**2)*(va+vb+.03**2)))
        metrics.update({"frame_id": frame_id, "location_id": row["location_id"], "psnr": float(-10.*math.log10(max(mse,1e-12))) if math.isfinite(mse) else None, "ssim": ssim if finite_color.any() else None, "valid_rgb_coverage": float(finite_color.mean()), "nonfinite_prediction_count": int((~np.isfinite(depth)).sum())})
        per.append(metrics)
    keys=("valid_predicted_depth_fraction","absrel","sqrel","rmse","rmse_log","delta1","delta2","delta3","median_depth_ratio","psnr","ssim","valid_rgb_coverage")
    aggregate={key: float(np.mean([x[key] for x in per if x[key] is not None])) if any(x[key] is not None for x in per) else None for key in keys}
    aggregate["nonfinite_prediction_count"] = int(sum(x["nonfinite_prediction_count"] for x in per))
    geometry_pass=aggregate["valid_predicted_depth_fraction"] is not None and aggregate["valid_predicted_depth_fraction"]>=.90 and aggregate["absrel"]<=.20 and aggregate["delta1"]>=.75 and .80<=aggregate["median_depth_ratio"]<=1.25 and aggregate["nonfinite_prediction_count"]==0
    out={"stage":stage,"regression":regression,"canonical_root":str(root),"holdout_frame_count":len(ids),"metrics":aggregate,"per_frame":per,"worst_5_frames":sorted([x for x in per if x["absrel"] is not None],key=lambda x:x["absrel"],reverse=True)[:5],"geometry_gate":{"valid_depth_coverage_gte":.90,"absrel_lte":.20,"delta1_gte":.75,"median_ratio_range":[.80,1.25],"pass":geometry_pass}}
    if expected is not None:
        keys=("absrel","delta1","median_depth_ratio","valid_predicted_depth_fraction")
        out["regression_expected_metrics"]={k:expected[k] for k in keys}; out["regression_absolute_differences"]={k:abs(aggregate[k]-expected[k]) for k in keys}; out["regression_pass"]=all(out["regression_absolute_differences"][k] <= 1e-9 for k in keys)
    print(json.dumps(out, sort_keys=True))


def main():
    parser=argparse.ArgumentParser(); parser.add_argument("--stage", choices=("smoke","qualification_pilot")); parser.add_argument("--regression-pr56-splatam", action="store_true"); parser.add_argument("--inner", action="store_true"); args=parser.parse_args()
    if args.inner:
        _inner(args.stage or "smoke", args.regression_pr56_splatam); return
    if not RENDERER_PYTHON.is_file(): raise SystemExit("BLOCKED_BY_SPLATFACTO_COMMON_EVALUATOR_INCOMPATIBILITY")
    env=task_env(); env["CUDA_VISIBLE_DEVICES"]="1"; command=[str(RENDERER_PYTHON), "-B", __file__, "--inner"]
    if args.regression_pr56_splatam: command.append("--regression-pr56-splatam")
    else: command.extend(("--stage", args.stage))
    result=subprocess.run(command, env=env, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, text=True, timeout=900)
    if result.returncode != 0: raise SystemExit(result.stdout[-4000:])
    payload=json.loads(result.stdout.splitlines()[-1])
    if args.regression_pr56_splatam:
        path=ROOT/"common_evaluation"/"splatfacto_common_evaluator_regression.json"; atomic_json(path,payload); print("SPLATFACTO_COMMON_EVALUATOR_REGRESSION_PASS" if payload.get("regression_pass") else "BLOCKED_BY_SPLATFACTO_COMMON_EVALUATOR_INCOMPATIBILITY"); return
    path=ROOT/"common_evaluation"/("splatfacto_smoke_geometry_diagnostic.json" if args.stage=="smoke" else "splatfacto_pilot_geometry_evaluation.json")
    atomic_json(path,payload); print("SPLATFACTO_COMMON_EVALUATION_COMPLETE")


if __name__ == "__main__": main()
