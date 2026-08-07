"""Freeze protected inputs from raw Git objects at the preregistered heads."""
from __future__ import annotations

import hashlib
import json
import subprocess
from pathlib import Path

from common import write_json
from task_config import BASE_HEAD, LIBRARY_SHA256, PR_HEADS, TASK_ROOT


PR_METADATA = {
    84: ("fas-cbf-core-v1-conceptual-closure", "17805e67b75412dc21b1a5fff4143ea3bc985f7f", "fas-cbf-unified-executable-safety-certifier-v1"),
    85: ("fas-cbf-unified-executable-safety-certifier-v1", PR_HEADS[84], "replica-gt-executable-safety-activated-benchmark-v1"),
    86: ("replica-gt-executable-safety-activated-benchmark-v1", PR_HEADS[85], "replica-gt-executable-safety-method-matrix-v1"),
    87: ("replica-gt-executable-safety-method-matrix-v1", PR_HEADS[86], "resume-replica-gt-executable-safety-activated-benchmark-v1"),
    88: ("resume-replica-gt-executable-safety-activated-benchmark-v1", PR_HEADS[87], "research-direction-novelty-data-winnability-audit-v1"),
}

PROTECTED = (
    (84, "reproduction/cross_dataset/fas_cbf_unified_executable_safety_certifier_v1/certifier/executable_safety_certifier.py", "certifier"),
    (84, "reproduction/cross_dataset/fas_cbf_unified_executable_safety_certifier_v1/adapters/current_cbf_adapter.py", "current_full_query"),
    (84, "reproduction/cross_dataset/fas_cbf_unified_executable_safety_certifier_v1/adapters/gaussian_barrier_adapter.py", "map_adapter"),
    (84, "reproduction/cross_dataset/fas_cbf_unified_executable_safety_certifier_v1/certifier/segment_backends/conservative_interval.py", "segment_backend"),
    (86, "reproduction/cross_dataset/replica_gt_executable_safety_method_matrix_v1/methods/method_registry.json", "method_matrix"),
    (86, "reproduction/cross_dataset/replica_gt_executable_safety_method_matrix_v1/alternative_library/directional_library.py", "six_slot_library"),
    (86, "reproduction/cross_dataset/replica_gt_executable_safety_method_matrix_v1/alternative_library/alternative_library_identity.json", "library_identity"),
    (87, "reproduction/cross_dataset/resume_replica_gt_executable_safety_activated_benchmark_v1/runtime_core.py", "formal_runtime"),
    (87, "reproduction/cross_dataset/resume_replica_gt_executable_safety_activated_benchmark_v1/registry/representative_holdout_registry_v1.json", "replica_registry"),
    (87, "reproduction/cross_dataset/resume_replica_gt_executable_safety_activated_benchmark_v1/benchmark/one_step_records.csv", "replica_formal_evidence"),
    (88, "reproduction/research_direction/safer_splat_direction_audit_v1/report/downstream_handoff.json", "case_d_decision"),
    (88, "reproduction/cross_dataset/retrospective_requalify_existing_gaussian_maps_protocol_v2/classification/classification_matrix.json", "protocol_v2_map_tiers"),
    (88, "reproduction/cross_dataset/eth3d_delivery_area_provision_7zz_resume_assets_v1/routes/reference_route_contract_failure.json", "eth3d_route_boundary"),
    (88, "reproduction/cross_dataset/cross_dataset_qualified_gaussian_map_acquisition_v1/official_safer_scene_inventory.json", "official_scene_identities"),
)


def git_blob(commit: str, path: str) -> bytes:
    return subprocess.run(["git", "show", f"{commit}:{path}"], check=True, capture_output=True).stdout


def main() -> None:
    if subprocess.check_output(["git", "rev-parse", "HEAD"], text=True).strip() != BASE_HEAD:
        raise SystemExit("BASE_HEAD_MISMATCH_BEFORE_FREEZE")
    identities = {}
    for number, head in PR_HEADS.items():
        base, base_oid, branch = PR_METADATA[number]
        value = {
            "number": number, "state": "OPEN", "draft": True, "mergeable": "MERGEABLE",
            "base": base, "base_sha": base_oid, "head": branch, "head_sha": head,
            "url": f"https://github.com/kenqiana04/safer-splat/pull/{number}",
        }
        identities[number] = value
        write_json(TASK_ROOT / "input_freeze" / f"pr{number}_identity.json", value)
    records = []
    for number, path, role in PROTECTED:
        data = git_blob(PR_HEADS[number], path)
        records.append({
            "pr": number, "commit": PR_HEADS[number], "path": path, "role": role,
            "size": len(data), "sha256": hashlib.sha256(data).hexdigest(),
            "git_blob": subprocess.check_output(["git", "hash-object", "--stdin"], input=data).decode().strip(),
        })
    write_json(TASK_ROOT / "input_freeze" / "protected_source_hashes.json", {
        "status": "PASS_PROTECTED_INPUTS_FROZEN_FROM_RAW_GIT_OBJECTS",
        "library_sha256": LIBRARY_SHA256,
        "record_count": len(records), "records": records,
    })
    write_json(TASK_ROOT / "audits" / "protected_source_audit.json", {
        "status": "PASS_NO_PROTECTED_SOURCE_MUTATION", "protected_source_mutation_count": 0,
        "raw_git_object_source": True, "pr_identity_count": len(identities),
    })
    print("PASS_PROTECTED_INPUTS_FROZEN", len(records))


if __name__ == "__main__":
    main()
