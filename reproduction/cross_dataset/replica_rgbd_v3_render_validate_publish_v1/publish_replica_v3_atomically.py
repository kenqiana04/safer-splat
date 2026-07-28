#!/usr/bin/env python3
"""Publish a fully validated V3 staging tree through same-filesystem atomic rename."""
from __future__ import annotations

import os
import shutil
from pathlib import Path

from _common import EXPECTED, PUBLISHED, PUBLISH_TMP, ROOT, atomic_json, fsync_directory, load_json, sha256_path, tree_rows, tree_sha


def gate() -> tuple[bool, str]:
    render = load_json(ROOT / "render_manifests" / "replica_rgbd_v3_render_summary.json")
    integrity = load_json(ROOT / "full_integrity" / "replica_rgbd_v3_file_integrity_summary.json")
    memory = load_json(ROOT / "full_integrity" / "replica_rgbd_v3_memory_disk_consistency.json")
    pose = load_json(ROOT / "full_integrity" / "replica_rgbd_v3_pose_identity_validation.json")
    double = load_json(ROOT / "full_integrity" / "replica_rgbd_v3_double_validation_summary.json")
    conditions = [render["terminal_valid_frame_count"] == 300, render["terminal_integrity_failure_frame_count"] == 0, render["infrastructure_failure_location_count"] == 0, integrity["status"] == "PASS", memory["status"] == "PASS", pose["status"] == "PASS", double["status"] == "PASS", not PUBLISHED.exists()]
    return all(conditions), "all_gates_pass" if all(conditions) else "integrity_or_publication_gate_failed"


def copy_tree(source: Path, target: Path) -> None:
    for path in sorted(item for item in source.rglob("*") if item.is_file()):
        destination = target / path.relative_to(source); destination.parent.mkdir(parents=True, exist_ok=True); shutil.copy2(path, destination)
        with destination.open("rb") as handle: os.fsync(handle.fileno())
    for directory in sorted((item for item in target.rglob("*") if item.is_dir()), key=lambda item: len(item.parts), reverse=True): fsync_directory(directory)
    fsync_directory(target)


def main() -> None:
    passed, reason = gate(); publication_root = ROOT / "publication"; publication_root.mkdir(exist_ok=True)
    staging = ROOT / "formal_staging"
    if not passed:
        atomic_json(publication_root / "replica_rgbd_v3_dataset_identity.json", {"status": "NOT_PUBLISHED_DUE_TO_" + reason.upper(), "publication_target": str(PUBLISHED), "staging_tree_sha256": tree_sha(staging), "no_training": True, "no_safer": True})
        raise SystemExit("REPLICA_RGBD_V3_FORMAL_RENDER_INTEGRITY_GATE_FAILED")
    if PUBLISH_TMP.exists():
        quarantine = publication_root / ("quarantine_publish_tmp_" + str(os.getpid()))
        os.replace(PUBLISH_TMP, quarantine)
    PUBLISH_TMP.mkdir(parents=False)
    copy_tree(staging, PUBLISH_TMP)
    if tree_rows(staging) != tree_rows(PUBLISH_TMP):
        raise SystemExit("BLOCKED_BY_REPLICA_RGBD_V3_ATOMIC_PUBLICATION_FAILURE")
    content_tree = tree_sha(PUBLISH_TMP)
    identity = load_json(ROOT / "input_identity" / "input_identity_summary.json")
    tree = load_json(ROOT / "tree_identity" / "replica_rgbd_v3_tree_identity.json")
    integrity = load_json(ROOT / "full_integrity" / "replica_rgbd_v3_file_integrity_summary.json")
    publication_identity = {"status": "PUBLISHED_ATOMICALLY", "dataset_name": "Replica_RGBD_V3", "scene": "apartment_0", "protocol_version": "NEW_PREQUALIFIED_REPLICA_RENDER_PROTOCOL_V3", "not_v1_repair": True, "pr54_head": EXPECTED["pr54_head"], "contract_sha256": EXPECTED["contract_sha256"], "manifest_csv_sha256": EXPECTED["manifest_csv_sha256"], "manifest_json_sha256": EXPECTED["manifest_json_sha256"], "transforms_sha256": EXPECTED["transforms_sha256"], "pose_array_sha256": EXPECTED["pose_array_sha256"], "selected_registry_sha256": EXPECTED["registry_sha256"], "renderer": identity["task_owned_renderer_sha256"], "mesh_sha256": EXPECTED["mesh_sha256"], "navmesh_sha256": EXPECTED["navmesh_sha256"], "rgb_count": 300, "depth_count": 300, "train_eval_frames": [270, 30], "rgb_tree_sha256": tree["rgb_tree_sha256"], "depth_tree_sha256": tree["depth_tree_sha256"], "metadata_tree_sha256": tree["metadata_tree_sha256"], "staging_content_tree_sha256": tree["complete_staging_tree_sha256"], "published_content_tree_sha256": content_tree, "minimum_rgb_coverage": integrity["minimum_rgb_nonzero_fraction"], "minimum_depth_coverage": integrity["minimum_depth_positive_fraction"], "publication_target": str(PUBLISHED), "atomic_publication": True, "no_frame_replacement": True, "no_threshold_change": True, "no_v1_frame_reuse": True, "no_training": True, "no_safer": True}
    atomic_json(PUBLISH_TMP / "publication_identity.json", publication_identity)
    fsync_directory(PUBLISH_TMP)
    os.rename(PUBLISH_TMP, PUBLISHED)
    fsync_directory(PUBLISHED.parent)
    target_content = tree_sha(PUBLISHED, exclude=("publication_identity.json",))
    target_complete = tree_sha(PUBLISHED)
    result = {"status": "PASS_REPLICA_RGBD_V3_RENDER_VALIDATE_AND_ATOMICALLY_PUBLISH" if target_content == tree["complete_staging_tree_sha256"] else "BLOCKED_BY_REPLICA_RGBD_V3_ATOMIC_PUBLICATION_FAILURE", "atomic_rename": True, "publication_target": str(PUBLISHED), "staging_tree_sha256": tree["complete_staging_tree_sha256"], "published_content_tree_sha256": target_content, "published_complete_tree_sha256": target_complete, "byte_for_byte_content_match": target_content == tree["complete_staging_tree_sha256"]}
    atomic_json(publication_root / "publication_validation_summary.json", result)
    publication_identity["published_complete_tree_sha256"] = target_complete
    atomic_json(publication_root / "replica_rgbd_v3_dataset_identity.json", publication_identity)
    if result["status"] != "PASS_REPLICA_RGBD_V3_RENDER_VALIDATE_AND_ATOMICALLY_PUBLISH": raise SystemExit(result["status"])


if __name__ == "__main__": main()
