#!/usr/bin/env python3
"""Fixed-grid selective depth evaluation for an immutable SplaTAM map.

With no arguments it builds the retained-summary audit.  The explicit remote
mode renders each held-out frame once, reuses the exact predicted depth/alpha
arrays for all frozen working points, and verifies the source params file did
not change.  It performs no training, optimizer, filtering, or map export.
"""
from __future__ import annotations
import argparse, csv, hashlib, json, math, sys
from collections import defaultdict
from pathlib import Path

from audit_core import ALPHA_GRID, historical_metrics, risk_coverage


def file_sha(path: Path) -> str:
    h=hashlib.sha256()
    with path.open("rb") as f:
        for b in iter(lambda:f.read(1024*1024),b""): h.update(b)
    return h.hexdigest()


def rows(path: Path):
    with path.open("r",encoding="utf-8",newline="") as f: return list(csv.DictReader(f))


def pose(np,row):
    return np.array([[float(row[f"c2w_{i}{j}"]) for j in range(4)] for i in range(4)],dtype=np.float64)


def asset(root: Path, rel: str) -> Path:
    p=(root/rel).resolve(); p.relative_to(root.resolve())
    if not p.is_file(): raise FileNotFoundError(p)
    return p


def remote_eval(args) -> None:
    import imageio.v2 as imageio
    import numpy as np
    import torch
    sys.path.insert(0,str(args.runtime))
    from utils.recon_helpers import setup_camera
    from utils.gs_helpers import params2depthplussilhouette
    from diff_gaussian_rasterization import GaussianRasterizer as Renderer

    train,held=rows(args.train),rows(args.heldout)
    if not train or not held: raise RuntimeError("empty frozen manifest")
    before=file_sha(args.params)
    world_from_apple=np.linalg.inv(pose(np,train[0]))
    with np.load(args.params,allow_pickle=True) as ar:
        params={k:torch.as_tensor(ar[k],dtype=torch.float32,device="cuda:0") for k in ("means3D","rgb_colors","unnorm_rotations","logit_opacities","log_scales")}
    accum={a:{"target":0,"supported":0,"absrel_sum":0.0,"sqrel_sum":0.0,"sqerr_sum":0.0,"delta1":0,"delta2":0,"delta3":0,"ratios":[],"nonfinite":0,"frames":[],"groups":defaultdict(lambda:[0,0])} for a in ALPHA_GRID}
    with torch.no_grad():
        for idx,row in enumerate(held):
            gt=np.asarray(imageio.imread(asset(args.asset_root,row["depth"])),dtype=np.float32)/1000.0
            conf=np.asarray(imageio.imread(asset(args.asset_root,row["confidence"])))
            h,w=gt.shape
            k=np.array([[float(row["fx"]),0,float(row["cx"])],[0,float(row["fy"]),float(row["cy"])],[0,0,1]],dtype=np.float32)
            c2w=world_from_apple@pose(np,row); w2c=np.linalg.inv(c2w).astype(np.float32)
            cam=setup_camera(w,h,k,w2c); w2c_t=torch.as_tensor(w2c,device="cuda:0")
            depth_sil,_,_=Renderer(raster_settings=cam)(**params2depthplussilhouette(params,w2c_t))
            alpha=depth_sil[1].cpu().numpy(); pred=(depth_sil[0]/depth_sil[1].clamp_min(1e-8)).cpu().numpy()
            target=(gt>0)&(conf>=1); target_n=int(target.sum())
            group=row.get("group_id") or row.get("spatial_group") or "UNAVAILABLE"
            for a in ALPHA_GRID:
                valid=target&(alpha>=a)&np.isfinite(pred)&(pred>0); n=int(valid.sum()); z=accum[a]
                z["target"]+=target_n; z["supported"]+=n; z["nonfinite"]+=int((target&~np.isfinite(pred)).sum()); z["groups"][group][0]+=target_n; z["groups"][group][1]+=n
                if n:
                    p,g=pred[valid].astype(np.float64),gt[valid].astype(np.float64); ratio=p/g; sym=np.maximum(ratio,1/np.maximum(ratio,1e-15)); err=p-g
                    z["absrel_sum"]+=float(np.sum(np.abs(err)/g)); z["sqrel_sum"]+=float(np.sum(err*err/g)); z["sqerr_sum"]+=float(np.sum(err*err)); z["delta1"]+=int(np.sum(sym<1.25)); z["delta2"]+=int(np.sum(sym<1.25**2)); z["delta3"]+=int(np.sum(sym<1.25**3)); z["ratios"].append(ratio)
                z["frames"].append({"heldout_index":idx,"group_id":group,"target_count":target_n,"supported_count":n,"coverage":n/target_n if target_n else None})
            print(json.dumps({"frame":idx+1,"of":len(held)},sort_keys=True),flush=True)
    points=[]
    for a in ALPHA_GRID:
        z=accum[a]; n=z["supported"]; frame_cov=[x["coverage"] for x in z["frames"] if x["coverage"] is not None]; group_cov=[s/t for t,s in z["groups"].values() if t]
        ratios=np.concatenate(z["ratios"]) if z["ratios"] else np.array([],dtype=np.float64)
        points.append({"tau_alpha":a,"status":"OBSERVED_READ_ONLY_FIXED_GRID","target_pixel_count":z["target"],"accepted_pixel_count":n,"rejected_unknown_pixel_count":z["target"]-n,"global_coverage":n/z["target"],"per_frame_macro_coverage":float(np.mean(frame_cov)),"per_group_macro_coverage":float(np.mean(group_cov)) if group_cov and list(z["groups"])[0]!="UNAVAILABLE" else None,"worst_5_percent_frame_coverage":float(np.mean(sorted(frame_cov)[:max(1,math.ceil(.05*len(frame_cov)))])),"AbsRel":z["absrel_sum"]/n if n else None,"RMSE":math.sqrt(z["sqerr_sum"]/n) if n else None,"SqRel":z["sqrel_sum"]/n if n else None,"delta1":z["delta1"]/n if n else None,"delta2":z["delta2"]/n if n else None,"delta3":z["delta3"]/n if n else None,"median_ratio":float(np.median(ratios)) if len(ratios) else None,"nonfinite":z["nonfinite"]})
    after=file_sha(args.params)
    if before!=after: raise RuntimeError("MAP_IDENTITY_CHANGED")
    valid=[p for p in points if p["global_coverage"] is not None and p["AbsRel"] is not None]
    ordered=sorted(valid,key=lambda p:p["global_coverage"])
    aurc=float(np.trapz([p["AbsRel"] for p in ordered],[p["global_coverage"] for p in ordered])) if len(ordered)>1 else None
    result={"schema":"fixed-alpha-risk-coverage/v1","map_id":args.map_id,"fixed_alpha_grid":ALPHA_GRID,"renderer":"SplaTAM camera-z alpha-composited conditional expected depth","target":"GT_depth>0 and ARKit confidence>=1","points":points,"complete_curve":len(points)==len(ALPHA_GRID),"AURC":aurc,"AURC_definition":"trapezoid of conditional AbsRel over ascending observed global coverage; descriptive only","params_path":str(args.params),"params_sha256_before":before,"params_sha256_after":after,"map_unmodified":True,"training_count":0,"controller_count":0}
    args.output.parent.mkdir(parents=True,exist_ok=True); args.output.write_text(json.dumps(result,indent=2,sort_keys=True)+"\n",encoding="utf-8")
    print("PASS_FIXED_ALPHA_READ_ONLY_EVALUATION")


def main():
    p=argparse.ArgumentParser(); p.add_argument("--params",type=Path); p.add_argument("--runtime",type=Path); p.add_argument("--train",type=Path); p.add_argument("--heldout",type=Path); p.add_argument("--asset-root",type=Path); p.add_argument("--output",type=Path); p.add_argument("--map-id",default="ARKITSCENES_M1_SPLATAM")
    a=p.parse_args()
    if a.params:
        if not all((a.runtime,a.train,a.heldout,a.asset_root,a.output)): p.error("remote mode requires all paths")
        remote_eval(a)
    else: risk_coverage(historical_metrics())
if __name__=="__main__": main()
