#!/usr/bin/env python3
"""Run reconstruction, feasibility, allocation, and validation in three fresh interpreters."""
from __future__ import annotations

import argparse
import json
import subprocess
import sys
from pathlib import Path

from arkitscenes_split_v2_common import atomic_json, sha256_file


def run(command: list[str]) -> None:
    result = subprocess.run(command, check=False, capture_output=True, text=True)
    if result.returncode != 0:
        raise SystemExit(f"FRESH_PROCESS_FAILURE: {' '.join(command)}\n{result.stdout}\n{result.stderr}")


def snapshot(root: Path) -> dict[str, object]:
    split = root / "v2_split"; validation = root / "validation" / "validation_result.json"
    contract = json.loads((split / "arkitscenes_spatial_group_split_contract_v2.json").read_text(encoding="utf-8"))
    return {"selected_scene": "48018874", "selected_group_hashes": contract["selected_group_hashes"], "train_manifest_sha256": sha256_file(split / "arkitscenes_train_manifest_v2.csv"), "heldout_manifest_sha256": sha256_file(split / "arkitscenes_heldout_manifest_v2.csv"), "split_identity_sha256": contract["split_identity_sha256"], "validation_sha256": sha256_file(validation), "validation_status": json.loads(validation.read_text(encoding="utf-8"))["status"], "group_tree_primary": json.loads((root / "group_reconstruction" / "42899163" / "reconstruction_validation.json").read_text(encoding="utf-8"))["registry_tree_sha256"], "group_tree_backup": json.loads((root / "group_reconstruction" / "48018874" / "reconstruction_validation.json").read_text(encoding="utf-8"))["registry_tree_sha256"]}


def main() -> int:
    parser = argparse.ArgumentParser(); parser.add_argument("--task-root", type=Path, required=True); parser.add_argument("--v1-root", type=Path, required=True); parser.add_argument("--script-root", type=Path, required=True); args = parser.parse_args()
    python = sys.executable; records = []
    for run_index in range(3):
        run([python, "-B", str(args.script_root / "reconstruct_arkitscenes_v1_group_registry.py"), "--task-root", str(args.task_root), "--v1-root", str(args.v1_root), "--video-id", "42899163"])
        run([python, "-B", str(args.script_root / "reconstruct_arkitscenes_v1_group_registry.py"), "--task-root", str(args.task_root), "--v1-root", str(args.v1_root), "--video-id", "48018874"])
        run([python, "-B", str(args.script_root / "analyze_arkitscenes_v2_split_feasibility.py"), "--task-root", str(args.task_root)])
        run([python, "-B", str(args.script_root / "freeze_arkitscenes_spatial_group_split_v2.py"), "--task-root", str(args.task_root), "--v1-root", str(args.v1_root)])
        run([python, "-B", str(args.script_root / "validate_arkitscenes_spatial_group_split_v2.py"), "--task-root", str(args.task_root), "--v1-root", str(args.v1_root)])
        records.append(snapshot(args.task_root) | {"fresh_process_run": run_index + 1})
    deterministic = records[0] == {key: value for key, value in records[1].items() if key != "fresh_process_run"} | {"fresh_process_run": 1} and records[0] == {key: value for key, value in records[2].items() if key != "fresh_process_run"} | {"fresh_process_run": 1}
    output = {"status": "FRESH_PROCESS_REPRODUCIBILITY_PASS" if deterministic else "FRESH_PROCESS_REPRODUCIBILITY_FAIL", "runs": records, "random_calls": 0}
    atomic_json(args.task_root / "validation" / "fresh_process_reproducibility.json", output)
    if not deterministic: raise SystemExit(output["status"])
    print(output["status"])
    return 0


if __name__ == "__main__": raise SystemExit(main())
