#!/usr/bin/env python3
"""Read-only inventory of post-switch untracked files for the V2 safety gate."""

from __future__ import annotations

import hashlib
import json
import mimetypes
import os
import pathlib
import subprocess
import sys


REPO = pathlib.Path("/disk1/zlab/projects/safer-splat")
ROOT = pathlib.Path("/disk1/zlab/maintenance_records/tum_splatam_one_shot_runtime_recovery_g1_v2")
ALLOWED_PREFIX = "work/risk_aware_cbf/"


def digest(path: pathlib.Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as handle:
        for block in iter(lambda: handle.read(1024 * 1024), b""):
            h.update(block)
    return h.hexdigest()


def text_edges(path: pathlib.Path) -> tuple[list[str], list[str]]:
    try:
        lines = path.read_text(encoding="utf-8", errors="replace").splitlines()
    except OSError:
        return [], []
    return lines[:5], lines[-5:]


def detail(relative: str) -> dict[str, object]:
    path = REPO / relative
    st = path.lstat()
    first, last = text_edges(path) if path.is_file() else ([], [])
    return {
        "absolute_path": str(path),
        "relative_path": relative,
        "is_symlink": path.is_symlink(),
        "symlink_target": os.readlink(path) if path.is_symlink() else None,
        "size": st.st_size,
        "mode_octal": oct(st.st_mode & 0o7777),
        "uid": st.st_uid,
        "gid": st.st_gid,
        "mtime_ns": st.st_mtime_ns,
        "mime": mimetypes.guess_type(str(path))[0] or "application/octet-stream",
        "sha256": digest(path) if path.is_file() else None,
        "first_5_lines": first,
        "last_5_lines": last,
    }


def main() -> int:
    raw = subprocess.check_output(
        ["git", "status", "--porcelain=v2", "--untracked-files=all"],
        cwd=REPO,
        text=True,
    )
    paths = [line[2:] for line in raw.splitlines() if line.startswith("? ")]
    inside = sorted(path for path in paths if path.startswith(ALLOWED_PREFIX))
    outside = sorted(path for path in paths if not path.startswith(ALLOWED_PREFIX))
    payload = {
        "head": subprocess.check_output(["git", "rev-parse", "HEAD"], cwd=REPO, text=True).strip(),
        "untracked_total": len(paths),
        "untracked_under_authorized_work_root": len(inside),
        "untracked_outside_authorized_work_root": outside,
        "outside_details": [detail(path) for path in outside],
        "decision": "BLOCK" if outside else "AUTHORIZED_WORK_ROOT_ARCHIVE_REQUIRED",
        "reason": (
            "An untracked user file outside work/risk_aware_cbf cannot be classified as a task/report asset."
            if outside
            else "All untracked files are inside the explicitly authorized archive root."
        ),
    }
    output = ROOT / "post_sync" / "unexpected_untracked_summary.json"
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(json.dumps(payload, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    sys.exit(main())
