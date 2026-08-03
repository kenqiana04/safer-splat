#!/usr/bin/env python3
"""Synthetic value/gradient qualification for the empty-depth compatibility layer."""

from __future__ import annotations

import argparse
import json
import math
import sys
from pathlib import Path
from typing import Any

import torch

from empty_depth_safe_splatam_compat import compute_mapping_losses_empty_depth_safe


SEED = 20260730
FIXTURE_COUNT = 120
LOSS_WEIGHTS = {"depth": 0.0, "im": 1.0}


def write_json(path: Path, value: Any) -> None:
    path.write_text(json.dumps(value, indent=2, sort_keys=True) + "\n", encoding="utf-8", newline="\n")


def load_official(repo: Path):
    sys.path.insert(0, str(repo))
    import scripts.splatam as official  # type: ignore
    return official


def rgb_loss_fn(official):
    def loss(predicted: torch.Tensor, target: torch.Tensor) -> torch.Tensor:
        return 0.8 * official.l1_loss_v1(predicted, target) + 0.2 * (1.0 - official.calc_ssim(predicted, target))
    return loss


def run_nonempty(official) -> dict[str, Any]:
    generator = torch.Generator(device="cpu")
    generator.manual_seed(SEED)
    max_value_diff = {"float32": 0.0, "float64": 0.0}
    max_total_diff = {"float32": 0.0, "float64": 0.0}
    max_gradient_diff = {"float32": 0.0, "float64": 0.0}
    max_invalid_gradient = {"float32": 0.0, "float64": 0.0}
    nonfinite = 0
    valid_count_classes: set[str] = set()
    fixture_rows: list[dict[str, Any]] = []
    for fixture in range(FIXTURE_COUNT):
        dtype = torch.float64 if fixture % 2 else torch.float32
        dtype_name = str(dtype).split(".")[-1]
        size = 64
        category = fixture % 5
        valid_count = [1, 2, 7, 31, 64][category]
        valid_count_classes.add(["one", "two", "sparse", "medium", "all"][category])
        permutation = torch.randperm(size, generator=generator)
        mask = torch.zeros(size, dtype=torch.bool)
        mask[permutation[:valid_count]] = True
        mask = mask.reshape(1, 8, 8)
        target_depth = 0.2 + 2.0 * torch.rand((1, 8, 8), generator=generator, dtype=dtype)
        predicted_base = target_depth.detach() + 0.03 * torch.randn((1, 8, 8), generator=generator, dtype=dtype)
        predicted_official = predicted_base.clone().requires_grad_(True)
        predicted_compat = predicted_base.clone().requires_grad_(True)
        target_rgb = torch.rand((1, 3, 8, 8), generator=generator, dtype=dtype)
        predicted_rgb = torch.clamp(target_rgb * 0.97 + 0.01, 0.0, 1.0)
        official_depth = torch.abs(target_depth - predicted_official)[mask].mean()
        official_im = rgb_loss_fn(official)(predicted_rgb, target_rgb)
        official_total = official_depth * LOSS_WEIGHTS["depth"] + official_im * LOSS_WEIGHTS["im"]
        compat_total, components, metadata = compute_mapping_losses_empty_depth_safe(
            predicted_compat,
            target_depth,
            predicted_rgb,
            target_rgb,
            rgb_loss_fn(official),
            LOSS_WEIGHTS,
            valid_mask=mask,
        )
        official_depth.backward()
        components["depth"].backward()
        value_diff = float(torch.abs(official_depth.detach() - components["depth"].detach()).item())
        total_diff = float(torch.abs(official_total.detach() - compat_total.detach()).item())
        gradient_diff = float(torch.max(torch.abs(predicted_official.grad - predicted_compat.grad)).item())
        invalid_grad = float(torch.max(torch.abs(predicted_compat.grad[~mask])).item()) if (~mask).any() else 0.0
        max_value_diff[dtype_name] = max(max_value_diff[dtype_name], value_diff)
        max_total_diff[dtype_name] = max(max_total_diff[dtype_name], total_diff)
        max_gradient_diff[dtype_name] = max(max_gradient_diff[dtype_name], gradient_diff)
        max_invalid_gradient[dtype_name] = max(max_invalid_gradient[dtype_name], invalid_grad)
        tensors = [official_depth, official_im, official_total, compat_total, components["depth"], components["im"], predicted_compat.grad]
        nonfinite += sum(0 if bool(torch.isfinite(tensor).all().item()) else 1 for tensor in tensors)
        fixture_rows.append({
            "fixture": fixture,
            "dtype": dtype_name,
            "valid_count": valid_count,
            "value_diff": value_diff,
            "total_diff": total_diff,
            "gradient_diff": gradient_diff,
            "invalid_gradient_max_abs": invalid_grad,
            "metadata": metadata,
        })
    gates = {
        "fixture_count_ge_100": FIXTURE_COUNT >= 100,
        "float64_max_abs_diff_le_1e_10": max_value_diff["float64"] <= 1e-10 and max_total_diff["float64"] <= 1e-10,
        "float32_max_abs_diff_le_1e_6": max_value_diff["float32"] <= 1e-6 and max_total_diff["float32"] <= 1e-6,
        "gradient_max_abs_diff_le_1e_6": max(max_gradient_diff.values()) <= 1e-6,
        "invalid_position_gradients_zero": max(max_invalid_gradient.values()) == 0.0,
        "nonfinite_zero": nonfinite == 0,
        "dtype_coverage": {row["dtype"] for row in fixture_rows} == {"float32", "float64"},
        "valid_count_coverage": valid_count_classes == {"one", "two", "sparse", "medium", "all"},
    }
    return {
        "seed": SEED,
        "fixture_count": FIXTURE_COUNT,
        "synthetic_backward_count": FIXTURE_COUNT * 2,
        "optimizer_count": 0,
        "parameter_update_count": 0,
        "loss_weights": LOSS_WEIGHTS,
        "max_depth_value_diff": max_value_diff,
        "max_total_diff": max_total_diff,
        "max_gradient_diff": max_gradient_diff,
        "max_invalid_gradient": max_invalid_gradient,
        "nonfinite_count": nonfinite,
        "valid_count_classes": sorted(valid_count_classes),
        "gates": gates,
        "pass": all(gates.values()),
        "status": "PASS_NONEMPTY_SYNTHETIC_EQUIVALENCE" if all(gates.values()) else "FAIL_NONEMPTY_SYNTHETIC_EQUIVALENCE",
    }


def run_zero(official) -> dict[str, Any]:
    cases: list[dict[str, Any]] = []
    requested_devices = ["cpu"]
    if torch.cuda.is_available():
        requested_devices.append("cuda:0")
    backward_count = 0
    for device in requested_devices:
        for dtype in (torch.float32, torch.float64):
            target_depth = torch.zeros((1, 8, 8), dtype=dtype, device=device)
            predicted_depth = torch.linspace(0.1, 1.0, 64, dtype=dtype, device=device).reshape(1, 8, 8).requires_grad_(True)
            target_rgb = torch.full((1, 3, 8, 8), 0.4, dtype=dtype, device=device)
            predicted_rgb = torch.full((1, 3, 8, 8), 0.5, dtype=dtype, device=device)
            mask = torch.zeros_like(target_depth, dtype=torch.bool)
            official_depth = torch.abs(target_depth - predicted_depth)[mask].mean()
            total, components, metadata = compute_mapping_losses_empty_depth_safe(
                predicted_depth, target_depth, predicted_rgb, target_rgb, rgb_loss_fn(official), LOSS_WEIGHTS, valid_mask=mask
            )
            components["depth"].backward()
            backward_count += 1
            grad = predicted_depth.grad
            case = {
                "device": device,
                "dtype": str(dtype).split(".")[-1],
                "official_depth_finite": bool(torch.isfinite(official_depth).item()),
                "compat_depth": float(components["depth"].detach().item()),
                "compat_depth_finite": bool(torch.isfinite(components["depth"]).item()),
                "compat_total_finite": bool(torch.isfinite(total).item()),
                "rgb_finite": bool(torch.isfinite(components["im"]).item()),
                "gradient_finite": bool(torch.isfinite(grad).all().item()),
                "gradient_max_abs": float(torch.max(torch.abs(grad)).item()),
                "metadata": metadata,
            }
            case["pass"] = (
                not case["official_depth_finite"]
                and case["compat_depth"] == 0.0
                and case["compat_depth_finite"]
                and case["compat_total_finite"]
                and case["rgb_finite"]
                and case["gradient_finite"]
                and case["gradient_max_abs"] == 0.0
                and metadata["depth_event"] == "EMPTY_DEPTH_SAFE_SKIP_DEPTH_INITIALIZATION"
            )
            cases.append(case)
    passed = all(case["pass"] for case in cases)
    return {
        "cases": cases,
        "case_count": len(cases),
        "devices": requested_devices,
        "synthetic_backward_count": backward_count,
        "optimizer_count": 0,
        "parameter_update_count": 0,
        "pass": passed,
        "status": "PASS_ZERO_MASK_SYNTHETIC_VALIDATION" if passed else "FAIL_ZERO_MASK_SYNTHETIC_VALIDATION",
    }


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--official-repo", type=Path, required=True)
    parser.add_argument("--output-dir", type=Path, required=True)
    args = parser.parse_args()
    args.output_dir.mkdir(parents=True, exist_ok=True)
    torch.manual_seed(SEED)
    official = load_official(args.official_repo.resolve())
    nonempty = run_nonempty(official)
    zero = run_zero(official)
    write_json(args.output_dir / "nonempty_synthetic_equivalence.json", nonempty)
    write_json(args.output_dir / "zero_mask_synthetic_validation.json", zero)
    print(nonempty["status"])
    print(zero["status"])
    return 0 if nonempty["pass"] and zero["pass"] else 2


if __name__ == "__main__":
    raise SystemExit(main())
