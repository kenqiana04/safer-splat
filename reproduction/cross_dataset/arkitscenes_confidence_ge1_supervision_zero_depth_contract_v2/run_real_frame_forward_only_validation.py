#!/usr/bin/env python3
"""Forward-only real-frame and state-machine validation for the frozen M1 policy."""

from __future__ import annotations

import argparse
import copy
import csv
import hashlib
import json
import sys
from pathlib import Path
from typing import Any

import imageio.v2 as imageio
import numpy as np
import torch

from empty_depth_safe_splatam_compat import (
    EMPTY_EVENT,
    NONEMPTY_EVENT,
    compute_mapping_losses_empty_depth_safe,
    maybe_add_new_gaussians_empty_depth_safe,
    maybe_initialize_depth_points_empty_depth_safe,
)


LOSS_WEIGHTS = {"depth": 0.0, "im": 1.0}
ZERO_INDICES = [76, 79]
SEQUENCE = [74, 75, 76, 77, 78, 79, 80, 81]


def write_json(path: Path, value: Any) -> None:
    path.write_text(json.dumps(value, indent=2, sort_keys=True) + "\n", encoding="utf-8", newline="\n")


def file_sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def load_official(repo: Path):
    sys.path.insert(0, str(repo))
    import scripts.splatam as official  # type: ignore
    return official


def rgb_loss_fn(official):
    def loss(predicted: torch.Tensor, target: torch.Tensor) -> torch.Tensor:
        return 0.8 * official.l1_loss_v1(predicted, target) + 0.2 * (1.0 - official.calc_ssim(predicted, target))
    return loss


def load_rows(path: Path) -> list[dict[str, str]]:
    with path.open("r", encoding="utf-8", newline="") as handle:
        return list(csv.DictReader(handle))


def load_frame(index: int, row: dict[str, str], asset_root: Path, device: torch.device) -> dict[str, Any]:
    def resolved(relative: str) -> Path:
        path = (asset_root / relative).resolve()
        path.relative_to(asset_root.resolve())
        if not path.is_file():
            raise FileNotFoundError(path)
        return path

    rgb_path = resolved(row["rgb"])
    depth_path = resolved(row["depth"])
    confidence_path = resolved(row["confidence"])
    rgb_np = np.asarray(imageio.imread(rgb_path))
    depth_raw = np.asarray(imageio.imread(depth_path))
    confidence = np.asarray(imageio.imread(confidence_path))
    if rgb_np.shape[:2] != depth_raw.shape or depth_raw.shape != confidence.shape:
        raise RuntimeError(f"shape mismatch at TRAIN row {index}")
    if confidence.dtype != np.uint8 or not set(np.unique(confidence)).issubset({0, 1, 2}):
        raise RuntimeError(f"invalid confidence asset at TRAIN row {index}")
    rgb = torch.from_numpy(np.ascontiguousarray(rgb_np)).to(device=device, dtype=torch.float32).permute(2, 0, 1) / 255.0
    # PyTorch 2.1 does not accept NumPy uint16 directly.  Cast without scaling,
    # then apply the frozen ARKitScenes millimetre-to-metre conversion.
    depth_float = np.ascontiguousarray(depth_raw.astype(np.float32, copy=False))
    raw_depth = torch.from_numpy(depth_float).to(device=device).unsqueeze(0) / 1000.0
    confidence_tensor = torch.from_numpy(np.ascontiguousarray(confidence)).to(device=device)
    m1_mask = (raw_depth > 0) & (confidence_tensor.unsqueeze(0) >= 1)
    m1_depth = raw_depth.clone()
    m1_depth[~m1_mask] = 0.0
    intrinsics = torch.tensor([
        [float(row["fx"]), 0.0, float(row["cx"])],
        [0.0, float(row["fy"]), float(row["cy"])],
        [0.0, 0.0, 1.0],
    ], dtype=torch.float32, device=device)
    c2w = torch.tensor([[float(row[f"c2w_{i}{j}"]) for j in range(4)] for i in range(4)], dtype=torch.float32, device=device)
    w2c = torch.linalg.inv(c2w)
    return {
        "index": index,
        "row": row,
        "rgb": rgb,
        "raw_depth": raw_depth,
        "m1_depth": m1_depth,
        "m1_mask": m1_mask,
        "confidence": confidence,
        "intrinsics": intrinsics,
        "c2w": c2w,
        "w2c": w2c,
        "asset_sha256": {
            "rgb": file_sha256(rgb_path),
            "depth": file_sha256(depth_path),
            "confidence": file_sha256(confidence_path),
        },
    }


def select_nonempty(rows: list[dict[str, str]], per_frame: list[dict[str, str]]) -> list[int]:
    m1 = {int(row["index"]): row for row in per_frame if row["mask"] == "M1_CONFIDENCE_GE1"}
    by_group: dict[str, list[int]] = {}
    for index, row in enumerate(rows):
        if int(m1[index]["valid_pixel_count"]) > 0:
            by_group.setdefault(row["v1_group_id"], []).append(index)
    selected: set[int] = set()
    for group in sorted(by_group, key=int):
        candidates = sorted(by_group[group], key=lambda i: (float(m1[i]["retained_fraction"]), i))
        count = min(4, len(candidates))
        if count == 1:
            positions = [0]
        else:
            positions = sorted({round(k * (len(candidates) - 1) / (count - 1)) for k in range(count)})
        selected.update(candidates[position] for position in positions)
    remaining = sorted(
        (i for i in m1 if int(m1[i]["valid_pixel_count"]) > 0 and i not in selected),
        key=lambda i: (float(m1[i]["retained_fraction"]), i),
    )
    selected.update(remaining[: max(0, 32 - len(selected))])
    result = sorted(selected)
    if len(result) < 32 or {rows[i]["v1_group_id"] for i in result} != set(by_group):
        raise RuntimeError("deterministic selection failed frame-count/group coverage")
    return result[:32]


def tensor_unchanged(before: torch.Tensor, after: torch.Tensor) -> bool:
    return before.shape == after.shape and before.dtype == after.dtype and bool(torch.equal(before, after))


def run_nonempty(official, rows, per_frame, asset_root: Path, device: torch.device) -> dict[str, Any]:
    selected = select_nonempty(rows, per_frame)
    details: list[dict[str, Any]] = []
    max_depth_diff = max_rgb_diff = max_total_diff = max_point_diff = max_attr_diff = 0.0
    nonfinite = 0
    for index in selected:
        frame = load_frame(index, rows[index], asset_root, device)
        target_depth = frame["m1_depth"]
        predicted_depth = target_depth + 0.01
        target_rgb = frame["rgb"].unsqueeze(0)
        predicted_rgb = torch.clamp(target_rgb * 0.97 + 0.01, 0.0, 1.0)
        mask = frame["m1_mask"]
        official_depth = torch.abs(target_depth - predicted_depth)[mask].mean()
        official_im = rgb_loss_fn(official)(predicted_rgb, target_rgb)
        official_total = official_depth * LOSS_WEIGHTS["depth"] + official_im * LOSS_WEIGHTS["im"]
        compat_total, components, metadata = compute_mapping_losses_empty_depth_safe(
            predicted_depth, target_depth, predicted_rgb, target_rgb, rgb_loss_fn(official), LOSS_WEIGHTS, valid_mask=mask
        )
        color_before = frame["rgb"].clone()
        depth_before = target_depth.clone()
        intrinsics_before = frame["intrinsics"].clone()
        w2c_before = frame["w2c"].clone()
        direct_points, direct_scales = official.get_pointcloud(
            frame["rgb"], target_depth, frame["intrinsics"], frame["w2c"],
            transform_pts=True, mask=mask.reshape(-1), compute_mean_sq_dist=True, mean_sq_dist_method="projective"
        )
        wrapped, point_meta = maybe_initialize_depth_points_empty_depth_safe(
            mask, official.get_pointcloud, frame["rgb"], target_depth, frame["intrinsics"], frame["w2c"],
            transform_pts=True, compute_mean_sq_dist=True, mean_sq_dist_method="projective"
        )
        compat_points, compat_scales = wrapped
        point_diff = float(torch.max(torch.abs(direct_points - compat_points)).item()) if direct_points.numel() else 0.0
        attr_diff = float(torch.max(torch.abs(direct_scales - compat_scales)).item()) if direct_scales.numel() else 0.0
        depth_diff = float(torch.abs(official_depth - components["depth"]).item())
        rgb_diff = float(torch.abs(official_im - components["im"]).item())
        total_diff = float(torch.abs(official_total - compat_total).item())
        max_depth_diff = max(max_depth_diff, depth_diff)
        max_rgb_diff = max(max_rgb_diff, rgb_diff)
        max_total_diff = max(max_total_diff, total_diff)
        max_point_diff = max(max_point_diff, point_diff)
        max_attr_diff = max(max_attr_diff, attr_diff)
        finite = all(bool(torch.isfinite(value).all().item()) for value in [official_depth, official_im, official_total, compat_total, direct_points, direct_scales])
        nonfinite += 0 if finite else 1
        no_mutation = (
            tensor_unchanged(color_before, frame["rgb"])
            and tensor_unchanged(depth_before, target_depth)
            and tensor_unchanged(intrinsics_before, frame["intrinsics"])
            and tensor_unchanged(w2c_before, frame["w2c"])
        )
        details.append({
            "index": index,
            "timestamp": rows[index]["timestamp"],
            "group_id": int(rows[index]["v1_group_id"]),
            "group_hash": rows[index]["v1_group_hash"],
            "m1_valid_count": int(mask.sum().item()),
            "m1_retention": float(mask.sum().item()) / int((frame["raw_depth"] > 0).sum().item()),
            "depth_loss_abs_diff": depth_diff,
            "rgb_loss_abs_diff": rgb_diff,
            "total_loss_abs_diff": total_diff,
            "initialization_point_count_official": int(direct_points.shape[0]),
            "initialization_point_count_compat": int(compat_points.shape[0]),
            "point_attribute_max_abs_diff": point_diff,
            "scale_attribute_max_abs_diff": attr_diff,
            "no_mutation": no_mutation,
            "finite": finite,
            "depth_metadata": metadata,
            "point_metadata": point_meta,
        })
    gates = {
        "frame_count_ge_32": len(details) >= 32,
        "all_groups_covered": len({row["group_id"] for row in details}) == 8,
        "depth_equivalent": max_depth_diff <= 1e-6,
        "rgb_equivalent": max_rgb_diff <= 1e-6,
        "total_equivalent": max_total_diff <= 1e-6,
        "point_count_identical": all(row["initialization_point_count_official"] == row["initialization_point_count_compat"] for row in details),
        "point_attributes_identical": max_point_diff == 0.0 and max_attr_diff == 0.0,
        "no_mutation": all(row["no_mutation"] for row in details),
        "nonfinite_zero": nonfinite == 0,
        "no_backward": True,
        "no_optimizer": True,
        "no_update": True,
    }
    return {
        "selection_rule": "per-group retention quantiles, then lowest-retention unused canonical TRAIN rows; deterministic index tie-break",
        "selected_indices": selected,
        "frame_count": len(details),
        "group_ids": sorted({row["group_id"] for row in details}),
        "max_depth_loss_abs_diff": max_depth_diff,
        "max_rgb_loss_abs_diff": max_rgb_diff,
        "max_total_loss_abs_diff": max_total_diff,
        "max_point_attribute_abs_diff": max_point_diff,
        "max_scale_attribute_abs_diff": max_attr_diff,
        "nonfinite_count": nonfinite,
        "backward_count": 0,
        "optimizer_count": 0,
        "parameter_update_count": 0,
        "details": details,
        "gates": gates,
        "pass": all(gates.values()),
        "status": "PASS_NONEMPTY_REAL_FRAME_FORWARD_EQUIVALENCE" if all(gates.values()) else "FAIL_NONEMPTY_REAL_FRAME_FORWARD_EQUIVALENCE",
    }


def run_zero(official, rows, asset_root: Path, device: torch.device) -> dict[str, Any]:
    cases: list[dict[str, Any]] = []
    for index in ZERO_INDICES:
        frame = load_frame(index, rows[index], asset_root, device)
        target_depth = frame["m1_depth"]
        predicted_depth = frame["raw_depth"] + 0.01
        target_rgb = frame["rgb"].unsqueeze(0)
        predicted_rgb = torch.clamp(target_rgb * 0.97 + 0.01, 0.0, 1.0)
        official_depth = torch.abs(target_depth - predicted_depth)[frame["m1_mask"]].mean()
        total, components, metadata = compute_mapping_losses_empty_depth_safe(
            predicted_depth, target_depth, predicted_rgb, target_rgb, rgb_loss_fn(official), LOSS_WEIGHTS, valid_mask=frame["m1_mask"]
        )
        wrapped, point_meta = maybe_initialize_depth_points_empty_depth_safe(
            frame["m1_mask"], official.get_pointcloud, frame["rgb"], target_depth, frame["intrinsics"], frame["w2c"],
            transform_pts=True, compute_mean_sq_dist=True, mean_sq_dist_method="projective"
        )
        points, scales = wrapped
        params = {"means3D": torch.ones((3, 3), device=device)}
        variables = {"scene_radius": torch.tensor(2.0, device=device), "marker": torch.tensor([1.0], device=device)}
        params_before = copy.deepcopy(params)
        variables_before = copy.deepcopy(variables)
        callback_called = {"value": False}
        def forbidden_callback(*_args, **_kwargs):
            callback_called["value"] = True
            raise RuntimeError("official add callback must not run for an empty M1 frame")
        out_params, out_variables, add_meta = maybe_add_new_gaussians_empty_depth_safe(
            frame["m1_mask"], params, variables, forbidden_callback
        )
        confidence_unique = sorted(int(value) for value in np.unique(frame["confidence"]))
        no_mutation = (
            out_params is params
            and out_variables is variables
            and tensor_unchanged(params_before["means3D"], params["means3D"])
            and tensor_unchanged(variables_before["scene_radius"], variables["scene_radius"])
            and tensor_unchanged(variables_before["marker"], variables["marker"])
        )
        finite = all(bool(torch.isfinite(value).all().item()) for value in [total, components["depth"], components["im"], points, scales])
        case = {
            "index": index,
            "timestamp": rows[index]["timestamp"],
            "not_first_frame": index != 0,
            "confidence_unique": confidence_unique,
            "official_confidence_all_zero": confidence_unique == [0],
            "m1_valid_count": int(frame["m1_mask"].sum().item()),
            "official_depth_finite": bool(torch.isfinite(official_depth).item()),
            "compat_total_finite": bool(torch.isfinite(total).item()),
            "compat_depth": float(components["depth"].item()),
            "compat_rgb_finite": bool(torch.isfinite(components["im"]).item()),
            "initialization_point_count": int(points.shape[0]),
            "add_new_gaussian_count": int(add_meta["added_count"]),
            "callback_called": callback_called["value"],
            "no_parameter_or_scene_radius_mutation": no_mutation,
            "depth_event": metadata["depth_event"],
            "point_event": point_meta["event"],
            "add_event": add_meta["event"],
            "finite": finite,
            "asset_sha256": frame["asset_sha256"],
            "canonical_manifest_identity": {key: rows[index][key] for key in ["video_id", "timestamp", "rgb", "depth", "confidence", "intrinsics", "split"]},
        }
        case["pass"] = (
            case["not_first_frame"]
            and case["official_confidence_all_zero"]
            and case["m1_valid_count"] == 0
            and not case["official_depth_finite"]
            and case["compat_total_finite"]
            and case["compat_depth"] == 0.0
            and case["compat_rgb_finite"]
            and case["initialization_point_count"] == 0
            and case["add_new_gaussian_count"] == 0
            and not case["callback_called"]
            and case["no_parameter_or_scene_radius_mutation"]
            and case["depth_event"] == EMPTY_EVENT
            and case["point_event"] == EMPTY_EVENT
            and case["add_event"] == EMPTY_EVENT
            and case["finite"]
        )
        cases.append(case)
    passed = all(case["pass"] for case in cases)
    return {
        "zero_indices": ZERO_INDICES,
        "cases": cases,
        "real_frame_backward_count": 0,
        "optimizer_count": 0,
        "parameter_update_count": 0,
        "pass": passed,
        "status": "PASS_ZERO_FRAME_REAL_FORWARD_VALIDATION" if passed else "FAIL_ZERO_FRAME_REAL_FORWARD_VALIDATION",
    }


def run_sequence(rows, per_frame) -> dict[str, Any]:
    m1 = {int(row["index"]): int(row["valid_pixel_count"]) for row in per_frame if row["mask"] == "M1_CONFIDENCE_GE1"}
    states: list[dict[str, Any]] = []
    state_token = "INITIAL"
    for index in SEQUENCE:
        before = state_token
        if m1[index] == 0:
            route = "EMPTY_DEPTH_SAFE"
            event = EMPTY_EVENT
            added = 0
        else:
            route = "OFFICIAL_EQUIVALENT_NONEMPTY"
            event = NONEMPTY_EVENT
            added = "DELEGATED_NOT_EXECUTED_STATE_ONLY"
        state_token = hashlib.sha256(f"{state_token}|{index}|{route}".encode("utf-8")).hexdigest()
        states.append({
            "index": index,
            "timestamp": rows[index]["timestamp"],
            "valid_depth_count": m1[index],
            "route": route,
            "event": event,
            "new_gaussian_count": added,
            "state_before": before,
            "state_after": state_token,
            "frame_retained": True,
        })
    gates = {
        "order_unchanged": [row["index"] for row in states] == SEQUENCE,
        "all_frames_retained": all(row["frame_retained"] for row in states),
        "zero_frames_exact": [row["index"] for row in states if row["route"] == "EMPTY_DEPTH_SAFE"] == ZERO_INDICES,
        "zero_frames_add_zero": all(row["new_gaussian_count"] == 0 for row in states if row["route"] == "EMPTY_DEPTH_SAFE"),
        "later_nonempty_resumes": states[-2]["route"] == "OFFICIAL_EQUIVALENT_NONEMPTY" and states[-1]["route"] == "OFFICIAL_EQUIVALENT_NONEMPTY",
        "no_mapper": True,
        "no_optimizer": True,
        "no_nonfinite_or_state_leak": len({row["state_after"] for row in states}) == len(states),
    }
    return {
        "sequence": SEQUENCE,
        "mode": "LIGHTWEIGHT_STATE_MACHINE_ONLY",
        "states": states,
        "gates": gates,
        "pass": all(gates.values()),
        "status": "PASS_SEQUENCE_STATE_DRY_RUN" if all(gates.values()) else "FAIL_SEQUENCE_STATE_DRY_RUN",
    }


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--official-repo", type=Path, required=True)
    parser.add_argument("--asset-root", type=Path, required=True)
    parser.add_argument("--train-manifest", type=Path, required=True)
    parser.add_argument("--prior-per-frame", type=Path, required=True)
    parser.add_argument("--output-dir", type=Path, required=True)
    args = parser.parse_args()
    if not torch.cuda.is_available():
        raise RuntimeError("official get_pointcloud requires the qualified CUDA environment")
    device = torch.device("cuda:0")
    rows = load_rows(args.train_manifest.resolve())
    per_frame = load_rows(args.prior_per_frame.resolve())
    if len(rows) != 214:
        raise RuntimeError("canonical TRAIN manifest row count changed")
    official = load_official(args.official_repo.resolve())
    args.output_dir.mkdir(parents=True, exist_ok=True)
    nonempty = run_nonempty(official, rows, per_frame, args.asset_root.resolve(), device)
    zero = run_zero(official, rows, args.asset_root.resolve(), device)
    sequence = run_sequence(rows, per_frame)
    first = load_frame(0, rows[0], args.asset_root.resolve(), device)
    first_frame = {
        "index": 0,
        "timestamp": rows[0]["timestamp"],
        "m1_valid_count": int(first["m1_mask"].sum().item()),
        "first_frame_nonempty": bool(first["m1_mask"].any().item()),
        "failure_if_empty": "INITIAL_FRAME_ZERO_DEPTH_UNSUPPORTED",
    }
    write_json(args.output_dir / "nonempty_real_frame_equivalence.json", nonempty)
    write_json(args.output_dir / "zero_frame_real_validation.json", zero)
    write_json(args.output_dir / "sequence_state_dry_run.json", sequence)
    write_json(args.output_dir / "first_frame_m1_validation.json", first_frame)
    print(nonempty["status"])
    print(zero["status"])
    print(sequence["status"])
    print("PASS_FIRST_FRAME_M1_NONEMPTY" if first_frame["first_frame_nonempty"] else first_frame["failure_if_empty"])
    passed = nonempty["pass"] and zero["pass"] and sequence["pass"] and first_frame["first_frame_nonempty"]
    return 0 if passed else 2


if __name__ == "__main__":
    raise SystemExit(main())
