#!/usr/bin/env python3
"""Metric and isolation audit for the canonical ARKitScenes SplaTAM adapter."""

from __future__ import annotations

import argparse
import csv
import hashlib
import json
import sys
from pathlib import Path

import imageio.v2 as imageio
import numpy as np
import open3d as o3d


TRAIN_SHA256 = "167066916ce1a3281ac754dfdeec37ada9f5b0e31227c731c94cebb698a2a6e3"
SCENE = "48018874"
SEED = 20260730


def sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def row_pose(row: dict[str, str]) -> np.ndarray:
    return np.array([[float(row[f"c2w_{r}{c}"]) for c in range(4)] for r in range(4)], dtype=np.float64)


def row_intrinsics(row: dict[str, str]) -> np.ndarray:
    return np.array(
        [[float(row["fx"]), 0.0, float(row["cx"])], [0.0, float(row["fy"]), float(row["cy"])], [0.0, 0.0, 1.0]],
        dtype=np.float64,
    )


def parse_pincam(path: Path) -> tuple[int, int, float, float, float, float]:
    values = path.read_text(encoding="utf-8").strip().split()
    if len(values) != 6:
        raise RuntimeError(f"invalid pincam content: {path}")
    width, height = int(values[0]), int(values[1])
    return width, height, *(float(value) for value in values[2:])


def under(root: Path, relative: str) -> Path:
    candidate = (root / relative).resolve()
    try:
        candidate.relative_to(root)
    except ValueError as exc:
        raise RuntimeError(f"frozen manifest path escapes asset root: {relative}") from exc
    if not candidate.is_file():
        raise FileNotFoundError(candidate)
    return candidate


def stable_digest(value: object) -> str:
    return hashlib.sha256(json.dumps(value, sort_keys=True, separators=(",", ":")).encode("utf-8")).hexdigest()


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--source", type=Path, required=True)
    parser.add_argument("--adapter-root", type=Path, required=True)
    parser.add_argument("--manifest", type=Path, required=True)
    parser.add_argument("--asset-root", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    source = args.source.resolve()
    adapter_root = args.adapter_root.resolve()
    manifest = args.manifest.resolve()
    asset_root = args.asset_root.resolve()
    if sha256(manifest) != TRAIN_SHA256:
        raise RuntimeError("noncanonical TRAIN manifest")

    sys.path.insert(0, str(adapter_root))
    sys.path.insert(0, str(source))
    from arkitscenes_splatam_dataset import ARKitScenesSplaTAMDataset

    with manifest.open("r", encoding="utf-8", newline="") as handle:
        rows = list(csv.DictReader(handle))
    if len(rows) != 214 or any(row["split"] != "TRAIN" or row["video_id"] != SCENE for row in rows):
        raise RuntimeError("canonical TRAIN isolation failure")
    for row in rows:
        if "HELDOUT" in " ".join(row.values()).upper():
            raise RuntimeError("HELDOUT token in TRAIN manifest")

    adapter_config = {
        "dataset_name": "arkitscenes",
        "scene_id": SCENE,
        "expected_split": "TRAIN",
        "manifest_path": str(manifest),
        "manifest_sha256": TRAIN_SHA256,
        "asset_root": str(asset_root),
        "depth_mask_mode": "depth_gt_zero",
    }
    dataset = ARKitScenesSplaTAMDataset(
        adapter_config,
        str(asset_root.parent),
        SCENE,
        start=0,
        end=-1,
        stride=1,
        desired_height=192,
        desired_width=256,
        device="cpu",
        relative_pose=True,
    )
    if len(dataset) != 214:
        raise RuntimeError("adapter did not retain exactly TRAIN frames")
    heldout_rejected = False
    try:
        rejected = dict(adapter_config)
        rejected["expected_split"] = "HELDOUT"
        ARKitScenesSplaTAMDataset(rejected, str(asset_root.parent), SCENE, device="cpu")
    except ValueError:
        heldout_rejected = True
    if not heldout_rejected:
        raise RuntimeError("adapter accepted a HELDOUT request")

    first_color, first_depth, first_k, first_pose = dataset[0]
    if tuple(first_color.shape[:2]) != (192, 256) or tuple(first_depth.shape[:2]) != (192, 256):
        raise RuntimeError("adapter image resize contract failure")
    if not np.allclose(first_pose.numpy(), np.eye(4), atol=1e-5):
        raise RuntimeError("relative first pose must be identity")
    if not np.all(np.isfinite(first_depth.numpy())) or not np.all(np.isfinite(first_k.numpy())):
        raise RuntimeError("nonfinite adapter output")

    mesh = o3d.io.read_triangle_mesh(str(asset_root / f"{SCENE}_3dod_mesh.ply"))
    if mesh.is_empty() or len(mesh.triangles) == 0:
        raise RuntimeError("official ARKit mesh unavailable")
    scene = o3d.t.geometry.RaycastingScene()
    scene.add_triangles(o3d.t.geometry.TriangleMesh.from_legacy(mesh))

    rng = np.random.default_rng(SEED)
    sample_indices = sorted(int(index) for index in rng.choice(len(rows), size=64, replace=False))
    all_distances: list[float] = []
    frame_medians: list[float] = []
    reprojection_errors: list[float] = []
    depth_unit_errors: list[float] = []
    frame_records: list[dict[str, object]] = []
    per_frame_intrinsics: list[tuple[float, float, float, float]] = []

    for index in sample_indices:
        row = rows[index]
        rgb = np.asarray(imageio.imread(under(asset_root, row["rgb"])))
        depth_u16 = np.asarray(imageio.imread(under(asset_root, row["depth"])))
        confidence = np.asarray(imageio.imread(under(asset_root, row["confidence"])))
        pin = parse_pincam(under(asset_root, row["intrinsics"]))
        if rgb.shape[:2] != (int(row["height"]), int(row["width"])):
            raise RuntimeError("RGB dimensions disagree with frozen manifest")
        if depth_u16.shape[:2] != rgb.shape[:2] or confidence.shape[:2] != rgb.shape[:2]:
            raise RuntimeError("RGB/depth/confidence dimension mismatch")
        pin_expected = (int(row["width"]), int(row["height"]), float(row["fx"]), float(row["fy"]), float(row["cx"]), float(row["cy"]))
        if not np.allclose(np.asarray(pin), np.asarray(pin_expected), atol=1e-6, rtol=0.0):
            raise RuntimeError("pincam values disagree with frozen manifest")
        c2w = row_pose(row)
        w2c = np.linalg.inv(c2w)
        if not np.all(np.isfinite(c2w)) or not np.allclose(c2w @ w2c, np.eye(4), atol=1e-8):
            raise RuntimeError("C2W/W2C inverse contract failure")
        k = row_intrinsics(row)
        valid = np.argwhere(depth_u16 > 0)
        if len(valid) < 256:
            raise RuntimeError("insufficient valid depth for metric audit")
        chosen = valid[rng.choice(len(valid), size=min(512, len(valid)), replace=False)]
        v = chosen[:, 0].astype(np.float64)
        u = chosen[:, 1].astype(np.float64)
        z = depth_u16[chosen[:, 0], chosen[:, 1]].astype(np.float64) * 0.001
        local = np.column_stack(((u - k[0, 2]) * z / k[0, 0], (v - k[1, 2]) * z / k[1, 1], z))
        world = (c2w[:3, :3] @ local.T).T + c2w[:3, 3]
        local_roundtrip = (w2c[:3, :3] @ world.T).T + w2c[:3, 3]
        u_roundtrip = k[0, 0] * local_roundtrip[:, 0] / local_roundtrip[:, 2] + k[0, 2]
        v_roundtrip = k[1, 1] * local_roundtrip[:, 1] / local_roundtrip[:, 2] + k[1, 2]
        reprojection = np.sqrt((u_roundtrip - u) ** 2 + (v_roundtrip - v) ** 2)
        distances = scene.compute_distance(o3d.core.Tensor(world.astype(np.float32))).numpy().astype(np.float64)
        if not np.all(np.isfinite(distances)) or not np.all(np.isfinite(reprojection)):
            raise RuntimeError("nonfinite mesh/reprojection audit result")

        adapter_color, adapter_depth, adapter_k, _adapter_pose = dataset[index]
        depth_unit_error = float(np.max(np.abs(adapter_depth.numpy()[chosen[:, 0], chosen[:, 1], 0] - z)))
        expected_k = np.eye(4, dtype=np.float32)
        expected_k[:3, :3] = k.astype(np.float32)
        if not np.allclose(adapter_k.numpy(), expected_k, atol=1e-5, rtol=0.0):
            raise RuntimeError("adapter per-frame intrinsics contract failure")
        if tuple(adapter_color.shape[:2]) != (192, 256):
            raise RuntimeError("adapter RGB shape changed unexpectedly")
        all_distances.extend(float(value) for value in distances)
        frame_medians.append(float(np.median(distances)))
        reprojection_errors.extend(float(value) for value in reprojection)
        depth_unit_errors.append(depth_unit_error)
        per_frame_intrinsics.append((float(row["fx"]), float(row["fy"]), float(row["cx"]), float(row["cy"])))
        frame_records.append(
            {
                "index": index,
                "timestamp": row["timestamp"],
                "camera_center_world_m": [float(value) for value in c2w[:3, 3]],
                "mesh_distance_median_m": float(np.median(distances)),
                "mesh_distance_p95_m": float(np.quantile(distances, 0.95)),
                "reprojection_max_px": float(np.max(reprojection)),
                "depth_unit_max_error_m": depth_unit_error,
            }
        )

    distances_array = np.asarray(all_distances)
    intrinsics_array = np.asarray(per_frame_intrinsics)
    summary = {
        "status": "PASS_ARKITSCENES_SPLATAM_LOADER_METRIC_CONTRACT",
        "scene": SCENE,
        "train_manifest_sha256": TRAIN_SHA256,
        "train_rows": len(rows),
        "sample_seed": SEED,
        "sample_count": len(sample_indices),
        "sample_indices": sample_indices,
        "adapter": {
            "train_only": True,
            "heldout_rejected": heldout_rejected,
            "depth_conversion": "uint16_depth * 0.001",
            "baseline_mask": "depth > 0",
            "pose_estimation": False,
            "scale_fitting": False,
            "icp": False,
            "sim3": False,
        },
        "intrinsics": {
            "per_frame_preserved_by_adapter": True,
            "fx_range": [float(intrinsics_array[:, 0].min()), float(intrinsics_array[:, 0].max())],
            "fy_range": [float(intrinsics_array[:, 1].min()), float(intrinsics_array[:, 1].max())],
            "cx_range": [float(intrinsics_array[:, 2].min()), float(intrinsics_array[:, 2].max())],
            "cy_range": [float(intrinsics_array[:, 3].min()), float(intrinsics_array[:, 3].max())],
            "resize_rotation": "identity at frozen 256x192 input resolution",
        },
        "metric": {
            "point_count": int(len(distances_array)),
            "median_m": float(np.median(distances_array)),
            "p95_m": float(np.quantile(distances_array, 0.95)),
            "p99_m": float(np.quantile(distances_array, 0.99)),
            "frames_median_le_0_10_fraction": float(np.mean(np.asarray(frame_medians) <= 0.10)),
            "reprojection_max_px": float(np.max(reprojection_errors)),
            "depth_unit_max_error_m": float(np.max(depth_unit_errors)),
            "nonfinite": 0,
        },
        "frame_records": frame_records,
    }
    gates = {
        "median_le_0_05": summary["metric"]["median_m"] <= 0.05,
        "p95_le_0_15": summary["metric"]["p95_m"] <= 0.15,
        "p99_le_0_30": summary["metric"]["p99_m"] <= 0.30,
        "per_frame_median_fraction_ge_0_80": summary["metric"]["frames_median_le_0_10_fraction"] >= 0.80,
        "reprojection_exact": summary["metric"]["reprojection_max_px"] <= 1e-6,
        "depth_scale_exact": summary["metric"]["depth_unit_max_error_m"] <= 1e-6,
    }
    summary["gates"] = gates
    deterministic_view = {key: value for key, value in summary.items() if key not in {"status"}}
    summary["deterministic_sha256"] = stable_digest(deterministic_view)
    if not all(gates.values()):
        summary["status"] = "FAIL_ARKITSCENES_SPLATAM_LOADER_METRIC_CONTRACT"
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(summary, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(summary["status"])
    print("DETERMINISTIC_SHA256=" + summary["deterministic_sha256"])
    print("METRIC_MEDIAN_M=" + str(summary["metric"]["median_m"]))
    print("METRIC_P95_M=" + str(summary["metric"]["p95_m"]))
    return 0 if summary["status"].startswith("PASS") else 2


if __name__ == "__main__":
    raise SystemExit(main())
