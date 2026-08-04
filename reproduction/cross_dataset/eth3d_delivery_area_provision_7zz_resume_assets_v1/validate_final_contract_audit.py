#!/usr/bin/env python3
"""Fail-closed final validator for the compact ETH3D contract evidence."""

from __future__ import annotations

import json
from pathlib import Path

from task_config import TASK_ROOT


EXPECTED = "PASS_ETH3D_DELIVERY_AREA_ASSET_SPLIT_REFERENCE_UNKNOWN_ROUTE_CONTRACT"


def load(relative):
    return json.loads((TASK_ROOT / relative).read_text(encoding="utf-8"))


def main() -> None:
    validation = load("validation_result.json")
    manifest = load("run_manifest.json")
    decision = load("decision/final_decision.json")
    handoff = load("downstream_handoff.json")
    counters = load("execution_counters.json")
    routes = load("routes/reference_route_registry_identity.json")
    boundary = load("final_no_execution_boundary.json")
    assertions = {
        "final_status": validation["status"] == manifest["FINAL_STATUS"] == decision["FINAL_STATUS"] == EXPECTED,
        "all_gates": set(validation["gates"].values()) == {"PASS"},
        "no_failed_gate": validation["failed_gate_count"] == 0,
        "no_unresolved_critical_evidence": not validation["unresolved_critical_evidence"],
        "route_count": routes["route_count"] >= 30,
        "blocked_route_quota": routes["blocked_straight_line_ratio"] >= 0.5,
        "positive_route_budget": routes["minimum_B_map_available_m"] > 0,
        "route_reproducibility": load("routes/fresh_process_route_reproducibility.json")["process_count"] == 3,
        "split_reproducibility": load("split/fresh_process_split_reproducibility.json")["process_count"] == 3,
        "train_reproducibility": load("train_model/train_only_colmap_identity.json")["fresh_build_count"] == 3,
        "train_reference_isolation": load("train_model/train_eval_isolation_audit.json")["train_reference_access_count"] == 0,
        "no_execution_boundary": boundary["status"] == "PASS_NO_EXECUTION_BOUNDARY",
        "no_task_process": boundary["task_owned_running_process_count"] == 0,
        "no_training": counters["training_count"] == counters["official_3dgs_run_count"] == 0,
        "no_map_controller": counters["model_or_map_generation_count"] == counters["controller_count"] == 0,
        "no_candidate_map_access": counters["candidate_map_access_count"] == 0,
        "no_environment_change": counters["training_environment_create_count"] == counters["training_environment_modify_count"] == 0,
        "no_scientific_contract_change": validation["scientific_contract_change_count"] == 0,
        "training_not_authorized": validation["training_authorized"] is handoff["training_authorized"] is False,
        "report_exists": (TASK_ROOT / "REPORT_PROVISION_TASK_LOCAL_7ZZ_AND_RESUME_ETH3D_ASSET_CONTRACT_AUDIT_V1.md").is_file(),
        "handoff_exists": (TASK_ROOT / "FREEZE_ETH3D_DELIVERY_AREA_OFFICIAL_3DGS_ENVIRONMENT_INPUT_HANDOFF_V1.md").is_file(),
        "figure_count": len(list((TASK_ROOT / "figures").glob("*.png"))) == 24,
    }
    result = {"status": "PASS" if all(assertions.values()) else "FAIL",
              "assertions": assertions, "assertion_count": len(assertions),
              "failure_count": sum(not value for value in assertions.values())}
    (TASK_ROOT / "final_validator_result.json").write_text(
        json.dumps(result, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    if result["status"] != "PASS":
        raise RuntimeError(result)
    print("PASS_FINAL_VALIDATOR", len(assertions))


if __name__ == "__main__":
    main()
