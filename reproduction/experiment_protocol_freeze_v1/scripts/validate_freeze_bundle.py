#!/usr/bin/env python3
"""Validate Experiment Protocol Freeze V1 without running any experiment."""
from __future__ import annotations

import csv
import hashlib
import json
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[3]
OUT = ROOT / "reproduction" / "experiment_protocol_freeze_v1"
PARENT = "41ccb54d2e9f10c0b3b559431a58a5763977d462"
REQUIRED = [
    "EXPERIMENT_PROTOCOL_FROZEN_V1.md", "METRICS_AND_FAILURE_TAXONOMY.md", "config_registry.yaml",
    "dataset_registry.yaml", "trial_set_registry.yaml", "provenance/commit_reachability.json",
    "provenance/source_file_inventory.csv", "commit_lock.json", "freeze_bundle_sha256.json",
]


def sha(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def git(*args: str) -> tuple[int, str]:
    p = subprocess.run(["git", *args], cwd=ROOT, text=True, capture_output=True)
    return p.returncode, (p.stdout + p.stderr).strip()


def main() -> None:
    checks: list[dict[str, object]] = []
    def check(name: str, passed: bool, detail: str) -> None:
        checks.append({"check": name, "passed": passed, "detail": detail})

    for rel in REQUIRED:
        check(f"required:{rel}", (OUT / rel).is_file(), "required freeze artifact")
    try:
        provenance = json.loads((OUT / "provenance/commit_reachability.json").read_text(encoding="utf-8"))
        invalid = [row["module"] for row in provenance["commits"] if row["object_type"] != "commit"]
        nonancestor = [row["module"] for row in provenance["commits"] if not row["reachable_from_freeze_parent"]]
        check("all_required_commits_resolve", not invalid, ", ".join(invalid) or "all required commit objects resolve")
        check("nonancestor_history_recorded", True, ", ".join(nonancestor) or "all audited commits are ancestors")
    except Exception as exc:
        check("commit_reachability_parse", False, repr(exc))
    try:
        with (OUT / "provenance/source_file_inventory.csv").open(encoding="utf-8", newline="") as handle:
            inventory = list(csv.DictReader(handle))
        missing = [row["path"] for row in inventory if row["read_status"] != "read"]
        bad_hashes = [row["path"] for row in inventory if row["read_status"] == "read" and sha(ROOT / row["path"]) != row["sha256"]]
        check("source_inventory_hashes", not bad_hashes, ", ".join(bad_hashes) or "all source hashes match")
        check("source_inventory_readable", not missing, ", ".join(missing) or "all indexed source evidence readable")
    except Exception as exc:
        check("source_inventory_parse", False, repr(exc))
    try:
        bundle = json.loads((OUT / "freeze_bundle_sha256.json").read_text(encoding="utf-8"))
        bad = [row["path"] for row in bundle["files"] if not (OUT / row["path"]).is_file() or sha(OUT / row["path"]) != row["sha256"]]
        check("freeze_bundle_hashes", not bad, ", ".join(bad) or "bundle hashes match")
    except Exception as exc:
        check("freeze_bundle_parse", False, repr(exc))
    try:
        heldout = list(csv.DictReader((OUT / "trial_manifests/heldout_activated_16.csv").open(encoding="utf-8", newline="")))
        development = {12, 13, 14}
        ids = [int(row["trial"]) for row in heldout]
        check("heldout_count", len(ids) == 16 and len(ids) == len(set(ids)), f"heldout={ids}")
        check("development_heldout_disjoint", not development.intersection(ids), "development [12,13,14] is disjoint")
        trial20 = list(csv.DictReader((OUT / "trial_manifests/trial20_activation_contexts.csv").open(encoding="utf-8", newline="")))
        order = [int(row["activation_index"]) for row in trial20]
        check("trial20_order", order == list(range(1, 35)), f"activation indices={order}")
    except Exception as exc:
        check("trial_manifest_parse", False, repr(exc))
    code, changed = git("diff", "--name-only", PARENT, "HEAD")
    status_code, status = git("status", "--porcelain")
    working_paths = [line[3:] for line in status.splitlines() if len(line) > 3]
    observed_paths = [line for line in changed.splitlines() if line] + working_paths
    unexpected = [line for line in observed_paths if line and not line.replace("\\", "/").startswith("reproduction/experiment_protocol_freeze_v1/")]
    check("allowed_path_only", code == 0 and status_code == 0 and not unexpected, ", ".join(unexpected) or "all changed paths are inside freeze directory")
    code, parent = git("merge-base", "HEAD", PARENT)
    check("freeze_parent", code == 0 and parent == PARENT, f"merge-base={parent}")
    config_text = (OUT / "config_registry.yaml").read_text(encoding="utf-8") if (OUT / "config_registry.yaml").is_file() else ""
    check("configuration_conflicts", "configuration_conflict: true" not in config_text, "no recorded H/N/margin conflict")
    failed = [row for row in checks if not row["passed"]]
    status = "PASS_WITH_UNRESOLVED_NONCRITICAL_FIELDS" if not failed else "FAIL"
    payload = {"status": status, "freeze_parent": PARENT, "checks": checks, "failed_checks": [row["check"] for row in failed], "note": "No GPU experiment or rerun was performed. Unresolved registry fields are explicitly marked and are not inferred."}
    (OUT / "validation_result.json").write_text(json.dumps(payload, indent=2) + "\n", encoding="utf-8")
    print(status)
    if failed:
        print(json.dumps(failed, indent=2))
        sys.exit(1)


if __name__ == "__main__":
    main()
