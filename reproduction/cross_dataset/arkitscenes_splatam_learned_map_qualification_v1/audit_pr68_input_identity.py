"""Fail-closed byte-identity audit for the PR #68 V2 mapping manifests."""

from __future__ import annotations

import argparse
import hashlib
import json
import subprocess
from pathlib import Path


def sha256_bytes(value: bytes) -> str:
    return hashlib.sha256(value).hexdigest()


def audit_one(repo: Path, relative: str, declared: str) -> dict[str, object]:
    path = repo / relative
    worktree = path.read_bytes()
    object_id = subprocess.check_output(["git", "-C", str(repo), "rev-parse", f"HEAD:{relative}"], text=True).strip()
    blob = subprocess.check_output(["git", "-C", str(repo), "cat-file", "blob", object_id])
    return {
        "path": relative,
        "declared_contract_sha256": declared,
        "worktree_sha256": sha256_bytes(worktree),
        "git_blob_oid": object_id,
        "git_blob_sha256": sha256_bytes(blob),
        "worktree_equals_git_blob": worktree == blob,
        "declared_matches_git_blob": declared == sha256_bytes(blob),
        "line_endings": {
            "git_blob_lf": blob.count(b"\n"),
            "git_blob_crlf": blob.count(b"\r\n"),
        },
    }


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--repo", required=True, type=Path)
    parser.add_argument("--output", required=True, type=Path)
    args = parser.parse_args()
    contract_path = args.repo / "reproduction/cross_dataset/arkitscenes_spatial_group_split_contract_v2/v2_split/arkitscenes_spatial_group_split_contract_v2.json"
    contract = json.loads(contract_path.read_text(encoding="utf-8"))
    root = "reproduction/cross_dataset/arkitscenes_spatial_group_split_contract_v2/v2_split"
    records = [
        audit_one(args.repo, f"{root}/arkitscenes_train_manifest_v2.csv", str(contract["train_manifest_sha256"])),
        audit_one(args.repo, f"{root}/arkitscenes_heldout_manifest_v2.csv", str(contract["heldout_manifest_sha256"])),
    ]
    valid = all(bool(record["declared_matches_git_blob"]) and bool(record["worktree_equals_git_blob"]) for record in records)
    payload = {
        "status": "ARKITSCENES_MAPPING_INPUT_IDENTITY_PASS" if valid else "BLOCKED_BY_ARKITSCENES_MAPPING_INPUT_IDENTITY_MISMATCH",
        "source_head": subprocess.check_output(["git", "-C", str(args.repo), "rev-parse", "HEAD"], text=True).strip(),
        "contract_path": str(contract_path.relative_to(args.repo)),
        "contract_sha256": sha256_bytes(contract_path.read_bytes()),
        "video_id": contract["video_id"],
        "records": records,
        "interpretation": "raw Git blob identity is authoritative for this task; semantic CSV equality cannot substitute for a declared byte SHA-256",
    }
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(payload["status"])
    return 0 if valid else 2


if __name__ == "__main__":
    raise SystemExit(main())
