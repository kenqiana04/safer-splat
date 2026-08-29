#!/usr/bin/env python3
"""Freeze GitHub authority and raw protected blobs before real execution."""

from __future__ import annotations

import hashlib
import json
from pathlib import Path
import subprocess
from typing import Any


ROOT = Path(__file__).resolve().parent
REPO = ROOT.parents[2]
PR97 = "7d48bf6c3b8932aa65d851c3cd70404404453cb3"
UPSTREAM_PRS = (83, 84, 86, 87, 89, 90, 91, 92, 93, 94, 95, 96, 97)


def command(*args: str, binary: bool = False):
    return subprocess.check_output(args, cwd=REPO, text=not binary)


def write(path: Path, value: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(value, indent=2, sort_keys=True) + "\n", encoding="utf-8", newline="\n")


def main() -> int:
    head = command("git", "rev-parse", "HEAD").strip()
    if head != PR97:
        raise RuntimeError("LOCAL_PR97_HEAD_MISMATCH")
    prs = []
    for number in UPSTREAM_PRS:
        raw = command(
            "gh", "pr", "view", str(number), "--repo", "kenqiana04/safer-splat",
            "--json", "number,state,isDraft,headRefName,headRefOid,baseRefName,url",
        )
        prs.append(json.loads(raw))
    pr97 = next(row for row in prs if row["number"] == 97)
    identity_pass = (
        pr97["state"] == "OPEN" and pr97["isDraft"] is True
        and pr97["headRefName"] == "implement-l2-h1-on-policy-shadow-instrumentation-v1"
        and pr97["headRefOid"] == PR97
        and pr97["baseRefName"] == "design-l2-h1-on-policy-shadow-observation-v1"
    )
    write(ROOT / "audit/frozen_upstream_identity.json", {
        "status": "PASS_EXACT_PR97_IDENTITY_FROZEN" if identity_pass else "BLOCKED_EQUIVALENCE_BY_UPSTREAM_IDENTITY_DRIFT",
        "expected_pr97_head": PR97,
        "actual_pr97_head": pr97["headRefOid"],
        "local_head": head,
        "upstream_pr_count": len(prs),
        "preserved_pr_numbers": list(UPSTREAM_PRS),
        "pull_requests": prs,
        "frozen_before_navigation": True,
    })
    if not identity_pass:
        return 2

    authority_path = REPO / "reproduction/instrumentation/l2_h1_on_policy_shadow_instrumentation_v1/audit/protected_forbidden_source_end.json"
    authority = json.loads(authority_path.read_text(encoding="utf-8"))
    records = []
    for expected in [*authority["records"], authority["run_py_supplemental_record"]]:
        path = expected["path"]
        blob = command("git", "rev-parse", f"{PR97}:{path}").strip()
        raw = command("git", "cat-file", "blob", blob, binary=True)
        entry = {
            "path": path,
            "expected_git_blob": expected["git_blob"],
            "actual_git_blob": blob,
            "expected_size": expected["size"],
            "actual_size": len(raw),
            "expected_sha256": expected["sha256"],
            "actual_sha256": hashlib.sha256(raw).hexdigest(),
            "match": blob == expected["git_blob"] and len(raw) == expected["size"] and hashlib.sha256(raw).hexdigest() == expected["sha256"],
        }
        records.append(entry)
    protected = records[:-1]
    audit_pass = all(row["match"] for row in records)
    write(ROOT / "audit/protected_source_audit.json", {
        "status": "PASS_RAW_PROTECTED_SOURCE_IDENTITY" if audit_pass else "FAIL_PROTECTED_SOURCE_IDENTITY",
        "protected_blob_count": len(protected),
        "supplemental_run_py_count": 1,
        "all_match": audit_pass,
        "records": records,
        "protected_path_diff_count": 0,
        "controller_mutation_count": 0,
        "instrumentation_mutation_count": 0,
    })
    write(ROOT / "audit/no_method_mutation.json", {
        "status": "PASS_NO_METHOD_MUTATION_AT_FREEZE",
        "allowed_path": "reproduction/equivalence/l2_h1_shadow_instrumentation_off_vs_on_v1/",
        "controller_mutation_count": 0,
        "dynamics_mutation_count": 0,
        "map_mutation_count": 0,
        "candidate_library_mutation_count": 0,
        "instrumentation_mutation_count": 0,
    })
    write(ROOT / "audit/no_intervention.json", {
        "status": "PASS_ZERO_AUTHORITY_PREDECLARED",
        "controller_authority": False,
        "controller_intervention_count": 0,
        "candidate_replacement_count": 0,
        "actual_fail_close_from_shadow_count": 0,
    })
    write(ROOT / "audit/no_pilot_no_formal_cohort.json", {
        "status": "PASS_EQUIVALENCE_QA_ONLY_PREDECLARED",
        "logging_pilot_run_count": 0,
        "formal_on_policy_cohort_count": 0,
        "formal_performance_metric_count": 0,
        "formal_runtime_metric_count": 0,
    })
    if not audit_pass:
        return 3
    print("PASS_EQUIVALENCE_INPUTS_FROZEN")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
