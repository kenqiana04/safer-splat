#!/usr/bin/env python3
"""Freeze official source, submodule, environment, and prior-result identities."""
from __future__ import annotations

import argparse
import platform
from pathlib import Path

from arkitscenes_common import atomic_json, git_head, run, sha256_file


def package_versions() -> dict[str, str | None]:
    names = ("torch", "numpy", "open3d", "trimesh")
    values: dict[str, str | None] = {}
    for name in names:
        try:
            values[name] = __import__(name).__version__
        except Exception:
            values[name] = None
    return values


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--task-root", type=Path, required=True)
    parser.add_argument("--apple-source", type=Path, required=True)
    parser.add_argument("--splatam-source", type=Path, required=True)
    args = parser.parse_args()
    apple = args.apple_source.resolve()
    splatam = args.splatam_source.resolve()
    task = args.task_root.resolve()
    required = (apple / "download_data.py", apple / "raw" / "raw_train_val_splits.csv", apple / "LICENSE")
    if any(not path.is_file() for path in required):
        raise RuntimeError("BLOCKED_BY_ARKITSCENES_OFFICIAL_DOWNLOAD_ACCESS:authority files absent")
    submodules = run(["git", "submodule", "status", "--recursive"], cwd=splatam)
    if submodules["returncode"] != 0:
        raise RuntimeError("BLOCKED_BY_ARKITSCENES_SPLATAM_INFRASTRUCTURE:submodule status failed")
    atomic_json(task / "authority" / "arkitscenes_authority_identity.json", {
        "authority": "https://github.com/apple/ARKitScenes",
        "commit": git_head(apple),
        "download_data_py_sha256": sha256_file(apple / "download_data.py"),
        "raw_train_val_splits_csv_sha256": sha256_file(apple / "raw" / "raw_train_val_splits.csv"),
        "license_sha256": sha256_file(apple / "LICENSE"),
        "raw_asset_contract": ["mesh", "confidence", "lowres_depth", "lowres_wide.traj", "lowres_wide", "lowres_wide_intrinsics"],
        "faro_join_status": "FARO_TO_ARKIT_WORLD_JOIN_NOT_AUTHORIZED",
        "faro_download_count": 0,
    })
    atomic_json(task / "authority" / "splatam_authority_identity.json", {
        "authority": "https://github.com/spla-tam/SplaTAM",
        "commit": git_head(splatam),
        "submodule_status": submodules["stdout_tail"],
        "required_route": "scripts/gaussian_splatting.py GT-pose map-only",
        "forbidden": ["camera_tracking", "COLMAP", "Nerfstudio_camera_optimizer", "ICP", "Sim3", "pose_scale_fitting"],
    })
    cuda = run(["nvidia-smi", "-i", "1", "--query-gpu=index,name,uuid,driver_version,memory.total", "--format=csv,noheader"])
    atomic_json(task / "authority" / "environment_identity.json", {
        "python": platform.python_version(),
        "platform": platform.platform(),
        "packages": package_versions(),
        "gpu": cuda["stdout_tail"].strip(),
        "gpu_query_returncode": cuda["returncode"],
    })
    atomic_json(task / "frozen_pre_arkitscenes_research_ledger.json", {
        "TUM_navigation": "CLOSE_TUM_NAVIGATION_BENCHMARK_KEEP_SAFETY_CASE_STUDY",
        "TUM_Splatfacto": ["DIAGNOSTIC_ONLY", "GEOMETRY_NOT_QUALIFIED"],
        "Replica_Splatfacto": "CLOSE_SPLATFACTO_NAVIGATION_MAP_ROUTE",
        "Replica_SplaTAM": ["SPLATAM_REPLICA_60_FRAME_PILOT_GEOMETRY_NOT_QUALIFIED", "CLOSE_SPLATAM_REPLICA_MAPPING_ROUTE_UNDER_FROZEN_CONFIG"],
        "Replica_Gaussian_SLAM": ["NO_LEGAL_GAUSSIAN_SLAM_RESOLUTION_ADAPTATION_CONTRACT", "CLOSE_GAUSSIAN_SLAM_REPLICA_ROUTE_UNDER_OFFICIAL_CONFIG"],
        "public_pretrained_component_search": "CLOSE_PUBLIC_PRETRAINED_EXTERNAL_MAP_SEARCH",
        "prior_ARKit_component_join": "NO_ARKITSCENES_GS_TO_OFFICIAL_RGBD_FRAME_JOIN",
        "Replica_GT_derived_map": ["CERTIFIED_GT_GEOMETRY_DERIVED_GAUSSIAN_SAFETY_MAP", "NOT_LEARNED_3DGS"],
        "Replica_benchmark": "PASS_REPLICA_BOUNDED_DIRECT_GOAL_SAFER_FAS_CBF_BENCHMARK_COMPLETE",
        "ScanNetPP": ["BLOCKED_BY_SCANNETPP_V2_TOKEN_REQUIRED", "DEFER_SCANNETPP_PENDING_MANUAL_ACCESS", "NOT_A_SCIENTIFIC_FAILURE"],
    })
    print("AUTHORITY_FREEZE_PASS")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
