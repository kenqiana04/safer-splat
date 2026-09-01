#!/usr/bin/env python3
"""Freeze all task-owned code and server identities before formal data."""

from __future__ import annotations

import argparse
from pathlib import Path

from collection_common import (
    EXPECTED_UPSTREAM_HEAD, MAP_AUTHORITY_ID, OFFICIAL100_SHA256, PROTOCOL_SHA256,
    atomic_write_json, file_sha256, load_json, semantic_sha256,
)

LOCKED_SCRIPTS = (
    "collection_common.py", "collect_formal_cohort.py", "run_one_formal_trial.py",
    "outcome_blind_qc.py", "build_collection_lock.py", "raw_artifact_manifest.py",
    "freeze_collection_execution_lock.py", "server_preflight.py", "materialize_official100.py",
)


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--script-dir", type=Path, required=True)
    parser.add_argument("--environment-identity", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    if args.output.exists():
        raise RuntimeError("execution lock overwrite forbidden")
    environment = load_json(args.environment_identity)
    required = {
        "upstream_head": EXPECTED_UPSTREAM_HEAD,
        "protocol_sha256": PROTOCOL_SHA256,
        "official100_sha256": OFFICIAL100_SHA256,
        "map_authority_id": MAP_AUTHORITY_ID,
        "formal_navigation_run_count": 0,
        "formal_intended_step_count": 0,
        "formal_capture_count": 0,
        "formal_result_count": 0,
    }
    for key, expected in required.items():
        if environment.get(key) != expected:
            raise RuntimeError(f"pre-data environment identity mismatch: {key}")
    script_hashes = {name: file_sha256(args.script_dir / name) for name in LOCKED_SCRIPTS}
    payload = {
        "schema_version": "L2_H1_COLLECTION_EXECUTION_LOCK_V1",
        "upstream_head": EXPECTED_UPSTREAM_HEAD,
        "upstream_PR100_head": EXPECTED_UPSTREAM_HEAD,
        "protocol_sha256": PROTOCOL_SHA256,
        "protocol_combined_sha256": PROTOCOL_SHA256,
        "official100_sha256": OFFICIAL100_SHA256,
        "official100_manifest_sha256": OFFICIAL100_SHA256,
        "map_authority_id": MAP_AUTHORITY_ID,
        "formal_data_role": "FORMAL_PROSPECTIVE_SHADOW_COHORT_V1",
        "task_script_sha256": script_hashes,
        "runner_file_sha256": script_hashes["collect_formal_cohort.py"],
        "one_trial_launcher_sha256": script_hashes["run_one_formal_trial.py"],
        "outcome_blind_qc_file_sha256": script_hashes["outcome_blind_qc.py"],
        "collection_lock_builder_sha256": script_hashes["build_collection_lock.py"],
        "raw_artifact_manifest_builder_sha256": script_hashes["raw_artifact_manifest.py"],
        "environment_identity_sha256": file_sha256(args.environment_identity),
        "environment_identity": environment,
        "instrumentation_identity": environment["instrumentation_identity"],
        "controller_identity": environment["controller_identity"],
        "python": environment["python"],
        "torch": environment["torch"],
        "cuda": environment["torch_cuda"],
        "physical_gpu": environment["physical_gpu_index"],
        "created_before_first_formal_observation": True,
        "formal_intended_step_count_at_lock": 0,
        "formal_capture_count_at_lock": 0,
        "pre_data_counts": {
            "formal_navigation_run_count": 0,
            "formal_intended_step_count": 0,
            "formal_capture_count": 0,
            "formal_result_count": 0,
        },
        "outcome_blind_collection_only": True,
        "scientific_analysis_authorized": False,
    }
    payload["collection_execution_lock_sha256"] = semantic_sha256(payload)
    payload["combined_collection_execution_sha256"] = payload["collection_execution_lock_sha256"]
    atomic_write_json(args.output, payload)
    print(payload["collection_execution_lock_sha256"])
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
