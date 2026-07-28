#!/usr/bin/env python3
"""Verify staging pose/split bytes and coordinate contracts against PR #54 inputs."""
from __future__ import annotations

import numpy as np

from _common import EXPECTED, ROOT, atomic_json, load_json, sha256_path


def main() -> None:
    source, staging = ROOT / "input_identity" / "frozen_inputs", ROOT / "formal_staging"
    names = ("formal_camera_manifest_v3.csv", "formal_camera_manifest_v3.json", "transforms_v3.json", "selected_v3_location_registry.json", "replica_v3_location_split.json", "REPLICA_RENDER_PROTOCOL_V3_CONTRACT.json", "replica_protocol_v3_identity.json")
    byte_checks = {name: sha256_path(source / name) == sha256_path(staging / name) for name in names}
    manifest = load_json(staging / "formal_camera_manifest_v3.json")["frames"]
    transforms = load_json(staging / "transforms_v3.json")
    identity = load_json(staging / "replica_protocol_v3_identity.json")
    matrices = [np.asarray(row["camera_to_world"], dtype=np.float64) for row in manifest]
    rotations_ok = all(np.isfinite(matrix).all() and abs(float(np.linalg.det(matrix[:3,:3])) - 1.0) < 1e-9 and float(np.max(np.abs(matrix[:3,:3].T @ matrix[:3,:3] - np.eye(3)))) < 1e-9 for matrix in matrices)
    payload = {"status": "PASS" if all(byte_checks.values()) and len(manifest) == 300 and len(transforms["frames"]) == 300 and rotations_ok and identity["pose_array_sha256"] == EXPECTED["pose_array_sha256"] else "FAIL", "byte_checks": byte_checks, "manifest_csv_sha256": sha256_path(staging / "formal_camera_manifest_v3.csv"), "manifest_json_sha256": sha256_path(staging / "formal_camera_manifest_v3.json"), "transforms_sha256": sha256_path(staging / "transforms_v3.json"), "selected_registry_sha256": sha256_path(staging / "selected_v3_location_registry.json"), "split_sha256": sha256_path(staging / "replica_v3_location_split.json"), "pose_array_sha256": identity["pose_array_sha256"], "frame_count": len(manifest), "rotation_identity_pass": rotations_ok, "auto_scale": False, "normalization": False, "colmap": False, "pose_estimation": False, "coordinate_refit": False, "camera_replacement": False}
    atomic_json(ROOT / "full_integrity" / "replica_rgbd_v3_pose_identity_validation.json", payload)
    if payload["status"] != "PASS": raise SystemExit("REPLICA_RGBD_V3_FORMAL_RENDER_INTEGRITY_GATE_FAILED")


if __name__ == "__main__": main()
