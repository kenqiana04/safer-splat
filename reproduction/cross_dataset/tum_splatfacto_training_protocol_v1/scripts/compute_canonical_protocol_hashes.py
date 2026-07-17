#!/usr/bin/env python3
"""Inspect protocol bytes through Git blobs without changing protocol content."""
from __future__ import annotations

import argparse
import hashlib
import json
import subprocess
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
REPO = ROOT.parents[2]
ARTIFACTS = ("exact_training_command.sh", "frozen_training_config.json")


def git_bytes(*args: str) -> bytes:
    return subprocess.check_output(["git", *args], cwd=REPO)


def git_text(*args: str) -> str:
    return git_bytes(*args).decode("utf-8").strip()


def digest(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def audit(commit: str, name: str) -> dict[str, object]:
    relative = f"{ROOT.relative_to(REPO).as_posix()}/{name}"
    blob = git_text("rev-parse", f"{commit}:{relative}")
    raw = git_bytes("cat-file", "blob", blob)
    lf = raw.replace(b"\r\n", b"\n").replace(b"\r", b"\n")
    crlf = lf.replace(b"\n", b"\r\n")
    result: dict[str, object] = {
        "git_blob_sha": blob,
        "raw_byte_count": len(raw),
        "raw_crlf_count": raw.count(b"\r\n"),
        "raw_lf_count": raw.count(b"\n"),
        "final_newline": raw.endswith(b"\n"),
        "canonical_git_blob_sha256": digest(raw),
        "lf_normalized_sha256": digest(lf),
        "crlf_normalized_sha256": digest(crlf),
        "windows_worktree_sha256": digest((ROOT / name).read_bytes()),
    }
    if name.endswith(".json"):
        base = json.loads(raw.decode("utf-8"))
        current = json.loads((ROOT / name).read_text(encoding="utf-8"))
        result.update({
            "json_deep_equality": base == current,
            "key_count": len(base),
            "semantic_difference_count": 0 if base == current else 1,
        })
    else:
        result["semantic_equivalence"] = lf == (ROOT / name).read_bytes().replace(b"\r\n", b"\n").replace(b"\r", b"\n")
    return result


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--commit", required=True)
    parser.add_argument("--output", type=Path)
    args = parser.parse_args()
    payload = {
        "policy_version": "git_blob_sha256_v1",
        "protocol_commit": args.commit,
        "artifacts": {name: audit(args.commit, name) for name in ARTIFACTS},
    }
    text = json.dumps(payload, indent=2, sort_keys=True) + "\n"
    if args.output:
        args.output.write_text(text, encoding="utf-8", newline="\n")
    else:
        print(text, end="")


if __name__ == "__main__":
    main()
