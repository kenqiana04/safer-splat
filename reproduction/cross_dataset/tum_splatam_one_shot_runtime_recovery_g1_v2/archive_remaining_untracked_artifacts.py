#!/usr/bin/env python3
"""Archive the explicitly authorized post-switch untracked checkout paths.

This script is intentionally server-rooted and only removes a source after the
complete frozen set has been archived, extracted, and verified.
"""

from __future__ import annotations

import hashlib
import json
import mimetypes
import os
import pathlib
import shutil
import stat
import subprocess
import sys
import tarfile
from dataclasses import dataclass, asdict


REPO = pathlib.Path("/disk1/zlab/projects/safer-splat")
ONESHOT = pathlib.Path("/disk1/zlab/maintenance_records/tum_splatam_one_shot_runtime_recovery_g1_v2")
ARCHIVE = ONESHOT / "user_file_archive_remaining"
ALLOWED_FILE = ".vscode/extensions.json"
ALLOWED_PREFIX = "work/risk_aware_cbf/"
EXPECTED_HEAD = "f63b4c496861c4f8881348d74244c1ff9a528d51"
EXPECTED_BLOBS = {
    "splat/distances.py": "d7f17b67df40e36e458c7a5ed77c4a04659c6f35",
    "splat/gsplat_utils.py": "782c38eca50e78c605085b481155ed61e4607336",
    "cbf/cbf_utils.py": "7c6e1300b125cc0a2a950ac2835a1fbe3d0de113",
    "reproduction/cross_dataset/safer_world_frame_stable_ellipsoid_hessian_runtime_correction_v1/SAFER_ELLIPSOID_QUERY_NUMERICAL_CONTRACT_V2.json": "7a0d85b0b334c2e94ccc23b033d8453322d72fe1",
}
OLD_TAR = ONESHOT / "user_file_archive" / "risk_aware_cbf_untracked_reports.tar"
OLD_TAR_SHA256 = "1aedcc3a8c60f63caeceeaedb235c12ead23a251266c34b06c2fd7f6e91ffe27"


@dataclass(frozen=True)
class Entry:
    relative_path: str
    absolute_path: str
    file_type: str
    is_regular: bool
    is_directory: bool
    is_symlink: bool
    symlink_target: str | None
    size: int
    mode_octal: str
    uid: int
    gid: int
    mtime_ns: int
    sha256: str | None
    blake2b: str | None
    mime: str | None
    line_count: int | None


def run(*args: str) -> str:
    return subprocess.check_output(args, cwd=REPO, text=True).strip()


def hashes(path: pathlib.Path) -> tuple[str, str]:
    sha = hashlib.sha256()
    blake = hashlib.blake2b()
    with path.open("rb") as handle:
        for block in iter(lambda: handle.read(1024 * 1024), b""):
            sha.update(block)
            blake.update(block)
    return sha.hexdigest(), blake.hexdigest()


def is_text(path: pathlib.Path) -> bool:
    with path.open("rb") as handle:
        return b"\0" not in handle.read(65536)


def safe_relative(relative: str) -> pathlib.PurePosixPath:
    pure = pathlib.PurePosixPath(relative)
    if pure.is_absolute() or ".." in pure.parts or not pure.parts:
        raise RuntimeError(f"unsafe archive path: {relative!r}")
    return pure


def classify(path: pathlib.Path) -> Entry:
    st = path.lstat()
    regular = stat.S_ISREG(st.st_mode)
    directory = stat.S_ISDIR(st.st_mode)
    symlink = stat.S_ISLNK(st.st_mode)
    if not (regular or directory or symlink):
        raise RuntimeError(f"unsupported artifact file type: {path}")
    rel = path.relative_to(REPO).as_posix()
    safe_relative(rel)
    target = os.readlink(path) if symlink else None
    if symlink:
        resolved = (path.parent / target).resolve(strict=False)
        try:
            resolved.relative_to(REPO)
        except ValueError as exc:
            raise RuntimeError(f"external symlink is not authorized: {rel} -> {target}") from exc
    sha = blake = mime = None
    lines = None
    if regular:
        sha, blake = hashes(path)
        mime = mimetypes.guess_type(str(path))[0] or "application/octet-stream"
        if is_text(path):
            with path.open("rb") as handle:
                lines = sum(block.count(b"\n") for block in iter(lambda: handle.read(1024 * 1024), b""))
    return Entry(
        relative_path=rel,
        absolute_path=str(path),
        file_type="regular" if regular else "directory" if directory else "symlink",
        is_regular=regular,
        is_directory=directory,
        is_symlink=symlink,
        symlink_target=target,
        size=st.st_size,
        mode_octal=oct(stat.S_IMODE(st.st_mode)),
        uid=st.st_uid,
        gid=st.st_gid,
        mtime_ns=st.st_mtime_ns,
        sha256=sha,
        blake2b=blake,
        mime=mime,
        line_count=lines,
    )


def git_untracked() -> list[str]:
    if run("git", "rev-parse", "HEAD") != EXPECTED_HEAD:
        raise RuntimeError("authoritative HEAD identity mismatch")
    for path, expected in EXPECTED_BLOBS.items():
        if run("git", "rev-parse", f"HEAD:{path}") != expected:
            raise RuntimeError(f"target blob mismatch: {path}")
    if run("git", "diff", "--name-only") or run("git", "diff", "--cached", "--name-only"):
        raise RuntimeError("tracked or staged checkout modification detected")
    raw = run("git", "status", "--porcelain=v2", "--untracked-files=all")
    lines = raw.splitlines() if raw else []
    if any(not line.startswith("? ") for line in lines):
        raise RuntimeError("unexpected non-untracked porcelain entry")
    paths = sorted(line[2:] for line in lines)
    if not paths:
        raise RuntimeError("no remaining untracked paths to archive")
    if len(paths) != len(set(paths)):
        raise RuntimeError("duplicate path in frozen untracked status")
    for path in paths:
        safe_relative(path)
        if path != ALLOWED_FILE and not path.startswith(ALLOWED_PREFIX):
            raise RuntimeError(f"unrecognized untracked path outside authorization: {path}")
    if ALLOWED_FILE not in paths:
        raise RuntimeError("authorized editor configuration is missing from frozen set")
    known = REPO / ALLOWED_FILE
    if known.lstat().st_size != 59 or hashes(known)[0] != "cdfa302bad7cd93e2e1a5abae2e499ed6997b4c6a15c04ccdd451282e5276956":
        raise RuntimeError("authorized editor configuration identity mismatch")
    return paths


def compare_regular(left: pathlib.Path, right: pathlib.Path) -> None:
    with left.open("rb") as a, right.open("rb") as b:
        while True:
            ba = a.read(1024 * 1024)
            bb = b.read(1024 * 1024)
            if ba != bb:
                raise RuntimeError(f"byte comparison failed: {left} != {right}")
            if not ba:
                return


def main() -> int:
    if ARCHIVE.exists():
        raise RuntimeError(f"refusing to overwrite evidence root: {ARCHIVE}")
    if not OLD_TAR.is_file() or hashes(OLD_TAR)[0] != OLD_TAR_SHA256:
        raise RuntimeError("previous three-report archive is missing or has wrong SHA-256")
    paths = git_untracked()
    entries = [classify(REPO / relative) for relative in paths]
    ARCHIVE.mkdir(parents=True)
    (ARCHIVE / "source_manifest").mkdir()
    (ARCHIVE / "archive_tree").mkdir()
    frozen = ARCHIVE / "authorized_untracked_paths.txt"
    frozen.write_text("\n".join(paths) + "\n", encoding="utf-8")
    (ARCHIVE / "source_manifest" / "manifest.json").write_text(
        json.dumps([asdict(entry) for entry in entries], indent=2, sort_keys=True) + "\n", encoding="utf-8"
    )
    tar_path = ARCHIVE / "remaining_checkout_untracked.tar"
    with tarfile.open(tar_path, "w", format=tarfile.PAX_FORMAT, dereference=False) as archive:
        for entry in entries:
            source = REPO / entry.relative_path
            archive.add(source, arcname=entry.relative_path, recursive=False)
    tar_sha, tar_blake = hashes(tar_path)
    extracted = ARCHIVE / "extracted_verification"
    extracted.mkdir()
    with tarfile.open(tar_path, "r") as archive:
        names = archive.getnames()
        if sorted(names) != sorted(paths):
            raise RuntimeError("tar path set does not exactly match frozen path set")
        for name in names:
            safe_relative(name)
        # Names and source-link targets were validated above; fully_trusted is
        # required here to verify the original mode and nanosecond mtime.
        archive.extractall(extracted, filter="fully_trusted")
    verification: list[dict[str, object]] = []
    for entry in entries:
        source = REPO / entry.relative_path
        restored = extracted / entry.relative_path
        rst = restored.lstat()
        if stat.S_IMODE(rst.st_mode) != int(entry.mode_octal, 8):
            raise RuntimeError(f"mode mismatch: {entry.relative_path}")
        if rst.st_mtime_ns != entry.mtime_ns:
            raise RuntimeError(f"mtime mismatch: {entry.relative_path}")
        if entry.is_regular:
            sha, blake = hashes(restored)
            if sha != entry.sha256 or blake != entry.blake2b or restored.lstat().st_size != entry.size:
                raise RuntimeError(f"identity mismatch after extraction: {entry.relative_path}")
            compare_regular(source, restored)
        elif entry.is_symlink and os.readlink(restored) != entry.symlink_target:
            raise RuntimeError(f"symlink target mismatch: {entry.relative_path}")
        verification.append({"path": entry.relative_path, "verified": True})
    total_regular_bytes = sum(entry.size for entry in entries if entry.is_regular)
    summary = {
        "status": "PASS_REMAINING_USER_ARTIFACTS_ARCHIVED_AND_VERIFIED",
        "frozen_path_count": len(entries),
        "regular_file_count": sum(entry.is_regular for entry in entries),
        "symlink_count": sum(entry.is_symlink for entry in entries),
        "directory_count": sum(entry.is_directory for entry in entries),
        "total_regular_file_bytes": total_regular_bytes,
        "tar_path": str(tar_path),
        "tar_sha256": tar_sha,
        "tar_blake2b": tar_blake,
        "old_archive_tar_sha256": OLD_TAR_SHA256,
        "extraction_verified": True,
        "path_traversal_verified": True,
        "verification_count": len(verification),
    }
    (ARCHIVE / "verification.json").write_text(json.dumps(verification, indent=2) + "\n", encoding="utf-8")
    (ARCHIVE / "summary.json").write_text(json.dumps(summary, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    for entry in entries:
        source = REPO / entry.relative_path
        if entry.is_regular or entry.is_symlink:
            source.unlink()
    for directory in sorted({(REPO / entry.relative_path).parent for entry in entries}, key=lambda p: len(p.parts), reverse=True):
        if directory not in (REPO / ".vscode", REPO / "work", REPO / "work" / "risk_aware_cbf"):
            try:
                directory.rmdir()
            except OSError:
                pass
    if run("git", "status", "--porcelain=v2", "--untracked-files=all"):
        raise RuntimeError("checkout remains non-clean after exact authorized relocation")
    print(json.dumps(summary, sort_keys=True))
    return 0


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except Exception as exc:
        print(f"BLOCKED_BY_REMAINING_USER_ARTIFACT_ARCHIVE_FAILURE: {exc}", file=sys.stderr)
        raise SystemExit(1)
