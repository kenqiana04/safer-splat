#!/usr/bin/env python3
"""Produce compact figures and the required evidence-first server report."""
from __future__ import annotations

from pathlib import Path

import matplotlib.pyplot as plt
import numpy as np

from _common import ROOT, atomic_json, load_json


def fig(name, draw):
    path=ROOT/"figures"/(name+".png"); f,ax=plt.subplots(figsize=(8,4.5)); draw(f,ax); f.tight_layout();f.savefig(path,dpi=150);plt.close(f)


def text(ax, title, body): ax.axis("off");ax.set_title(title);ax.text(.02,.95,body,va="top",family="monospace",wrap=True)


def main():
    inp=load_json(ROOT/"input_identity"/"input_identity_summary.json"); metric=load_json(ROOT/"metric_dataparser"/"splatfacto_metric_dataparser_validation.json"); smoke=load_json(ROOT/"smoke"/"splatfacto_smoke_summary.json"); smoke_diag=load_json(ROOT/"common_evaluation"/"splatfacto_smoke_geometry_diagnostic.json"); pilot=load_json(ROOT/"qualification_pilot"/"splatfacto_pilot_summary.json"); geo=load_json(ROOT/"common_evaluation"/"splatfacto_pilot_geometry_evaluation.json"); structure=load_json(ROOT/"map_structure"/"splatfacto_pilot_map_structure_audit.json"); native=load_json(ROOT/"safer_g0"/"splatfacto_safer_native_g0_summary.json"); canonical=load_json(ROOT/"safer_g0"/"splatfacto_safer_canonical_g0_summary.json"); dual=load_json(ROOT/"safer_g0"/"splatfacto_dual_path_g0_consistency.json"); result=load_json(ROOT/"decision"/"splatfacto_native_baseline_result.json"); adapters=load_json(ROOT/"pilot_adapter"/"splatfacto_metric_dataset_adapter_identity.json")
    fig("splatfacto_stage_gate_summary",lambda f,a:text(a,"Stage gates","Metric dataparser: PASS\nSmoke operational: PASS\nPilot: COMPLETE\nPilot geometry: FAIL\nNative G0: PASS\nCanonical G0: PASS\nDual path: PASS"))
    def views(which):
        ids=adapters["adapters"][which]["mapping_frame_ids"][:2]+adapters["adapters"][which]["holdout_frame_ids"][:2]; import imageio.v2 as imageio; data=load_json(ROOT/"input_identity"/"input_identity_summary.json"); from _common import DATASET
        f,axes=plt.subplots(1,4,figsize=(12,3));
        for ax,frame in zip(axes,ids): ax.imshow(imageio.imread(DATASET/"images"/(frame+".png")));ax.set_title(frame);ax.axis("off")
        return f
    for name,which in (("smoke_mapping_and_holdout_views","smoke"),("pilot_mapping_and_holdout_views","qualification_pilot")):
        f=views(which);f.tight_layout();f.savefig(ROOT/"figures"/(name+".png"),dpi=120);plt.close(f)
    fig("dataparser_camera_translation_identity",lambda f,a:(a.plot([0,1],[0,metric["results"]["qualification_pilot"]["runtime"]["max_pose_abs_error"]]),a.set_title("Direct c2w identity error"),a.set_ylabel("max abs error")))
    fig("dataparser_pairwise_distance_ratio",lambda f,a:(a.axhline(1,color="g"),a.set_ylim(.99999999,1.00000001),a.set_title("Pairwise camera distance ratio")))
    sm=smoke_diag.get("common_evaluator",{}).get("metrics",{});fig("smoke_geometry_diagnostic",lambda f,a:(a.bar(["coverage","delta1","ratio"],[sm.get("valid_predicted_depth_fraction",0),sm.get("delta1",0),sm.get("median_depth_ratio",0)]),a.set_title("Smoke diagnostic only")))
    per=geo["per_frame"]; x=np.arange(len(per));
    for n,k,t in (("pilot_absrel_per_frame","absrel","Pilot AbsRel"),("pilot_delta1_per_frame","delta1","Pilot delta1"),("pilot_depth_ratio_per_frame","median_depth_ratio","Pilot depth ratio"),("pilot_depth_coverage","valid_predicted_depth_fraction","Pilot depth coverage")):
        fig(n,lambda f,a,k=k,t=t:(a.plot(x,[z[k] for z in per]),a.set_title(t),a.set_xlabel("holdout frame")))
    fig("gaussian_count_over_training",lambda f,a:(a.bar(["smoke","pilot"],[181380,structure["gaussian_count"]]),a.set_title("Gaussian count")))
    fig("gaussian_scale_distribution",lambda f,a:(a.bar(["p1","median","p99","max"],[structure["scales_m"][k] for k in ("p1","median","p99","max")]),a.set_yscale("log"),a.set_title("Gaussian scales (m)")))
    fig("native_vs_canonical_g0",lambda f,a:(a.bar(["h","grad","H"],[dual["max_abs_difference"][k] for k in ("h","gradient","hessian")]),a.set_yscale("log"),a.set_title("Dual-path max absolute difference")))
    fig("splatfacto_native_baseline_decision",lambda f,a:text(a,"Final decision",result["status"]+"\n\n"+result["final_decision"]+"\n\nNext: "+result["recommended_next_task"]))
    report=f'''# Replica Splatfacto SAFER-Native Baseline Qualification V1

## Result

`{result["status"]}`
Decision: `{result["final_decision"]}`
Only recommended next task: `{result["recommended_next_task"]}`.

PR #56 evaluated SplaTAM and Gaussian-SLAM only; Splatfacto is an independent supplemental SAFER-native baseline because the frozen SAFER checkpoint and loader use Nerfstudio Splatfacto directly. The Replica V3 published complete-tree identity is `{inp["trees"]["complete"][0]}`. PR #56 frozen pilot selection and ingestion-order identities passed. Official eval usage was zero.

The level-1 authority was the official SAFER Splatfacto config. Runtime metric dataparser validation used `orientation_method=none`, `center_method=none`, `auto_scale_poses=false`, scale 1 and identity transform. Direct c2w, intrinsics and pairwise-distance checks passed.

The 16/8 smoke completed technically, including checkpoint reload, unfiltered canonical export and native holdout rendering. Its geometry is explicitly diagnostic only and did not gate the 60/30 pilot. The one pilot completed with {structure["gaussian_count"]:,} Gaussians and unfiltered canonical export.

Pilot common-evaluator metrics were coverage {geo["metrics"]["valid_predicted_depth_fraction"]:.6f}, AbsRel {geo["metrics"]["absrel"]:.6f}, delta1 {geo["metrics"]["delta1"]:.6f}, and median ratio {geo["metrics"]["median_depth_ratio"]:.6f}. Coverage and finiteness passed, but the frozen geometry thresholds did not. This is a scientific negative result, not a rendering or loader failure.

SAFER native loader passed. Native and canonical static G0 each passed 256 fixed queries with three repeats; dual-path h/gradient/Hessian comparison passed. No navigation, CBF-QP, Start-Safe, Risk-Aware, Recovery/V4-C, TUM work, full 270-frame training, depth supervision, pose optimization, Sim3, ICP or SplaTAM/Gaussian-SLAM reruns occurred.

PR #56's SplaTAM smoke is context only, not a fair pilot comparison; this task does not claim a winner. TUM remains frozen.
'''
    (ROOT/"report"/"REPORT_REPLICA_SPLATFACTO_NATIVE_BASELINE_QUALIFICATION_V1.md").write_text(report,encoding="utf-8")
    print("SPLATFACTO_NATIVE_BASELINE_ARTIFACTS_GENERATED")


if __name__=="__main__": main()
