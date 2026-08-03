#!/usr/bin/env python3
"""Validate one frozen SplaTAM mapper run without modifying its parameters."""

from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path
from typing import Any

import numpy as np


def sha(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def finite(array: np.ndarray) -> bool:
    return bool(np.isfinite(array).all())


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--output-dir", type=Path, required=True)
    parser.add_argument("--events", type=Path, required=True)
    parser.add_argument("--log", type=Path, required=True)
    parser.add_argument("--first-index", type=int, required=True)
    parser.add_argument("--frame-count", type=int, required=True)
    parser.add_argument("--zero-indices", default="")
    parser.add_argument("--result", type=Path, required=True)
    parser.add_argument("--kind", choices=("smoke", "formal"), required=True)
    args = parser.parse_args()
    params_path = args.output_dir / "params.npz"
    expected_frames = list(range(args.first_index, args.first_index + args.frame_count))
    expected_zero = sorted(int(x) for x in args.zero_indices.split(",") if x)
    records = [json.loads(line) for line in args.events.read_text(encoding="utf-8").splitlines() if line.strip()]
    frames = [row for row in records if row.get("kind") == "frame"]
    losses = [row for row in records if row.get("kind") == "loss"]
    frame_by_index = {int(row["frame_index"]): row for row in frames}
    zero_rows = [row for row in frames if row["depth_event"] == "EMPTY_DEPTH_SAFE_SKIP_DEPTH_INITIALIZATION"]
    loss_zero = [row for row in losses if int(row["frame_index"]) in expected_zero]
    log_text = args.log.read_text(encoding="utf-8", errors="replace")
    with np.load(params_path, allow_pickle=True) as archive:
        arrays = {key: archive[key] for key in archive.files}
    required = ["means3D", "rgb_colors", "unnorm_rotations", "logit_opacities", "log_scales"]
    count = int(arrays["means3D"].shape[0]) if "means3D" in arrays else 0
    gates = {
        "params_exists": params_path.is_file(),
        "required_arrays": all(key in arrays for key in required),
        "gaussian_count_positive": count > 0,
        "all_parameter_arrays_finite": all(finite(arrays[key]) for key in required),
        "frame_events_complete": sorted(frame_by_index) == expected_frames,
        "zero_events_exact": sorted(int(row["frame_index"]) for row in zero_rows) == expected_zero,
        "zero_added_count_exact": all(int(row["added_count"]) == 0 and int(row["valid_depth_count"]) == 0 for row in zero_rows),
        "nonempty_events_valid": all(int(row["valid_depth_count"]) > 0 for row in frames if int(row["frame_index"]) not in expected_zero),
        "losses_present": len(losses) == 7000,
        "losses_finite": all(np.isfinite(float(row["rgb_loss"])) and np.isfinite(float(row["depth_loss"])) for row in losses),
        "zero_depth_losses_exact": all(float(row["depth_loss"]) == 0.0 and np.isfinite(float(row["rgb_loss"])) for row in loss_zero),
        "zero_frames_sampled_by_optimizer": not expected_zero or sorted({int(row["frame_index"]) for row in loss_zero}) == expected_zero,
        "official_render_eval_completed": all(token in log_text for token in ("Average PSNR:", "Average MS-SSIM:", "Average LPIPS:")),
        "official_render_plots_complete": len(list((args.output_dir / "eval" / "plots").glob("*.png"))) == args.frame_count,
    }
    passed = all(gates.values())
    result: dict[str, Any] = {
        "status": ("PASS_" + args.kind.upper() + "_MAPPER_RUN") if passed else ("FAIL_" + args.kind.upper() + "_MAPPER_RUN"),
        "pass": passed,
        "gates": gates,
        "output_dir": str(args.output_dir),
        "params_sha256": sha(params_path),
        "params_size": params_path.stat().st_size,
        "gaussian_count": count,
        "frame_event_count": len(frames),
        "loss_event_count": len(losses),
        "zero_indices": expected_zero,
        "zero_loss_observation_count": len(loss_zero),
        "checkpoint": False,
    }
    args.result.parent.mkdir(parents=True, exist_ok=True)
    args.result.write_text(json.dumps(result, indent=2, sort_keys=True) + "\n", encoding="utf-8", newline="\n")
    print(result["status"])
    if not passed:
        raise SystemExit(2)


if __name__ == "__main__":
    main()
