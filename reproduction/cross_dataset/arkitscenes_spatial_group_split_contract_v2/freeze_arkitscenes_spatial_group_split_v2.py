#!/usr/bin/env python3
"""Freeze the sole V2 allocation from a completed feasibility audit."""
from __future__ import annotations

import argparse
import json
from pathlib import Path

from arkitscenes_split_v2_common import atomic_csv, atomic_json, read_csv, sha256_file


def main() -> int:
    parser = argparse.ArgumentParser(); parser.add_argument("--task-root", type=Path, required=True); parser.add_argument("--v1-root", type=Path, required=True); args = parser.parse_args()
    feasibility_path = args.task_root / "feasibility" / "arkitscenes_v2_reachable_heldout_counts.json"
    feasibility = json.loads(feasibility_path.read_text(encoding="utf-8")); selected = feasibility.get("selected")
    if feasibility.get("status") != "V2_FEASIBLE" or not selected: raise SystemExit("NO_FEASIBLE_V2_SPLIT_FOR_EXISTING_ARKITSCENES_CANDIDATES")
    registry_path = args.task_root / "group_reconstruction" / "48018874" / "arkitscenes_v1_group_registry.json"
    registry = json.loads(registry_path.read_text(encoding="utf-8")); selected_hashes = set(selected["selected_group_hashes"])
    rows = read_csv(args.v1_root / "frame_join" / "48018874" / "arkitscenes_joined_frame_manifest.csv")
    keyframes = [row for row in rows]
    # Recreate the V1 keyframe rows from the registry's index/timestamp identity without changing selection.
    by_identity = {(row["timestamp"], row["rgb"], row["depth"], row["confidence"]): row for row in rows}
    group_by_index = {member: group for group in registry["groups"] for member in group["members"]}
    ordered = []
    for record in sorted(registry["keyframes"], key=lambda item: int(item["keyframe_index"])):
        source = by_identity[(record["timestamp"], record["rgb"], record["depth"], record["confidence"])]
        group = group_by_index[int(record["keyframe_index"])]
        split = "HELDOUT" if str(group["group_hash"]) in selected_hashes else "TRAIN"
        ordered.append(source | {"keyframe_index": record["keyframe_index"], "v1_group_id": group["group_id"], "v1_group_hash": group["group_hash"], "split": split})
    train = [row for row in ordered if row["split"] == "TRAIN"]; heldout = [row for row in ordered if row["split"] == "HELDOUT"]
    if len(train) < 200 or not (40 <= len(heldout) <= 60) or len(train)+len(heldout) != 267: raise SystemExit("V2_CONSTRAINT_VIOLATION")
    output = args.task_root / "v2_split"; fields = list(rows[0]) + ["keyframe_index", "v1_group_id", "v1_group_hash", "split"]
    atomic_csv(output / "arkitscenes_train_manifest_v2.csv", train, fields); atomic_csv(output / "arkitscenes_heldout_manifest_v2.csv", heldout, fields)
    selected_tuple = tuple(sorted(selected_hashes)); tuple_sha = sha256_file(feasibility_path) if False else __import__("hashlib").sha256("\n".join(selected_tuple).encode("utf-8")).hexdigest()
    identity = {"source_pr": 67, "source_pr_head": "f8974c21d81eba7f207945bd50bd1a5245bd3bb7", "video_id": "48018874", "algorithm": "complete_v1_group_subset_sum_dp_v2", "algorithm_version": 2, "target_formula": "floor(0.20*N+0.5)", "target_heldout": feasibility["target_heldout"], "hard_constraints": feasibility["hard_constraints"], "optimization_score": [abs(len(heldout)-int(feasibility["target_heldout"])), len(heldout), list(selected_tuple)], "selected_group_hashes": list(selected_tuple), "selected_group_hash_tuple_sha256": tuple_sha, "train_count": len(train), "heldout_count": len(heldout), "train_group_count": len(registry["groups"]) - len(selected_hashes), "heldout_group_count": len(selected_hashes), "v1_group_registry_sha256": sha256_file(registry_path), "train_manifest_sha256": sha256_file(output / "arkitscenes_train_manifest_v2.csv"), "heldout_manifest_sha256": sha256_file(output / "arkitscenes_heldout_manifest_v2.csv"), "no_training": True, "no_mapping": True, "no_geometry_result": True}
    import hashlib
    identity["split_identity_sha256"] = hashlib.sha256(json.dumps(identity, sort_keys=True, separators=(",", ":")).encode("utf-8")).hexdigest()
    atomic_json(output / "arkitscenes_spatial_group_split_contract_v2.json", identity)
    atomic_json(output / "selected_arkitscenes_mapping_scene_v2.json", {"video_id": "48018874", "role": "ARKITSCENES_V2_SELECTED_MAPPING_SCENE", "primary_role": "VALID_DATA_AND_COORDINATE_AUDIT_BUT_INSUFFICIENT_KEYFRAMES_FOR_V2", "split_identity_sha256": identity["split_identity_sha256"], "no_training": True})
    print("V2_SPLIT_FROZEN", len(train), len(heldout), tuple_sha)
    return 0


if __name__ == "__main__": raise SystemExit(main())
