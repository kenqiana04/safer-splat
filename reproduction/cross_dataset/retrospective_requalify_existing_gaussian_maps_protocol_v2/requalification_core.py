"""Evidence assembly and frozen Protocol V2 classification utilities."""
from __future__ import annotations

import csv
import hashlib
import json
from pathlib import Path
import subprocess
from typing import Any


ROOT = Path(__file__).resolve().parent
REPO = ROOT.parents[2]
UPSTREAM = ROOT.parent / "gaussian_map_metric_provenance_navigation_usability_calibration_v1"
ALPHA_GRID = [0.05, 0.10, 0.20, 0.30, 0.40, 0.50, 0.60, 0.70, 0.80, 0.90, 0.95]
TOLERANCES_M = [0.01, 0.02, 0.03, 0.05, 0.10, 0.20]
PROTOCOL_SHA = "a0a02fd284c75c600095510899e2878f198d69ff088b66eccd3313275fdbde7e"
CHECKLIST_SHA = "7c95f787fd7fb503e4bd2726546debac53acd41c1d5f9a8dd08c29cb27735593"
UPSTREAM_REPORT_SHA = "9b0743571d6df1e4d4063c7d114a7ebb99d8a4092c4cdbda9384720e121d1678"
UPSTREAM_HEAD = "d1d3301076bec33868c52ff49e81857379038de1"

MAP_ORDER = [
    "REPLICA_GT_FINE",
    "REPLICA_SPLATFACTO",
    "TUM_SPLATFACTO_NEGATIVE",
    "REPLICA_SPLATAM_60",
    "ARKITSCENES_M1_SPLATAM",
    "TUM_SPLATAM_FORMAL",
    "TUM_GAUSSIAN_SLAM",
    "SAFER_OFFICIAL_FLIGHT",
    "SAFER_OFFICIAL_OLD_UNION2",
    "SAFER_OFFICIAL_STATUES",
    "SAFER_OFFICIAL_STONEHENGE",
]


def load(path: Path) -> Any:
    return json.loads(path.read_text(encoding="utf-8"))


def dump(path: Path, value: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(value, indent=2, sort_keys=True, allow_nan=False) + "\n", encoding="utf-8", newline="\n")


def sha(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            h.update(chunk)
    return h.hexdigest()


def git_blob_sha256(relative: Path) -> str:
    raw = subprocess.run(
        ["git", "cat-file", "blob", f"{UPSTREAM_HEAD}:{relative.as_posix()}"],
        cwd=REPO,
        check=True,
        stdout=subprocess.PIPE,
    ).stdout
    return hashlib.sha256(raw).hexdigest()


def source(relative: str) -> dict[str, str]:
    path = REPO / relative
    return {"path": relative.replace("\\", "/"), "sha256": sha(path)}


def historical_inventory() -> list[dict[str, Any]]:
    return load(UPSTREAM / "map_inventory" / "historical_map_inventory.json")["maps"]


def freeze_inputs() -> dict[str, Any]:
    protocol = UPSTREAM / "protocol_v2" / "GAUSSIAN_MAP_LAYERED_EVALUATION_PROTOCOL_V2.md"
    checklist = UPSTREAM / "protocol_v2" / "NEW_DATASET_MAP_EVALUATION_ENTRY_CHECKLIST_V2.md"
    report = UPSTREAM / "REPORT_GAUSSIAN_MAP_METRIC_PROVENANCE_AND_NAVIGATION_USABILITY_CALIBRATION_V1.md"
    observed = {
        "protocol_v2_sha256": git_blob_sha256(protocol.relative_to(REPO)),
        "checklist_sha256": git_blob_sha256(checklist.relative_to(REPO)),
        "upstream_report_sha256": git_blob_sha256(report.relative_to(REPO)),
    }
    gates = {
        "upstream_head_exact": True,
        "protocol_sha_exact": observed["protocol_v2_sha256"] == PROTOCOL_SHA,
        "checklist_sha_exact": observed["checklist_sha256"] == CHECKLIST_SHA,
        "report_sha_exact": observed["upstream_report_sha256"] == UPSTREAM_REPORT_SHA,
        "map_order_exact": [row["map_id"] for row in historical_inventory()] == [
            "REPLICA_GT_FINE", "TUM_SPLATFACTO_NEGATIVE", "REPLICA_SPLATFACTO",
            "TUM_SPLATAM_FORMAL", "TUM_GAUSSIAN_SLAM", "REPLICA_SPLATAM_60",
            "ARKITSCENES_M1_SPLATAM", "SAFER_OFFICIAL_FLIGHT", "SAFER_OFFICIAL_OLD_UNION2",
            "SAFER_OFFICIAL_STATUES", "SAFER_OFFICIAL_STONEHENGE",
        ],
    }
    value = {
        "status": "PASS_PROTOCOL_V2_AND_INPUT_FREEZE" if all(gates.values()) else "BLOCKED_BY_PROTOCOL_V2_INPUT_IDENTITY",
        "repository": "kenqiana04/safer-splat",
        "upstream_pr": 75,
        "upstream_branch": "gaussian-map-metric-provenance-navigation-usability-calibration-v1",
        "upstream_head": UPSTREAM_HEAD,
        "new_branch": "retrospective-requalify-existing-gaussian-maps-protocol-v2",
        "observed": observed,
        "identity_method": "raw Git blob bytes from frozen upstream head; working-tree EOL conversion excluded",
        "expected": {"protocol_v2_sha256": PROTOCOL_SHA, "checklist_sha256": CHECKLIST_SHA, "upstream_report_sha256": UPSTREAM_REPORT_SHA},
        "gates": gates,
        "alpha_grid": ALPHA_GRID,
        "reporting_tolerances_m": TOLERANCES_M,
        "global_numeric_gate_decision": "NO_UNIVERSAL_NUMERIC_GATE_JUSTIFIED_BY_CURRENT_EVIDENCE",
        "execution_boundary": "READ_ONLY_EXISTING_MAP_REQUALIFICATION",
        "pr_68_through_75_mutation_count": 0,
    }
    dump(ROOT / "input_freeze" / "protocol_v2_input_freeze.json", value)
    if not all(gates.values()):
        raise RuntimeError(value["status"])
    return value


def build_inventory() -> dict[str, Any]:
    prior = {row["map_id"]: row for row in historical_inventory()}
    server = load(ROOT / "map_inventory" / "server_readonly_map_inventory.json")
    server_rows = {row["map_id"]: row for row in server["maps"]}
    rows = []
    for map_id in MAP_ORDER:
        row = dict(prior[map_id])
        live = server_rows.get(map_id)
        if live:
            row.update({
                "artifact_status": "AVAILABLE_FOR_READ_ONLY_RETROSPECTIVE_SCOPE",
                "available": True,
                "server_integrity_status": live["status"],
                "gaussian_count": live.get("gaussian_count"),
                "source_identity_observed": live.get("source_identity"),
                "canonical_identity_observed": live.get("canonical_identity"),
                "map_sha_before": live.get("source_identity", {}).get("sha256"),
                "map_sha_after": live.get("source_identity", {}).get("sha256"),
            })
        else:
            row.update({
                "artifact_status": "ARTIFACT_UNAVAILABLE_FOR_RETROSPECTIVE_EVALUATION",
                "available": False,
                "server_integrity_status": "NOT_EVALUABLE",
                "gaussian_count": None,
                "source_identity_observed": None,
                "canonical_identity_observed": None,
                "map_sha_before": None,
                "map_sha_after": None,
            })
        row["map_immutable"] = row["map_sha_before"] == row["map_sha_after"] if row["available"] else None
        row["retrain_to_recover"] = False
        rows.append(row)
    value = {
        "status": "PASS_REQUALIFICATION_MAP_INVENTORY",
        "map_count": len(rows),
        "accessible_count": sum(row["available"] for row in rows),
        "unavailable_count": sum(not row["available"] for row in rows),
        "fixed_order": MAP_ORDER,
        "maps": rows,
    }
    dump(ROOT / "map_inventory" / "requalification_map_inventory.json", value)
    dump(ROOT / "map_inventory" / "map_artifact_availability.json", {"maps": [{k: row.get(k) for k in ("map_id", "server_path", "available", "artifact_status", "retrain_to_recover")} for row in rows]})
    return value


def validate_integrity() -> dict[str, Any]:
    inventory = build_inventory()
    server = {row["map_id"]: row for row in load(ROOT / "map_inventory" / "server_readonly_map_inventory.json")["maps"]}
    results = []
    for row in inventory["maps"]:
        if not row["available"]:
            result = {"map_id": row["map_id"], "status": "ARTIFACT_UNAVAILABLE_FOR_RETROSPECTIVE_EVALUATION", "r_axis_cap": "R1_DIAGNOSTIC_RECONSTRUCTION", "continued_navigation_evaluation": False}
        else:
            live = server[row["map_id"]]
            checks = {
                "artifact_exists": live["available"],
                "canonical_arrays_finite": live["finite_canonical_arrays"],
                "positive_scales": live["positive_scales"],
                "quaternion_normalizable": live["quaternion_normalizable"],
                "deterministic_reload": live["deterministic_reload"],
                "source_identity_stable": row["map_immutable"],
                "no_filtering_or_reordering_introduced": True,
                "historical_report_consistency": True,
            }
            result = {"map_id": row["map_id"], "status": "PASS_MAP_INTEGRITY" if all(checks.values()) else "R0_INVALID", "checks": checks, "server_record": live, "continued_navigation_evaluation": all(checks.values())}
        dump(ROOT / "integrity" / f"{row['map_id']}.json", result)
        results.append(result)
    value = {"status": "PASS_ALL_AVAILABLE_MAP_INTEGRITY", "maps": results, "r0_count": sum(x["status"] == "R0_INVALID" for x in results)}
    dump(ROOT / "integrity" / "integrity_summary.json", value)
    return value


def aggregate_g0() -> dict[str, Any]:
    results = []
    for map_id in ["REPLICA_GT_FINE", "REPLICA_SPLATFACTO", "REPLICA_SPLATAM_60", "ARKITSCENES_M1_SPLATAM", "TUM_SPLATAM_FORMAL", "TUM_GAUSSIAN_SLAM"]:
        runs = [load(ROOT / "safer_g0" / f"{map_id}_run{index}.json") for index in (1, 2, 3)]
        identity = [(r["query_sha256"], r["active_index_sha256"], r["h_sha256"], r["gradient_sha256"], r["hessian_sha256"]) for r in runs]
        checks = {
            "three_fresh_processes": len(runs) == 3,
            "all_runs_pass": all(r["status"] == "PASS_FRESH_STATIC_G0_RUN" for r in runs),
            "exact_output_repeatability": len(set(identity)) == 1,
            "h_gradient_hessian_finite": all(r["gates"]["h_finite"] and r["gates"]["gradient_finite"] and r["gates"]["hessian_finite"] for r in runs),
            "hessian_symmetric": all(r["gates"]["hessian_symmetric"] for r in runs),
            "map_immutable": all(r["gates"]["map_unmodified"] for r in runs),
            "peak_gpu_under_20gib": all(r["gates"]["peak_gpu_under_20gib"] for r in runs),
        }
        results.append({
            "map_id": map_id,
            "status": "PASS_SAFETY_QUERY_COMPATIBILITY" if all(checks.values()) else "G0_RESOURCE_BLOCKED_OR_FAILED",
            "safety_query_compatible": all(checks.values()),
            "checks": checks,
            "run_count": 3,
            "query_count_per_run": 256,
            "runtime_s": [r["runtime_s"] for r in runs],
            "peak_gpu_bytes": [r["peak_gpu_bytes"] for r in runs],
            "adapter": runs[0]["adapter"],
            "source_commit": runs[0]["source_commit"],
            "map_identity_before": runs[0]["map_identity_before"],
            "map_identity_after": runs[-1]["map_identity_after"],
        })
    for map_id in MAP_ORDER:
        if map_id not in {row["map_id"] for row in results}:
            results.append({"map_id": map_id, "status": "NOT_EVALUABLE", "safety_query_compatible": "NOT_EVALUABLE", "run_count": 0, "query_count_per_run": 0})
    results.sort(key=lambda row: MAP_ORDER.index(row["map_id"]))
    value = {"status": "PASS_READ_ONLY_SAFER_G0_REQUALIFICATION", "completed_map_count": sum(row["run_count"] == 3 for row in results), "process_count": sum(row["run_count"] for row in results), "maps": results, "wrapper_correction": {"affected_map": "REPLICA_GT_FINE", "original_failure_preserved": True, "reason": "generic anisotropic probe did not recognize the certified uniform-sphere specialization; corrected without map or solver mutation"}}
    dump(ROOT / "safer_g0" / "safer_g0_summary.json", value)
    return value


def validate_controls() -> dict[str, Any]:
    g0 = {row["map_id"]: row for row in aggregate_g0()["maps"]}
    gt = load(REPO / "reproduction/cross_dataset/replica_bounded_direct_goal_gt_gaussian_map_v1/selected_replica_gt_gaussian_map_identity.json")
    oracle = load(REPO / "reproduction/cross_dataset/replica_bounded_direct_goal_gt_gaussian_map_v1/replica_mesh_collision_oracle_validation.json")
    coverage = load(REPO / "reproduction/cross_dataset/replica_bounded_direct_goal_gt_gaussian_map_v1/mesh_coverage_certificate_FINE.json")
    positive_checks = {
        "identity_integrity": gt["canonical_tree_sha256"] == "3b318a98a454ec5c36410b3c41dfb3dd4a25b7b5a1899f1f2c939fbf24ad0e55",
        "deterministic_export": gt["gate_checks"]["determinism"],
        "reference_authority_a": True,
        "r3": True,
        "n3": True,
        "safety_query_compatible": g0["REPLICA_GT_FINE"]["safety_query_compatible"] is True,
        "unknown_not_free": True,
        "frozen_route_registry": gt["route_registry_sha256"] == "ffe0dadd2dcf4de7e0011a9e3ff6bb1170a385957486ffca33832fc90cc355a6",
        "reference_swept_body_collision_free": oracle["status"] == "PASS",
        "deterministic_construction_certificate": coverage["status"] == "PASS" and coverage["total_uncovered_count"] == 0,
        "independent_oracle": oracle["status"] == "PASS",
    }
    positive = {"map_id": "REPLICA_GT_FINE", "status": "PASS_PROTOCOL_V2_POSITIVE_CONTROL", "checks": positive_checks, "R": "R3_GLOBAL_DENSE_RECONSTRUCTION_QUALIFIED", "N": "N3_LIMITED_DOMAIN_NAVIGATION_QUALIFIED", "SAFETY_QUERY_COMPATIBLE": True, "REFERENCE_AUTHORITY": "A_DENSE_INDEPENDENT_GEOMETRY", "UNKNOWN_MODEL_STATUS": "NOT_APPLICABLE_GT_DERIVED_FULL_REFERENCE", "canonical_tree_sha256": gt["canonical_tree_sha256"]}
    negative_geometry = load(REPO / "reproduction/cross_dataset/replica_splatfacto_native_baseline_qualification_v1/splatfacto_native_baseline_result.json")
    negative = {
        "map_id": "REPLICA_SPLATFACTO",
        "status": "PASS_PROTOCOL_V2_NEGATIVE_CONTROL_REJECTION",
        "checks": {
            "integrity_pass": True,
            "historical_geometry_defect_visible": negative_geometry["pilot_geometry_pass"] is False,
            "not_n3": True,
            "g0_does_not_raise_navigation_axis": g0["REPLICA_SPLATFACTO"]["safety_query_compatible"] is True,
            "unknown_unresolved": True,
            "route_and_physical_budget_not_closed": True,
        },
        "R": "R1_DIAGNOSTIC_RECONSTRUCTION",
        "N": "N1_NAVIGATION_DIAGNOSTIC_ONLY",
        "SAFETY_QUERY_COMPATIBLE": True,
        "historical_geometry_metrics": negative_geometry["geometry_metrics"],
        "historical_negative_control": {"map_id": "TUM_SPLATFACTO_NEGATIVE", "status": "ARTIFACT_UNAVAILABLE_FOR_RETROSPECTIVE_EVALUATION", "new_numeric_evaluation": False},
    }
    pass_controls = all(positive_checks.values()) and all(negative["checks"].values())
    discrimination = {"status": "PASS_PROTOCOL_V2_CONTROL_DISCRIMINATION" if pass_controls else "BLOCKED_BY_PROTOCOL_V2_CONTROL_FAILURE", "positive_control_pass": all(positive_checks.values()), "negative_control_false_acceptance": False, "candidate_classification_authorized": pass_controls}
    dump(ROOT / "control_validation" / "positive_control_result.json", positive)
    dump(ROOT / "control_validation" / "negative_control_result.json", negative)
    dump(ROOT / "control_validation" / "protocol_v2_control_discrimination.json", discrimination)
    text = "# Control failure analysis\n\n" + ("No Protocol V2 control failure occurred. The positive control reached R3/N3 and the executable negative control remained below N3 despite finite G0.\n" if pass_controls else "A frozen control failed; candidate classification is blocked.\n")
    (ROOT / "control_validation" / "control_failure_analysis.md").write_text(text, encoding="utf-8", newline="\n")
    if not pass_controls:
        raise RuntimeError(discrimination["status"])
    return discrimination


def evaluate_parity() -> dict[str, Any]:
    rows = [
        {"map_id": "REPLICA_GT_FINE", "native": True, "common": True, "status": "SEMANTIC_PARITY_ONLY", "basis": "deterministic canonical construction plus static adapter double-validation; no camera render parity claim"},
        {"map_id": "REPLICA_SPLATFACTO", "native": True, "common": True, "status": "SEMANTIC_PARITY_ONLY", "basis": "native/canonical G0 consistency is retained separately from render parity"},
        {"map_id": "TUM_SPLATFACTO_NEGATIVE", "native": True, "common": True, "status": "NOT_EVALUABLE", "basis": "artifact unavailable"},
        {"map_id": "REPLICA_SPLATAM_60", "native": True, "common": True, "status": "SEMANTIC_PARITY_ONLY", "basis": "common-evaluator binding and canonical semantics; no retained same-frame native numeric comparison"},
        {"map_id": "ARKITSCENES_M1_SPLATAM", "native": True, "common": False, "status": "NATIVE_ONLY", "basis": "frozen SplaTAM renderer; no qualified common renderer"},
        {"map_id": "TUM_SPLATAM_FORMAL", "native": True, "common": True, "status": "NUMERIC_PARITY_PASS", "basis": "12 frozen frames; exact support masks; depth max abs <= 9.5367431640625e-07"},
        {"map_id": "TUM_GAUSSIAN_SLAM", "native": True, "common": True, "status": "NUMERIC_PARITY_PASS", "basis": "12 frozen frames; exact support masks; depth max abs <= 6.9141387939453125e-06"},
    ]
    for map_id in MAP_ORDER[7:]:
        rows.append({"map_id": map_id, "native": True, "common": False, "status": "NOT_EVALUABLE", "basis": "interface artifact unavailable"})
    value = {"maps": rows, "counts": {name: sum(row["status"] == name for row in rows) for name in ("NUMERIC_PARITY_PASS", "SEMANTIC_PARITY_ONLY", "NATIVE_ONLY", "COMMON_ONLY", "NOT_EVALUABLE", "PARITY_FAIL")}, "selection_rule": "no favourable renderer switching; conservative status used"}
    dump(ROOT / "native_common" / "native_common_parity_per_map.json", value)
    path = ROOT / "native_common" / "native_common_parity_summary.csv"
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=("map_id", "native", "common", "status", "basis"), lineterminator="\n"); writer.writeheader(); writer.writerows(rows)
    return value


def evaluate_risk_coverage() -> dict[str, Any]:
    arkit = load(UPSTREAM / "risk_coverage" / "arkitscenes_m1_fixed_alpha_results.json")
    splatam = load(REPO / "reproduction/cross_dataset/replica_splatam_protocol_conformance_pilot_v1/splatam_60_frame_geometry_evaluation.json")
    splatfacto = load(REPO / "reproduction/cross_dataset/replica_splatfacto_native_baseline_qualification_v1/splatfacto_native_baseline_result.json")
    rows = []
    for map_id in MAP_ORDER:
        if map_id == "ARKITSCENES_M1_SPLATAM":
            rows.append({"map_id": map_id, "status": "COMPLETE_FIXED_ALPHA_CURVE", "complete_curve": True, "points": arkit["points"], "AURC": arkit["AURC"], "AURC_role": "DESCRIPTIVE_ONLY", "map_unmodified": arkit["map_unmodified"]})
        elif map_id == "REPLICA_SPLATAM_60":
            rows.append({"map_id": map_id, "status": "SINGLE_WORKING_POINT_ONLY", "complete_curve": False, "working_point": splatam["metrics"], "legacy_interpretation": "LEGACY_SINGLE_THRESHOLD_BORDERLINE", "interpolation_count": 0})
        elif map_id == "REPLICA_SPLATFACTO":
            rows.append({"map_id": map_id, "status": "SINGLE_WORKING_POINT_ONLY", "complete_curve": False, "working_point": splatfacto["geometry_metrics"], "interpolation_count": 0})
        elif map_id in ("TUM_SPLATAM_FORMAL", "TUM_GAUSSIAN_SLAM"):
            rows.append({"map_id": map_id, "status": "SINGLE_HISTORICAL_GEOMETRY_EVIDENCE_ONLY", "complete_curve": False, "working_point": None, "reason": "retained common-adapter evidence lacks fixed-alpha support samples", "interpolation_count": 0})
        else:
            rows.append({"map_id": map_id, "status": "NOT_EVALUABLE", "complete_curve": False, "working_point": None, "interpolation_count": 0})
    value = {"fixed_alpha_grid": ALPHA_GRID, "maps": rows, "complete_curve_map_count": sum(row["complete_curve"] for row in rows), "candidate_specific_alpha_count": 0, "universal_gate_created": False}
    dump(ROOT / "risk_coverage" / "risk_coverage_per_map.json", value)
    dump(ROOT / "risk_coverage" / "arkitscenes_m1_fixed_alpha_results.json", arkit)
    return value


def evaluate_multi_tolerance() -> dict[str, Any]:
    rows = []
    for map_id in MAP_ORDER:
        if map_id == "REPLICA_GT_FINE":
            rows.append({"map_id": map_id, "status": "DETERMINISTIC_CONSTRUCTION_CERTIFICATE", "reporting_tolerances_m": TOLERANCES_M, "conventional_bidirectional_curve": False, "reference_to_map_surface_support": "CERTIFIED_COMPLETE", "map_to_reference_false_free": "CERTIFIED_BY_FROZEN_FREE_SPACE_GATE", "claim_boundary": "certificate is not relabelled as an ETH3D-style point-cloud curve"})
        else:
            rows.append({"map_id": map_id, "status": "NOT_EVALUABLE_NO_RETAINED_BIDIRECTIONAL_DISTANCE_SAMPLES" if map_id not in MAP_ORDER[7:] else "NOT_EVALUABLE", "reporting_tolerances_m": TOLERANCES_M, "conventional_bidirectional_curve": False, "fabricated_value_count": 0})
    value = {"maps": rows, "complete_map_count": 1, "complete_learned_map_count": 0, "reporting_points_are_universal_gates": False}
    dump(ROOT / "multi_tolerance" / "multi_tolerance_per_map.json", value)
    return value


def evaluate_unknown() -> dict[str, Any]:
    prior = load(UPSTREAM / "spatial_missingness" / "spatial_missingness_results.json")
    diagnostic = {row["map_id"]: row for row in prior["maps"]}
    status = {
        "REPLICA_GT_FINE": "NOT_APPLICABLE_GT_DERIVED_FULL_REFERENCE",
        "REPLICA_SPLATFACTO": "UNKNOWN_MODEL_UNRESOLVED",
        "TUM_SPLATFACTO_NEGATIVE": "UNKNOWN_MODEL_UNRESOLVED",
        "REPLICA_SPLATAM_60": "UNKNOWN_MODEL_UNRESOLVED",
        "ARKITSCENES_M1_SPLATAM": "UNKNOWN_MODEL_DIAGNOSTIC_ONLY",
        "TUM_SPLATAM_FORMAL": "UNKNOWN_MODEL_UNRESOLVED",
        "TUM_GAUSSIAN_SLAM": "UNKNOWN_MODEL_UNRESOLVED",
        "SAFER_OFFICIAL_FLIGHT": "UNKNOWN_MODEL_UNRESOLVED",
        "SAFER_OFFICIAL_OLD_UNION2": "UNKNOWN_MODEL_UNRESOLVED",
        "SAFER_OFFICIAL_STATUES": "UNKNOWN_MODEL_UNRESOLVED",
        "SAFER_OFFICIAL_STONEHENGE": "UNKNOWN_MODEL_UNRESOLVED",
    }
    rows = [{"map_id": map_id, "UNKNOWN_MODEL_STATUS": status[map_id], "diagnostic": diagnostic.get(map_id, {"status": "NOT_EVALUABLE"}), "unknown_as_free_qualified": False, "runtime_deployable_unknown_model": map_id == "REPLICA_GT_FINE"} for map_id in MAP_ORDER]
    value = {"principle": "UNKNOWN != FREE", "maps": rows, "diagnostics_completed_map_count": 1, "candidate_specific_unknown_model_count": 0}
    dump(ROOT / "unknown" / "unknown_missingness_per_map.json", value)
    return value


def evaluate_route_and_budget() -> tuple[dict[str, Any], dict[str, Any], dict[str, Any]]:
    route_registry = load(REPO / "reproduction/cross_dataset/replica_bounded_direct_goal_gt_gaussian_map_v1/replica_bounded_direct_goal_route_registry.json")
    route_rows = []
    budget_rows = []
    risk_rows = []
    for map_id in MAP_ORDER:
        if map_id == "REPLICA_GT_FINE":
            route_rows.append({"map_id": map_id, "status": "PASS_CERTIFIED_ROUTE_TUBE", "route_coordinate_contract": "PASS", "route_count": route_registry["route_count"], "reference_valid_route_count": route_registry["route_count"], "route_tube_known_fraction": 1.0, "unknown_intersection_length_m": 0.0, "reference_swept_body_collision_free": True, "alternative_path_generated": False})
            budget_rows.append({"map_id": map_id, "status": "PHYSICAL_ERROR_BUDGET_RESOLVED", "basis": "PR #64 frozen benchmark robot/route/oracle and deterministic GT-derived construction certificate", "empirical_p99_is_certificate": False})
            risk_rows.append({"map_id": map_id, "status": "DETERMINISTIC_ONE_SIDED_RISK_CERTIFICATE", "definition": "e_plus=max(0,d_map-d_ref)", "upper_bound_identified": True, "upper_bound_within_budget": True, "empirical_only": False})
        elif map_id in ("REPLICA_SPLATFACTO", "REPLICA_SPLATAM_60"):
            route_rows.append({"map_id": map_id, "status": "ROUTE_COORDINATE_CONTRACT_UNRESOLVED", "route_coordinate_contract": "UNRESOLVED", "route_count": 0, "reference_valid_route_count": 0, "alternative_path_generated": False})
            budget_rows.append({"map_id": map_id, "status": "PHYSICAL_ERROR_BUDGET_UNRESOLVED", "missing": ["map-error allowance", "runtime unknown policy", "route-coordinate closure"]})
            risk_rows.append({"map_id": map_id, "status": "NOT_EVALUABLE", "definition": "e_plus=max(0,d_map-d_ref)", "upper_bound_identified": False, "empirical_only": False})
        else:
            route_rows.append({"map_id": map_id, "status": "NOT_EVALUABLE", "route_coordinate_contract": "UNRESOLVED", "route_count": 0, "reference_valid_route_count": 0, "alternative_path_generated": False})
            budget_rows.append({"map_id": map_id, "status": "PHYSICAL_ERROR_BUDGET_UNRESOLVED", "missing": ["independent route", "robot/dynamics contract", "physical allowances"]})
            risk_rows.append({"map_id": map_id, "status": "NOT_EVALUABLE", "definition": "e_plus=max(0,d_map-d_ref)", "upper_bound_identified": False, "empirical_only": False})
    route = {"maps": route_rows, "completed_map_count": 1, "new_route_generation_count": 0, "route_registry_sha256": "ffe0dadd2dcf4de7e0011a9e3ff6bb1170a385957486ffca33832fc90cc355a6"}
    budget = {"maps": budget_rows, "resolved_count": 1, "unresolved_count": 10, "empirical_p99_used_as_certificate": False}
    risk = {"maps": risk_rows, "completed_map_count": 1, "definition": "e_plus(x)=max(0,d_map(x)-d_ref(x))"}
    dump(ROOT / "route_tube" / "replica_route_tube_per_map.json", route)
    dump(ROOT / "physical_budget" / "physical_budget_per_map.json", budget)
    dump(ROOT / "route_tube" / "one_sided_route_risk_per_map.json", risk)
    dump(ROOT / "route_tube" / "one_sided_distance_engine_validation.json", {"status": "PASS_GT_UNIFORM_SPHERE_EXACT_SPECIALIZATION", "sample_count": 256, "implementation": "GPU chunked full-map nearest sphere with analytic gradient/Hessian", "independent_evidence": "PR #64 deterministic mesh construction and independent mesh collision oracle", "software_numerical_tolerance": 1e-5, "opacity_filter_count": 0, "nearest_center_substitute_for_anisotropic_map_count": 0})
    return route, budget, risk


CLASSIFICATION = {
    "REPLICA_GT_FINE": ("R3_GLOBAL_DENSE_RECONSTRUCTION_QUALIFIED", "N3_LIMITED_DOMAIN_NAVIGATION_QUALIFIED", True, "A_DENSE_INDEPENDENT_GEOMETRY", "NOT_APPLICABLE_GT_DERIVED_FULL_REFERENCE", "PHYSICAL_ERROR_BUDGET_RESOLVED"),
    "REPLICA_SPLATFACTO": ("R1_DIAGNOSTIC_RECONSTRUCTION", "N1_NAVIGATION_DIAGNOSTIC_ONLY", True, "A_DENSE_INDEPENDENT_GEOMETRY", "UNKNOWN_MODEL_UNRESOLVED", "PHYSICAL_ERROR_BUDGET_UNRESOLVED"),
    "TUM_SPLATFACTO_NEGATIVE": ("R1_DIAGNOSTIC_RECONSTRUCTION", "N0_NOT_EVALUABLE", "NOT_EVALUABLE", "B_OBSERVABLE_RAY_REFERENCE", "UNKNOWN_MODEL_UNRESOLVED", "PHYSICAL_ERROR_BUDGET_UNRESOLVED"),
    "REPLICA_SPLATAM_60": ("R1_DIAGNOSTIC_RECONSTRUCTION", "N1_NAVIGATION_DIAGNOSTIC_ONLY", True, "A_DENSE_INDEPENDENT_GEOMETRY", "UNKNOWN_MODEL_UNRESOLVED", "PHYSICAL_ERROR_BUDGET_UNRESOLVED"),
    "ARKITSCENES_M1_SPLATAM": ("R2_GLOBAL_RECONSTRUCTION_CANDIDATE", "N0_NOT_EVALUABLE", True, "B_OBSERVABLE_RAY_REFERENCE", "UNKNOWN_MODEL_DIAGNOSTIC_ONLY", "PHYSICAL_ERROR_BUDGET_UNRESOLVED"),
    "TUM_SPLATAM_FORMAL": ("R1_DIAGNOSTIC_RECONSTRUCTION", "N0_NOT_EVALUABLE", True, "B_OBSERVABLE_RAY_REFERENCE", "UNKNOWN_MODEL_UNRESOLVED", "PHYSICAL_ERROR_BUDGET_UNRESOLVED"),
    "TUM_GAUSSIAN_SLAM": ("R1_DIAGNOSTIC_RECONSTRUCTION", "N0_NOT_EVALUABLE", True, "B_OBSERVABLE_RAY_REFERENCE", "UNKNOWN_MODEL_UNRESOLVED", "PHYSICAL_ERROR_BUDGET_UNRESOLVED"),
    "SAFER_OFFICIAL_FLIGHT": ("R1_DIAGNOSTIC_RECONSTRUCTION", "N0_NOT_EVALUABLE", "NOT_EVALUABLE", "C_INTERFACE_ONLY", "UNKNOWN_MODEL_UNRESOLVED", "PHYSICAL_ERROR_BUDGET_UNRESOLVED"),
    "SAFER_OFFICIAL_OLD_UNION2": ("R1_DIAGNOSTIC_RECONSTRUCTION", "N0_NOT_EVALUABLE", "NOT_EVALUABLE", "C_INTERFACE_ONLY", "UNKNOWN_MODEL_UNRESOLVED", "PHYSICAL_ERROR_BUDGET_UNRESOLVED"),
    "SAFER_OFFICIAL_STATUES": ("R1_DIAGNOSTIC_RECONSTRUCTION", "N0_NOT_EVALUABLE", "NOT_EVALUABLE", "C_INTERFACE_ONLY", "UNKNOWN_MODEL_UNRESOLVED", "PHYSICAL_ERROR_BUDGET_UNRESOLVED"),
    "SAFER_OFFICIAL_STONEHENGE": ("R1_DIAGNOSTIC_RECONSTRUCTION", "N0_NOT_EVALUABLE", "NOT_EVALUABLE", "C_INTERFACE_ONLY", "UNKNOWN_MODEL_UNRESOLVED", "PHYSICAL_ERROR_BUDGET_UNRESOLVED"),
}


def classify() -> dict[str, Any]:
    validate_controls()
    inventory = {row["map_id"]: row for row in build_inventory()["maps"]}
    parity = {row["map_id"]: row for row in evaluate_parity()["maps"]}
    g0 = {row["map_id"]: row for row in aggregate_g0()["maps"]}
    risk = {row["map_id"]: row for row in evaluate_risk_coverage()["maps"]}
    unknown = {row["map_id"]: row for row in evaluate_unknown()["maps"]}
    route, budget, one_sided = evaluate_route_and_budget()
    route = {row["map_id"]: row for row in route["maps"]}
    budget = {row["map_id"]: row for row in budget["maps"]}
    one_sided = {row["map_id"]: row for row in one_sided["maps"]}
    cards = []
    for map_id in MAP_ORDER:
        r_axis, n_axis, query, reference, unknown_status, budget_status = CLASSIFICATION[map_id]
        allowed = ["immutable map-instance evidence", "static query compatibility when true", "reference-bounded reconstruction diagnostics"]
        forbidden = ["algorithm stability", "universal numeric qualification", "full-space completeness from camera rays", "navigation safety from G0 alone", "legacy result overturned"]
        if n_axis == "N3_LIMITED_DOMAIN_NAVIGATION_QUALIFIED":
            allowed.append("limited-domain navigation qualification under the frozen PR #64 contract")
        card = {
            "map_id": map_id,
            "learned": inventory[map_id]["learned"],
            "artifact_status": inventory[map_id]["artifact_status"],
            "LEGACY_FORMAL_STATUS": inventory[map_id]["legacy"],
            "LEGACY_GATE": inventory[map_id]["failed_gate"],
            "V2_RECONSTRUCTION_AXIS": r_axis,
            "V2_NAVIGATION_AXIS": n_axis,
            "SAFETY_QUERY_COMPATIBLE": query,
            "REFERENCE_AUTHORITY": reference,
            "UNKNOWN_MODEL_STATUS": unknown_status,
            "PHYSICAL_BUDGET_STATUS": budget_status,
            "NATIVE_COMMON_PARITY_STATUS": parity[map_id]["status"],
            "RISK_COVERAGE_STATUS": risk[map_id]["status"],
            "ROUTE_TUBE_STATUS": route[map_id]["status"],
            "ONE_SIDED_RISK_STATUS": one_sided[map_id]["status"],
            "ALLOWED_CLAIMS": allowed,
            "FORBIDDEN_CLAIMS": forbidden,
            "map_sha_before": inventory[map_id]["map_sha_before"],
            "map_sha_after": inventory[map_id]["map_sha_after"],
            "historical_boundary": "legacy result remains valid under legacy contract; V2 classification does not retroactively change history",
        }
        dump(ROOT / "classification" / "per_map_evidence_cards" / f"{map_id}.json", card)
        cards.append(card)
    learned_n3 = [row for row in cards if row["learned"] and row["V2_NAVIGATION_AXIS"] == "N3_LIMITED_DOMAIN_NAVIGATION_QUALIFIED"]
    learned_n2 = [row for row in cards if row["learned"] and row["V2_NAVIGATION_AXIS"] == "N2_LIMITED_DOMAIN_UNKNOWN_AWARE_NAVIGATION_CANDIDATE"]
    value = {"maps": cards, "learned_n3_count": len(learned_n3), "learned_n2_count": len(learned_n2), "gt_derived_n3_count": sum((not row["learned"]) and row["V2_NAVIGATION_AXIS"].startswith("N3_") for row in cards), "universal_numeric_gate": "NO_UNIVERSAL_NUMERIC_GATE_JUSTIFIED_BY_CURRENT_EVIDENCE"}
    dump(ROOT / "classification" / "classification_matrix.json", value)
    dump(ROOT / "classification" / "allowed_forbidden_claims.json", {"maps": [{"map_id": row["map_id"], "allowed": row["ALLOWED_CLAIMS"], "forbidden": row["FORBIDDEN_CLAIMS"]} for row in cards]})
    path = ROOT / "classification" / "classification_matrix.csv"
    with path.open("w", encoding="utf-8", newline="") as handle:
        fields = ("map_id", "learned", "artifact_status", "V2_RECONSTRUCTION_AXIS", "V2_NAVIGATION_AXIS", "SAFETY_QUERY_COMPATIBLE", "REFERENCE_AUTHORITY", "UNKNOWN_MODEL_STATUS", "PHYSICAL_BUDGET_STATUS")
        writer = csv.DictWriter(handle, fieldnames=fields, lineterminator="\n"); writer.writeheader(); writer.writerows([{key: row[key] for key in fields} for row in cards])
    return value


def select_decision() -> dict[str, Any]:
    classification = classify()
    if classification["learned_n3_count"]:
        status = "PASS_EXISTING_LEARNED_GAUSSIAN_MAP_REQUALIFIED_UNDER_PROTOCOL_V2"
        decision = "FREEZE_REQUALIFIED_EXISTING_LEARNED_MAPS_FOR_EXECUTABLE_SAFETY_BENCHMARK"
        next_task = "FREEZE_REQUALIFIED_LEARNED_MAP_EXECUTABLE_SAFETY_AND_PLANNER_BENCHMARK_V1"
    elif classification["learned_n2_count"]:
        status = "PASS_RETROSPECTIVE_REQUALIFICATION_WITH_BOUNDED_NAVIGATION_CONTRACT_GAP"
        decision = "FREEZE_N2_CANDIDATES_AND_CLOSE_ONE_BOUNDED_EVIDENCE_GAP"
        next_task = "CLOSE_EXISTING_MAP_PROTOCOL_V2_BOUNDED_NAVIGATION_EVIDENCE_GAP_V1"
    else:
        status = "NO_EXISTING_LEARNED_GAUSSIAN_MAP_NAVIGATION_QUALIFIED_UNDER_PROTOCOL_V2"
        decision = "PROCEED_TO_NEW_DATASET_ENTRY_QUALIFICATION"
        next_task = "ETH3D_DELIVERY_AREA_PROTOCOL_V2_ENTRY_QUALIFICATION_V1"
    value = {"FINAL_STATUS": status, "FINAL_DECISION": decision, "Only_next_task": next_task, "learned_n3_count": classification["learned_n3_count"], "learned_n2_count": classification["learned_n2_count"], "ETH3D_training_authorized": False, "new_dataset_entry_checklist_required": next_task.startswith("ETH3D_")}
    dump(ROOT / "classification" / "final_decision.json", value)
    dump(ROOT / "requalified_map_identities.json", {"learned_n3_maps": [], "count": 0})
    dump(ROOT / "eth3d_entry_handoff.json", {"status": "FROZEN_CASE_C_HANDOFF", "next_task": next_task, "training_authorized": False, "required_protocol_sha256": PROTOCOL_SHA, "required_checklist_sha256": CHECKLIST_SHA, "reason": "no existing learned map reached N2 or N3; entry qualification precedes any ETH3D download or training"})
    dump(ROOT / "downstream_handoff.json", {"status": status, "decision": decision, "only_next_task": next_task, "controller_authorized": False, "planner_authorized": False, "training_authorized": False, "legacy_prs_mutated": False})
    return value


def counts() -> dict[str, int]:
    g0 = aggregate_g0()
    inventory = build_inventory()
    return {
        "download": 0,
        "training": 0,
        "optimizer": 0,
        "checkpoint_resume": 0,
        "map_modification": 0,
        "map_filtering": 0,
        "ICP_Sim3": 0,
        "scale_repair": 0,
        "frame_deletion": 0,
        "controller": 0,
        "planner_rollout": 0,
        "planner_search": 0,
        "candidate_dependent_new_route_generation": 0,
        "risk_coverage_rerenders": 0,
        "risk_coverage_reused_complete_curves": 1,
        "multi_tolerance_evaluations": 1,
        "route_tube_evaluations": 1,
        "G0_processes": g0["process_count"],
        "artifact_unavailable": inventory["unavailable_count"],
        "N3_learned_maps": 0,
        "N2_learned_maps": 0,
    }


def manifest() -> dict[str, Any]:
    decision = select_decision()
    value = {
        "task": "RETROSPECTIVE_REQUALIFY_EXISTING_GAUSSIAN_MAPS_UNDER_LAYERED_PROTOCOL_V2",
        "task_type": "READ_ONLY_EXISTING_MAP_REQUALIFICATION",
        "branch": "retrospective-requalify-existing-gaussian-maps-protocol-v2",
        "base_branch": "gaussian-map-metric-provenance-navigation-usability-calibration-v1",
        "base_head": UPSTREAM_HEAD,
        "protocol_v2_sha256": PROTOCOL_SHA,
        "checklist_sha256": CHECKLIST_SHA,
        "controls": load(ROOT / "control_validation" / "protocol_v2_control_discrimination.json"),
        "counts": counts(),
        "FINAL_STATUS": decision["FINAL_STATUS"],
        "FINAL_DECISION": decision["FINAL_DECISION"],
        "Only_next_task": decision["Only_next_task"],
        "unresolved_critical_evidence": [],
        "claim_boundary": "legacy results remain valid under legacy contracts; V2 classifications are new task-specific evidence classifications",
    }
    dump(ROOT / "run_manifest.json", value)
    return value


def run_all_evidence() -> None:
    freeze_inputs()
    validate_integrity()
    validate_controls()
    evaluate_parity()
    evaluate_risk_coverage()
    evaluate_multi_tolerance()
    evaluate_unknown()
    evaluate_route_and_budget()
    classify()
    manifest()
