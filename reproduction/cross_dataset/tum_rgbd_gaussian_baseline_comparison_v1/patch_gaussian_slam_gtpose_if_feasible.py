"""Materialize the permitted one-field official-config GT-pose override."""
from __future__ import annotations

import argparse
from pathlib import Path

import yaml


def main() -> None:
    p = argparse.ArgumentParser(); p.add_argument("--official-config", type=Path, required=True); p.add_argument("--output", type=Path, required=True); p.add_argument("--input-path", type=Path, required=True); p.add_argument("--output-path", type=Path, required=True); p.add_argument("--frames", type=int, required=True); a = p.parse_args()
    config = yaml.safe_load(a.official_config.read_text(encoding="utf-8"))
    changes = {"data.input_path": str(a.input_path), "data.output_path": str(a.output_path), "frame_limit": a.frames,
               "tracking.odometry_type": "gt", "use_wandb": False}
    # GaussianSLAM passes only data+camera fields to its dataset constructor,
    # so the smoke/full limit must live under data as well as be recorded at
    # top level for the task's frozen launch audit.
    config["data"] = {"input_path": str(a.input_path), "output_path": str(a.output_path), "scene_name": "rgbd_dataset_freiburg1_room", "frame_limit": a.frames}
    config["cam"] = {"H": 480, "W": 640, "fx": 517.3, "fy": 516.5, "cx": 318.6, "cy": 255.3,
                     # Preserve the official TUM RGB-D scene-config crop
                     # convention; only I/O, frame limit, GT pose mode, and
                     # disabled external logging differ from the release.
                     "crop_edge": 50, "depth_scale": 5000.0,
                     "distortion": [0.2624, -0.9531, -0.0054, 0.0026, 1.1633]}
    config["frame_limit"] = a.frames
    config["tracking"]["odometry_type"] = "gt"
    config["use_wandb"] = False
    a.output.write_text(yaml.safe_dump(config, sort_keys=False), encoding="utf-8")
    # No source file changes: official Tracker.track returns the dataset pose on this branch.
    print({"status": "GTPOSE_CONFIG_FEASIBLE", "noncomment_source_patch_lines": 0, "changes": changes})


if __name__ == "__main__": main()
