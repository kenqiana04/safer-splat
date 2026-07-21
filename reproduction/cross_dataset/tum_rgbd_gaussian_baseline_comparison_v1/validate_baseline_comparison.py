"""Fail-closed final validator for the compact baseline-comparison evidence."""
from __future__ import annotations

import argparse
import json
from pathlib import Path


def load(path: Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8"))


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--frames", type=Path, required=True)
    parser.add_argument("--comparability", type=Path, required=True)
    parser.add_argument("--splatam", type=Path, required=True)
    parser.add_argument("--gaussian-slam", type=Path, required=True)
    parser.add_argument("--adapter", type=Path, required=True)
    parser.add_argument("--static", type=Path, required=True)
    parser.add_argument("--gate", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    frames, comparability, splat, gslam, adapter, static, gate = (load(path) for path in (args.frames, args.comparability, args.splatam, args.gaussian_slam, args.adapter, args.static, args.gate))
    checks = {
        "frame_registry": frames.get("status") == "PASS" and frames.get("train_count") == 240 and frames.get("eval_count") == 60 and frames.get("split_disjoint") and frames.get("split_exhaustive"),
        "protocol": all(comparability[name].get("classification") == "MAP_ONLY_COMPARABLE" and comparability[name].get("mapping_core_changes", 0) == 0 for name in ("SPLATAM_GTPOSE_MAP_ONLY", "GAUSSIAN_SLAM_GTPOSE_MAP_ONLY")),
        "splatam_native_eval": splat.get("status") == "PASS" and splat.get("frame_count") == 60 and not splat.get("sim3") and not splat.get("scale_fitting") and not splat.get("per_frame_alignment"),
        "gaussian_slam_native_eval": gslam.get("status") == "PASS" and gslam.get("frame_count") == 60 and gslam.get("gaussian_count", 0) > 0 and not gslam.get("sim3") and not gslam.get("scale_fitting") and not gslam.get("per_frame_alignment"),
        "adapter_fail_closed": adapter.get("status") == "COMMON_ADAPTER_UNRESOLVED",
        "static_not_run": static.get("status") == "NOT_RUN_COMMON_ADAPTER_UNRESOLVED" and not any(static[key] for key in ("controller", "dynamics", "qp", "trajectory", "navigation", "G1")),
        "boundary": gate.get("threshold_delta1") == 0.75 and not gate.get("threshold_changed") and not gate.get("formal_training") and not gate.get("navigation") and not gate.get("SAFER_rollout") and not gate.get("G1"),
    }
    result = {"status": "PASS" if all(checks.values()) else "FAIL", "checks": checks,
              "no_formal_training": True, "no_navigation": True, "no_SAFER_rollout": True, "no_G1": True}
    args.output.write_text(json.dumps(result, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(json.dumps(result, sort_keys=True))
    if result["status"] != "PASS":
        raise RuntimeError("BASELINE_COMPARISON_VALIDATION_FAILED")


if __name__ == "__main__":
    main()
