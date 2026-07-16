#!/usr/bin/env python3
"""Validate the recorded Git-blob canonicalization evidence without training."""
from __future__ import annotations

import csv
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
REQUIRED = ("exact_training_command.sh", "frozen_training_config.json")
PASS = "PASS_READY_FOR_FORMAL_TRAINING_EXECUTION_AFTER_HASH_CANONICALIZATION"


def load(name: str) -> dict:
    return json.loads((ROOT / name).read_text(encoding="utf-8"))


def main() -> None:
    policy = load("canonical_hash_policy.json")
    windows = load("canonical_hash_verification_windows.json")
    server = load("canonical_hash_verification_server.json")
    inventory = {row["path"]: row for row in csv.DictReader((ROOT / "canonical_hash_inventory.csv").open(encoding="utf-8", newline=""))}
    checks: list[tuple[str, bool]] = [
        ("canonical_policy", policy.get("policy_version") == "git_blob_sha256_v1" and policy.get("canonical_source") == "exact_git_blob_bytes" and policy.get("text_eol") == "lf"),
        ("directory_eol_contract", (ROOT / ".gitattributes").read_text(encoding="utf-8") == "*.sh text eol=lf\n*.json text eol=lf\n*.yaml text eol=lf\n*.yml text eol=lf\n*.csv text eol=lf\n*.md text eol=lf\n*.py text eol=lf\n"),
    ]
    for name in REQUIRED:
        record, win, srv = inventory.get(name, {}), windows.get("artifacts", {}).get(name, {}), server.get("artifacts", {}).get(name, {})
        checks.extend([
            (f"{name}: inventory", bool(record.get("git_blob_sha")) and record.get("canonical_git_blob_sha256") == win.get("canonical_git_blob_sha256")),
            (f"{name}: old_hash", record.get("old_hash_classification") == "CONFIRMED_EOL_ONLY_CRLF_VS_LF" and win.get("crlf_normalized_sha256") == record.get("old_windows_crlf_sha256")),
            (f"{name}: server", srv.get("working_tree_sha256") == record.get("canonical_git_blob_sha256") and srv.get("git_blob_sha") == record.get("git_blob_sha")),
            (f"{name}: semantic", bool(win.get("json_deep_equality")) if name.endswith(".json") else bool(win.get("semantic_equivalence"))),
        ])
    status = PASS if all(ok for _, ok in checks) and server.get("status") == "PASS" else "BLOCKED_BY_CANONICAL_HASH_MISMATCH"
    result = {
        "status": status,
        "checks": [{"check": name, "passed": ok} for name, ok in checks],
        "training_iterations_executed": 0,
        "run_directory_created": False,
        "checkpoint_created": False,
        "safer_executed": False,
        "G1_allowed": False,
        "unresolved_critical_fields": [] if status == PASS else ["canonical Git blob and server checkout evidence"],
        "unresolved_noncritical_fields": [],
    }
    (ROOT / "protocol_hash_correction_result.json").write_text(json.dumps(result, indent=2, sort_keys=True) + "\n", encoding="utf-8", newline="\n")
    print(status)
    if status != PASS:
        raise SystemExit(status)


if __name__ == "__main__":
    main()
