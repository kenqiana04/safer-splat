#!/usr/bin/env python3
"""Build server-only per-file inventory and deterministic V3 staging tree identities."""
from __future__ import annotations

import csv
from pathlib import Path

from _common import ROOT, atomic_json, load_json, sha256_path, tree_sha


def main() -> None:
    staging = ROOT / "formal_staging"
    frames = {item["frame_id"]: item for item in load_json(staging / "formal_camera_manifest_v3.json")["frames"]}
    rows = []
    for path in sorted(item for item in staging.rglob("*") if item.is_file()):
        relative = path.relative_to(staging).as_posix(); frame_id = path.stem if path.parent.name in {"images", "depth"} else ""; item = frames.get(frame_id, {})
        rows.append({"relative_path": relative, "file_size": path.stat().st_size, "sha256": sha256_path(path), "modality": "rgb" if path.parent.name == "images" else "depth" if path.parent.name == "depth" else "metadata", "frame_id": frame_id, "split": item.get("split", ""), "location_id": item.get("location_id", "")})
    inventory = ROOT / "tree_identity" / "formal_staging_file_sha256_manifest.csv"
    with inventory.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=list(rows[0])); writer.writeheader(); writer.writerows(rows)
    payload = {"status": "PASS", "tree_sha_algorithm": "SHA256(UTF-8 newline join of path_sorted_relative_path NUL decimal_size NUL file_SHA256)", "path_sort": "lexicographic POSIX relative path", "size_included": True, "rgb_tree_sha256": tree_sha(staging / "images"), "depth_tree_sha256": tree_sha(staging / "depth"), "metadata_tree_sha256": __import__("hashlib").sha256("\n".join(row["relative_path"] + "\0" + str(row["file_size"]) + "\0" + row["sha256"] for row in rows if row["modality"] == "metadata").encode()).hexdigest(), "complete_staging_tree_sha256": tree_sha(staging), "file_count": len(rows), "file_sha_manifest_server_only": str(inventory)}
    atomic_json(ROOT / "tree_identity" / "replica_rgbd_v3_tree_identity.json", payload)


if __name__ == "__main__": main()
