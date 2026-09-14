#!/usr/bin/env python3
"""CPU-only validator for the frozen Active Runtime Pilot V3 protocol."""

from __future__ import annotations

import argparse
import hashlib
import json
import subprocess
import sys
from pathlib import Path
from typing import Any


UPSTREAM = "aeab949629d314e930fda6c65bcc68c724fbf6c6"
TASK_REL = Path("reproduction/pilot/active_runtime_pilot_v3")
TRIALS = [5, 15, 25, 35, 45, 55, 65, 75, 85, 95]
ENV = "/disk1/zlab/conda_envs/safer_splat_official"
MAP_ID = "c9eade9ca89b741768a0ca33b3a755b2656402864f121aefdceaed4b0174f7c8"
ZERO_COUNTERS = {
    "gpu_pilot": 0,
    "official100": 0,
    "scientific_oracle": 0,
    "formal": 0,
    "reference_arm": 0,
}


def load_json(path: Path) -> dict[str, Any]:
    with path.open("r", encoding="utf-8") as handle:
        return json.load(handle)


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def git(repo: Path, *args: str) -> str:
    return subprocess.check_output(
        ["git", "-C", str(repo), *args], text=True, encoding="utf-8"
    ).rstrip()


def check(condition: bool, name: str, checks: dict[str, bool]) -> None:
    checks[name] = bool(condition)


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--repo-root", default=".")
    parser.add_argument("--phase", choices=["protocol"], default="protocol")
    args = parser.parse_args()

    repo = Path(args.repo_root).resolve()
    task = repo / TASK_REL
    protocol = load_json(task / "PILOT_V3_PROTOCOL.json")
    lock = load_json(task / "PILOT_V3_INPUT_LOCK.json")
    decisions = load_json(task / "PILOT_V3_DECISION_RULES.json")
    exposure = load_json(task / "PILOT_V3_DEVELOPMENT_EXPOSURE.json")
    evidence = load_json(task / "PILOT_V3_REQUIRED_EVIDENCE_SCHEMA.json")
    checks: dict[str, bool] = {}

    ancestor_ok = subprocess.run(
        ["git", "-C", str(repo), "merge-base", "--is-ancestor", UPSTREAM, "HEAD"],
        check=False,
    ).returncode == 0
    check(ancestor_ok, "exact_upstream_in_ancestry", checks)
    check(protocol["upstream"]["commit"] == UPSTREAM, "protocol_upstream_exact", checks)
    check(lock["upstream"]["commit"] == UPSTREAM, "input_lock_upstream_exact", checks)

    check(protocol["trial_ids"] == TRIALS, "trial_ids_exact", checks)
    check(protocol["trial_order"] == TRIALS, "trial_order_exact", checks)
    check(protocol["development_exposed_trial_ids"] == TRIALS, "development_trials_exact", checks)
    check(protocol["execution"]["maximum_completed_cycles_per_trial"] == 500, "max_cycles_500", checks)
    check(protocol["execution"]["seed"] == 0, "seed_zero", checks)
    check(protocol["execution"]["serial_execution"] is True, "serial_execution", checks)
    check(protocol["execution"]["separate_process_per_trial"] is True, "separate_process", checks)
    check(protocol["execution"]["gpu_id"] == 1, "gpu_one_reserved", checks)
    check(protocol["execution"]["conda_environment"] == ENV, "environment_exact", checks)

    check(protocol["map"]["identity"] == MAP_ID, "map_identity_exact", checks)
    map_hashes = {item["relative_path"]: item["sha256"] for item in protocol["map"]["artifacts"]}
    check(map_hashes == {
        "config.yml": "cd6ea45ad01553f0ce1531ad08cfaf8359e95041b39c77291d94e75f2d2f2f8e",
        "dataparser_transforms.json": "92a1af2f195be3b32e0422418aff40cbd426c1cf9d8f7d5da87629519f5a0f8e",
        "nerfstudio_models/step-000029999.ckpt": "ac14f5ced354c93f26cf92404540712eff65bd02554d9e9ed0332508e290382d",
    }, "map_artifact_hashes_exact", checks)

    geometry = protocol["v3_runtime_geometry"]
    check(geometry["coordinate_unit"] == "q", "coordinate_unit_q", checks)
    check(geometry["r_body_q"] == 0.015, "r_body_exact", checks)
    check(geometry["m_hard_q"] == 0.0, "hard_reserve_zero", checks)
    check(geometry["r_hard_q"] == 0.015, "r_hard_exact", checks)
    check(geometry["rho_seg_q"] == 0.0, "rho_seg_zero", checks)
    historical = protocol["historical_diagnostic_shell"]
    check(historical["radius_q"] == 0.025, "historical_shell_exact", checks)
    authority_keys = [key for key in historical if key.endswith("authority")]
    check(len(authority_keys) == 8 and all(historical[key] is False for key in authority_keys), "historical_authority_all_false", checks)

    switches = protocol["execution_switches"]
    check(all(value is False for value in switches.values()), "all_execution_switches_false", checks)
    check(protocol["execution_counts_at_freeze"] == ZERO_COUNTERS, "all_execution_counts_zero", checks)
    check(protocol["scientific_role"]["parameter_selection_authorized"] is False, "no_parameter_selection", checks)
    check(protocol["scientific_role"]["radius_selection_authorized"] is False, "no_radius_selection", checks)
    check(protocol["scientific_role"]["policy_selection_authorized"] is False, "no_policy_selection", checks)
    check(protocol["scientific_role"]["formal_claim_authorized"] is False, "no_formal_claim", checks)

    check(exposure["development_exposed_trial_ids"] == TRIALS, "exposure_manifest_exact", checks)
    check(exposure["new_formal_primary_trial_exposure_count"] == 0, "no_new_formal_exposure", checks)
    check(exposure["eligible_for_new_v3_primary_confirmatory_cohort"] is False, "not_primary_confirmatory", checks)
    check(decisions["frozen_before_any_pilot_outcome"] is True, "decisions_frozen_before_outcome", checks)
    check(len(decisions["hard_block_conditions"]) >= 12, "hard_blocks_complete", checks)
    check(decisions["pilot_final_decision_generated_by_this_freeze_task"] is False, "no_pilot_decision_generated", checks)

    trial_required = set(evidence["trial_required_fields"])
    aggregate_required = set(evidence["aggregate_required_fields"])
    required_trial = {
        "completed_cycles", "plant_commits", "primary_count", "alternative_count",
        "backup_count", "terminal_count", "boundary_count", "l1_pass", "l1_fail",
        "l1_unknown", "c0_pass", "c0_fail", "c0_unknown", "l2_pass", "l2_fail",
        "l2_unknown", "l3_pass", "l3_fail", "l3_unknown", "qp_failures",
        "deadline_open", "deadline_warning", "deadline_expired",
        "selected_executed_mismatch", "nonfinite", "actuator_violation",
        "evidence_incomplete", "recovery_required", "finalization_status",
        "termination_type", "runtime_hard_radius_observed_q",
        "historical_diagnostic_shell_runtime_authority_observed",
        "historical_diagnostic_intrusion_count",
        "action_rejected_only_by_historical_0p025_shell_count",
    }
    check(required_trial.issubset(trial_required), "trial_evidence_fields_complete", checks)
    check((required_trial - {"finalization_status", "termination_type", "runtime_hard_radius_observed_q", "historical_diagnostic_shell_runtime_authority_observed"}).issubset(aggregate_required), "aggregate_evidence_fields_complete", checks)

    upstream_hashes = lock["upstream_artifact_sha256"]
    check(all(sha256(repo / rel) == expected for rel, expected in upstream_hashes.items()), "upstream_artifact_hashes_exact", checks)
    check(sha256(task / "PILOT_V3_PROTOCOL.json") == lock["protocol_sha256"], "protocol_hash_exact", checks)
    for key, filename in {
        "decision_rules_sha256": "PILOT_V3_DECISION_RULES.json",
        "development_exposure_sha256": "PILOT_V3_DEVELOPMENT_EXPOSURE.json",
        "required_evidence_schema_sha256": "PILOT_V3_REQUIRED_EVIDENCE_SCHEMA.json",
    }.items():
        check(sha256(task / filename) == lock[key], key.replace("_sha256", "_hash_exact"), checks)

    porcelain = git(repo, "status", "--porcelain=v1", "--untracked-files=all")
    changed_paths = []
    for line in porcelain.splitlines():
        if not line:
            continue
        path = line[3:].replace("\\", "/")
        if " -> " in path:
            path = path.split(" -> ", 1)[1]
        changed_paths.append(path)
    task_prefix = TASK_REL.as_posix() + "/"
    outside = sorted(path for path in changed_paths if not path.startswith(task_prefix))
    check(not outside, "protected_runtime_diff_zero", checks)
    forbidden_names = {"run_active_runtime_pilot_v3.py", "PILOT_V3_TRIAL_RESULTS.csv", "raw"}
    check(not any((task / name).exists() for name in forbidden_names), "no_execution_artifacts_or_runner", checks)

    failed = sorted(name for name, passed in checks.items() if not passed)
    result = {
        "schema": "ACTIVE_RUNTIME_PILOT_V3_PROTOCOL_VALIDATION_RESULT_V1",
        "phase": args.phase,
        "status": "PASS_ACTIVE_RUNTIME_PILOT_V3_PROTOCOL_VALIDATION" if not failed else "FAIL_ACTIVE_RUNTIME_PILOT_V3_PROTOCOL_VALIDATION",
        "checks": checks,
        "failed_checks": failed,
        "outside_task_changes": outside,
        "protocol_sha256": lock["protocol_sha256"],
        "execution_counts": ZERO_COUNTERS,
    }
    with (task / "PILOT_V3_PROTOCOL_VALIDATION.json").open(
        "w", encoding="utf-8", newline="\n"
    ) as handle:
        handle.write(json.dumps(result, indent=2, sort_keys=True) + "\n")
    print(result["status"])
    print("GPU_PILOT_EXECUTION_COUNT=0")
    print("OFFICIAL100_EXECUTION_COUNT=0")
    print("ORACLE_EXECUTION_COUNT=0")
    print("FORMAL_EXECUTION_COUNT=0")
    print("REFERENCE_ARM_EXECUTION_COUNT=0")
    if failed:
        print("FAILED_CHECKS=" + ",".join(failed), file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
