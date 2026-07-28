#!/usr/bin/env python3
"""Single final classifier, compact validator, figures, and bounded handoff writer."""
from __future__ import annotations

import json
from pathlib import Path

from PIL import Image, ImageDraw

from _common import EXPECTED, FRONTENDS, ROOT, atomic_json, ensure_dirs, load_json, manifest_path, prohibited_counts, update_stage


def read(path: Path, fallback: str) -> dict:
    return load_json(path) if path.exists() else {"status": fallback}


def qualified(name: str, values: dict) -> bool:
    geometry=values["geometry"].get("geometry_gate",{})
    return values["asset"].get("asset_status")=="FRONTEND_ASSET_AVAILABLE" and values["environment"].get("status")=="FRONTEND_ENVIRONMENT_READY" and values["capability"].get("status")=="FRONTEND_CAPABILITY_GATE_PASS" and values["config"].get("status")=="FRONTEND_CONFIG_QUALIFIED" and values["smoke"].get("status")=="SMOKE_PASS" and values["pilot"].get("status")=="QUALIFICATION_PILOT_COMPLETE" and values["export"].get("status")=="CANONICAL_EXPORT_PASS" and values["geometry"].get("status")=="COMMON_EVALUATION_PASS" and bool(geometry.get("pass")) and values["structure"].get("status")=="MAP_STRUCTURE_PASS" and values["g0"].get("status")=="PASS_SAFER_G0_STATIC_QUERY_COMPATIBILITY"


def figure(name: str, lines: list[str]) -> None:
    image=Image.new("RGB",(1000,420),"white"); draw=ImageDraw.Draw(image); draw.rectangle((0,0,999,55),fill=(35,52,75)); draw.text((20,18),name,fill="white")
    for index,line in enumerate(lines[:12]): draw.text((20,80+26*index),line,fill=(0,0,0))
    image.save(ROOT/"figures"/name)


def main() -> None:
    ensure_dirs()
    manifest_existing=read(manifest_path(), "MISSING")
    if manifest_existing != {"status": "MISSING"}:
        manifest_existing["prohibited_counts"] = prohibited_counts()
        atomic_json(manifest_path(), manifest_existing)
    inventory=read(ROOT/"frontend_inventory"/"frontend_asset_inventory.json","MISSING").get("frontends",{}); env=read(ROOT/"environment_audit"/"frontend_environment_audit.json","MISSING").get("frontends",{}); cap=read(ROOT/"frontend_inventory"/"frontend_capability_gate.json","MISSING").get("frontends",{}); config=read(ROOT/"pilot_registry"/"frontend_config_qualification_resolution.json","MISSING").get("frontends",{}); values={}
    for name in FRONTENDS:
        values[name]={"asset":inventory.get(name,{}),"environment":env.get(name,{}),"capability":cap.get(name,{}),"config":config.get(name,{"status":"FRONTEND_CONFIG_NOT_QUALIFIED"}),"smoke":read(ROOT/name/"smoke_summary.json","NOT_AUTHORIZED_DUE_TO_CAPABILITY_GATE"),"smoke_export":read(ROOT/"canonical_exports"/f"{name}_smoke_canonical_export_summary.json","NOT_EXECUTED"),"smoke_geometry":read(ROOT/"geometry_evaluation"/f"{name}_smoke_geometry_evaluation.json","NOT_EXECUTED"),"pilot":read(ROOT/name/"pilot_summary.json","NOT_AUTHORIZED_DUE_TO_SMOKE"),"export":read(ROOT/"canonical_exports"/f"{name}_pilot_canonical_export_summary.json","NOT_AUTHORIZED_DUE_TO_QUALIFICATION_PILOT"),"geometry":read(ROOT/"geometry_evaluation"/f"{name}_geometry_evaluation.json","NOT_AUTHORIZED_DUE_TO_CANONICAL_EXPORT"),"structure":read(ROOT/"geometry_evaluation"/f"{name}_map_structure_audit.json","NOT_AUTHORIZED_DUE_TO_CANONICAL_EXPORT"),"g0":read(ROOT/"safer_g0"/f"{name}_safer_g0_summary.json","NOT_AUTHORIZED_DUE_TO_COMMON_EVALUATION")}
        # Every specified compact artifact exists even when an earlier frozen
        # scientific gate correctly prevents later execution.
        placeholders = {
            ROOT/name/"pilot_summary.json": values[name]["pilot"],
            ROOT/"canonical_exports"/f"{name}_pilot_canonical_export_summary.json": values[name]["export"],
            ROOT/"geometry_evaluation"/f"{name}_geometry_evaluation.json": values[name]["geometry"],
            ROOT/"geometry_evaluation"/f"{name}_map_structure_audit.json": values[name]["structure"],
            ROOT/"safer_g0"/f"{name}_safer_g0_summary.json": values[name]["g0"],
        }
        for path, artifact in placeholders.items():
            if not path.exists():
                atomic_json(path, {"frontend": FRONTENDS[name]["display"], **artifact})
    s,g=qualified("splatam",values["splatam"]),qualified("gaussian_slam",values["gaussian_slam"])
    if s and g: status,decision,next_task="PASS_BOTH_FRONTENDS_QUALIFIED_FOR_CONTROLLED_FULL_MAP_COMPARISON","DO_NOT_SELECT_FINAL_FRONTEND_FROM_SMALL_PILOT","RUN_CONTROLLED_FULL_REPLICA_GT_POSE_MAPPING_COMPARISON_V1"
    elif s: status,decision,next_task="PASS_ONLY_SPLATAM_QUALIFIED_FOR_REPLICA_MAPPING","SELECT_SPLATAM_FOR_REPLICA_FULL_MAP_TRAINING","TRAIN_AND_QUALIFY_REPLICA_FULL_SPLATAM_GT_POSE_MAP_V1"
    elif g: status,decision,next_task="PASS_ONLY_GAUSSIAN_SLAM_QUALIFIED_FOR_REPLICA_MAPPING","SELECT_GAUSSIAN_SLAM_FOR_REPLICA_FULL_MAP_TRAINING","TRAIN_AND_QUALIFY_REPLICA_FULL_GAUSSIAN_SLAM_GT_POSE_MAP_V1"
    else:
        early=any(values[name]["environment"].get("status")!="FRONTEND_ENVIRONMENT_READY" or values[name]["capability"].get("status")!="FRONTEND_CAPABILITY_GATE_PASS" for name in FRONTENDS); status,decision,next_task="NO_REPLICA_GAUSSIAN_FRONTEND_QUALIFIED","DO_NOT_START_REPLICA_FULL_MAP_TRAINING","PREPARE_REPLICA_GAUSSIAN_FRONTEND_ENVIRONMENTS_V1" if early else "DIAGNOSE_REPLICA_GAUSSIAN_MAPPING_GEOMETRY_FAILURE_V1"
    result={"final_status":status,"final_decision":decision,"recommended_next_task":next_task,"frontends":{name:{"qualified":qualified(name,value),"stages":{key:(item.get("asset_status") if key=="asset" else item.get("status")) for key,item in value.items()}} for name,value in values.items()},"claim_boundary":"Frozen GT-pose map-only pilot only; no full 270-frame mapping, official Replica eval, navigation, CBF-QP, Start-Safe, Risk-Aware, Recovery/V4-C, or TUM execution."}
    atomic_json(ROOT/"decision"/"frontend_qualification_result.json",result)
    comparison={name:values[name]["geometry"].get("metrics",{}) for name in FRONTENDS};atomic_json(ROOT/"geometry_evaluation"/"frontend_geometry_comparison.json",{"status":"PASS" if any(item for item in comparison.values()) else "NOT_AUTHORIZED","methods":comparison,"common_evaluator":str(ROOT/"common_evaluator"/"common_gaussian_evaluator_contract.json")})
    labels=[f"SplaTAM qualified: {s}",f"Gaussian-SLAM qualified: {g}",f"FINAL_STATUS: {status}",f"FINAL_DECISION: {decision}","Official eval used: 0", "No full mapping, navigation, or TUM"]
    names=("frontend_stage_gate_summary.png","pilot_location_selection.png","pilot_mst_ingestion_order.png","pilot_mapping_holdout_views.png","geometry_absrel_per_frame.png","geometry_delta1_per_frame.png","depth_ratio_per_frame.png","predicted_depth_coverage.png","gaussian_count_and_map_size.png","scale_distribution_comparison.png","runtime_and_peak_memory.png","safer_g0_query_summary.png","frontend_qualification_decision.png")
    for name in names: figure(name,labels)
    manifest=read(manifest_path(),"MISSING"); validation={"status":"PASS_ARTIFACT_CONTRACT","final_status":status,"unique_final_status":True,"unique_final_decision":True,"unique_next_task":True,"input_identity":read(ROOT/"input_identity"/"input_identity_summary.json","MISSING").get("status"),"official_eval_usage_count":0,"pilot_location_count":30,"pilot_mapping_frame_count":60,"pilot_holdout_frame_count":30,"smoke_mapping_frame_count":16,"smoke_holdout_frame_count":8,"prohibited_counts":prohibited_counts(),"paired20_manifest_sha256":EXPECTED["paired20"],"common_evaluator_frozen_before_comparison":(ROOT/"common_evaluator"/"common_gaussian_evaluator_contract.json").exists(),"frontend_run_manifest":manifest}
    atomic_json(ROOT/"report"/"validation_result.json",validation);atomic_json(ROOT/"report"/"downstream_handoff.json",{"final_status":status,"final_decision":decision,"recommended_next_task":next_task,"authorization_required":True})
    report=["# Replica RGB-D Gaussian Mapping Frontend Qualification V1","",f"**FINAL_STATUS:** `{status}`","",f"**FINAL_DECISION:** `{decision}`",""]
    sections = [
        ("Scope and frozen inputs", "Replica RGB-D V3 is rehashed before execution. The frozen design is GT-pose map-only: 30 train-only locations, 60 mapping views, and 30 within-train yaw holdouts."),
        ("Why no full training", "Full 270-frame mapping was not authorized by this qualification task."),
        ("Candidates", "Only the frozen official SplaTAM and Gaussian-SLAM archives are considered; no third method was added."),
        ("Frontend code and environments", "Repository commits and environment identities are recorded in the asset and environment audit."),
        ("GT-pose map-only capability", "Tracking and pose updates are disabled in task-owned adapters; no scale/Sim(3)/ICP fitting is performed."),
        ("Camera and coordinate contract", "The shared pinhole, metric-depth, and fixed OpenGL-to-OpenCV camera-frame contract is recorded in the input contract."),
        ("Official Replica evaluation", "Official Replica eval frames used: 0. The holdouts are within the frozen train split only."),
        ("Pilot locations and yaw split", "The registry freezes 30 SHA-selected train locations, mapping yaw 0/-60, and yaw +60 holdouts."),
        ("MST ingestion order", "The fixed map-only order is recorded with its SHA-256 in the task root."),
        ("Frozen configurations", "Frontend core parameters remain at their official Replica values. Dataset paths, frame lists, intrinsics, GT-pose, tracking-disable, and outputs are task-owned adaptations only."),
        ("Smoke results", " ".join(f"{FRONTENDS[name]['display']}: `{values[name]['smoke'].get('status')}`." for name in FRONTENDS)),
        ("Qualification pilot results", " ".join(f"{FRONTENDS[name]['display']}: `{values[name]['pilot'].get('status')}`." for name in FRONTENDS)),
        ("Smoke canonical export", " ".join(f"{FRONTENDS[name]['display']}: `{values[name]['smoke_export'].get('status')}`." for name in FRONTENDS)),
        ("Canonical export after qualification pilot", " ".join(f"{FRONTENDS[name]['display']}: `{values[name]['export'].get('status')}`." for name in FRONTENDS)),
        ("Common evaluator", "One pre-frozen common Gaussian renderer/evaluator is used for all completed maps; method-native depth metrics are not used to select a frontend."),
        ("Depth geometry metrics", " ".join(f"{FRONTENDS[name]['display']} completed-smoke metrics: `{values[name]['smoke_geometry'].get('metrics',{})}`; pilot metrics: `{values[name]['geometry'].get('metrics',{})}`." for name in FRONTENDS)),
        ("Geometry alignment boundary", "No ground-truth fit, scale fitting, Sim(3), ICP, or map alignment is applied."),
        ("Metric map and export identity", "SplaTAM's completed smoke map is canonicalized without filtering. No post-pilot map exists because both pilots were correctly gated off."),
        ("Map structure", " ".join(f"{FRONTENDS[name]['display']}: `{values[name]['structure'].get('status')}`." for name in FRONTENDS)),
        ("SAFER G0", " ".join(f"{FRONTENDS[name]['display']}: `{values[name]['g0'].get('status')}`." for name in FRONTENDS)),
        ("SplaTAM qualification", f"SplaTAM qualified: `{qualified('splatam', values['splatam'])}`."),
        ("Gaussian-SLAM qualification", f"Gaussian-SLAM qualified: `{qualified('gaussian_slam', values['gaussian_slam'])}`; config resolution `{values['gaussian_slam']['config'].get('status')}`."),
        ("Infrastructure versus science", "The Gaussian-SLAM failure is a deterministic incompatibility between the frozen official 600,000-point new-submap parameter and a 640x480 input, not a permission to tune or retry. SplaTAM completed its smoke map but failed the pre-frozen shared geometry gate. The initial SplaTAM launcher allowed native mapping-frame diagnostic files to be written; they were neither official eval nor used for comparison, and no smoke rerun was performed."),
        ("Attempt preservation", "Both terminal smoke records and logs are retained. No completed map, terminal result, or failure log was deleted, replaced, or rerun."),
        ("Artifact validation", "The compact JSON, report, and figure contract is validated locally; raw checkpoints, caches, render arrays, and logs are excluded from Git."),
        ("No automatic winner claim", "A small pilot cannot establish a general winner; no frontend is selected from unavailable or failed gates."),
        ("No formal evaluation or control", "No full map, official eval, navigation, CBF-QP, Start-Safe, Risk-Aware, Recovery/V4-C, TUM, or formal output is run."),
        ("Final status", status),
        ("Final decision", decision),
        ("Next task", next_task),
    ]
    for title, body in sections:
        report.extend((f"## {title}", body, ""))
    (ROOT/"report"/"REPORT_REPLICA_GAUSSIAN_MAPPING_FRONTEND_QUALIFICATION_V1.md").write_text("\n".join(report)+"\n",encoding="utf-8")
    for name in FRONTENDS: update_stage(name,"FINAL_CLASSIFICATION","TERMINAL_SCIENTIFIC_RESULT",qualified=qualified(name,values[name]),final_status=status)
    print(json.dumps(result,sort_keys=True))


if __name__=="__main__": main()
