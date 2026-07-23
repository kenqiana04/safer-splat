#!/usr/bin/env python3
"""Resume the V2 remaining-artifact archive after a compatible extraction retry."""

from __future__ import annotations

import hashlib
import json
import os
import pathlib
import stat
import subprocess
import sys
import tarfile


REPO = pathlib.Path("/disk1/zlab/projects/safer-splat")
ROOT = pathlib.Path("/disk1/zlab/maintenance_records/tum_splatam_one_shot_runtime_recovery_g1_v2/user_file_archive_remaining")
TAR = ROOT / "remaining_checkout_untracked.tar"
FROZEN = ROOT / "authorized_untracked_paths.txt"
MANIFEST = ROOT / "source_manifest" / "manifest.json"
EXTRACTED = ROOT / "extracted_verification_attempt_02"


def safe(relative: str) -> pathlib.PurePosixPath:
    path = pathlib.PurePosixPath(relative)
    if path.is_absolute() or ".." in path.parts or not path.parts:
        raise RuntimeError(f"unsafe archive member: {relative!r}")
    return path


def hashes(path: pathlib.Path) -> tuple[str, str]:
    sha, blake = hashlib.sha256(), hashlib.blake2b()
    with path.open("rb") as handle:
        for block in iter(lambda: handle.read(1024 * 1024), b""):
            sha.update(block)
            blake.update(block)
    return sha.hexdigest(), blake.hexdigest()


def bytes_equal(left: pathlib.Path, right: pathlib.Path) -> bool:
    with left.open("rb") as a, right.open("rb") as b:
        while True:
            aa, bb = a.read(1024 * 1024), b.read(1024 * 1024)
            if aa != bb:
                return False
            if not aa:
                return True


def main() -> int:
    if EXTRACTED.exists():
        raise RuntimeError(f"refusing to overwrite retry evidence: {EXTRACTED}")
    paths = [line for line in FROZEN.read_text(encoding="utf-8").splitlines() if line]
    records = json.loads(MANIFEST.read_text(encoding="utf-8"))
    if sorted(paths) != sorted(record["relative_path"] for record in records):
        raise RuntimeError("frozen path list and source manifest differ")
    if len(paths) != len(set(paths)):
        raise RuntimeError("duplicate frozen path")
    for path in paths:
        safe(path)
    tar_sha, tar_blake = hashes(TAR)
    EXTRACTED.mkdir()
    with tarfile.open(TAR, "r") as archive:
        members = archive.getmembers()
        names = [member.name for member in members]
        if sorted(names) != sorted(paths):
            raise RuntimeError("tar members do not exactly match frozen paths")
        for member in members:
            safe(member.name)
        archive.extractall(EXTRACTED)
    verified: list[dict[str, object]] = []
    total_bytes = 0
    for record in records:
        relative = record["relative_path"]
        source = REPO / relative
        restored = EXTRACTED / relative
        rst = restored.lstat()
        if stat.S_IMODE(rst.st_mode) != int(record["mode_octal"], 8):
            raise RuntimeError(f"mode mismatch: {relative}")
        if rst.st_mtime_ns != record["mtime_ns"]:
            raise RuntimeError(f"mtime mismatch: {relative}: {rst.st_mtime_ns} != {record['mtime_ns']}")
        if record["is_regular"]:
            sha, blake = hashes(restored)
            if (sha, blake, rst.st_size) != (record["sha256"], record["blake2b"], record["size"]):
                raise RuntimeError(f"content identity mismatch: {relative}")
            if not bytes_equal(source, restored):
                raise RuntimeError(f"byte comparison mismatch: {relative}")
            total_bytes += rst.st_size
        elif record["is_symlink"]:
            if os.readlink(restored) != record["symlink_target"]:
                raise RuntimeError(f"symlink target mismatch: {relative}")
        verified.append({"path": relative, "verified": True})
    summary = {
        "status": "PASS_REMAINING_USER_ARTIFACTS_ARCHIVED_AND_VERIFIED",
        "frozen_path_count": len(records),
        "regular_file_count": sum(record["is_regular"] for record in records),
        "symlink_count": sum(record["is_symlink"] for record in records),
        "directory_count": sum(record["is_directory"] for record in records),
        "total_regular_file_bytes": total_bytes,
        "tar_path": str(TAR),
        "tar_sha256": tar_sha,
        "tar_blake2b": tar_blake,
        "extracted_verification_path": str(EXTRACTED),
        "path_traversal_verified": True,
        "all_source_archive_byte_comparisons": True,
    }
    (ROOT / "verification_attempt_02.json").write_text(json.dumps(verified, indent=2) + "\n", encoding="utf-8")
    (ROOT / "summary.json").write_text(json.dumps(summary, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    for record in records:
        source = REPO / record["relative_path"]
        if record["is_regular"] or record["is_symlink"]:
            source.unlink()
    protected = {REPO / ".vscode", REPO / "work", REPO / "work" / "risk_aware_cbf"}
    parents = {((REPO / record["relative_path"]).parent) for record in records}
    for directory in sorted(parents, key=lambda path: len(path.parts), reverse=True):
        if directory not in protected:
            try:
                directory.rmdir()
            except OSError:
                pass
    status = subprocess.check_output(
        ["git", "status", "--porcelain=v2", "--untracked-files=all"], cwd=REPO, text=True
    )
    if status:
        raise RuntimeError("checkout is not clean after exact frozen-path relocation")
    print(json.dumps(summary, sort_keys=True))
    return 0


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except Exception as exc:
        print(f"BLOCKED_BY_REMAINING_USER_ARTIFACT_ARCHIVE_FAILURE: {exc}", file=sys.stderr)
        raise SystemExit(1)
