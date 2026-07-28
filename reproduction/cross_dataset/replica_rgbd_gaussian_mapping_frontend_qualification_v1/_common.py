"""Shared immutable contracts and compact-result helpers for Replica frontend qualification."""
from __future__ import annotations

import hashlib
import json
import os
import subprocess
import time
from pathlib import Path
from typing import Any, Iterable

TASK = "replica_rgbd_gaussian_mapping_frontend_qualification_v1"
ROOT = Path("/disk1/zlab/maintenance_records") / TASK
DATASET = Path("/disk1/zlab/cross_dataset_assets/processed/replica/apartment_0.rendering_v3")
SPLATAM_REPO = Path("/disk1/zlab/external_baselines/tum_rgbd_gaussian_v1/repos/SplaTAM_official_archive")
GAUSSIAN_SLAM_REPO = Path("/disk1/zlab/external_baselines/tum_rgbd_gaussian_v1/repos/Gaussian-SLAM_official_archive")
SPLATAM_PYTHON = Path("/disk1/zlab/external_baselines/tum_rgbd_gaussian_v1/envs/tum_splatam_baseline_v1/bin/python")
GAUSSIAN_SLAM_PYTHON = Path("/disk1/zlab/external_baselines/tum_rgbd_gaussian_v1/envs/tum_gaussian_slam_baseline_v1_conda/bin/python")
SAFER_REPO = Path("/disk1/zlab/projects/safer-splat")
EXPECTED = {
    "pr55_head": "c5d7e3899a98247407f4135234b75bfbcf75bb4c",
    "contract": "ddd147f908537165c40a34b412cd21c3cbfb5a0615871375d02adecbbfaec6f7",
    "manifest_csv": "6db89bc0dafaa5993b452216be1205ec9db0a1d9da23b9bc2b9029fabc2113d6",
    "manifest_json": "f029de724f33a2788c1f6570b5d730ec06f3223a2d512c38a0427ca9c1d14b2b",
    "transforms": "ec50b63a1263d9f6e355a6d5010ab79738d92d59f8bec481150d86f3145d888f",
    "pose": "0bc952fec3236d117b33d0d62085a60412b96e2174ab0a31c7c5fec204789622",
    "registry": "84edb118f01fe1460ff64be4b6ef838f23ed4520740af9f457041b438a7b9f5a",
    "rgb_tree": "d05a9fe3820cbbe019ab9891d0c13f9204254d49e910179c2d4326e38d4a57a4",
    "depth_tree": "707e6a8359e66e89bc72d7ee400a146fd86275274b7485359f3e2d85fc71b920",
    "content_tree": "60a9e0b517ba8e305c4b7ff010bb330c1e38c422c66899398129cce741a06bd0",
    "complete_tree": "24e21d3bccceb0516ed8b9b49b426964f3954ccd0cd804eedd5846baabd66dcb",
    "paired20": "380717f0ec39e0e422902573685f5a2838e78dd6efcce500ba71585efd3d82f6",
}
FRONTENDS = {
    "splatam": {"display": "SplaTAM", "repo": SPLATAM_REPO, "python": SPLATAM_PYTHON, "commit": "da6bbcd24c248dc884ac7f49d62e91b841b26ccc"},
    "gaussian_slam": {"display": "Gaussian-SLAM", "repo": GAUSSIAN_SLAM_REPO, "python": GAUSSIAN_SLAM_PYTHON, "commit": "eaec10d73ce7511563882b8856896e06d1f804e3"},
}
DIRS = ("input_identity", "frontend_inventory", "environment_audit", "input_contract", "pilot_registry", "common_evaluator", "splatam", "gaussian_slam", "canonical_exports", "geometry_evaluation", "safer_g0", "decision", "figures", "report", "logs", "tmp")


def ensure_dirs() -> None:
    for name in DIRS:
        (ROOT / name).mkdir(parents=True, exist_ok=True)


def sha256_path(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for block in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def sha256_bytes(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def tree_sha(root: Path, exclude: Iterable[str] = ()) -> tuple[str, int]:
    excluded = set(exclude)
    rows: list[str] = []
    for path in sorted(item for item in root.rglob("*") if item.is_file()):
        relative = path.relative_to(root).as_posix()
        if relative not in excluded:
            rows.append(relative + "\0" + str(path.stat().st_size) + "\0" + sha256_path(path))
    return sha256_bytes("\n".join(rows).encode("utf-8")), len(rows)


def atomic_json(path: Path, value: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary = path.with_suffix(path.suffix + ".tmp")
    temporary.write_text(json.dumps(value, indent=2, ensure_ascii=False, sort_keys=True) + "\n", encoding="utf-8")
    with temporary.open("rb") as handle:
        os.fsync(handle.fileno())
    os.replace(temporary, path)


def load_json(path: Path) -> Any:
    return json.loads(path.read_text(encoding="utf-8"))


def now() -> float:
    return time.time()


def task_env() -> dict[str, str]:
    env = os.environ.copy()
    env.update({"CUDA_VISIBLE_DEVICES": "1", "PYTHONNOUSERSITE": "1", "PYTHONDONTWRITEBYTECODE": "1"})
    return env


def run_capture(command: list[str], *, cwd: Path | None = None, timeout: int = 180, env: dict[str, str] | None = None) -> dict[str, Any]:
    started = now()
    try:
        result = subprocess.run(command, cwd=cwd, env=env or task_env(), text=True, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, timeout=timeout, check=False)
        return {"command": command, "returncode": result.returncode, "stdout": result.stdout[-16000:], "wall_seconds": now() - started, "timeout": False}
    except subprocess.TimeoutExpired as exc:
        return {"command": command, "returncode": None, "stdout": (exc.stdout or "")[-16000:] if isinstance(exc.stdout, str) else "", "wall_seconds": now() - started, "timeout": True}


def manifest_path() -> Path:
    return ROOT / "frontend_run_manifest.json"


def initial_manifest() -> dict[str, Any]:
    stages = ("ASSET_AUDIT", "ENVIRONMENT_AUDIT", "CAPABILITY_GATE", "SMOKE", "QUALIFICATION_PILOT", "CANONICAL_EXPORT", "COMMON_EVALUATION", "SAFER_G0", "FINAL_CLASSIFICATION")
    return {"task": TASK, "gpu_physical": 1, "official_eval_usage_count": 0, "frontends": {name: {stage: "NOT_STARTED" for stage in stages} for name in FRONTENDS}, "prohibited_counts": prohibited_counts()}


def prohibited_counts() -> dict[str, int]:
    return {"official_eval_frame_count_used": 0, "full_270_frame_training_count": 0, "tracking_count": 0, "pose_optimization_count": 0, "scale_fitting_count": 0, "sim3_count": 0, "frontend_core_modification_count": 0, "hyperparameter_sweep_count": 0, "scientific_rerun_count": 0, "infrastructure_retry_count": 0, "safer_navigation_count": 0, "cbf_qp_rollout_count": 0, "start_safe_count": 0, "risk_aware_count": 0, "recovery_v4c_count": 0, "tum_rollout_count": 0}


def update_stage(frontend: str, stage: str, status: str, **detail: Any) -> None:
    payload = load_json(manifest_path()) if manifest_path().exists() else initial_manifest()
    payload["frontends"][frontend][stage] = status
    payload.setdefault("stage_details", {}).setdefault(frontend, {})[stage] = detail
    atomic_json(manifest_path(), payload)


def mark_not_authorized(frontend: str, after_stage: str) -> None:
    stages = ("ASSET_AUDIT", "ENVIRONMENT_AUDIT", "CAPABILITY_GATE", "SMOKE", "QUALIFICATION_PILOT", "CANONICAL_EXPORT", "COMMON_EVALUATION", "SAFER_G0", "FINAL_CLASSIFICATION")
    payload = load_json(manifest_path()) if manifest_path().exists() else initial_manifest()
    skip = False
    for stage in stages:
        if stage == after_stage:
            skip = True
            continue
        if skip and (payload["frontends"][frontend][stage] == "NOT_STARTED" or payload["frontends"][frontend][stage].startswith("NOT_AUTHORIZED_DUE_TO_")):
            # The manifest has a deliberately closed stage-state vocabulary.
            # The more specific causal string belongs in the compact artifact.
            payload["frontends"][frontend][stage] = "NOT_AUTHORIZED"
            payload.setdefault("stage_details", {}).setdefault(frontend, {})[stage] = {
                "reason": f"NOT_AUTHORIZED_DUE_TO_{after_stage}"
            }
    atomic_json(manifest_path(), payload)


def compact_path(name: str) -> Path:
    return Path(__file__).resolve().parent / name
