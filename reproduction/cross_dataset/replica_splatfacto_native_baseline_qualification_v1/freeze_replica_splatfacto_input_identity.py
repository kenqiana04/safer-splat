#!/usr/bin/env python3
"""Read-only Replica V3 and PR #56 frozen-identity gate."""
from __future__ import annotations

import argparse
from collections import Counter

from _common import DATASET, EXPECTED, PR56_ROOT, ROOT, atomic_json, ensure_dirs, ensure_manifest, gate_after, load_json, sha256_path, tree_sha, update_stage


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--pr56-head", required=True)
    args = parser.parse_args()
    ensure_dirs()
    ensure_manifest(args.pr56_head)
    files = {
        "REPLICA_RENDER_PROTOCOL_V3_CONTRACT.json": "contract",
        "formal_camera_manifest_v3.csv": "manifest_csv",
        "formal_camera_manifest_v3.json": "manifest_json",
        "transforms_v3.json": "transforms",
        "selected_v3_location_registry.json": "registry",
    }
    hashes = {name: sha256_path(DATASET / name) for name in files}
    manifest = load_json(DATASET / "formal_camera_manifest_v3.json")["frames"]
    protocol = load_json(DATASET / "replica_protocol_v3_identity.json")
    rgb = {path.stem for path in (DATASET / "images").glob("*.png")}
    depth = {path.stem for path in (DATASET / "depth").glob("*.png")}
    ids = [row["frame_id"] for row in manifest]
    splits = Counter(row["split"] for row in manifest)
    rgb_tree, rgb_count = tree_sha(DATASET / "images")
    depth_tree, depth_count = tree_sha(DATASET / "depth")
    content_tree, content_count = tree_sha(DATASET, ("publication_identity.json",))
    complete_tree, complete_count = tree_sha(DATASET)
    order = load_json(PR56_ROOT / "pilot_registry" / "replica_frontend_map_only_order.json")
    checks = {
        "pr56_head": args.pr56_head == EXPECTED["pr56_head"],
        "metadata": all(hashes[name] == EXPECTED[key] for name, key in files.items()),
        "pose": protocol.get("pose_array_sha256") == EXPECTED["pose"],
        "rgb_tree": rgb_tree == EXPECTED["rgb_tree"], "depth_tree": depth_tree == EXPECTED["depth_tree"],
        "content_tree": content_tree == EXPECTED["content_tree"], "complete_tree": complete_tree == EXPECTED["complete_tree"],
        "frames": len(manifest) == 300 and len(set(ids)) == 300 and len({row["location_id"] for row in manifest}) == 100,
        "pairing": rgb == set(ids) and depth == set(ids) and len(rgb) == 300 and len(depth) == 300,
        "split": dict(splits) == {"train": 270, "eval": 30},
        "pilot_selection_core": order.get("registry_selection_core_sha256") == EXPECTED["pilot_selection_core"],
        "ingestion_order": order.get("frame_order_sha256") == EXPECTED["ingestion_order"],
    }
    status = "PASS_REPLICA_SPLATFACTO_INPUT_IDENTITY" if all(checks.values()) else "BLOCKED_BY_REPLICA_SPLATFACTO_INPUT_IDENTITY_MISMATCH"
    out = {"status": status, "dataset": str(DATASET), "pr56_head": args.pr56_head, "expected": EXPECTED, "metadata_sha256": hashes, "pose_array_sha256": protocol.get("pose_array_sha256"), "trees": {"rgb": [rgb_tree, rgb_count], "depth": [depth_tree, depth_count], "content": [content_tree, content_count], "complete": [complete_tree, complete_count]}, "frame_count": len(manifest), "location_count": len({row["location_id"] for row in manifest}), "split": dict(splits), "pilot_selection_core_sha256": order.get("registry_selection_core_sha256"), "ingestion_order_sha256": order.get("frame_order_sha256"), "checks": checks}
    atomic_json(ROOT / "input_identity" / "input_identity_summary.json", out)
    update_stage("INPUT_IDENTITY", "TERMINAL_SCIENTIFIC_RESULT", result_status=status)
    if status != "PASS_REPLICA_SPLATFACTO_INPUT_IDENTITY":
        gate_after("INPUT_IDENTITY", status)
        raise SystemExit(status)
    print(status)


if __name__ == "__main__":
    main()
