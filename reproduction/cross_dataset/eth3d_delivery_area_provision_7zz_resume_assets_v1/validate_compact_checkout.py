#!/usr/bin/env python3
"""Validate the copied compact Case C evidence without server payload access."""

from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path


ROOT = Path(__file__).resolve().parent
EXPECTED = "NO_ETH3D_DELIVERY_AREA_REFERENCE_ROUTE_BENCHMARK_CONTRACT"


def load(relative):
    return json.loads((ROOT / relative).read_text(encoding="utf-8"))


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def assertions(include_manifest):
    validation = load("validation_result.json")
    decision = load("decision/final_decision.json")
    manifest = load("run_manifest.json")
    failure = load("routes/reference_route_contract_failure.json")
    counters = load("execution_counters.json")
    boundary = load("final_no_execution_boundary.json")
    checks = {
        "case_c_status_consistent": validation["status"] == decision["FINAL_STATUS"] == manifest["FINAL_STATUS"] == EXPECTED,
        "exactly_one_failed_gate": validation["failed_gate_count"] == 1 and validation["gates"]["reference_only_routes"] == "FAIL",
        "route_candidate_minimum_met": failure["valid_reference_path_candidate_count"] >= 30,
        "blocked_quota_failed": failure["blocked_straight_line_candidate_ratio"] < 0.5,
        "no_route_registry_frozen": failure["route_registry_frozen"] is False and manifest["route_count"] == 0,
        "free_3d_implementation": failure["candidate_voxel_dimensionality"] == "THREE_DIMENSIONAL_FREE_3D_ROBOT_CONTRACT",
        "frozen_cost_implemented": failure["edge_cost_contract"] == "edge_length_plus_inverse_reference_residual_budget",
        "no_contract_change": failure["threshold_or_contract_modified"] is False and validation["scientific_contract_change_count"] == 0,
        "no_training_map_controller": counters["training_count"] == counters["model_or_map_generation_count"] == counters["controller_count"] == 0,
        "no_environment_change": counters["training_environment_create_count"] == counters["training_environment_modify_count"] == 0,
        "no_candidate_map_access": counters["candidate_map_access_count"] == 0,
        "no_task_process": boundary["task_owned_running_process_count"] == 0,
        "training_not_authorized": decision["training_authorized"] is False,
        "environment_not_authorized": decision["environment_qualification_authorized"] is False,
        "figure_count": len(list((ROOT / "figures").glob("*.png"))) == 23,
        "report_exists": (ROOT / "REPORT_PROVISION_TASK_LOCAL_7ZZ_AND_RESUME_ETH3D_ASSET_CONTRACT_AUDIT_V1.md").is_file(),
        "no_full_route_arrays": not any((ROOT / "routes" / name).exists() for name in (
            "reference_prm_graph_full.json", "reference_prm_nodes_pre_edges.json",
            "reference_route_candidates_full.json", "reference_route_registry_full.json")),
    }
    if include_manifest:
        artifact_manifest = load("compact_artifact_manifest.json")
        rows = artifact_manifest["artifacts"]
        checks["artifact_manifest_status"] = artifact_manifest["status"] == "PASS_COMPACT_TRACKED_ARTIFACT_SET"
        checks["artifact_manifest_count"] = artifact_manifest["file_count"] == len(rows)
        checks["artifact_manifest_hashes"] = all(
            (ROOT / row["path"]).is_file() and
            (ROOT / row["path"]).stat().st_size == row["bytes"] and
            sha(ROOT / row["path"]) == row["sha256"]
            for row in rows)
    return checks


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--write", action="store_true")
    parser.add_argument("--verify-manifest", action="store_true")
    args = parser.parse_args()
    checks = assertions(args.verify_manifest)
    result = {"status": "PASS" if all(checks.values()) else "FAIL",
              "assertion_count": len(checks), "failure_count": sum(not value for value in checks.values()),
              "assertions": checks}
    if args.write:
        (ROOT / "compact_checkout_validation.json").write_text(
            json.dumps(result, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    if result["status"] != "PASS":
        raise RuntimeError(result)
    print("PASS_COMPACT_CHECKOUT_VALIDATION", len(checks))


if __name__ == "__main__":
    main()
