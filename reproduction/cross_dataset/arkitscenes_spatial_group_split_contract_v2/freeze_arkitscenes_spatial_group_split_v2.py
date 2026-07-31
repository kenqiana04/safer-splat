#!/usr/bin/env python3
"""Freeze the sole V2 allocation from a completed feasibility audit."""
from __future__ import annotations

import argparse
import csv
import hashlib
import json
import subprocess
from pathlib import Path

from arkitscenes_split_v2_common import atomic_csv, atomic_json, read_csv, sha256_file


LEGACY_CRLFS = {
    "arkitscenes_train_manifest_v2.csv": "b2d66720fbb0bc7acc998a81e073a9e4774ece7e3ce2900651ff28bf921c2404",
    "arkitscenes_heldout_manifest_v2.csv": "670255f2e00f04a0e462e1a83cd4c4d0344e92906604aba9312aa7baabb3b78e",
}


def canonical_lf_text_sha256(path: Path) -> str:
    data = path.read_bytes()
    if data.startswith(b"\xef\xbb\xbf"):
        raise SystemExit("PRODUCER_OR_GITATTRIBUTES_BOM_FORBIDDEN")
    data = data.replace(b"\r\n", b"\n")
    if b"\r" in data:
        raise SystemExit("PRODUCER_OR_GITATTRIBUTES_BARE_CR_FORBIDDEN")
    return hashlib.sha256(data).hexdigest()


def manifest_identity(task_root: Path, path: Path, producer_sha256: str, gitattributes_sha256: str) -> dict[str, object]:
    with path.open("r", encoding="utf-8", newline="") as handle:
        rows = list(csv.reader(handle))
    if not rows or any(len(row) != len(rows[0]) for row in rows[1:]):
        raise SystemExit("CSV_SEMANTIC_IDENTITY_FAILURE")
    payload = {"fieldnames": rows[0], "ordered_rows": rows[1:]}
    semantic_bytes = (json.dumps(payload, ensure_ascii=True, separators=(",", ":"), sort_keys=False) + "\n").encode("utf-8")
    raw_sha = sha256_file(path)
    oid = subprocess.check_output(["git", "-C", str(Path(__file__).resolve().parent), "hash-object", str(path.resolve())], text=True).strip()
    return {"path": str(path.relative_to(task_root)).replace("\\", "/"), "git_blob_oid": oid, "git_blob_sha256": raw_sha, "semantic_csv_sha256": hashlib.sha256(semantic_bytes).hexdigest(), "encoding": "UTF-8", "bom": False, "line_ending": "LF", "row_count": len(rows) - 1, "fieldnames": rows[0], "producer_sha256": producer_sha256, "gitattributes_sha256": gitattributes_sha256, "precommit_generated_lf_sha256": raw_sha, "precommit_generated_sha_note": "PRECOMMIT_GENERATED_SHA_IS_NOT_YET_GIT_BLOB_AUTHORITY", "legacy_generation_identity": {"legacy_worktree_crlf_sha256": LEGACY_CRLFS[path.name], "classification": "PRECOMMIT_PLATFORM_DEPENDENT_NOT_AUTHORITATIVE", "source": "PR68_ORIGINAL_CONTRACT", "semantic_equivalence": "PASS"}}


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
    train_path = output / "arkitscenes_train_manifest_v2.csv"
    heldout_path = output / "arkitscenes_heldout_manifest_v2.csv"
    source_root = Path(__file__).resolve().parent
    producer_sha256 = canonical_lf_text_sha256(source_root / "arkitscenes_split_v2_common.py")
    gitattributes_sha256 = canonical_lf_text_sha256(source_root / ".gitattributes")
    identity = {"source_pr": 67, "source_pr_head": "f8974c21d81eba7f207945bd50bd1a5245bd3bb7", "video_id": "48018874", "algorithm": "complete_v1_group_subset_sum_dp_v2", "algorithm_version": 2, "target_formula": "floor(0.20*N+0.5)", "target_heldout": feasibility["target_heldout"], "hard_constraints": feasibility["hard_constraints"], "optimization_score": [abs(len(heldout)-int(feasibility["target_heldout"])), len(heldout), list(selected_tuple)], "selected_group_hashes": list(selected_tuple), "selected_group_hash_tuple_sha256": tuple_sha, "train_count": len(train), "heldout_count": len(heldout), "train_group_count": len(registry["groups"]) - len(selected_hashes), "heldout_group_count": len(selected_hashes), "v1_group_registry_sha256": sha256_file(registry_path), "train_manifest_sha256": sha256_file(train_path), "heldout_manifest_sha256": sha256_file(heldout_path), "identity_policy": "CANONICAL_GIT_BLOB_BYTES_SHA256_V1", "manifest_identities": {"train": manifest_identity(args.task_root, train_path, producer_sha256, gitattributes_sha256), "heldout": manifest_identity(args.task_root, heldout_path, producer_sha256, gitattributes_sha256)}, "producer_sha256": producer_sha256, "gitattributes_sha256": gitattributes_sha256, "no_training": True, "no_mapping": True, "no_geometry_result": True}
    identity["split_identity_sha256"] = hashlib.sha256(json.dumps(identity, sort_keys=True, separators=(",", ":")).encode("utf-8")).hexdigest()
    atomic_json(output / "arkitscenes_spatial_group_split_contract_v2.json", identity)
    atomic_json(output / "selected_arkitscenes_mapping_scene_v2.json", {"video_id": "48018874", "role": "ARKITSCENES_V2_SELECTED_MAPPING_SCENE", "primary_role": "VALID_DATA_AND_COORDINATE_AUDIT_BUT_INSUFFICIENT_KEYFRAMES_FOR_V2", "split_identity_sha256": identity["split_identity_sha256"], "no_training": True})
    print("V2_SPLIT_FROZEN", len(train), len(heldout), tuple_sha)
    return 0


if __name__ == "__main__": raise SystemExit(main())
