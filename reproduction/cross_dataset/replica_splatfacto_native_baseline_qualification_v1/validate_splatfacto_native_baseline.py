#!/usr/bin/env python3
"""Validate immutable boundaries and the single final classification."""
from __future__ import annotations

import json
import subprocess
from pathlib import Path

from _common import EXPECTED, ROOT, atomic_json, load_json, sha256_path


def main():
    manifest=load_json(ROOT/"splatfacto_run_manifest.json"); inp=load_json(ROOT/"input_identity"/"input_identity_summary.json"); metric=load_json(ROOT/"metric_dataparser"/"splatfacto_metric_dataparser_validation.json"); result=load_json(ROOT/"decision"/"splatfacto_native_baseline_result.json"); counts=manifest["prohibited_counts"]
    zero=["official_eval_frame_count_used","depth_supervision_count","camera_optimizer_count","pose_optimization_count","auto_scale_count","auto_orient_count","centering_count","scene_contraction_count","colmap_count","sim3_count","icp_count","scale_fitting_count","hyperparameter_sweep_count","smoke_scientific_rerun_count","pilot_scientific_rerun_count","canonical_export_filter_count","safer_core_modification_count","safer_navigation_count","cbf_qp_count","start_safe_count","risk_aware_count","recovery_v4c_count","splatam_rerun_count","gaussian_slam_rerun_count","tum_rollout_count","full_270_frame_training_count"]
    checks={"pr56_head":inp["checks"]["pr56_head"],"dataset_tree":inp["checks"]["complete_tree"],"pilot_and_order":inp["checks"]["pilot_selection_core"] and inp["checks"]["ingestion_order"],"metric_dataparser":all(metric["checks"].values()),"prohibited_zero":all(counts[k]==0 for k in zero),"pilot_once":counts["pilot_scientific_run_count"]==1,"all_terminal":all(v!="NOT_STARTED" and v!="RUNNING" for v in manifest["stages"].values()),"final_status_unique":result["status"]=="PASS_SPLATFACTO_NATIVE_COMPATIBILITY_ONLY_GEOMETRY_NOT_QUALIFIED","report_exists":(ROOT/"report"/"REPORT_REPLICA_SPLATFACTO_NATIVE_BASELINE_QUALIFICATION_V1.md").is_file()}
    gpu=subprocess.check_output(["nvidia-smi","-i","1","--query-compute-apps=pid","--format=csv,noheader"],text=True,stderr=subprocess.STDOUT).strip();checks["gpu1_clean"]=gpu in ("", "No running compute processes found")
    out={"status":"PASS_REPLICA_SPLATFACTO_NATIVE_BASELINE_VALIDATION" if all(checks.values()) else "FAIL_REPLICA_SPLATFACTO_NATIVE_BASELINE_VALIDATION","checks":checks,"prohibited_counts":counts,"final_status":result["status"],"final_decision":result["final_decision"],"next_task":result["recommended_next_task"]}
    atomic_json(ROOT/"decision"/"validation_result.json",out);print(out["status"])


if __name__=="__main__":main()
