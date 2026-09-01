#!/usr/bin/env python3
"""Validate only the frozen Case-C bootstrap terminal path and evidence immutability."""

from __future__ import annotations

import argparse
import hashlib
import json
import math
from pathlib import Path
from typing import Any


class ErratumValidationError(RuntimeError):
    pass


def load_json(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def file_sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def is_finite_number(value: Any) -> bool:
    return isinstance(value, (int, float)) and not isinstance(value, bool) and math.isfinite(value)


def is_not_estimable_value(value: Any) -> bool:
    return value is None or value == "NOT_ESTIMABLE"


def validate_frozen_contract(contract: dict[str, Any]) -> None:
    bootstrap = contract["cluster_bootstrap"]
    expected = {
        "valid_replicates": 10000,
        "maximum_total_draws": 100000,
        "zero_denominator_replicate": "DISCARD_AND_REDRAW",
        "insufficient_valid_replicates": "BOOTSTRAP_NOT_ESTIMABLE",
        "cluster_unit": "formal_trial",
        "cluster_count": 100,
        "clusters_per_replicate": 100,
        "resampling": "WITH_REPLACEMENT",
        "rng_seed": 20260831,
        "step_iid_assumption": False,
        "p_value_or_significance_test": False,
    }
    mismatches = {key: (bootstrap.get(key), value) for key, value in expected.items() if bootstrap.get(key) != value}
    if mismatches:
        raise ErratumValidationError(f"frozen bootstrap contract mismatch: {mismatches}")


def evaluate_bootstrap_terminal(
    contract: dict[str, Any], bootstrap: dict[str, Any], primary: dict[str, Any]
) -> str:
    validate_frozen_contract(contract)
    frozen = contract["cluster_bootstrap"]
    valid = bootstrap["bootstrap_valid_replicates"]
    total = bootstrap["bootstrap_total_draws"]
    zero = bootstrap["bootstrap_zero_denominator_draws"]

    if not all(isinstance(value, int) and not isinstance(value, bool) and value >= 0 for value in (valid, total, zero)):
        raise ErratumValidationError("bootstrap counts must be non-negative integers")
    if valid + zero != total:
        raise ErratumValidationError("valid plus zero-denominator draws must equal total draws")

    if valid == frozen["valid_replicates"]:
        if total > frozen["maximum_total_draws"]:
            raise ErratumValidationError("estimable path exceeds maximum draws")
        if not is_finite_number(bootstrap.get("bootstrap_ci_low")) or not is_finite_number(
            bootstrap.get("bootstrap_ci_high")
        ):
            raise ErratumValidationError("estimable path requires finite CI")
        return "PATH_A_ESTIMABLE"

    if valid < frozen["valid_replicates"]:
        if total != frozen["maximum_total_draws"]:
            raise ErratumValidationError("not-estimable path is only legal at maximum total draws")
        if bootstrap.get("status") != frozen["insufficient_valid_replicates"]:
            raise ErratumValidationError("not-estimable path has the wrong status")
        if not all(
            is_not_estimable_value(bootstrap.get(key))
            for key in ("bootstrap_point_estimate_check", "bootstrap_ci_low", "bootstrap_ci_high")
        ):
            raise ErratumValidationError("not-estimable path must not contain point estimate or CI")
        return "PATH_B_NOT_ESTIMABLE"

    raise ErratumValidationError("valid replicate count exceeds the frozen target")


def find_repo_root(start: Path) -> Path:
    for candidate in (start, *start.parents):
        if (candidate / ".git").exists():
            return candidate
    raise ErratumValidationError("repository root not found")


def validate_original_failure(original: dict[str, Any]) -> None:
    checks = original.get("checks", {})
    failed = sorted(key for key, value in checks.items() if value is not True)
    if failed != ["bootstrap_contract_exact"]:
        raise ErratumValidationError(f"original validation failure set changed: {failed}")
    if sum(value is True for value in checks.values()) != 21 or original.get("passed_check_count") != 21:
        raise ErratumValidationError("original validation must preserve exactly 21 passing checks")
    if original.get("failed_checks") != ["bootstrap_contract_exact"] or original.get("pass") is not False:
        raise ErratumValidationError("original failed validation history is not preserved")


def verify_locked_files(task_dir: Path, evidence: dict[str, Any]) -> list[dict[str, str]]:
    changes: list[dict[str, str]] = []
    for artifact in evidence["blocked_scientific_artifacts"]:
        path = task_dir / artifact["path"]
        actual = file_sha256(path)
        if actual != artifact["sha256"]:
            changes.append({"path": artifact["path"], "expected": artifact["sha256"], "actual": actual})
    original_validator = evidence["original_validator"]
    validator_path = task_dir / original_validator["path"]
    actual_validator = file_sha256(validator_path)
    if actual_validator != original_validator["sha256"]:
        changes.append(
            {"path": original_validator["path"], "expected": original_validator["sha256"], "actual": actual_validator}
        )
    return changes


def validate_task(task_dir: Path) -> dict[str, Any]:
    task_dir = task_dir.resolve()
    repo_root = find_repo_root(task_dir)
    evidence = load_json(task_dir / "POST_REVEAL_EVIDENCE_LOCK.json")
    original_validation = load_json(task_dir / "validation_result.json")
    primary = load_json(task_dir / "primary_result.json")
    bootstrap = load_json(task_dir / "primary_bootstrap.json")
    decision = load_json(task_dir / "FINAL_CASE_DECISION.json")
    protocol_path = repo_root / "reproduction/protocol/l2_h1_prospective_shadow_cohort_v1/formal_analysis_contract.json"
    collection_path = repo_root / "reproduction/collection/l2_h1_prospective_shadow_cohort_v1/FORMAL_COLLECTION_LOCK.json"
    contract = load_json(protocol_path)

    checks: dict[str, bool] = {}
    checks["protocol_file_identity"] = file_sha256(protocol_path) == evidence["formal_analysis_contract_file_sha256"]
    checks["collection_lock_file_identity"] = file_sha256(collection_path) == evidence["collection_lock_file_sha256"]
    checks["original_validator_identity"] = (
        file_sha256(task_dir / evidence["original_validator"]["path"]) == evidence["original_validator"]["sha256"]
    )
    checks["original_validation_result_identity"] = (
        file_sha256(task_dir / "validation_result.json") == evidence["original_validation_result_sha256"]
    )
    validate_original_failure(original_validation)
    checks["original_failure_precisely_limited"] = True
    validate_frozen_contract(contract)
    checks["frozen_case_c_bootstrap_contract_exact"] = True

    accepted_path = evaluate_bootstrap_terminal(contract, bootstrap, primary)
    checks["bootstrap_terminal_path_accepted"] = accepted_path == "PATH_B_NOT_ESTIMABLE"
    checks["case_c_counts_exact"] = (
        primary["N_intended_control_steps"] == 14122
        and primary["N_primary"] == 0
        and primary["N_L2_PASS"] == 0
        and primary["N_L2_FAIL"] == 0
        and primary["N_L2_UNKNOWN"] == 0
        and bootstrap["bootstrap_valid_replicates"] == 0
        and bootstrap["bootstrap_total_draws"] == 100000
        and bootstrap["bootstrap_zero_denominator_draws"] == 100000
        and bootstrap["status"] == "BOOTSTRAP_NOT_ESTIMABLE"
        and is_not_estimable_value(bootstrap.get("bootstrap_point_estimate_check"))
        and is_not_estimable_value(bootstrap.get("bootstrap_ci_low"))
        and is_not_estimable_value(bootstrap.get("bootstrap_ci_high"))
    )
    checks["case_c_decision_exact"] = decision["case"] == "CASE_C_PRIMARY_NOT_ESTIMABLE"

    changes = verify_locked_files(task_dir, evidence)
    checks["scientific_artifact_hash_changes_zero"] = len(changes) == 0
    passed = all(checks.values())
    return {
        "accepted_bootstrap_path": accepted_path,
        "checks": checks,
        "erratum_status": "PASS_CASE_C_AWARE_VALIDATOR_ERRATUM_V1" if passed else "FAIL_CASE_C_AWARE_VALIDATOR_ERRATUM_V1",
        "final_decision": "FREEZE_CASE_C_EVIDENCE_AND_AUTHORIZE_PRIMARY_REACHABILITY_DIAGNOSIS",
        "final_status": "PASS_L2_H1_CASE_C_ANALYSIS_ERRATUM_AND_EVIDENCE_FREEZE_V1" if passed else "FAIL_L2_H1_CASE_C_ANALYSIS_ERRATUM_V1",
        "only_next_task": "DIAGNOSE_L2_H1_PRIMARY_REACHABILITY_V1",
        "original_failed_check": "bootstrap_contract_exact",
        "original_passing_check_count": 21,
        "pass": passed,
        "schema_version": "L2_H1_CASE_C_AWARE_VALIDATOR_ERRATUM_RESULT_V1",
        "scientific_artifact_hash_changes": changes,
        "scientific_artifact_hash_changes_count": len(changes),
        "scientific_case": "CASE_C_PRIMARY_NOT_ESTIMABLE",
        "scientific_decision": "PRIMARY_OPERATIONAL_OPPORTUNITY_NOT_ESTIMABLE",
        "scientific_result_unchanged": len(changes) == 0,
    }


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--task-dir", type=Path, default=Path(__file__).resolve().parents[1])
    parser.add_argument("--output", type=Path, default=Path(__file__).resolve().parent / "erratum_validation_result.json")
    args = parser.parse_args()
    try:
        result = validate_task(args.task_dir)
    except (ErratumValidationError, KeyError, OSError, ValueError, json.JSONDecodeError) as exc:
        result = {
            "erratum_status": "FAIL_CASE_C_AWARE_VALIDATOR_ERRATUM_V1",
            "error": str(exc),
            "pass": False,
            "schema_version": "L2_H1_CASE_C_AWARE_VALIDATOR_ERRATUM_RESULT_V1",
        }
    args.output.write_text(json.dumps(result, indent=2, sort_keys=True) + "\n", encoding="utf-8", newline="\n")
    print(json.dumps(result, sort_keys=True))
    return 0 if result.get("pass") else 2


if __name__ == "__main__":
    raise SystemExit(main())
