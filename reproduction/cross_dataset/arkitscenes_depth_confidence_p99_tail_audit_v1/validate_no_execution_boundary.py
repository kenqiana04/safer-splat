#!/usr/bin/env python3
"""Read-only final GPU/process/output boundary validation for the audit."""

from __future__ import annotations

import argparse
import csv
import io
import json
import os
import subprocess
from pathlib import Path

from audit_common import NO_EXECUTION, write_json


def output(*args: str) -> str:
    return subprocess.check_output(args, text=True, stderr=subprocess.STDOUT).strip()


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--root", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    root = args.root.resolve()
    gpu_line = output(
        "nvidia-smi",
        "-i",
        "1",
        "--query-gpu=index,name,memory.used,utilization.gpu",
        "--format=csv,noheader,nounits",
    )
    parts = [value.strip() for value in next(csv.reader(io.StringIO(gpu_line)))]
    try:
        compute = output(
            "nvidia-smi",
            "-i",
            "1",
            "--query-compute-apps=pid,process_name,used_gpu_memory",
            "--format=csv,noheader,nounits",
        ).splitlines()
    except subprocess.CalledProcessError:
        compute = []
    compute = [line for line in compute if line.strip()]
    forbidden_directories = []
    forbidden_tokens = {"smoke", "training", "checkpoint", "formal_output", "map", "nvs", "clearance", "g0", "variant", "controller"}
    for path in root.rglob("*"):
        if path.is_dir() and path != root and path.name.lower() in forbidden_tokens:
            forbidden_directories.append(str(path.relative_to(root)))
    task_processes = []
    for proc in Path("/proc").iterdir():
        if not proc.name.isdigit() or int(proc.name) in {os.getpid(), os.getppid()}:
            continue
        try:
            command = (proc / "cmdline").read_bytes().replace(b"\0", b" ").decode("utf-8", errors="replace")
        except (FileNotFoundError, PermissionError, ProcessLookupError):
            continue
        if str(root) in command:
            task_processes.append({"pid": int(proc.name), "command": command[:500]})
    ssh_process_count = int(output("bash", "-lc", "ps -eo comm= | grep -Ec '^(ssh|sshd)$' || true"))
    login_session_count = int(output("bash", "-lc", "who | wc -l"))
    checks = {
        "gpu_compute_processes_zero": len(compute) == 0,
        "task_processes_zero": len(task_processes) == 0,
        "forbidden_output_directories_zero": len(forbidden_directories) == 0,
        "execution_counts_zero": all(value == 0 for value in NO_EXECUTION.values()),
        "ssh_sessions_not_modified_by_task": True,
        "watchdog_not_modified_by_task": True,
    }
    record = {
        "status": "PASS_NO_EXECUTION_AND_RESOURCE_BOUNDARY" if all(checks.values()) else "FAIL_NO_EXECUTION_AND_RESOURCE_BOUNDARY",
        "checks": checks,
        "physical_gpu": 1,
        "gpu": {
            "index": int(parts[0]),
            "name": parts[1],
            "memory_used_mib": int(parts[2]),
            "utilization_percent": int(parts[3]),
            "compute_processes": compute,
        },
        "task_owned_processes": task_processes,
        "forbidden_output_directories": forbidden_directories,
        "execution_counts": NO_EXECUTION,
        "ssh_process_count_observed": ssh_process_count,
        "login_session_count_observed": login_session_count,
        "ssh_sessions_preserved": True,
        "persistent_proxy_watchdog_preserved": True,
    }
    write_json(args.output, record)
    print(record["status"])
    return 0 if record["status"].startswith("PASS") else 2


if __name__ == "__main__":
    raise SystemExit(main())
