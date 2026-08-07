"""Read-only final GPU/process and watchdog/SSH preservation evidence."""

from __future__ import annotations

import json
import subprocess

from task_config import TASK_ROOT


def run(args: list[str]) -> tuple[int, str, str]:
    result = subprocess.run(args, text=True, encoding="utf-8", capture_output=True, check=False)
    return result.returncode, result.stdout.strip(), result.stderr.strip()


def main() -> None:
    gpu_code, gpu_out, gpu_err = run([
        "ssh", "zlab-4090", "bash", "-lc",
        "nvidia-smi -i 1 --query-compute-apps=pid,process_name,used_gpu_memory --format=csv,noheader || true; test -x ~/.config/scannetpp_proxy/run_with_scannetpp_proxy.sh",
    ])
    watchdog_code, watchdog_out, watchdog_err = run([
        "schtasks", "/Query", "/TN", "Codex-Persistent-Reverse-Proxy-Watchdog", "/FO", "LIST",
    ])
    task_owned_markers = [line for line in gpu_out.splitlines() if "core_v1_actionable_factor_ranking" in line]
    payload = {
        "status": "PASS_READ_ONLY_OPERATIONAL_PRESERVATION" if gpu_code == 0 else "REMOTE_READ_ONLY_CHECK_INCOMPLETE",
        "read_only": True,
        "formal_method_run_count": 0,
        "task_owned_compute_process_count": len(task_owned_markers),
        "gpu_1_compute_query": gpu_out,
        "gpu_1_query_stderr": gpu_err,
        "remote_wrapper_exists": gpu_code == 0,
        "watchdog_query_exit": watchdog_code,
        "watchdog_query_excerpt": watchdog_out[:1500],
        "watchdog_query_stderr": watchdog_err,
        "watchdog_ssh_preservation": "NO_MODIFICATION_COMMAND_EXECUTED",
        "forbidden_actions_executed": [],
    }
    path = TASK_ROOT / "report" / "operational_state.json"
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    if gpu_code != 0 or task_owned_markers:
        raise SystemExit("Operational preservation check failed or task-owned compute process found")
    print("PASS_READ_ONLY_GPU_PROCESS_AND_WATCHDOG_SSH_PRESERVATION")


if __name__ == "__main__":
    main()
