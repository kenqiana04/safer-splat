#!/usr/bin/env python3
"""Collect Git-backed, pre-freeze Replica/TUM provenance without executing data work."""
from __future__ import annotations

import csv
import hashlib
import json
import subprocess
from pathlib import Path

ROOT = Path(__file__).resolve().parents[3]
OUT = ROOT / "reproduction" / "experiment_protocol_freeze_v1" / "provenance"
SOURCES = [
    ("replica_formal_report", "replica_apartment_0", "fe250df543aa158557c176ee4f87dc131bb61e60", "safer-replica-frozen-render-protocol-v1", "work/risk_aware_cbf/REPORT_REPLICA_FORMAL_METRIC_PREPROCESSING_V1.md", "formal_replica_rgbd_protocol_and_integrity_gate"),
    ("replica_py39_closure", "replica_apartment_0", "c3d26ebe1fc010247e2de20a028d288f01d64c1f", "safer-replica-habitat-py39-closure", "work/risk_aware_cbf/REPORT_REPLICA_HABITAT_PY39_CLOSURE.md", "renderer_environment_scene_navmesh_egl_closure"),
    ("tum_metric_report", "tum_metric_candidate", "3e22a7cae6f4c3c2c192cc2d7af3c9fbd607a0a3", "safer-cross-dataset-metric-preprocessing", "work/risk_aware_cbf/REPORT_CROSS_DATASET_METRIC_PREPROCESSING.md", "metric_rgbd_pose_transforms_preprocessing"),
    ("tum_transforms_immutability_reference", "tum_metric_candidate", "fe250df543aa158557c176ee4f87dc131bb61e60", "safer-replica-frozen-render-protocol-v1", "work/risk_aware_cbf/REPORT_REPLICA_FORMAL_METRIC_PREPROCESSING_V1.md", "formal_reported_tum_transforms_sha256"),
    ("cross_dataset_g0_g1_audit", "cross_dataset_global", "aa9d7a00b3db1b7723867351594a669d61f61bf2", "safer-baseline-cross-dataset-g0-g1", "work/risk_aware_cbf/REPORT_SAFER_BASELINE_CROSS_DATASET_G0_G1.md", "historical_g0_g1_boundary_audit"),
]


def git(*args: str) -> tuple[int, bytes, str]:
    process = subprocess.run(["git", *args], cwd=ROOT, capture_output=True)
    return process.returncode, process.stdout, process.stderr.decode("utf-8", errors="replace").strip()


def source_bytes(commit: str, path: str) -> bytes:
    code, data, stderr = git("show", f"{commit}:{path}")
    if code:
        raise RuntimeError(stderr)
    return data


def main() -> None:
    OUT.mkdir(parents=True, exist_ok=True)
    evidence_rows: list[dict[str, object]] = []
    commits: dict[str, dict[str, object]] = {}
    for evidence_id, dataset_id, commit, branch, path, role in SOURCES:
        object_code, object_type, _ = git("cat-file", "-t", commit)
        ancestor_code, _, _ = git("merge-base", "--is-ancestor", commit, "HEAD")
        try:
            data = source_bytes(commit, path)
            exists, digest, size, status = True, hashlib.sha256(data).hexdigest(), len(data), "read"
        except RuntimeError:
            exists, digest, size, status = False, "", "", "unresolved_missing"
        evidence_rows.append({
            "evidence_id": evidence_id, "dataset_id": dataset_id, "path": path,
            "source_type": "git_historical_report", "source_branch": branch,
            "source_commit": commit, "git_tracked": "true", "exists": str(exists).lower(),
            "size_bytes": size, "sha256": digest, "evidence_role": role,
            "read_status": status, "notes": "Historical external-lineage provenance; no branch was checked out, merged, or cherry-picked.",
        })
        if commit not in commits:
            commits[commit] = {
                "commit": commit, "branch": branch, "object_exists": object_code == 0 and object_type.decode().strip() == "commit",
                "ancestor_of_freeze_head": ancestor_code == 0, "available_via_git_show": exists,
                "evidence_paths": [path], "lineage_status": "historical_external_lineage_provenance" if ancestor_code else "historical_external_lineage_provenance",
            }
        elif path not in commits[commit]["evidence_paths"]:
            commits[commit]["evidence_paths"].append(path)
    fields = ["evidence_id", "dataset_id", "path", "source_type", "source_branch", "source_commit", "git_tracked", "exists", "size_bytes", "sha256", "evidence_role", "read_status", "notes"]
    with (OUT / "cross_dataset_evidence_inventory.csv").open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=fields)
        writer.writeheader()
        writer.writerows(evidence_rows)
    (OUT / "cross_dataset_commit_reachability.json").write_text(json.dumps({"freeze_head": subprocess.check_output(["git", "rev-parse", "HEAD"], cwd=ROOT, text=True).strip(), "commits": list(commits.values())}, indent=2) + "\n", encoding="utf-8")


if __name__ == "__main__":
    main()
