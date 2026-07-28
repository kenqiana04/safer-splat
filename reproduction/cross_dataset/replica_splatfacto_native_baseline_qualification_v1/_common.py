"""Immutable contracts and atomic bookkeeping for the Replica Splatfacto task."""
from __future__ import annotations

import hashlib
import json
import os
import subprocess
import time
from pathlib import Path

TASK = "replica_splatfacto_native_baseline_qualification_v1"
ROOT = Path("/disk1/zlab/maintenance_records") / TASK
DATASET = Path("/disk1/zlab/cross_dataset_assets/processed/replica/apartment_0.rendering_v3")
PR56_ROOT = Path("/disk1/zlab/maintenance_records/replica_rgbd_gaussian_mapping_frontend_qualification_v1")
SAFER_REPO = Path("/disk1/zlab/projects/safer-splat")
SPLATNAV_REPO = Path("/disk1/zlab/projects/splatnav")
PYTHON = Path("/disk1/zlab/conda_envs/splatnav/bin/python")
AUTHORITY_CONFIG = SPLATNAV_REPO / "outputs/flight/splatfacto/2024-09-12_172434/config.yml"
AUTHORITY_CHECKPOINT = SPLATNAV_REPO / "outputs/flight/splatfacto/2024-09-12_172434/nerfstudio_models/step-000029999.ckpt"
EXPECTED = {
    "pr56_head": "e2e6a48253df2a930f5dd0a3e09788adc5f53eb0",
    "complete_tree": "24e21d3bccceb0516ed8b9b49b426964f3954ccd0cd804eedd5846baabd66dcb",
    "content_tree": "60a9e0b517ba8e305c4b7ff010bb330c1e38c422c66899398129cce741a06bd0",
    "contract": "ddd147f908537165c40a34b412cd21c3cbfb5a0615871375d02adecbbfaec6f7",
    "manifest_csv": "6db89bc0dafaa5993b452216be1205ec9db0a1d9da23b9bc2b9029fabc2113d6",
    "manifest_json": "f029de724f33a2788c1f6570b5d730ec06f3223a2d512c38a0427ca9c1d14b2b",
    "transforms": "ec50b63a1263d9f6e355a6d5010ab79738d92d59f8bec481150d86f3145d888f",
    "pose": "0bc952fec3236d117b33d0d62085a60412b96e2174ab0a31c7c5fec204789622",
    "registry": "84edb118f01fe1460ff64be4b6ef838f23ed4520740af9f457041b438a7b9f5a",
    "rgb_tree": "d05a9fe3820cbbe019ab9891d0c13f9204254d49e910179c2d4326e38d4a57a4",
    "depth_tree": "707e6a8359e66e89bc72d7ee400a146fd86275274b7485359f3e2d85fc71b920",
    "pilot_selection_core": "1beaacaeb8a4126ff4410aae0b296702a7b84dfaee402e15d90d4f5d70741d19",
    "ingestion_order": "d3dc24d673c97700dc340785425abf8482827c0c81b72a6b33e6972b361c2fb1",
    "paired20": "380717f0ec39e0e422902573685f5a2838e78dd6efcce500ba71585efd3d82f6",
    "safer_head": "f63b4c496861c4f8881348d74244c1ff9a528d51",
}
STAGES = (
    "INPUT_IDENTITY", "NATIVE_ASSET_AUDIT", "CONFIG_AUTHORITY", "METRIC_DATAPARSER",
    "DATASET_ADAPTER", "COMMON_EVALUATOR_BINDING", "SMOKE", "SMOKE_EXPORT",
    "SMOKE_DIAGNOSTIC_EVALUATION", "QUALIFICATION_PILOT", "PILOT_EXPORT", "PILOT_GEOMETRY",
    "MAP_STRUCTURE", "SAFER_NATIVE_LOADER", "SAFER_NATIVE_G0", "SAFER_CANONICAL_G0",
    "DUAL_PATH_CONSISTENCY", "FINAL_CLASSIFICATION",
)
DIRS = (
    "input_identity", "native_asset_inventory", "environment_audit", "config_authority",
    "metric_dataparser", "pilot_adapter", "smoke", "qualification_pilot", "native_checkpoint",
    "canonical_export", "common_evaluation", "map_structure", "safer_native_loader", "safer_g0",
    "decision", "figures", "report", "logs", "tmp",
)


def ensure_dirs():
    for name in DIRS:
        (ROOT / name).mkdir(parents=True, exist_ok=True)


def sha256_path(path):
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for block in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def sha256_bytes(value):
    return hashlib.sha256(value).hexdigest()


def tree_sha(root, exclude=()):
    excluded = set(exclude)
    rows = []
    for path in sorted(item for item in root.rglob("*") if item.is_file()):
        relative = path.relative_to(root).as_posix()
        if relative not in excluded:
            rows.append(relative + "\0" + str(path.stat().st_size) + "\0" + sha256_path(path))
    return sha256_bytes("\n".join(rows).encode("utf-8")), len(rows)


def atomic_json(path, value):
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary = path.with_suffix(path.suffix + ".tmp")
    temporary.write_text(json.dumps(value, indent=2, ensure_ascii=False, sort_keys=True) + "\n", encoding="utf-8")
    with temporary.open("rb") as handle:
        os.fsync(handle.fileno())
    os.replace(str(temporary), str(path))


def load_json(path):
    return json.loads(path.read_text(encoding="utf-8"))


def manifest_path():
    return ROOT / "splatfacto_run_manifest.json"


def prohibited_counts(existing=None):
    counts = {
        "official_eval_frame_count_used": 0, "full_270_frame_training_count": 0,
        "depth_supervision_count": 0, "camera_optimizer_count": 0, "pose_optimization_count": 0,
        "auto_scale_count": 0, "auto_orient_count": 0, "centering_count": 0,
        "scene_contraction_count": 0, "colmap_count": 0, "sim3_count": 0, "icp_count": 0,
        "scale_fitting_count": 0, "hyperparameter_sweep_count": 0, "smoke_scientific_rerun_count": 0,
        "pilot_scientific_run_count": 0, "pilot_scientific_rerun_count": 0,
        "canonical_export_filter_count": 0, "safer_core_modification_count": 0,
        "safer_navigation_count": 0, "cbf_qp_count": 0, "start_safe_count": 0,
        "risk_aware_count": 0, "recovery_v4c_count": 0, "splatam_rerun_count": 0,
        "gaussian_slam_rerun_count": 0, "tum_rollout_count": 0, "infrastructure_retry_count": 0,
    }
    if existing:
        counts["infrastructure_retry_count"] = int(existing.get("infrastructure_retry_count", 0))
        counts["pilot_scientific_run_count"] = int(existing.get("pilot_scientific_run_count", 0))
    return counts


def initial_manifest(pr56_head):
    return {
        "task": TASK, "pr56_head": pr56_head, "physical_gpu": 1,
        "stages": {stage: "NOT_STARTED" for stage in STAGES},
        "stage_details": {}, "prohibited_counts": prohibited_counts(),
    }


def ensure_manifest(pr56_head):
    if not manifest_path().exists():
        atomic_json(manifest_path(), initial_manifest(pr56_head))
    return load_json(manifest_path())


def update_stage(stage, state, **detail):
    if state not in ("NOT_STARTED", "RUNNING", "TERMINAL_SCIENTIFIC_RESULT", "FAILED_INFRASTRUCTURE", "NOT_AUTHORIZED_DUE_TO_GATE"):
        raise ValueError("invalid manifest state: " + state)
    payload = load_json(manifest_path())
    payload["stages"][stage] = state
    payload.setdefault("stage_details", {})[stage] = detail
    payload["prohibited_counts"] = prohibited_counts(payload.get("prohibited_counts"))
    atomic_json(manifest_path(), payload)


def gate_after(stage, reason):
    payload = load_json(manifest_path())
    seen = False
    for item in STAGES:
        if item == stage:
            seen = True
            continue
        if seen and payload["stages"][item] == "NOT_STARTED":
            payload["stages"][item] = "NOT_AUTHORIZED_DUE_TO_GATE"
            payload.setdefault("stage_details", {})[item] = {"reason": reason}
    payload["prohibited_counts"] = prohibited_counts(payload.get("prohibited_counts"))
    atomic_json(manifest_path(), payload)


def increment_infrastructure_retry(reason):
    payload = load_json(manifest_path())
    counts = prohibited_counts(payload.get("prohibited_counts"))
    counts["infrastructure_retry_count"] += 1
    payload["prohibited_counts"] = counts
    payload.setdefault("infrastructure_retries", []).append({"index": counts["infrastructure_retry_count"], "reason": reason, "authorized": True})
    atomic_json(manifest_path(), payload)


def annotate_infrastructure_retry(detail):
    payload = load_json(manifest_path())
    entries = payload.setdefault("infrastructure_retries", [])
    if not entries:
        raise RuntimeError("cannot annotate a retry that was not recorded")
    entries[-1].setdefault("repair_steps", []).append(detail)
    atomic_json(manifest_path(), payload)


def set_actual_count(name, value):
    payload = load_json(manifest_path())
    counts = prohibited_counts(payload.get("prohibited_counts"))
    if name not in counts:
        raise KeyError(name)
    counts[name] = int(value)
    payload["prohibited_counts"] = counts
    atomic_json(manifest_path(), payload)


def task_env():
    env = os.environ.copy()
    env.update({
        "CUDA_VISIBLE_DEVICES": "1", "PYTHONNOUSERSITE": "1", "PYTHONDONTWRITEBYTECODE": "1",
        "CUDA_HOME": "/usr/local/cuda-11.8",
        "TORCH_EXTENSIONS_DIR": str(ROOT / "torch_extensions_cuda118"),
        "PATH": "/disk1/zlab/conda_envs/splatnav/bin:/usr/local/cuda-11.8/bin:" + env.get("PATH", ""),
    })
    return env


def capture(command, cwd=None, timeout=120, env=None):
    started = time.time()
    try:
        result = subprocess.run(command, cwd=str(cwd) if cwd else None, env=env or task_env(), stdout=subprocess.PIPE, stderr=subprocess.STDOUT, text=True, timeout=timeout)
        return {"command": command, "returncode": result.returncode, "timeout": False, "wall_seconds": time.time() - started, "stdout": result.stdout[-16000:]}
    except subprocess.TimeoutExpired as exc:
        return {"command": command, "returncode": None, "timeout": True, "wall_seconds": time.time() - started, "stdout": (exc.stdout or "")[-16000:]}
