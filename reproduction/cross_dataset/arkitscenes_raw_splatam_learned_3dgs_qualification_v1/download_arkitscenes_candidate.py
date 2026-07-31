#!/usr/bin/env python3
"""Bounded transparent invocation of Apple's frozen ARKitScenes downloader."""
from __future__ import annotations

import argparse
import json
import os
import subprocess
from pathlib import Path

from arkitscenes_common import atomic_json, sha256_file, tree_sha256


ASSETS = ("mesh", "confidence", "lowres_depth", "lowres_wide.traj", "lowres_wide", "lowres_wide_intrinsics")
MAX_DOWNLOAD_BYTES = 80 * 1024 ** 3
MAX_OFFICIAL_ATTEMPTS_PER_FILE = 3  # initial request plus at most two official retries


def files(root: Path) -> list[dict[str, object]]:
    result: list[dict[str, object]] = []
    for item in sorted(path for path in root.rglob("*") if path.is_file()):
        result.append({
            "path": item.relative_to(root).as_posix(),
            "bytes": item.stat().st_size,
            "sha256": sha256_file(item),
        })
    return result


def asset_completeness(target: Path, video_id: str) -> dict[str, bool]:
    return {
        "mesh": (target / f"{video_id}_3dod_mesh.ply").is_file(),
        "confidence_archive": (target / "confidence.zip").is_file(),
        "confidence_tree": (target / "confidence").is_dir(),
        "depth_archive": (target / "lowres_depth.zip").is_file(),
        "depth_tree": (target / "lowres_depth").is_dir(),
        "trajectory": (target / "lowres_wide.traj").is_file(),
        "rgb_archive": (target / "lowres_wide.zip").is_file(),
        "rgb_tree": (target / "lowres_wide").is_dir(),
        "intrinsics_archive": (target / "lowres_wide_intrinsics.zip").is_file(),
        "intrinsics_tree": (target / "lowres_wide_intrinsics").is_dir(),
        "no_partial_files": not any(target.glob("*.tmp")),
    }


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--task-root", type=Path, required=True)
    parser.add_argument("--apple-source", type=Path, required=True)
    parser.add_argument("--python", required=True)
    parser.add_argument("--video-id", required=True)
    parser.add_argument("--visit-id", required=True)
    parser.add_argument("--split", choices=("Training",), required=True)
    args = parser.parse_args()
    task = args.task_root.resolve()
    source = args.apple_source.resolve()
    script = source / "download_data.py"
    if not script.is_file():
        raise RuntimeError("BLOCKED_BY_ARKITSCENES_OFFICIAL_DOWNLOAD_ACCESS: frozen download script absent")
    staging = task / "download" / "staging" / args.video_id / "payload"
    target = staging / "raw" / args.split / args.video_id
    manifest_path = task / "download" / f"arkitscenes_download_manifest_{args.video_id}.json"
    command = [args.python, "-B", str(script), "raw", "--split", args.split, "--video_id", args.video_id,
               "--download_dir", str(staging), "--keep_zip", "--raw_dataset_assets", *ASSETS]
    previous = json.loads(manifest_path.read_text(encoding="utf-8")) if manifest_path.is_file() else {}
    attempts: list[dict[str, object]] = list(previous.get("attempts", []))
    status = "BLOCKED_BY_ARKITSCENES_OFFICIAL_DOWNLOAD_ACCESS"
    completeness = asset_completeness(target, args.video_id) if target.is_dir() else {}
    if completeness and all(completeness.values()):
        status = "DOWNLOAD_PASS"
    for attempt in range(len(attempts) + 1, MAX_OFFICIAL_ATTEMPTS_PER_FILE + 1):
        if status == "DOWNLOAD_PASS":
            break
        log_path = task / "logs" / f"download_{args.video_id}_attempt_{attempt}.log"
        log_path.parent.mkdir(parents=True, exist_ok=True)
        completed = subprocess.run(command, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, check=False, env=os.environ.copy())
        log_path.write_bytes(completed.stdout)
        attempts.append({"attempt": attempt, "returncode": completed.returncode,
                         "log": str(log_path), "log_sha256": sha256_file(log_path)})
        completeness = asset_completeness(target, args.video_id) if target.is_dir() else {}
        if completed.returncode == 0 and completeness and all(completeness.values()):
            status = "DOWNLOAD_PASS"
            break
    tree_bytes = sum(path.stat().st_size for path in task.joinpath("download").rglob("*") if path.is_file())
    if tree_bytes > MAX_DOWNLOAD_BYTES:
        status = "BLOCKED_BY_ARKITSCENES_DOWNLOAD_CAP"
    identity = files(target) if target.is_dir() else []
    atomic_json(manifest_path, {
        "status": status,
        "video_id": args.video_id,
        "visit_id": args.visit_id,
        "split": args.split,
        "official_download_script": str(script),
        "official_download_script_sha256": sha256_file(script),
        "official_url_host": "docs-assets.developer.apple.com",
        "raw_asset_contract": list(ASSETS),
        "command": command,
        "retry_count": max(0, len(attempts) - 1),
        "attempts": attempts,
        "staging_target": str(target),
        "download_tree_bytes": tree_bytes,
        "download_cap_bytes": MAX_DOWNLOAD_BYTES,
        "candidate_tree_sha256": tree_sha256(target) if target.is_dir() else None,
        "asset_completeness": completeness,
        "files": identity,
    })
    print(status)
    return 0 if status == "DOWNLOAD_PASS" else 2


if __name__ == "__main__":
    raise SystemExit(main())
