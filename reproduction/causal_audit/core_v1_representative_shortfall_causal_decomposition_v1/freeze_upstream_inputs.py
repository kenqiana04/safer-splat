"""Freeze PR84-PR89 identities and canonical Git-blob evidence."""
from __future__ import annotations

import json
import subprocess
from pathlib import Path

from common import sha256_bytes, sha256_file, write_json
from task_config import BASE_BRANCH, BASE_HEAD, PR89_BASE_BRANCH, PR_HEADS, REPO_ROOT, TASK_ROOT, UPSTREAM_ROOT

PROTECTED = [
    (84, "reproduction/cross_dataset/fas_cbf_unified_executable_safety_certifier_v1/certifier/executable_safety_certifier.py", "unified_certifier"),
    (84, "reproduction/cross_dataset/fas_cbf_unified_executable_safety_certifier_v1/adapters/current_cbf_adapter.py", "current_gate"),
    (84, "reproduction/cross_dataset/fas_cbf_unified_executable_safety_certifier_v1/adapters/normative_dynamics_adapter.py", "position_first_dynamics"),
    (84, "reproduction/cross_dataset/fas_cbf_unified_executable_safety_certifier_v1/certifier/backup_certifier.py", "backup_certifier"),
    (84, "reproduction/cross_dataset/fas_cbf_unified_executable_safety_certifier_v1/certifier/segment_backends/conservative_interval.py", "segment_backend"),
    (86, "reproduction/cross_dataset/replica_gt_executable_safety_method_matrix_v1/alternative_library/directional_library.py", "six_slot_library"),
    (86, "reproduction/cross_dataset/replica_gt_executable_safety_method_matrix_v1/methods/method_registry.json", "method_matrix"),
    (87, "reproduction/cross_dataset/resume_replica_gt_executable_safety_activated_benchmark_v1/runtime_core.py", "replica_runtime"),
    (87, "reproduction/cross_dataset/resume_replica_gt_executable_safety_activated_benchmark_v1/registry/representative_holdout_registry_v1.json", "replica_registry"),
    (87, "reproduction/cross_dataset/resume_replica_gt_executable_safety_activated_benchmark_v1/benchmark/one_step_records.csv", "pr87_formal_records"),
    (88, "reproduction/research_direction/safer_splat_direction_audit_v1/report/downstream_handoff.json", "pr88_case_d"),
    (89, "reproduction/cross_dataset/core_v1_cross_environment_activation_portability_audit_v1/benchmark/one_step_records.csv", "pr89_formal_records"),
    (89, "reproduction/cross_dataset/core_v1_cross_environment_activation_portability_audit_v1/benchmark/formal_attempt.json", "pr89_attempt_marker"),
    (89, "reproduction/cross_dataset/core_v1_cross_environment_activation_portability_audit_v1/registry/combined_registry_manifest.json", "pr89_registry_manifest"),
    (89, "reproduction/cross_dataset/core_v1_cross_environment_activation_portability_audit_v1/decision/final_portability_decision.json", "pr89_case_c"),
    (89, "reproduction/cross_dataset/core_v1_cross_environment_activation_portability_audit_v1/benchmark/source_runtime.py", "external_runtime_adapter"),
]


def gh_identity(number: int) -> dict:
    result = subprocess.run([
        "gh", "pr", "view", str(number), "--repo", "kenqiana04/safer-splat",
        "--json", "number,state,isDraft,mergeable,baseRefName,baseRefOid,headRefName,headRefOid,url",
    ], cwd=REPO_ROOT, check=True, capture_output=True, text=True)
    value = json.loads(result.stdout)
    value = {
        "number": value["number"], "state": value["state"], "draft": value["isDraft"],
        "mergeable": value["mergeable"], "base": value["baseRefName"], "base_sha": value["baseRefOid"],
        "head": value["headRefName"], "head_sha": value["headRefOid"], "url": value["url"],
    }
    if value["state"] != "OPEN" or value["draft"] is not True or value["mergeable"] not in (True, "MERGEABLE"):
        raise RuntimeError(f"PR_{number}_NOT_OPEN_DRAFT_MERGEABLE")
    if value["head_sha"] != PR_HEADS[number]:
        raise RuntimeError(f"PR_{number}_HEAD_MISMATCH")
    return value


def blob(commit: str, path: str) -> tuple[str, bytes]:
    object_name = f"{commit}:{path}"
    git_blob = subprocess.run(["git", "rev-parse", object_name], cwd=REPO_ROOT, check=True, capture_output=True, text=True).stdout.strip()
    data = subprocess.run(["git", "cat-file", "blob", object_name], cwd=REPO_ROOT, check=True, capture_output=True).stdout
    return git_blob, data


def main() -> None:
    identities = {number: gh_identity(number) for number in PR_HEADS}
    if identities[89]["base"] != PR89_BASE_BRANCH or identities[89]["base_sha"] != "9287617cce74561aa434d1aca7eb684f79551188":
        raise RuntimeError("PR89_BASE_MISMATCH")
    for number, identity in identities.items():
        write_json(TASK_ROOT / f"input_freeze/pr{number}_identity.json", identity)
    records = []
    for number, path, role in PROTECTED:
        object_id, data = blob(PR_HEADS[number], path)
        records.append({"pr": number, "commit": PR_HEADS[number], "path": path, "role": role, "git_blob": object_id, "size": len(data), "sha256": sha256_bytes(data)})
    manifest = {
        "status": "PASS_CANONICAL_GIT_BLOB_INPUT_FREEZE", "base_branch": BASE_BRANCH,
        "base_head": BASE_HEAD, "record_count": len(records), "records": records,
        "upstream_task_report_sha256": sha256_file(UPSTREAM_ROOT / "report/REPORT_AUDIT_CORE_V1_CROSS_ENVIRONMENT_ACTIVATION_PORTABILITY_V1.md"),
    }
    write_json(TASK_ROOT / "input_freeze/protected_source_hashes.json", manifest)
    print("PASS_INPUT_FREEZE", len(records))


if __name__ == "__main__":
    main()
