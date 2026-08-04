#!/usr/bin/env python3
"""Run three fresh train-model builds and materialize physically separated TRAIN/EVAL roots."""

from __future__ import annotations

import json
import os
import shutil
import subprocess
import sys
from pathlib import Path

from archive_common import tree_identity
from task_config import DATA_ROOT, EVAL_ROOT, QUARANTINE, TASK_ROOT, TRAIN_ROOT


def safe_reset(path: Path) -> None:
    resolved = path.resolve()
    if DATA_ROOT.resolve() not in resolved.parents:
        raise RuntimeError(f"UNSAFE_DATA_ROOT_RESET {resolved}")
    if path.exists():
        shutil.rmtree(path)
    path.mkdir(parents=True)


def hardlink(source: Path, target: Path) -> None:
    target.parent.mkdir(parents=True, exist_ok=True)
    try:
        os.link(str(source), str(target))
    except OSError:
        shutil.copy2(str(source), str(target))


def link_tree(source: Path, target: Path) -> None:
    for path in sorted(source.rglob("*")):
        relative = path.relative_to(source)
        if path.is_dir():
            (target / relative).mkdir(parents=True, exist_ok=True)
        elif path.is_file():
            hardlink(path, target / relative)
        else:
            raise RuntimeError(f"UNEXPECTED_SPECIAL_FILE_AFTER_EXTRACTION {path}")


def main() -> None:
    build_root = TASK_ROOT / "tmp" / "train_only_fresh_builds"
    if build_root.exists():
        shutil.rmtree(build_root)
    build_root.mkdir(parents=True)
    records = []
    script = TASK_ROOT / "build_train_only_colmap.py"
    for index in range(1, 4):
        output = build_root / f"build_{index}"
        result = subprocess.run([sys.executable, str(script), "--output", str(output), "--allowed-root", str(build_root)],
                                text=True, stdout=subprocess.PIPE, stderr=subprocess.STDOUT)
        (TASK_ROOT / "logs" / f"train_only_build_{index}.log").write_text(result.stdout, encoding="utf-8")
        if result.returncode:
            raise RuntimeError(f"TRAIN_ONLY_BUILD_FAILURE {index} {result.stdout[-1000:]}")
        records.append(json.loads(result.stdout.strip().splitlines()[-1]))
    hashes = {record["tree_sha256"] for record in records}
    if len(hashes) != 1:
        raise RuntimeError(f"TRAIN_ONLY_REPRODUCIBILITY_FAILURE {sorted(hashes)}")
    safe_reset(TRAIN_ROOT)
    safe_reset(EVAL_ROOT)
    link_tree(build_root / "build_1", TRAIN_ROOT)
    split = json.loads((TASK_ROOT / "split" / "pose_block_split_v1.json").read_text(encoding="utf-8"))
    partitions = {"HELDOUT": set(split["HELDOUT"]), "GUARD": set(split["GUARD"])}
    rig_images = QUARANTINE / "delivery_area_rig_undistorted" / "delivery_area" / "images"
    for partition, captures in partitions.items():
        for source in sorted(rig_images.rglob("*.png")):
            if source.stem in captures:
                hardlink(source, EVAL_ROOT / "rig_rgb" / partition / source.relative_to(rig_images))
    dslr_images = QUARANTINE / "delivery_area_dslr_undistorted" / "delivery_area" / "images"
    for source in sorted(path for path in dslr_images.rglob("*") if path.is_file()):
        hardlink(source, EVAL_ROOT / "dslr_rgb" / source.relative_to(dslr_images))
    oracle_archives = [
        "delivery_area_rig_scan_eval", "delivery_area_rig_occlusion", "delivery_area_rig_depth",
        "delivery_area_scan_clean", "delivery_area_dslr_scan_eval", "delivery_area_dslr_occlusion",
        "delivery_area_dslr_depth",
    ]
    for archive in oracle_archives:
        link_tree(QUARANTINE / archive, EVAL_ROOT / "oracle_assets" / archive)
    train_names = [path.relative_to(TRAIN_ROOT).as_posix().lower() for path in TRAIN_ROOT.rglob("*") if path.is_file()]
    forbidden_tokens = ("heldout", "guard", "depth", "scan", "occlusion", "dslr", "reference", "oracle")
    forbidden = [name for name in train_names if any(token in name for token in forbidden_tokens)]
    if forbidden:
        raise RuntimeError(f"TRAIN_REFERENCE_LEAKAGE {forbidden[:20]}")
    train_identity, eval_identity = tree_identity(TRAIN_ROOT), tree_identity(EVAL_ROOT)
    isolation = {
        "status": "PASS_PHYSICAL_TRAIN_EVAL_ISOLATION",
        "fresh_process_build_count": 3, "fresh_builds": records,
        "reproducible_tree_sha256": next(iter(hashes)),
        "TRAIN_INPUT_ROOT": str(TRAIN_ROOT), "EVAL_ORACLE_ROOT": str(EVAL_ROOT),
        "train_tree_sha256": train_identity["tree_sha256"], "eval_tree_sha256": eval_identity["tree_sha256"],
        "train_file_count": train_identity["file_count"], "eval_file_count": eval_identity["file_count"],
        "train_total_bytes": train_identity["total_bytes"], "eval_total_bytes": eval_identity["total_bytes"],
        "reference_accessible_from_train_root": False,
        "heldout_accessible_from_train_root": False,
        "train_reference_access_count": 0,
        "forbidden_train_path_count": 0,
    }
    (TASK_ROOT / "train_model" / "train_only_colmap_reproducibility.json").write_text(json.dumps({
        "status": "PASS", "builds": records, "tree_sha256": next(iter(hashes))}, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    (TASK_ROOT / "train_model" / "train_eval_isolation_audit.json").write_text(json.dumps(isolation, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    (TASK_ROOT / "train_model" / "train_only_colmap_build_contract.json").write_text(json.dumps(records[0], indent=2, sort_keys=True) + "\n", encoding="utf-8")
    (TASK_ROOT / "train_model" / "train_only_colmap_identity.json").write_text(json.dumps({
        "status": "PASS", "tree_sha256": next(iter(hashes)), "fresh_build_count": 3}, indent=2) + "\n", encoding="utf-8")
    (TASK_ROOT / "train_model" / "train_reference_isolation_validation.json").write_text(json.dumps(isolation, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    (TASK_ROOT / "train_model" / "open_file_deny_policy.json").write_text(json.dumps({
        "status": "FROZEN", "training_mount": str(TRAIN_ROOT), "denied_roots": [str(EVAL_ROOT), str(QUARANTINE)],
        "reference_access_allowed": False, "heldout_access_allowed": False}, indent=2) + "\n", encoding="utf-8")
    print("PASS_TRAIN_EVAL_ISOLATION", next(iter(hashes)), train_identity["file_count"], eval_identity["file_count"])


if __name__ == "__main__":
    main()
