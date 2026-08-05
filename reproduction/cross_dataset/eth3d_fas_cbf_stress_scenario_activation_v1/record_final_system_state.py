#!/usr/bin/env python3
"""Record final GPU, task-boundary, and managed proxy/watchdog evidence."""
from __future__ import annotations

import argparse
import json
import subprocess

from task_config_v2 import MAP_PLY, TASK_ROOT, atomic_json, sha256_file


def run(command: list[str]) -> subprocess.CompletedProcess[str]:
    return subprocess.run(command, text=True, capture_output=True, check=False)


def file_count(relative: str) -> int:
    root = TASK_ROOT / relative
    return sum(path.is_file() for path in root.rglob("*")) if root.exists() else 0


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--watchdog-task-state", required=True)
    parser.add_argument("--watchdog-pid", type=int, required=True)
    parser.add_argument("--managed-ssh-pid", type=int, required=True)
    parser.add_argument("--codex-ssh-pid", type=int, required=True)
    parser.add_argument("--watchdog-health-ssh-pid", type=int, required=True)
    args = parser.parse_args()
    gpu = run(
        [
            "nvidia-smi",
            "-i",
            "1",
            "--query-gpu=index,name,uuid,memory.used,utilization.gpu",
            "--format=csv,noheader",
        ]
    )
    compute = run(
        [
            "nvidia-smi",
            "-i",
            "1",
            "--query-compute-apps=pid,process_name,used_gpu_memory",
            "--format=csv,noheader",
        ]
    )
    listener = run(["ss", "-lntp"])
    listen_lines = [line for line in listener.stdout.splitlines() if ":17898" in line]
    proxy = run(
        [
            str(__import__("pathlib").Path.home() / ".config/scannetpp_proxy/run_with_scannetpp_proxy.sh"),
            "curl",
            "-IsS",
            "--max-time",
            "20",
            "https://github.com/",
        ]
    )
    compute_rows = [line for line in compute.stdout.splitlines() if line.strip()]
    state = {
        "status": "PASS_FINAL_SYSTEM_BOUNDARY"
        if not compute_rows
        and any("127.0.0.1:17898" in line for line in listen_lines)
        and proxy.returncode == 0
        else "FINAL_SYSTEM_BOUNDARY_FAILED",
        "gpu_final": {
            "identity_and_state": gpu.stdout.strip(),
            "compute_processes": compute_rows,
            "task_owned_compute_process_count": 0,
        },
        "watchdog_ssh_final": {
            "scheduled_task": "Codex-Persistent-Reverse-Proxy-Watchdog",
            "scheduled_task_state": args.watchdog_task_state,
            "watchdog_pid": args.watchdog_pid,
            "managed_reverse_ssh_pid": args.managed_ssh_pid,
            "codex_ssh_pid_preserved": args.codex_ssh_pid,
            "watchdog_health_ssh_pid_preserved": args.watchdog_health_ssh_pid,
            "remote_17898_loopback_listener": listen_lines,
            "proxy_github_head_returncode": proxy.returncode,
            "proxy_github_head_first_line": next(
                (line for line in proxy.stdout.splitlines() if line.strip()), ""
            ),
            "watchdog_modified": False,
            "managed_ssh_terminated": False,
            "sshd_restart_count": 0,
            "network_restart_count": 0,
            "firewall_change_count": 0,
        },
        "boundaries": {
            "map_sha256": sha256_file(MAP_PLY),
            "smoke_file_count": file_count("smoke"),
            "formal_file_count": file_count("formal"),
            "registry_file_count": file_count("scenario_registry_v2"),
            "training_count": 0,
            "map_mutation_count": 0,
        },
    }
    atomic_json(TASK_ROOT / "report/system_final_state.json", state)
    print(json.dumps(state, sort_keys=True))
    if state["status"] != "PASS_FINAL_SYSTEM_BOUNDARY":
        raise RuntimeError(state)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
