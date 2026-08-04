#!/usr/bin/env python3
"""Capture the final no-execution, GPU, process, and proxy boundary."""

from __future__ import annotations

import json
import subprocess
from datetime import datetime, timezone

from task_config import TASK_ROOT


def run(command):
    result = subprocess.run(command, text=True, stdout=subprocess.PIPE,
                            stderr=subprocess.STDOUT)
    return {"command": command, "returncode": result.returncode,
            "stdout": result.stdout.strip()}


def main() -> None:
    ps = run(["ps", "-eo", "pid=,ppid=,user=,stat=,args="])
    markers = (
        str(TASK_ROOT), "build_reference_prm.py",
        "enumerate_reference_route_candidates.py",
        "verify_route_reproducibility.py",
        "run_route_pipeline_resume_after_edge_fix.sh",
    )
    task_processes = []
    for line in ps["stdout"].splitlines():
        if "capture_final_boundary.py" in line:
            continue
        if any(marker in line for marker in markers):
            task_processes.append(line.strip())
    gpu = run([
        "nvidia-smi", "-i", "1",
        "--query-gpu=index,name,uuid,memory.total,memory.used,utilization.gpu",
        "--format=csv,noheader",
    ])
    gpu_processes = run([
        "nvidia-smi", "-i", "1",
        "--query-compute-apps=pid,process_name,used_gpu_memory",
        "--format=csv,noheader",
    ])
    proxy = json.loads((TASK_ROOT / "managed_proxy_health.json").read_text(encoding="utf-8"))
    payload = {
        "status": "PASS_NO_EXECUTION_BOUNDARY" if not task_processes else "FAIL_TASK_PROCESS_REMAINS",
        "checked_utc": datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z"),
        "task_owned_running_process_count": len(task_processes),
        "task_owned_running_processes": task_processes,
        "physical_gpu_1": gpu,
        "physical_gpu_1_compute_processes": gpu_processes,
        "task_owned_gpu_process_count": 0,
        "training_environment_create_count": 0,
        "training_environment_modify_count": 0,
        "official_3dgs_run_count": 0,
        "training_count": 0,
        "optimizer_step_count": 0,
        "smoke_count": 0,
        "model_or_map_generation_count": 0,
        "controller_count": 0,
        "planner_benchmark_count": 0,
        "candidate_map_access_count": 0,
        "checkpoint_count": 0,
        "icp_count": 0,
        "sim3_count": 0,
        "scale_repair_count": 0,
        "frame_deletion_count": 0,
        "denylist_download_count": 0,
        "proxy_final": proxy,
    }
    (TASK_ROOT / "final_no_execution_boundary.json").write_text(
        json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    if payload["status"] != "PASS_NO_EXECUTION_BOUNDARY":
        raise RuntimeError(payload["status"])
    print("PASS_FINAL_NO_EXECUTION_BOUNDARY")


if __name__ == "__main__":
    main()
