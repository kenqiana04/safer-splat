#!/usr/bin/env python3
"""Issue one unambiguous compatibility and geometry classification."""
from __future__ import annotations

from _common import ROOT, atomic_json, load_json, set_actual_count, update_stage


def main():
    set_actual_count("pilot_scientific_run_count", 1)
    smoke=load_json(ROOT/"smoke"/"splatfacto_smoke_summary.json"); smoke_export=load_json(ROOT/"canonical_export"/"splatfacto_smoke_canonical_export_summary.json"); pilot=load_json(ROOT/"qualification_pilot"/"splatfacto_pilot_summary.json"); export=load_json(ROOT/"canonical_export"/"splatfacto_pilot_canonical_export_summary.json"); geometry=load_json(ROOT/"common_evaluation"/"splatfacto_pilot_geometry_evaluation.json"); structure=load_json(ROOT/"map_structure"/"splatfacto_pilot_map_structure_audit.json"); loader=load_json(ROOT/"safer_native_loader"/"splatfacto_safer_native_loader_summary.json"); native=load_json(ROOT/"safer_g0"/"splatfacto_safer_native_g0_summary.json"); canonical=load_json(ROOT/"safer_g0"/"splatfacto_safer_canonical_g0_summary.json"); dual=load_json(ROOT/"safer_g0"/"splatfacto_dual_path_g0_consistency.json")
    native_pass=all((smoke["status"]=="SPLATFACTO_SMOKE_OPERATIONAL_PASS", smoke_export["status"].endswith("PASS"), pilot["status"]=="SPLATFACTO_PILOT_COMPLETE", export["status"].endswith("PASS"), loader["status"]=="SPLATFACTO_SAFER_NATIVE_LOADER_PASS", native["status"].endswith("PASS"), canonical["status"].endswith("PASS"), dual["status"].endswith("PASS")))
    geometry_pass=bool(geometry.get("geometry_pass") and structure.get("status")=="SPLATFACTO_PILOT_MAP_STRUCTURE_FINITE")
    if native_pass and geometry_pass:
        final_status="PASS_SPLATFACTO_NATIVE_COMPATIBILITY_AND_PILOT_GEOMETRY"; decision="AUTHORIZE_SPLATFACTO_FULL_REPLICA_MAP_TRAINING_AS_NATIVE_BASELINE"; next_task="TRAIN_AND_QUALIFY_FULL_REPLICA_SPLATFACTO_NATIVE_MAP_V1"
    elif native_pass:
        final_status="PASS_SPLATFACTO_NATIVE_COMPATIBILITY_ONLY_GEOMETRY_NOT_QUALIFIED"; decision="KEEP_SPLATFACTO_AS_NATIVE_COMPATIBILITY_BASELINE_NOT_NAVIGATION_MAP"; next_task="REPLICA_GAUSSIAN_FRONTEND_FAILURE_DECOMPOSITION_AND_PROTOCOL_CONFORMANCE_AUDIT_V1"
    elif geometry_pass:
        final_status="SPLATFACTO_GEOMETRY_QUALIFIED_BUT_SAFER_NATIVE_COMPATIBILITY_FAILED"; decision="DO_NOT_START_FULL_TRAINING_UNTIL_NATIVE_G0_IS_RESOLVED"; next_task="DIAGNOSE_SPLATFACTO_SAFER_NATIVE_LOADER_G0_V1"
    else:
        final_status="SPLATFACTO_NATIVE_BASELINE_OPERATIONAL_GATE_FAILED"; decision="DO_NOT_START_SPLATFACTO_QUALIFICATION_PILOT"; next_task="DIAGNOSE_SPLATFACTO_NATIVE_PIPELINE_OPERATIONAL_FAILURE_V1"
    out={"status":final_status,"final_decision":decision,"recommended_next_task":next_task,"native_compatibility_pass":native_pass,"pilot_geometry_pass":geometry_pass,"pilot_geometry_gate":geometry.get("geometry_gate"),"geometry_metrics":geometry.get("metrics"),"scale_certification_pass":structure.get("scale_certification_pass"),"scope":{"full_270_frame_training":False,"official_eval_used":False,"navigation":False,"cbf_qp":False,"tum_execution":False,"splatam_or_gaussian_slam_rerun":False},"unresolved_critical_evidence":"Pilot depth geometry does not meet the frozen qualification thresholds; this is a scientific negative result, not an operational or native-loader failure." if native_pass and not geometry_pass else None}
    atomic_json(ROOT/"decision"/"splatfacto_native_baseline_result.json",out);atomic_json(ROOT/"decision"/"downstream_handoff.json",{"task":"Replica Splatfacto SAFER-native baseline qualification V1","final_status":final_status,"final_decision":decision,"next_task":next_task,"resume_or_full_training_authorized":bool(native_pass and geometry_pass)})
    update_stage("FINAL_CLASSIFICATION","TERMINAL_SCIENTIFIC_RESULT",result_status=final_status,final_decision=decision,next_task=next_task);print(final_status)


if __name__=="__main__": main()
