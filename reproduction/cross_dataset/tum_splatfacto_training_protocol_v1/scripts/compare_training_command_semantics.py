#!/usr/bin/env python3
"""Prove the launch-shell correction leaves the ns-train command unchanged."""
from __future__ import annotations

import argparse
import hashlib
import json
import shlex
import subprocess
from pathlib import Path


def git_blob(commit: str, path: str) -> bytes:
    return subprocess.check_output(["git", "show", f"{commit}:{path}"])


def ns_train_line(data: bytes) -> str:
    for line in data.decode("utf-8").splitlines():
        if line.startswith("ns-train "):
            return line
    raise ValueError("ns-train line not found")


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--old-commit", required=True)
    parser.add_argument("--path", required=True)
    parser.add_argument("--current", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    old = git_blob(args.old_commit, args.path)
    new = args.current.read_bytes()
    old_tokens = shlex.split(ns_train_line(old))
    new_tokens = shlex.split(ns_train_line(new))
    old_lines = old.decode("utf-8").splitlines()
    new_lines = new.decode("utf-8").splitlines()
    changed_shell_lines = [
        {"old": old_lines[index] if index < len(old_lines) else None,
         "new": new_lines[index] if index < len(new_lines) else None}
        for index in range(max(len(old_lines), len(new_lines)))
        if (old_lines[index] if index < len(old_lines) else None)
        != (new_lines[index] if index < len(new_lines) else None)
    ]
    payload = {
        "old_commit": args.old_commit,
        "old_command_blob_sha": subprocess.check_output(
            ["git", "rev-parse", f"{args.old_commit}:{args.path}"], text=True
        ).strip(),
        "old_command_sha256": hashlib.sha256(old).hexdigest(),
        "new_worktree_sha256": hashlib.sha256(new).hexdigest(),
        "old_ns_train_token_count": len(old_tokens),
        "new_ns_train_token_count": len(new_tokens),
        "ns_train_tokens_equal": old_tokens == new_tokens,
        "changed_shell_lines": changed_shell_lines,
        "training_argument_difference_count": 0 if old_tokens == new_tokens else 1,
        "training_semantics_unchanged": old_tokens == new_tokens,
    }
    args.output.write_text(json.dumps(payload, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(payload, indent=2))
    return 0 if payload["training_semantics_unchanged"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
