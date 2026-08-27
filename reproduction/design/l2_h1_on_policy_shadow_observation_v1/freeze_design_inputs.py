#!/usr/bin/env python3
"""Freeze PR lineage and raw protected-source identities for this design-only task."""

from __future__ import annotations

import argparse
import hashlib
import json
import subprocess
from datetime import datetime, timezone
from pathlib import Path


TASK_DIR = Path(__file__).resolve().parent
REPO = TASK_DIR.parents[2]
AUTHORITY = REPO / "reproduction/replay/l2_h1_shadow_frozen_replay_v1/audit/protected_source_audit.json"
EXPECTED_PRS = {
    83: "17805e67b75412dc21b1a5fff4143ea3bc985f7f",
    84: "04ebca2b1b35124ad0e61ebed96e491c9edae4bb",
    86: "d4f20f44a810afc2d6379853a286a3e18b175221",
    87: "fbe67f0c607add7f8049d4ce75e8f9e1ae8498d9",
    89: "047513b5e612f91e63ab1e7054815615cb455fd7",
    90: "48db34d4e61f019fcd2b578c04cc87eefb00747a",
    91: "e8ec67d5585f9634ae6a5d4991eac5f9e4abfbae",
    92: "dfd9bce2633e542fdb72a1805f79cc4feeeebc3a",
    93: "1df09c56eedb53d46f9347695026086319738a89",
    94: "9bffdd2db585974ee61684cebfc99229aa52c47c",
    95: "a7fd936804284a299467f1bfcc76deab12fdf0c3",
}


def run(*args: str, binary: bool = False) -> bytes | str:
    completed = subprocess.run(
        list(args), cwd=REPO, check=True, capture_output=True, text=not binary
    )
    return completed.stdout if not binary else completed.stdout


def pr_identity(number: int) -> dict:
    raw = run(
        "gh", "pr", "view", str(number), "--repo", "kenqiana04/safer-splat",
        "--json", "number,state,isDraft,headRefName,headRefOid,baseRefName,url",
    )
    item = json.loads(raw)
    expected = EXPECTED_PRS[number]
    item["expected_head"] = expected
    item["identity_match"] = (
        item["headRefOid"] == expected and item["state"] == "OPEN" and item["isDraft"] is True
    )
    if not item["identity_match"]:
        raise SystemExit(f"PR #{number} identity drift: {item}")
    return item


def protected_records() -> list[dict]:
    authority = json.loads(AUTHORITY.read_text(encoding="utf-8"))
    records = []
    for expected in authority["records"]:
        path = expected["path"]
        commit = expected["commit"]
        tree = str(run("git", "ls-tree", commit, "--", path)).strip()
        if not tree:
            raise SystemExit(f"protected path missing at {commit}: {path}")
        metadata, actual_path = tree.split("\t", 1)
        mode, object_type, blob = metadata.split()
        if object_type != "blob" or actual_path != path:
            raise SystemExit(f"unexpected tree entry for {path}: {tree}")
        data = run("git", "cat-file", "blob", blob, binary=True)
        actual = {
            "commit": commit,
            "path": path,
            "role": expected["role"],
            "mode": mode,
            "git_blob": blob,
            "size": len(data),
            "sha256": hashlib.sha256(data).hexdigest(),
        }
        for key in ("mode", "git_blob", "size", "sha256"):
            if actual[key] != expected[key]:
                raise SystemExit(f"protected identity mismatch {path} {key}: {actual[key]} != {expected[key]}")
        actual["verification"] = "PASS_RAW_GIT_OBJECT_SIZE_MODE_IDENTITY"
        records.append(actual)
    return records


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--phase", choices=("start", "end"), required=True)
    args = parser.parse_args()
    audit_dir = TASK_DIR / "audit"
    audit_dir.mkdir(parents=True, exist_ok=True)
    prs = [pr_identity(number) for number in EXPECTED_PRS]
    head = str(run("git", "rev-parse", "HEAD")).strip()
    remote_head = str(run("git", "rev-parse", "origin/l2-h1-shadow-frozen-replay-v1")).strip()
    expected = EXPECTED_PRS[95]
    if args.phase == "start" and (head != expected or remote_head != expected):
        raise SystemExit(f"local/remote upstream mismatch: head={head} remote={remote_head}")
    upstream = {
        "repository": "kenqiana04/safer-splat",
        "checked_at_utc": datetime.now(timezone.utc).isoformat(),
        "upstream_pr_count": len(prs),
        "prs": prs,
        "pr95_expected_head": expected,
        "pr95_actual_head": prs[-1]["headRefOid"],
        "pr95_state": prs[-1]["state"],
        "pr95_is_draft": prs[-1]["isDraft"],
        "local_head_at_audit": head,
        "remote_pr95_branch_head": remote_head,
        "status": "PASS_UPSTREAM_PR_IDENTITY",
    }
    (audit_dir / "upstream_pr_identity.json").write_text(
        json.dumps(upstream, indent=2, sort_keys=True) + "\n", encoding="utf-8", newline="\n"
    )
    records = protected_records()
    protected = {
        "phase": args.phase,
        "checked_at_utc": datetime.now(timezone.utc).isoformat(),
        "manifest_authority": str(AUTHORITY.relative_to(REPO)).replace("\\", "/"),
        "protected_blob_count": len(records),
        "protected_path_diff_count": 0,
        "records": records,
        "status": f"PASS_PROTECTED_SOURCE_{args.phase.upper()}_AUDIT",
    }
    (audit_dir / f"protected_source_{args.phase}.json").write_text(
        json.dumps(protected, indent=2, sort_keys=True) + "\n", encoding="utf-8", newline="\n"
    )
    print(upstream["status"])
    print(protected["status"], len(records))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
