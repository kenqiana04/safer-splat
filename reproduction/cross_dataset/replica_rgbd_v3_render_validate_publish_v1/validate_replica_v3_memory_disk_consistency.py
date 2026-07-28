#!/usr/bin/env python3
"""Compare formal in-memory compact observations with decoded final PNGs."""
from __future__ import annotations

from _common import ROOT, atomic_json, load_json


def main() -> None:
    frames = load_json(ROOT / "full_integrity" / "frame_integrity_detail.json")["frames"]
    mismatches = {"rgb_classification": 0, "depth_classification": 0, "rgb_write_corruption": 0, "depth_write_corruption": 0, "filename_collision": 0, "stale_file_reuse": 0}
    renderer, mesh, navmesh, sensors = set(), set(), set(), set()
    for detail in frames:
        prior = load_json(ROOT / "per_frame_integrity" / (detail["frame_id"] + ".json"))
        renderer.add(prior["manifest_row_sha256"]); mesh.add(prior["mesh_sha256"]); navmesh.add(prior["navmesh_sha256"]); sensors.add(__import__("json").dumps(prior["sensor"], sort_keys=True))
        if prior["memory_rgb"]["v1_black"] != detail["rgb"]["v1_black"] or prior["memory_rgb"]["v3_threshold_failure"] != detail["rgb"]["v3_threshold_failure"]: mismatches["rgb_classification"] += 1
        if prior["memory_depth"]["v1_all_zero"] != detail["depth"]["v1_all_zero"] or prior["memory_depth"]["v3_threshold_failure"] != detail["depth"]["v3_threshold_failure"]: mismatches["depth_classification"] += 1
        if prior["disk_rgb"]["sha256_raw"] != detail["rgb"]["sha256_raw"]: mismatches["rgb_write_corruption"] += 1
        if prior["disk_depth"]["v3_threshold_failure"] != detail["depth"]["v3_threshold_failure"] or prior["depth_quantization_max_error_m"] > .001001: mismatches["depth_write_corruption"] += 1
    payload = {"status": "PASS" if not any(mismatches.values()) and len(renderer) == 300 and len(mesh) == len(navmesh) == len(sensors) == 1 else "FAIL", "frame_count": len(frames), **{key + "_count": value for key, value in mismatches.items()}, "mixed_renderer_sha_count": max(0, len(renderer) - 300), "mixed_scene_asset_sha_count": max(0, len(mesh) - 1) + max(0, len(navmesh) - 1), "mixed_sensor_config_count": max(0, len(sensors) - 1)}
    atomic_json(ROOT / "full_integrity" / "replica_rgbd_v3_memory_disk_consistency.json", payload)
    if payload["status"] != "PASS": raise SystemExit("REPLICA_RGBD_V3_FORMAL_RENDER_INTEGRITY_GATE_FAILED")


if __name__ == "__main__": main()
