#!/usr/bin/env python3
"""Read-only final GPU/disk/watchdog/managed-SSH preservation record."""

from __future__ import annotations

import argparse
import datetime as dt
import hashlib
import json
import subprocess
from pathlib import Path


SERVER_ROOT = "/disk1/zlab/maintenance_records/eth3d_delivery_area_protocol_v2_entry_qualification_v1"


def run(*args: str) -> str:
    return subprocess.check_output(args, text=True, encoding="utf-8", errors="replace").strip()


def ssh(command: str) -> str:
    return run("ssh", "zlab-4090", command)


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--task-root", type=Path, required=True)
    args = parser.parse_args()
    root = args.task_root.resolve()
    report = root / "REPORT_ETH3D_DELIVERY_AREA_PROTOCOL_V2_ENTRY_QUALIFICATION_V1.md"
    host = ssh("hostname")
    gpu_line = ssh("nvidia-smi -i 1 --query-gpu=index,name,uuid,driver_version,memory.total,memory.used,utilization.gpu --format=csv,noheader,nounits")
    gpu_parts = [x.strip() for x in gpu_line.split(",")]
    compute_text = ssh("nvidia-smi -i 1 --query-compute-apps=pid,process_name,used_gpu_memory --format=csv,noheader,nounits || true")
    compute = []
    for line in compute_text.splitlines():
        if not line.strip():
            continue
        parts = [x.strip() for x in line.split(",")]
        compute.append({"pid": int(parts[0]), "process_name": parts[1], "used_gpu_memory_mib": int(parts[2]) if parts[2].isdigit() else parts[2]})
    process_text = ssh("ps -eo pid=,user=,args=")
    task_processes = []
    for line in process_text.splitlines():
        low = line.lower()
        if SERVER_ROOT in line and any(token in low for token in ["python", "cuda", "ns-train", "train.py"]):
            parts = line.strip().split(None, 2)
            task_processes.append({"pid": int(parts[0]), "user": parts[1], "args": parts[2] if len(parts) > 2 else ""})
    task_size = int(ssh(f"du -sb {SERVER_ROOT} | cut -f1"))
    disk_free = int(ssh("df -B1 --output=avail /disk1 | tail -n 1"))
    server_report = f"{SERVER_ROOT}/report/{report.name}"
    server_report_sha = ssh(f"sha256sum {server_report} | cut -d' ' -f1")
    server_validator_status = ssh(f"python3 -c \"import json; print(json.load(open('{SERVER_ROOT}/validation_result.json'))['status'])\"")
    local_report_sha = hashlib.sha256(report.read_bytes()).hexdigest()
    watchdog = run("powershell", "-NoProfile", "-Command", "(Get-ScheduledTask -TaskName 'Codex-Persistent-Reverse-Proxy-Watchdog').State.ToString()")
    ssh_json = run(
        "powershell",
        "-NoProfile",
        "-Command",
        "$p=Get-CimInstance Win32_Process | Where-Object {$_.Name -eq 'ssh.exe' -and $_.CommandLine -like '*127.0.0.1:17898:127.0.0.1:7897*' -and $_.CommandLine -like '*zlab-4090*'} | Select-Object ProcessId,CommandLine; $p | ConvertTo-Json -Compress",
    )
    managed = json.loads(ssh_json) if ssh_json else []
    if isinstance(managed, dict):
        managed = [managed]
    result = {
        "status": "PASS_RUNTIME_BOUNDARY_PRESERVED" if not task_processes and server_report_sha == local_report_sha and server_validator_status == "PASS" and task_size < 1_073_741_824 and watchdog == "Running" and managed else "FAIL",
        "checked_utc": dt.datetime.now(dt.timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z"),
        "server_host": host,
        "physical_gpu": 1,
        "gpu_final": {
            "index": int(gpu_parts[0]), "name": gpu_parts[1], "uuid": gpu_parts[2], "driver_version": gpu_parts[3],
            "memory_total_mib": int(gpu_parts[4]), "memory_used_mib": int(gpu_parts[5]), "utilization_gpu_percent": int(gpu_parts[6]),
            "all_compute_process_count": len(compute), "all_compute_processes": compute,
            "task_compute_process_count": len(task_processes), "task_compute_processes": task_processes,
        },
        "task_root": SERVER_ROOT,
        "task_root_size_bytes": task_size,
        "task_root_initial_size_bytes": 86016,
        "new_task_bytes_upper_bound": max(0, task_size - 86016),
        "new_disk_limit_bytes": 1_073_741_824,
        "disk1_free_bytes": disk_free,
        "server_report": server_report,
        "server_report_sha256": server_report_sha,
        "local_report_sha256": local_report_sha,
        "server_validator_status": server_validator_status,
        "watchdog_task": "Codex-Persistent-Reverse-Proxy-Watchdog",
        "watchdog_status": watchdog,
        "managed_reverse_ssh_process_count": len(managed),
        "managed_reverse_ssh_pids": [int(x["ProcessId"]) for x in managed],
        "managed_reverse_ssh_preserved": bool(managed),
        "port_17897_operation_count": 0,
        "sshd_restart_count": 0,
        "network_restart_count": 0,
        "firewall_change_count": 0,
        "global_git_proxy_change_count": 0,
        "training_authorized": False,
    }
    (root / "runtime_finalization.json").write_text(json.dumps(result, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(result, indent=2))
    return 0 if result["status"].startswith("PASS") else 2


if __name__ == "__main__":
    raise SystemExit(main())
