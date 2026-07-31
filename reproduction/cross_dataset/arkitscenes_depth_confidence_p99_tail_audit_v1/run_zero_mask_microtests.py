#!/usr/bin/env python3
"""Forward-only synthetic tests of the exact official SplaTAM mask reductions."""

from __future__ import annotations

import argparse
from pathlib import Path

import torch

from audit_common import write_json


def evaluate(name: str, depth: torch.Tensor) -> dict[str, object]:
    rendered = torch.full_like(depth, 0.75)
    uncertainty = torch.zeros_like(depth)
    nan_mask = (~torch.isnan(rendered)) & (~torch.isnan(uncertainty))
    mask = (depth > 0) & nan_mask
    absolute = torch.abs(depth - rendered)[mask]
    tracking_sum = absolute.sum()
    mapping_mean = absolute.mean()
    rgb_loss = torch.tensor(0.25, dtype=torch.float64)
    return {
        "case": name,
        "valid_depth_count": int(mask.sum()),
        "tracking_depth_sum": float(tracking_sum),
        "tracking_depth_sum_finite": bool(torch.isfinite(tracking_sum)),
        "mapping_depth_mean": float(mapping_mean) if torch.isfinite(mapping_mean) else None,
        "mapping_depth_mean_finite": bool(torch.isfinite(mapping_mean)),
        "rgb_loss_independently_finite": bool(torch.isfinite(rgb_loss)),
    }


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    zero = torch.zeros((1, 4, 4), dtype=torch.float64)
    one = zero.clone()
    one[0, 1, 1] = 1.0
    sparse = zero.clone()
    sparse[0, 0, 0] = 0.5
    sparse[0, 2, 3] = 1.5
    results = [evaluate("all_zero_depth_mask", zero), evaluate("one_valid_pixel", one), evaluate("sparse_valid_mask", sparse)]
    payload = {
        "status": "FAIL_ZERO_MASK_MAPPING_DEPTH_MEAN_NONFINITE",
        "case_count": len(results),
        "cases": results,
        "optimizer_created": False,
        "backward_called": False,
        "parameters_updated": False,
        "checkpoint_created": False,
        "mapper_loop_executed": False,
        "real_scene_data_used": False,
        "contract": "official get_loss uses sum for tracking and mean for non-tracking mapping over mask=(depth>0)&nan_mask",
    }
    if all(case["mapping_depth_mean_finite"] for case in results):
        payload["status"] = "PASS_ZERO_MASK_FORWARD_REDUCTION_FINITE"
    write_json(args.output, payload)
    print(payload["status"])
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
