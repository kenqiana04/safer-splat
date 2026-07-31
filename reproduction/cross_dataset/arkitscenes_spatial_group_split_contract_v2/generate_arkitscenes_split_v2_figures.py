#!/usr/bin/env python3
"""Generate compact split-protocol-only figures from compact manifests."""
from __future__ import annotations

import argparse
import json
from pathlib import Path

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np

from arkitscenes_split_v2_common import read_csv

FOOTER = "split protocol only | no mapping training | no geometry result"


def save(path: Path, title: str) -> None:
    plt.title(title); plt.figtext(0.5, 0.01, FOOTER, ha="center", fontsize=8); plt.tight_layout(rect=(0, 0.04, 1, 1)); plt.savefig(path, dpi=160); plt.close()


def main() -> int:
    parser = argparse.ArgumentParser(); parser.add_argument("--task-root", type=Path, required=True); args = parser.parse_args(); out = args.task_root / "figures"; out.mkdir(parents=True, exist_ok=True)
    feasible = json.loads((args.task_root / "feasibility" / "arkitscenes_v2_reachable_heldout_counts.json").read_text(encoding="utf-8")); registry = json.loads((args.task_root / "group_reconstruction" / "48018874" / "arkitscenes_v1_group_registry.json").read_text(encoding="utf-8")); split = args.task_root / "v2_split"; train, held = read_csv(split / "arkitscenes_train_manifest_v2.csv"), read_csv(split / "arkitscenes_heldout_manifest_v2.csv")
    plt.figure(figsize=(6,3)); plt.bar(["PRIMARY", "BACKUP", "V1 minimum"], [173,267,270], color=["#c44e52","#4c72b0","#777777"]); plt.ylabel("keyframes"); save(out / "v1_split_failure_arithmetic.png", "V1 arithmetic: 220 + 50 requires 270")
    plt.figure(figsize=(6,3)); plt.bar(["42899163", "48018874"], [173,267], color=["#c44e52","#4c72b0"]); plt.axhline(240, color="black", linestyle="--"); plt.ylabel("V1 keyframes"); save(out / "primary_backup_keyframe_counts.png", "Immutable V1 keyframe counts")
    sizes=[len(group["members"]) for group in registry["groups"]]; plt.figure(figsize=(6,3)); plt.bar(range(1,len(sizes)+1), sizes); plt.xlabel("group in V1 hash order"); plt.ylabel("members"); save(out / "backup_group_size_distribution.png", "BACKUP complete V1 group sizes")
    counts=feasible["reachable_counts_0_to_n"]; plt.figure(figsize=(7,3)); plt.scatter(counts,[1]*len(counts),s=12); plt.axvspan(40,60,color="#55a868",alpha=.2); plt.axvline(feasible["target_heldout"],color="#c44e52"); plt.yticks([]); plt.xlabel("reachable complete-group heldout count"); save(out / "reachable_heldout_counts_v2.png", "V2 reachable heldout counts")
    plt.figure(figsize=(6,3)); plt.bar(["V1 heldout", "V2 heldout", "V2 train"],[0,len(held),len(train)],color=["#c44e52","#55a868","#4c72b0"]); plt.ylabel("keyframes"); save(out / "v1_vs_v2_allocation.png", "Fixed V1 versus proportionate V2 allocation")
    centers=lambda rows: np.asarray([[float(r["c2w_03"]),float(r["c2w_13"]),float(r["c2w_23"])] for r in rows]); t,h=centers(train),centers(held); plt.figure(figsize=(5,4)); plt.scatter(t[:,0],t[:,2],s=9,label="TRAIN"); plt.scatter(h[:,0],h[:,2],s=14,label="HELDOUT"); plt.legend(); plt.xlabel("x m");plt.ylabel("z m");save(out / "v2_train_heldout_pose_distribution.png", "V2 pose distribution")
    assignments=["HELDOUT" if g["group_hash"] in set(feasible["selected"]["selected_group_hashes"]) else "TRAIN" for g in registry["groups"]]; plt.figure(figsize=(7,3)); plt.bar(range(len(sizes)),sizes,color=["#55a868" if x=="HELDOUT" else "#4c72b0" for x in assignments]);plt.xlabel("V1 group hash order");plt.ylabel("members");save(out / "v2_group_assignment.png", "Complete V1 group assignment")
    plt.figure(figsize=(7,2.6)); plt.axis("off"); plt.text(.02,.70,"Allowed: deterministic pre-training group allocation\nNot claimed: mapping, learned map, geometry, SAFER, controller results",fontsize=12);save(out / "v2_split_claim_boundary.png", "V2 claim boundary")
    print("FIGURES_PASS", len(list(out.glob("*.png"))))
    return 0


if __name__ == "__main__": raise SystemExit(main())
