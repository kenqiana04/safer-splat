"""Read-only GPU/process and persistent proxy preservation check."""

from __future__ import annotations

import json
import subprocess

from task_config import TASK_ROOT


def probe(args: list[str]) -> tuple[int, str, str]:
    result = subprocess.run(args, text=True, encoding="utf-8", capture_output=True, check=False)
    return result.returncode, result.stdout.strip(), result.stderr.strip()


def main() -> None:
    gpu_code, gpu_out, gpu_err = probe(["ssh", "zlab-4090", "bash", "-lc", "nvidia-smi -i 1 --query-compute-apps=pid,process_name,used_gpu_memory --format=csv,noheader || true; test -x ~/.config/scannetpp_proxy/run_with_scannetpp_proxy.sh"])
    watch_code, watch_out, watch_err = probe(["schtasks", "/Query", "/TN", "Codex-Persistent-Reverse-Proxy-Watchdog", "/FO", "LIST"])
    markers = [line for line in gpu_out.splitlines() if "core_causal_architecture_specification" in line]
    payload = {
        "status": "PASS_READ_ONLY_OPERATIONAL_PRESERVATION" if gpu_code == 0 and not markers else "OPERATIONAL_CHECK_INCOMPLETE",
        "task_owned_compute_process_count": len(markers), "gpu_1_compute_query": gpu_out, "gpu_1_stderr": gpu_err,
        "remote_wrapper_exists": gpu_code == 0, "watchdog_query_exit": watch_code, "watchdog_query_excerpt": watch_out[:1200], "watchdog_query_stderr": watch_err,
        "watchdog_ssh_preservation": "NO_MODIFICATION_COMMAND_EXECUTED", "read_only": True,
    }
    path = TASK_ROOT / "audits" / "runtime_preservation_check.json"; path.parent.mkdir(parents=True, exist_ok=True); path.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    if payload["status"] != "PASS_READ_ONLY_OPERATIONAL_PRESERVATION": raise SystemExit(payload["status"])
    print(payload["status"])


if __name__ == "__main__": main()
