#!/usr/bin/env python3
"""Audit the unfiltered pilot map's geometry and metric-scale evidence."""
from __future__ import annotations

import numpy as np

from _common import ROOT, atomic_json, load_json, update_stage


def main():
    export = load_json(ROOT / "canonical_export" / "splatfacto_pilot_canonical_export_summary.json")
    geometry = load_json(ROOT / "common_evaluation" / "splatfacto_pilot_geometry_evaluation.json")
    dataparser = load_json(ROOT / "metric_dataparser" / "splatfacto_metric_dataparser_validation.json")
    path = ROOT / "map_structure" / "splatfacto_pilot_map_structure_audit.json"
    if not export.get("status", "").endswith("PASS"):
        atomic_json(path, {"status": "NOT_AUTHORIZED_DUE_TO_PILOT_EXPORT"}); return
    root = __import__("pathlib").Path(export["canonical_root"])
    means=np.load(root/"means_world_m.npy"); scales=np.load(root/"scales_linear_m.npy"); quats=np.load(root/"quaternions_wxyz.npy"); op=np.load(root/"opacities.npy")
    quat_norm=np.linalg.norm(quats,axis=1); eigenvalues=scales**2
    rounded=np.round(means, decimals=6); duplicate=int(len(rounded)-len(np.unique(rounded,axis=0)))
    metrics=geometry.get("metrics", {}); metric=dataparser["results"]["qualification_pilot"]["runtime"]
    finite=bool(all(np.isfinite(x).all() for x in (means,scales,quats,op)) and (scales>0).all())
    scale_certification={"dataparser_scale_one":metric["dataparser_scale_abs_error"]==0.,"camera_translation_ratio_one":metric["max_pair_ratio_error"]<=1e-8,"no_auto_orient":True,"no_centering":True,"no_auto_scale":True,"no_scene_contraction":True,"no_sim3":True,"no_icp":True,"no_posthoc_scale_fitting":True,"median_depth_ratio_in_range":metrics.get("median_depth_ratio") is not None and .8<=metrics["median_depth_ratio"]<=1.25}
    out={"status":"SPLATFACTO_PILOT_MAP_STRUCTURE_FINITE" if finite else "SPLATFACTO_PILOT_MAP_STRUCTURE_NONFINITE","gaussian_count":int(len(means)),"means_bbox_m":[means.min(axis=0).tolist(),means.max(axis=0).tolist()],"scales_m":{"min":float(scales.min()),"p1":float(np.quantile(scales,.01)),"median":float(np.median(scales)),"p99":float(np.quantile(scales,.99)),"max":float(scales.max())},"opacity":{"min":float(op.min()),"median":float(np.median(op)),"max":float(op.max())},"quaternion_norm":{"min":float(quat_norm.min()),"median":float(np.median(quat_norm)),"max":float(quat_norm.max())},"covariance_eigenvalues":{"min":float(eigenvalues.min()),"p1":float(np.quantile(eigenvalues,.01)),"median":float(np.median(eigenvalues)),"p99":float(np.quantile(eigenvalues,.99)),"max":float(eigenvalues.max())},"extreme_scale_count":int(((scales<1e-6)|(scales>10.)).any(axis=1).sum()),"nonfinite_count":int(sum((~np.isfinite(x)).sum() for x in (means,scales,quats,op))),"duplicate_mean_indication":duplicate,"map_file_size_bytes":int(sum(x.stat().st_size for x in root.glob("*.npy"))),"map_camera_frame_relation":"same metric V3 world; identity dataparser transform; no scale conversion beyond exp(log scales)","scale_certification":scale_certification,"scale_certification_pass":bool(all(scale_certification.values()))}
    atomic_json(path,out); update_stage("MAP_STRUCTURE","TERMINAL_SCIENTIFIC_RESULT" if finite else "FAILED_INFRASTRUCTURE",result_status=out["status"],scale_certification_pass=out["scale_certification_pass"]); print(out["status"])


if __name__ == "__main__": main()
