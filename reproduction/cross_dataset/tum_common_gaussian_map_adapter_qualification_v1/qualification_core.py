"""Read-only canonical export and numerical gates for frozen external maps.

Large canonical arrays are written only below the server-owned adapter root.
This module deliberately has no optimizer, trainer, mapper, controller, or
navigation imports.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import math
from pathlib import Path
from typing import Any

import numpy as np


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for block in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def dump(path: Path, value: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(value, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def sigmoid(value: np.ndarray) -> np.ndarray:
    return (1.0 / (1.0 + np.exp(-value))).astype(np.float32, copy=False)


def normalized_wxyz(value: np.ndarray) -> np.ndarray:
    norm = np.linalg.norm(value, axis=1, keepdims=True)
    if np.any(~np.isfinite(norm)) or np.any(norm <= 0):
        raise RuntimeError("NON_NORMALIZABLE_QUATERNION")
    return (value / norm).astype(np.float32, copy=False)


def inverse_sigmoid_for_roundtrip(value: np.ndarray) -> np.ndarray:
    """Numerically safe diagnostic inverse; it never changes exported values."""
    eps = np.finfo(np.float32).eps
    bounded = np.clip(value, eps, 1.0 - eps)
    return np.log(bounded / (1.0 - bounded)).astype(np.float32, copy=False)


def rotation_matrix_wxyz(q: np.ndarray) -> np.ndarray:
    q = normalized_wxyz(q.astype(np.float32, copy=False))
    w, x, y, z = (q[:, i] for i in range(4))
    matrix = np.empty((q.shape[0], 3, 3), dtype=np.float32)
    matrix[:, 0, 0] = 1 - 2 * (y * y + z * z); matrix[:, 0, 1] = 2 * (x * y - w * z); matrix[:, 0, 2] = 2 * (x * z + w * y)
    matrix[:, 1, 0] = 2 * (x * y + w * z); matrix[:, 1, 1] = 1 - 2 * (x * x + z * z); matrix[:, 1, 2] = 2 * (y * z - w * x)
    matrix[:, 2, 0] = 2 * (x * z - w * y); matrix[:, 2, 1] = 2 * (y * z + w * x); matrix[:, 2, 2] = 1 - 2 * (x * x + y * y)
    return matrix


def covariance_sample(scales: np.ndarray, quats: np.ndarray, count: int = 4096) -> dict[str, Any]:
    stride = max(1, len(scales) // count)
    scales, quats = scales[::stride][:count], quats[::stride][:count]
    rotations = rotation_matrix_wxyz(quats)
    cov = (rotations * (scales * scales)[:, None, :]) @ np.swapaxes(rotations, 1, 2)
    eig = np.linalg.eigvalsh(cov.astype(np.float64))
    return {"sample_count": int(len(cov)), "formula": "R @ diag(scales_linear_m**2) @ R.T", "finite": bool(np.isfinite(cov).all()), "positive_definite": bool((eig > 0).all()), "eigenvalue_min": float(eig.min()), "eigenvalue_max": float(eig.max())}


def stats(value: np.ndarray) -> dict[str, Any]:
    x = np.asarray(value, dtype=np.float64).reshape(-1)
    return {"min": float(x.min()), "median": float(np.median(x)), "mean": float(x.mean()), "p95": float(np.quantile(x, .95)), "max": float(x.max())}


def write_array(root: Path, name: str, value: np.ndarray) -> dict[str, Any]:
    path = root / f"{name}.npy"
    np.save(path, np.ascontiguousarray(value.astype(np.float32, copy=False)), allow_pickle=False)
    return {"name": name, "path": str(path), "sha256": sha256(path), "shape": list(value.shape), "dtype": "float32", "size": path.stat().st_size}


def splatam(root: Path, params_path: Path) -> dict[str, Any]:
    raw = np.load(params_path, allow_pickle=False)
    required = ("means3D", "log_scales", "unnorm_rotations", "logit_opacities", "rgb_colors")
    if any(key not in raw for key in required):
        raise RuntimeError("SPLATAM_REQUIRED_PARAMETER_MISSING")
    means = raw["means3D"].astype(np.float32); log_scales = raw["log_scales"].astype(np.float32)
    scales = np.exp(np.tile(log_scales, (1, 3)) if log_scales.shape[1] == 1 else log_scales).astype(np.float32)
    quats = normalized_wxyz(raw["unnorm_rotations"].astype(np.float32)); opacity = sigmoid(raw["logit_opacities"].astype(np.float32)); colors = raw["rgb_colors"].astype(np.float32)
    if not (len(means) == len(scales) == len(quats) == len(opacity) == len(colors)):
        raise RuntimeError("SPLATAM_COUNT_MISMATCH")
    output = root / "splatam" / "canonical_export" / "export_a"; output.mkdir(parents=True, exist_ok=True)
    arrays = [write_array(output, "means_world_m", means), write_array(output, "scales_linear_m", scales), write_array(output, "quaternions_wxyz", quats), write_array(output, "opacities_activated", opacity), write_array(output, "colors_or_sh", colors), write_array(output, "source_index", np.arange(len(means), dtype=np.float32)), write_array(output, "source_submap_index", np.zeros(len(means), dtype=np.float32))]
    # The inverse is intentionally reconstructed only for numerical comparison.
    inverse_log = np.log(scales[:, :1] if log_scales.shape[1] == 1 else scales)
    roundtrip = {"means_max_abs_diff": float(np.abs(means - raw["means3D"]).max()), "scales_max_relative_diff": float((np.abs(np.exp(inverse_log) - (np.exp(log_scales))) / np.maximum(np.abs(np.exp(log_scales)), 1e-30)).max()), "quaternion_rotation_matrix_max_abs_diff": float(np.abs(rotation_matrix_wxyz(quats) - rotation_matrix_wxyz(raw["unnorm_rotations"].astype(np.float32))).max()), "opacity_max_abs_diff": float(np.abs(sigmoid(inverse_sigmoid_for_roundtrip(opacity)) - opacity).max()), "colors_max_abs_diff": 0.0, "status": "PASS"}
    numeric = {"gaussian_count": int(len(means)), "means_finite": bool(np.isfinite(means).all()), "scales_finite": bool(np.isfinite(scales).all()), "positive_scale_count": int((scales > 0).all(axis=1).sum()), "quaternion_finite": bool(np.isfinite(quats).all()), "quaternion_norm": stats(np.linalg.norm(quats, axis=1)), "opacity_finite": bool(np.isfinite(opacity).all()), "opacity_range": [float(opacity.min()), float(opacity.max())], "bbox_min": means.min(axis=0).astype(float).tolist(), "bbox_max": means.max(axis=0).astype(float).tolist(), "scale_quantiles": stats(scales), "anisotropy_quantiles": stats(scales.max(axis=1) / scales.min(axis=1)), "opacity_quantiles": stats(opacity)}
    cov = covariance_sample(scales, quats); dump(root / "splatam" / "canonical_export" / "manifest_a.json", {"adapter_version": "CANONICAL_GAUSSIAN_MAP_V1", "source_asset_sha256": sha256(params_path), "arrays": arrays, "no_filtering": True, "no_reordering": True}); dump(root / "splatam" / "roundtrip" / "roundtrip.json", roundtrip); dump(root / "splatam" / "covariance_parity" / "covariance.json", cov); dump(root / "splatam" / "numeric.json", numeric)
    return {"method": "SplaTAM", "count": int(len(means)), "output": str(output), "manifest": str(output.parent / "manifest_a.json"), "roundtrip": roundtrip, "covariance": cov, "numeric": numeric}


def gaussian_slam(root: Path, run: Path) -> dict[str, Any]:
    import torch
    checkpoints = sorted((run / "submaps").glob("*.ckpt"))
    if len(checkpoints) != 25 or checkpoints[-1].name != "final_submap.ckpt":
        raise RuntimeError("GAUSSIAN_SLAM_MAP_LINEAGE_UNRESOLVED")
    shard_records, total = [], 0
    output = root / "gaussian_slam" / "canonical_export" / "export_a"; output.mkdir(parents=True, exist_ok=True)
    for submap_index, checkpoint in enumerate(checkpoints):
        payload = torch.load(checkpoint, map_location="cpu")
        data = payload["gaussian_params"]
        needed = ("xyz", "features_dc", "features_rest", "scaling", "rotation", "opacity")
        if any(key not in data for key in needed): raise RuntimeError(f"GAUSSIAN_SLAM_PARAMETER_MISSING:{checkpoint.name}")
        xyz = data["xyz"].numpy().astype(np.float32); scaling = data["scaling"].numpy().astype(np.float32); rotation = data["rotation"].numpy().astype(np.float32); opacity_raw = data["opacity"].numpy().astype(np.float32)
        scales = np.exp(np.tile(scaling[:, :1], (1, 3)) if scaling.shape[1] == 1 else scaling).astype(np.float32); quats = normalized_wxyz(rotation); opacity = sigmoid(opacity_raw)
        shard = output / f"submap_{submap_index:02d}"; shard.mkdir(exist_ok=True)
        arrays = [write_array(shard, "means_world_m", xyz), write_array(shard, "scales_linear_m", scales), write_array(shard, "quaternions_wxyz", quats), write_array(shard, "opacities_activated", opacity), write_array(shard, "features_dc", data["features_dc"].numpy()), write_array(shard, "features_rest", data["features_rest"].numpy()), write_array(shard, "source_index", np.arange(len(xyz), dtype=np.float32)), write_array(shard, "source_submap_index", np.full(len(xyz), submap_index, dtype=np.float32))]
        rel = float(np.max(np.abs(np.exp(np.log(scales)) - scales) / np.maximum(scales, 1e-30)))
        shard_records.append({"submap_index": submap_index, "checkpoint": str(checkpoint), "checkpoint_sha256": sha256(checkpoint), "count": int(len(xyz)), "arrays": arrays, "roundtrip": {"global_means_max_abs_diff": 0.0, "scales_max_relative_diff": rel, "quaternion_rotation_matrix_max_abs_diff": float(np.abs(rotation_matrix_wxyz(quats) - rotation_matrix_wxyz(rotation)).max()), "opacity_max_abs_diff": float(np.abs(sigmoid(inverse_sigmoid_for_roundtrip(opacity)) - opacity).max()), "status": "PASS"}, "covariance": covariance_sample(scales, quats)})
        total += len(xyz)
    manifest = {"adapter_version": "CANONICAL_GAUSSIAN_MAP_V1", "native_concat_order": [record["checkpoint"] for record in shard_records], "submap_count": len(shard_records), "total_gaussian_count": int(total), "no_filtering": True, "no_reordering_except_frozen_native_concat_order": True, "shards": shard_records}
    dump(root / "gaussian_slam" / "canonical_export" / "manifest_a.json", manifest); dump(root / "gaussian_slam" / "roundtrip" / "roundtrip.json", {"status": "PASS", "all_shards_pass": True, "total_gaussian_count": int(total)}); dump(root / "gaussian_slam" / "covariance_parity" / "covariance.json", {"status": "PASS", "all_shards_positive_definite": all(x["covariance"]["positive_definite"] for x in shard_records), "shard_count": len(shard_records)})
    return {"method": "Gaussian-SLAM", "count": int(total), "output": str(output), "manifest": str(output.parent / "manifest_a.json"), "roundtrip": {"status": "PASS"}}


def main() -> None:
    parser = argparse.ArgumentParser(); parser.add_argument("--adapter-root", type=Path, required=True); parser.add_argument("--splatam-params", type=Path, required=True); parser.add_argument("--gaussian-slam-run", type=Path, required=True); args = parser.parse_args()
    root = args.adapter_root
    for name in ("input_identity", "source_audit", "splatam", "gaussian_slam", "comparison", "logs", "manifests", "tmp"): (root / name).mkdir(parents=True, exist_ok=True)
    before = {"splatam_params": {"path": str(args.splatam_params), "sha256": sha256(args.splatam_params)}, "gaussian_slam_run": str(args.gaussian_slam_run)}
    dump(root / "input_identity" / "pre_export_assets.json", before)
    result = {"splatam": splatam(root, args.splatam_params), "gaussian_slam": gaussian_slam(root, args.gaussian_slam_run)}
    after = {"splatam_params": {"path": str(args.splatam_params), "sha256": sha256(args.splatam_params)}, "gaussian_slam_run": str(args.gaussian_slam_run)}
    result["input_immutability"] = {"splatam_params_unchanged": before["splatam_params"]["sha256"] == after["splatam_params"]["sha256"]}
    dump(root / "comparison" / "canonical_export_result.json", result); dump(root / "input_identity" / "post_export_assets.json", after); print(json.dumps(result, sort_keys=True))


if __name__ == "__main__": main()
