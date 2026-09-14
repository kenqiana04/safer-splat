#!/usr/bin/env python3
"""Build the V3 Reference reuse lock from immutable Formal V2 evidence.

This helper performs read-only SSH inspection. It never launches a trial, an
oracle, or a GPU process and never writes to the Formal V2 result root.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import subprocess
from pathlib import Path


UPSTREAM = "974b1957f3da55964814650ec5db6e98c84fc12e"
FORMAL_COMMIT = "ea2dfad6ad1e4b4cb4040e48a70084f7dcbfeab8"
FORMAL_ROOT = "/disk1/zlab/formal_execution_records/formal_paired_v2_20260911"
REMOTE_PYTHON = "/disk1/zlab/conda_envs/safer_splat_official/bin/python"
FORMAL_FILES = (
    "FORMAL_PAIRED_EXPERIMENT_PROTOCOL_V2.json",
    "FORMAL_TRIAL_MANIFEST_V2.csv",
    "FORMAL_ANALYSIS_PLAN_V2.md",
    "FORMAL_RUN_CONFIG_V2.json",
)


def git(repo: Path, *args: str) -> str:
    return subprocess.run(
        ["git", "-C", str(repo), *args],
        check=True,
        text=True,
        capture_output=True,
    ).stdout


def git_bytes(repo: Path, revision_path: str) -> bytes:
    return subprocess.run(
        ["git", "-C", str(repo), "show", revision_path],
        check=True,
        capture_output=True,
    ).stdout


def sha256(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


REMOTE_SCRIPT = r'''
import hashlib
import json
import pathlib
import sys

import numpy as np

root = pathlib.Path(sys.argv[1])
primary_ids = json.loads(sys.argv[2])


def digest(path):
    h = hashlib.sha256()
    with open(path, "rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            h.update(chunk)
    return h.hexdigest()


def canonical_hash(value):
    payload = json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=False)
    return hashlib.sha256(payload.encode("utf-8")).hexdigest()


accepted_path = root / "FORMAL_ACCEPTED_INDEX.json"
raw_manifest_path = root / "FORMAL_RAW_EVIDENCE_MANIFEST.json"
environment_path = root / "FORMAL_ENVIRONMENT_MANIFEST.json"
accepted = json.load(open(accepted_path, encoding="utf-8"))["arms"]
raw_manifest = json.load(open(raw_manifest_path, encoding="utf-8"))["arms"]
environment = json.load(open(environment_path, encoding="utf-8"))
raw_by_key = {(int(row["trial_id"]), row["arm"]): row for row in raw_manifest}

t = np.linspace(0, 2 * np.pi, 100)
t_z = 10 * np.linspace(0, 2 * np.pi, 100)
radius = 0.784 / 2
center = np.array([-0.08, -0.03, 0.05])
goals = np.stack(
    [radius * np.cos(t + np.pi), radius * np.sin(t + np.pi), 0.01 * np.sin(t_z + np.pi)],
    axis=-1,
) + center

records = []
for trial_id in primary_ids:
    key = f"{trial_id:03d}:REFERENCE_CBF_QP"
    if key not in accepted:
        raise RuntimeError(f"REFERENCE_ACCEPTANCE_MISSING:{trial_id}")
    entry = accepted[key]
    manifest_entry = raw_by_key.get((trial_id, "REFERENCE_CBF_QP"))
    if manifest_entry != entry:
        raise RuntimeError(f"REFERENCE_MANIFEST_INDEX_MISMATCH:{trial_id}")
    attempt_dir = pathlib.Path(entry["attempt_dir"])
    summary_path = pathlib.Path(entry["summary_path"])
    meta_path = attempt_dir / "attempt_meta.json"
    raw_root = summary_path.parent
    raw_lock_path = raw_root / "raw_evidence_lock.json"
    summary = json.load(open(summary_path, encoding="utf-8"))
    meta = json.load(open(meta_path, encoding="utf-8"))
    raw_lock = json.load(open(raw_lock_path, encoding="utf-8"))

    if digest(summary_path) != entry["summary_sha256"]:
        raise RuntimeError(f"REFERENCE_SUMMARY_HASH_MISMATCH:{trial_id}")
    if not meta.get("accepted") or meta.get("child_return_code") != 0:
        raise RuntimeError(f"REFERENCE_ATTEMPT_NOT_ACCEPTED:{trial_id}")
    if meta.get("summary_sha256") != entry["summary_sha256"]:
        raise RuntimeError(f"REFERENCE_META_SUMMARY_HASH_MISMATCH:{trial_id}")
    if summary.get("trial_id") != trial_id or summary.get("arm") != "REFERENCE_CBF_QP":
        raise RuntimeError(f"REFERENCE_SUMMARY_IDENTITY_MISMATCH:{trial_id}")
    if not summary.get("execution_complete") or not summary.get("evaluation_eligible"):
        raise RuntimeError(f"REFERENCE_NOT_EVALUATION_ELIGIBLE:{trial_id}")
    if summary.get("process_exit_code") != 0:
        raise RuntimeError(f"REFERENCE_PROCESS_NONZERO:{trial_id}")
    if summary.get("evidence_incomplete_count") != 0 or summary.get("recovery_required_count") != 0:
        raise RuntimeError(f"REFERENCE_EVIDENCE_INCOMPLETE:{trial_id}")
    if summary.get("raw_evidence_lock") != entry["raw_evidence_lock"]:
        raise RuntimeError(f"REFERENCE_RAW_LOCK_IDENTITY_MISMATCH:{trial_id}")
    oracle = summary.get("oracle") or {}
    if not oracle.get("evaluation_eligible") or oracle.get("feedback") is not False:
        raise RuntimeError(f"REFERENCE_ORACLE_INPUT_NOT_ELIGIBLE:{trial_id}")

    locked_files = {}
    for file_row in raw_lock["files"]:
        path = raw_root / file_row["name"]
        actual = {"sha256": digest(path), "size": path.stat().st_size}
        if actual != {"sha256": file_row["sha256"], "size": file_row["size"]}:
            raise RuntimeError(f"REFERENCE_RAW_FILE_DRIFT:{trial_id}:{file_row['name']}")
        locked_files[file_row["name"]] = actual
    required = {"trajectory_states.jsonl", "executed_actions.jsonl", "step_timing.jsonl", "termination.json"}
    if set(locked_files) != required:
        raise RuntimeError(f"REFERENCE_RAW_FILE_SET_MISMATCH:{trial_id}")

    with open(raw_root / "trajectory_states.jsonl", encoding="utf-8") as handle:
        first_state = json.loads(handle.readline())
    goal_position = goals[trial_id].astype(np.float32)
    goal_state = [float(value) for value in np.concatenate((goal_position, np.zeros(3, dtype=np.float32)))]
    termination = json.load(open(raw_root / "termination.json", encoding="utf-8"))
    if termination.get("typed_termination") != summary.get("typed_termination"):
        raise RuntimeError(f"REFERENCE_TERMINATION_MISMATCH:{trial_id}")

    evidence_components = {
        "summary_sha256": entry["summary_sha256"],
        "raw_evidence_lock": entry["raw_evidence_lock"],
        "raw_evidence_lock_sha256": digest(raw_lock_path),
        "trajectory_sha256": locked_files["trajectory_states.jsonl"]["sha256"],
        "executed_actions_sha256": locked_files["executed_actions.jsonl"]["sha256"],
        "step_timing_sha256": locked_files["step_timing.jsonl"]["sha256"],
        "termination_sha256": locked_files["termination.json"]["sha256"],
    }
    records.append({
        "trial_id": trial_id,
        "arm": "REFERENCE_CBF_QP",
        "method_identity": "CURRENT_PRIMARY_CBF_QP_WITH_FROZEN_PLANT_DYNAMICS_BYPASS_ACTIVE_RUNTIME_ASSURANCE",
        "source_git_identity": environment["method_head"],
        "accepted_attempt_relative_path": str(attempt_dir.relative_to(root)),
        "accepted_at_unix": entry["accepted_at_unix"],
        "summary_sha256": entry["summary_sha256"],
        "raw_evidence_lock_identity": entry["raw_evidence_lock"],
        "raw_evidence_lock_sha256": evidence_components["raw_evidence_lock_sha256"],
        "trajectory_action_evidence_sha256": canonical_hash({
            "trajectory": evidence_components["trajectory_sha256"],
            "actions": evidence_components["executed_actions_sha256"],
        }),
        "locked_files": locked_files,
        "state_count": raw_lock["state_count"],
        "action_count": raw_lock["action_count"],
        "timing_count": raw_lock["timing_count"],
        "start_state": first_state["state"],
        "start_state_hash": first_state["state_hash"],
        "goal_state": goal_state,
        "goal_state_task_hash": canonical_hash(goal_state),
        "seed": 0,
        "dt": 0.05,
        "max_steps": 500,
        "typed_termination": summary["typed_termination"],
        "steps_executed": summary["steps_executed"],
        "execution_complete": True,
        "evaluation_eligible": True,
        "finalization_proof": "ACCEPTED_SUMMARY_AND_IMMUTABLE_RAW_EVIDENCE_LOCK",
        "finalization_proven": True,
        "oracle_input_availability": {
            "complete_state_log": True,
            "complete_action_log": True,
            "posthoc_oracle_evaluation_eligible": True,
            "oracle_feedback": False,
        },
        "reference_evidence_identity_sha256": canonical_hash(evidence_components),
    })

out = {
    "schema": "ACTIVE_RUNTIME_V3_REFERENCE_REUSE_LOCK_V1",
    "status": "PASS_REFERENCE_REUSE_IDENTITY_RESOLVED",
    "reference_policy": "REFERENCE_EVIDENCE_REUSE_REQUIRED",
    "reference_rerun_authorized": False,
    "reference_rerun_count": 0,
    "formal_v2_result_root": str(root),
    "formal_v2_result_artifact_sha256": {
        "FORMAL_ACCEPTED_INDEX.json": digest(accepted_path),
        "FORMAL_RAW_EVIDENCE_MANIFEST.json": digest(raw_manifest_path),
        "FORMAL_ENVIRONMENT_MANIFEST.json": digest(environment_path),
        "FORMAL_INTEGRITY_REGISTER.csv": digest(root / "FORMAL_INTEGRITY_REGISTER.csv"),
        "FORMAL_PAIR_SUMMARY.csv": digest(root / "FORMAL_PAIR_SUMMARY.csv"),
    },
    "formal_v2_source_git_identity": environment["method_head"],
    "reference_arm_count": len(records),
    "reference_trial_ids": primary_ids,
    "all_immutable_complete_identity_compatible": len(records) == 85,
    "records": records,
}
print(json.dumps(out, indent=2, sort_keys=True))
'''


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--repo-root", type=Path, default=Path.cwd())
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    repo = args.repo_root.resolve()

    if git(repo, "rev-parse", "HEAD").strip() != UPSTREAM:
        raise RuntimeError("BUILDER_MUST_RUN_BEFORE_TASK_COMMIT_AT_EXACT_PR143_HEAD")
    formal_blobs = {}
    for name in FORMAL_FILES:
        data = git_bytes(repo, f"{FORMAL_COMMIT}:reproduction/formal/active_runtime_paired_experiment_v2/{name}")
        formal_blobs[name] = {"git_blob": git(repo, "rev-parse", f"{FORMAL_COMMIT}:reproduction/formal/active_runtime_paired_experiment_v2/{name}").strip(), "sha256": sha256(data)}
    protocol = json.loads(git_bytes(repo, f"{FORMAL_COMMIT}:reproduction/formal/active_runtime_paired_experiment_v2/FORMAL_PAIRED_EXPERIMENT_PROTOCOL_V2.json"))
    primary_ids = protocol["study_design"]["primary_analysis_trial_ids"]

    result = subprocess.run(
        ["ssh", "zlab-4090", REMOTE_PYTHON, "-", FORMAL_ROOT, json.dumps(primary_ids, separators=(",", ":"))],
        input=REMOTE_SCRIPT,
        text=True,
        capture_output=True,
        check=True,
    )
    lock = json.loads(result.stdout)
    lock["formal_v2_protocol_git_identity"] = FORMAL_COMMIT
    lock["formal_v2_protocol_artifacts"] = formal_blobs
    lock["v3_protocol_upstream_pr"] = 143
    lock["v3_protocol_upstream_head"] = UPSTREAM
    lock["map_identity"] = protocol["map_lock"]["map_identity_sha256"]
    lock["map_artifacts"] = protocol["map_lock"]["artifacts"]
    lock["execution_identity"] = {
        "seed": protocol["study_design"]["seed"],
        "max_steps": protocol["study_design"]["max_steps"],
        "dt": protocol["dynamics_lock"]["dt"],
        "dynamics": protocol["dynamics_lock"]["identity"],
        "velocity_bounds": protocol["dynamics_lock"]["velocity_bounds"],
        "controller": protocol["controller_lock"]["proposal_source"],
        "alpha": protocol["controller_lock"]["alpha"],
        "beta": protocol["controller_lock"]["beta"],
        "controller_radius_q": protocol["controller_lock"]["controller_radius_m"],
        "actuator_bounds": protocol["controller_lock"]["actuator_bounds"],
        "goal_predicate": "STRICT_6D_L2_NORM_LT_0P001",
    }
    checkpoint_sha = next(
        row["sha256"]
        for row in protocol["map_lock"]["artifacts"]
        if row["relative_path"].endswith(".ckpt")
    )
    for record in lock["records"]:
        record["map_identity"] = protocol["map_lock"]["map_identity_sha256"]
        record["checkpoint_identity"] = checkpoint_sha
        record["controller_identity"] = protocol["controller_lock"]["proposal_source"]
        record["controller_alpha"] = protocol["controller_lock"]["alpha"]
        record["controller_beta"] = protocol["controller_lock"]["beta"]
        record["controller_radius_q"] = protocol["controller_lock"]["controller_radius_m"]
        record["actuator_bounds"] = protocol["controller_lock"]["actuator_bounds"]
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(lock, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(f"PASS_REFERENCE_REUSE_IDENTITY_RESOLVED count={lock['reference_arm_count']}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
