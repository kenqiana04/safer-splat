#!/usr/bin/env python3
"""Fresh-process component gates for generated Protocol V2 entry artifacts."""

from __future__ import annotations

import argparse
import json
from pathlib import Path


COMPONENTS = {
    "license": [("license/license_compatibility_audit.json", "status", "PASS_NONCOMMERCIAL_ACADEMIC_COMPATIBILITY")],
    "benchmark_identity": [("dataset_identity/eth3d_delivery_area_benchmark_identity.json", "status", "PASS_BENCHMARK_IDENTITY_UNAMBIGUOUS")],
    "asset_roles": [("asset_manifest/asset_role_matrix.json", "role_enum", ["MAPPING_INPUT_ONLY", "HELDOUT_EVALUATION_ONLY", "REFERENCE_ORACLE_ONLY", "CROSS_VIEW_EVALUATION_ONLY", "OPTIONAL_DIAGNOSTIC_ONLY", "PROHIBITED_AS_MAPPING_INPUT", "NOT_REQUIRED"])],
    "isolation": [("input_reference_partition/eth3d_asset_access_control_contract.json", "status", "PASS_PHYSICAL_ISOLATION_ENTRY_CONTRACT")],
    "modalities": [("modality_audit/modality_candidate_audit.json", "status", "PASS_MODALITY_ENTRY_AUDIT")],
    "frontends": [("frontend_audit/frontend_authority_audit.json", "status", "PASS_FRONTEND_ENTRY_CONTRACT")],
    "splatam_leakage": [("modality_audit/splatam_admissibility_audit.json", "ROUTE_M3_STATUS", "NOT_ADMISSIBLE_WITHOUT_REFERENCE_GEOMETRY_LEAKAGE")],
    "split": [("split_contract/future_split_generation_contract.json", "status", "FUTURE_SPLIT_CONTRACT_FEASIBLE_NOT_GENERATED")],
    "reference": [("reference_contract/eth3d_reference_authority_contract.json", "status", "REFERENCE_AUTHORITY_ENTRY_PATH_FEASIBLE_PENDING_ASSET_AUDIT")],
    "unknown": [("unknown_contract/runtime_unknown_entry_audit.json", "status", "UNKNOWN_CONTRACT_FEASIBLE_FOR_FUTURE_ASSET_VALIDATION")],
    "robot_route": [("route_robot_contract/eth3d_robot_benchmark_entry_contract.json", "status", "ROBOT_ROUTE_ENTRY_PATH_FEASIBLE_PENDING_REFERENCE_ASSET_AUDIT"), ("route_robot_contract/future_reference_route_contract.json", "status", "INDEPENDENT_REFERENCE_ROUTE_PATH_FEASIBLE_PENDING_ASSET_AUDIT")],
    "physical_budget": [("physical_budget/physical_budget_entry_contract.json", "status", "PHYSICAL_BUDGET_DERIVATION_PATH_FEASIBLE")],
    "evaluator": [("evaluator_contract/eth3d_protocol_v2_future_evaluator_contract.json", "status", "PROTOCOL_V2_FUTURE_EVALUATOR_PATH_FEASIBLE")],
    "decision": [("decision/entry_decision.json", "status", "PASS"), ("decision/entry_decision.json", "training_authorized", False)],
}


def run_from_cli(component: str) -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--task-root", type=Path, required=True)
    args = parser.parse_args()
    root = args.task_root.resolve()
    checks = []
    for relpath, key, expected in COMPONENTS[component]:
        path = root / relpath
        value = json.loads(path.read_text(encoding="utf-8"))
        actual = value[key]
        checks.append({"path": relpath, "field": key, "expected": expected, "actual": actual, "pass": actual == expected})
    result = {"component": component, "status": "PASS" if all(x["pass"] for x in checks) else "FAIL", "checks": checks}
    print(json.dumps(result, indent=2))
    return 0 if result["status"] == "PASS" else 2
