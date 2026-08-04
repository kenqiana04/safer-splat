#!/usr/bin/env python3
"""Run the single authorized 500-iteration official 3DGS pipeline smoke."""

from __future__ import annotations

import argparse
import hashlib
import json
import os
import re
import subprocess
import sys
import time
from pathlib import Path

import torch


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for chunk in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def open_fd_paths(pid: int) -> list[str]:
    paths: list[str] = []
    fd_root = Path(f"/proc/{pid}/fd")
    if not fd_root.is_dir():
        return paths
    try:
        descriptors = list(fd_root.iterdir())
    except OSError:
        return paths
    for fd in descriptors:
        try:
            paths.append(os.readlink(fd))
        except OSError:
            continue
    return paths


def gpu_sample() -> dict[str, int] | None:
    process = subprocess.run(
        [
            "nvidia-smi",
            "-i",
            "1",
            "--query-gpu=memory.used,utilization.gpu",
            "--format=csv,noheader,nounits",
        ],
        stdout=subprocess.PIPE,
        stderr=subprocess.DEVNULL,
        text=True,
        check=False,
    )
    if process.returncode:
        return None
    used, utilization = [int(value.strip()) for value in process.stdout.split(",")]
    return {"memory_used_mib": used, "utilization_percent": utilization}


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--source", type=Path, required=True)
    parser.add_argument("--train-input", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--entrypoint", type=Path, required=True)
    parser.add_argument("--oracle-root", type=Path, required=True)
    parser.add_argument("--result", type=Path, required=True)
    parser.add_argument("--seed", type=int, required=True)
    args = parser.parse_args()

    source = args.source.resolve(strict=True)
    train_input = args.train_input.resolve(strict=True)
    oracle_root = str(args.oracle_root.resolve(strict=True))
    reuse_completed_smoke = args.output.exists()
    args.output.parent.mkdir(parents=True, exist_ok=True)
    log_path = args.output.parent / "official_500_iterations.log"
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
        str(args.output),
        "--iterations",
        "500",
        "--save_iterations",
        "500",
        "--test_iterations",
        "999999",
        "--data_device",
        "cpu",
        "--disable_viewer",
    ]
    forbidden_accesses: list[str] = []
    samples: list[dict[str, int]] = []
    if reuse_completed_smoke:
        runtime_seconds = None
    else:
        started = time.time()
        with log_path.open("w", encoding="utf-8", newline="\n") as log:
            process = subprocess.Popen(
                command,
                cwd=source,
                stdout=log,
                stderr=subprocess.STDOUT,
                text=True,
                env=os.environ.copy(),
            )
            while process.poll() is None:
                for path in open_fd_paths(process.pid):
                    if path.startswith(oracle_root):
                        forbidden_accesses.append(path)
                sample = gpu_sample()
                if sample:
                    sample["elapsed_seconds"] = int(time.time() - started)
                    samples.append(sample)
                time.sleep(1.0)
        runtime_seconds = time.time() - started
        if process.returncode:
            raise RuntimeError(f"500-iteration smoke failed with {process.returncode}; see {log_path}")
    if forbidden_accesses:
        raise RuntimeError(f"smoke accessed forbidden oracle paths: {forbidden_accesses[:3]}")

    ply = args.output / "point_cloud" / "iteration_500" / "point_cloud.ply"
    if not ply.is_file():
        raise RuntimeError(f"smoke output PLY missing: {ply}")
    sys.path.insert(0, str(source))
    from scene.gaussian_model import GaussianModel  # pylint: disable=import-outside-toplevel

    model = GaussianModel(3, "default")
    model.load_ply(str(ply))
    gaussian_count = int(model.get_xyz.shape[0])
    finite = bool(torch.isfinite(model.get_xyz).all().item())
    del model
    torch.cuda.empty_cache()
    if gaussian_count <= 0 or not finite:
        raise RuntimeError("500-iteration smoke PLY failed finite/count gate")

    log_text = log_path.read_text(encoding="utf-8", errors="replace")
    if oracle_root in log_text:
        raise RuntimeError("oracle root appeared in completed smoke log")
    adapter_targets = []
    for path in train_input.rglob("*"):
        if path.is_symlink():
            target = str(path.resolve(strict=True))
            adapter_targets.append(target)
            if target.startswith(oracle_root):
                forbidden_accesses.append(target)
    if forbidden_accesses:
        raise RuntimeError(f"smoke adapter closure reached oracle: {forbidden_accesses[:3]}")
    losses = [
        float(value)
        for value in re.findall(r"(?<!Depth )Loss=([0-9.eE+-]+)", log_text)
    ]
    record = {
        "schema_version": 1,
        "status": "PASS_OFFICIAL_3DGS_500_ITERATION_SMOKE",
        "seed": args.seed,
        "iterations": 500,
        "command": command,
        "command_token_count": len(command),
        "source_commit": subprocess.check_output(
            ["git", "-C", str(source), "rev-parse", "HEAD"], text=True
        ).strip(),
        "train_input": str(train_input),
        "output": str(args.output),
        "runtime_seconds": runtime_seconds,
        "completed_smoke_reused_after_fd_monitor_exit_race": reuse_completed_smoke,
        "gaussian_count": gaussian_count,
        "finite_map": finite,
        "loss_sample_count": len(losses),
        "final_logged_ema_loss": losses[-1] if losses else None,
        "max_gpu_memory_used_mib": max((s["memory_used_mib"] for s in samples), default=None),
        "max_gpu_utilization_percent": max((s["utilization_percent"] for s in samples), default=None),
        "gpu_sample_count": len(samples),
        "reference_access_count": len(forbidden_accesses),
        "heldout_access_count": len(forbidden_accesses),
        "adapter_symlink_target_count": len(adapter_targets),
        "reference_audit_mode": "runtime_fd_plus_adapter_closure" if not reuse_completed_smoke else "completed_run_log_plus_adapter_closure_postcheck",
        "ply_path": str(ply),
        "ply_sha256": sha256(ply),
        "log_path": str(log_path),
        "log_sha256": sha256(log_path),
        "formal_attempt_count": 0,
    }
    args.result.parent.mkdir(parents=True, exist_ok=True)
    args.result.write_text(
        json.dumps(record, indent=2, sort_keys=True) + "\n", encoding="utf-8"
    )
    print("OFFICIAL_3DGS_SMOKE_PASS")
    print(json.dumps(record, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
