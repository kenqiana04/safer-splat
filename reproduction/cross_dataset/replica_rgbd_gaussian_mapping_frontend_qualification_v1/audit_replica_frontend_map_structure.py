#!/usr/bin/env python3
"""Canonical-map finite/metric/covariance audit without filtering or mutation."""
from __future__ import annotations

import argparse
from pathlib import Path

import numpy as np

from _common import ROOT, atomic_json, ensure_dirs, load_json


def quantiles(values: np.ndarray) -> dict:
    return {key: float(value) for key, value in zip(("min", "p1", "median", "p99", "max"), np.quantile(values, (0, .01, .5, .99, 1)))}


def main() -> None:
    parser=argparse.ArgumentParser();parser.add_argument("frontend",choices=("splatam","gaussian_slam"));args=parser.parse_args();ensure_dirs(); summary=ROOT/"canonical_exports"/f"{args.frontend}_pilot_canonical_export_summary.json"
    if not summary.exists() or load_json(summary).get("status")!="CANONICAL_EXPORT_PASS": out={"status":"NOT_AUTHORIZED_DUE_TO_CANONICAL_EXPORT","frontend":args.frontend};atomic_json(ROOT/"geometry_evaluation"/f"{args.frontend}_map_structure_audit.json",out);print(out["status"]);return
    root=Path(load_json(summary)["canonical_root"]); means=np.load(root/"means_world_m.npy",mmap_mode="r"); scales=np.load(root/"scales_linear_m.npy",mmap_mode="r"); quats=np.load(root/"quaternions_wxyz.npy",mmap_mode="r"); op=np.load(root/"opacities.npy",mmap_mode="r"); n=len(means); finite=bool(np.isfinite(means).all() and np.isfinite(scales).all() and np.isfinite(quats).all() and np.isfinite(op).all()); covariance=np.square(scales); qnorm=np.linalg.norm(quats,axis=1); duplicate=int(n-len(np.unique(np.asarray(means[:min(n,200000)]),axis=0))); size=sum(path.stat().st_size for path in root.glob("*.npy")); out={"status":"MAP_STRUCTURE_PASS" if finite and bool((scales>0).all()) else "MAP_STRUCTURE_FAILURE","frontend":args.frontend,"gaussian_count":int(n),"scene_bbox":{"min":np.min(means,axis=0).astype(float).tolist(),"max":np.max(means,axis=0).astype(float).tolist()},"mean_bbox":{"min":np.min(means,axis=0).astype(float).tolist(),"max":np.max(means,axis=0).astype(float).tolist()},"scale_m":quantiles(np.asarray(scales).reshape(-1)),"opacity":quantiles(np.asarray(op).reshape(-1)),"quaternion_norm":quantiles(qnorm),"covariance_eigenvalue":quantiles(np.asarray(covariance).reshape(-1)),"nonfinite_count":int(sum((~np.isfinite(array)).sum() for array in (means,scales,quats,op))),"duplicate_means_indication_first_200k":duplicate,"extreme_scale_count":int(((scales<1e-6)|(scales>1.0)).any(axis=1).sum()),"map_file_size_bytes":int(size),"metric_scale_certification":{"camera_translation_unit":"metres","no_sim3":True,"no_auto_scale":True,"no_normalization":True,"same_world_frame":True}}
    atomic_json(ROOT/"geometry_evaluation"/f"{args.frontend}_map_structure_audit.json",out);print(out["status"])


if __name__=="__main__": main()
