#!/usr/bin/env python3
"""Enumerate V2 complete-group heldout counts without writing a split."""
from __future__ import annotations

import argparse
import json
import math
from pathlib import Path

from arkitscenes_split_v2_common import atomic_json, group_dp, sha256_file


def main() -> int:
    parser = argparse.ArgumentParser(); parser.add_argument("--task-root", type=Path, required=True); args = parser.parse_args()
    group_path = args.task_root / "group_reconstruction" / "48018874" / "arkitscenes_v1_group_registry.json"
    registry = json.loads(group_path.read_text(encoding="utf-8")); groups = registry["groups"]; n = int(registry["keyframe_count"])
    states = group_dp(groups)
    target = math.floor(0.20 * n + 0.5)
    feasible = [{"heldout_count": count, "train_count": n-count, "selected_group_hashes": list(states[count])} for count in sorted(states) if 40 <= count <= 60 and n-count >= 200]
    selected = min(feasible, key=lambda item: (abs(item["heldout_count"] - target), item["heldout_count"], tuple(item["selected_group_hashes"]))) if feasible else None
    v1_train = states.get(240)
    remaining = [group for group in groups if not v1_train or str(group["group_hash"]) not in set(v1_train)]
    v1_heldout_after_train = group_dp(remaining).get(60) if v1_train else None
    reachable = {str(count): list(states[count]) for count in sorted(states)}
    output = {"status": "V2_FEASIBLE" if selected else "NO_FEASIBLE_V2_SPLIT_FOR_EXISTING_ARKITSCENES_CANDIDATES", "video_id": "48018874", "n_keyframes": n, "target_heldout": target, "target_formula": "floor(0.20*N+0.5)", "group_count": len(groups), "group_sizes_hash_order": [len(group["members"]) for group in groups], "reachable_counts_0_to_n": sorted(states), "reachable_count_to_lexicographically_smallest_group_hash_tuple": reachable, "feasible_counts_40_to_60_train_ge_200": feasible, "selected": selected, "hard_constraints": {"heldout_min": 40, "heldout_max": 60, "train_min": 200, "complete_v1_groups_only": True, "all_frames_assigned_once": True}, "group_registry_sha256": sha256_file(group_path), "random_calls": 0}
    feasibility = {"v1_exact_train_240_reachable": v1_train is not None, "v1_exact_train_240_group_hashes": list(v1_train) if v1_train else [], "v1_remaining_exact_heldout_60_reachable": v1_heldout_after_train is not None, "v1_minimum_220_50_total_feasible": n >= 270, "primary_42899163_v2_eligibility": "V2_INELIGIBLE_KEYFRAME_COUNT_LT_240", "backup_48018874_v2_feasible": selected is not None, "block_category": "ARITHMETIC_AND_FIXED_240_60_ALLOCATION_ORDER", "no_candidate_reselection": True}
    atomic_json(args.task_root / "feasibility" / "arkitscenes_v2_reachable_heldout_counts.json", output)
    atomic_json(args.task_root / "feasibility" / "arkitscenes_v1_vs_v2_feasibility.json", feasibility)
    print(output["status"], f"target={target}", f"selected={None if selected is None else selected['heldout_count']}")
    return 0 if selected else 2


if __name__ == "__main__": raise SystemExit(main())
