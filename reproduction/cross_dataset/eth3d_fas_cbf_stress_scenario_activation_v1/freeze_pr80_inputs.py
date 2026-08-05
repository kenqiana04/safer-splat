#!/usr/bin/env python3
"""Fail-closed freeze of PR #80 and the authoritative frozen-map inputs."""
from __future__ import annotations

import json
import os
import platform
import subprocess
from datetime import datetime, timezone

from task_config_v2 import *  # noqa: F403

def main() -> int:
    ensure_roots()
    required = [PR80_ROOT, MAP_ROOT, ENV_ROOT, DATA_ROOT, SOURCE_ROOT, CANONICAL_ROOT,
                CONTROLLER_SNAPSHOT, PRM_GRAPH, REFERENCE_MESH, V1_REGISTRY, V1_RESULTS,
                V1_REPORT, MAP_PLY]
    missing = [str(path) for path in required if not path.exists()]
    if missing: raise RuntimeError(f"missing frozen inputs: {missing}")
    registry = json.loads(V1_REGISTRY.read_text())
    canonical = json.loads((PR80_ROOT / "canonical_export/canonical_validation.json").read_text())
    identities = {
        "pr80_report_sha256": sha256_file(V1_REPORT),
        "v1_registry_raw_sha256": sha256_file(V1_REGISTRY),
        "v1_registry_logical_sha256": registry["registry_sha256"],
        "map_ply_sha256": sha256_file(MAP_PLY),
        "canonical_tree_sha256": canonical["tree_sha256"],
        "reference_mesh_sha256": sha256_file(REFERENCE_MESH),
        "method_code_sha256": sha256_file(PR80_ROOT / "fas_cbf_modules.py"),
        "baseline_core_sha256": sha256_file(PR80_ROOT / "eth3d_controller_core.py"),
        "formal_runner_sha256": sha256_file(PR80_ROOT / "run_formal_paired_controller_benchmark.py"),
        "prm_graph_sha256": sha256_file(PRM_GRAPH),
    }
    checks = {
        key: identities[key] == EXPECTED[key]
        for key in ("pr80_report_sha256", "v1_registry_logical_sha256", "map_ply_sha256",
                    "canonical_tree_sha256", "reference_mesh_sha256")
    }
    if not all(checks.values()): raise RuntimeError({"identity_checks": checks, "identities": identities})
    gpu = subprocess.run(["nvidia-smi", "-i", "1", "--query-gpu=index,name,uuid,driver_version,memory.total",
                          "--format=csv,noheader"], check=True, capture_output=True, text=True).stdout.strip()
    payload = {
        "status": "PASS_PR80_AND_FROZEN_MAP_INPUT_FREEZE", "task": TASK_NAME,
        "branch": BRANCH, "base_branch": BASE_BRANCH, "base_head": BASE_HEAD,
        "recorded_utc": datetime.now(timezone.utc).isoformat(), "host": platform.node(),
        "user": os.environ.get("USER"), "gpu": gpu, "identities": identities,
        "identity_checks": checks, "official_3dgs_commit": EXPECTED["official_3dgs_commit"],
        "protocol_sha256": EXPECTED["protocol_sha256"], "v1_activation": {"H1":14,"H2":0,"H3":0,"H4":0},
        "pr80_preserved": True, "map_training_count": 0, "map_mutation_count": 0,
        "dataset_count": 1, "scene_count": 1, "formal_map_count": 1,
    }
    atomic_json(TASK_ROOT / "input_freeze/pr80_frozen_input_identity.json", payload)
    print(json.dumps({"status": payload["status"], "checks": checks}, sort_keys=True))
    return 0

if __name__ == "__main__": raise SystemExit(main())
