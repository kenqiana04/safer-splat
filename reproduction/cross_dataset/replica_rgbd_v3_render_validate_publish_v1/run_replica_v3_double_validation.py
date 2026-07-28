#!/usr/bin/env python3
"""Run two independent fresh-process complete staging validations."""
from __future__ import annotations

import os
import subprocess
import sys

from _common import ROOT, atomic_json, load_json, tree_sha


def one(label: str) -> dict:
    env = {**os.environ, "PYTHONNOUSERSITE": "1", "PYTHONDONTWRITEBYTECODE": "1"}
    output = ROOT / "full_integrity" / ("validation_pass_" + label + ".json")
    commands = [[sys.executable, str(ROOT / "code" / "validate_replica_v3_full_integrity.py"), "--output", str(output)], [sys.executable, str(ROOT / "code" / "validate_replica_v3_memory_disk_consistency.py")], [sys.executable, str(ROOT / "code" / "validate_replica_v3_pose_identity.py")]]
    results = []
    for command in commands:
        process = subprocess.run(command, env=env, capture_output=True, text=True)
        results.append({"command": command[-1], "returncode": process.returncode})
        if process.returncode: raise RuntimeError("validation_" + label + "_child_failure")
    value = load_json(output)
    return {"status": value["status"], "bad_frames": value["bad_frames"], "rgb_extra": value["rgb_extra"], "depth_extra": value["depth_extra"], "tree_sha256": tree_sha(ROOT / "formal_staging"), "commands": results}


def main() -> None:
    a, b = one("A"), one("B")
    status = "PASS" if a["status"] == b["status"] == "PASS" and a["bad_frames"] == b["bad_frames"] == [] and a["rgb_extra"] == b["rgb_extra"] == [] and a["depth_extra"] == b["depth_extra"] == [] and a["tree_sha256"] == b["tree_sha256"] else "FAIL"
    atomic_json(ROOT / "full_integrity" / "replica_rgbd_v3_double_validation_summary.json", {"status": status, "validation_pass_a": a, "validation_pass_b": b, "a_b_disagreement_count": 0 if status == "PASS" else 1})
    if status != "PASS": raise SystemExit("BLOCKED_BY_REPLICA_RGBD_V3_VALIDATION_NONDETERMINISM")


if __name__ == "__main__": main()
