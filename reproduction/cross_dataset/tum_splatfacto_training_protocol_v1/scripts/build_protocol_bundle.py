#!/usr/bin/env python3
"""Build a non-self-referential bundle from raw Git blobs at one commit."""
from __future__ import annotations

import argparse
import hashlib
import json
import subprocess
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
REPO = ROOT.parents[2]
EXCLUDED = {
    "protocol_bundle_sha256.json",
    "validation_result.json",
    "protocol_hash_correction_result.json",
}


def git_text(*args: str) -> str:
    return subprocess.check_output(["git", *args], cwd=REPO, text=True).strip()


def git_bytes(*args: str) -> bytes:
    return subprocess.check_output(["git", *args], cwd=REPO)


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--canonical-commit", required=True)
    args = parser.parse_args()
    prefix = ROOT.relative_to(REPO).as_posix()
    paths = git_text("ls-tree", "-r", "--name-only", args.canonical_commit, "--", prefix).splitlines()
    hashes: dict[str, dict[str, str]] = {}
    for path in paths:
        relative = path.removeprefix(prefix + "/")
        if relative in EXCLUDED:
            continue
        blob = git_text("rev-parse", f"{args.canonical_commit}:{path}")
        hashes[relative] = {
            "git_blob_sha": blob,
            "canonical_git_blob_sha256": hashlib.sha256(git_bytes("cat-file", "blob", blob)).hexdigest(),
        }
    server = json.loads((ROOT / "canonical_hash_verification_server.json").read_text(encoding="utf-8"))
    offline = json.loads((ROOT / "offline_bundle_server_verification.json").read_text(encoding="utf-8"))
    bundle = {
        "bundle_policy": "git_blob_sha256_v1",
        "canonical_commit": args.canonical_commit,
        "canonical_blob_hashes": hashes,
        "excluded_self_referential_files": sorted(EXCLUDED),
        "server_verification_status": server["status"],
        "offline_bundle_server_verification_status": offline["status"],
        "offline_bundle_transport_method": offline["transfer_method"],
    }
    (ROOT / "protocol_bundle_sha256.json").write_text(json.dumps(bundle, indent=2, sort_keys=True) + "\n", encoding="utf-8", newline="\n")
    print("CANONICAL_PROTOCOL_BUNDLE_BUILT")


if __name__ == "__main__":
    main()
