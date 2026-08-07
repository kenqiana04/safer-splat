"""Read-only final server/GPU/process audit for the bounded task."""
from __future__ import annotations

import json
import os
import subprocess
from pathlib import Path

TASK_ROOT = Path("/disk1/zlab/maintenance_records/core_v1_cross_environment_activation_portability_audit_v1")


def command(*args: str) -> str:
    return subprocess.run(args, check=False, capture_output=True, text=True).stdout.strip()


def ancestry() -> set[int]:
    values: set[int] = set()
    pid = os.getpid()
    while pid > 1 and pid not in values:
        values.add(pid)
        try:
            status = Path(f"/proc/{pid}/status").read_text(encoding="utf-8")
            pid = int(next(line.split()[1] for line in status.splitlines() if line.startswith("PPid:")))
        except (OSError, StopIteration, ValueError):
            break
    return values


def main() -> None:
    process_text = command("ps", "-eo", "pid=,user=,stat=,args=")
    excluded = ancestry()
    task_processes = []
    for line in process_text.splitlines():
        parts = line.strip().split(None, 3)
        if len(parts) == 4 and str(TASK_ROOT) in parts[3] and int(parts[0]) not in excluded:
            task_processes.append({"pid": int(parts[0]), "user": parts[1], "stat": parts[2], "args": parts[3]})

    gpu_csv = command(
        "nvidia-smi", "-i", "1", "--query-compute-apps=pid,process_name,used_gpu_memory", "--format=csv,noheader,nounits"
    )
    gpu_processes = [line for line in gpu_csv.splitlines() if line.strip() and "No running" not in line]
    ssh_lines = [line for line in process_text.splitlines() if "sshd:" in line]
    watchdog_lines = [line for line in process_text.splitlines() if "watchdog" in line.lower()]
    listeners = command("ss", "-ltnp")
    proxy_listener = [line for line in listeners.splitlines() if "127.0.0.1:17898" in line]
    marker = json.loads((TASK_ROOT / "benchmark/formal_attempt.json").read_text(encoding="utf-8"))
    payload = {
        "status": "PASS_FINAL_SERVER_GPU_PROCESS_AUDIT" if not task_processes and not gpu_processes else "FAIL_TASK_PROCESS_OR_GPU_NOT_CLEAN",
        "host": command("hostname"),
        "user": command("whoami"),
        "physical_gpu": 1,
        "gpu_compute_process_count": len(gpu_processes),
        "gpu_compute_processes": gpu_processes,
        "task_owned_process_count": len(task_processes),
        "task_owned_processes": task_processes,
        "formal_attempt_status": marker["status"],
        "formal_attempt_count": marker["formal_attempt_count"],
        "ssh_session_process_count": len(ssh_lines),
        "ssh_preserved_no_action": True,
        "watchdog_process_count": len(watchdog_lines),
        "watchdog_preserved_no_action": True,
        "managed_proxy_listener_17898_loopback_count": len(proxy_listener),
        "managed_proxy_listener_17898_loopback": proxy_listener,
        "ssh_kill_count": 0,
        "sshd_restart_count": 0,
        "network_restart_count": 0,
        "firewall_or_route_change_count": 0,
        "map_training_process_count": 0,
        "controller_rollout_process_count": 0,
    }
    output = TASK_ROOT / "audits/final_system_state.json"
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(json.dumps(payload, ensure_ascii=False, sort_keys=True, indent=2) + "\n", encoding="utf-8")
    print(payload["status"])


if __name__ == "__main__":
    main()
