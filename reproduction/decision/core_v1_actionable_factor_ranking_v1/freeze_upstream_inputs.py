"""Freeze only PR #84-#90 identities and protected PR #90 input bytes."""

from __future__ import annotations

import hashlib
import json
import subprocess
from pathlib import Path

from task_config import EXPECTED_PRS, TASK_ROOT, UPSTREAM_HEAD, UPSTREAM_ROOT


def run(*args: str) -> str:
    return subprocess.check_output(args, text=True, encoding="utf-8").strip()


def write_json(path: Path, payload: object) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def freeze_pr_identities() -> None:
    for number, (branch, oid) in EXPECTED_PRS.items():
        payload = json.loads(run(
            "gh", "pr", "view", str(number), "--repo", "kenqiana04/safer-splat",
            "--json", "number,state,isDraft,mergedAt,mergeable,baseRefName,baseRefOid,headRefName,headRefOid,url",
        ))
        assert payload["number"] == number
        assert payload["state"] == "OPEN" and payload["isDraft"] is True
        assert payload["mergedAt"] is None and payload["mergeable"] == "MERGEABLE"
        assert payload["headRefName"] == branch and payload["headRefOid"] == oid
        payload["freeze_status"] = "PASS_LIVE_PR_IDENTITY_MATCH"
        payload["freeze_scope"] = "identity only; no PR mutation"
        write_json(TASK_ROOT / "input_freeze" / f"pr{number}_identity.json", payload)


def freeze_protected_sources() -> None:
    prior = json.loads((UPSTREAM_ROOT / "input_freeze" / "protected_source_hashes.json").read_text(encoding="utf-8"))
    records = []
    for record in prior["records"]:
        raw = subprocess.check_output(["git", "show", f"{record['commit']}:{record['path']}"])
        blob = run("git", "rev-parse", f"{record['commit']}:{record['path']}")
        assert blob == record["git_blob"]
        assert len(raw) == record["size"]
        assert hashlib.sha256(raw).hexdigest() == record["sha256"]
        records.append({**record, "verification": "PASS_RAW_GIT_OBJECT_MATCH"})
    write_json(TASK_ROOT / "input_freeze" / "protected_source_hashes.json", {
        "status": "PASS_PROTECTED_SOURCE_BYTES_PRESERVED",
        "source_pr90_head": UPSTREAM_HEAD,
        "record_count": len(records),
        "records": records,
        "scope": "read-only source-byte verification; no upstream or method mutation",
    })


def main() -> None:
    freeze_pr_identities()
    freeze_protected_sources()
    print("PASS_UPSTREAM_IDENTITIES_AND_PROTECTED_SOURCES_FROZEN")


if __name__ == "__main__":
    main()
