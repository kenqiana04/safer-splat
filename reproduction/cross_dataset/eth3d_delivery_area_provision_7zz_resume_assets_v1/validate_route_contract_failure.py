#!/usr/bin/env python3
"""Validate the fail-closed Case C route-contract closeout."""

import json

from task_config import TASK_ROOT


EXPECTED = "NO_ETH3D_DELIVERY_AREA_REFERENCE_ROUTE_BENCHMARK_CONTRACT"


def load(relative):
    return json.loads((TASK_ROOT / relative).read_text(encoding="utf-8"))


def main() -> None:
    validation = load("validation_result.json")
    decision = load("decision/final_decision.json")
    manifest = load("run_manifest.json")
    failure = load("routes/reference_route_contract_failure.json")
    counters = load("execution_counters.json")
    boundary = load("final_no_execution_boundary.json")
    assertions = {
        "status_consistent": validation["status"] == decision["FINAL_STATUS"] == manifest["FINAL_STATUS"] == EXPECTED,
        "one_failed_gate": validation["failed_gate_count"] == 1 and validation["gates"]["reference_only_routes"] == "FAIL",
        "no_unresolved_evidence": not validation["unresolved_critical_evidence"],
        "valid_candidate_count": failure["valid_reference_path_candidate_count"] >= 30,
        "blocked_quota_failed": failure["blocked_straight_line_candidate_ratio"] < failure["frozen_blocked_straight_line_ratio_minimum"],
        "no_registry": failure["route_registry_frozen"] is False and manifest["route_count"] == 0,
        "contract_unchanged": failure["threshold_or_contract_modified"] is False and validation["scientific_contract_change_count"] == 0,
        "no_training": counters["training_count"] == counters["official_3dgs_run_count"] == 0,
        "no_map_controller": counters["model_or_map_generation_count"] == counters["controller_count"] == 0,
        "no_candidate_map": counters["candidate_map_access_count"] == 0,
        "no_environment": counters["training_environment_create_count"] == counters["training_environment_modify_count"] == 0,
        "no_task_process": boundary["task_owned_running_process_count"] == 0,
        "training_not_authorized": decision["training_authorized"] is False,
        "environment_not_authorized": decision["environment_qualification_authorized"] is False,
        "report_exists": (TASK_ROOT / "REPORT_PROVISION_TASK_LOCAL_7ZZ_AND_RESUME_ETH3D_ASSET_CONTRACT_AUDIT_V1.md").is_file(),
        "required_figures": len(list((TASK_ROOT / "figures").glob("*.png"))) >= 21,
    }
    result = {"status": "PASS" if all(assertions.values()) else "FAIL",
              "assertions": assertions, "assertion_count": len(assertions),
              "failure_count": sum(not value for value in assertions.values())}
    (TASK_ROOT / "final_validator_result.json").write_text(
        json.dumps(result, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    if result["status"] != "PASS":
        raise RuntimeError(result)
    print("PASS_ROUTE_CONTRACT_FAILURE_VALIDATOR", len(assertions))


if __name__ == "__main__":
    main()
