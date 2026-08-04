#!/usr/bin/env python3
"""Hash every compact tracked artifact while excluding the self-referential manifest."""

from __future__ import annotations

import hashlib
import json
from pathlib import Path


ROOT = Path(__file__).resolve().parent
OUTPUT = ROOT / "compact_artifact_manifest.json"
FORBIDDEN_NAMES = {
    "reference_prm_graph_full.json",
    "reference_prm_nodes_pre_edges.json",
    "reference_route_candidates_full.json",
    "reference_route_registry_full.json",
    "archive_internal_manifest.csv",
}
FORBIDDEN_SUFFIXES = {".7z", ".xz", ".ply", ".jpg", ".jpeg", ".exr"}


def sha(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def main() -> None:
    rows = []
    for path in sorted(item for item in ROOT.rglob("*") if item.is_file()):
        if path == OUTPUT or "__pycache__" in path.parts:
            continue
        relative = path.relative_to(ROOT).as_posix()
        if path.name in FORBIDDEN_NAMES or path.suffix.lower() in FORBIDDEN_SUFFIXES:
            raise RuntimeError(f"FORBIDDEN_TRACKED_PAYLOAD {relative}")
        if path.suffix.lower() == ".png" and path.parent.name != "figures":
            raise RuntimeError(f"NONFIGURE_IMAGE_PAYLOAD {relative}")
        rows.append({"path": relative, "bytes": path.stat().st_size, "sha256": sha(path)})
    payload = {
        "status": "PASS_COMPACT_TRACKED_ARTIFACT_SET",
        "file_count": len(rows),
        "total_bytes": sum(row["bytes"] for row in rows),
        "forbidden_payload_count": 0,
        "artifacts": rows,
    }
    OUTPUT.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print("PASS_COMPACT_ARTIFACT_MANIFEST", len(rows), payload["total_bytes"])


if __name__ == "__main__":
    main()
