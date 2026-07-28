#!/usr/bin/env python3
"""Read-only identity gate for the atomically published Replica RGB-D V3 tree."""
from __future__ import annotations

import argparse
from collections import Counter

from _common import DATASET, EXPECTED, ROOT, atomic_json, ensure_dirs, initial_manifest, load_json, manifest_path, sha256_path, tree_sha


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--pr55-head", required=True)
    args = parser.parse_args()
    ensure_dirs()
    file_names = {
        "REPLICA_RENDER_PROTOCOL_V3_CONTRACT.json": "contract",
        "formal_camera_manifest_v3.csv": "manifest_csv",
        "formal_camera_manifest_v3.json": "manifest_json",
        "transforms_v3.json": "transforms",
        "selected_v3_location_registry.json": "registry",
    }
    hashes = {name: sha256_path(DATASET / name) for name in file_names}
    manifest = load_json(DATASET / "formal_camera_manifest_v3.json")["frames"]
    protocol_identity = load_json(DATASET / "replica_protocol_v3_identity.json")
    rgb = {path.stem for path in (DATASET / "images").glob("*.png")}
    depth = {path.stem for path in (DATASET / "depth").glob("*.png")}
    ids = [row["frame_id"] for row in manifest]
    locations = {row["location_id"] for row in manifest}
    splits = Counter(row["split"] for row in manifest)
    location_splits = {(row["location_id"], row["split"]) for row in manifest}
    rgb_tree, rgb_count = tree_sha(DATASET / "images")
    depth_tree, depth_count = tree_sha(DATASET / "depth")
    content_tree, content_count = tree_sha(DATASET, ("publication_identity.json",))
    complete_tree, complete_count = tree_sha(DATASET)
    checks = {
        "pr55_head": args.pr55_head == EXPECTED["pr55_head"],
        "metadata_hashes": all(hashes[name] == EXPECTED[key] for name, key in file_names.items()),
        "pose_hash": protocol_identity.get("pose_array_sha256") == EXPECTED["pose"],
        "rgb_tree": rgb_tree == EXPECTED["rgb_tree"],
        "depth_tree": depth_tree == EXPECTED["depth_tree"],
        "content_tree": content_tree == EXPECTED["content_tree"],
        "complete_tree": complete_tree == EXPECTED["complete_tree"],
        "manifest": len(manifest) == 300 and len(set(ids)) == 300 and len(locations) == 100,
        "disk_pairing": rgb == set(ids) and depth == set(ids) and len(rgb) == 300 and len(depth) == 300,
        "split": splits == {"train": 270, "eval": 30} and len({location for location, split in location_splits if split == "train"}) == 90 and len({location for location, split in location_splits if split == "eval"}) == 10,
    }
    status = "PASS_REPLICA_MAPPING_INPUT_IDENTITY" if all(checks.values()) else "BLOCKED_BY_REPLICA_MAPPING_INPUT_IDENTITY_MISMATCH"
    output = {
        "status": status, "dataset": str(DATASET), "pr55_head": args.pr55_head,
        "expected": EXPECTED, "metadata_sha256": hashes, "pose_array_sha256": protocol_identity.get("pose_array_sha256"),
        "trees": {"rgb": [rgb_tree, rgb_count], "depth": [depth_tree, depth_count], "content": [content_tree, content_count], "complete": [complete_tree, complete_count]},
        "frame_count": len(manifest), "location_count": len(locations), "disk_rgb_count": len(rgb), "disk_depth_count": len(depth), "splits": dict(splits),
        "missing_rgb": sorted(set(ids) - rgb), "missing_depth": sorted(set(ids) - depth), "extra_rgb": sorted(rgb - set(ids)), "extra_depth": sorted(depth - set(ids)), "checks": checks,
    }
    atomic_json(ROOT / "input_identity" / "input_identity_summary.json", output)
    if not manifest_path().exists():
        atomic_json(manifest_path(), initial_manifest())
    if status != "PASS_REPLICA_MAPPING_INPUT_IDENTITY":
        raise SystemExit(status)


if __name__ == "__main__":
    main()
