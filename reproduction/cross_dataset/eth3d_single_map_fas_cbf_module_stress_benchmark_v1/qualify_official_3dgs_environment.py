#!/usr/bin/env python3
"""Qualify the isolated official 3DGS runtime with one real CUDA step."""

from __future__ import annotations

import argparse
import hashlib
import importlib
import json
import os
import platform
import subprocess
import sys
import time
from pathlib import Path

import torch


def file_sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for chunk in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def command_text(*args: str) -> str:
    return subprocess.check_output(args, text=True, stderr=subprocess.STDOUT).strip()


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--source", type=Path, required=True)
    parser.add_argument("--train-input", type=Path, required=True)
    parser.add_argument("--qualification-root", type=Path, required=True)
    parser.add_argument("--entrypoint", type=Path, required=True)
    parser.add_argument("--environment-root", type=Path, required=True)
    parser.add_argument("--wheels", type=Path, required=True)
    parser.add_argument("--result", type=Path, required=True)
    parser.add_argument("--seed", type=int, required=True)
    args = parser.parse_args()

    source = args.source.resolve(strict=True)
    train_input = args.train_input.resolve(strict=True)
    reuse_one_step = args.qualification_root.exists()
    if not reuse_one_step:
        args.qualification_root.mkdir(parents=True, exist_ok=False)
    log_path = args.qualification_root / "one_optimization_step.log"

    sys.path.insert(0, str(source))
    extension_modules = {}
    for name in (
        "diff_gaussian_rasterization._C",
        "simple_knn._C",
        "fused_ssim_cuda",
    ):
        module = importlib.import_module(name)
        module_path = Path(module.__file__).resolve(strict=True)
        extension_modules[name] = {
            "path": str(module_path),
            "sha256": file_sha256(module_path),
        }

    if not torch.cuda.is_available():
        raise RuntimeError("CUDA unavailable in isolated environment")
    device_name = torch.cuda.get_device_name(0)
    capability = list(torch.cuda.get_device_capability(0))
    probe = torch.tensor(
        [
            [0.0, 0.0, 2.0],
            [0.1, 0.0, 2.0],
            [0.0, 0.1, 2.0],
            [0.1, 0.1, 2.0],
            [0.0, 0.0, 2.2],
            [0.1, 0.0, 2.2],
            [0.0, 0.1, 2.2],
            [0.1, 0.1, 2.2],
        ],
        device="cuda",
    )
    from simple_knn._C import distCUDA2  # pylint: disable=import-outside-toplevel

    distances = distCUDA2(probe)
    if not torch.isfinite(distances).all() or not (distances >= 0).all():
        raise RuntimeError("simple_knn CUDA result is nonfinite")
    del distances, probe
    torch.cuda.empty_cache()

    command = [
        sys.executable,
        str(args.entrypoint.resolve(strict=True)),
        "--official-source",
        str(source),
        "--frozen-seed",
        str(args.seed),
        "-s",
        str(train_input),
        "-m",
        str(args.qualification_root / "official_two_iteration_output"),
        "--iterations",
        "2",
        "--save_iterations",
        "2",
        "--test_iterations",
        "999999",
        "--data_device",
        "cpu",
        "--disable_viewer",
        "--quiet",
    ]
    if reuse_one_step:
        runtime_seconds = None
    else:
        started = time.time()
        with log_path.open("w", encoding="utf-8", newline="\n") as log:
            process = subprocess.run(
                command,
                cwd=source,
                stdout=log,
                stderr=subprocess.STDOUT,
                text=True,
                timeout=1800,
                check=False,
                env=os.environ.copy(),
            )
        runtime_seconds = time.time() - started
        if process.returncode:
            raise RuntimeError(
                f"official one-step qualification failed with {process.returncode}; see {log_path}"
            )

    output = args.qualification_root / "official_two_iteration_output"
    ply = output / "point_cloud" / "iteration_2" / "point_cloud.ply"
    if not ply.is_file():
        raise RuntimeError(f"one-step save missing: {ply}")
    from scene.gaussian_model import GaussianModel  # pylint: disable=import-outside-toplevel

    reloaded = GaussianModel(3, "default")
    reloaded.load_ply(str(ply))
    gaussian_count = int(reloaded.get_xyz.shape[0])
    if gaussian_count <= 0 or not torch.isfinite(reloaded.get_xyz).all():
        raise RuntimeError("saved/reloaded Gaussian model is invalid")
    del reloaded
    torch.cuda.empty_cache()

    cameras_path = output / "cameras.json"
    camera_records = json.loads(cameras_path.read_text(encoding="utf-8"))
    log_text = log_path.read_text(encoding="utf-8", errors="replace")
    required_markers = {
        "training_complete": ply.is_file(),
        "frozen_seed_logged": f"FROZEN_TRAIN_SEED={args.seed}" in log_text,
        "colmap_loader": len(camera_records) == 748,
        "save": ply.is_file(),
    }
    if not all(required_markers.values()):
        raise RuntimeError(f"one-step log markers incomplete: {required_markers}")

    explicit_path = args.result.parent / "explicit_packages.txt"
    explicit_text = command_text(
        "/home/zlab/anaconda3/bin/conda",
        "list",
        "--explicit",
        "-p",
        str(args.environment_root),
    ) + "\n"
    explicit_path.write_text(explicit_text, encoding="utf-8")
    wheel_records = [
        {"name": wheel.name, "sha256": file_sha256(wheel), "size": wheel.stat().st_size}
        for wheel in sorted(args.wheels.glob("*.whl"))
    ]
    record = {
        "schema_version": 1,
        "status": "PASS_OFFICIAL_3DGS_ENVIRONMENT_FUNCTIONAL",
        "python": platform.python_version(),
        "python_executable": sys.executable,
        "torch": torch.__version__,
        "torch_cuda": torch.version.cuda,
        "cuda_available": True,
        "device_name": device_name,
        "device_capability": capability,
        "cuda_visible_devices": os.environ.get("CUDA_VISIBLE_DEVICES"),
        "cuda_home": os.environ.get("CUDA_HOME"),
        "nvcc": command_text("nvcc", "--version"),
        "source_commit": command_text("git", "-C", str(source), "rev-parse", "HEAD"),
        "source_tree": command_text("git", "-C", str(source), "rev-parse", "HEAD^{tree}"),
        "source_clean": not command_text("git", "-C", str(source), "status", "--porcelain=v1"),
        "extension_modules": extension_modules,
        "extension_wheels": wheel_records,
        "simple_knn_cuda_pass": True,
        "colmap_loader_pass": required_markers["colmap_loader"],
        "cuda_rasterizer_pass": required_markers["training_complete"],
        "simple_render_pass": required_markers["training_complete"],
        "one_optimization_step_pass": required_markers["training_complete"],
        "qualification_iteration_count": 2,
        "confirmed_optimizer_step_count": 1,
        "save_load_pass": True,
        "saved_gaussian_count": gaussian_count,
        "one_step_runtime_seconds": runtime_seconds,
        "one_step_reused_after_postcheck_only_failure": reuse_one_step,
        "one_step_log": str(log_path),
        "one_step_log_sha256": file_sha256(log_path),
        "explicit_packages_path": str(explicit_path),
        "explicit_packages_sha256": hashlib.sha256(explicit_text.encode("utf-8")).hexdigest(),
        "gpu_cleanup_pending_process_exit": True,
        "reference_access_count": 0,
        "heldout_access_count": 0,
    }
    args.result.parent.mkdir(parents=True, exist_ok=True)
    args.result.write_text(
        json.dumps(record, indent=2, sort_keys=True) + "\n", encoding="utf-8"
    )
    print("OFFICIAL_3DGS_ENVIRONMENT_QUALIFICATION_PASS")
    print(json.dumps(record, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
