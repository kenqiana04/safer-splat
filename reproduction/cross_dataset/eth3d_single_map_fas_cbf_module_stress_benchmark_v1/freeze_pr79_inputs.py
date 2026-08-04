#!/usr/bin/env python3
"""Fail-closed freeze of PR #79 and the existing ETH3D data root."""

from __future__ import annotations

import json
import os
from datetime import datetime, timezone

from task_config import (
    BASE_BRANCH,
    BASE_HEAD,
    BRANCH,
    CONTRACTS,
    DATA_ROOT,
    EVAL_ROOT,
    LICENSES,
    PR79_ARTIFACT_MANIFEST_SHA256,
    PR79_REPORT_SHA256,
    PR79_RUN_MANIFEST_SHA256,
    PR79_SERVER_ROOT,
    PROTOCOL_V2_SHA256,
    REFERENCE_SHA256,
    SPLIT_SHA256,
    TASK_NAME,
    TASK_ROOT,
    TRAIN_ROOT,
    TRAIN_TREE_SHA256,
    atomic_json,
    ensure_task_roots,
    sha256_file,
    sha256_json,
    tree_identity,
)


def require(condition: bool, message: str) -> None:
    if not condition:
        raise RuntimeError(message)


def load_json(path):
    return json.loads(path.read_text(encoding="utf-8"))


def main() -> int:
    ensure_task_roots()
    report = PR79_SERVER_ROOT / "REPORT_PROVISION_TASK_LOCAL_7ZZ_AND_RESUME_ETH3D_ASSET_CONTRACT_AUDIT_V1.md"
    run_manifest = PR79_SERVER_ROOT / "run_manifest.json"
    require(sha256_file(report) == PR79_REPORT_SHA256, "PR79_REPORT_IDENTITY_DRIFT")
    require(sha256_file(run_manifest) == PR79_RUN_MANIFEST_SHA256, "PR79_RUN_MANIFEST_IDENTITY_DRIFT")
    upstream = load_json(run_manifest)
    require(upstream["branch"] == BASE_BRANCH, "PR79_BRANCH_DRIFT")
    require(upstream["FINAL_STATUS"] == "NO_ETH3D_DELIVERY_AREA_REFERENCE_ROUTE_BENCHMARK_CONTRACT", "PR79_STATUS_DRIFT")
    require(upstream["FINAL_DECISION"] == "CLOSE_ETH3D_DELIVERY_AREA_BEFORE_ENVIRONMENT_OR_TRAINING", "PR79_DECISION_DRIFT")
    require(upstream["protocol_v2_sha256"] == PROTOCOL_V2_SHA256, "PROTOCOL_IDENTITY_DRIFT")
    require(upstream["split_sha256"] == SPLIT_SHA256, "SPLIT_IDENTITY_DRIFT")
    require(upstream["train_only_colmap_tree_sha256"] == TRAIN_TREE_SHA256, "TRAIN_IDENTITY_DRIFT")
    require(upstream["reference_surface_sha256"] == REFERENCE_SHA256, "REFERENCE_IDENTITY_DRIFT")
    counters = upstream["counters"]
    for key in ("training_count", "training_environment_create_count", "model_or_map_generation_count", "controller_count"):
        require(counters[key] == 0, f"PR79_NONZERO_{key.upper()}")
    for root in (DATA_ROOT, TRAIN_ROOT, EVAL_ROOT, CONTRACTS, LICENSES):
        require(root.is_dir(), f"MISSING_DATA_COMPONENT:{root}")
    train_identity = tree_identity(TRAIN_ROOT)
    require(train_identity["tree_sha256"] == TRAIN_TREE_SHA256, "LIVE_TRAIN_TREE_IDENTITY_DRIFT")
    require(train_identity["file_count"] == 753, "LIVE_TRAIN_FILE_COUNT_DRIFT")
    split_identity = load_json(TRAIN_ROOT / "SPLIT_IDENTITY.json")
    require(split_identity["split_sha256"] == SPLIT_SHA256, "LIVE_SPLIT_IDENTITY_DRIFT")
    contract = load_json(TRAIN_ROOT / "TRAIN_ONLY_COLMAP_CONTRACT.json")
    require(contract["image_count"] == 748 and contract["point3d_count"] == 40092, "LIVE_TRAIN_CONTRACT_DRIFT")
    require(contract["colmap_execution_count"] == 0 and contract["reference_point_injection_count"] == 0, "TRAIN_CONTRACT_LEAKAGE")
    data_root_identity = {
        "train_tree_sha256": train_identity["tree_sha256"],
        "train_file_count": train_identity["file_count"],
        "train_total_bytes": train_identity["total_bytes"],
        "eval_root_device": int(os.stat(EVAL_ROOT).st_dev),
        "train_root_device": int(os.stat(TRAIN_ROOT).st_dev),
        "component_paths": {
            "TRAIN_INPUT_ROOT": str(TRAIN_ROOT),
            "EVAL_ORACLE_ROOT": str(EVAL_ROOT),
            "CONTRACTS": str(CONTRACTS),
            "LICENSES": str(LICENSES),
        },
    }
    result = {
        "status": "PR79_INPUT_FREEZE_PASS",
        "task": TASK_NAME,
        "branch": BRANCH,
        "base_branch": BASE_BRANCH,
        "base_head": BASE_HEAD,
        "recorded_utc": datetime.now(timezone.utc).isoformat(),
        "pr79_preserved": True,
        "pr79_planner_coupled_failure_remains_valid": True,
        "benchmark_role": "LOCAL_SAFETY_AND_CONTROLLER_STRESS_BENCHMARK",
        "not_benchmark_role": "PLANNER_COUPLED_GLOBAL_OBSTACLE_BENCHMARK",
        "identities": {
            "protocol_v2_sha256": PROTOCOL_V2_SHA256,
            "split_sha256": SPLIT_SHA256,
            "train_only_colmap_tree_sha256": TRAIN_TREE_SHA256,
            "reference_mesh_sha256": REFERENCE_SHA256,
            "pr79_report_sha256": PR79_REPORT_SHA256,
            "pr79_artifact_manifest_sha256": PR79_ARTIFACT_MANIFEST_SHA256,
            "pr79_artifact_manifest_identity_source": "CANONICAL_GIT_BLOB_AT_BASE_HEAD",
            "pr79_run_manifest_sha256": PR79_RUN_MANIFEST_SHA256,
        },
        "data_root_identity": data_root_identity,
        "upstream_execution_counts": {key: counters[key] for key in (
            "training_count", "training_environment_create_count", "model_or_map_generation_count", "controller_count"
        )},
        "training_authorized_by_current_task": True,
    }
    result["identity_sha256"] = sha256_json(result)
    atomic_json(TASK_ROOT / "input_freeze" / "pr79_and_data_identity.json", result)
    print("PR79_INPUT_FREEZE_PASS")
    print(json.dumps({"identity_sha256": result["identity_sha256"], "train_files": train_identity["file_count"]}, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
