#!/usr/bin/env python3
"""Close the ARKitScenes qualification fail-closed before any SplaTAM training."""
from __future__ import annotations

import argparse
import json
from pathlib import Path

from arkitscenes_common import atomic_json, sha256_file


FINAL_STATUS = "BLOCKED_BY_ARKITSCENES_DATA_OR_COORDINATE_CONTRACT"


def load(path: Path) -> dict[str, object]:
    return json.loads(path.read_text(encoding="utf-8"))


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--task-root", type=Path, required=True)
    args = parser.parse_args()
    task = args.task_root.resolve()
    selection = load(task / "selection" / "arkitscenes_primary_backup_selection.json")
    primary, backup = selection["primary"], selection["backup"]
    if primary is None or backup is None:
        raise RuntimeError("selection evidence unavailable")
    primary_id, backup_id = str(primary["video_id"]), str(backup["video_id"])
    splits = {primary_id: load(task / "frame_split" / primary_id / "arkitscenes_frame_split_contract.json"),
              backup_id: load(task / "frame_split" / backup_id / "arkitscenes_frame_split_contract.json")}
    if any(split["status"] != FINAL_STATUS for split in splits.values()):
        raise RuntimeError("refusing blocked closeout without both recorded split-gate failures")
    authority = load(task / "authority" / "arkitscenes_authority_identity.json")
    splatam = load(task / "authority" / "splatam_authority_identity.json")
    registry = task / "metadata" / "arkitscenes_candidate_registry.json"
    manifests = [task / "download" / f"arkitscenes_download_manifest_{video_id}.json" for video_id in (primary_id, backup_id)]
    result = {
        "final_status": FINAL_STATUS,
        "final_decision": "STOP_BEFORE_SPLATAM_TRAINING_WITHOUT_RELAXING_FROZEN_SPLIT_CONTRACT",
        "training_count": 0,
        "smoke_count": 0,
        "controller_benchmark_count": 0,
        "checkpoint_exists": False,
        "formal_map_exists": False,
        "primary": primary,
        "backup": backup,
        "split_failures": splits,
        "no_third_candidate_downloaded": True,
        "no_group_splitting": True,
        "no_threshold_relaxation": True,
        "no_icp_sim3_scale_repair": True,
        "no_splatam_environment_created": True,
        "no_splatam_training_started": True,
        "candidate_registry_sha256": sha256_file(registry),
        "download_manifest_sha256": {path.name: sha256_file(path) for path in manifests},
    }
    atomic_json(task / "run_manifest.json", result)
    validation = {
        "status": FINAL_STATUS,
        "passed_before_split": ["official_access", "authority_freeze", "candidate_selection", "raw_asset_validation", "RGB-D-pose join", "metric_coordinate_audit", "future_hard_benchmark_geometry_precheck"],
        "failed_gate": "frozen spatial group split",
        "primary_keyframes_train_heldout": [splits[primary_id]["keyframe_count"], splits[primary_id]["train_count"], splits[primary_id]["heldout_count"]],
        "backup_keyframes_train_heldout": [splits[backup_id]["keyframe_count"], splits[backup_id]["train_count"], splits[backup_id]["heldout_count"]],
        "critical_evidence_unresolved": "Neither pre-frozen candidate can form the required >=220 TRAIN and >=50 HELDOUT disjoint spatial-group split.",
    }
    atomic_json(task / "validation_result.json", validation)
    atomic_json(task / "downstream_handoff.json", {
        "status": FINAL_STATUS,
        "hard_benchmark_handoff_created": False,
        "reason": "No learned map exists because the frozen split gate failed before smoke or baseline.",
        "automatic_next_task": None,
        "requires_explicit_new_authorization": True,
    })
    report = task / "report" / "REPORT_ARKITSCENES_RAW_SPLATAM_LEARNED_3DGS_QUALIFICATION_V1.md"
    report.parent.mkdir(parents=True, exist_ok=True)
    content = f"""# ARKitScenes raw SplaTAM learned-3DGS qualification V1

`FINAL_STATUS={FINAL_STATUS}`

## Decision

The task stopped before creating an independent SplaTAM environment, smoke, baseline, checkpoint, canonical map, rendering, clearance audit, G0, or controller benchmark. The frozen spatial-group split gate failed for both pre-frozen candidates; no threshold, group, pose, scale, or mapping parameter was changed.

## Authority and access

- Apple ARKitScenes commit: `{authority['commit']}`
- Official download script SHA-256: `{authority['download_data_py_sha256']}`
- Official SplaTAM commit: `{splatam['commit']}`
- Access preflight passed through the task wrapper.
- FARO-to-ARKit join remains not authorized; FARO download count is zero.

## Deterministic candidates

- PRIMARY: visit `{primary['visit_id']}`, video `{primary_id}`, hash `{primary['candidate_hash']}`.
- BACKUP: visit `{backup['visit_id']}`, video `{backup_id}`, hash `{backup['candidate_hash']}`.
- Both completed official raw-asset validation, strict RGB-D-confidence-intrinsics-pose joins, metric depth-to-mesh coordinate audits, and future hard-benchmark geometry prechecks.
- No third candidate was downloaded.

## Blocking split evidence

- PRIMARY: {splits[primary_id]['keyframe_count']} keyframes; TRAIN={splits[primary_id]['train_count']}; HELDOUT={splits[primary_id]['heldout_count']}; status `{splits[primary_id]['status']}`.
- BACKUP: {splits[backup_id]['keyframe_count']} keyframes; TRAIN={splits[backup_id]['train_count']}; HELDOUT={splits[backup_id]['heldout_count']}; status `{splits[backup_id]['status']}`.
- The contract requires an exact 240/60 split when possible, otherwise at least 220/50, with no group splitting. Neither candidate meets the minimum.

## Boundaries preserved

- training=0; smoke=0; controller benchmark=0; checkpoint=false; formal map=false.
- No ICP, Sim3, pose-scale fitting, threshold relaxation, group splitting, or third-candidate fallback was performed.
- No ARKitScenes learned-map qualification or downstream hard-benchmark handoff was created.

## Required next action

No automatic next task is authorized. Any reconsideration of the split contract or candidate-selection protocol requires separate explicit authorization.
"""
    report.write_text(content, encoding="utf-8")
    print(FINAL_STATUS)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
