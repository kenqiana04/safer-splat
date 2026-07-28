#!/usr/bin/env python3
"""Run the frozen common Gaussian evaluator for canonical maps; never use a native metric."""
from __future__ import annotations

import argparse
import json
import math
from pathlib import Path

import imageio.v2 as imageio
import numpy as np
import torch

from _common import DATASET, FRONTENDS, ROOT, atomic_json, ensure_dirs, load_json, update_stage
from _frontend_runner import P, c2w_cv, frame_rows


class EmptyModel: pass


def rgb_from_map(root: Path) -> np.ndarray:
    if (root / "appearance.npy").is_file(): return np.clip(np.load(root / "appearance.npy"), 0.0, 1.0)
    sh = np.load(root / "sh_coefficients.npy"); return np.clip(sh[:, 0, :] * 0.28209479177387814 + 0.5, 0.0, 1.0)


def metrics(pred: np.ndarray, gt: np.ndarray) -> dict:
    valid_gt = np.isfinite(gt) & (gt > 0) & (gt <= 20.0); valid_pred = np.isfinite(pred) & (pred > 0); joint = valid_gt & valid_pred
    coverage = float(joint.sum() / max(1, valid_gt.sum()))
    if not joint.any(): return {"valid_predicted_depth_fraction": coverage, "absrel": None, "sqrel": None, "rmse": None, "rmse_log": None, "delta1": None, "delta2": None, "delta3": None, "median_depth_ratio": None, "nonfinite_prediction_count": int((~np.isfinite(pred)).sum())}
    p, g = pred[joint], gt[joint]; ratio = p / g; threshold = np.maximum(ratio, 1.0 / ratio)
    return {"valid_predicted_depth_fraction": coverage, "absrel": float(np.mean(np.abs(p-g)/g)), "sqrel": float(np.mean((p-g)**2/g)), "rmse": float(np.sqrt(np.mean((p-g)**2))), "rmse_log": float(np.sqrt(np.mean((np.log(np.maximum(p,1e-8))-np.log(g))**2))), "delta1": float(np.mean(threshold < 1.25)), "delta2": float(np.mean(threshold < 1.25**2)), "delta3": float(np.mean(threshold < 1.25**3)), "median_depth_ratio": float(np.median(ratio)), "nonfinite_prediction_count": int((~np.isfinite(pred)).sum())}


def ssim_global(a: np.ndarray, b: np.ndarray) -> float:
    a=a.astype(np.float64); b=b.astype(np.float64); c1=.01**2; c2=.03**2; ma,mb=a.mean(),b.mean(); va,vb=a.var(),b.var(); cab=((a-ma)*(b-mb)).mean(); return float(((2*ma*mb+c1)*(2*cab+c2))/((ma*ma+mb*mb+c1)*(va+vb+c2)))


def main() -> None:
    parser=argparse.ArgumentParser(); parser.add_argument("frontend",choices=("splatam","gaussian_slam")); parser.add_argument("--stage",choices=("smoke","pilot"),default="pilot"); args=parser.parse_args(); ensure_dirs(); frontend=args.frontend
    canonical_summary=ROOT/"canonical_exports"/f"{frontend}_{args.stage}_canonical_export_summary.json"
    if not canonical_summary.exists() or load_json(canonical_summary).get("status") != "CANONICAL_EXPORT_PASS":
        out={"status":"NOT_AUTHORIZED_DUE_TO_CANONICAL_EXPORT","frontend":frontend,"stage":args.stage}; atomic_json(ROOT/"geometry_evaluation"/f"{frontend}_{args.stage}_geometry_evaluation.json",out); print(out["status"]); return
    root=Path(load_json(canonical_summary)["canonical_root"]); means=torch.from_numpy(np.load(root/"means_world_m.npy")).cuda(); scales=torch.from_numpy(np.load(root/"scales_linear_m.npy")).cuda(); quats=torch.from_numpy(np.load(root/"quaternions_wxyz.npy")).cuda(); op=torch.from_numpy(np.load(root/"opacities.npy").reshape(-1,1)).cuda(); colors=torch.from_numpy(rgb_from_map(root)).cuda()
    import sys
    sys.path.insert(0,str(FRONTENDS["gaussian_slam"]["repo"])); from src.utils.utils import get_render_settings,render_gaussian_model
    camera=load_json(ROOT/"input_contract"/"replica_mapping_input_contract.json"); k=np.array([[camera["fx"],0,camera["cx"]],[0,camera["fy"],camera["cy"]],[0,0,1]],dtype=np.float64); order=load_json(ROOT/"pilot_registry"/"replica_frontend_map_only_order.json"); ids=order["smoke_holdout_frame_ids"] if args.stage=="smoke" else order["holdout_frame_order"]; rows=frame_rows(ids); per=[]
    for row in rows:
        settings=get_render_settings(camera["width"],camera["height"],k,np.linalg.inv(c2w_cv(row)),near=.05,far=20.0,sh_degree=0); rendered=render_gaussian_model(EmptyModel(),settings,override_means_3d=means,override_scales=scales,override_rotations=quats,override_opacities=op,override_colors=colors); depth=rendered["depth"].detach().float().cpu().numpy().squeeze(); color=rendered["color"].detach().float().cpu().numpy().transpose(1,2,0); gt=np.asarray(imageio.imread(DATASET/"depth"/f"{row['frame_id']}.png"),dtype=np.float32)*.001; gt_rgb=np.asarray(imageio.imread(DATASET/"images"/f"{row['frame_id']}.png"),dtype=np.float32)/255.; m=metrics(depth,gt); mask=np.isfinite(color).all(axis=2); mse=float(np.mean((color[mask]-gt_rgb[mask])**2)) if mask.any() else float("inf"); m.update({"frame_id":row["frame_id"],"location_id":row["location_id"],"yaw_offset_deg":row["yaw_offset_deg"],"psnr":float(-10*math.log10(max(mse,1e-12))) if math.isfinite(mse) else None,"ssim":ssim_global(color,gt_rgb) if mask.any() else None,"valid_rgb_coverage":float(mask.mean())});per.append(m)
    keys=("valid_predicted_depth_fraction","absrel","sqrel","rmse","rmse_log","delta1","delta2","delta3","median_depth_ratio","psnr","ssim","valid_rgb_coverage")
    aggregate={key:float(np.mean([row[key] for row in per if row[key] is not None])) if any(row[key] is not None for row in per) else None for key in keys}; aggregate["nonfinite_prediction_count"]=int(sum(row["nonfinite_prediction_count"] for row in per)); worst=sorted([row for row in per if row["absrel"] is not None],key=lambda item:item["absrel"],reverse=True)[:5]; geometry_pass=aggregate["valid_predicted_depth_fraction"] is not None and aggregate["valid_predicted_depth_fraction"]>=.90 and aggregate["absrel"]<=.20 and aggregate["delta1"]>=.75 and .80<=aggregate["median_depth_ratio"]<=1.25 and aggregate["nonfinite_prediction_count"]==0
    status="SMOKE_RENDER_PASS" if args.stage=="smoke" and geometry_pass else "SMOKE_RENDER_FAILURE" if args.stage=="smoke" else "COMMON_EVALUATION_PASS" if geometry_pass else "QUALIFICATION_PILOT_RENDER_FAILURE"
    out={"status":status,"frontend":FRONTENDS[frontend]["display"],"stage":args.stage,"common_evaluator_contract":str(ROOT/"common_evaluator"/"common_gaussian_evaluator_contract.json"),"holdout_frame_count":len(per),"metrics":aggregate,"per_frame":per,"worst_5_frames":worst,"geometry_gate":{"valid_depth_coverage_gte":.90,"absrel_lte":.20,"delta1_gte":.75,"median_ratio_range":[.80,1.25],"nonfinite_prediction_count":0,"pass":geometry_pass},"method_native_metrics_used":False}
    name=f"{frontend}_{'smoke_' if args.stage=='smoke' else ''}geometry_evaluation.json";atomic_json(ROOT/"geometry_evaluation"/name,out)
    if args.stage=="smoke":
        summary=load_json(ROOT/frontend/"smoke_summary.json"); summary["status"]="SMOKE_PASS" if geometry_pass else "SMOKE_RENDER_FAILURE"; summary["canonical_export_for_smoke"]=str(root); summary["shared_holdout_render"]=str(ROOT/"geometry_evaluation"/name); atomic_json(ROOT/frontend/"smoke_summary.json",summary); update_stage(frontend,"SMOKE","TERMINAL_SCIENTIFIC_RESULT",result_status=summary["status"])
    else:
        pilot=load_json(ROOT/frontend/"pilot_summary.json"); pilot["status"]="QUALIFICATION_PILOT_COMPLETE" if geometry_pass else "QUALIFICATION_PILOT_RENDER_FAILURE"; pilot["canonical_export"]=str(root); pilot["common_geometry_evaluation"]=str(ROOT/"geometry_evaluation"/name); atomic_json(ROOT/frontend/"pilot_summary.json",pilot); update_stage(frontend,"QUALIFICATION_PILOT","TERMINAL_SCIENTIFIC_RESULT",result_status=pilot["status"]); update_stage(frontend,"COMMON_EVALUATION","TERMINAL_SCIENTIFIC_RESULT" if geometry_pass else "FAILED_INFRASTRUCTURE",result_status=status)
    print(json.dumps(out,sort_keys=True))


if __name__ == "__main__": main()
