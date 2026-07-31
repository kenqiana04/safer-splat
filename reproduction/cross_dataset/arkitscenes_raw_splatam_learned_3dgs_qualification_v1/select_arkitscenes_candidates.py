#!/usr/bin/env python3
"""Freeze the complete deterministic Training candidate order before download."""
from __future__ import annotations

import argparse
import csv
import hashlib
from pathlib import Path

from arkitscenes_common import atomic_json, sha256_file


def rank(visit_id: str, video_id: str) -> str:
    value = f"ARKITSCENES_RAW_CANDIDATE_V1:{visit_id}:{video_id}".encode("utf-8")
    return hashlib.sha256(value).hexdigest()


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--splits", type=Path, required=True)
    parser.add_argument("--task-root", type=Path, required=True)
    args = parser.parse_args()
    rows: list[dict[str, str]] = []
    with args.splits.open(newline="", encoding="utf-8") as handle:
        for row in csv.DictReader(handle):
            if row["fold"] == "Training":
                rows.append({"video_id": row["video_id"], "visit_id": row["visit_id"], "candidate_hash": rank(row["visit_id"], row["video_id"])})
    rows.sort(key=lambda row: (row["candidate_hash"], row["video_id"]))
    atomic_json(args.task_root / "metadata" / "arkitscenes_candidate_registry.json", {
        "selection_contract": "SHA-256(ARKITSCENES_RAW_CANDIDATE_V1:{visit_id}:{video_id}) ascending Training fold",
        "splits_sha256": sha256_file(args.splits),
        "max_complete_candidate_downloads": 3,
        "candidates": rows,
        "primary": None,
        "backup": None,
    })
    print(f"CANDIDATE_REGISTRY_PASS training_candidates={len(rows)} first_video={rows[0]['video_id']}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
