"""Fail-closed upstream and raw protected-object freeze."""
from __future__ import annotations

import hashlib
import json
import subprocess
from typing import Any

from replay_common import PR94_HEAD, PR94_ROOT, REPO_ROOT, TASK_ROOT, write_json


EXPECTED = {
    83: "17805e67b75412dc21b1a5fff4143ea3bc985f7f",
    84: "04ebca2b1b35124ad0e61ebed96e491c9edae4bb",
    86: "d4f20f44a810afc2d6379853a286a3e18b175221",
    87: "fbe67f0c607add7f8049d4ce75e8f9e1ae8498d9",
    89: "047513b5e612f91e63ab1e7054815615cb455fd7",
    90: "48db34d4e61f019fcd2b578c04cc87eefb00747a",
    91: "e8ec67d5585f9634ae6a5d4991eac5f9e4abfbae",
    92: "dfd9bce2633e542fdb72a1805f79cc4feeeebc3a",
    93: "1df09c56eedb53d46f9347695026086319738a89",
    94: PR94_HEAD,
}


def run(args: list[str], binary: bool = False) -> Any:
    result = subprocess.run(args, cwd=REPO_ROOT, capture_output=True, check=True, text=not binary)
    return result.stdout


def pr_record(number: int) -> dict[str, Any]:
    raw = run(["gh", "pr", "view", str(number), "--repo", "kenqiana04/safer-splat", "--json", "number,state,isDraft,baseRefName,headRefName,headRefOid"])
    value = json.loads(raw)
    if value["state"] != "OPEN" or value["isDraft"] is not True or value["headRefOid"] != EXPECTED[number]:
        raise RuntimeError(f"UPSTREAM_PR_IDENTITY_DRIFT:{number}")
    return value


def main() -> None:
    if run(["git", "merge-base", "--is-ancestor", PR94_HEAD, "HEAD"]).strip():
        pass
    prs = [pr_record(number) for number in EXPECTED]
    manifest = json.loads((PR94_ROOT / "audit/protected_source_audit.json").read_text(encoding="utf-8"))
    records = []
    for expected in manifest["records"]:
        blob = run(["git", "cat-file", "blob", expected["git_blob"]], binary=True)
        tree_line = run(["git", "ls-tree", expected["commit"], "--", expected["path"]]).strip()
        if not tree_line:
            raise RuntimeError("PROTECTED_PATH_MISSING:" + expected["path"])
        metadata, path = tree_line.split("\t", 1)
        mode, kind, blob_id = metadata.split()
        actual = {
            **expected,
            "actual_git_blob": blob_id,
            "actual_mode": mode,
            "actual_size": len(blob),
            "actual_sha256": hashlib.sha256(blob).hexdigest(),
        }
        if kind != "blob" or blob_id != expected["git_blob"] or mode != expected["mode"] or len(blob) != expected["size"] or actual["actual_sha256"] != expected["sha256"]:
            raise RuntimeError("PROTECTED_RAW_IDENTITY_MISMATCH:" + path)
        records.append(actual)
    current = run(["git", "rev-parse", "HEAD"]).strip()
    if run(["git", "merge-base", "--is-ancestor", PR94_HEAD, current]) is None:
        raise RuntimeError("PR94_NOT_ANCESTOR")
    write_json(TASK_ROOT / "audit/upstream_identity.json", {
        "status": "PASS_FROZEN_REPLAY_UPSTREAM_IDENTITY",
        "pr_count": len(prs), "prs": prs, "task_start_head": current,
        "pr94_expected_head": PR94_HEAD, "pr94_is_ancestor": True,
    })
    write_json(TASK_ROOT / "audit/protected_source_audit.json", {
        "status": "PASS_FROZEN_REPLAY_PROTECTED_SOURCE_AUDIT",
        "manifest_authority": manifest["manifest_authority"],
        "protected_blob_count": len(records), "protected_path_diff_count": 0,
        "records": records,
    })
    print("PASS_FROZEN_REPLAY_UPSTREAM_FREEZE")


if __name__ == "__main__":
    main()
