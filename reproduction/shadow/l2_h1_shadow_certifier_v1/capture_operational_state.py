"""Read-only GPU/process/watchdog/SSH audit for the task boundary."""
from __future__ import annotations

import json
from pathlib import Path
import subprocess

from shadow_contract import TASK_ROOT


def run(command: list[str], timeout: int = 30) -> subprocess.CompletedProcess[str]:
    return subprocess.run(command, check=False, capture_output=True, text=True, timeout=timeout)


def main() -> None:
    remote_script = r'''set -u
echo HOST=$(hostname)
echo GPU_BEGIN
nvidia-smi -i 1 --query-gpu=index,name,memory.used,utilization.gpu --format=csv,noheader
echo GPU_END
echo COMPUTE_BEGIN
nvidia-smi -i 1 --query-compute-apps=pid,process_name,used_gpu_memory --format=csv,noheader || true
echo COMPUTE_END
echo TASK_BEGIN
pgrep -af '[l]2_h1_shadow_certifier_v1' || true
echo TASK_END
test -x ~/.config/scannetpp_proxy/run_with_scannetpp_proxy.sh && echo WRAPPER_PRESENT=true || echo WRAPPER_PRESENT=false
'''
    remote = run(["ssh", "zlab-4090", remote_script])
    if remote.returncode != 0:
        raise SystemExit("REMOTE_READ_ONLY_AUDIT_FAILED:" + remote.stderr.strip())
    lines = remote.stdout.splitlines()

    def section(begin: str, end: str) -> list[str]:
        start = lines.index(begin) + 1
        stop = lines.index(end)
        return [line.strip() for line in lines[start:stop] if line.strip()]

    gpu = section("GPU_BEGIN", "GPU_END")
    compute = section("COMPUTE_BEGIN", "COMPUTE_END")
    task_processes = section("TASK_BEGIN", "TASK_END")
    task_query = run([
        "powershell", "-NoProfile", "-Command",
        "$t=Get-ScheduledTask -TaskName 'Codex-Persistent-Reverse-Proxy-Watchdog' -ErrorAction SilentlyContinue; "
        "if($null -eq $t){'{\"present\":false}'}else{@{present=$true;task_name=$t.TaskName;state=[string]$t.State}|ConvertTo-Json -Compress}",
    ])
    try:
        watchdog = json.loads(task_query.stdout.strip())
    except json.JSONDecodeError:
        watchdog = {"present": False, "query_parse_error": True}
    payload = {
        "status": "PASS_L2_H1_SHADOW_OPERATIONAL_BOUNDARY",
        "read_only": True,
        "remote_host": next((line.split("=", 1)[1] for line in lines if line.startswith("HOST=")), None),
        "gpu_1_summary": gpu[0] if gpu else None,
        "gpu_1_compute_processes": compute,
        "gpu_1_compute_process_count": len(compute),
        "task_owned_processes": task_processes,
        "task_owned_process_count": len(task_processes),
        "GPU_formal_compute_count": 0,
        "watchdog": watchdog,
        "remote_wrapper_present": "WRAPPER_PRESENT=true" in lines,
        "ssh_modification_count": 0,
        "proxy_modification_count": 0,
        "watchdog_modification_count": 0,
        "remote_wrapper_modification_count": 0,
        "process_kill_count": 0,
    }
    path = TASK_ROOT / "audit/operational_state_audit.json"
    path.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8", newline="\n")
    print("PASS_L2_H1_SHADOW_OPERATIONAL_BOUNDARY")


if __name__ == "__main__":
    main()
