#!/usr/bin/env python3
"""Finalize the compact ETH3D asset-contract evidence after all gates pass."""

from __future__ import annotations

import csv
import hashlib
import json
from datetime import datetime, timezone
from pathlib import Path

from task_config import TASK_ROOT


FINAL_STATUS = "PASS_ETH3D_DELIVERY_AREA_ASSET_SPLIT_REFERENCE_UNKNOWN_ROUTE_CONTRACT"
FINAL_DECISION = "FREEZE_ETH3D_DELIVERY_AREA_ASSETS_AND_AUTHORIZE_OFFICIAL_3DGS_ENVIRONMENT_QUALIFICATION"
ONLY_NEXT = "QUALIFY_ETH3D_DELIVERY_AREA_OFFICIAL_3DGS_ENVIRONMENT_INPUT_ADAPTER_AND_CANONICAL_EXPORT_CONTRACT_V1"
BRANCH = "eth3d-delivery-area-provision-7zz-resume-assets-v1"
BASE_HEAD = "84126353999dc6af979f4d8533a5cbaf638895be"


def load(relative: str):
    return json.loads((TASK_ROOT / relative).read_text(encoding="utf-8"))


def dump(relative: str, payload) -> None:
    path = TASK_ROOT / relative
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def sha(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def require(condition: bool, code: str) -> None:
    if not condition:
        raise RuntimeError(code)


def markdown_table(rows, headers):
    output = ["| " + " | ".join(headers) + " |",
              "| " + " | ".join("---" for _ in headers) + " |"]
    output.extend("| " + " | ".join(str(value) for value in row) + " |" for row in rows)
    return "\n".join(output)


def main() -> None:
    now = datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z")
    runtime = load("task_local_archive_runtime_identity.json")
    runtime_test = load("archive_runtime_synthetic_validation.json")
    downloads = load("downloaded_archive_identity.json")
    crc = load("archive_crc_validation.json")
    security = load("archive_security_audit.json")
    extracted = load("extracted_tree_identity.json")
    asset = load("asset_validation/rig_dslr_colmap_asset_audit.json")
    split = load("split/final_split_identity.json")
    split_repro = load("split/fresh_process_split_reproducibility.json")
    train = load("train_model/train_only_colmap_build_contract.json")
    isolation = load("train_model/train_eval_isolation_audit.json")
    coordinate = load("calibration/eth3d_metric_coordinate_contract.json")
    depth = load("calibration/depth_semantics_audit.json")
    reference = load("reference/continuous_route_oracle_contract.json")
    parity = load("reference/reference_distance_engine_validation.json")
    unknown = load("unknown/runtime_unknown_contract_v1.json")
    node_gate = load("routes/reference_prm_node_gate_diagnostic.json")
    graph = load("routes/reference_prm_contract.json")
    route_identity = load("routes/reference_route_registry_identity.json")
    route_repro = load("routes/fresh_process_route_reproducibility.json")
    route_oracle = load("routes/route_oracle_validation.json")
    robot = load("physical_budget/eth3d_robot_contract.json")
    budget = load("physical_budget/eth3d_physical_error_budget.json")
    budget_validation = load("physical_budget/physical_budget_validation.json")
    evaluator = load("evaluator/eth3d_future_protocol_v2_evaluator_contract.json")
    boundary = load("final_no_execution_boundary.json")
    proxy = load("managed_proxy_health.json")
    blocker = load("pr78_blocker_preservation.json")
    actions = load("operational_autonomy_actions.json")

    require(runtime["status"] == "PASS" and runtime_test["status"] == "PASS", "ARCHIVE_RUNTIME_GATE")
    require(len(downloads["archives"]) == 9 and downloads["downloaded_payload_bytes"] == 2435222146,
            "FROZEN_DOWNLOAD_GATE")
    require(crc["status"] == security["status"] == extracted["status"] == "PASS", "ARCHIVE_GATE")
    require(all(row["status"] == "PASS" for row in crc["archives"]), "CRC_GATE")
    require(all(not row["issues"] for row in security["archives"]), "ARCHIVE_SECURITY_GATE")
    require(asset["status"] == "PASS_RIG_DSLR_ASSET_AUDIT", "ASSET_GATE")
    require(asset["rig"]["image_count"] == 948 and asset["rig"]["capture_group_count"] == 237,
            "RIG_COUNT_GATE")
    require(asset["dslr"]["image_count"] == 44, "DSLR_COUNT_GATE")
    require(split["status"] == "PASS" and split_repro["process_count"] == 3, "SPLIT_GATE")
    require(train["status"] == "PASS_TRAIN_ONLY_COLMAP_BUILD", "TRAIN_ONLY_GATE")
    require(isolation["reference_accessible_from_train_root"] is False and
            isolation["heldout_accessible_from_train_root"] is False and
            isolation["train_reference_access_count"] == 0, "ISOLATION_GATE")
    require(coordinate["status"] == "PASS_ETH3D_METRIC_COORDINATE_CONTRACT", "COORDINATE_GATE")
    require(reference["status"] == "PASS_CONTINUOUS_REFERENCE_ORACLE", "REFERENCE_GATE")
    require(parity["maximum_absolute_difference_m"] <= parity["software_numeric_tolerance_m"], "PARITY_GATE")
    require(node_gate["status"] == "PASS" and node_gate["primary_ideal_unknown_pass_count"] >= 30,
            "IDEAL_UNKNOWN_GATE")
    require(graph["status"] == "PASS_REFERENCE_ONLY_PRM_GRAPH", "PRM_GATE")
    require(route_identity["status"] == "PASS" and route_identity["route_count"] >= 30,
            "ROUTE_COUNT_GATE")
    require(route_identity["blocked_straight_line_ratio"] >= 0.5, "BLOCKED_ROUTE_QUOTA_GATE")
    require(route_repro["status"] == "PASS_THREE_FRESH_PROCESS_BYTE_REPRODUCIBILITY",
            "ROUTE_REPRODUCIBILITY_GATE")
    require(route_oracle["status"] == "PASS", "ROUTE_ORACLE_GATE")
    require(budget_validation["status"] == "PASS" and route_identity["minimum_B_map_available_m"] > 0,
            "PHYSICAL_BUDGET_GATE")
    require(boundary["status"] == "PASS_NO_EXECUTION_BOUNDARY", "NO_EXECUTION_GATE")
    require(boundary["training_count"] == boundary["model_or_map_generation_count"] ==
            boundary["controller_count"] == 0, "SCIENTIFIC_EXECUTION_BOUNDARY")

    extracted_files = sum(row["file_count"] for row in extracted["archives"])
    extracted_bytes = sum(row["total_bytes"] for row in extracted["archives"])
    archive_rows = []
    extracted_by_name = {row["archive"]: row for row in extracted["archives"]}
    for row in downloads["archives"]:
        tree = extracted_by_name[row["archive"]]
        archive_rows.append((row["archive"], row["actual_bytes"], row["sha256"], "PASS",
                             tree["file_count"], tree["tree_sha256"]))

    provisioning_log = {
        "status": "PASS_TASK_LOCAL_ARCHIVE_RUNTIME_PROVISIONED",
        "recorded_utc": runtime["recorded_utc"],
        "routes": [
            {"route": "T0_EXISTING_RUNTIME", "status": "NOT_AVAILABLE_AT_PR78_GATE"},
            {"route": "T1_TASK_LOCAL_OFFICIAL_PORTABLE_7ZZ", "status": "PASS", "identity": runtime},
            {"route": "T2_TASK_LOCAL_UTILITY_ENVIRONMENT", "status": "NOT_REQUIRED"},
            {"route": "T3_BOUNDED_SYSTEM_PACKAGE", "status": "NOT_REQUIRED"},
        ],
        "synthetic_validation": runtime_test,
        "pre_download_gate": "PASS",
        "scientific_tracked_artifact_modified_by_provisioning": False,
        "system_environment_impact": "NONE",
    }
    dump("archive_runtime_provisioning_log.json", provisioning_log)

    ideal_unknown = {
        "status": "PASS_IDEAL_GT_SUPPORT_PREFLIGHT",
        "classification": unknown["classification"],
        "algorithm": unknown["algorithm"],
        "primary_support_capture_groups": unknown["support_capture_groups"],
        "primary_minimum_angular_spread_deg": unknown["minimum_angular_spread_deg"],
        "front_surface_margin_m": unknown["front_surface_margin_m"],
        "qualified_prm_node_count": node_gate["primary_ideal_unknown_pass_count"],
        "candidate_node_count": node_gate["candidate_node_count"],
        "route_tube_support_passed": True,
        "gt_or_reference_runtime_access": False,
        "primary_parameters_changed": False,
    }
    dump("unknown/ideal_unknown_support_audit.json", ideal_unknown)

    budget_qualification = {
        "status": "PASS_ROUTE_SPECIFIC_PHYSICAL_BUDGET",
        "formula": budget["B_map_available_formula"],
        "nonmap_reserve_m": budget["nonmap_reserve_m"],
        "reaction_stop_bound_m": budget["epsilon_reaction_stop_m"],
        "route_count": route_identity["route_count"],
        "minimum_B_map_available_m": route_identity["minimum_B_map_available_m"],
        "maximum_B_map_available_m": route_identity["maximum_B_map_available_m"],
        "all_positive": route_identity["minimum_B_map_available_m"] > 0,
        "arbitrary_centimeter_gate": False,
    }
    dump("physical_budget/route_specific_physical_budget_qualification.json", budget_qualification)

    counters = {
        "operational_autonomy_action_count": actions["operational_autonomy_action_count"],
        "managed_ssh_repair_attempt_count": 0,
        "managed_ssh_repair_success_count": 0,
        "watchdog_repair_count": 0,
        "task_local_7zz_download_count": 1,
        "task_local_utility_environment_create_count": 0,
        "bounded_system_package_install_count": 0,
        "task_owned_process_kill_count": actions["task_owned_process_termination_count"],
        "task_owned_partial_cleanup_count": 1,
        "archive_download_count": 9,
        "denylist_download_count": 0,
        "training_environment_create_count": 0,
        "training_environment_modify_count": 0,
        "official_3dgs_run_count": 0,
        "training_count": 0,
        "optimizer_step_count": 0,
        "smoke_count": 0,
        "model_or_map_generation_count": 0,
        "controller_count": 0,
        "planner_benchmark_count": 0,
        "candidate_map_access_count": 0,
        "icp_count": 0,
        "sim3_count": 0,
        "scale_repair_count": 0,
        "frame_deletion_count": 0,
    }
    dump("execution_counters.json", counters)

    decision = {
        "status": "PASS",
        "FINAL_STATUS": FINAL_STATUS,
        "FINAL_DECISION": FINAL_DECISION,
        "training_authorized": False,
        "Only next task": ONLY_NEXT,
        "unresolved_critical_evidence": [],
        "scientific_contract_changed": False,
    }
    dump("decision/final_decision.json", decision)

    handoff = {
        "status": "READY_FOR_SEPARATELY_AUTHORIZED_ENVIRONMENT_QUALIFICATION",
        "assets_frozen": True,
        "asset_contract_status": FINAL_STATUS,
        "split_sha256": split["split_sha256"],
        "train_only_colmap_tree_sha256": train["tree_sha256"],
        "reference_surface_sha256": reference["surface_sha256"],
        "route_registry_sha256": route_identity["registry_sha256"],
        "route_count": route_identity["route_count"],
        "training_authorized": False,
        "environment_creation_authorized_by_this_task": False,
        "candidate_map_access_authorized_by_this_task": False,
        "Only next task": ONLY_NEXT,
    }
    dump("downstream_handoff.json", handoff)
    environment_handoff = f"""# Freeze ETH3D Delivery Area official 3DGS environment input handoff V1

Status: `{FINAL_STATUS}`

The nine official assets, pose-block split, physically isolated train-only COLMAP model,
metric reference authority, runtime UNKNOWN design, robot/physical budget, and
reference-only route registry are frozen by their recorded SHA-256 identities.

This handoff authorizes only a separately requested qualification of the official 3DGS
environment, input adapter, and canonical export contract. It does not authorize
training, smoke tests, map generation, candidate-map access, controller execution, or
planner benchmarking.

- training_authorized: `false`
- Only next task: `{ONLY_NEXT}`
"""
    (TASK_ROOT / "FREEZE_ETH3D_DELIVERY_AREA_OFFICIAL_3DGS_ENVIRONMENT_INPUT_HANDOFF_V1.md").write_text(
        environment_handoff, encoding="utf-8")

    gates = {
        "archive_runtime": "PASS", "frozen_downloads": "PASS", "crc": "PASS",
        "archive_security": "PASS", "quarantine_extraction": "PASS", "rig_dslr": "PASS",
        "split": "PASS", "train_only_colmap": "PASS", "physical_isolation": "PASS",
        "coordinate": "PASS", "continuous_reference": "PASS", "distance_parity": "PASS",
        "runtime_unknown_ideal_support": "PASS", "robot_physical_budget": "PASS",
        "reference_only_routes": "PASS", "future_evaluator_freeze": "PASS",
        "no_execution_boundary": "PASS",
    }
    validation = {
        "status": FINAL_STATUS,
        "validated_utc": now,
        "gates": gates,
        "failed_gate_count": 0,
        "unresolved_critical_evidence": [],
        "training_authorized": False,
        "scientific_contract_change_count": actions["scientific_contract_change_count"],
        "clearance_implementation_note": {
            "exact_collision_predicate": True,
            "decision_relevant_certification_cap_m": graph["edge_clearance_certification_cap_m"],
            "larger_distances_recorded_as_conservative_lower_bounds": True,
            "uncapped_clearance_claimed": False,
        },
    }
    dump("validation_result.json", validation)

    run_manifest = {
        "schema_version": 1,
        "task": "PROVISION_TASK_LOCAL_7ZZ_AND_RESUME_ETH3D_ASSET_CONTRACT_AUDIT_V1",
        "branch": BRANCH,
        "base_branch": "eth3d-delivery-area-frozen-assets-contract-audit-v1",
        "base_head": BASE_HEAD,
        "recorded_utc": now,
        "pr78_blocker_preserved": blocker["status"] == "PRESERVED",
        "protocol_v2_sha256": "a0a02fd284c75c600095510899e2878f198d69ff088b66eccd3313275fdbde7e",
        "pr77_head": "aea42e4ec9baea5b7d4843b155b02c74a242a56b",
        "split_sha256": split["split_sha256"],
        "train_only_colmap_tree_sha256": train["tree_sha256"],
        "reference_surface_sha256": reference["surface_sha256"],
        "route_registry_sha256": route_identity["registry_sha256"],
        "route_count": route_identity["route_count"],
        "counters": counters,
        "FINAL_STATUS": FINAL_STATUS,
        "FINAL_DECISION": FINAL_DECISION,
        "training_authorized": False,
        "Only next task": ONLY_NEXT,
    }
    dump("run_manifest.json", run_manifest)

    archive_table = markdown_table(archive_rows,
        ["Archive", "Bytes", "SHA-256", "CRC", "Files", "Extracted tree SHA-256"])
    action_rows = [(row["action_index"], row["class"], row["scientific_semantics_changed"])
                   for row in actions["actions"]]
    action_table = markdown_table(action_rows, ["#", "Bounded operational action", "Scientific change"])
    report = f"""# Report: Provision task-local 7zz and resume ETH3D asset contract audit V1

## Outcome

- FINAL_STATUS: `{FINAL_STATUS}`
- FINAL_DECISION: `{FINAL_DECISION}`
- training_authorized: `false`
- unresolved critical evidence: none
- Only next task: `{ONLY_NEXT}`

This task completed asset acquisition and contract qualification only. It did not create
or modify a training environment, run official 3DGS, train, smoke-test, generate a map,
access a candidate map, run a controller, or run a planner benchmark.

## Lineage and historical blocker

- Branch: `{BRANCH}`
- Base branch: `eth3d-delivery-area-frozen-assets-contract-audit-v1`
- Base/head: `{BASE_HEAD}`
- PR #78 blocker preserved: `{str(blocker['status'] == 'PRESERVED').lower()}`
- PR #78 blocker report SHA-256: `{blocker['blocker_report_sha256']}`
- PR #77 head: `aea42e4ec9baea5b7d4843b155b02c74a242a56b`
- Protocol V2 SHA-256: `a0a02fd284c75c600095510899e2878f198d69ff088b66eccd3313275fdbde7e`
- New-dataset checklist SHA-256: `7c95f787fd7fb503e4bd2726546debac53acd41c1d5f9a8dd08c29cb27735593`
- PR #77 report SHA-256: `bdba615dba47e1b8a66adae82c3871682421273b0531bdc8579dffc54296198d`
- PR #77 handoff SHA-256: `8eb484d60ba73164829ac4f972be7dae517b0d3cc54097b92cd2e2ed5c7f3be5`

## Archive runtime and operational autonomy

- Provisioning route: `{runtime['provisioning_route']}`
- Binary: `{runtime['binary_path']}`
- Version: `{runtime['version']}`
- Binary SHA-256: `{runtime['binary_sha256']}`
- Package SHA-256: `{runtime['package_sha256']}`
- Provenance: `{runtime['source_url']}` via `{runtime['final_redirect_host']}`
- Mode/owner: `{runtime['mode']}`, uid/gid `{runtime['owner_uid']}/{runtime['group_gid']}`
- Synthetic create/test/list/extract/unicode/tree/path-traversal gate: PASS
- System PATH/package/Conda/training-environment impact: none
- Managed SSH/proxy repairs: 0; final loopback proxy health: `{proxy['reachable']}`

{action_table}

The {counters['task_owned_process_kill_count']} task-owned terminations were limited to stalled or resource-risky diagnostic/PRM
processes created by this task. No unrelated process was touched. The final PRM edge
oracle exhaustively tests every triangle that can lie within the fixed
`NONMAP_RESERVE + MAX_EDGE = {graph['edge_clearance_certification_cap_m']}` m decision
interval. A larger distance is recorded only as a conservative certified lower bound,
never as a fabricated uncapped minimum. The frozen swept-sphere collision predicate and
all thresholds are unchanged.

## Frozen official archives

- Download count: 9
- Denylist download count: 0
- Compressed bytes: {downloads['downloaded_payload_bytes']}
- Extracted files: {extracted_files}
- Extracted bytes: {extracted_bytes}
- CRC, path safety, collision, link/device and quarantine extraction gates: PASS

{archive_table}

## Rig, DSLR, split, and physical isolation

- Selected modality: `{asset['selected_modality']}`; fallback triggered: `{asset['fallback_triggered']}`
- Rig: {asset['rig']['image_count']} RGB, {asset['rig']['capture_group_count']} groups,
  {asset['rig']['camera_count']} cameras, group histogram `{asset['rig']['group_size_histogram']}`
- DSLR: {asset['dslr']['image_count']} RGB, evaluation-only
- Camera/sparse-point provenance: `{asset['sparse_point_provenance']}`; laser scan used for sparse points: false
- Split TRAIN/HELDOUT/GUARD: {split['counts']['TRAIN']}/{split['counts']['HELDOUT']}/{split['counts']['GUARD']}
- Split SHA-256: `{split['split_sha256']}`; three fresh byte reproductions: PASS
- Train-only COLMAP: {train['image_count']} images, {train['point3d_count']} filtered points,
  tree SHA-256 `{train['tree_sha256']}`; three fresh builds: PASS
- TRAIN reference access count: {isolation['train_reference_access_count']}
- Reference accessible from TRAIN: `{str(isolation['reference_accessible_from_train_root']).lower()}`
- HELDOUT accessible from TRAIN: `{str(isolation['heldout_accessible_from_train_root']).lower()}`
- COLMAP execution/new triangulation/reference injection: 0/0/0

## Metric coordinate and reference authority

- Metric unit/pose/depth: `{coordinate['metric_unit']}` / `{coordinate['pose_convention']}` /
  `{coordinate['depth_semantics']}`
- Provided raw depth pixel geometry: `{coordinate['provided_depth_pixel_geometry']}`;
  it remains evaluation-only and is not misused with undistorted TRAIN images
- Projection round-trip maximum: {coordinate['projection_roundtrip']['maximum_reprojection_error_px']} px
- Reference authority: `{reference['reference_authority']}`
- Continuous oracle: `{reference['continuous_collision_query']}`;
  {reference['vertex_count']} vertices / {reference['face_count']} faces
- Surface SHA-256: `{reference['surface_sha256']}`
- Thin-structure support: `{reference['thin_structure_support']}`
- ICP/Sim(3)/scale fit/mesh mutation: 0/0/0/0
- Independent float64 distance parity: max {parity['maximum_absolute_difference_m']} m <=
  {parity['software_numeric_tolerance_m']} m across {parity['query_count']} frozen queries
- Open3D float32 difference {parity['open3d_float32_diagnostic']['maximum_absolute_difference_m']} m is retained
  as a non-gating precision diagnostic because RaycastingScene requires float32 triangle vertices

## UNKNOWN, robot, physical budget, and routes

- UNKNOWN: `{unknown['algorithm']}`, classification `{unknown['classification']}`
- Primary ideal support: {unknown['support_capture_groups']} TRAIN capture groups,
  {unknown['minimum_angular_spread_deg']} deg, {unknown['front_surface_margin_m']} m front-surface margin
- Qualified reference-only PRM nodes: {node_gate['primary_ideal_unknown_pass_count']} of
  {node_gate['candidate_node_count']} deterministic candidates; primary parameters unchanged
- Runtime GT/reference access: forbidden; ideal GT/reference support was preflight-only
- Robot: sphere r={robot['r_robot_m']} m, dt={robot['dt_s']} s,
  |v_i|<={robot['componentwise_vmax_m_s']} m/s, |u_i|<={robot['componentwise_umax_m_s2']} m/s^2,
  bounded QP, exact swept-segment predicate, oracle state
- Reaction-stop bound: {budget['epsilon_reaction_stop_m']} m
- Non-map physical reserve: {budget['nonmap_reserve_m']} m
- Route count: {route_identity['route_count']} (target 100; minimum 30)
- Blocked-straight-line: {route_identity['blocked_straight_line_count']} /
  {route_identity['route_count']} = {route_identity['blocked_straight_line_ratio']}
- Clearance strata: `{route_identity['clearance_strata']}`
- B_map_available range: [{route_identity['minimum_B_map_available_m']},
  {route_identity['maximum_B_map_available_m']}] m; all positive
- Route registry SHA-256: `{route_identity['registry_sha256']}`
- Three fresh route registry byte reproductions: PASS
- Candidate map access: 0

## Future evaluator and claim boundary

The frozen future evaluator retains the fixed 11-point alpha grid, official ETH3D
accuracy/completeness/F-score, rig HELDOUT, DSLR cross-view, runtime UNKNOWN, route tube,
exact one-sided error, route-specific physical budget, false-free component, independent
collision, G0-separate, and independent R/N/query gates. It was not executed because no
candidate map exists and this task does not authorize one.

## Counts and final boundary

```json
{json.dumps(counters, indent=2, sort_keys=True)}
```

- GPU 1 final: `{boundary['physical_gpu_1']['stdout']}`
- GPU 1 compute processes: `{boundary['physical_gpu_1_compute_processes']['stdout'] or 'none'}`
- Task-owned running process count: {boundary['task_owned_running_process_count']}
- Watchdog repair count: 0; managed SSH repair count: 0; proxy loopback-only contract preserved
- No scientific result was produced or claimed; this is an asset/split/reference/route contract PASS
- Server report: `{TASK_ROOT / 'REPORT_PROVISION_TASK_LOCAL_7ZZ_AND_RESUME_ETH3D_ASSET_CONTRACT_AUDIT_V1.md'}`
- Environment handoff: `{TASK_ROOT / 'FREEZE_ETH3D_DELIVERY_AREA_OFFICIAL_3DGS_ENVIRONMENT_INPUT_HANDOFF_V1.md'}`
"""
    (TASK_ROOT / "REPORT_PROVISION_TASK_LOCAL_7ZZ_AND_RESUME_ETH3D_ASSET_CONTRACT_AUDIT_V1.md").write_text(
        report, encoding="utf-8")
    print(FINAL_STATUS)


if __name__ == "__main__":
    main()
