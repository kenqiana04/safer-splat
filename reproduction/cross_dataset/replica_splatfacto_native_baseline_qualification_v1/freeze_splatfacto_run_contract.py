#!/usr/bin/env python3
"""Freeze the only allowed smoke and pilot execution contracts before training."""
from __future__ import annotations

from _common import ROOT, atomic_json, ensure_dirs, load_json, sha256_path


def main():
    ensure_dirs()
    authority = load_json(ROOT / "config_authority" / "splatfacto_native_configuration_authority.json")
    adapters = load_json(ROOT / "pilot_adapter" / "splatfacto_metric_dataset_adapter_identity.json")
    max_iterations = authority["authority"]["max_num_iterations"]
    contract = {
        "status": "SPLATFACTO_RUN_CONTRACT_FROZEN",
        "seed": 20260728,
        "physical_gpu": 1,
        "concurrent_splatfacto_runs": 1,
        "authority_config": authority["source_path"],
        "authority_config_sha256": authority["source_sha256"],
        "authority_max_num_iterations": max_iterations,
        "prohibited": {"official_eval_usage": 0, "depth_supervision": 0, "camera_optimization": 0, "pose_update": 0, "sim3": 0, "icp": 0, "scale_fitting": 0, "full_270_frame_training": 0},
        "smoke": {"adapter": adapters["adapters"]["smoke"], "max_num_iterations": min(2000, max_iterations), "wall_clock_cap_minutes": 45, "checkpoint_reload_required": True, "scientific_attempts": 1},
        "qualification_pilot": {"adapter": adapters["adapters"]["qualification_pilot"], "max_num_iterations": max_iterations, "wall_clock_cap_minutes": 180, "scientific_attempts": 1, "scientific_retry_forbidden": True},
        "infrastructure_retry": {"maximum": 1, "reasons": ["path", "environment_variable", "local_existing_cuda_extension", "permission", "stale_process", "log_conflict"], "fresh_output_required": True, "same_seed_config_and_frames_required": True},
        "allowed_task_owned_overrides": ["dataset path", "output path", "run name", "max iteration", "eval/save interval", "metric dataparser fields"],
        "core_hyperparameter_modification": False,
    }
    path = ROOT / "splatfacto_run_contract.json"
    atomic_json(path, contract)
    print(contract["status"])


if __name__ == "__main__":
    main()
