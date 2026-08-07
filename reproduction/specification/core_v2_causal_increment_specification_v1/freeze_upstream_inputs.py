"""Freeze upstream PR identities and verify raw Git blob bytes without mutation."""

from __future__ import annotations

import hashlib
import json
import subprocess
import time
from pathlib import Path

from task_config import EXPECTED_PRS, PR92_TASK_ROOT, REPO_ROOT, SUPPLEMENTAL_SOURCE_PATHS, TASK_ROOT


def run_bytes(*args: str) -> bytes:
    return subprocess.check_output(list(args), cwd=REPO_ROOT)


def git_blob(commit: str, path: str) -> tuple[str, bytes]:
    spec = f"{commit}:{path}"
    oid = run_bytes("git", "rev-parse", spec).decode("ascii").strip()
    data = run_bytes("git", "cat-file", "blob", spec)
    return oid, data


def github_pr(number: int) -> dict[str, object]:
    raw: bytes | None = None
    last_error = ""
    for attempt in range(4):
        result = subprocess.run(
            ["gh", "api", f"repos/kenqiana04/safer-splat/pulls/{number}"],
            cwd=REPO_ROOT,
            capture_output=True,
            check=False,
        )
        if result.returncode == 0:
            raw = result.stdout
            break
        last_error = result.stderr.decode("utf-8", errors="replace").strip()
        if attempt < 3:
            time.sleep(1.0)
    if raw is None:
        raise RuntimeError(f"GITHUB_PR_IDENTITY_QUERY_FAILED:{number}:{last_error}")
    payload = json.loads(raw.decode("utf-8"))
    return {
        "number": payload["number"],
        "url": payload["html_url"],
        "state": payload["state"].upper(),
        "isDraft": payload["draft"],
        "baseRefName": payload["base"]["ref"],
        "baseRefOid": payload["base"]["sha"],
        "headRefName": payload["head"]["ref"],
        "headRefOid": payload["head"]["sha"],
        "title": payload["title"],
    }


def main() -> None:
    identities: list[dict[str, object]] = []
    for number, (branch, oid) in EXPECTED_PRS.items():
        actual = github_pr(number)
        if actual["state"] != "OPEN" or actual["isDraft"] is not True:
            raise RuntimeError(f"UPSTREAM_PR_STATE_DRIFT:{number}")
        if actual["headRefName"] != branch or actual["headRefOid"] != oid:
            if number == 92:
                raise RuntimeError("BLOCKED_CORE_V2_SPEC_BY_UPSTREAM_IDENTITY_DRIFT")
            raise RuntimeError(f"UPSTREAM_PR_IDENTITY_DRIFT:{number}")
        identities.append(actual)

    frozen = {
        "status": "PASS_FROZEN_UPSTREAM_IDENTITY",
        "repository": "kenqiana04/safer-splat",
        "upstream_pr_count": len(identities),
        "pr92_expected_head": EXPECTED_PRS[92][1],
        "pr92_actual_head": identities[-1]["headRefOid"],
        "pull_requests": identities,
    }
    (TASK_ROOT / "FROZEN_UPSTREAM_IDENTITY.json").write_text(
        json.dumps(frozen, indent=2, sort_keys=True) + "\n", encoding="utf-8"
    )

    prior = json.loads((PR92_TASK_ROOT / "input_freeze/protected_source_hashes.json").read_text(encoding="utf-8"))
    if prior.get("record_count") != 17 or len(prior.get("records", [])) != 17:
        raise RuntimeError(f"PROTECTED_BLOB_SET_COUNT_DRIFT:{prior.get('record_count')}")
    protected_records: list[dict[str, object]] = []
    for record in prior["records"]:
        oid, data = git_blob(record["commit"], record["path"])
        digest = hashlib.sha256(data).hexdigest()
        if oid != record["git_blob"] or digest != record["sha256"] or len(data) != record["size"]:
            raise RuntimeError(f"PROTECTED_BLOB_IDENTITY_MISMATCH:{record['path']}")
        protected_records.append({**record, "verification": "PASS_RAW_GIT_OBJECT_MATCH"})

    supplemental: list[dict[str, object]] = []
    for path in SUPPLEMENTAL_SOURCE_PATHS:
        oid, data = git_blob(EXPECTED_PRS[84][1], path)
        supplemental.append(
            {
                "commit": EXPECTED_PRS[84][1],
                "path": path,
                "git_blob": oid,
                "sha256": hashlib.sha256(data).hexdigest(),
                "size": len(data),
                "verification": "PASS_RAW_GIT_OBJECT_MATCH",
            }
        )
    audit = {
        "status": "PASS_CORE_V2_PROTECTED_SOURCE_AUDIT",
        "protected_blob_count": len(protected_records),
        "protected_records": protected_records,
        "supplemental_evidence_blob_count": len(supplemental),
        "supplemental_evidence_records": supplemental,
        "scope": "read-only raw Git object verification; supplemental evidence does not alter the protected count",
    }
    (TASK_ROOT / "PROTECTED_SOURCE_AUDIT.json").write_text(
        json.dumps(audit, indent=2, sort_keys=True) + "\n", encoding="utf-8"
    )
    print("PASS_CORE_V2_UPSTREAM_AND_PROTECTED_FREEZE")


if __name__ == "__main__":
    main()
