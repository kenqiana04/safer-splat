#!/usr/bin/env python3
"""Capture the local freeze environment; no experiment is executed."""
from __future__ import annotations

import json
import os
import platform
import subprocess
import sys
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parents[3]
OUT = ROOT / "reproduction" / "experiment_protocol_freeze_v1"


def command(*args: str) -> str:
    run = subprocess.run(args, cwd=ROOT, text=True, capture_output=True)
    return (run.stdout + run.stderr).strip()


def main() -> None:
    payload = {
        "repository_remote": command("git", "remote", "get-url", "origin"),
        "freeze_parent": "41ccb54d2e9f10c0b3b559431a58a5763977d462",
        "freeze_head_before_commit": command("git", "rev-parse", "HEAD"),
        "branch": command("git", "branch", "--show-current"),
        "timestamp_utc": datetime.now(timezone.utc).isoformat(),
        "python": sys.version,
        "python_executable": sys.executable,
        "conda_prefix": os.environ.get("CONDA_PREFIX", "unresolved"),
        "os": platform.platform(),
        "gpu": "unresolved_not_queried_no_gpu_experiment",
        "git_status_before_commit": command("git", "status", "--short"),
        "experiment_execution": "none; protocol/provenance freeze only",
        "status_after_commit": "filled_after_commit_in_git_metadata_not_mutated_in_lock",
    }
    (OUT / "commit_lock.json").write_text(json.dumps(payload, indent=2) + "\n", encoding="utf-8")


if __name__ == "__main__":
    main()
