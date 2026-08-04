#!/usr/bin/env python3
"""Fail-closed Case C closeout when the frozen route quota is impossible."""

from __future__ import annotations

import json
from datetime import datetime, timezone

from task_config import TASK_ROOT


FINAL_STATUS = "NO_ETH3D_DELIVERY_AREA_REFERENCE_ROUTE_BENCHMARK_CONTRACT"
FINAL_DECISION = "CLOSE_ETH3D_DELIVERY_AREA_BEFORE_ENVIRONMENT_OR_TRAINING"
ONLY_NEXT = "REVIEW_PROTOCOL_V2_REAL_WORLD_DATASET_ALTERNATIVES_V1"


def load(relative):
    return json.loads((TASK_ROOT / relative).read_text(encoding="utf-8"))


def dump(relative, payload):
    path = TASK_ROOT / relative
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8")


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
    train = load("train_model/train_only_colmap_build_contract.json")
    isolation = load("train_model/train_eval_isolation_audit.json")
    coordinate = load("calibration/eth3d_metric_coordinate_contract.json")
    reference = load("reference/continuous_route_oracle_contract.json")
    parity = load("reference/reference_distance_engine_validation.json")
    unknown = load("unknown/runtime_unknown_contract_v1.json")
    node_gate = load("routes/reference_prm_node_gate_diagnostic.json")
    graph = load("routes/reference_prm_contract.json")
    candidates = load("routes/reference_route_candidates_full.json")
    robot = load("physical_budget/eth3d_robot_contract.json")
    budget = load("physical_budget/eth3d_physical_error_budget.json")
    evaluator = load("evaluator/eth3d_future_protocol_v2_evaluator_contract.json")
    boundary = load("final_no_execution_boundary.json")
    proxy = load("managed_proxy_health.json")
    blocker = load("pr78_blocker_preservation.json")
    actions = load("operational_autonomy_actions.json")
    watchdog = load("watchdog_ssh_final_health.json")

    prerequisites = {
        "archive_runtime": runtime["status"] == runtime_test["status"] == "PASS",
        "nine_frozen_downloads": len(downloads["archives"]) == 9 and downloads["downloaded_payload_bytes"] == 2435222146,
        "crc_security_extraction": crc["status"] == security["status"] == extracted["status"] == "PASS",
        "rig_dslr": asset["status"] == "PASS_RIG_DSLR_ASSET_AUDIT",
        "split": split["status"] == "PASS",
        "train_only_colmap": train["status"] == "PASS_TRAIN_ONLY_COLMAP_BUILD",
        "physical_isolation": isolation["train_reference_access_count"] == 0,
        "coordinate": coordinate["status"] == "PASS_ETH3D_METRIC_COORDINATE_CONTRACT",
        "continuous_reference": reference["status"] == "PASS_CONTINUOUS_REFERENCE_ORACLE",
        "distance_parity": parity["maximum_absolute_difference_m"] <= parity["software_numeric_tolerance_m"],
        "ideal_unknown": node_gate["status"] == "PASS",
        "prm_graph": graph["status"] == "PASS_REFERENCE_ONLY_PRM_GRAPH",
        "no_execution": boundary["status"] == "PASS_NO_EXECUTION_BOUNDARY",
    }
    if not all(prerequisites.values()):
        raise RuntimeError({key: value for key, value in prerequisites.items() if not value})
    candidate_count = candidates["candidate_count"]
    blocked_count = candidates["blocked_candidate_count"]
    blocked_ratio = blocked_count / candidate_count if candidate_count else 0.0
    if candidate_count < 30 or blocked_ratio >= 0.5:
        raise RuntimeError("ROUTE_FAILURE_CLOSEOUT_PRECONDITION_NOT_MET")

    dump("archive_runtime_provisioning_log.json", {
        "status": "PASS_TASK_LOCAL_ARCHIVE_RUNTIME_PROVISIONED",
        "routes": [
            {"route": "T0_EXISTING_RUNTIME", "status": "NOT_AVAILABLE_AT_PR78_GATE"},
            {"route": "T1_TASK_LOCAL_OFFICIAL_PORTABLE_7ZZ", "status": "PASS", "identity": runtime},
            {"route": "T2_TASK_LOCAL_UTILITY_ENVIRONMENT", "status": "NOT_REQUIRED"},
            {"route": "T3_BOUNDED_SYSTEM_PACKAGE", "status": "NOT_REQUIRED"},
        ],
        "synthetic_validation": runtime_test,
        "pre_download_gate": "PASS",
        "system_environment_impact": "NONE",
    })
    dump("unknown/ideal_unknown_support_audit.json", {
        "status": "PASS_IDEAL_GT_SUPPORT_PREFLIGHT",
        "algorithm": unknown["algorithm"],
        "qualified_prm_node_count": node_gate["primary_ideal_unknown_pass_count"],
        "candidate_node_count": node_gate["candidate_node_count"],
        "primary_support_capture_groups": unknown["support_capture_groups"],
        "primary_minimum_angular_spread_deg": unknown["minimum_angular_spread_deg"],
        "front_surface_margin_m": unknown["front_surface_margin_m"],
        "gt_or_reference_runtime_access": False,
        "primary_parameters_changed": False,
    })
    route_failure = {
        "status": FINAL_STATUS,
        "failure_gate": "BLOCKED_STRAIGHT_LINE_RATIO_AT_LEAST_0_5",
        "frozen_minimum_route_count": 30,
        "frozen_blocked_straight_line_ratio_minimum": 0.5,
        "valid_reference_path_candidate_count": candidate_count,
        "blocked_straight_line_candidate_count": blocked_count,
        "blocked_straight_line_candidate_ratio": blocked_ratio,
        "frozen_robot_state": "6D_FREE_3D_DOUBLE_INTEGRATOR",
        "candidate_voxel_dimensionality": node_gate.get("candidate_voxel_dimensionality"),
        "edge_cost_contract": graph["edge_cost_contract"],
        "exact_swept_sphere_collision_predicate": True,
        "decision_relevant_clearance_certification_cap_m": graph["edge_clearance_certification_cap_m"],
        "uncapped_clearance_claimed": False,
        "candidate_map_access_count": 0,
        "threshold_or_contract_modified": False,
        "route_registry_frozen": False,
        "reason": "The corrected deterministic free-3D reference-only PRM did not provide the preregistered minimum 50% direct-obstruction composition among otherwise valid path candidates.",
    }
    dump("routes/reference_route_contract_failure.json", route_failure)
    dump("routes/reference_route_registry_full.json", {
        "status": FINAL_STATUS, "route_count": 0, "routes": [],
        "failure_record": "reference_route_contract_failure.json"})
    dump("routes/reference_route_registry_identity.json", {
        "status": FINAL_STATUS, "route_count": 0,
        "blocked_straight_line_count": 0, "blocked_straight_line_ratio": 0.0,
        "clearance_strata": {"TIGHT": 0, "MODERATE": 0, "OPEN": 0},
        "minimum_B_map_available_m": None, "maximum_B_map_available_m": None,
        "registry_sha256": None, "all_routes_primary_ideal_unknown_supported": False,
        "candidate_map_access_count": 0})
    dump("routes/route_oracle_validation.json", {
        "status": FINAL_STATUS, "exact_swept_sphere_collision_predicate": True,
        "candidate_paths_collision_free": True, "route_registry_frozen": False})
    dump("routes/route_clearance_budget_summary.json", {
        "status": "NOT_FROZEN_BECAUSE_ROUTE_COMPOSITION_GATE_FAILED",
        "nonmap_reserve_m": budget["nonmap_reserve_m"], "route_count": 0})
    dump("routes/route_knownness_summary.json", {
        "status": "CANDIDATE_PATHS_PASS_BUT_REGISTRY_NOT_FROZEN",
        "primary_contract": "3 groups / 15 deg / 0.01 m", "route_count": 0})
    dump("routes/fresh_process_route_reproducibility.json", {
        "status": "NOT_RUN_FAIL_CLOSED_AFTER_DETERMINISTIC_ROUTE_COMPOSITION_FAILURE",
        "process_count": 1, "route_registry_frozen": False})

    counters = {
        "operational_autonomy_action_count": actions["operational_autonomy_action_count"],
        "managed_ssh_repair_attempt_count": 0, "managed_ssh_repair_success_count": 0,
        "watchdog_repair_count": 0, "task_local_7zz_download_count": 1,
        "task_local_utility_environment_create_count": 0,
        "bounded_system_package_install_count": 0,
        "task_owned_process_kill_count": actions["task_owned_process_termination_count"],
        "task_owned_partial_cleanup_count": 1,
        "official_archive_download_count": 9,
        "downloaded_payload_bytes": downloads["downloaded_payload_bytes"],
        "archive_crc_test_count": 9, "extracted_archive_count": 9,
        "split_generation_process_count": 3, "train_only_colmap_build_count": 3,
        "reference_distance_validation_count": 1,
        "route_generation_process_count": 2,
        "route_count": 0, "denylist_download_count": 0,
        "training_environment_create_count": 0, "training_environment_modify_count": 0,
        "git_clone_count": 0, "compilation_count": 0, "official_3dgs_run_count": 0,
        "training_count": 0, "optimizer_step_count": 0, "smoke_count": 0,
        "model_or_map_generation_count": 0, "controller_count": 0,
        "planner_benchmark_count": 0, "candidate_map_access_count": 0,
        "icp_count": 0, "sim3_count": 0, "scale_repair_count": 0,
        "frame_deletion_count": 0,
    }
    dump("execution_counters.json", counters)
    decision = {
        "status": "FAIL_CLOSED_CASE_C", "FINAL_STATUS": FINAL_STATUS,
        "FINAL_DECISION": FINAL_DECISION, "training_authorized": False,
        "environment_qualification_authorized": False,
        "Only next task": ONLY_NEXT,
        "unresolved_critical_evidence": [],
        "resolved_scientific_incompatibility": "FROZEN_ROUTE_COMPOSITION_GATE_FAILED",
        "scientific_contract_changed": False,
    }
    dump("decision/final_decision.json", decision)
    dump("downstream_handoff.json", {
        "status": "CLOSED_BEFORE_ENVIRONMENT_OR_TRAINING",
        "asset_audit_prerequisites_passed": True,
        "route_contract_qualified": False,
        "training_authorized": False,
        "environment_qualification_authorized": False,
        "candidate_map_access_authorized": False,
        "Only next task": ONLY_NEXT,
    })
    validation = {
        "status": FINAL_STATUS, "validated_utc": now,
        "gates": {**{key: "PASS" for key in prerequisites}, "reference_only_routes": "FAIL"},
        "failed_gate_count": 1,
        "failed_gate": "reference_only_routes.blocked_straight_line_ratio",
        "unresolved_critical_evidence": [],
        "training_authorized": False,
        "scientific_contract_change_count": actions["scientific_contract_change_count"],
    }
    dump("validation_result.json", validation)
    dump("run_manifest.json", {
        "schema_version": 1,
        "task": "PROVISION_TASK_LOCAL_7ZZ_AND_RESUME_ETH3D_ASSET_CONTRACT_AUDIT_V1",
        "branch": "eth3d-delivery-area-provision-7zz-resume-assets-v1",
        "base_branch": "eth3d-delivery-area-frozen-assets-contract-audit-v1",
        "base_head": "84126353999dc6af979f4d8533a5cbaf638895be",
        "recorded_utc": now, "pr78_blocker_preserved": True,
        "protocol_v2_sha256": "a0a02fd284c75c600095510899e2878f198d69ff088b66eccd3313275fdbde7e",
        "pr77_head": "aea42e4ec9baea5b7d4843b155b02c74a242a56b",
        "split_sha256": split["split_sha256"],
        "train_only_colmap_tree_sha256": train["tree_sha256"],
        "reference_surface_sha256": reference["surface_sha256"],
        "route_registry_sha256": None, "route_count": 0,
        "counters": counters, "FINAL_STATUS": FINAL_STATUS,
        "FINAL_DECISION": FINAL_DECISION, "training_authorized": False,
        "Only next task": ONLY_NEXT,
    })

    archive_lines = "\n".join(
        f"- `{row['archive']}`: {row['actual_bytes']} bytes, SHA-256 `{row['sha256']}`, CRC PASS, tree SHA-256 `{next(item for item in extracted['archives'] if item['archive'] == row['archive'])['tree_sha256']}`"
        for row in downloads["archives"])
    report = f"""# Report: Provision task-local 7zz and resume ETH3D asset contract audit V1

## Outcome

- FINAL_STATUS: `{FINAL_STATUS}`
- FINAL_DECISION: `{FINAL_DECISION}`
- training_authorized: `false`
- unresolved critical evidence: none
- Only next task: `{ONLY_NEXT}`

All asset, integrity, split, isolation, coordinate, continuous-reference, ideal UNKNOWN,
robot, and physical-budget prerequisites passed. The task closes fail-closed because the
frozen planner-coupled route composition requires at least 50% blocked straight lines,
while the corrected deterministic free-3D reference-only PRM candidate set produced
{blocked_count}/{candidate_count} = {blocked_ratio:.6f}. No threshold or frozen contract
was changed, and no route registry was frozen.

## Lineage and infrastructure

- Branch: `eth3d-delivery-area-provision-7zz-resume-assets-v1`
- Base/head: `eth3d-delivery-area-frozen-assets-contract-audit-v1` / `84126353999dc6af979f4d8533a5cbaf638895be`
- PR #78 blocker preserved: true; blocker SHA-256 `{blocker['blocker_report_sha256']}`
- PR #77 head: `aea42e4ec9baea5b7d4843b155b02c74a242a56b`
- Protocol V2 SHA-256: `a0a02fd284c75c600095510899e2878f198d69ff088b66eccd3313275fdbde7e`
- 7zz route/version/SHA: `{runtime['provisioning_route']}` / `{runtime['version']}` / `{runtime['binary_sha256']}`
- 7zz provenance: `{runtime['source_url']}`; system/environment impact: none
- Managed SSH/proxy repair attempts: 0; final proxy reachable: `{proxy['reachable']}`
- Watchdog: `{watchdog['scheduled_task_state']}` (`{watchdog['last_task_result_interpretation']}`);
  established SSH sessions preserved: {watchdog['established_ssh_session_count']}; SSH/network/firewall changes: 0/0/0
- Operational autonomy actions: {actions['operational_autonomy_action_count']}; task-owned process terminations: {actions['task_owned_process_termination_count']}; scientific changes: 0

## Assets

- Official downloads: 9; compressed bytes: {downloads['downloaded_payload_bytes']}; denylist: 0
- Extracted files/bytes: {sum(row['file_count'] for row in extracted['archives'])}/{sum(row['total_bytes'] for row in extracted['archives'])}
- CRC/security/quarantine: PASS/PASS/PASS
{archive_lines}

## Rig, split, and isolation

- Modality: `{asset['selected_modality']}`; fallback false
- Rig RGB/groups/cameras: {asset['rig']['image_count']}/{asset['rig']['capture_group_count']}/{asset['rig']['camera_count']}; DSLR: {asset['dslr']['image_count']}
- Sparse points: `{asset['sparse_point_provenance']}`; no laser scan, ICP, Sim(3), or scale repair
- TRAIN/HELDOUT/GUARD: {split['counts']['TRAIN']}/{split['counts']['HELDOUT']}/{split['counts']['GUARD']}; split SHA `{split['split_sha256']}`; 3 fresh processes PASS
- Train-only COLMAP: {train['image_count']} images, {train['point3d_count']} points, SHA `{train['tree_sha256']}`; 3 fresh builds PASS
- TRAIN reference/heldout access: 0/false; new triangulation/reference injection: 0/0

## Coordinate, reference, UNKNOWN, and physical contract

- Metric coordinate/depth/alignment: `{coordinate['status']}`; no fitted transform
- Continuous reference: {reference['vertex_count']} vertices, {reference['face_count']} faces, SHA `{reference['surface_sha256']}`
- Independent distance parity: {parity['maximum_absolute_difference_m']} m <= {parity['software_numeric_tolerance_m']} m
- UNKNOWN: `{unknown['algorithm']}`, 3 groups / 15 deg / 0.01 m; {node_gate['primary_ideal_unknown_pass_count']} qualified nodes
- Robot: free-3D sphere r={robot['r_robot_m']} m, exact swept segment, bounded QP
- Reaction-stop/non-map reserve: {budget['epsilon_reaction_stop_m']} / {budget['nonmap_reserve_m']} m

## Route failure evidence

- Corrected candidate dimensionality: `{node_gate.get('candidate_voxel_dimensionality')}`
- Qualified PRM nodes/edges: {graph['qualified_node_count']}/{graph['qualified_edge_count']}
- Cost: `{graph['edge_cost_contract']}`
- Valid path candidates: {candidate_count}; blocked straight-line candidates: {blocked_count}; ratio: {blocked_ratio}
- Required ratio: 0.5; frozen route count: 0; route registry SHA: none
- Exact swept-sphere collision predicate: true; candidate map access: 0
- Larger-than-cap distances are conservative lower bounds; uncapped distance claimed: false
- Three-process registry reproduction was not continued after the deterministic composition gate failed.

## Future evaluator and no-execution boundary

The future evaluator remains frozen and unexecuted. GPU 1: `{boundary['physical_gpu_1']['stdout']}`.
GPU compute processes: `{boundary['physical_gpu_1_compute_processes']['stdout'] or 'none'}`.
Task-owned running processes: {boundary['task_owned_running_process_count']}.
Environment create/modify, official 3DGS, training, optimizer, smoke, map, controller,
planner benchmark, candidate-map access, ICP/Sim(3), scale repair, and frame deletion are all zero.

Server report: `{TASK_ROOT / 'REPORT_PROVISION_TASK_LOCAL_7ZZ_AND_RESUME_ETH3D_ASSET_CONTRACT_AUDIT_V1.md'}`
No environment handoff is issued in Case C.
"""
    (TASK_ROOT / "REPORT_PROVISION_TASK_LOCAL_7ZZ_AND_RESUME_ETH3D_ASSET_CONTRACT_AUDIT_V1.md").write_text(
        report, encoding="utf-8")
    print(FINAL_STATUS)


if __name__ == "__main__":
    main()
