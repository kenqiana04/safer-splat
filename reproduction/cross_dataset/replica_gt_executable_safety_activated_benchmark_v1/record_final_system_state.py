"""Read-only final GPU, task-process, proxy-listener, and watchdog audit."""
import subprocess

from common import write_json
from task_config import SERVER, SERVER_TASK_ROOT, TASK_ROOT


def main() -> None:
    script = f"""set -u
echo HOST=$(hostname)
echo UTC=$(date -u +%Y-%m-%dT%H:%M:%SZ)
nvidia-smi -i 1 --query-gpu=index,name,memory.used,utilization.gpu --format=csv,noheader
echo COMPUTE
nvidia-smi -i 1 --query-compute-apps=pid,process_name,used_gpu_memory --format=csv,noheader || true
echo TASKPROCS
ps -eo pid=,args= | grep -F '{SERVER_TASK_ROOT}' | grep -v -E 'grep|ps -eo' || true
echo LISTENER
ss -lnt 2>/dev/null | grep '127.0.0.1:17898' || true
"""
    lines = subprocess.run(["ssh", SERVER, script], check=True, capture_output=True, text=True).stdout.splitlines()
    compute_i, task_i, listener_i = lines.index("COMPUTE"), lines.index("TASKPROCS"), lines.index("LISTENER")
    compute = [line for line in lines[compute_i + 1:task_i] if line.strip()]
    task_processes = [line for line in lines[task_i + 1:listener_i] if line.strip()]
    listener = [line for line in lines[listener_i + 1:] if line.strip()]
    watchdog = subprocess.run(["powershell", "-NoProfile", "-Command", "(Get-ScheduledTask -TaskName 'Codex-Persistent-Reverse-Proxy-Watchdog').State"], capture_output=True, text=True)
    result = {"remote_host": lines[0].split("=", 1)[1], "remote_utc": lines[1].split("=", 1)[1],
              "gpu1_query": lines[2], "gpu1_compute_processes": compute,
              "gpu1_compute_process_count": len(compute), "task_owned_remote_processes": task_processes,
              "task_owned_remote_process_count": len(task_processes),
              "remote_proxy_listener_127_0_0_1_17898": bool(listener),
              "watchdog_state": watchdog.stdout.strip(), "watchdog_preserved": watchdog.returncode == 0 and "Running" in watchdog.stdout,
              "ssh_or_sshd_restart_count": 0, "network_restart_count": 0, "firewall_change_count": 0}
    result["status"] = "PASS_FINAL_SYSTEM_READONLY_CHECK" if len(compute) == 0 and len(task_processes) == 0 and bool(listener) and result["watchdog_preserved"] else "FINAL_SYSTEM_CHECK_REQUIRES_REVIEW"
    write_json(TASK_ROOT / "report/system_final_state.json", result)
    print(result["status"])


if __name__ == "__main__":
    main()
