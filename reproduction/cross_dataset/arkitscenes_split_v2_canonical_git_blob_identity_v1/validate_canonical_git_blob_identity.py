"""Validate contract raw identities against exact committed Git blob bytes."""

from __future__ import annotations

import argparse
import json
from pathlib import Path

from canonical_identity_common import (CONTRACT_RELATIVE, HELDOUT_RELATIVE, TRAIN_RELATIVE,
    eol_profile, git_blob, git_file, sha256, write_json)


def main() -> int:
    parser = argparse.ArgumentParser(); parser.add_argument("--repo", type=Path, required=True); parser.add_argument("--commit", required=True); parser.add_argument("--output", type=Path, required=True); args = parser.parse_args()
    contract = json.loads(git_file(args.repo, args.commit, CONTRACT_RELATIVE).decode("utf-8"))
    entries = []
    for name, relative, legacy_key in (("train", TRAIN_RELATIVE, "train_manifest_sha256"), ("heldout", HELDOUT_RELATIVE, "heldout_manifest_sha256")):
        oid, blob = git_blob(args.repo, args.commit, relative); contract_item = contract["manifest_identities"][name]
        entries.append({"name": name, "path": relative.as_posix(), "git_blob_oid": oid, "git_blob_sha256": sha256(blob), "contract_git_blob_oid": contract_item["git_blob_oid"], "contract_git_blob_sha256": contract_item["git_blob_sha256"], "contract_legacy_crlf_sha256": contract_item["legacy_generation_identity"]["legacy_worktree_crlf_sha256"], "contract_top_level_sha256": contract[legacy_key], "eol": eol_profile(blob), "contract_matches_exact_blob": oid == contract_item["git_blob_oid"] and sha256(blob) == contract_item["git_blob_sha256"] and sha256(blob) == contract[legacy_key]})
    valid = contract.get("identity_policy") == "CANONICAL_GIT_BLOB_BYTES_SHA256_V1" and all(item["contract_matches_exact_blob"] and item["eol"]["lf_only"] and item["eol"]["final_lf"] for item in entries)
    payload = {"status": "PASS_CANONICAL_GIT_BLOB_IDENTITY" if valid else "BLOCKED_BY_CROSS_PLATFORM_MANIFEST_IDENTITY_CANONICALIZATION", "commit": args.commit, "identity_policy": contract.get("identity_policy"), "entries": entries, "authority": "SHA-256(git cat-file blob <commit>:<path>)"}
    write_json(args.output, payload); print(payload["status"])
    return 0 if valid else 2


if __name__ == "__main__": raise SystemExit(main())
