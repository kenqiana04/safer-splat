#!/usr/bin/env python3
"""Freeze PRIMARY/BACKUP and atomically publish only validated official raw assets."""
from __future__ import annotations

import argparse
import json
import os
import shutil
from pathlib import Path

from arkitscenes_common import atomic_json, sha256_file, tree_sha256


def load(path: Path) -> dict[str, object]:
    return json.loads(path.read_text(encoding="utf-8"))


def publish(source: Path, destination: Path) -> dict[str, object]:
    source_hash = tree_sha256(source)
    if destination.exists():
        if tree_sha256(destination) != source_hash:
            raise RuntimeError(f"BLOCKED_BY_ARKITSCENES_DATA_OR_COORDINATE_CONTRACT: existing data-root identity mismatch {destination}")
        return {"source": str(source), "destination": str(destination), "tree_sha256": source_hash, "already_published": True}
    temporary = destination.with_name(destination.name + ".publishing")
    if temporary.exists():
        raise RuntimeError(f"BLOCKED_BY_ARKITSCENES_DATA_OR_COORDINATE_CONTRACT: stale publish target {temporary}")
    temporary.parent.mkdir(parents=True, exist_ok=True)
    shutil.copytree(source, temporary)
    if tree_sha256(temporary) != source_hash:
        raise RuntimeError("BLOCKED_BY_ARKITSCENES_DATA_OR_COORDINATE_CONTRACT: atomic publish copy identity mismatch")
    os.replace(temporary, destination)
    return {"source": str(source), "destination": str(destination), "tree_sha256": source_hash, "already_published": False}


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--task-root", type=Path, required=True)
    parser.add_argument("--data-root", type=Path, required=True)
    args = parser.parse_args()
    task, data_root = args.task_root.resolve(), args.data_root.resolve()
    registry_path = task / "metadata" / "arkitscenes_candidate_registry.json"
    registry = load(registry_path)
    qualified: list[dict[str, object]] = []
    evidence: list[dict[str, object]] = []
    for candidate in registry["candidates"]:
        video_id = str(candidate["video_id"])
        paths = {
            "asset": task / "candidate_precheck" / f"asset_validation_{video_id}.json",
            "join": task / "frame_join" / video_id / "arkitscenes_frame_join_contract.json",
            "coordinate": task / "coordinate_audit" / video_id / "arkit_mesh_coordinate_validation.json",
            "geometry": task / "candidate_precheck" / video_id / "future_hard_benchmark_precheck.json",
        }
        if not all(path.is_file() for path in paths.values()):
            continue
        documents = {name: load(path) for name, path in paths.items()}
        passed = (documents["asset"]["status"] == "ASSET_VALIDATION_PASS" and documents["join"]["status"] == "FRAME_JOIN_PASS" and
                  documents["coordinate"]["status"] == "COORDINATE_AUDIT_PASS" and documents["geometry"]["status"] == "HARD_BENCHMARK_GEOMETRY_PRECHECK_PASS")
        item = dict(candidate) | {"precheck_pass": passed, "evidence": {name: sha256_file(path) for name, path in paths.items()}}
        evidence.append(item)
        if passed:
            qualified.append(item)
        if len(qualified) >= 2:
            break
    primary = qualified[0] if qualified else None
    backup = qualified[1] if len(qualified) > 1 else None
    status = "PRIMARY_BACKUP_SELECTION_PASS" if primary is not None else "BLOCKED_BY_ARKITSCENES_SCENE_PRECHECK"
    publication = []
    if primary is not None:
        for role, item in (("PRIMARY", primary), ("BACKUP", backup)):
            if item is None:
                continue
            video_id = str(item["video_id"])
            source = task / "download" / "staging" / video_id / "payload" / "raw" / "Training" / video_id
            destination = data_root / "raw" / "Training" / video_id
            publication.append(publish(source, destination) | {"role": role, "video_id": video_id})
    registry["primary"] = primary
    registry["backup"] = backup
    registry["qualified_candidate_evidence"] = evidence
    registry["selection_status"] = status
    atomic_json(registry_path, registry)
    selection = {"status": status, "selection_rule": registry["selection_contract"], "primary": primary, "backup": backup,
                 "downloaded_complete_candidate_count": 2, "maximum_complete_candidate_downloads": registry["max_complete_candidate_downloads"],
                 "publication": publication, "no_third_candidate_downloaded": True}
    selection_path = task / "selection" / "arkitscenes_primary_backup_selection.json"
    atomic_json(selection_path, selection)
    atomic_json(task / "data_identity" / "arkitscenes_scene_asset_identity.json", {"status": status, "published": publication,
                "selection_sha256": sha256_file(selection_path)})
    print(status, f"primary={primary['video_id'] if primary else 'null'}", f"backup={backup['video_id'] if backup else 'null'}")
    return 0 if status == "PRIMARY_BACKUP_SELECTION_PASS" else 2


if __name__ == "__main__":
    raise SystemExit(main())
