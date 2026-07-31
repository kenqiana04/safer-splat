#!/usr/bin/env python3
"""Finalize compact V2 split evidence without running mapping or training."""
from __future__ import annotations

import argparse
import json
import subprocess
from pathlib import Path

from arkitscenes_split_v2_common import atomic_json, sha256_file


def main() -> int:
    parser = argparse.ArgumentParser(); parser.add_argument("--task-root", type=Path, required=True); args = parser.parse_args()
    identity = json.loads((args.task_root / "v1_identity" / "frozen_arkitscenes_v1_input_identity.json").read_text(encoding="utf-8")); feasibility = json.loads((args.task_root / "feasibility" / "arkitscenes_v2_reachable_heldout_counts.json").read_text(encoding="utf-8")); split = args.task_root / "v2_split"; contract = json.loads((split / "arkitscenes_spatial_group_split_contract_v2.json").read_text(encoding="utf-8")); validation = json.loads((args.task_root / "validation" / "validation_result.json").read_text(encoding="utf-8")); repro = json.loads((args.task_root / "validation" / "fresh_process_reproducibility.json").read_text(encoding="utf-8"))
    if not (feasibility["status"] == "V2_FEASIBLE" and validation["status"] == "V2_SPLIT_VALIDATION_PASS" and repro["status"] == "FRESH_PROCESS_REPRODUCIBILITY_PASS"): raise SystemExit("FINALIZATION_BLOCKED")
    gpu = subprocess.check_output(["nvidia-smi", "-i", "1", "--query-gpu=index,memory.used,utilization.gpu", "--format=csv,noheader"], text=True).strip()
    final_status = "PASS_ARKITSCENES_SPATIAL_GROUP_SPLIT_V2"; final_decision = "FREEZE_ARKITSCENES_VIDEO_48018874_FOR_SPLATAM_MAPPING"; next_task = "RESUME_ARKITSCENES_SPLATAM_SMOKE_AND_LEARNED_MAP_QUALIFICATION_V1"
    counters = {"new_arkitscenes_downloads": 0, "third_candidate_downloads": 0, "splatam_environment_creation": 0, "smoke": 0, "baseline_training": 0, "variant_training": 0, "checkpoint": False, "gaussian_export": 0, "nvs": 0, "heldout_gaussian_depth_evaluation": 0, "clearance_audit": 0, "safer_g0": 0, "controller_benchmark": 0, "formal_map": False}
    run_manifest = {"task": "REVISE_ARKITSCENES_SPATIAL_GROUP_SPLIT_CONTRACT_V2", "final_status": final_status, "final_decision": final_decision, "only_next_task": next_task, "v1_input_identity_sha256": sha256_file(args.task_root / "v1_identity" / "frozen_arkitscenes_v1_input_identity.json"), "split_identity_sha256": contract["split_identity_sha256"], "validation_status": validation["status"], "fresh_process_status": repro["status"], "counters": counters, "gpu1_final_read_only": gpu, "no_raw_assets_copied": True, "no_training": True}
    atomic_json(args.task_root / "report" / "run_manifest.json", run_manifest)
    handoff = {"status": final_status, "decision": final_decision, "only_next_task": next_task, "selected_scene": "48018874", "selected_scene_role": "ARKITSCENES_V2_SELECTED_MAPPING_SCENE", "immutable_v1_identity_sha256": run_manifest["v1_input_identity_sha256"], "v2_split_identity_sha256": contract["split_identity_sha256"], "prohibited_actions_all_zero": counters}
    atomic_json(args.task_root / "report" / "downstream_handoff.json", handoff)
    report = f"""# ARKitScenes Spatial Group Split Contract V2\n\n`PR67_FORMAL_STATUS=BLOCKED_BY_ARKITSCENES_DATA_OR_COORDINATE_CONTRACT`  \n`SCIENTIFIC_INTERPRETATION=BLOCKED_BY_FIXED_240_60_SPATIAL_GROUP_SPLIT_CONTRACT`\n\nPR #67 remains unchanged. Both fixed candidates previously passed raw asset validation, strict RGB/depth/confidence/intrinsics/pose joining, metric coordinate audit, and the 20/20/20/10 future hard-benchmark precheck. PRIMARY `42899163` remains V2-ineligible because its immutable V1 keyframe count is 173, below 240. BACKUP `48018874` has 267 V1 keyframes. The old 220/50 lower bound needs 270 total frames, and V1's exact-240-then-exact-60 allocation can leave at most 27 after a 240-frame TRAIN subset.\n\nV1 identities were frozen before reconstruction. V1 keyframes and connected components were reconstructed from the immutable joined manifests, with the original timestamp/center/orientation edge contract and original group hash identity. V2 uses complete V1 groups only, target `floor(0.20*N+0.5)={feasibility['target_heldout']}`, hard gates TRAIN>=200 and HELDOUT 40–60, and deterministic subset-sum DP with the prescribed lexicographic tie-break.\n\nSelected result: HELDOUT={contract['heldout_count']}, TRAIN={contract['train_count']}, HELDOUT groups={contract['heldout_group_count']}, TRAIN groups={contract['train_group_count']}. The independent validator found zero frame-index, filename, RGB, depth, confidence, pose-timestamp, and group-hash overlap; zero cross-split group edges; zero discarded/duplicate records; and global score agreement. Three fresh processes reproduced all group trees, selected hashes, manifests, split identity, and validation result.\n\nAll prohibited counters are zero: no new download, third candidate, environment creation, smoke, training, checkpoint, map, Gaussian export, NVS, geometry/clearance evaluation, SAFER G0, or controller benchmark. GPU 1 was read only: `{gpu}`.\n\n## Final\n\n`FINAL_STATUS={final_status}`  \n`FINAL_DECISION={final_decision}`  \n`ONLY_NEXT_TASK={next_task}`\n\nSplit protocol only: no mapping training and no geometry result. This revision does not guarantee later training success.\n"""
    path = args.task_root / "report" / "REPORT_REVISE_ARKITSCENES_SPATIAL_GROUP_SPLIT_CONTRACT_V2.md"; path.write_text(report, encoding="utf-8", newline="\n")
    print(final_status, contract["split_identity_sha256"])
    return 0


if __name__ == "__main__": raise SystemExit(main())
