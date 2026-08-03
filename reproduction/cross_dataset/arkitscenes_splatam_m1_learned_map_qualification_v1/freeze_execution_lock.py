#!/usr/bin/env python3
"""Freeze the exact one-attempt formal M1 mapper execution identity."""

from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path


def sha(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--task-root", type=Path, required=True)
    parser.add_argument("--env-prefix", type=Path, required=True)
    args = parser.parse_args()
    root = args.task_root.resolve()
    runtime = root / "runtime_checkout" / "SplaTAM-m1-empty-depth-safe"
    formal_output = root / "outputs" / "ARKITSCENES_SPLATAM_M1_EMPTY_DEPTH_SAFE_GT_POSE_MAP_ONLY_V1"
    required = {
        "input_identity": root / "input_identity_freeze.json",
        "runtime_identity": root / "runtime_integration" / "runtime_identity.json",
        "config_diff": root / "config" / "resolved_config_diff.json",
        "formal_config": root / "config" / "formal.py",
        "compatibility": runtime / "empty_depth_safe_splatam_compat.py",
        "runtime_script": runtime / "scripts" / "gaussian_splatting.py",
        "train_manifest": root / "staging" / "arkitscenes_train_manifest_v2.csv",
        "evaluation_registry": root / "evaluation_freeze" / "registry_freeze.json",
        "clearance_registry": root / "evaluation_freeze" / "clearance_registry.npz",
        "g0_registry": root / "evaluation_freeze" / "g0_query_registry.npz",
        "smoke_a": root / "smoke" / "smoke_a_validation.json",
        "smoke_b": root / "smoke" / "smoke_b_validation.json",
    }
    missing = [name for name, path in required.items() if not path.is_file()]
    if missing:
        raise RuntimeError(f"execution lock prerequisites missing: {missing}")
    if formal_output.exists():
        raise RuntimeError("formal output already exists before lock")
    smoke_a = json.loads(required["smoke_a"].read_text(encoding="utf-8"))
    smoke_b = json.loads(required["smoke_b"].read_text(encoding="utf-8"))
    if not smoke_a["pass"] or not smoke_b["pass"]:
        raise RuntimeError("smoke gate failed")
    command = [
        "env", "CUDA_VISIBLE_DEVICES=1", "PYTHONNOUSERSITE=1", "PYTHONDONTWRITEBYTECODE=1",
        f"PYTHONPATH={runtime}:/disk1/zlab/maintenance_records/arkitscenes_splatam_canonical_learned_map_qualification_v1/environment/runtime_overlay_setuptools_81_0_0",
        f"SPLATAM_M1_EVENT_LOG={root / 'events' / 'formal.jsonl'}", "SPLATAM_M1_INDEX_OFFSET=0",
        str(args.env_prefix / "bin" / "python"), "-u", "scripts/gaussian_splatting.py", str(root / "config" / "formal.py"),
    ]
    lock = {
        "status": "PASS_ARKITSCENES_M1_FORMAL_EXECUTION_LOCK",
        "task": "ARKITSCENES_SPLATAM_M1_EMPTY_DEPTH_SAFE_GT_POSE_MAP_ONLY_V1",
        "scene": "48018874",
        "seed": 20260730,
        "physical_gpu": 1,
        "cuda_visible_device": "1",
        "mapper_role": "SPLATAM_DERIVED_GT_POSE_MAP_ONLY_WITH_EMPTY_DEPTH_SAFE_COMPATIBILITY",
        "train_frames": 214,
        "heldout_mapper_access_expected": 0,
        "max_formal_attempts": 2,
        "retry_contract": "only explicit infrastructure failure before final params; no scientific retry; no rerun after complete params",
        "exact_command_argv": command,
        "artifact_sha256": {name: sha(path) for name, path in required.items()},
        "formal_output_absent": True,
        "formal_attempt_count_before_launch": 0,
        "checkpoint": False,
        "controller_count": 0,
        "forbidden": ["M0", "M2", "delete 76/79", "HELDOUT mapper access", "hyperparameter change", "opacity filtering", "ICP", "Sim3", "controller benchmark"],
    }
    path = root / "execution_lock.json"
    path.write_text(json.dumps(lock, indent=2, sort_keys=True) + "\n", encoding="utf-8", newline="\n")
    digest = sha(path)
    (root / "execution_lock.sha256").write_text(f"{digest}  execution_lock.json\n", encoding="utf-8", newline="\n")
    print(f"PASS_EXECUTION_LOCK_SHA256={digest}")


if __name__ == "__main__":
    main()

