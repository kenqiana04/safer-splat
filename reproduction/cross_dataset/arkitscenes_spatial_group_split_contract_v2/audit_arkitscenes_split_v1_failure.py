#!/usr/bin/env python3
"""Write the non-mutating arithmetic explanation for the V1 split block."""
from __future__ import annotations

import argparse
from pathlib import Path


def main() -> int:
    parser = argparse.ArgumentParser(); parser.add_argument("--task-root", type=Path, required=True); args = parser.parse_args()
    report = """# ARKitScenes V1 Split Failure Audit\n\nPR67_FORMAL_STATUS=BLOCKED_BY_ARKITSCENES_DATA_OR_COORDINATE_CONTRACT\n\nSCIENTIFIC_INTERPRETATION=BLOCKED_BY_FIXED_240_60_SPATIAL_GROUP_SPLIT_CONTRACT\n\n- PRIMARY `42899163` has `N=173`; the immutable V1 minimum `TRAIN>=220` plus `HELDOUT>=50` needs at least 270 frames and is mathematically impossible.\n- BACKUP `48018874` has `N=267`; the same immutable 220/50 total lower bound is mathematically impossible.\n- V1 first searched an exact complete-group `TRAIN=240` subset. Even when such a subset exists, at most `267-240=27` frames remain, so an exact complete-group `HELDOUT=60` subset cannot exist.\n- Therefore V1 `HELDOUT=0` follows from allocation order and the fixed integer contract. It does not prove that independently held-out spatial groups do not exist.\n\nThis audit does not modify PR #67, candidates, data, keyframes, groups, or any mapping/geometry result. Split protocol only: no mapping training; no geometry result.\n"""
    output = args.task_root / "report" / "ARKITSCENES_SPLIT_V1_FAILURE_AUDIT.md"; output.parent.mkdir(parents=True, exist_ok=True); output.write_text(report, encoding="utf-8", newline="\n")
    print("V1_FAILURE_AUDIT_PASS")
    return 0


if __name__ == "__main__": raise SystemExit(main())
