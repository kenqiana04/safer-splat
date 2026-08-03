"""Fail-closed validator for the complete Protocol V2 requalification payload."""
from __future__ import annotations

import hashlib
import json
import subprocess
from collections import Counter
from pathlib import Path

from requalification_core import MAP_ORDER, ROOT


EXPECTED_PROTOCOL = "a0a02fd284c75c600095510899e2878f198d69ff088b66eccd3313275fdbde7e"
EXPECTED_CHECKLIST = "7c95f787fd7fb503e4bd2726546debac53acd41c1d5f9a8dd08c29cb27735593"
EXPECTED_HEAD = "d1d3301076bec33868c52ff49e81857379038de1"
R_VALUES = {"R0_INVALID", "R1_DIAGNOSTIC_RECONSTRUCTION", "R2_GLOBAL_RECONSTRUCTION_CANDIDATE", "R3_GLOBAL_DENSE_RECONSTRUCTION_QUALIFIED"}
N_VALUES = {"N0_NOT_EVALUABLE", "N1_NAVIGATION_DIAGNOSTIC_ONLY", "N2_LIMITED_DOMAIN_UNKNOWN_AWARE_NAVIGATION_CANDIDATE", "N3_LIMITED_DOMAIN_NAVIGATION_QUALIFIED"}
QUERY_VALUES = {True, False, "NOT_EVALUABLE"}
UNKNOWN_VALUES = {"EXPLICIT_UNKNOWN_MODEL_AVAILABLE", "UNKNOWN_MODEL_DIAGNOSTIC_ONLY", "UNKNOWN_MODEL_UNRESOLVED", "NOT_APPLICABLE_GT_DERIVED_FULL_REFERENCE"}
REFERENCE_VALUES = {"A_DENSE_INDEPENDENT_GEOMETRY", "B_OBSERVABLE_RAY_REFERENCE", "C_INTERFACE_ONLY", "UNRESOLVED"}
PARITY_VALUES = {"NUMERIC_PARITY_PASS", "SEMANTIC_PARITY_ONLY", "NATIVE_ONLY", "COMMON_ONLY", "NOT_EVALUABLE", "PARITY_FAIL"}
ZERO_KEYS = {"download", "training", "optimizer", "checkpoint_resume", "map_modification", "map_filtering", "ICP_Sim3", "scale_repair", "frame_deletion", "controller", "planner_rollout", "planner_search", "candidate_dependent_new_route_generation"}
FIGURES = [
    "protocol_v2_control_discrimination.png", "map_artifact_availability.png", "map_reference_authority.png",
    "native_common_parity.png", "risk_coverage_all_available_maps.png", "conditional_error_vs_coverage.png",
    "multi_tolerance_replica_maps.png", "spatial_missingness_summary.png", "unknown_model_status.png",
    "replica_route_tube_knownness.png", "replica_one_sided_risk.png", "physical_budget_status.png",
    "safer_g0_compatibility.png", "reconstruction_axis_classification.png", "navigation_axis_classification.png",
    "two_axis_map_matrix.png", "legacy_vs_v2_interpretation.png", "candidate_evidence_gaps.png",
    "final_decision_tree.png", "next_task_handoff.png",
]
SCRIPTS = [
    "freeze_protocol_v2_and_inputs.py", "build_requalification_map_inventory.py", "validate_control_maps.py",
    "validate_map_integrity.py", "evaluate_native_common_parity.py", "evaluate_fixed_alpha_risk_coverage.py",
    "evaluate_multi_tolerance_geometry.py", "evaluate_unknown_missingness.py", "evaluate_replica_route_tube.py",
    "derive_route_physical_budget.py", "validate_one_sided_distance_engine.py", "evaluate_one_sided_route_risk.py",
    "run_readonly_safer_g0.py", "classify_protocol_v2_axes.py", "select_requalification_decision.py",
    "run_requalification.py", "generate_figures.py", "build_report.py", "finalize_runtime_record.py",
]


def load(path: str):
    return json.loads((ROOT / path).read_text(encoding="utf-8"))


def git_blob_sha(path: str) -> str:
    raw = subprocess.check_output(["git", "show", f"{EXPECTED_HEAD}:{path}"], cwd=ROOT)
    return hashlib.sha256(raw).hexdigest()


def check(condition: bool, name: str, checks: dict[str, bool], failures: list[str]) -> None:
    checks[name] = bool(condition)
    if not condition:
        failures.append(name)


def main() -> None:
    checks: dict[str, bool] = {}
    failures: list[str] = []
    freeze = load("input_freeze/protocol_v2_input_freeze.json")
    manifest = load("run_manifest.json")
    inventory = load("map_inventory/requalification_map_inventory.json")
    initial_server_inventory = load("map_inventory/server_readonly_map_inventory.json")
    final_server_inventory = load("map_inventory/final_server_readonly_map_inventory.json")
    controls = load("control_validation/protocol_v2_control_discrimination.json")
    matrix = load("classification/classification_matrix.json")["maps"]
    claims = load("classification/allowed_forbidden_claims.json")["maps"]
    parity = load("native_common/native_common_parity_per_map.json")["maps"]
    risk = load("risk_coverage/risk_coverage_per_map.json")["maps"]
    multi = load("multi_tolerance/multi_tolerance_per_map.json")["maps"]
    unknown = load("unknown/unknown_missingness_per_map.json")["maps"]
    routes = load("route_tube/replica_route_tube_per_map.json")["maps"]
    one_sided = load("route_tube/one_sided_route_risk_per_map.json")["maps"]
    budget = load("physical_budget/physical_budget_per_map.json")["maps"]
    g0 = load("safer_g0/safer_g0_summary.json")["maps"]
    decision = load("classification/final_decision.json")
    report_text = (ROOT / "REPORT_RETROSPECTIVE_REQUALIFY_EXISTING_GAUSSIAN_MAPS_UNDER_LAYERED_PROTOCOL_V2.md").read_text(encoding="utf-8")

    protocol_path = "reproduction/cross_dataset/gaussian_map_metric_provenance_navigation_usability_calibration_v1/protocol_v2/GAUSSIAN_MAP_LAYERED_EVALUATION_PROTOCOL_V2.md"
    checklist_path = "reproduction/cross_dataset/gaussian_map_metric_provenance_navigation_usability_calibration_v1/protocol_v2/NEW_DATASET_MAP_EVALUATION_ENTRY_CHECKLIST_V2.md"
    check(git_blob_sha(protocol_path) == EXPECTED_PROTOCOL == freeze["observed"]["protocol_v2_sha256"], "protocol_raw_git_blob_sha_exact", checks, failures)
    check(git_blob_sha(checklist_path) == EXPECTED_CHECKLIST == freeze["observed"]["checklist_sha256"], "checklist_raw_git_blob_sha_exact", checks, failures)
    check(freeze["upstream_head"] == EXPECTED_HEAD, "upstream_head_exact", checks, failures)
    check(freeze["pr_68_through_75_mutation_count"] == 0, "legacy_pr_mutation_zero", checks, failures)
    check(all((ROOT / p).is_file() for p in SCRIPTS), "all_required_scripts_present", checks, failures)
    check(len(FIGURES) == 20 and all((ROOT / "figures" / p).is_file() and (ROOT / "figures" / p).stat().st_size > 10_000 for p in FIGURES), "all_20_figures_present", checks, failures)
    check(inventory["fixed_order"] == MAP_ORDER and inventory["map_count"] == 11, "inventory_fixed_order_11", checks, failures)
    check(inventory["accessible_count"] == 6 and inventory["unavailable_count"] == 5, "inventory_6_accessible_5_unavailable", checks, failures)
    initial_by_id = {r["map_id"]: r for r in initial_server_inventory["maps"]}
    final_by_id = {r["map_id"]: r for r in final_server_inventory["maps"]}
    stable_fields = ("available", "status", "gaussian_count", "source_identity", "canonical_identity")
    check(initial_by_id.keys() == final_by_id.keys() and all(all(initial_by_id[m].get(k) == final_by_id[m].get(k) for k in stable_fields) for m in initial_by_id), "server_final_map_identities_unchanged", checks, failures)
    check(all((not r["available"]) or (r["map_sha_before"] == r["map_sha_after"] and r["map_immutable"]) for r in inventory["maps"]), "map_identity_before_after_immutable", checks, failures)
    check(controls["status"] == "PASS_PROTOCOL_V2_CONTROL_DISCRIMINATION" and controls["positive_control_pass"] and not controls["negative_control_false_acceptance"], "control_discrimination_pass", checks, failures)
    check(len(matrix) == 11 and [r["map_id"] for r in matrix] == MAP_ORDER, "classification_11_fixed_order", checks, failures)
    check(all(r["V2_RECONSTRUCTION_AXIS"] in R_VALUES and r["V2_NAVIGATION_AXIS"] in N_VALUES and r["SAFETY_QUERY_COMPATIBLE"] in QUERY_VALUES and r["UNKNOWN_MODEL_STATUS"] in UNKNOWN_VALUES and r["REFERENCE_AUTHORITY"] in REFERENCE_VALUES and r["NATIVE_COMMON_PARITY_STATUS"] in PARITY_VALUES for r in matrix), "classification_enums_only", checks, failures)
    check(len(claims) == 11 and all(r["allowed"] and r["forbidden"] for r in claims), "per_map_claim_boundaries_present", checks, failures)
    check(Counter(r["status"] for r in parity) == Counter({"NOT_EVALUABLE": 5, "SEMANTIC_PARITY_ONLY": 3, "NUMERIC_PARITY_PASS": 2, "NATIVE_ONLY": 1}), "native_common_counts_exact", checks, failures)
    check(sum(r["status"] == "COMPLETE_FIXED_ALPHA_CURVE" for r in risk) == 1, "risk_coverage_complete_one", checks, failures)
    check(sum(r["status"] == "DETERMINISTIC_CONSTRUCTION_CERTIFICATE" for r in multi) == 1, "multi_tolerance_complete_one", checks, failures)
    check(sum(r["UNKNOWN_MODEL_STATUS"] == "UNKNOWN_MODEL_DIAGNOSTIC_ONLY" for r in unknown) == 1, "unknown_diagnostic_complete_one", checks, failures)
    check(sum(r["status"] == "PASS_CERTIFIED_ROUTE_TUBE" for r in routes) == 1, "route_tube_complete_one", checks, failures)
    check(sum(r["status"] == "DETERMINISTIC_ONE_SIDED_RISK_CERTIFICATE" for r in one_sided) == 1, "one_sided_certificate_one", checks, failures)
    check(sum(r["status"] == "PHYSICAL_ERROR_BUDGET_RESOLVED" for r in budget) == 1, "physical_budget_1_resolved_10_unresolved", checks, failures)
    g0_pass = [r for r in g0 if r["status"] == "PASS_SAFETY_QUERY_COMPATIBILITY"]
    check(len(g0_pass) == 6 and sum(r["run_count"] for r in g0_pass) == 18 and all(r["query_count_per_run"] == 256 and r["checks"]["exact_output_repeatability"] and r["checks"]["map_immutable"] for r in g0_pass), "g0_6_maps_18_processes_deterministic", checks, failures)
    check(manifest["counts"]["N3_learned_maps"] == 0 and manifest["counts"]["N2_learned_maps"] == 0, "no_learned_n2_n3", checks, failures)
    check(all(manifest["counts"][key] == 0 for key in ZERO_KEYS), "all_prohibited_execution_counts_zero", checks, failures)
    check(manifest["counts"]["G0_processes"] == 18 and manifest["counts"]["artifact_unavailable"] == 5, "positive_execution_counts_exact", checks, failures)
    check(decision["FINAL_STATUS"] == "NO_EXISTING_LEARNED_GAUSSIAN_MAP_NAVIGATION_QUALIFIED_UNDER_PROTOCOL_V2" and decision["FINAL_DECISION"] == "PROCEED_TO_NEW_DATASET_ENTRY_QUALIFICATION" and decision["Only_next_task"] == "ETH3D_DELIVERY_AREA_PROTOCOL_V2_ENTRY_QUALIFICATION_V1" and not decision["ETH3D_training_authorized"], "case_c_decision_exact", checks, failures)
    check(freeze["global_numeric_gate_decision"] == "NO_UNIVERSAL_NUMERIC_GATE_JUSTIFIED_BY_CURRENT_EVIDENCE", "no_universal_numeric_gate", checks, failures)
    check(manifest["unresolved_critical_evidence"] == [], "unresolved_critical_evidence_empty", checks, failures)
    check(all(f"{i}. " in report_text for i in range(1, 30)), "report_answers_all_29", checks, failures)
    check("legacy result remains valid under legacy contract" in report_text and "does not rewrite history" in report_text, "legacy_preservation_explicit", checks, failures)
    check((ROOT / "eth3d_entry_handoff.json").is_file() and not (ROOT / "bounded_gap_handoff.json").exists(), "case_c_handoff_only", checks, failures)
    requalified = load("requalified_map_identities.json")
    check(requalified["count"] == 0 and requalified["learned_n3_maps"] == [], "no_requalified_learned_identity", checks, failures)
    if (ROOT / "runtime_finalization.json").exists():
        runtime = load("runtime_finalization.json")
        check(runtime["new_disk_bytes"] <= runtime["new_disk_limit_bytes"], "disk_growth_below_120_gib", checks, failures)
        check(runtime["watchdog_status"] == "Running" and runtime["managed_ssh_preserved"], "watchdog_and_managed_ssh_preserved", checks, failures)
        check(runtime["gpu_final"]["task_compute_process_count"] == 0, "gpu_final_no_task_compute", checks, failures)
        report_sha = hashlib.sha256((ROOT / "REPORT_RETROSPECTIVE_REQUALIFY_EXISTING_GAUSSIAN_MAPS_UNDER_LAYERED_PROTOCOL_V2.md").read_bytes()).hexdigest()
        check(runtime["local_report_sha256"] == runtime["server_report_sha256"] == report_sha, "local_server_report_sha_exact", checks, failures)
    else:
        check(False, "runtime_finalization_present", checks, failures)

    result = {
        "status": "PASS_RETROSPECTIVE_REQUALIFICATION_VALIDATION" if not failures else "FAIL_RETROSPECTIVE_REQUALIFICATION_VALIDATION",
        "checks": checks,
        "failure_count": len(failures),
        "failures": failures,
        "unresolved_critical_evidence": [] if not failures else failures,
    }
    (ROOT / "validation_result.json").write_text(json.dumps(result, indent=2, sort_keys=True) + "\n", encoding="utf-8", newline="\n")
    print(result["status"], "checks=", len(checks), "failures=", len(failures))
    if failures:
        raise SystemExit(1)


if __name__ == "__main__":
    main()
