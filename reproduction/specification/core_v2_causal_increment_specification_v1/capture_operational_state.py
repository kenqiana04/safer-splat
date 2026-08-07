"""Capture GPU/watchdog state read-only and update only task-owned records."""

from __future__ import annotations

import json
import subprocess

from task_config import TASK_ROOT


def run(command: list[str]) -> subprocess.CompletedProcess[str]:
    return subprocess.run(command, text=True, encoding="utf-8", errors="replace", capture_output=True, check=False)


def main() -> None:
    remote = run(
        [
            "ssh",
            "zlab-4090",
            "set -u; hostname; nvidia-smi -i 1 --query-gpu=index,name,memory.used,utilization.gpu --format=csv,noheader; "
            "echo COMPUTE_APPS; nvidia-smi -i 1 --query-compute-apps=pid,process_name,used_gpu_memory --format=csv,noheader || true; "
            "echo TASK_PROCESSES; ps -eo pid=,args= | awk '$0 ~ /core_v2_causal_increment_specification_v1/ && $0 !~ /(awk|grep|sshd|bash -lc)/ {print}'; "
            "test -x ~/.config/scannetpp_proxy/run_with_scannetpp_proxy.sh && echo REMOTE_WRAPPER_PRESENT=true || echo REMOTE_WRAPPER_PRESENT=false",
        ]
    )
    if remote.returncode != 0:
        raise RuntimeError(f"REMOTE_READ_ONLY_AUDIT_FAILED:{remote.stderr.strip()}")
    lines = [line.strip() for line in remote.stdout.splitlines() if line.strip()]
    compute_index = lines.index("COMPUTE_APPS")
    task_index = lines.index("TASK_PROCESSES")
    wrapper_index = next(i for i, line in enumerate(lines) if line.startswith("REMOTE_WRAPPER_PRESENT="))
    compute_apps = lines[compute_index + 1 : task_index]
    task_processes = lines[task_index + 1 : wrapper_index]
    watchdog = run(["schtasks", "/Query", "/TN", "Codex-Persistent-Reverse-Proxy-Watchdog", "/FO", "LIST", "/V"])
    watchdog_running = watchdog.returncode == 0 and "Running" in watchdog.stdout
    payload = {
        "status": "PASS_CORE_V2_SPEC_OPERATIONAL_PRESERVATION",
        "read_only": True,
        "remote_host": lines[0],
        "gpu_1_summary": lines[1],
        "gpu_1_compute_processes": compute_apps,
        "task_owned_compute_processes": task_processes,
        "task_owned_compute_process_count": len(task_processes),
        "GPU_formal_compute_count": 0,
        "remote_wrapper_present": lines[wrapper_index].endswith("true"),
        "watchdog_running": watchdog_running,
        "watchdog_query_exit": watchdog.returncode,
        "watchdog_ssh_action": "NO_MODIFICATION_COMMAND_EXECUTED",
        "task_owned_process_cleanup_count": 0,
    }
    if payload["task_owned_compute_process_count"] != 0 or not payload["remote_wrapper_present"] or not watchdog_running:
        raise RuntimeError("OPERATIONAL_PRESERVATION_CHECK_FAILED")
    (TASK_ROOT / "operational_state_audit.json").write_text(
        json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8"
    )
    manifest_path = TASK_ROOT / "run_manifest.json"
    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    manifest["operational_state_captured"] = True
    manifest["gpu_1_summary"] = payload["gpu_1_summary"]
    manifest["task_owned_compute_process_count"] = 0
    manifest["watchdog_running"] = watchdog_running
    manifest["remote_wrapper_present"] = payload["remote_wrapper_present"]
    manifest_path.write_text(json.dumps(manifest, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(payload["status"])


if __name__ == "__main__":
    main()
