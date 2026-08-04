#!/usr/bin/env python3
"""Reconstruct the frozen official 3DGS Git object from GitHub tar bytes.

GitHub source tarballs omit the repository metadata and submodule worktrees.  This
utility extracts the ordinary tree, installs the four frozen gitlinks into the
index, verifies the exact upstream tree object, and writes the exact upstream
commit payload.  It never reads or modifies the scientific input dataset.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import os
import subprocess
import tarfile
from pathlib import Path


COMMIT = "54c035f7834b564019656c3e3fcc3646292f727d"
TREE = "3e76b1a6180966faccc4c1cdf1bf95a68350c48f"
PARENT = "3dc0b75595ac113db0c49ca51a9be33e1ed7e876"
GITLINKS = {
    "SIBR_viewers": "d8856f60c5384cc1975439193bb627d77d917d77",
    "submodules/diff-gaussian-rasterization": "9c5c2028f6fbee2be239bc4c9421ff894fe4fbe0",
    "submodules/fused-ssim": "1272e21a282342e89537159e4bad508b19b34157",
    "submodules/simple-knn": "86710c2d4b46680c02301765dd79e465819c8f19",
}


def run(*args: str, cwd: Path, input_bytes: bytes | None = None) -> str:
    proc = subprocess.run(
        args,
        cwd=cwd,
        input=input_bytes,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        check=False,
    )
    if proc.returncode:
        raise RuntimeError(
            f"command failed ({proc.returncode}): {' '.join(args)}\n"
            + proc.stderr.decode("utf-8", "replace")
        )
    return proc.stdout.decode("utf-8", "strict").strip()


def safe_extract(tar_path: Path, destination: Path) -> str:
    destination.mkdir(parents=True, exist_ok=False)
    with tarfile.open(tar_path, "r:gz") as archive:
        members = archive.getmembers()
        roots = {m.name.split("/", 1)[0] for m in members if m.name}
        if len(roots) != 1:
            raise RuntimeError(f"expected one archive prefix, found {sorted(roots)}")
        prefix = next(iter(roots))
        for member in members:
            parts = Path(member.name).parts
            if not parts or parts[0] != prefix:
                raise RuntimeError(f"unexpected archive member: {member.name}")
            relative = Path(*parts[1:])
            if not relative.parts:
                continue
            if relative.is_absolute() or ".." in relative.parts:
                raise RuntimeError(f"unsafe archive member: {member.name}")
            member.name = relative.as_posix()
            if member.issym() or member.islnk():
                target = Path(member.linkname)
                if target.is_absolute() or ".." in target.parts:
                    raise RuntimeError(f"unsafe archive link: {member.name}")
        archive.extractall(destination, members=members)
    return prefix


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--tar", type=Path, required=True)
    parser.add_argument("--destination", type=Path, required=True)
    parser.add_argument("--identity-out", type=Path, required=True)
    args = parser.parse_args()

    if args.destination.exists():
        raise RuntimeError(f"destination must not exist: {args.destination}")
    tar_sha256 = hashlib.sha256(args.tar.read_bytes()).hexdigest()
    prefix = safe_extract(args.tar, args.destination)

    run("git", "init", "-q", cwd=args.destination)
    run("git", "config", "core.autocrlf", "false", cwd=args.destination)
    run("git", "add", "-A", cwd=args.destination)
    for path, sha in GITLINKS.items():
        run(
            "git",
            "update-index",
            "--add",
            "--cacheinfo",
            f"160000,{sha},{path}",
            cwd=args.destination,
        )

    actual_tree = run("git", "write-tree", cwd=args.destination)
    if actual_tree != TREE:
        raise RuntimeError(f"tree mismatch: expected {TREE}, got {actual_tree}")

    commit_payload = (
        f"tree {TREE}\n"
        f"parent {PARENT}\n"
        "author alanvin <laanvin@gmail.com> 1730291962 +0100\n"
        "committer alanvin <laanvin@gmail.com> 1730291962 +0100\n"
        "\n"
        "fix submodule name in environment.yml\n"
    ).encode("utf-8")
    actual_commit = run(
        "git", "hash-object", "-t", "commit", "-w", "--stdin",
        cwd=args.destination,
        input_bytes=commit_payload,
    )
    if actual_commit != COMMIT:
        raise RuntimeError(f"commit mismatch: expected {COMMIT}, got {actual_commit}")
    run("git", "update-ref", "refs/heads/frozen", COMMIT, cwd=args.destination)
    run("git", "checkout", "-q", "--detach", COMMIT, cwd=args.destination)

    license_sha256 = hashlib.sha256(
        (args.destination / "LICENSE.md").read_bytes()
    ).hexdigest()
    status = run("git", "status", "--porcelain=v1", cwd=args.destination)
    if status:
        raise RuntimeError(f"reconstructed source is dirty:\n{status}")

    record = {
        "schema_version": 1,
        "authority": "https://github.com/graphdeco-inria/gaussian-splatting",
        "archive_prefix": prefix,
        "archive_sha256": tar_sha256,
        "commit": actual_commit,
        "tree": actual_tree,
        "parent": PARENT,
        "detached_head": True,
        "source_status_clean": True,
        "license_path": "LICENSE.md",
        "license_sha256": license_sha256,
        "submodule_gitlinks": GITLINKS,
        "reconstruction_changes_scientific_source": False,
    }
    args.identity_out.parent.mkdir(parents=True, exist_ok=True)
    args.identity_out.write_text(
        json.dumps(record, indent=2, sort_keys=True) + "\n", encoding="utf-8"
    )
    print("OFFICIAL_SOURCE_RECONSTRUCTION_PASS")
    print(json.dumps(record, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
