#!/usr/bin/env python3
"""Validate the frozen protocol and canonicalization evidence without training."""
from __future__ import annotations

import json
import subprocess
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
REPO = ROOT.parents[2]
BASE = "8199c9c4c5ce76e65f389e963376a8a02d784247"
POLICY = "becbc4af"
PASS = "PASS_READY_FOR_FORMAL_TRAINING_EXECUTION_AFTER_HASH_CANONICALIZATION"


def load(name: str) -> dict:
    return json.loads((ROOT / name).read_text(encoding="utf-8"))


def git(*args: str) -> subprocess.CompletedProcess[str]:
    return subprocess.run(["git", *args], cwd=REPO, text=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)


def attr(path: str) -> bool:
    output = git("check-attr", "text", "eol", "--", path).stdout
    return "text: set" in output and "eol: lf" in output


def cache(path: str) -> bool:
    return path.endswith(".pyc") or "/__pycache__/" in path.replace("\\", "/")


def main() -> None:
    dataset, env, frozen, command, output, handoff = map(load, [
        "dataset_lock.json", "environment_lock.json", "frozen_training_config.json",
        "exact_training_command.json", "output_directory_contract.json", "training_execution_handoff.json",
    ])
    correction = load("protocol_hash_correction_result.json")
    server = load("canonical_hash_verification_server.json")
    audit = "reproduction/cross_dataset/tum_splatfacto_training_protocol_v1"
    base_caches = sorted(x for x in git("ls-tree", "-r", "--name-only", BASE).stdout.splitlines() if cache(x))
    current_caches = sorted(x for x in git("ls-files").stdout.splitlines() if cache(x))
    protocol_caches = [x for x in git("ls-files", "--others", "--exclude-standard", "--", audit).stdout.splitlines() if cache(x)]
    checks = [
        ("base_commit", git("merge-base", "--is-ancestor", BASE, "HEAD").returncode == 0),
        ("policy_commit", git("merge-base", "--is-ancestor", POLICY, "HEAD").returncode == 0),
        ("dataset_lock", dataset["transforms_sha256"] == "b6a685f4b1a5b2ff3bb9b389c63a138a58119b19dd5cb6d7f671282aeecad29a" and (dataset["source_frame_count"], dataset["train_frame_count"], dataset["eval_frame_count"]) == (300, 240, 60)),
        ("metric_parser", dataset["depth_unit_scale_factor_meters"] == 0.0002 and dataset["orientation_method"] == "none" and dataset["center_method"] == "none" and dataset["auto_scale_poses"] is False and dataset["dataparser_scale"] == 1.0),
        ("environment", env["hostname"] == "zlab-Super-Server" and env["nerfstudio_version"] == "1.1.5" and env["visible_gpu_name"] == "NVIDIA GeForce RTX 4090"),
        ("method_seed", frozen["method"] == "splatfacto" and frozen["seed"] == 20260716 and frozen["formal_run_count"] == 1),
        ("canonical_hash_policy", correction["status"] == PASS and command["command_sha256_domain"] == "git_blob_bytes"),
        ("directory_lf_contract", attr(f"{audit}/exact_training_command.sh") and attr(f"{audit}/frozen_training_config.json")),
        ("server_output_absent", server.get("output_path_absent") is True),
        ("no_execution", command["training_iterations_executed"] == 0 and command["checkpoint_created"] is False and command["run_directory_created"] is False),
        ("handoff", handoff["training_authorized_by_this_correction"] is False and handoff["previous_execution_branch_reusable"] is False and handoff["previous_training_attempt_count"] == 0 and handoff["G1_allowed"] is False),
        ("output_contract", output["must_not_exist_before_training"] and not output["source_data_overlap"] and not output["overwrite_allowed"] and not output["resume_allowed"]),
        ("freeze_zero_diff", git("diff", "--exit-code", BASE, "--", "reproduction/experiment_protocol_freeze_v1").returncode == 0),
        ("g0_zero_diff", git("diff", "--exit-code", BASE, "--", "reproduction/cross_dataset/tum_g0_checkpoint_entry_audit_v1").returncode == 0),
        ("execution_zero_diff", git("diff", "--exit-code", BASE, "--", "reproduction/cross_dataset/tum_splatfacto_training_execution_v1").returncode == 0),
        ("core_zero_diff", git("diff", "--exit-code", BASE, "--", "cbf", "dynamics", "ellipsoids", "ns_utils", "splat", "run.py").returncode == 0),
        ("cache_baseline_unchanged", base_caches == current_caches and not protocol_caches),
    ]
    status = PASS if all(ok for _, ok in checks) else "FAIL"
    result = {
        "status": status,
        "checks": [{"check": name, "passed": ok} for name, ok in checks],
        "training_iterations_executed": 0,
        "run_directory_created": False,
        "checkpoint_created": False,
        "safer_executed": False,
        "G1_allowed": False,
        "unresolved_critical_fields": [] if status == PASS else [name for name, ok in checks if not ok],
        "unresolved_noncritical_fields": [],
    }
    (ROOT / "validation_result.json").write_text(json.dumps(result, indent=2, sort_keys=True) + "\n", encoding="utf-8", newline="\n")
    print(status)
    if status != PASS:
        raise SystemExit(status)


if __name__ == "__main__":
    main()
