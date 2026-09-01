#!/usr/bin/env python3
"""Validate the compact, read-only primary reachability diagnosis."""

from __future__ import annotations

import argparse
import csv
import hashlib
import json
import subprocess
from pathlib import Path
from typing import Any


UPSTREAM_HEAD = "80a7e691937f9e45b68e1c606befa03ff0a12553"
TASK_PREFIX = "reproduction/diagnosis/l2_h1_primary_reachability_v1/"

EXPECTED_GATES = [
    ("G1", "data_role=FORMAL_PROSPECTIVE_SHADOW_COHORT_V1"),
    ("G2", "logging_qc_complete=true"),
    ("G3", "selected_candidate_role=SELECTED_EXECUTED_CONTROL"),
    ("G4", "selected_candidate_committed=true"),
    ("G5", "l1_observation_source=SHADOW_RECOMPUTED_FROZEN_CERTIFIER"),
    ("G6", "l1_status=PASS"),
    ("G7", "l2_reached=true"),
    ("G8", "l2_status in {PASS,FAIL,UNKNOWN}"),
    ("G9", "map_authority_valid=true"),
    ("G10", "payload_join_identity_valid=true"),
]


def load_json(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def find_repo_root(start: Path) -> Path:
    for candidate in (start, *start.parents):
        if (candidate / ".git").exists():
            return candidate
    raise RuntimeError("repository root not found")


def git_blob_sha256(repo: Path, ref: str, path: str) -> str:
    blob = subprocess.check_output(["git", "cat-file", "blob", f"{ref}:{path}"], cwd=repo)
    return hashlib.sha256(blob).hexdigest()


def git_output(repo: Path, *args: str) -> str:
    return subprocess.check_output(["git", *args], cwd=repo, text=True, encoding="utf-8").strip()


def read_csv(path: Path) -> list[dict[str, str]]:
    with path.open("r", encoding="utf-8", newline="") as handle:
        return list(csv.DictReader(handle))


def validate(task_dir: Path) -> dict[str, Any]:
    task_dir = task_dir.resolve()
    repo = find_repo_root(task_dir)
    lock = load_json(task_dir / "DIAGNOSIS_INPUT_LOCK.json")
    funnel = load_json(task_dir / "reachability_funnel.json")
    data_only = load_json(task_dir / "DATA_ONLY_DIAGNOSIS.json")
    root = load_json(task_dir / "root_cause_diagnosis.json")
    recovery = load_json(task_dir / "STREAMING_PACKAGING_RECOVERY_RECORD.json")
    gate_rows = read_csv(task_dir / "gate_failure_counts.csv")
    l1_rows = read_csv(task_dir / "l1_status_distribution.csv")
    l2_rows = read_csv(task_dir / "l2_reachability_distribution.csv")

    checks: dict[str, bool] = {}
    checks["upstream_identity_exact"] = (
        lock["upstream_PR102_head"] == UPSTREAM_HEAD
        and lock["upstream_PR102_branch"] == "analyze-l2-h1-prospective-shadow-cohort-v1"
        and lock["upstream_PR102_state"] == "OPEN_DRAFT"
        and subprocess.run(["git", "cat-file", "-e", f"{UPSTREAM_HEAD}^{{commit}}"], cwd=repo).returncode == 0
    )
    checks["input_git_blob_identities_exact"] = all(
        git_blob_sha256(repo, UPSTREAM_HEAD, path) == expected
        for path, expected in lock["input_artifact_git_blob_sha256"].items()
    )
    checks["frozen_identity_fields_exact"] = (
        lock["protocol_sha"] == "e8ea8f3fda15ab81664829ea6f71fcb37f772ad613c13f61007856c16117791a"
        and lock["collection_lock_sha"] == "c30adc48099e8d7b90c980d84389cc1fa693cc1f87d3fc519089efb7cb81b756"
        and lock["analysis_execution_lock_sha"] == "08cecef117031f599167ca944ba1ac9ac78da94a908a314ecf750729073e6d59"
        and lock["post_reveal_evidence_lock_sha"] == "a25172a98838d1e132ffc0f0a178029ead0f67dcf44b3ec634eb331c2113d1e4"
    )
    checks["canonical_identity_and_counts"] = (
        lock["canonical_analysis_table"]["sha256"]
        == "8a0fd056f5cc1a598444e8b3c1dd1af494d302f1bb71df7bdb6e0c57547fc55c"
        and funnel["row_count"] == lock["canonical_analysis_table"]["row_count"] == 14122
        and funnel["formal_trial_count"] == lock["formal_trial_count"] == 100
    )

    protocol_path = "reproduction/protocol/l2_h1_prospective_shadow_cohort_v1/formal_analysis_contract.json"
    protocol = json.loads(subprocess.check_output(["git", "cat-file", "blob", f"{UPSTREAM_HEAD}:{protocol_path}"], cwd=repo))
    checks["frozen_gate_contract_exact"] = protocol["primary_eligibility_all"] == [condition for _, condition in EXPECTED_GATES]
    checks["gate_csv_exact"] = (
        [(row["gate_id"], row["frozen_condition"]) for row in gate_rows] == EXPECTED_GATES
        and [row["gate_id"] for row in gate_rows] == [f"G{i}" for i in range(1, 11)]
    )
    checks["first_failure_algebra"] = (
        sum(int(row["first_failing_count"]) for row in gate_rows) + funnel["N_primary"] == funnel["row_count"] == 14122
    )
    checks["l1_distribution_complete"] = sum(int(row["count"]) for row in l1_rows) == 14122
    checks["l2_reach_distribution_complete"] = sum(int(row["count"]) for row in l2_rows) == 14122
    checks["record_reached_typed_separated"] = (
        funnel["N_formal_result_records"] == 14122
        and funnel["l2_reach"]["true"] == 0
        and funnel["N_l2_status_typed"] == 0
        and funnel["result_record_is_not_equivalent_to_l2_evaluation"] is True
    )
    checks["root_cause_supported"] = (
        root["root_cause_class"] == "D1_L1_ZERO_PASS_SUPPORT"
        and root["subcause"] == "UPSTREAM_L0_BLOCKED_BEFORE_L1_CERTIFIER_EXECUTION"
        and funnel["l1_status"] == {"NOT_REACHED": 14122}
        and data_only["earliest_universal_blocking_gate"] == "G6"
        and data_only["earliest_universal_blocking_gate_count"] == 14122
    )
    changed = [line for line in git_output(repo, "diff", "--name-only", UPSTREAM_HEAD).splitlines() if line]
    status_paths = []
    for line in git_output(repo, "status", "--porcelain", "--untracked-files=all").splitlines():
        if line:
            status_paths.append(line[3:].replace("\\", "/"))
    checks["task_local_changes_only"] = all(path.startswith(TASK_PREFIX) for path in (*changed, *status_paths))
    checks["no_scientific_runtime_mutation"] = checks["input_git_blob_identities_exact"] and checks["task_local_changes_only"]
    checks["no_new_experiment"] = root["new_experiment_count"] == 0 and recovery["canonical_streaming_scan_count"] == 1
    checks["no_collision_progress_efficacy"] = root["collision_progress_efficacy_analysis"] is False
    checks["raw_logs_not_committed"] = not any(path.suffix in {".jsonl", ".log"} for path in task_dir.rglob("*"))
    checks["scientific_result_not_reinterpreted"] = root["scientific_result_reinterpretation"] is False
    passed = all(checks.values())
    return {
        "checks": checks,
        "failed_checks": [key for key, value in checks.items() if not value],
        "pass": passed,
        "schema_version": "L2_H1_PRIMARY_REACHABILITY_DIAGNOSIS_VALIDATION_RESULT_V1",
        "validator": "PASS_L2_H1_PRIMARY_REACHABILITY_DIAGNOSIS_V1_VALIDATION" if passed else "FAIL_L2_H1_PRIMARY_REACHABILITY_DIAGNOSIS_V1_VALIDATION",
    }


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--task-dir", type=Path, default=Path(__file__).resolve().parent)
    parser.add_argument("--output", type=Path, default=Path(__file__).resolve().parent / "validation_result.json")
    args = parser.parse_args()
    result = validate(args.task_dir)
    with args.output.open("w", encoding="utf-8", newline="\n") as handle:
        handle.write(json.dumps(result, indent=2, sort_keys=True) + "\n")
    print(json.dumps({"failed_checks": result["failed_checks"], "validator": result["validator"]}, sort_keys=True))
    return 0 if result["pass"] else 2


if __name__ == "__main__":
    raise SystemExit(main())
