#!/usr/bin/env python3
"""Freeze the immutable V1 evidence that V2 is permitted to consume."""
from __future__ import annotations

import argparse
import json
import subprocess
from pathlib import Path

from arkitscenes_split_v2_common import atomic_json, sha256_file, v1_path

EXPECTED = {
    "42899163": {"visit_id": "434897", "joined_frames": 544, "keyframes": 173, "joined_sha256": "61ba0f5d18475f546e5e1a9220fe485453b19d3250fb81586734ccf13997344d"},
    "48018874": {"visit_id": "483945", "joined_frames": 571, "keyframes": 267, "joined_sha256": "d758fe69d01cfc3e9e2f75dcda5a2a3e81eae700602093b3cb785455900fc6f3"},
}
FILES = [
    "frame_join/{video}/arkitscenes_joined_frame_manifest.csv",
    "frame_split/{video}/arkitscenes_frame_split_contract.json",
    "coordinate_audit/{video}/arkitscenes_coordinate_contract.json",
    "coordinate_audit/{video}/arkit_mesh_coordinate_validation.json",
    "candidate_precheck/{video}/future_hard_benchmark_precheck.json",
    "arkitscenes_download_manifest_{video}.json",
]
GLOBAL_FILES = ["metadata/arkitscenes_candidate_registry.json", "selection/arkitscenes_primary_backup_selection.json", "data_identity/arkitscenes_scene_asset_identity.json", "authority/arkitscenes_authority_identity.json", "authority/splatam_authority_identity.json"]


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--task-root", type=Path, required=True)
    parser.add_argument("--v1-root", type=Path, required=True)
    parser.add_argument("--v1-script", type=Path, required=True)
    parser.add_argument("--pr67-head", required=True)
    parser.add_argument("--script-blob", required=True)
    parser.add_argument("--script-sha256", required=True)
    args = parser.parse_args()
    if args.pr67_head != "f8974c21d81eba7f207945bd50bd1a5245bd3bb7":
        raise SystemExit("BLOCKED_BY_ARKITSCENES_V1_IDENTITY_MISMATCH: unexpected PR67 head")
    script_sha = sha256_file(args.v1_script)
    script_blob = subprocess.check_output(["git", "hash-object", str(args.v1_script)], text=True).strip()
    if script_sha != args.script_sha256 or script_blob != args.script_blob:
        raise SystemExit("BLOCKED_BY_ARKITSCENES_V1_IDENTITY_MISMATCH: V1 script mismatch")
    records: dict[str, str] = {}
    contracts: dict[str, dict[str, object]] = {}
    for video, expected in EXPECTED.items():
        for template in FILES:
            relative = template.format(video=video)
            path = v1_path(args.v1_root, relative)
            if not path.is_file():
                raise SystemExit(f"BLOCKED_BY_ARKITSCENES_V1_IDENTITY_MISMATCH: missing {relative}")
            records[relative] = sha256_file(path)
        joined = v1_path(args.v1_root, f"frame_join/{video}/arkitscenes_joined_frame_manifest.csv")
        split = v1_path(args.v1_root, f"frame_split/{video}/arkitscenes_frame_split_contract.json")
        contracts[video] = json.loads(split.read_text(encoding="utf-8"))
        if records[f"frame_join/{video}/arkitscenes_joined_frame_manifest.csv"] != expected["joined_sha256"]:
            raise SystemExit("BLOCKED_BY_ARKITSCENES_V1_IDENTITY_MISMATCH: joined manifest SHA")
        if int(contracts[video]["keyframe_count"]) != expected["keyframes"] or str(contracts[video]["joined_manifest_sha256"]) != expected["joined_sha256"]:
            raise SystemExit("BLOCKED_BY_ARKITSCENES_V1_IDENTITY_MISMATCH: V1 split contract")
    for relative in GLOBAL_FILES:
        path = v1_path(args.v1_root, relative)
        if not path.is_file():
            raise SystemExit(f"BLOCKED_BY_ARKITSCENES_V1_IDENTITY_MISMATCH: missing {relative}")
        records[relative] = sha256_file(path)
    authority = json.loads(v1_path(args.v1_root, "authority/arkitscenes_authority_identity.json").read_text(encoding="utf-8"))
    splatam = json.loads(v1_path(args.v1_root, "authority/splatam_authority_identity.json").read_text(encoding="utf-8"))
    result = {
        "status": "V1_INPUT_IDENTITY_PASS",
        "source_pr": 67,
        "source_pr_head": args.pr67_head,
        "v1_frame_split_script": {"path": "freeze_arkitscenes_frame_split.py", "git_blob_sha": script_blob, "sha256": script_sha},
        "fixed_candidates": EXPECTED,
        "critical_file_sha256": records,
        "arkitscenes_authority_commit": authority.get("commit", authority.get("head")),
        "splatam_authority_commit": splatam.get("commit", splatam.get("head")),
        "v1_seed": 20260730,
        "v1_keyframe_thresholds": {"translation_m": 0.08, "rotation_deg": 8.0, "farthest_pose_only_above": 600},
        "v1_group_thresholds": {"timestamp_s": 2.0, "center_m": 0.15, "rotation_deg": 15.0},
        "no_training": True,
    }
    destination = args.task_root / "v1_identity" / "frozen_arkitscenes_v1_input_identity.json"
    atomic_json(destination, result)
    print("V1_INPUT_IDENTITY_PASS", sha256_file(destination))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
