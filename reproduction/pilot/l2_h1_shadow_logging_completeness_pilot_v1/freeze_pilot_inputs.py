#!/usr/bin/env python3
"""Freeze PR #98, protected-source, and deterministic pilot selection identities."""

from __future__ import annotations

import csv
import json
import math
from pathlib import Path
import subprocess
from typing import Any


TASK = Path(__file__).resolve().parent
REPO = TASK.parents[2]
EXPECTED_HEAD = "b47b0e924804e3e446b1f9c184ee5ea5d268d613"
EXPECTED_IDS = [10, 30, 50, 70, 90]


def command(*args: str) -> str:
    return subprocess.run(args, cwd=REPO, text=True, capture_output=True, check=True).stdout.strip()


def write_json(path: Path, value: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(value, indent=2, sort_keys=True) + "\n", encoding="utf-8", newline="\n")


def main() -> int:
    head = command("git", "rev-parse", "HEAD")
    if head != EXPECTED_HEAD:
        raise RuntimeError(f"HEAD_DRIFT:{head}")
    pr = json.loads(command(
        "gh", "pr", "view", "98", "--repo", "kenqiana04/safer-splat",
        "--json", "number,state,isDraft,headRefName,headRefOid,baseRefName,url",
    ))
    expected_pr = {
        "number": 98,
        "state": "OPEN",
        "isDraft": True,
        "headRefName": "validate-l2-h1-shadow-instrumentation-equivalence-v1",
        "headRefOid": EXPECTED_HEAD,
        "baseRefName": "implement-l2-h1-on-policy-shadow-instrumentation-v1",
    }
    identity_match = all(pr.get(key) == value for key, value in expected_pr.items())
    write_json(TASK / "audit/upstream_identity.json", {
        "repo": "kenqiana04/safer-splat",
        "pr": pr,
        "expected": expected_pr,
        "identity_match": identity_match,
        "status": "PASS_PR98_EXACT_IDENTITY" if identity_match else "BLOCKED_LOGGING_PILOT_BY_UPSTREAM_IDENTITY_DRIFT",
    })
    if not identity_match:
        return 2

    source = json.loads((REPO / "reproduction/equivalence/l2_h1_shadow_instrumentation_off_vs_on_v1/audit/protected_source_audit.json").read_text(encoding="utf-8"))
    records = []
    for frozen in source["records"]:
        path = frozen["path"]
        fields = command("git", "ls-tree", "HEAD", "--", path).split(None, 3)
        if len(fields) != 4:
            raise RuntimeError(f"PROTECTED_PATH_MISSING:{path}")
        mode, object_type, blob, _ = fields
        size = int(command("git", "cat-file", "-s", blob))
        match = object_type == "blob" and blob == frozen["expected_git_blob"] and size == frozen["expected_size"]
        records.append({
            "path": path,
            "mode": mode,
            "git_blob": blob,
            "size": size,
            "expected_git_blob": frozen["expected_git_blob"],
            "expected_size": frozen["expected_size"],
            "match": match,
        })
    protected_paths = [record["path"] for record in records]
    diff = command("git", "diff", "--name-only", "HEAD", "--", *protected_paths)
    protected = {
        "source_artifact": "reproduction/equivalence/l2_h1_shadow_instrumentation_off_vs_on_v1/audit/protected_source_audit.json",
        "protected_blob_count": int(source["protected_blob_count"]),
        "supplemental_run_py_count": int(source.get("supplemental_run_py_count", 0)),
        "audited_record_count": len(records),
        "all_match": all(record["match"] for record in records),
        "protected_path_diff_count": len(diff.splitlines()) if diff else 0,
        "controller_mutation_count": 0,
        "instrumentation_mutation_count": 0,
        "records": records,
    }
    write_json(TASK / "audit/protected_no_mutation.json", protected)
    if not protected["all_match"] or protected["protected_path_diff_count"]:
        return 3

    manifest_path = REPO / "reproduction/experiment_protocol_freeze_v1/trial_manifests/stonehenge_official100_manifest.csv"
    with manifest_path.open(encoding="utf-8", newline="") as handle:
        rows = sorted(csv.DictReader(handle), key=lambda row: int(row["trial"]))
    positions = [math.floor((j + 0.5) * len(rows) / 5) for j in range(5)]
    actual_ids = [int(rows[position]["trial"]) for position in positions]
    selection = json.loads((TASK / "pilot_trial_selection.json").read_text(encoding="utf-8"))
    if positions != [10, 30, 50, 70, 90] or actual_ids != EXPECTED_IDS or selection["selected_trial_ids"] != actual_ids:
        raise RuntimeError("FROZEN_SELECTION_MISMATCH")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
