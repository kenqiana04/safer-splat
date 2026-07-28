#!/usr/bin/env python3
"""Freeze the only allowed path/frame/pose adaptations before frontend execution."""
from __future__ import annotations

from _common import FRONTENDS, ROOT, atomic_json, ensure_dirs, load_json, sha256_path


def main() -> None:
    ensure_dirs(); registry = load_json(ROOT / "pilot_registry" / "replica_frontend_pilot_registry.json"); order = load_json(ROOT / "pilot_registry" / "replica_frontend_map_only_order.json"); camera = load_json(ROOT / "input_contract" / "replica_mapping_input_contract.json")
    source = {"splatam": FRONTENDS["splatam"]["repo"] / "configs" / "replica" / "gaussian_splatting.py", "gaussian_slam": FRONTENDS["gaussian_slam"]["repo"] / "configs" / "Replica" / "room0.yaml"}
    contract = {"status": "PASS_FRONTEND_PILOT_CONFIGURATION_FROZEN", "registry_sha256": registry["registry_sha256"], "frame_order_sha256": order["frame_order_sha256"], "input_contract_sha256": camera["contract_sha256"], "physical_gpu": 1, "cuda_visible_devices": "1", "seed": 0, "official_eval_usage_count": 0, "frontends": {}}
    for name, item in FRONTENDS.items():
        contract["frontends"][name] = {"repository": str(item["repo"]), "repository_commit": item["commit"], "environment_python": str(item["python"]), "official_config_source": str(source[name]), "official_config_source_sha256": sha256_path(source[name]), "dataset_adapter_sha256": sha256_path(__import__("pathlib").Path(__file__)), "gt_pose_mode": True, "tracking_disabled": True, "pose_optimization_disabled": True, "scale_fitting": False, "sim3": False, "intrinsics": {key: camera[key] for key in ("width", "height", "fx", "fy", "cx", "cy")}, "depth_scale_m": camera["depth_decode_scale_m"], "mapping_frames": 60, "holdout_frames": 30, "smoke_mapping_frames": 16, "smoke_holdout_frames": 8, "mapping_frame_order": order["mapping_frame_order"], "holdout_frame_order": order["holdout_frame_order"], "smoke_mapping_frame_order": order["smoke_mapping_frame_ids"], "smoke_holdout_frame_order": order["smoke_holdout_frame_ids"], "wall_clock_cap_seconds": {"smoke": 1800, "pilot": 7200}, "optimization_budget_source": "unaltered official Replica configuration", "densification_pruning_keyframe_source": "unaltered official Replica configuration", "checkpoint_interval_source": "unaltered official Replica configuration", "export_format": "canonical arrays without filtering"}
    atomic_json(ROOT / "pilot_registry" / "frontend_pilot_configuration_contract.json", contract); print(contract["status"])


if __name__ == "__main__":
    main()
