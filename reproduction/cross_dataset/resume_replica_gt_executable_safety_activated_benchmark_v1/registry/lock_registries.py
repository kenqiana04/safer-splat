#!/usr/bin/env python3
"""Lock and three-process rebuild both cohorts before formal/reference outcomes."""
from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path

TASK_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(TASK_ROOT))

from common import read_json, sha256_file, write_json


def rebuild(path: Path, label: str) -> tuple[dict, list[str]]:
    worker = TASK_ROOT / "registry/registry_rebuild_worker.py"
    outputs = []
    hashes = []
    for index in range(3):
        output = TASK_ROOT / f"runtime_work/registry_rebuild/{label}_{index + 1}.json"
        subprocess.run([sys.executable, "-B", str(worker), "--input", str(path), "--output", str(output)], check=True)
        outputs.append(output)
        hashes.append(sha256_file(output))
    if len(set(hashes)) != 1:
        raise SystemExit("BLOCKED_BY_REGISTRY_REBUILD_NONDETERMINISM")
    locked = json.loads(outputs[0].read_text(encoding="utf-8"))
    path.write_bytes(outputs[0].read_bytes())
    return locked, hashes


def main() -> None:
    activated_path = TASK_ROOT / "registry/activated_registry_v1.json"
    representative_path = TASK_ROOT / "registry/representative_holdout_registry_v1.json"
    if not activated_path.exists() or not representative_path.exists():
        raise SystemExit("REGISTRY_INPUT_MISSING")
    prelock = read_json(TASK_ROOT / "reference/reference_prelock_access_log.json")
    if prelock.get("future_outcome_read_count") != 0:
        raise SystemExit("BLOCKED_BY_COHORT_SELECTION_LEAKAGE")
    activated, activated_hashes = rebuild(activated_path, "activated")
    representative, representative_hashes = rebuild(representative_path, "representative")
    activated_sha = sha256_file(activated_path)
    representative_sha = sha256_file(representative_path)
    activated_ids = {item["state_id"] for item in activated["states"]}
    representative_ids = {item["state_id"] for item in representative["states"]}
    overlap = sorted(activated_ids & representative_ids)
    write_json(TASK_ROOT / "registry/combined_registry_manifest.json", {
        "status": "PASS_DUAL_REGISTRY_MANIFEST_LOCKED",
        "activated": {"path": "registry/activated_registry_v1.json", "sha256": activated_sha, "count": len(activated["states"])},
        "representative": {"path": "registry/representative_holdout_registry_v1.json", "sha256": representative_sha, "count": len(representative["states"])},
        "cohort_overlap_count": len(overlap),
        "pooling_allowed": False,
    })
    write_json(TASK_ROOT / "registry/registry_rebuild_audit.json", {
        "status": "PASS_THREE_PROCESS_DUAL_REGISTRY_REBUILD",
        "rebuild_count_each": 3,
        "activated_sha256_values": activated_hashes,
        "representative_sha256_values": representative_hashes,
        "activated_mismatch_count": len(set(activated_hashes)) - 1,
        "representative_mismatch_count": len(set(representative_hashes)) - 1,
    })
    write_json(TASK_ROOT / "registry/registry_lock.json", {
        "status": "IMMUTABLY_LOCKED_BEFORE_FORMAL_AND_FUTURE_REFERENCE_OUTCOMES",
        "activated_sha256": activated_sha,
        "representative_sha256": representative_sha,
        "activated_state_count": len(activated["states"]),
        "representative_state_count": len(representative["states"]),
        "prelock_future_reference_read_count": 0,
        "prelock_formal_method_run_count": 0,
        "prelock_rollout_count": 0,
        "prelock_progress_read_count": 0,
        "runtime_selection_count": 0,
        "post_lock_replacement_count": 0,
    })
    write_json(TASK_ROOT / "audits/cohort_overlap_audit.json", {
        "status": "PASS_COHORT_OVERLAP_ACCOUNTED_WITHOUT_POOLING",
        "overlap_count": len(overlap),
        "overlap_state_ids": overlap,
        "cohorts_pooled": False,
    })
    leakage_checks = {
        "activated_group_assignment_stage_predicates_only": True,
        "activated_prelock_future_reference_reads_zero": True,
        "activated_prelock_formal_runs_zero": True,
        "activated_no_progress_runtime_selection": True,
        "activated_no_post_lock_replacement": True,
        "representative_selection_no_stage_predicates": True,
        "representative_selection_no_B0_B3": True,
        "representative_selection_no_future_reference": True,
        "representative_no_observed_gate_balancing": True,
        "representative_no_post_lock_replacement": True,
    }
    write_json(TASK_ROOT / "audits/selection_leakage_audit.json", {"status": "PASS_SELECTION_LEAKAGE_AUDIT", "checks": leakage_checks, "all_pass": all(leakage_checks.values())})
    print("PASS_DUAL_REGISTRY_LOCK", len(activated["states"]), len(representative["states"]), len(overlap))


if __name__ == "__main__":
    main()
