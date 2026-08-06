"""Materialize only canonical upstream Python blobs into ignored task runtime payload."""
from __future__ import annotations

import subprocess
from pathlib import Path

from common import sha256_bytes, write_json
from task_config import PR84_HEAD, PR86_HEAD, REPO_ROOT, TASK_ROOT


SOURCES = (
    (PR84_HEAD, "reproduction/cross_dataset/fas_cbf_unified_executable_safety_certifier_v1/adapters", "pr84"),
    (PR84_HEAD, "reproduction/cross_dataset/fas_cbf_unified_executable_safety_certifier_v1/certifier", "pr84"),
    (PR86_HEAD, "reproduction/cross_dataset/replica_gt_executable_safety_method_matrix_v1/alternative_library", "pr86"),
)


def git_bytes(arguments: list[str]) -> bytes:
    return subprocess.run(["git", *arguments], cwd=REPO_ROOT, check=True, capture_output=True).stdout


def main() -> None:
    records = []
    for commit, prefix, payload_name in SOURCES:
        raw = git_bytes(["ls-tree", "-r", "-z", commit, "--", prefix])
        for entry in raw.split(b"\0"):
            if not entry:
                continue
            header, path_raw = entry.split(b"\t", 1)
            mode, kind, blob = header.split(b" ")
            if kind != b"blob" or not path_raw.endswith(b".py"):
                continue
            path = path_raw.decode("utf-8")
            relative = Path(path).relative_to(prefix).as_posix()
            top = Path(prefix).name
            destination = TASK_ROOT / "runtime_payload" / payload_name / top / relative
            content = git_bytes(["cat-file", "blob", blob.decode("ascii")])
            destination.parent.mkdir(parents=True, exist_ok=True)
            destination.write_bytes(content)
            records.append({
                "commit": commit,
                "source_path": path,
                "destination": destination.relative_to(TASK_ROOT).as_posix(),
                "mode": mode.decode("ascii"),
                "git_blob": blob.decode("ascii"),
                "sha256": sha256_bytes(content),
                "size": len(content),
            })
    write_json(TASK_ROOT / "runtime_payload_manifest.json", {"status": "PASS_CANONICAL_RUNTIME_PAYLOAD", "files": records})
    print("PASS_CANONICAL_RUNTIME_PAYLOAD", len(records))


if __name__ == "__main__":
    main()
