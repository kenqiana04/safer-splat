#!/usr/bin/env python3
"""Gate the only permissible next task from the decomposed mechanism."""
from __future__ import annotations
from _common import ROOT, atomic_json, load_json

def main()->None:
    c=load_json(ROOT/"classification/replica_asset_failure_classification.json")
    if c["OVERALL_ASSET_AUDIT_CLASSIFICATION"]=="PURE_GEOMETRY_COVERAGE_DEFECT":
        feasibility="NOT_FIXABLE_WITHOUT_CHANGING_SCENE_GEOMETRY_OR_CAMERA_PROTOCOL";next_task="DESIGN_REPLICA_RENDER_PROTOCOL_V3_WITH_PRE_RENDER_ASSET_COVERAGE_QUALIFICATION";final="PASS_REPLICA_ASSET_AUDIT_REQUIRES_NEW_CAMERA_PROTOCOL"
    else:
        feasibility="UNRESOLVED";next_task="REPLICA_ASSET_RENDERER_MINIMAL_REPRODUCTION_V2";final="BLOCKED_BY_REPLICA_ASSET_CAUSE_UNRESOLVED"
    payload={"status":final,"REPAIR_FEASIBILITY":feasibility,"recommended_next_task":next_task,"camera_protocol_fields_changed":[],"formal_asset_repair_applied":False,"official_alternate_asset_diagnostic_outcome":"official habitat/mesh_semantic.ply restores depth for the sampled failures but is a distinct semantic mesh and was not qualified as a formal RGB render asset; it is diagnostic-only, not an approved V1 replacement","forbidden_pseudo_repairs":["delete bad frames","replace yaw","copy RGB/depth","relax checker","patch official mesh","use double-sided diagnostic mesh formally","substitute semantic mesh without a new formal qualification"]}
    atomic_json(ROOT/"classification/replica_asset_repair_feasibility.json",payload)
    atomic_json(ROOT/"report/downstream_handoff.json",{"status":final,"recommended_next_task":next_task,"TUM_final_decision":"CLOSE_TUM_NAVIGATION_BENCHMARK_KEEP_SAFETY_CASE_STUDY","Replica_scene_asset_qualification_not_equivalent_to":["RGB-D dataset qualification","Gaussian mapping qualification","SAFER baseline qualification","FAS-CBF evaluation"]})

if __name__=="__main__":main()
