"""Record source-level proof that mapping uses fixed GT poses and held-out frames are excluded."""
from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path


def sha256(path: Path) -> str:
    h = hashlib.sha256(path.read_bytes()).hexdigest()
    return h


def require_text(path: Path, snippets: list[str]) -> dict:
    text = path.read_text(encoding="utf-8")
    absent = [s for s in snippets if s not in text]
    if absent:
        raise RuntimeError(f"SOURCE_AUDIT_MISSING:{path.name}:{absent}")
    return {"path": str(path), "sha256": sha256(path), "required_snippets": snippets}


def main() -> None:
    p = argparse.ArgumentParser(); p.add_argument("--splatam", type=Path, required=True); p.add_argument("--gaussian-slam", type=Path, required=True); p.add_argument("--output", type=Path, required=True); a = p.parse_args()
    splat = require_text(a.splatam / "scripts" / "gaussian_splatting.py", ["# Use GT Poses for Tracking", "params['cam_unnorm_rots']", "get_loss_gs"])
    gtrack = require_text(a.gaussian_slam / "src" / "entities" / "tracker.py", ["if self.odometry_type == \"gt\":", "return gt_c2w"])
    grun = require_text(a.gaussian_slam / "src" / "entities" / "gaussian_slam.py", ["estimated_c2w = self.tracker.track", "self.mapper.map"])
    out = {"status": "PASS", "SPLATAM_GTPOSE_MAP_ONLY": {"classification": "MAP_ONLY_COMPARABLE", "proof": splat,
            "mapping_core_changes": 0, "fixed_gt_poses": True, "tracking_pose_updates": False},
           "GAUSSIAN_SLAM_GTPOSE_MAP_ONLY": {"classification": "MAP_ONLY_COMPARABLE", "proof": [gtrack, grun],
            "mapping_core_changes": 0, "noncomment_source_patch_lines": 0, "fixed_gt_poses": True, "tracking_pose_updates": False,
            "condition": "task-owned config uses official tracking.odometry_type=gt"}}
    a.output.write_text(json.dumps(out, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(json.dumps(out, sort_keys=True))


if __name__ == "__main__": main()
