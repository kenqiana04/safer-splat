#!/usr/bin/env python3
"""Fail-closed validator for the frozen M1 supervision V2 result."""

from __future__ import annotations

import argparse
import json
from pathlib import Path


EXPECTED = {
    "frame_count": 214,
    "m0_positive_pixels": 10518528,
    "m1_valid_pixels": 9277821,
    "supported_frame_count": 210,
    "unsupported_indices": [76, 77, 78, 79],
    "zero_valid_indices": [76, 79],
    "longest_unsupported_run": 4,
}


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("result", type=Path)
    args = parser.parse_args()
    result = json.loads(args.result.read_text(encoding="utf-8"))
    errors: list[str] = []
    if result.get("candidate") != "M1_CONFIDENCE_GE1":
        errors.append("candidate")
    if result.get("group_supported_count_formula") != "S_g >= max(1, ceil(0.80*N_g))":
        errors.append("group_formula")
    for key, expected in EXPECTED.items():
        if result.get("global", {}).get(key) != expected:
            errors.append(f"global.{key}")
    if len(result.get("groups", [])) != 8:
        errors.append("group_count")
    if not result.get("pass") or not all(result.get("gates", {}).values()):
        errors.append("gates")
    if errors:
        print("FAIL_M1_SUPERVISION_V2_VALIDATION", ",".join(errors))
        return 2
    print("PASS_M1_SUPERVISION_V2_VALIDATION")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
