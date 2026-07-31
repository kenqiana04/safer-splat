#!/usr/bin/env python3
"""Validate all five fixed tail definitions and concentration summaries."""

import argparse
import json
from pathlib import Path


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--record", type=Path, required=True)
    args = parser.parse_args()
    record = json.loads(args.record.read_text(encoding="utf-8"))
    names = {"TAIL_010", "TAIL_050", "TAIL_010_PERCENT", "TAIL_GT_030", "TAIL_GT_050"}
    passed = record.get("status") == "PASS_FIXED_TAIL_REGISTRY" and names.issubset(record) and len(record.get("top20_frames_by_gt_030", [])) == 20
    print("PASS_TAIL_CONCENTRATION_VALIDATION" if passed else "FAIL_TAIL_CONCENTRATION_VALIDATION")
    return 0 if passed else 2


if __name__ == "__main__":
    raise SystemExit(main())
