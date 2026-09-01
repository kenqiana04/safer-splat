#!/usr/bin/env python3
"""Verify every frozen collection commitment without reading formal statuses."""

from __future__ import annotations

import argparse
import json
import subprocess
from pathlib import Path

from analysis_common import (
    COLLECTION_LOCK_SHA256, DATA_ROLE, EXECUTION_LOCK_SHA256, EXPECTED_PR101_HEAD,
    ORDERED_RESULT_COMMITMENT_SHA256, PROTOCOL_SHA256, RAW_MANIFEST_SHA256,
    RESULT_COMMITMENT_FILE_SHA256, atomic_write_json, file_sha256, load_json, semantic_sha256,
)


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--repo-root", type=Path, required=True)
    parser.add_argument("--server-root", required=True)
    parser.add_argument("--ssh-host", default="zlab-4090")
    parser.add_argument("--upstream-head", required=True)
    parser.add_argument("--unlock-output", type=Path, required=True)
    parser.add_argument("--identity-output", type=Path, required=True)
    args = parser.parse_args()
    protocol_dir = args.repo_root / "reproduction/protocol/l2_h1_prospective_shadow_cohort_v1"
    collection_dir = args.repo_root / "reproduction/collection/l2_h1_prospective_shadow_cohort_v1"
    if args.upstream_head != EXPECTED_PR101_HEAD:
        raise RuntimeError("PR101 identity mismatch")
    protocol_lock = load_json(protocol_dir / "PROTOCOL_LOCK.json")
    per_file = {}
    for name in protocol_lock["per_file_sha256"]:
        relative = f"reproduction/protocol/l2_h1_prospective_shadow_cohort_v1/{name}"
        raw_blob = subprocess.check_output(["git", "-C", str(args.repo_root), "cat-file", "blob", f"{EXPECTED_PR101_HEAD}:{relative}"])
        import hashlib
        per_file[name] = hashlib.sha256(raw_blob).hexdigest()
    if per_file != protocol_lock["per_file_sha256"]:
        raise RuntimeError("protocol raw file hash mismatch")
    if semantic_sha256([{"path": name, "sha256": per_file[name]} for name in sorted(per_file)]) != PROTOCOL_SHA256:
        raise RuntimeError("protocol combined hash mismatch")
    execution = load_json(collection_dir / "COLLECTION_EXECUTION_LOCK.json")
    unhashed = dict(execution)
    unhashed.pop("collection_execution_lock_sha256", None)
    unhashed.pop("combined_collection_execution_sha256", None)
    if semantic_sha256(unhashed) != EXECUTION_LOCK_SHA256:
        raise RuntimeError("collection execution lock mismatch")
    def git_blob_sha(relative: str) -> str:
        import hashlib
        raw = subprocess.check_output(["git", "-C", str(args.repo_root), "cat-file", "blob", f"{EXPECTED_PR101_HEAD}:{relative}"])
        return hashlib.sha256(raw).hexdigest()

    collection_prefix = "reproduction/collection/l2_h1_prospective_shadow_cohort_v1"
    if git_blob_sha(f"{collection_prefix}/FORMAL_COLLECTION_LOCK.json") != COLLECTION_LOCK_SHA256:
        raise RuntimeError("formal collection lock mismatch")
    if git_blob_sha(f"{collection_prefix}/raw_artifact_manifest.csv") != RAW_MANIFEST_SHA256:
        raise RuntimeError("raw artifact manifest mismatch")
    commitment_path = collection_dir / "scientific_outcome_artifact_commitment.json"
    if git_blob_sha(f"{collection_prefix}/scientific_outcome_artifact_commitment.json") != RESULT_COMMITMENT_FILE_SHA256:
        raise RuntimeError("result commitment file mismatch")
    commitment = load_json(commitment_path)
    if semantic_sha256(commitment["ordered_result_artifacts"]) != ORDERED_RESULT_COMMITMENT_SHA256:
        raise RuntimeError("ordered result commitment mismatch")
    collection_lock = load_json(collection_dir / "FORMAL_COLLECTION_LOCK.json")
    qc = load_json(collection_dir / "formal_blind_qc_summary.json")
    progress = load_json(collection_dir / "formal_collection_progress.json")
    validation = load_json(collection_dir / "validation_result.json")
    if not (collection_lock["formal_trial_count"] == 100 and collection_lock["qc_completeness"] is True and collection_lock["collection_deviations"] == []):
        raise RuntimeError("collection lock/QC mismatch")
    if not (qc["data_role"] == DATA_ROLE and qc["formal_trial_count"] == 100 and qc["aggregate_error_count"] == 0 and qc["post_data_failure_count"] == 0):
        raise RuntimeError("compact collection QC mismatch")
    if not (progress["state"] == "LOCKED" and progress["completed_trial_count"] == 100 and progress["running_trial_count"] == 0):
        raise RuntimeError("collection progress mismatch")
    if validation.get("pass") is not True:
        raise RuntimeError("collection validator mismatch")
    remote_code = r'''import hashlib,json,pathlib,sys
root=pathlib.Path(sys.argv[1]); c=json.loads((root/'scientific_outcome_artifact_commitment.json').read_text())
def sha(p):
 h=hashlib.sha256()
 with p.open('rb') as f:
  for b in iter(lambda:f.read(1048576),b''): h.update(b)
 return h.hexdigest()
for row in c['ordered_result_artifacts']:
 p=root/row['relative_path']
 if not p.is_file() or p.stat().st_size!=row['size'] or sha(p)!=row['sha256']: raise SystemExit(2)
print(json.dumps({'verified_result_artifact_count':len(c['ordered_result_artifacts']),'formal_status_values_read':0}))'''
    import base64
    encoded = base64.b64encode(remote_code.encode("utf-8")).decode("ascii")
    remote_command = f"python3 -c \"import base64;exec(base64.b64decode('{encoded}'))\" {args.server_root}"
    remote = subprocess.check_output(["ssh", args.ssh_host, remote_command], text=True)
    remote_result = json.loads(remote.strip())
    if remote_result != {"verified_result_artifact_count": 100, "formal_status_values_read": 0}:
        raise RuntimeError("remote artifact commitment verification mismatch")
    unlock = {
        "schema_version": "L2_H1_FORMAL_SCIENTIFIC_ANALYSIS_UNLOCK_V1", "upstream_PR101_head": args.upstream_head,
        "protocol_sha": PROTOCOL_SHA256, "collection_execution_lock_sha": EXECUTION_LOCK_SHA256,
        "collection_lock_sha": COLLECTION_LOCK_SHA256, "raw_manifest_sha": RAW_MANIFEST_SHA256,
        "result_commitment_file_sha": RESULT_COMMITMENT_FILE_SHA256, "ordered_result_commitment_sha": ORDERED_RESULT_COMMITMENT_SHA256,
        "formal_trial_count": 100, "formal_result_artifact_count": 100, "formal_data_role": DATA_ROLE,
        "formal_qa_namespace_isolation": True, "collection_qc_valid": True, "post_data_deviation_count": 0,
        "outcomes_read_before_unlock": False, "real_outcome_rows_read_before_unlock": 0, "unlock_authorized": True,
    }
    identity = dict(unlock)
    identity.update({"server_root": args.server_root, "remote_result_artifact_hash_verification": True,
                     "scientific_analysis_unlock_sha256": semantic_sha256(unlock)})
    atomic_write_json(args.unlock_output, unlock)
    atomic_write_json(args.identity_output, identity)
    print(json.dumps({"unlock_authorized": True, "outcomes_read_before_unlock": False, "verified_result_artifact_count": 100}, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
