#!/usr/bin/env python3
"""Copy frozen PR #54 inputs byte-for-byte and construct the serial location schedule."""
from __future__ import annotations

import shutil
from pathlib import Path

from _common import ROOT, atomic_json, ensure_root, load_json, sha256_path


FROZEN = ("REPLICA_RENDER_PROTOCOL_V3_CONTRACT.json", "formal_camera_manifest_v3.csv", "formal_camera_manifest_v3.json", "transforms_v3.json", "selected_v3_location_registry.json", "replica_v3_location_split.json", "replica_protocol_v3_identity.json")


def main() -> None:
    ensure_root()
    source = ROOT / "input_identity" / "frozen_inputs"
    staging = ROOT / "formal_staging"
    if any(staging.iterdir()):
        raise SystemExit("formal_staging_not_empty_refuse_mutation")
    for name in FROZEN:
        shutil.copyfile(source / name, staging / name)
        if sha256_path(source / name) != sha256_path(staging / name):
            raise RuntimeError("frozen_input_copy_mismatch:" + name)
    (staging / "images").mkdir(); (staging / "depth").mkdir()
    frames = load_json(source / "formal_camera_manifest_v3.json")["frames"]
    locations = {}
    for frame in frames:
        locations.setdefault(frame["location_id"], []).append(frame)
    ordered = []
    for location_id in sorted(locations):
        group = sorted(locations[location_id], key=lambda item: item["yaw_slot"])
        if len(group) != 3 or [item["yaw_offset_deg"] for item in group] != [0, -60, 60]:
            raise RuntimeError("frozen_location_yaw_contract_failure:" + location_id)
        ordered.append({"location_id": location_id, "status": "NOT_STARTED", "attempts": 0, "frames": [{"frame_id": item["frame_id"], "status": "NOT_STARTED", "split": item["split"], "yaw_slot": item["yaw_slot"], "yaw_offset_deg": item["yaw_offset_deg"]} for item in group]})
    if len(frames) != 300 or len(ordered) != 100:
        raise RuntimeError("frozen_formal_render_schedule_count_failure")
    payload = {"status": "FROZEN_FORMAL_RENDER_SCHEDULE", "fresh_subprocess_and_simulator_per_location": True, "location_count": 100, "frame_count": 300, "locations": ordered, "frozen_input_sha256": {name: sha256_path(source / name) for name in FROZEN}}
    atomic_json(ROOT / "render_manifests" / "formal_render_manifest_v3.json", payload)
    atomic_json(ROOT / "render_manifests" / "formal_render_manifest_summary.json", {key: payload[key] for key in ("status", "fresh_subprocess_and_simulator_per_location", "location_count", "frame_count", "frozen_input_sha256")})


if __name__ == "__main__":
    main()
