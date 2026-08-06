#!/usr/bin/env python3
"""Read-only remote asset, runtime, GPU, and payload preflight."""
from __future__ import annotations

import json
import platform
import subprocess
import sys
from pathlib import Path

import clarabel
import matplotlib
import numpy
import scipy

from common import read_json, sha256_file, write_json
from runtime_core import ReplicaRuntime
from task_config import (
    MAP_FILES, MAP_ROOT, MAP_SNAPSHOT_ID, MESH_ORACLE,
    MESH_ORACLE_VALIDATION, REFERENCE_MESH, REFERENCE_MESH_SHA256,
    ROUTE_REGISTRY, ROUTE_SHA256, START_REGISTRY, START_SHA256, TASK_ROOT,
)


def command(arguments: list[str]) -> str:
    return subprocess.run(arguments, check=True, capture_output=True, text=True).stdout.strip()


def main() -> None:
    checks = {}
    assets = {}
    for name, expected in MAP_FILES.items():
        path = Path(MAP_ROOT) / name
        actual = sha256_file(path)
        checks[name] = actual == expected
        assets[name] = {"path": str(path), "sha256": actual, "size": path.stat().st_size}
    route_sha = sha256_file(ROUTE_REGISTRY)
    start_sha = sha256_file(START_REGISTRY)
    mesh_sha = sha256_file(REFERENCE_MESH)
    checks.update({
        "route_registry": route_sha == ROUTE_SHA256,
        "start_registry": start_sha == START_SHA256,
        "reference_mesh": mesh_sha == REFERENCE_MESH_SHA256,
        "mesh_oracle_executable": Path(MESH_ORACLE).is_file(),
        "mesh_oracle_validation": Path(MESH_ORACLE_VALIDATION).is_file(),
    })
    validation = read_json(MESH_ORACLE_VALIDATION)
    checks["mesh_oracle_validation_pass"] = validation.get("status") == "PASS"
    payload = read_json(TASK_ROOT / "runtime_payload_manifest.json")
    payload_checks = []
    for item in payload["files"]:
        path = TASK_ROOT / item["destination"]
        payload_checks.append(path.exists() and sha256_file(path) == item["sha256"])
    checks["runtime_payload_identity"] = all(payload_checks)
    runtime = ReplicaRuntime(Path(MAP_ROOT))
    checks["runtime_map_snapshot"] = runtime.map_adapter.map_snapshot_id == MAP_SNAPSHOT_ID
    checks["runtime_h_stop_max"] = runtime.braking_policy.h_stop_max() == 20
    gpu = command(["nvidia-smi", "-i", "1", "--query-gpu=index,memory.used,utilization.gpu", "--format=csv,noheader"])
    compute = command(["nvidia-smi", "-i", "1", "--query-compute-apps=pid,process_name,used_gpu_memory", "--format=csv,noheader"])
    listener = command(["bash", "-lc", "ss -ltn 'sport = :17898' || true"])
    checks["gpu_compute_empty"] = compute == ""
    checks["proxy_loopback_listener"] = "127.0.0.1:17898" in listener
    if not all(checks.values()):
        write_json(TASK_ROOT / "report/server_preflight.json", {"status": "BLOCKED_SERVER_PREFLIGHT", "checks": checks})
        raise SystemExit("BLOCKED_SERVER_PREFLIGHT")
    write_json(TASK_ROOT / "input_freeze/replica_map_identity.json", {
        "status": "PASS_REMOTE_READ_ONLY_MAP_AND_REGISTRY_IDENTITY",
        "map_snapshot_id": MAP_SNAPSHOT_ID,
        "assets": assets,
        "route_registry": {"path": ROUTE_REGISTRY, "sha256": route_sha},
        "start_registry": {"path": START_REGISTRY, "sha256": start_sha},
        "map_training_count": 0,
        "map_mutation_count": 0,
    })
    write_json(TASK_ROOT / "input_freeze/reference_mesh_identity.json", {
        "status": "PASS_REMOTE_READ_ONLY_REFERENCE_IDENTITY",
        "reference_mesh": {"path": REFERENCE_MESH, "sha256": mesh_sha},
        "validated_oracle": {"path": MESH_ORACLE, "validation_path": MESH_ORACLE_VALIDATION, "validation_status": validation.get("status")},
        "prelock_future_reference_read_count": 0,
        "reference_online_read_count": 0,
    })
    write_json(TASK_ROOT / "report/server_preflight.json", {
        "status": "PASS_SERVER_PREFLIGHT",
        "checks": checks,
        "python": sys.version,
        "platform": platform.platform(),
        "versions": {"numpy": numpy.__version__, "scipy": scipy.__version__, "clarabel": clarabel.__version__, "matplotlib": matplotlib.__version__},
        "gpu": gpu,
        "gpu_compute_processes": compute,
        "proxy_listener": listener,
        "route_count": len(read_json(ROUTE_REGISTRY)["routes"]),
        "runtime_payload_file_count": len(payload["files"]),
    })
    print("PASS_SERVER_PREFLIGHT", gpu, len(payload["files"]))


if __name__ == "__main__":
    main()
