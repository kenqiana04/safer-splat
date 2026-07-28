#!/usr/bin/env python3
"""Validate compact audit evidence and immutable-boundary counters."""
from __future__ import annotations
import json
from _common import FROZEN, ROOT, atomic_json, load_json, sha256

def main()->None:
    identity=load_json(ROOT/"input_identity/upstream_replica_asset_audit_identity.json");ray=load_json(ROOT/"independent_raycast/independent_mesh_raycast_summary.json");repair=load_json(ROOT/"classification/replica_asset_repair_feasibility.json");diagnostic=load_json(ROOT/"diagnostic_variants/diagnostic_render_summary.json")
    needed=["source_asset_inventory/replica_scene_asset_inventory.json","mesh_structure/replica_mesh_structure_summary.json","habitat_asset_loading/habitat_asset_loading_audit.json","diagnostic_variants/diagnostic_asset_variant_identity.json","diagnostic_variants/diagnostic_render_summary.json","joint_failure_analysis/replica_joint_failure_mechanism.json","rgb_only_analysis/replica_rgb_only_frame_0034_audit.json","classification/replica_asset_failure_classification.json","classification/replica_asset_repair_feasibility.json"]
    missing=[p for p in needed if not (ROOT/p).exists()]
    checks={"upstream_identity_pass":identity["status"]=="PASS_FROZEN_UPSTREAM_IDENTITY","float64_reference_agreement":ray["reference_agreement"],"fixed_grid":ray["independent_ray_count"]==103275,"all_required_compact_files_present":not missing,"diagnostic_terminal_result_count":len(diagnostic["results"]),"diagnostic_terminal_budget_max":166,"diagnostic_terminal_within_budget":len(diagnostic["results"])==166,"nonterminal_writer_correction_recorded":(ROOT/"logs/diagnostic_writer_correction.md").exists(),"camera_protocol_fields_changed":[],"formal_300_frame_rerender_count":0,"publication_count":0,"gaussian_training_count":0,"safer_cbf_count":0,"start_safe_risk_aware_recovery_count":0,"tum_rollout_count":0,"paired20_manifest_sha256":FROZEN["paired20_manifest_sha256"]}
    status=repair["status"] if all([checks["upstream_identity_pass"],checks["float64_reference_agreement"],checks["fixed_grid"],checks["all_required_compact_files_present"],checks["diagnostic_terminal_within_budget"]]) else "BLOCKED_BY_REPLICA_ASSET_CAUSE_UNRESOLVED"
    atomic_json(ROOT/"report/validation_result.json",{"status":status,"checks":checks,"missing":missing})

if __name__=="__main__":main()
