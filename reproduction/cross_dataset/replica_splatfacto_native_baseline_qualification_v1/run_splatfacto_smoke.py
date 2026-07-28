#!/usr/bin/env python3
"""Run the sole 16-frame operational Splatfacto smoke without judging geometry."""
from __future__ import annotations

import argparse
import os
import subprocess
import sys
import time
from pathlib import Path

from _common import AUTHORITY_CONFIG, PYTHON, ROOT, SPLATNAV_REPO, annotate_infrastructure_retry, atomic_json, ensure_dirs, increment_infrastructure_retry, load_json, sha256_path, task_env, update_stage


def _prepare(stage, attempt):
    import yaml
    contract = load_json(ROOT / "splatfacto_run_contract.json")
    spec = contract[stage]
    config = yaml.load(AUTHORITY_CONFIG.read_text(encoding="utf-8"), Loader=yaml.Loader)
    adapter = Path(spec["adapter"]["root"])
    config.data = adapter
    config.pipeline.datamanager.data = adapter
    config.pipeline.datamanager.dataparser.data = adapter
    parser = config.pipeline.datamanager.dataparser
    parser.orientation_method = "none"; parser.center_method = "none"; parser.auto_scale_poses = False
    parser.scale_factor = 1.0; parser.scene_scale = 1.0; parser.eval_mode = "filename"
    config.max_num_iterations = spec["max_num_iterations"]
    config.steps_per_save = min(1000, max(1, config.max_num_iterations))
    config.steps_per_eval_image = min(500, max(1, config.max_num_iterations))
    config.steps_per_eval_all_images = config.max_num_iterations
    config.output_dir = ROOT / stage / ("outputs" if attempt == 0 else "outputs_infrastructure_retry_" + str(attempt) + "_cuda118")
    config.experiment_name = "replica_splatfacto_native_" + stage
    config.timestamp = "seed_20260728"
    config.machine.seed = contract["seed"]
    config.vis = "tensorboard"
    config.viewer.quit_on_train_completion = True
    base = config.get_base_dir()
    base.mkdir(parents=True, exist_ok=True)
    config.save_config()
    return config, base, spec


def _inner(stage, attempt):
    from nerfstudio.scripts.train import train_loop
    config, base, spec = _prepare(stage, attempt)
    atomic_json(base / "launch_contract.json", {"stage": stage, "attempt": attempt, "adapter": spec["adapter"], "max_num_iterations": spec["max_num_iterations"], "seed": config.machine.seed, "physical_gpu": 1, "core_parameters_from_authority": True})
    train_loop(0, 1, config)


def _run(stage, success, failure_prefix, attempt=0, reuse_authorized_retry=False):
    ensure_dirs()
    contract = load_json(ROOT / "splatfacto_run_contract.json")
    spec = contract[stage]
    update_stage("SMOKE" if stage == "smoke" else "QUALIFICATION_PILOT", "RUNNING", run_stage=stage, expected_iterations=spec["max_num_iterations"])
    if attempt and not reuse_authorized_retry:
        increment_infrastructure_retry("relative launcher path prevented process startup before trainer initialization")
    if attempt and reuse_authorized_retry:
        annotate_infrastructure_retry("CUDA 11.7 cannot target RTX 4090 sm_89; task-owned CUDA 11.8 JIT cache built and verified _C.CameraModelType before retrying the same smoke contract")
    log = ROOT / stage / "logs" / ("train.log" if attempt == 0 else "train_infrastructure_retry_" + str(attempt) + "_cuda118.log"); log.parent.mkdir(parents=True, exist_ok=True)
    start = time.time(); env = task_env(); env["TORCH_EXTENSIONS_DIR"] = str(ROOT / "torch_extensions_cuda118")
    env["CUDA_VISIBLE_DEVICES"] = "1"
    env["CUDA_HOME"] = "/usr/local/cuda-11.8"
    env["PATH"] = "/disk1/zlab/conda_envs/splatnav/bin:/usr/local/cuda-11.8/bin:" + env.get("PATH", "")
    try:
        with log.open("w", encoding="utf-8") as handle:
            result = subprocess.run([str(PYTHON), "-B", str(Path(__file__).resolve()), "--inner", "--stage", stage, "--attempt", str(attempt)], cwd=str(SPLATNAV_REPO), env=env, stdout=handle, stderr=subprocess.STDOUT, timeout=spec["wall_clock_cap_minutes"] * 60)
        timed_out = False; rc = result.returncode
    except subprocess.TimeoutExpired:
        timed_out = True; rc = None
    elapsed = time.time() - start
    text = log.read_text(encoding="utf-8", errors="replace") if log.is_file() else ""
    output_root = ROOT / stage / ("outputs" if attempt == 0 else "outputs_infrastructure_retry_" + str(attempt) + "_cuda118")
    checkpoints = sorted(output_root.rglob("*.ckpt"))
    if rc == 0 and checkpoints:
        status = success
    elif rc == 0:
        status = "SPLATFACTO_SMOKE_CHECKPOINT_FAILURE" if stage == "smoke" else "SPLATFACTO_PILOT_CHECKPOINT_FAILURE"
    elif timed_out:
        status = "SPLATFACTO_SMOKE_RESOURCE_LIMIT" if stage == "smoke" else "SPLATFACTO_PILOT_RESOURCE_LIMIT"
    elif "out of memory" in text.lower():
        status = "SPLATFACTO_SMOKE_OOM" if stage == "smoke" else "SPLATFACTO_PILOT_OOM"
    elif "nonfinite" in text.lower() or "nan" in text.lower():
        status = "SPLATFACTO_SMOKE_NONFINITE" if stage == "smoke" else "SPLATFACTO_PILOT_NONFINITE"
    else:
        status = "SPLATFACTO_SMOKE_TRAINING_FAILURE" if stage == "smoke" else "SPLATFACTO_PILOT_ALGORITHM_FAILURE"
    configs = sorted(output_root.rglob("config.yml"))
    summary = {"status": status, "stage": stage, "attempt": attempt, "seed": contract["seed"], "physical_gpu": 1, "adapter": spec["adapter"], "authority_config": str(AUTHORITY_CONFIG), "authority_config_sha256": sha256_path(AUTHORITY_CONFIG), "runtime_config": str(configs[-1]) if configs else None, "runtime_config_sha256": sha256_path(configs[-1]) if configs else None, "max_num_iterations": spec["max_num_iterations"], "wall_clock_cap_minutes": spec["wall_clock_cap_minutes"], "returncode": rc, "timed_out": timed_out, "wall_seconds": elapsed, "log": str(log), "log_sha256": sha256_path(log) if log.is_file() else None, "checkpoints": [{"path": str(item), "sha256": sha256_path(item), "size_bytes": item.stat().st_size} for item in checkpoints], "camera_optimization": "off", "pose_update": False, "depth_supervision": False, "official_eval_frames": 0}
    path = ROOT / stage / ("splatfacto_smoke_summary.json" if stage == "smoke" else "splatfacto_pilot_summary.json")
    if attempt and path.exists():
        atomic_json(path.with_name(path.stem + "_infrastructure_failure_attempt_1.json"), load_json(path))
    atomic_json(path, summary)
    update_stage("SMOKE" if stage == "smoke" else "QUALIFICATION_PILOT", "TERMINAL_SCIENTIFIC_RESULT" if status == success else "FAILED_INFRASTRUCTURE", result_status=status, summary=str(path))
    print(status)
    return 0 if status == success else 1


def main():
    parser = argparse.ArgumentParser(); parser.add_argument("--stage", choices=("smoke", "qualification_pilot"), default="smoke"); parser.add_argument("--inner", action="store_true"); parser.add_argument("--attempt", type=int, default=0); parser.add_argument("--infrastructure-retry", action="store_true"); parser.add_argument("--backend-repair-retry", action="store_true")
    args = parser.parse_args()
    if args.inner:
        _inner(args.stage, args.attempt); return
    if args.stage != "smoke":
        raise SystemExit("use run_splatfacto_qualification_pilot.py for the scientific pilot")
    attempt = 1 if (args.infrastructure_retry or args.backend_repair_retry) else 0
    if attempt > 1:
        raise SystemExit("only one infrastructure retry is authorized")
    raise SystemExit(_run("smoke", "SPLATFACTO_SMOKE_OPERATIONAL_PASS", "SPLATFACTO_SMOKE", attempt, args.backend_repair_retry))


if __name__ == "__main__":
    main()
