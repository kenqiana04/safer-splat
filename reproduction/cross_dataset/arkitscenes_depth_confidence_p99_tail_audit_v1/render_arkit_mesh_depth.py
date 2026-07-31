#!/usr/bin/env python3
"""Validate the recorded official-mesh camera-z rendering contract."""

import argparse
import json
from pathlib import Path


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--record", type=Path, required=True)
    args = parser.parse_args()
    record = json.loads(args.record.read_text(encoding="utf-8"))
    passed = record["status"] == "PASS_OFFICIAL_MESH_CAMERA_Z_RENDER_CONTRACT" and record["sanity_frame_count"] >= 16 and record["all_sanity_positive"]
    print("PASS_MESH_CAMERA_Z_RENDER_VALIDATION" if passed else "FAIL_MESH_CAMERA_Z_RENDER_VALIDATION")
    return 0 if passed else 2


if __name__ == "__main__":
    raise SystemExit(main())
