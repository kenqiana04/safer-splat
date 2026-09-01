#!/usr/bin/env python3
"""Fail-closed pre-data identity audit for the authoritative 4090 host."""

from __future__ import annotations

import argparse
import hashlib
import json
import os
import platform
import subprocess
from pathlib import Path
from typing import Any

from collection_common import (
    EXPECTED_UPSTREAM_HEAD, MAP_AUTHORITY_ID, OFFICIAL100_SHA256, PROTOCOL_SHA256,
    atomic_write_json, file_sha256, semantic_sha256,
)


def git(checkout: Path, *args: str, binary: bool = False) -> Any:
    result = subprocess.run(["git", "-C", str(checkout), *args], stdout=subprocess.PIPE, stderr=subprocess.PIPE, check=True)
    return result.stdout if binary else result.stdout.decode("utf-8").strip()


def map_identity(checkout: Path) -> tuple[str, list[dict[str, Any]]]:
    root = (checkout / "outputs/stonehenge/splatfacto/2024-09-11_100724").resolve(strict=True)
    relatives = sorted(("config.yml", "dataparser_transforms.json", "nerfstudio_models/step-000029999.ckpt"))
    records = [{"relative_path": rel, "size": (root / rel).stat().st_size, "sha256": file_sha256(root / rel)} for rel in relatives]
    semantic = {
        "schema_version": "MAP_AUTHORITY_MANIFEST_V1", "logical_map_name": "STONEHENGE_OFFICIAL_SAFER_MAP",
        "artifacts": records, "representation_contract": "OFFICIAL_NERFSTUDIO_SPLATFACTO_ANISOTROPIC_GAUSSIAN_MAP",
        "robot_radius": 0.10, "safety_margin": 0.01, "effective_radius": 0.11, "rho_seg": 0.0,
    }
    return semantic_sha256(semantic), records


def protocol_identity(checkout: Path) -> tuple[str, dict[str, str]]:
    root = "reproduction/protocol/l2_h1_prospective_shadow_cohort_v1"
    lock = json.loads(git(checkout, "show", f"{EXPECTED_UPSTREAM_HEAD}:{root}/PROTOCOL_LOCK.json"))
    actual = {}
    for name in sorted(lock["per_file_sha256"]):
        raw = git(checkout, "cat-file", "blob", f"{EXPECTED_UPSTREAM_HEAD}:{root}/{name}", binary=True)
        actual[name] = hashlib.sha256(raw).hexdigest()
    if actual != lock["per_file_sha256"]:
        raise RuntimeError("raw Git blob protocol per-file identity mismatch")
    records = [{"path": name, "sha256": actual[name]} for name in sorted(actual)]
    combined = semantic_sha256(records)
    if combined != PROTOCOL_SHA256 or lock["combined_protocol_sha256"] != PROTOCOL_SHA256:
        raise RuntimeError("raw Git blob combined protocol identity mismatch")
    return combined, actual


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--checkout", type=Path, required=True)
    parser.add_argument("--task-root", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    checkout = args.checkout.resolve(strict=True)
    head = git(checkout, "rev-parse", "HEAD")
    if head != EXPECTED_UPSTREAM_HEAD:
        raise RuntimeError("PR100 checkout head mismatch")
    combined, protocol_files = protocol_identity(checkout)
    official = checkout / "reproduction/experiment_protocol_freeze_v1/trial_manifests/stonehenge_official100_manifest.csv"
    if file_sha256(official) != OFFICIAL100_SHA256:
        raise RuntimeError("official100 raw-byte identity mismatch")
    manifest = json.loads((checkout / "reproduction/protocol/l2_h1_prospective_shadow_cohort_v1/formal_trial_manifest.json").read_text(encoding="utf-8"))
    if manifest.get("trial_count") != 100 or [row["trial_id"] for row in manifest["trials"]] != list(range(100)):
        raise RuntimeError("formal manifest order/coverage mismatch")
    map_id, map_artifacts = map_identity(checkout)
    if map_id != MAP_AUTHORITY_ID:
        raise RuntimeError("map authority identity mismatch")
    run_py = checkout / "run.py"
    run_py_blob = git(checkout, "rev-parse", f"{EXPECTED_UPSTREAM_HEAD}:run.py")
    if run_py_blob != "361f09fc8f37e4713ea2fc8975d82d56cb9be46a" or file_sha256(run_py) != "c6adfe77ca69658566c8028f2b24ef4ebda4af0662868d39c348ee81d3f0199c":
        raise RuntimeError("controller entry identity mismatch")
    instrumentation_tree = git(checkout, "rev-parse", f"{EXPECTED_UPSTREAM_HEAD}:reproduction/instrumentation/l2_h1_on_policy_shadow_instrumentation_v1")
    frozen_runner = checkout / "reproduction/equivalence/l2_h1_shadow_instrumentation_off_vs_on_v1/server_run_one.py"
    formal_root = args.task_root / "formal-v1"
    formal_files = list(formal_root.rglob("*")) if formal_root.exists() else []
    if formal_files:
        raise RuntimeError("formal artifact namespace is not empty before execution lock")
    import numpy
    import torch
    if os.environ.get("CUDA_VISIBLE_DEVICES") != "1" or not torch.cuda.is_available() or torch.cuda.device_count() != 1:
        raise RuntimeError("CUDA_VISIBLE_DEVICES/GPU visibility mismatch")
    device_name = torch.cuda.get_device_name(0)
    if device_name != "NVIDIA GeForce RTX 4090":
        raise RuntimeError("physical GPU identity mismatch")
    identity = {
        "schema_version": "L2_H1_FORMAL_COLLECTION_ENVIRONMENT_IDENTITY_V1",
        "upstream_head": head, "protocol_sha256": combined, "protocol_raw_git_blob_file_count": len(protocol_files),
        "official100_sha256": OFFICIAL100_SHA256, "official100_trial_count": 100, "official100_order": "0..99",
        "controller_identity": {"run_py_git_blob": run_py_blob, "run_py_sha256": file_sha256(run_py), "runtime_baseline_commit": "7d48bf6c3b8932aa65d851c3cd70404404453cb3"},
        "instrumentation_identity": {"git_tree": instrumentation_tree, "frozen_server_runner_sha256": file_sha256(frozen_runner)},
        "python": platform.python_version(), "python_executable": os.path.realpath(os.sys.executable),
        "torch": torch.__version__, "torch_cuda": torch.version.cuda, "numpy": numpy.__version__,
        "cuda_visible_devices": "1", "physical_gpu_index": 1, "cuda_device_name": device_name,
        "map_authority_id": map_id, "map_artifacts": map_artifacts,
        "dt": 0.05, "robot_radius": 0.10, "safety_margin": 0.01, "rho_seg": 0.0,
        "formal_navigation_run_count": 0, "formal_intended_step_count": 0,
        "formal_capture_count": 0, "formal_result_count": 0,
        "created_before_first_formal_observation": True,
    }
    atomic_write_json(args.output, identity)
    print(json.dumps({
        "status": "PASS_PRE_DATA_ENVIRONMENT_IDENTITY", "upstream_head": head,
        "protocol_sha256": combined, "official100_sha256": OFFICIAL100_SHA256,
        "map_authority_id": map_id, "formal_navigation_run_count": 0,
    }, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
