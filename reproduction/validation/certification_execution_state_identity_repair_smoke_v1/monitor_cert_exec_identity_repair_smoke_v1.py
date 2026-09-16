#!/usr/bin/env python3
"""Compact, outcome-blind monitor for the future frozen smoke."""

from __future__ import annotations
import json
from pathlib import Path
import subprocess

ROOT = Path("/disk1/zlab/v3_repair_records/cert_exec_identity_repair_smoke_v1_retry1_20260916")
SUMMARY = ROOT / "SMOKE_REPAIR_V1_COLLECTION_SUMMARY.json"
SESSION = "cert-exec-identity-repair-smoke-v1"

running = subprocess.run(["tmux", "has-session", "-t", SESSION], capture_output=True).returncode == 0
summary = json.loads(SUMMARY.read_text()) if SUMMARY.is_file() else {}
gpu = subprocess.run(["nvidia-smi", "--query-gpu=index,utilization.gpu,memory.used,memory.total", "--format=csv,noheader,nounits"], text=True, capture_output=True).stdout.splitlines()
gpu1 = next((line for line in gpu if line.strip().startswith("1,")), "unavailable")
print(json.dumps({
    "session": "RUNNING" if running else "STOPPED",
    "completed_trials": summary.get("trials_completed", []),
    "completed_cycles": summary.get("completed_cycles", 0),
    "trace_records": summary.get("trace_records", 0),
    "plant_commits": summary.get("plant_commits", 0),
    "status": summary.get("status", "NOT_AVAILABLE"),
    "gpu1": gpu1,
}, sort_keys=True))
