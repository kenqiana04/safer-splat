#!/usr/bin/env python3
"""CPU-only validator for the frozen Active Runtime V3 paired protocol."""

from __future__ import annotations

import argparse
import csv
import hashlib
import json
import subprocess
import sys
from pathlib import Path


UPSTREAM = "974b1957f3da55964814650ec5db6e98c84fc12e"
BRANCH = "freeze-active-runtime-v3-paired-validation-protocol-v1"
FORMAL_COMMIT = "ea2dfad6ad1e4b4cb4040e48a70084f7dcbfeab8"
TASK_REL = "reproduction/validation/active_runtime_paired_validation_v3/"
PRIMARY = [0,1,2,3,4,6,7,8,9,11,12,13,14,16,17,18,19,20,21,22,23,24,26,27,28,29,31,32,33,34,36,37,38,39,40,41,42,43,44,46,47,48,49,51,52,53,54,56,57,58,59,60,61,62,63,64,66,67,68,69,71,72,73,74,76,77,78,79,80,81,82,83,84,86,87,88,89,91,92,93,94,96,97,98,99]
DEV15 = [5,10,15,25,30,35,45,50,55,65,70,75,85,90,95]
ORDER = [66,74,9,12,73,26,79,31,54,18,19,88,38,8,28,29,0,24,37,98,27,91,2,78,76,80,82,99,56,21,33,44,14,16,61,23,6,96,43,47,51,69,59,63,42,13,4,93,39,49,97,60,83,36,67,86,3,81,87,71,20,53,7,58,40,89,94,68,48,92,34,72,17,32,62,41,52,64,22,84,11,57,1,46,77]
CHECKPOINT = "ac14f5ced354c93f26cf92404540712eff65bd02554d9e9ed0332508e290382d"
MAP = "c9eade9ca89b741768a0ca33b3a755b2656402864f121aefdceaed4b0174f7c8"


def run(repo: Path, *args: str, check: bool = True) -> subprocess.CompletedProcess[str]:
    return subprocess.run(["git", "-C", str(repo), *args], text=True, capture_output=True, check=check)


def sha(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            h.update(chunk)
    return h.hexdigest()


def git_sha(repo: Path, spec: str) -> str:
    data = subprocess.run(["git", "-C", str(repo), "show", spec], capture_output=True, check=True).stdout
    return hashlib.sha256(data).hexdigest()


def git_content(repo: Path, spec: str) -> bytes:
    return subprocess.run(
        ["git", "-C", str(repo), "show", spec], capture_output=True, check=True
    ).stdout


def require(condition: bool, name: str, failures: list[str]) -> None:
    if not condition:
        failures.append(name)


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--repo-root", type=Path, default=Path.cwd())
    parser.add_argument("--phase", choices=["protocol"], default="protocol")
    args = parser.parse_args()
    repo = args.repo_root.resolve()
    root = repo / TASK_REL
    failures: list[str] = []

    protocol = json.loads((root / "V3_PAIRED_VALIDATION_PROTOCOL.json").read_text(encoding="utf-8"))
    lock = json.loads((root / "V3_INPUT_LOCK.json").read_text(encoding="utf-8"))
    reuse = json.loads((root / "V3_REFERENCE_REUSE_LOCK.json").read_text(encoding="utf-8"))
    rules = json.loads((root / "V3_DECISION_RULES.json").read_text(encoding="utf-8"))
    schema = json.loads((root / "V3_REQUIRED_EVIDENCE_SCHEMA.json").read_text(encoding="utf-8"))
    with (root / "V3_TRIAL_MANIFEST.csv").open(encoding="utf-8", newline="") as handle:
        manifest = list(csv.DictReader(handle))

    require(run(repo, "merge-base", "--is-ancestor", UPSTREAM, "HEAD", check=False).returncode == 0, "UPSTREAM_NOT_ANCESTOR", failures)
    require(run(repo, "branch", "--show-current").stdout.strip() == BRANCH, "BRANCH_MISMATCH", failures)
    require(protocol["upstream"]["head"] == UPSTREAM, "PROTOCOL_UPSTREAM", failures)
    require(lock["upstream"]["head"] == UPSTREAM, "LOCK_UPSTREAM", failures)
    require(protocol["formal_v2_protocol_source"]["head"] == FORMAL_COMMIT, "FORMAL_COMMIT", failures)

    formal_expected = lock["formal_v2_protocol"]["artifacts"]
    for name, expected in formal_expected.items():
        spec = f"{FORMAL_COMMIT}:reproduction/formal/active_runtime_paired_experiment_v2/{name}"
        require(run(repo, "rev-parse", spec).stdout.strip() == expected["git_blob"], f"FORMAL_BLOB:{name}", failures)
        require(git_sha(repo, spec) == expected["sha256"], f"FORMAL_SHA256:{name}", failures)
    formal_root = "reproduction/formal/active_runtime_paired_experiment_v2"
    formal_protocol = json.loads(git_content(repo, f"{FORMAL_COMMIT}:{formal_root}/FORMAL_PAIRED_EXPERIMENT_PROTOCOL_V2.json"))
    formal_study = formal_protocol["study_design"]
    require(formal_study["primary_analysis_trial_ids"] == PRIMARY, "FORMAL_PRIMARY_IDENTITY", failures)
    require(formal_study["development_exposed_secondary_trial_ids"] == DEV15, "FORMAL_DEV15_IDENTITY", failures)
    require([trial for trial in formal_study["execution_order"] if trial not in set(DEV15)] == ORDER, "FORMAL_FILTERED_ORDER_IDENTITY", failures)
    formal_manifest = list(csv.DictReader(git_content(repo, f"{FORMAL_COMMIT}:{formal_root}/FORMAL_TRIAL_MANIFEST_V2.csv").decode("utf-8").splitlines()))
    formal_primary_from_manifest = sorted(int(row["trial_id"]) for row in formal_manifest if row["included_in_primary_85"].lower() == "true")
    require(formal_primary_from_manifest == PRIMARY, "FORMAL_MANIFEST_PRIMARY_IDENTITY", failures)

    pilot_dir = repo / "reproduction/pilot/active_runtime_pilot_v3"
    for name, expected in lock["pilot_v3_evidence"]["artifact_sha256"].items():
        require(sha(pilot_dir / name) == expected, f"PILOT_ARTIFACT:{name}", failures)
    pilot_summary = json.loads((pilot_dir / "PILOT_V3_EXECUTION_SUMMARY.json").read_text(encoding="utf-8"))
    require(pilot_summary["FINAL_STATUS"] == "PASS_ACTIVE_RUNTIME_PILOT_V3", "PILOT_STATUS", failures)
    require((pilot_summary["completed_trials"], pilot_summary["completed_cycles"], pilot_summary["plant_commits"]) == (10, 4859, 4858), "PILOT_COUNTS", failures)
    require(pilot_summary["trace_cardinality"] == "PASS" and pilot_summary["finalization_pass_count"] == 10, "PILOT_TRACE_FINALIZATION", failures)
    require(pilot_summary["hard_runtime_radius_observed_values_q"] == [0.015], "PILOT_RADIUS", failures)
    require(pilot_summary["historical_diagnostic_intrusion_count"] == 0 and pilot_summary["historical_diagnostic_runtime_authority_observed"] is False, "PILOT_HISTORICAL_AUTHORITY", failures)

    pstudy = protocol["study_design"]
    require(pstudy["primary_trial_ids"] == PRIMARY, "PRIMARY_IDS", failures)
    require(pstudy["execution_order"] == ORDER, "EXECUTION_ORDER", failures)
    require(pstudy["development_exposed_trial_ids"] == DEV15, "DEV15_IDS", failures)
    require(set(PRIMARY).isdisjoint(DEV15) and len(PRIMARY) == 85, "COHORT_PARTITION", failures)
    require(len(manifest) == 85, "MANIFEST_COUNT", failures)
    require([int(row["trial_id"]) for row in manifest] == ORDER, "MANIFEST_ORDER", failures)
    require([int(row["execution_rank"]) for row in manifest] == list(range(1, 86)), "MANIFEST_RANK", failures)
    require(all(row == {
        "execution_rank": str(index),
        "trial_id": str(ORDER[index - 1]),
        "analysis_cohort": "PRIMARY_V3_REPEATED_BENCHMARK_85",
        "active_arm": "ACTIVE_RUNTIME_V3",
        "reference_source": "FORMAL_V2_REFERENCE_CBF_QP",
        "reference_reuse": "true",
        "outcome_exposure": "FORMAL_V2_OUTCOME_EXPOSED_FOR_V3",
        "included_in_primary": "true",
    } for index, row in enumerate(manifest, 1)), "MANIFEST_FIELDS", failures)

    require(pstudy["seed"] == 0 and pstudy["max_completed_cycles_per_active_arm"] == 500, "SEED_MAX", failures)
    require(pstudy["serial_execution"] is True and pstudy["separate_process_per_active_arm"] is True, "PROCESS_MODE", failures)
    require(pstudy["future_gpu_id"] == 1, "GPU_ID", failures)
    env = protocol["environment"]
    require(env["conda_environment"] == "/disk1/zlab/conda_envs/safer_splat_official", "ENV", failures)
    require(env["python"] == "/disk1/zlab/conda_envs/safer_splat_official/bin/python", "PYTHON", failures)
    require(protocol["map"]["identity"] == MAP, "MAP_IDENTITY", failures)
    require(any(row["sha256"] == CHECKPOINT for row in protocol["map"]["artifacts"]), "CHECKPOINT_IDENTITY", failures)
    cd = protocol["controller_and_dynamics"]
    require(cd["proposal_source"] == "CURRENT_PRIMARY_CBF_QP" and cd["alpha"] == 5.0 and cd["beta"] == 1.0, "CONTROLLER", failures)
    require(cd["dynamics"] == "POSITION_FIRST_FORWARD_EULER_DOUBLE_INTEGRATOR_V1" and cd["dt"] == 0.05, "DYNAMICS", failures)
    require(cd["actuator_bounds"] == [-0.1, 0.1] and cd["velocity_bounds"] == [-0.1, 0.1], "BOUNDS", failures)

    geom = protocol["v3_hard_geometry"]
    require((geom["r_body_q"], geom["m_hard_q"], geom["r_hard_q"], geom["rho_seg_q"]) == (0.015, 0.0, 0.015, 0.0), "V3_GEOMETRY", failures)
    hist = protocol["historical_diagnostic_shell"]
    require(hist["radius_q"] == 0.025, "HIST_RADIUS", failures)
    require(all(value is False for key, value in hist.items() if key.endswith("authority")), "HIST_AUTHORITY", failures)
    require(protocol["primary_hard_safety_gate"]["historical_0p025_primary_gate_authority"] is False, "HIST_PRIMARY_GATE", failures)

    oracle = protocol["posthoc_oracle"]
    require(oracle["feedback"] is False and oracle["posthoc_only"] is True, "ORACLE_BOUNDARY", failures)
    require(oracle["hard_collision_safety_radius_q"] == 0.015 and oracle["rho_seg_q"] == 0.0, "ORACLE_RADIUS", failures)
    require(oracle["normalized_progress"] == "(d_start - d_final) / d_start" and oracle["progress_clipping"] == "NONE", "PROGRESS_DEFINITION", failures)
    ni = protocol["primary_progress_noninferiority_gate"]
    require(ni["margin"] == -0.02 and ni["bootstrap_resamples"] == 10000 and ni["bootstrap_seed"] == 20260911, "NI_CONFIGURATION", failures)
    require(ni["pass_rule"] == "LOWER_BOUND_STRICTLY_GREATER_THAN_MINUS_0P02", "NI_RULE", failures)
    require(protocol["outcome_exposure"] == "OUTCOME_EXPOSED_REPEATED_BENCHMARK_VALIDATION", "EXPOSURE_ROLE", failures)
    require(protocol["claim_boundary"]["prohibited"] and protocol["claim_boundary"]["allowed_if_supported"], "CLAIM_BOUNDARY", failures)

    require(reuse["status"] == "PASS_REFERENCE_REUSE_IDENTITY_RESOLVED", "REFERENCE_STATUS", failures)
    require(reuse["reference_arm_count"] == 85 and reuse["reference_trial_ids"] == PRIMARY, "REFERENCE_COHORT", failures)
    require(reuse["all_immutable_complete_identity_compatible"] is True, "REFERENCE_COMPATIBILITY", failures)
    require(reuse["reference_rerun_authorized"] is False and reuse["reference_rerun_count"] == 0, "REFERENCE_RERUN", failures)
    records = reuse["records"]
    require(len(records) == 85 and [row["trial_id"] for row in records] == PRIMARY, "REFERENCE_RECORDS", failures)
    required_record_fields = set(schema["reused_reference_per_trial_required"])
    for row in records:
        require(required_record_fields.issubset(row), f"REFERENCE_FIELDS:{row.get('trial_id')}", failures)
        require(row["arm"] == "REFERENCE_CBF_QP" and row["source_git_identity"] == "606edd1c254f4ffaec48e0b84d8f5e5f29c039ec", f"REFERENCE_METHOD:{row['trial_id']}", failures)
        require(row["map_identity"] == MAP and row["checkpoint_identity"] == CHECKPOINT, f"REFERENCE_MAP:{row['trial_id']}", failures)
        require(row["seed"] == 0 and row["dt"] == 0.05 and row["max_steps"] == 500, f"REFERENCE_EXECUTION:{row['trial_id']}", failures)
        require(row["execution_complete"] is True and row["evaluation_eligible"] is True and row["finalization_proven"] is True, f"REFERENCE_ELIGIBILITY:{row['trial_id']}", failures)
        require(row["oracle_input_availability"]["posthoc_oracle_evaluation_eligible"] is True and row["oracle_input_availability"]["oracle_feedback"] is False, f"REFERENCE_ORACLE:{row['trial_id']}", failures)

    for filename, expected in lock["task_artifact_sha256"].items():
        require(sha(root / filename) == expected, f"TASK_HASH:{filename}", failures)
    sha_line = (root / "V3_PAIRED_VALIDATION_PROTOCOL.sha256").read_text(encoding="utf-8").strip()
    require(sha_line == f"{sha(root / 'V3_PAIRED_VALIDATION_PROTOCOL.json')}  V3_PAIRED_VALIDATION_PROTOCOL.json", "PROTOCOL_SHA_FILE", failures)

    require(rules["frozen_pre_outcome"] is True and rules["required_pair_count"] == 85, "RULES_FROZEN", failures)
    require(len(schema["active_v3_per_trial_required"]) >= 40 and len(schema["reused_reference_per_trial_required"]) >= 20, "EVIDENCE_SCHEMA", failures)
    require(all(value == 0 for value in protocol["execution_counts_at_freeze"].values()), "PROTOCOL_EXECUTION_COUNTS", failures)
    require(all(value == 0 for value in lock["execution_counts"].values()), "LOCK_EXECUTION_COUNTS", failures)

    changed = []
    status = run(repo, "status", "--porcelain").stdout.splitlines()
    for line in status:
        path = line[3:].replace("\\", "/")
        if " -> " in path:
            path = path.split(" -> ", 1)[1]
        changed.append(path)
    committed = run(repo, "diff", "--name-only", UPSTREAM, "HEAD").stdout.splitlines()
    require(all(path.startswith(TASK_REL) for path in changed + committed), "PROTECTED_DIFF", failures)

    if failures:
        print("BLOCK_ACTIVE_RUNTIME_V3_PAIRED_VALIDATION_PROTOCOL")
        for failure in failures:
            print(f"FAIL={failure}")
        return 1
    print("PASS_ACTIVE_RUNTIME_V3_PAIRED_VALIDATION_PROTOCOL_VALIDATION")
    print("ACTIVE_V3_EXECUTION_COUNT=0")
    print("REFERENCE_RERUN_COUNT=0")
    print("ORACLE_EXECUTION_COUNT=0")
    print("OFFICIAL100_EXECUTION_COUNT=0")
    print("FORMAL_NEW_OUTCOME_COUNT=0")
    return 0


if __name__ == "__main__":
    sys.exit(main())
