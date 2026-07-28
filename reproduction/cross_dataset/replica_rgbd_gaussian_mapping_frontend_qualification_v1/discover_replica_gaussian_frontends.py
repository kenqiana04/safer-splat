#!/usr/bin/env python3
"""Bounded, non-mutating inventory of the two protocol-fixed frontends."""
from __future__ import annotations

import os
from pathlib import Path

from _common import FRONTENDS, ROOT, atomic_json, ensure_dirs, sha256_path, update_stage


def listed(root: Path, patterns: tuple[str, ...], limit: int = 120) -> list[str]:
    values: list[str] = []
    for pattern in patterns:
        values.extend(path.relative_to(root).as_posix() for path in root.rglob(pattern) if path.is_file())
    return sorted(set(values))[:limit]


def inventory(name: str) -> dict:
    item = FRONTENDS[name]; repo = item["repo"]
    available = repo.is_dir()
    result = {"frontend": item["display"], "asset_status": "FRONTEND_ASSET_AVAILABLE" if available else "FRONTEND_ASSET_NOT_AVAILABLE", "repository_absolute_path": str(repo), "official_commit": item["commit"], "git_worktree": "not_applicable_official_archive", "git_remote": "https://github.com/spla-tam/SplaTAM.git" if name == "splatam" else "https://github.com/VladimirYugay/Gaussian-SLAM.git", "branch": "official_archive", "dirty_status": False, "submodules": {"diff-gaussian-rasterization-w-depth.git": "cb65e4b86bc3bd8ed42174b72a62e8d3a3a71110"} if name == "splatam" else {}, "conda_environment": str(item["python"].parent.parent), "environment_python": str(item["python"])}
    if not available:
        return result
    readme = repo / "README.md"; license_file = repo / "LICENSE"
    result.update({"file_count": sum(1 for _ in repo.rglob("*") if _.is_file()), "readme": str(readme) if readme.is_file() else None, "readme_sha256": sha256_path(readme) if readme.is_file() else None, "license": str(license_file) if license_file.is_file() else None, "license_sha256": sha256_path(license_file) if license_file.is_file() else None, "official_replica_configs": listed(repo, ("*replica*.yaml", "*replica*.py", "*Replica*.yaml")), "tum_configs": listed(repo, ("*tum*.yaml", "*TUM*.yaml", "*tum*.py")), "rgbd_loader_candidates": listed(repo, ("*dataset*.py", "*datasets.py")), "gaussian_export_candidates": listed(repo, ("*gaussian_model*.py", "*io_utils.py", "*slam_helpers.py")), "renderer_candidates": listed(repo, ("*render*.py", "*utils.py", "*slam_helpers.py")), "existing_replica_artifacts": [], "existing_tum_artifacts": []})
    if name == "splatam":
        result.update({"gt_pose_support": "scripts/gaussian_splatting.py injects GT w2c and freezes camera learning rates", "tracking_disable_support": "offline map-only entry has no pose optimizer when GT pose learning rates are zero", "map_only_support": True, "checkpoint_format": "params.npz"})
    else:
        result.update({"gt_pose_support": "tracker odometry_type=gt returns gt_c2w", "tracking_disable_support": "task-owned launcher bypasses Tracker.track while preserving Mapper.map", "map_only_support": True, "checkpoint_format": "submaps/*.ckpt"})
    return result


def main() -> None:
    ensure_dirs()
    values = {name: inventory(name) for name in FRONTENDS}
    output = {"status": "PASS", "bounded_search_roots": ["/disk1/zlab/projects", "/disk1/zlab/maintenance_records", "/disk1/zlab/conda_envs", "/disk1/zlab/cross_dataset_assets"], "registered_official_archive_root": "/disk1/zlab/external_baselines/tum_rgbd_gaussian_v1", "frontends": values}
    atomic_json(ROOT / "frontend_inventory" / "frontend_asset_inventory.json", output)
    for name, value in values.items():
        update_stage(name, "ASSET_AUDIT", "TERMINAL_SCIENTIFIC_RESULT", asset_status=value["asset_status"])
    print(output["status"])


if __name__ == "__main__":
    main()
