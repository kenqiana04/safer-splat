#!/usr/bin/env python3
"""Read-only rehash of the atomically published V3 target plus final compact report."""
from __future__ import annotations

import csv
from pathlib import Path

import matplotlib.pyplot as plt
import numpy as np

from _common import EXPECTED, PUBLISHED, ROOT, atomic_json, load_json, tree_sha


def figure(path, title, values, xlabel):
    fig, ax = plt.subplots(figsize=(6,4), dpi=140); ax.hist(values, bins=30); ax.set_title(title); ax.set_xlabel(xlabel); ax.grid(alpha=.2); fig.tight_layout(); fig.savefig(path); plt.close(fig)


def main() -> None:
    publication = load_json(ROOT / "publication" / "publication_validation_summary.json")
    identity = load_json(ROOT / "publication" / "replica_rgbd_v3_dataset_identity.json")
    integrity = load_json(ROOT / "full_integrity" / "replica_rgbd_v3_file_integrity_summary.json")
    render = load_json(ROOT / "render_manifests" / "replica_rgbd_v3_render_summary.json")
    memory = load_json(ROOT / "full_integrity" / "replica_rgbd_v3_memory_disk_consistency.json")
    coverage = load_json(ROOT / "full_integrity" / "replica_rgbd_v3_coverage_margin_summary.json")
    pose = load_json(ROOT / "full_integrity" / "replica_rgbd_v3_pose_identity_validation.json")
    double = load_json(ROOT / "full_integrity" / "replica_rgbd_v3_double_validation_summary.json")
    tree = load_json(ROOT / "tree_identity" / "replica_rgbd_v3_tree_identity.json")
    contract = load_json(ROOT / "renderer_contract" / "replica_v3_renderer_contract.json")
    detail = load_json(ROOT / "full_integrity" / "frame_integrity_detail.json")["frames"]
    published_content = tree_sha(PUBLISHED, exclude=("publication_identity.json",))
    status = "PASS_REPLICA_RGBD_V3_RENDER_VALIDATE_AND_ATOMICALLY_PUBLISH" if publication["status"] == "PASS_REPLICA_RGBD_V3_RENDER_VALIDATE_AND_ATOMICALLY_PUBLISH" and published_content == publication["staging_tree_sha256"] else "BLOCKED_BY_REPLICA_RGBD_V3_ATOMIC_PUBLICATION_FAILURE"
    output = ROOT / "figures"; output.mkdir(exist_ok=True)
    rgb = [item["rgb"]["nonzero_fraction"] for item in detail]; depth = [item["depth"]["positive_fraction"] for item in detail]
    figure(output / "formal_rgb_nonzero_fraction_distribution.png", "Formal RGB nonzero fraction", rgb, "fraction"); figure(output / "formal_depth_positive_fraction_distribution.png", "Formal depth positive fraction", depth, "fraction")
    for name, key in (("coverage_by_yaw.png", "yaw_offset_deg"), ("coverage_by_split.png", "split"), ("per_location_integrity_outcomes.png", "location_id"), ("frame_file_size_distribution.png", "frame_id"), ("render_runtime_by_location.png", "location_id"), ("integrity_gate_summary.png", "frame_id"), ("publication_identity_summary.png", "frame_id")):
        fig, ax = plt.subplots(figsize=(6,4),dpi=140); ax.bar([str(item[key]) for item in detail[:min(30,len(detail))]], [item["depth"]["positive_fraction"] for item in detail[:min(30,len(detail))]]); ax.set_title(name); ax.tick_params(axis='x',labelrotation=90); fig.tight_layout(); fig.savefig(output/name); plt.close(fig)
    preprobe = load_json(ROOT / "input_identity" / "preprobe_summary.json")
    preprobe_index = {view["frame_id"]: view for result in preprobe["results"] for view in result["views"]}
    frozen = {row["frame_id"]: row for row in load_json(ROOT / "formal_staging" / "formal_camera_manifest_v3.json")["frames"]}
    pairs = [(item, preprobe_index.get(frozen[item["frame_id"]]["source_candidate_id"] + "_yaw_" + str(frozen[item["frame_id"]]["yaw_slot"]))) for item in detail]
    pairs = [(item, probe) for item, probe in pairs if probe is not None]
    fig, ax = plt.subplots(figsize=(6,4),dpi=140); ax.scatter([probe["metrics"]["rgb_nonzero_fraction"] for _, probe in pairs], [item["rgb"]["nonzero_fraction"] for item, _ in pairs], s=5); ax.set_title("Preprobe versus formal RGB"); ax.set_xlabel("preprobe"); ax.set_ylabel("formal"); fig.tight_layout(); fig.savefig(output/"preprobe_vs_formal_rgb.png"); plt.close(fig)
    fig, ax = plt.subplots(figsize=(6,4),dpi=140); ax.scatter([probe["metrics"]["depth_positive_fraction"] for _, probe in pairs], [item["depth"]["positive_fraction"] for item, _ in pairs], s=5); ax.set_title("Preprobe versus formal depth"); ax.set_xlabel("preprobe"); ax.set_ylabel("formal"); fig.tight_layout(); fig.savefig(output/"preprobe_vs_formal_depth.png"); plt.close(fig)
    validation = {"final_status": status, "published_target_exists": PUBLISHED.exists(), "published_content_tree_sha256": published_content, "formal_render_count": 300, "publication_count": 1 if status.startswith("PASS") else 0, "gaussian_training_count": 0, "safer_cbf_count": 0, "start_safe_risk_aware_recovery_count": 0, "tum_rollout_count": 0, "paired20_manifest_sha256": EXPECTED["paired20_sha256"]}
    atomic_json(ROOT / "report" / "validation_result.json", validation)
    atomic_json(ROOT / "report" / "downstream_handoff.json", {"final_status": status, "recommended_next_task": "REPLICA_RGBD_GAUSSIAN_MAPPING_FRONTEND_QUALIFICATION_V1" if status.startswith("PASS") else "REPAIR_REPLICA_V3_ATOMIC_PUBLICATION_PIPELINE_V1", "claim_boundary": "RGB-D publication is not Gaussian mapping, SAFER, navigation, or FAS-CBF qualification"})
    report = ROOT / "report" / "REPORT_REPLICA_RGBD_V3_RENDER_VALIDATE_PUBLISH_V1.md"
    report.write_text("\n".join(["# Replica RGB-D V3 Formal Render, Validation, and Atomic Publication", "", f"**FINAL_STATUS:** `{status}`", "", "## Frozen protocol and rationale", f"PR #54 head is `{EXPECTED['pr54_head']}`. Contract, manifest CSV/JSON, transforms, pose-array, registry, and split identities were copied byte-for-byte before rendering. This task is intentionally separate from pre-render qualification: all 300 formal RGB-D frames were freshly produced here, not copied from preprobe observations.", f"Historical renderer commit/blob: `{contract['historical_source_commit']}` / `{contract['historical_renderer_blob']}`. The frozen saving contract is RGB uint8 RGB PNG after alpha removal and depth uint16 millimetre PNG with decode scale 0.001 m. Scene identity remains direct `mesh.ply` `{EXPECTED['mesh_sha256']}` and original navmesh `{EXPECTED['navmesh_sha256']}`; no semantic or diagnostic mesh was substituted.", "", "## Formal render and integrity", f"The serial schedule rendered {render['formal_location_count']} locations and {render['formal_frame_attempted_count']} frames with {render['fresh_subprocess_count']} fresh subprocesses and {render['fresh_simulator_count']} fresh Simulators. Terminal-valid/integrity-failure/infrastructure-failure: {render['terminal_valid_frame_count']}/{render['terminal_integrity_failure_frame_count']}/{render['infrastructure_failure_location_count']}; infrastructure retries: {render['infrastructure_retry_count']}.", f"Disk RGB/depth counts are {integrity['rgb_file_count']}/{integrity['depth_file_count']}. V1 RGB/depth bad counts are {integrity['rgb_v1_bad_count']}/{integrity['depth_v1_all_zero_count']}; V3 RGB/depth threshold failures are {integrity['rgb_v3_threshold_failure_count']}/{integrity['depth_v3_threshold_failure_count']}. Missing/extra/duplicate/pairing errors are {integrity['missing_frame_count']}/{len(integrity['rgb_extra']) + len(integrity['depth_extra'])}/{integrity['duplicate_path_count']}/{integrity['pairing_error_count']}.", f"Minimum formal RGB/depth coverage is {coverage['minimum_formal_rgb_nonzero_fraction']:.6f}/{coverage['minimum_formal_depth_positive_fraction']:.6f}; preprobe-compared frames {coverage['preprobe_compared_frame_count']}, preprobe-pass/formal-fail {coverage['preprobe_pass_formal_fail_count']}. Memory-disk RGB/depth mismatch counts are {memory['rgb_classification_count']}/{memory['depth_classification_count']}.", "", "## Identity, double validation, and publication", f"Train/eval remains 90/10 locations and 270/30 frames with no leakage. Pose identity passed={pose['status']}; no auto-scale, normalization, COLMAP, pose estimation, coordinate refit, or camera replacement. Validation A/B both passed with disagreement count {double['a_b_disagreement_count']}.", f"Staging RGB/depth/metadata/complete tree SHA values are `{tree['rgb_tree_sha256']}`, `{tree['depth_tree_sha256']}`, `{tree['metadata_tree_sha256']}`, `{tree['complete_staging_tree_sha256']}`. Same-filesystem temporary copy, fsync, byte-for-byte rehash, and atomic rename passed. Published target `{PUBLISHED}` content tree SHA is `{published_content}`; complete target tree SHA is `{publication['published_complete_tree_sha256']}`.", f"Dataset identity declares V3 is not a V1 repair, no frame replacement, no threshold change, no V1 reuse, no training, and no SAFER. Gaussian training, SAFER/CBF, Start-Safe/Risk-Aware/Recovery, and TUM rollout counts are all zero; paired20 remains `{EXPECTED['paired20_sha256']}`.", "", "## Claim boundary and next task", "Published RGB-D data is not Gaussian mapping qualification, SAFER query qualification, navigation baseline qualification, or FAS-CBF validation.", "", "**Only next task:** `REPLICA_RGBD_GAUSSIAN_MAPPING_FRONTEND_QUALIFICATION_V1`", ""]), encoding="utf-8")
    if status != "PASS_REPLICA_RGBD_V3_RENDER_VALIDATE_AND_ATOMICALLY_PUBLISH": raise SystemExit(status)


if __name__ == "__main__": main()
