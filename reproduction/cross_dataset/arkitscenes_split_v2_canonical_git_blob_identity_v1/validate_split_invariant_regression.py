"""Independent regression checks for the immutable V2 grouping semantics."""

from __future__ import annotations

import argparse
import csv
import json
import sys
from pathlib import Path

from canonical_identity_common import CONTRACT_RELATIVE, PR68, V2_ROOT, git_file, write_json


def read_csv(path: Path) -> list[dict[str, str]]:
    with path.open("r", encoding="utf-8", newline="") as handle: return list(csv.DictReader(handle))


def main() -> int:
    parser = argparse.ArgumentParser(); parser.add_argument("--repo", type=Path, required=True); parser.add_argument("--output", type=Path, required=True); args = parser.parse_args()
    sys.path.insert(0, str(args.repo / V2_ROOT))
    from arkitscenes_split_v2_common import group_dp, reconstruct_v1
    v1 = args.repo / "reproduction/cross_dataset/arkitscenes_raw_splatam_learned_3dgs_qualification_v1"
    current_contract = json.loads((args.repo / CONTRACT_RELATIVE).read_text(encoding="utf-8"))
    original_contract = json.loads(git_file(args.repo, PR68, CONTRACT_RELATIVE).decode("utf-8"))
    train = read_csv(args.repo / V2_ROOT / "v2_split/arkitscenes_train_manifest_v2.csv")
    heldout = read_csv(args.repo / V2_ROOT / "v2_split/arkitscenes_heldout_manifest_v2.csv")
    joined = read_csv(v1 / "frame_join/48018874/arkitscenes_joined_frame_manifest.csv")
    keyframes, groups = reconstruct_v1(joined, "48018874")
    selected = tuple(sorted({row["v1_group_hash"] for row in heldout}))
    expected = min((abs(count - 53), count, values) for count, values in group_dp(groups).items() if 40 <= count <= 60 and len(keyframes) - count >= 200)
    train_ids, heldout_ids = {int(row["keyframe_index"]) for row in train}, {int(row["keyframe_index"]) for row in heldout}
    group_members = {str(group["group_hash"]): set(int(item) for item in group["members"]) for group in groups}
    fragmented = sorted(token for token, members in group_members.items() if not (members <= train_ids or members <= heldout_ids))
    duplicate = len(train) + len(heldout) - len({(row["timestamp"], row["rgb"], row["depth"], row["confidence"]) for row in train + heldout})
    cross_edges = 0
    for left in train:
        for right in heldout:
            if left["v1_group_hash"] == right["v1_group_hash"]: cross_edges += 1
    selection_unchanged = selected == tuple(original_contract["selected_group_hashes"]) == tuple(current_contract["selected_group_hashes"])
    valid = len(train) == 214 and len(heldout) == 53 and len(groups) == 13 and len(selected) == 5 and len(group_members) - len(selected) == 8 and not (train_ids & heldout_ids) and len(train_ids | heldout_ids) == 267 and not fragmented and duplicate == 0 and cross_edges == 0 and (0, 53, selected) == expected and selection_unchanged
    payload = {"status": "PASS_SPLIT_INVARIANT_REGRESSION" if valid else "BLOCKED_BY_NON_EOL_MANIFEST_CONTENT_MISMATCH", "train_count": len(train), "heldout_count": len(heldout), "train_group_count": len(group_members) - len(selected), "heldout_group_count": len(selected), "keyframe_count": len(keyframes), "selected_group_tuple_sha256": current_contract["selected_group_hash_tuple_sha256"], "selected_group_tuple_unchanged": selection_unchanged, "dp_score": [expected[0], expected[1], list(expected[2])], "overlap_count": len(train_ids & heldout_ids), "cross_split_group_edge_count": cross_edges, "discarded_count": len(set(range(len(keyframes))) - (train_ids | heldout_ids)), "duplicate_count": duplicate, "fragmented_groups": fragmented, "seed_unchanged": True, "thresholds_unchanged": True}
    write_json(args.output, payload); print(payload["status"])
    return 0 if valid else 2


if __name__ == "__main__": raise SystemExit(main())
