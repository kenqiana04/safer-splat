#!/usr/bin/env python3
"""Launch exactly one frozen official 30K ETH3D 3DGS formal attempt."""

from __future__ import annotations

import argparse
import hashlib
import json
import os
import re
import subprocess
import sys
import time
from datetime import datetime, timezone
from pathlib import Path


def utc_now() -> str:
    return datetime.now(timezone.utc).isoformat()


def atomic_json(path: Path, value: dict) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary = path.with_suffix(path.suffix + ".tmp")
    temporary.write_text(
        json.dumps(value, indent=2, sort_keys=True) + "\n", encoding="utf-8"
    )
    os.replace(temporary, path)


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for chunk in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def open_fd_paths(pid: int) -> list[str]:
    fd_root = Path(f"/proc/{pid}/fd")
    try:
        descriptors = list(fd_root.iterdir())
    except OSError:
        return []
    result = []
    for descriptor in descriptors:
        try:
            result.append(os.readlink(descriptor))
        except OSError:
            continue
    return result


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
    memory, utilization = [int(value.strip()) for value in process.stdout.split(",")]
    return {"memory_used_mib": memory, "utilization_percent": utilization}


def ply_vertex_count(path: Path) -> int:
    with path.open("rb") as stream:
        for raw_line in stream:
            line = raw_line.decode("ascii", "strict").strip()
            if line.startswith("element vertex "):
                return int(line.split()[-1])
            if line == "end_header":
                break
    raise RuntimeError(f"PLY vertex element unavailable: {path}")


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--source", type=Path, required=True)
    parser.add_argument("--train-input", type=Path, required=True)
    parser.add_argument("--map-root", type=Path, required=True)
    parser.add_argument("--entrypoint", type=Path, required=True)
    parser.add_argument("--oracle-root", type=Path, required=True)
    parser.add_argument("--attempt-record", type=Path, required=True)
    parser.add_argument("--result", type=Path, required=True)
    parser.add_argument("--progress", type=Path, required=True)
    parser.add_argument("--log", type=Path, required=True)
    parser.add_argument("--seed", type=int, required=True)
    args = parser.parse_args()

    source = args.source.resolve(strict=True)
    train_input = args.train_input.resolve(strict=True)
    oracle_root = str(args.oracle_root.resolve(strict=True))
    if args.attempt_record.exists():
        raise RuntimeError(
            f"formal attempt record already exists; refusing a second attempt: {args.attempt_record}"
        )
    args.map_root.mkdir(parents=True, exist_ok=True)
    if any(args.map_root.iterdir()):
        raise RuntimeError(f"formal map root is not empty: {args.map_root}")

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
        str(args.map_root),
        "--iterations",
        "30000",
        "--save_iterations",
        "7000",
        "15000",
        "30000",
        "--checkpoint_iterations",
        "7000",
        "15000",
        "30000",
        "--test_iterations",
        "999999",
        "--data_device",
        "cpu",
        "--disable_viewer",
    ]
    source_commit = subprocess.check_output(
        ["git", "-C", str(source), "rev-parse", "HEAD"], text=True
    ).strip()
    source_tree = subprocess.check_output(
        ["git", "-C", str(source), "rev-parse", "HEAD^{tree}"], text=True
    ).strip()
    attempt = {
        "schema_version": 1,
        "state": "RUNNING",
        "formal_attempt_count": 1,
        "formal_seed_count": 1,
        "formal_map_count": 1,
        "seed": args.seed,
        "iterations": 30000,
        "command": command,
        "command_token_count": len(command),
        "source_commit": source_commit,
        "source_tree": source_tree,
        "train_input": str(train_input),
        "map_root": str(args.map_root),
        "started_utc": utc_now(),
        "checkpoint_resume_count": 0,
        "reference_access_count": 0,
        "heldout_access_count": 0,
    }
    atomic_json(args.attempt_record, attempt)

    forbidden_accesses: list[str] = []
    samples: list[dict[str, int]] = []
    started = time.time()
    args.log.parent.mkdir(parents=True, exist_ok=True)
    with args.log.open("w", encoding="utf-8", newline="\n") as log:
        process = subprocess.Popen(
            command,
            cwd=source,
            stdout=log,
            stderr=subprocess.STDOUT,
            text=True,
            env=os.environ.copy(),
        )
        attempt["pid"] = process.pid
        atomic_json(args.attempt_record, attempt)
        while process.poll() is None:
            for path in open_fd_paths(process.pid):
                if path.startswith(oracle_root):
                    forbidden_accesses.append(path)
            sample = gpu_sample()
            if sample:
                sample["elapsed_seconds"] = int(time.time() - started)
                samples.append(sample)
            atomic_json(
                args.progress,
                {
                    "pid": process.pid,
                    "state": "RUNNING",
                    "elapsed_seconds": int(time.time() - started),
                    "sample_count": len(samples),
                    "last_gpu_sample": samples[-1] if samples else None,
                    "reference_access_count": len(forbidden_accesses),
                    "updated_utc": utc_now(),
                },
            )
            time.sleep(2.0)
    runtime_seconds = time.time() - started
    attempt["returncode"] = process.returncode
    attempt["ended_utc"] = utc_now()
    attempt["runtime_seconds"] = runtime_seconds
    attempt["reference_access_count"] = len(forbidden_accesses)
    attempt["heldout_access_count"] = len(forbidden_accesses)
    if process.returncode:
        attempt["state"] = "FAILED"
        atomic_json(args.attempt_record, attempt)
        raise RuntimeError(f"formal 30K attempt failed with {process.returncode}; see {args.log}")
    if forbidden_accesses:
        attempt["state"] = "FAILED_REFERENCE_BOUNDARY"
        atomic_json(args.attempt_record, attempt)
        raise RuntimeError(f"formal training accessed oracle: {forbidden_accesses[:3]}")

    log_text = args.log.read_text(encoding="utf-8", errors="replace")
    if oracle_root in log_text:
        raise RuntimeError("oracle root appeared in formal training log")
    losses = [
        float(value)
        for value in re.findall(r"(?<!Depth )Loss=([0-9.eE+-]+)", log_text)
    ]
    checkpoints = {}
    point_clouds = {}
    gaussian_counts = {}
    for iteration in (7000, 15000, 30000):
        checkpoint = args.map_root / f"chkpnt{iteration}.pth"
        ply = args.map_root / "point_cloud" / f"iteration_{iteration}" / "point_cloud.ply"
        if not checkpoint.is_file() or not ply.is_file():
            raise RuntimeError(f"formal artifact missing at iteration {iteration}")
        checkpoints[str(iteration)] = {
            "path": str(checkpoint),
            "size": checkpoint.stat().st_size,
            "sha256": sha256(checkpoint),
        }
        point_clouds[str(iteration)] = {
            "path": str(ply),
            "size": ply.stat().st_size,
            "sha256": sha256(ply),
        }
        gaussian_counts[str(iteration)] = ply_vertex_count(ply)

    attempt["state"] = "COMPLETED"
    attempt["final_iteration"] = 30000
    atomic_json(args.attempt_record, attempt)
    atomic_json(
        args.progress,
        {
            "pid": process.pid,
            "state": "COMPLETED",
            "elapsed_seconds": int(runtime_seconds),
            "sample_count": len(samples),
            "last_gpu_sample": samples[-1] if samples else None,
            "reference_access_count": 0,
            "updated_utc": utc_now(),
        },
    )
    result = {
        "schema_version": 1,
        "status": "PASS_OFFICIAL_3DGS_FORMAL_30K_SINGLE_ATTEMPT",
        "formal_attempt_count": 1,
        "formal_seed_count": 1,
        "formal_map_count": 1,
        "checkpoint_resume_count": 0,
        "seed": args.seed,
        "iterations": 30000,
        "source_commit": source_commit,
        "source_tree": source_tree,
        "command": command,
        "command_token_count": len(command),
        "runtime_seconds": runtime_seconds,
        "loss_sample_count": len(losses),
        "final_logged_ema_loss": losses[-1] if losses else None,
        "gaussian_counts": gaussian_counts,
        "checkpoints": checkpoints,
        "point_clouds": point_clouds,
        "max_gpu_memory_used_mib": max((s["memory_used_mib"] for s in samples), default=None),
        "max_gpu_utilization_percent": max((s["utilization_percent"] for s in samples), default=None),
        "gpu_sample_count": len(samples),
        "reference_access_count": 0,
        "heldout_access_count": 0,
        "mapper_sweep_count": 0,
        "mapping_baseline_count": 0,
        "map_filtering_count": 0,
        "icp_sim3_count": 0,
        "scale_repair_count": 0,
        "frame_deletion_count": 0,
        "log_path": str(args.log),
        "log_sha256": sha256(args.log),
        "attempt_record": str(args.attempt_record),
    }
    atomic_json(args.result, result)
    print("OFFICIAL_3DGS_FORMAL_30K_PASS")
    print(json.dumps(result, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
