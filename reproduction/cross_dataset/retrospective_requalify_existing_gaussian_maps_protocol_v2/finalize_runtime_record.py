"""Record final infrastructure evidence without changing scientific evidence."""
from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path

from requalification_core import ROOT


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--server-host", required=True)
    parser.add_argument("--gpu-memory-used-mib", type=int, required=True)
    parser.add_argument("--gpu-utilization-percent", type=int, required=True)
    parser.add_argument("--all-compute-process-count", type=int, required=True)
    parser.add_argument("--task-compute-process-count", type=int, required=True)
    parser.add_argument("--watchdog-status", required=True)
    parser.add_argument("--managed-ssh-status", required=True)
    parser.add_argument("--disk-before-bytes", type=int, required=True)
    parser.add_argument("--disk-after-bytes", type=int, required=True)
    parser.add_argument("--server-report", required=True)
    parser.add_argument("--server-report-sha256", required=True)
    args = parser.parse_args()
    report = ROOT / "REPORT_RETROSPECTIVE_REQUALIFY_EXISTING_GAUSSIAN_MAPS_UNDER_LAYERED_PROTOCOL_V2.md"
    record = {
        "server_host": args.server_host,
        "physical_gpu": 1,
        "gpu_final": {
            "index": 1,
            "name": "NVIDIA GeForce RTX 4090",
            "memory_total_mib": 24564,
            "memory_used_mib": args.gpu_memory_used_mib,
            "utilization_gpu_percent": args.gpu_utilization_percent,
            "all_compute_process_count": args.all_compute_process_count,
            "task_compute_process_count": args.task_compute_process_count,
        },
        "watchdog_status": args.watchdog_status,
        "managed_ssh_preserved": args.managed_ssh_status == "PRESERVED",
        "disk_before_bytes": args.disk_before_bytes,
        "disk_after_bytes": args.disk_after_bytes,
        "new_disk_bytes": max(0, args.disk_before_bytes - args.disk_after_bytes),
        "new_disk_limit_bytes": 120 * 1024**3,
        "server_report": args.server_report,
        "server_report_sha256": args.server_report_sha256,
        "local_report_sha256": hashlib.sha256(report.read_bytes()).hexdigest(),
        "scientific_execution_added": False,
    }
    target = ROOT / "runtime_finalization.json"
    target.write_text(json.dumps(record, indent=2, sort_keys=True) + "\n", encoding="utf-8", newline="\n")
    manifest_path = ROOT / "run_manifest.json"
    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    manifest["runtime_finalization"] = record
    manifest_path.write_text(json.dumps(manifest, indent=2, sort_keys=True) + "\n", encoding="utf-8", newline="\n")
    print("RUNTIME_FINALIZATION_COMPLETE")


if __name__ == "__main__":
    main()
