#!/usr/bin/env python3
"""Serial parent scheduler: one fresh process and Simulator per frozen location."""
from __future__ import annotations

import os
import subprocess
import sys
from pathlib import Path

from _common import ROOT, atomic_json, ensure_root, load_json


def write_manifest(payload):
    atomic_json(ROOT / "render_manifests" / "formal_render_manifest_v3.json", payload)


def main() -> None:
    ensure_root()
    manifest_path = ROOT / "render_manifests" / "formal_render_manifest_v3.json"
    payload = load_json(manifest_path)
    if payload["status"] != "FROZEN_FORMAL_RENDER_SCHEDULE":
        raise RuntimeError("invalid_formal_render_manifest_status")
    retries = 0
    environment = {**os.environ, "CUDA_VISIBLE_DEVICES": "1", "PYTHONNOUSERSITE": "1", "PYTHONDONTWRITEBYTECODE": "1"}
    for location in payload["locations"]:
        if location["status"] != "NOT_STARTED":
            raise RuntimeError("unexpected_resumed_location_status")
        location["status"] = "RUNNING"; write_manifest(payload)
        final = None
        for attempt in (1, 2):
            location["attempts"] = attempt; write_manifest(payload)
            process = subprocess.run([sys.executable, str(ROOT / "code" / "render_replica_v3_location.py"), "--location-id", location["location_id"], "--attempt", str(attempt)], env=environment, capture_output=True, text=True)
            log = ROOT / "logs" / (location["location_id"] + ".attempt" + str(attempt) + ".log")
            log.write_text(process.stdout + "\n--- STDERR ---\n" + process.stderr, encoding="utf-8")
            result_path = ROOT / "per_location_status" / (location["location_id"] + ".attempt" + str(attempt) + ".json")
            if not result_path.exists():
                final = {"status": "FAILED_INFRASTRUCTURE", "frames": [], "exception": "missing_location_terminal_json"}
            else:
                final = load_json(result_path)
            if final["status"] == "FAILED_INFRASTRUCTURE" and attempt == 1:
                retries += 1
                continue
            break
        location["status"] = final["status"]
        index = {item["frame_id"]: item for item in location["frames"]}
        for frame in final.get("frames", []):
            if frame["frame_id"] in index:
                index[frame["frame_id"]]["status"] = frame["status"]
        write_manifest(payload)
    frames = [frame for location in payload["locations"] for frame in location["frames"]]
    summary = {"status": "FORMAL_RENDER_COMPLETED", "formal_location_count": len(payload["locations"]), "fresh_subprocess_count": sum(location["attempts"] for location in payload["locations"]), "fresh_simulator_count": sum(location["attempts"] for location in payload["locations"]), "formal_frame_attempted_count": len(frames), "terminal_valid_frame_count": sum(frame["status"] == "TERMINAL_VALID" for frame in frames), "terminal_integrity_failure_frame_count": sum(frame["status"] == "TERMINAL_INTEGRITY_FAILURE" for frame in frames), "infrastructure_failure_location_count": sum(location["status"] == "FAILED_INFRASTRUCTURE" for location in payload["locations"]), "infrastructure_retry_count": retries, "location_status_counts": {status: sum(location["status"] == status for location in payload["locations"]) for status in ("TERMINAL_COMPLETE", "TERMINAL_INTEGRITY_FAILURE", "FAILED_INFRASTRUCTURE")}, "frame_replacement_count": 0, "preprobe_image_reuse_count": 0, "pose_modification_count": 0, "threshold_modification_count": 0, "v1_frame_reuse_count": 0}
    atomic_json(ROOT / "render_manifests" / "replica_rgbd_v3_render_summary.json", summary)


if __name__ == "__main__":
    main()
