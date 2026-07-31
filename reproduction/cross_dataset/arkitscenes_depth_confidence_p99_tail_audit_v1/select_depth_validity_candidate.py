#!/usr/bin/env python3
"""Apply the preregistered fail-closed M0/M1/M2 decision hierarchy."""

from __future__ import annotations

import argparse
import json
from pathlib import Path

from audit_common import write_json


def read(path: Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8"))


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--output-root", type=Path, required=True)
    args = parser.parse_args()
    root = args.output_root.resolve()
    structural = read(root / "confidence_structural_validation.json")
    alignment = read(root / "confidence_alignment_decision.json")
    geometry = read(root / "full_train_mask_metrics.json")
    supervision = read(root / "mask_supervision_structure.json")
    ray = read(root / "mesh_ray_coverage_metrics.json")
    zero = read(root / "splatam_mask_compatibility_decision.json")
    implementation_error = bool(structural["implementation_error"] or alignment["implementation_error"])
    geometry_pass = {name: bool(metrics["geometry_pass"]) for name, metrics in geometry["global"].items()}
    structure_pass: dict[str, bool] = {}
    for name in ("M1_CONFIDENCE_GE1", "M2_CONFIDENCE_EQ2"):
        record = supervision["masks"][name]
        zero_ok = record["zero_valid_frame_count"] == 0 or bool(zero["zero_valid_depth_safe_without_algorithm_change"])
        structure_pass[name] = bool(record["structure_pass_before_zero_mask_semantics"] and zero_ok)
    no_hit = {
        name: float(record["classes"]["NO_MESH_RAY_HIT"]["fraction"])
        for name, record in ray.items()
    }
    all_masks_fail = not any(geometry_pass.values())
    mesh_coverage_dominant = (
        all_masks_fail
        and no_hit["M0_RAW_POSITIVE"] > 0.50
        and no_hit["M1_CONFIDENCE_GE1"] > 0.50
        and no_hit["M2_CONFIDENCE_EQ2"] > 0.50
        and max(no_hit.values()) - min(no_hit.values()) <= 0.10
        and not implementation_error
    )
    unresolved_zero_candidate = False
    for name in ("M1_CONFIDENCE_GE1", "M2_CONFIDENCE_EQ2"):
        record = supervision["masks"][name]
        if geometry_pass[name] and record["structure_pass_before_zero_mask_semantics"] and record["zero_valid_frame_count"] > 0 and zero["semantics_unresolved"]:
            unresolved_zero_candidate = True

    if implementation_error:
        final_status = "ARKITSCENES_CONFIDENCE_ALIGNMENT_IMPLEMENTATION_ERROR_IDENTIFIED"
        final_decision = "CORRECT_IMPLEMENTATION_AND_RERUN_ORIGINAL_M0_M1_M2_AUDIT"
        next_task = "CORRECT_ARKITSCENES_CONFIDENCE_ALIGNMENT_AND_RERUN_LOADER_AUDIT_V1"
        recommended_mask = None
        reason = "A reader or alignment implementation error met the preregistered evidence gate."
    elif geometry_pass["M0_RAW_POSITIVE"]:
        final_status = "PASS_ARKITSCENES_RAW_POSITIVE_DEPTH_INPUT_CONTRACT_FULL_TRAIN"
        final_decision = "KEEP_M0_RAW_POSITIVE_DEPTH_AS_PRIMARY_INPUT"
        next_task = "RESUME_ARKITSCENES_SPLATAM_SMOKE_FROM_FULL_TRAIN_M0_AUDIT_V1"
        recommended_mask = "M0_RAW_POSITIVE"
        reason = "M0 passed every unchanged full-TRAIN geometry gate, so stricter masks are not selected."
    elif geometry_pass["M1_CONFIDENCE_GE1"] and structure_pass["M1_CONFIDENCE_GE1"]:
        final_status = "PASS_ARKITSCENES_CONFIDENCE_GE1_METRIC_INPUT_CANDIDATE"
        final_decision = "FREEZE_M1_AS_NEW_PRIMARY_DATA_VALIDITY_CONTRACT_PENDING_DEDICATED_PROTOCOL"
        next_task = "FREEZE_ARKITSCENES_CONFIDENCE_GE1_MAPPING_INPUT_CONTRACT_V1"
        recommended_mask = "M1_CONFIDENCE_GE1"
        reason = "M0 failed while M1 passed unchanged geometry, supervision structure, and zero-mask compatibility gates."
    elif geometry_pass["M2_CONFIDENCE_EQ2"] and structure_pass["M2_CONFIDENCE_EQ2"]:
        final_status = "PASS_ARKITSCENES_CONFIDENCE_EQ2_METRIC_INPUT_CANDIDATE"
        final_decision = "FREEZE_M2_AS_NEW_PRIMARY_DATA_VALIDITY_CONTRACT_PENDING_DEDICATED_PROTOCOL"
        next_task = "FREEZE_ARKITSCENES_CONFIDENCE_EQ2_MAPPING_INPUT_CONTRACT_V1"
        recommended_mask = "M2_CONFIDENCE_EQ2"
        reason = "M1 did not qualify while M2 passed unchanged geometry, supervision structure, and zero-mask compatibility gates."
    elif unresolved_zero_candidate:
        final_status = "BLOCKED_BY_SPLATAM_ZERO_DEPTH_MASK_SEMANTICS"
        final_decision = "REQUIRE_SEPARATE_OFFICIAL_MAPPER_COMPATIBILITY_PROTOCOL"
        next_task = "AUDIT_SPLATAM_ZERO_DEPTH_FRAME_COMPATIBILITY_V1"
        recommended_mask = None
        reason = "A geometric and structural candidate contains zero-valid frames whose official mapper behavior remains unresolved."
    elif mesh_coverage_dominant:
        final_status = "BLOCKED_BY_ARKITSCENES_REFERENCE_MESH_COVERAGE_LIMITATION"
        final_decision = "DO_NOT_TRAIN_UNTIL_REFERENCE_GEOMETRY_PROTOCOL_IS_REDEFINED"
        next_task = "REDEFINE_ARKITSCENES_METRIC_REFERENCE_GEOMETRY_PROTOCOL_V1"
        recommended_mask = None
        reason = "More than half of every failed mask's >0.30 m tail has no mesh ray hit and confidence filtering changes that share by at most 10 percentage points."
    else:
        final_status = "NO_ARKITSCENES_METRIC_DEPTH_INPUT_CONTRACT_QUALIFIED"
        final_decision = "CLOSE_ARKITSCENES_SPLATAM_MAPPING_ROUTE_WITHOUT_TRAINING"
        next_task = "ETH3D_DELIVERY_AREA_LEARNED_3DGS_QUALIFICATION_V1"
        recommended_mask = None
        reason = "No implementation error or dominant mesh-coverage explanation was established, and none of M0/M1/M2 satisfies all preregistered gates."
    decision = {
        "FINAL_STATUS": final_status,
        "FINAL_DECISION": final_decision,
        "Only_next_task": next_task,
        "recommended_mask": recommended_mask,
        "recommendation_reason": reason,
        "implementation_error": implementation_error,
        "geometry_pass": geometry_pass,
        "structure_pass_with_zero_semantics": structure_pass,
        "mesh_no_hit_gt_030_fraction": no_hit,
        "mesh_coverage_dominant": mesh_coverage_dominant,
        "zero_mask_source_decision": zero["status"],
        "selection_order_applied": ["implementation_error", "M0", "M1", "M2", "zero_semantics_unresolved", "mesh_coverage", "no_qualified_contract"],
        "mask_contract_modified": False,
        "frame_deleted": False,
        "geometry_threshold_relaxed": False,
    }
    write_json(root / "decision" / "decision.json", decision)
    write_json(root / "depth_validity_candidate_decision.json", decision)
    print(final_status)
    print(final_decision)
    print(next_task)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
