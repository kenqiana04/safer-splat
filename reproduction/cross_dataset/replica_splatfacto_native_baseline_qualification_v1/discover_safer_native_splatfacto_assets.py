#!/usr/bin/env python3
"""Bounded discovery of the already installed SAFER-native Splatfacto asset."""
from __future__ import annotations

from _common import AUTHORITY_CHECKPOINT, AUTHORITY_CONFIG, PYTHON, ROOT, SPLATNAV_REPO, atomic_json, capture, ensure_dirs, sha256_path, update_stage


def main():
    ensure_dirs()
    code = "from pathlib import Path\nfrom nerfstudio.utils.eval_utils import eval_setup\nc,p,k,s=eval_setup(Path(r'%s'),test_mode='inference')\nprint(type(p.model).__module__)\nprint(type(p.model).__name__)\nprint(k)\nprint(s)" % AUTHORITY_CONFIG
    load = capture([str(PYTHON), "-B", "-c", code], cwd=SPLATNAV_REPO, timeout=180)
    passed = AUTHORITY_CONFIG.is_file() and AUTHORITY_CHECKPOINT.is_file() and load["returncode"] == 0 and "SplatfactoModel" in load["stdout"]
    status = "SAFER_NATIVE_SPLATFACTO_ASSET_AVAILABLE" if passed else "BLOCKED_BY_SPLATFACTO_NATIVE_ASSET_OR_ENVIRONMENT_UNAVAILABLE"
    out = {"status": status, "bounded_search_roots": ["/disk1/zlab/projects", "/disk1/zlab/maintenance_records", "/disk1/zlab/conda_envs", "/disk1/zlab/cross_dataset_assets"], "environment_python": str(PYTHON), "splatnav_repository": str(SPLATNAV_REPO), "authority_config": str(AUTHORITY_CONFIG), "authority_config_sha256": sha256_path(AUTHORITY_CONFIG) if AUTHORITY_CONFIG.is_file() else None, "official_checkpoint": str(AUTHORITY_CHECKPOINT), "official_checkpoint_sha256": sha256_path(AUTHORITY_CHECKPOINT) if AUTHORITY_CHECKPOINT.is_file() else None, "native_loader_probe": load, "checkpoint_format": "Nerfstudio TrainerConfig YAML plus step-000029999.ckpt", "native_loader_entry": "nerfstudio.utils.eval_utils.eval_setup", "environment_mutated": False}
    atomic_json(ROOT / "native_asset_inventory" / "splatfacto_native_asset_inventory.json", out)
    update_stage("NATIVE_ASSET_AUDIT", "TERMINAL_SCIENTIFIC_RESULT" if passed else "FAILED_INFRASTRUCTURE", result_status=status)
    if not passed:
        raise SystemExit(status)
    print(status)


if __name__ == "__main__":
    main()
