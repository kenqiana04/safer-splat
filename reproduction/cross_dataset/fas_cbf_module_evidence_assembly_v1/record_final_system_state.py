#!/usr/bin/env python3
"""Record a read-only final GPU, tunnel, and watchdog boundary snapshot."""
from __future__ import annotations

import subprocess

from evidence_common import TASK, write_json


def command(args: list[str]) -> tuple[int, str]:
    completed = subprocess.run(args, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, text=True, encoding="utf-8", errors="replace")
    return completed.returncode, completed.stdout.strip()


def main() -> int:
    gpu_code, gpu = command(["ssh", "zlab-4090", "nvidia-smi -i 1 --query-gpu=index,name,uuid,memory.used,utilization.gpu --format=csv,noheader"])
    compute_code, compute = command(["ssh", "zlab-4090", "nvidia-smi -i 1 --query-compute-apps=pid,process_name,used_gpu_memory --format=csv,noheader || true"])
    task_code, task_python = command(["ssh", "zlab-4090", "ps -C python -C python3 -o pid=,args= | grep fas_cbf_module_evidence_assembly_v1 || true"])
    listener_code, listener = command(["ssh", "zlab-4090", "ss -ltn | grep '127.0.0.1:17898' || true"])
    watchdog_code, watchdog = command(["powershell", "-NoProfile", "-Command", "(Get-ScheduledTask -TaskName 'Codex-Persistent-Reverse-Proxy-Watchdog').State"])
    status = "PASS_FINAL_SYSTEM_READONLY_CHECK" if gpu_code == 0 and task_code == 0 and not task_python and watchdog.strip() == "Running" and "127.0.0.1:17898" in listener else "FAIL_FINAL_SYSTEM_READONLY_CHECK"
    write_json(TASK / "report/system_final_state.json", {"status": status, "gpu": gpu, "gpu_compute_processes": compute if compute_code == 0 else "UNKNOWN", "task_owned_python_processes": task_python, "listener_17898": listener, "watchdog_state": watchdog, "return_codes": {"gpu": gpu_code, "compute": compute_code, "task_python": task_code, "listener": listener_code, "watchdog": watchdog_code}, "mutations": {"training": 0, "controller_rollout": 0, "map_mutation": 0, "method_tuning": 0, "dataset_switch": 0, "watchdog_modification": 0}})
    print(status)
    return 0 if status.startswith("PASS") else 2


if __name__ == "__main__":
    raise SystemExit(main())
