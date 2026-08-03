#!/usr/bin/env python3
"""Freeze upstream PR #76 and Protocol V2 identities before entry decisions."""

from __future__ import annotations

import argparse
import datetime as dt
import hashlib
import json
import subprocess
from pathlib import Path


UPSTREAM = Path("reproduction/cross_dataset/retrospective_requalify_existing_gaussian_maps_protocol_v2")
PROTOCOL_ROOT = Path("reproduction/cross_dataset/gaussian_map_metric_provenance_navigation_usability_calibration_v1/protocol_v2")


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for block in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def git_blob_sha256(repo: Path, path: Path) -> str:
    data = subprocess.check_output(["git", "show", f"HEAD:{path.as_posix()}"], cwd=repo)
    return hashlib.sha256(data).hexdigest()


def run(repo: Path, *args: str) -> str:
    return subprocess.check_output(args, cwd=repo, text=True, encoding="utf-8").strip()


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--repo-root", type=Path, required=True)
    parser.add_argument("--task-root", type=Path, required=True)
    args = parser.parse_args()
    repo = args.repo_root.resolve()
    task = args.task_root.resolve()
    out = task / "input_freeze"
    out.mkdir(parents=True, exist_ok=True)

    protocol = repo / PROTOCOL_ROOT / "GAUSSIAN_MAP_LAYERED_EVALUATION_PROTOCOL_V2.md"
    checklist = repo / PROTOCOL_ROOT / "NEW_DATASET_MAP_EVALUATION_ENTRY_CHECKLIST_V2.md"
    report = repo / UPSTREAM / "REPORT_RETROSPECTIVE_REQUALIFY_EXISTING_GAUSSIAN_MAPS_UNDER_LAYERED_PROTOCOL_V2.md"
    upstream_manifest = repo / UPSTREAM / "run_manifest.json"
    handoff = repo / UPSTREAM / "eth3d_entry_handoff.json"
    pr = json.loads(run(repo, "gh", "pr", "view", "76", "--json", "state,isDraft,mergedAt,mergeable,baseRefName,headRefName,headRefOid,url"))
    manifest = json.loads(upstream_manifest.read_text(encoding="utf-8"))
    expected = {
        "protocol": "a0a02fd284c75c600095510899e2878f198d69ff088b66eccd3313275fdbde7e",
        "checklist": "7c95f787fd7fb503e4bd2726546debac53acd41c1d5f9a8dd08c29cb27735593",
        "report": "052ccdf0b63fbfdfed49a0a5f861a9f0f8bbf7e337079805cfa382cf5153b570",
        "head": "d8fc27f7fa781ceb80e66ff12ca1a93fa0fc52de",
    }
    actual = {
        "protocol": git_blob_sha256(repo, PROTOCOL_ROOT / "GAUSSIAN_MAP_LAYERED_EVALUATION_PROTOCOL_V2.md"),
        "checklist": git_blob_sha256(repo, PROTOCOL_ROOT / "NEW_DATASET_MAP_EVALUATION_ENTRY_CHECKLIST_V2.md"),
        "report": git_blob_sha256(repo, UPSTREAM / "REPORT_RETROSPECTIVE_REQUALIFY_EXISTING_GAUSSIAN_MAPS_UNDER_LAYERED_PROTOCOL_V2.md"),
        "upstream_run_manifest": git_blob_sha256(repo, UPSTREAM / "run_manifest.json"),
        "upstream_handoff": git_blob_sha256(repo, UPSTREAM / "eth3d_entry_handoff.json"),
        "head": run(repo, "git", "rev-parse", "HEAD"),
        "branch": run(repo, "git", "branch", "--show-current"),
    }
    gates = {
        "expected_hashes_match": all(actual[k] == expected[k] for k in ["protocol", "checklist", "report", "head"]),
        "pr_open": pr["state"] == "OPEN",
        "pr_draft": pr["isDraft"] is True,
        "pr_unmerged": pr["mergedAt"] is None,
        "pr_mergeable": pr["mergeable"] == "MERGEABLE",
        "pr_head_matches": pr["headRefOid"] == expected["head"],
        "pr_lineage_matches": pr["headRefName"] == "retrospective-requalify-existing-gaussian-maps-protocol-v2",
        "upstream_final_status_matches": manifest["FINAL_STATUS"] == "NO_EXISTING_LEARNED_GAUSSIAN_MAP_NAVIGATION_QUALIFIED_UNDER_PROTOCOL_V2",
        "upstream_final_decision_matches": manifest["FINAL_DECISION"] == "PROCEED_TO_NEW_DATASET_ENTRY_QUALIFICATION",
        "upstream_next_task_matches": manifest["Only_next_task"] == "ETH3D_DELIVERY_AREA_PROTOCOL_V2_ENTRY_QUALIFICATION_V1",
        "upstream_zero_download_training_controller": all(manifest["counts"][k] == 0 for k in ["download", "training", "controller", "planner_rollout", "planner_search", "optimizer", "map_modification"]),
    }
    result = {
        "status": "PASS" if all(gates.values()) else "FAIL",
        "frozen_utc": dt.datetime.now(dt.timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z"),
        "expected": expected,
        "actual": actual,
        "pr76": pr,
        "gates": gates,
        "upstream_final_status": manifest["FINAL_STATUS"],
        "upstream_final_decision": manifest["FINAL_DECISION"],
        "upstream_only_next_task": manifest["Only_next_task"],
    }
    (out / "protocol_v2_entry_input_freeze.json").write_text(json.dumps(result, indent=2) + "\n", encoding="utf-8")
    print(json.dumps({"status": result["status"], "gates": gates}, indent=2))
    return 0 if result["status"] == "PASS" else 2


if __name__ == "__main__":
    raise SystemExit(main())
