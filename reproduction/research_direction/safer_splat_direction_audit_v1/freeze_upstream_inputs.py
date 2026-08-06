"""Freeze canonical Git identities for PR #84-#87 and protected source paths."""

from __future__ import annotations

import hashlib
import json
import subprocess
from pathlib import Path

from task_config import UPSTREAM

ROOT = Path(__file__).resolve().parents[3]
TASK_ROOT = Path(__file__).resolve().parent
FREEZE_ROOT = TASK_ROOT / "input_freeze"

PR_CONTRACTS = {
    84: {
        "base_ref": "fas-cbf-core-v1-conceptual-closure",
        "base_sha": "17805e67b75412dc21b1a5fff4143ea3bc985f7f",
        "head_ref": "fas-cbf-unified-executable-safety-certifier-v1",
    },
    85: {
        "base_ref": "fas-cbf-unified-executable-safety-certifier-v1",
        "base_sha": UPSTREAM[84],
        "head_ref": "replica-gt-executable-safety-activated-benchmark-v1",
    },
    86: {
        "base_ref": "replica-gt-executable-safety-activated-benchmark-v1",
        "base_sha": UPSTREAM[85],
        "head_ref": "replica-gt-executable-safety-method-matrix-v1",
    },
    87: {
        "base_ref": "replica-gt-executable-safety-method-matrix-v1",
        "base_sha": UPSTREAM[86],
        "head_ref": "resume-replica-gt-executable-safety-activated-benchmark-v1",
    },
}

PROTECTED_PATHS = ["cbf", "dynamics", "ellipsoids", "splat", "run.py", "visualize.py"]


def git(*args: str, raw: bool = False) -> bytes | str:
    result = subprocess.run(
        ["git", *args], cwd=ROOT, check=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE
    )
    return result.stdout if raw else result.stdout.decode("utf-8").strip()


def canonical_file_manifest(commit: str) -> list[dict[str, object]]:
    raw = git("ls-tree", "-r", "-z", commit, raw=True)
    assert isinstance(raw, bytes)
    entries: list[dict[str, object]] = []
    for record in raw.split(b"\0"):
        if not record:
            continue
        metadata, path_raw = record.split(b"\t", 1)
        mode, kind, object_id = metadata.decode("ascii").split(" ")
        path = path_raw.decode("utf-8", "surrogateescape")
        if not any(path == p or path.startswith(p + "/") for p in PROTECTED_PATHS):
            continue
        blob = git("cat-file", "blob", object_id, raw=True)
        assert isinstance(blob, bytes)
        entries.append(
            {
                "path": path,
                "mode": mode,
                "kind": kind,
                "git_object": object_id,
                "size": len(blob),
                "sha256": hashlib.sha256(blob).hexdigest(),
            }
        )
    return entries


def main() -> None:
    FREEZE_ROOT.mkdir(parents=True, exist_ok=True)
    for number, head in UPSTREAM.items():
        git("cat-file", "-e", f"{head}^{{commit}}")
        parents = str(git("show", "-s", "--format=%P", head)).split()
        contract = PR_CONTRACTS[number]
        payload = {
            "pr": number,
            "state_required": "OPEN",
            "draft_required": True,
            "merged_required": False,
            "mergeable_required": True,
            **contract,
            "head_sha": head,
            "head_object_exists": True,
            "head_parents": parents,
            "base_is_parent": contract["base_sha"] in parents,
            "canonical_tree": git("rev-parse", f"{head}^{{tree}}"),
            "frozen_from": "local canonical Git object; GitHub state verified separately in audit record",
        }
        (FREEZE_ROOT / f"pr{number}_identity.json").write_text(
            json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8", newline="\n"
        )

    manifest = canonical_file_manifest(UPSTREAM[87])
    protected = manifest
    payload = {
        "commit": UPSTREAM[87],
        "protected_paths": PROTECTED_PATHS,
        "file_count": len(protected),
        "files": protected,
        "aggregate_sha256": hashlib.sha256(
            b"".join(
                f'{row["path"]}\0{row["mode"]}\0{row["git_object"]}\0{row["sha256"]}\n'.encode("utf-8")
                for row in protected
            )
        ).hexdigest(),
    }
    (FREEZE_ROOT / "protected_source_hashes.json").write_text(
        json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8", newline="\n"
    )


if __name__ == "__main__":
    main()
