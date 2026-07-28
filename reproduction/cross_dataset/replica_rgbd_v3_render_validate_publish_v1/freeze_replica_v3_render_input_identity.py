#!/usr/bin/env python3
"""Verify exact PR #54 render inputs before any formal frame generation."""
from __future__ import annotations

import argparse
import importlib.metadata
import json
from pathlib import Path

from _common import EXPECTED, MESH, NAVMESH, PUBLISHED, PUBLISH_TMP, ROOT, atomic_json, ensure_root, sha256_path


INPUTS = {
    "REPLICA_RENDER_PROTOCOL_V3_CONTRACT.json": "contract_sha256",
    "formal_camera_manifest_v3.csv": "manifest_csv_sha256",
    "formal_camera_manifest_v3.json": "manifest_json_sha256",
    "transforms_v3.json": "transforms_sha256",
    "selected_v3_location_registry.json": "registry_sha256",
}


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--frozen-inputs", type=Path, required=True)
    parser.add_argument("--pr54-head", required=True)
    parser.add_argument("--task-renderer", type=Path, required=True)
    args = parser.parse_args()
    ensure_root()
    observed = {name: sha256_path(args.frozen_inputs / name) for name in INPUTS}
    checks = {name: observed[name] == EXPECTED[key] for name, key in INPUTS.items()}
    identity = json.loads((args.frozen_inputs / "replica_protocol_v3_identity.json").read_text(encoding="utf-8"))
    pose_ok = identity.get("pose_array_sha256") == EXPECTED["pose_array_sha256"]
    scene = {"mesh_sha256": sha256_path(MESH), "navmesh_sha256": sha256_path(NAVMESH)}
    scene_ok = scene["mesh_sha256"] == EXPECTED["mesh_sha256"] and scene["navmesh_sha256"] == EXPECTED["navmesh_sha256"]
    try:
        habitat_version = importlib.metadata.version("habitat-sim")
    except importlib.metadata.PackageNotFoundError:
        habitat_version = "unavailable"
    environment = {"python_version": __import__("sys").version.split()[0], "habitat_sim_version": habitat_version, "cuda_visible_devices": __import__("os").environ.get("CUDA_VISIBLE_DEVICES"), "physical_gpu": 1, "inprocess_gpu": 0}
    status = "PASS_REPLICA_RGBD_V3_RENDER_INPUT_IDENTITY" if all(checks.values()) and pose_ok and scene_ok and args.pr54_head == EXPECTED["pr54_head"] else "BLOCKED_BY_REPLICA_RGBD_V3_PROTOCOL_IDENTITY_MISMATCH"
    payload = {"status": status, "pr54_head": args.pr54_head, "expected": EXPECTED, "input_sha256": observed, "input_checks": checks, "pose_array_check": pose_ok, "scene": scene, "scene_check": scene_ok, "environment": environment, "published_target_exists": PUBLISHED.exists(), "publish_tmp_exists": PUBLISH_TMP.exists(), "task_owned_renderer_sha256": sha256_path(args.task_renderer), "formal_render_count": 0, "publication_count": 0, "gaussian_training_count": 0, "safer_cbf_count": 0, "tum_rollout_count": 0}
    atomic_json(ROOT / "input_identity" / "input_identity_summary.json", payload)
    if status != "PASS_REPLICA_RGBD_V3_RENDER_INPUT_IDENTITY":
        raise SystemExit(status)
    if PUBLISHED.exists():
        raise SystemExit("BLOCKED_BY_REPLICA_RGBD_V3_PUBLISH_TARGET_ALREADY_EXISTS")


if __name__ == "__main__":
    main()
