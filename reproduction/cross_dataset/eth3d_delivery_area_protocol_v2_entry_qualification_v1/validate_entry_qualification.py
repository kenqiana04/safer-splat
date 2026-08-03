#!/usr/bin/env python3
"""Fail-closed validator for the metadata-only ETH3D entry audit."""

from __future__ import annotations

import argparse
import hashlib
import json
import re
from pathlib import Path


REQUIRED_SCRIPTS = [
    "freeze_protocol_v2_entry_inputs.py", "audit_eth3d_official_authority.py", "parse_eth3d_delivery_area_assets.py",
    "validate_eth3d_http_metadata.py", "audit_eth3d_license.py", "audit_dataset_benchmark_identity.py",
    "classify_asset_roles.py", "audit_input_reference_isolation.py", "audit_delivery_area_modalities.py",
    "audit_mapping_frontends.py", "audit_splatam_gt_depth_leakage.py", "build_future_split_contract.py",
    "build_reference_authority_contract.py", "audit_runtime_unknown_entry.py", "build_robot_route_entry_contract.py",
    "build_physical_budget_entry_contract.py", "build_future_evaluator_contract.py", "select_entry_decision.py",
]

REQUIRED_FIGURES = [
    "eth3d_benchmark_identity.png", "delivery_area_variant_comparison.png", "official_asset_role_matrix.png",
    "train_eval_oracle_isolation.png", "gt_depth_leakage_boundary.png", "modality_selection_flow.png",
    "frontend_selection_flow.png", "rig_group_split_contract.png", "cross_view_evaluation_design.png",
    "reference_authority_layers.png", "runtime_unknown_entry_options.png", "unknown_not_free_flow.png",
    "robot_route_reference_separation.png", "physical_budget_derivation_path.png", "protocol_v2_future_evaluation.png",
    "stage_gate_plan.png", "bounded_download_whitelist.png", "license_and_attribution.png",
    "final_entry_decision.png", "claim_boundary.png",
]

REQUIRED_ARTIFACTS = [
    "ETH3D_DELIVERY_AREA_PROTOCOL_V2_ENTRY_QUALIFICATION_V1.md", "IMPLEMENTATION_PLAN.md",
    "input_freeze/protocol_v2_entry_input_freeze.json", "official_authority/primary_authority_registry.json",
    "official_authority/official_web_snapshot_identity.json", "official_authority/official_repo_identity.json",
    "asset_manifest/official_asset_manifest.json", "asset_manifest/official_asset_manifest.csv",
    "asset_manifest/http_head_validation.json", "asset_manifest/asset_role_matrix.json",
    "license/license_compatibility_audit.json", "license/LICENSE_AND_ATTRIBUTION_PLAN.md",
    "dataset_identity/eth3d_delivery_area_benchmark_identity.json",
    "input_reference_partition/eth3d_asset_access_control_contract.json",
    "input_reference_partition/eth3d_mapping_claim_contract.json", "input_reference_partition/allowed_forbidden_claims.md",
    "modality_audit/modality_candidate_audit.json", "modality_audit/splatam_admissibility_audit.json",
    "modality_audit/selected_input_modality_contract.json", "frontend_audit/frontend_authority_audit.json",
    "frontend_audit/selected_frontend_contract.json", "split_contract/future_split_generation_contract.json",
    "split_contract/split_leakage_prohibition.json", "reference_contract/eth3d_reference_authority_contract.json",
    "reference_contract/reference_role_boundary.md", "unknown_contract/runtime_unknown_entry_audit.json",
    "unknown_contract/future_unknown_contract_specification.md",
    "route_robot_contract/eth3d_robot_benchmark_entry_contract.json",
    "route_robot_contract/future_reference_route_contract.json", "physical_budget/physical_budget_entry_contract.json",
    "evaluator_contract/eth3d_protocol_v2_future_evaluator_contract.json",
    "acquisition_plan/eth3d_delivery_area_stage_gate_plan.json",
    "acquisition_plan/future_bounded_download_whitelist.json", "acquisition_plan/future_download_denylist.json",
    "acquisition_plan/future_disk_budget.json", "decision/entry_decision.json", "run_manifest.json",
    "downstream_handoff.json", "runtime_finalization.json", "REPORT_ETH3D_DELIVERY_AREA_PROTOCOL_V2_ENTRY_QUALIFICATION_V1.md",
]

ZERO_COUNTERS = [
    "dataset_archive_download_count", "dataset_payload_bytes", "image_download_count", "depth_download_count",
    "scan_download_count", "occlusion_download_count", "model_download_count", "git_clone_count",
    "environment_create_count", "environment_modify_count", "training_count", "optimizer_count", "model_count",
    "map_count", "controller_count", "planner_count", "route_generation_count", "final_data_split_generation_count",
]


def digest(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--task-root", type=Path, required=True)
    args = parser.parse_args()
    root = args.task_root.resolve()
    manifest = json.loads((root / "run_manifest.json").read_text(encoding="utf-8"))
    assets = json.loads((root / "asset_manifest/official_asset_manifest.json").read_text(encoding="utf-8"))
    head = json.loads((root / "asset_manifest/http_head_validation.json").read_text(encoding="utf-8"))
    whitelist = json.loads((root / "acquisition_plan/future_bounded_download_whitelist.json").read_text(encoding="utf-8"))
    denylist = json.loads((root / "acquisition_plan/future_download_denylist.json").read_text(encoding="utf-8"))
    decision = json.loads((root / "decision/entry_decision.json").read_text(encoding="utf-8"))
    runtime = json.loads((root / "runtime_finalization.json").read_text(encoding="utf-8"))
    freeze = json.loads((root / "input_freeze/protocol_v2_entry_input_freeze.json").read_text(encoding="utf-8"))
    report = (root / "REPORT_ETH3D_DELIVERY_AREA_PROTOCOL_V2_ENTRY_QUALIFICATION_V1.md").read_text(encoding="utf-8")
    counters = manifest["execution_counts"]
    all_files = [p for p in root.rglob("*") if p.is_file()]
    size_bytes = sum(p.stat().st_size for p in all_files)

    checks = {
        "required_scripts_present": all((root / p).is_file() for p in REQUIRED_SCRIPTS),
        "required_artifacts_present": all((root / p).is_file() for p in REQUIRED_ARTIFACTS),
        "twenty_figures_present": len(REQUIRED_FIGURES) == 20 and all((root / "figures" / p).is_file() for p in REQUIRED_FIGURES),
        "figures_are_nontrivial_png": all((root / "figures" / p).read_bytes().startswith(b"\x89PNG\r\n\x1a\n") and (root / "figures" / p).stat().st_size > 20_000 for p in REQUIRED_FIGURES),
        "protocol_freeze_pass": freeze["status"] == "PASS" and all(freeze["gates"].values()),
        "protocol_sha": manifest["protocol_v2_sha256"] == "a0a02fd284c75c600095510899e2878f198d69ff088b66eccd3313275fdbde7e",
        "checklist_sha": manifest["checklist_sha256"] == "7c95f787fd7fb503e4bd2726546debac53acd41c1d5f9a8dd08c29cb27735593",
        "pr76_report_sha": manifest["pr76_report_sha256"] == "052ccdf0b63fbfdfed49a0a5f861a9f0f8bbf7e337079805cfa382cf5153b570",
        "asset_count_14": len(assets) == manifest["official_asset_count"] == 14,
        "head_only_14": head["status"] == "PASS" and head["head_count"] == 14 and head["get_body_count"] == 0 and head["response_body_bytes"] == 0,
        "asset_head_metadata_complete": all(a["http_status"] == 200 and a["content_length"] > 0 and a["mime"] == "application/x-7z-compressed" for a in assets),
        "whitelist_count_9": whitelist["count"] == counters["asset_whitelist_count"] == 9,
        "denylist_count_5": denylist["count"] == counters["asset_denylist_count"] == 5,
        "mapping_input_exactly_rig_undistorted": [a["official_filename"] for a in assets if a["project_role"] == "MAPPING_INPUT_ONLY"] == ["delivery_area_rig_undistorted.7z"],
        "all_zero_boundaries": all(counters[k] == 0 for k in ZERO_COUNTERS),
        "no_payload_extensions": not any(p.suffix.lower() in {".7z", ".zip", ".ply", ".jpg", ".jpeg", ".png", ".raw", ".depth"} and p.parent.name != "figures" for p in all_files),
        "no_python_cache": not any(p.name == "__pycache__" or p.suffix == ".pyc" for p in root.rglob("*")),
        "under_one_gib": size_bytes < 1_073_741_824,
        "report_31_numbered_answers": len(re.findall(r"^## (?:[1-9]|[12][0-9]|3[01])\.", report, flags=re.M)) == 31,
        "report_boundaries": all(token.lower() in report.lower() for token in ["metadata-only", "Training remains unauthorized", "NOT_ADMISSIBLE_WITHOUT_REFERENCE_GEOMETRY_LEAKAGE", "UNKNOWN is never free", "GT-pose RGB-only map-only"]),
        "decision_pass": decision["status"] == "PASS" and all(decision["gates"].values()),
        "final_status": manifest["FINAL_STATUS"] == "PASS_ETH3D_DELIVERY_AREA_PROTOCOL_V2_ENTRY_QUALIFICATION",
        "final_decision": manifest["FINAL_DECISION"] == "AUTHORIZE_BOUNDED_ETH3D_DELIVERY_AREA_ASSET_ACQUISITION_AND_CONTRACT_AUDIT",
        "only_next_task": manifest["Only_next_task"] == "ACQUIRE_ETH3D_DELIVERY_AREA_FROZEN_ASSETS_AND_VALIDATE_SPLIT_REFERENCE_UNKNOWN_ROUTE_CONTRACT_V1",
        "training_unauthorized": manifest["training_authorized"] is False and decision["training_authorized"] is False,
        "runtime_boundary_preserved": runtime["status"] == "PASS_RUNTIME_BOUNDARY_PRESERVED",
        "gpu_task_clean": runtime["gpu_final"]["task_compute_process_count"] == 0,
        "watchdog_and_ssh_preserved": runtime["watchdog_status"] == "Running" and runtime["managed_reverse_ssh_preserved"] is True,
        "server_report_identity": runtime["server_report_sha256"] == runtime["local_report_sha256"],
        "unresolved_critical_empty": manifest["unresolved_critical_evidence"] == [] and decision["unresolved_critical_evidence"] == [],
    }
    identities = []
    for path in sorted(all_files):
        rel = path.relative_to(root).as_posix()
        if rel in {"validation_result.json", "artifact_identity.json"}:
            continue
        identities.append({"path": rel, "bytes": path.stat().st_size, "sha256": digest(path)})
    result = {
        "status": "PASS" if all(checks.values()) else "FAIL",
        "validator": "validate_entry_qualification.py",
        "checks": checks,
        "task_file_count": len(all_files),
        "task_size_bytes": size_bytes,
        "required_script_count": len(REQUIRED_SCRIPTS),
        "required_figure_count": len(REQUIRED_FIGURES),
        "unresolved_critical_evidence": [] if all(checks.values()) else [k for k, v in checks.items() if not v],
    }
    (root / "artifact_identity.json").write_text(json.dumps(identities, indent=2) + "\n", encoding="utf-8")
    (root / "validation_result.json").write_text(json.dumps(result, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(result, indent=2))
    return 0 if result["status"] == "PASS" else 2


if __name__ == "__main__":
    raise SystemExit(main())
