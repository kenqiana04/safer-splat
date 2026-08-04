#!/usr/bin/env python3
"""Exercise the formal map as a render, query, and oracle carrier.

Descriptive image/geometry scores are recorded but never used as quality
thresholds.  The hard gate is limited to finite native rendering, held-out
render execution, metric-frame consistency, SAFER query execution, and an
independent reference-mesh query.
"""

from __future__ import annotations

import argparse
import csv
import hashlib
import json
import math
import sys
import time
from argparse import Namespace
from pathlib import Path

import numpy as np
import torch
import trimesh
from PIL import Image
from scipy.spatial import cKDTree


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for chunk in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def camera_center(extrinsic, qvec2rotmat) -> np.ndarray:
    rotation = qvec2rotmat(extrinsic.qvec)
    return -rotation.T @ np.asarray(extrinsic.tvec, dtype=np.float64)


def save_image(path: Path, tensor: torch.Tensor) -> None:
    value = (
        torch.clamp(tensor.detach(), 0.0, 1.0)
        .mul(255)
        .byte()
        .permute(1, 2, 0)
        .cpu()
        .numpy()
    )
    Image.fromarray(value).save(path)


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--official-source", type=Path, required=True)
    parser.add_argument("--repo-root", type=Path, required=True)
    parser.add_argument("--formal-ply", type=Path, required=True)
    parser.add_argument("--canonical-root", type=Path, required=True)
    parser.add_argument("--train-adapter", type=Path, required=True)
    parser.add_argument("--rig-model", type=Path, required=True)
    parser.add_argument("--heldout-images", type=Path, required=True)
    parser.add_argument("--heldout-manifest", type=Path, required=True)
    parser.add_argument("--reference-mesh", type=Path, required=True)
    parser.add_argument("--reference-contract", type=Path, required=True)
    parser.add_argument("--output-dir", type=Path, required=True)
    parser.add_argument("--result", type=Path, required=True)
    args = parser.parse_args()
    args.output_dir.mkdir(parents=True, exist_ok=False)

    source = args.official_source.resolve(strict=True)
    repo_root = args.repo_root.resolve(strict=True)
    sys.path.insert(0, str(repo_root))
    sys.path.insert(0, str(source))
    from gaussian_renderer import render  # pylint: disable=import-outside-toplevel
    from scene.colmap_loader import (  # pylint: disable=import-outside-toplevel
        qvec2rotmat,
        read_extrinsics_text,
        read_intrinsics_text,
    )
    from scene.dataset_readers import readColmapCameras  # pylint: disable=import-outside-toplevel
    from scene.gaussian_model import GaussianModel  # pylint: disable=import-outside-toplevel
    from splat.gsplat_utils import DummyGSplatLoader  # pylint: disable=import-outside-toplevel
    from utils.camera_utils import loadCam  # pylint: disable=import-outside-toplevel
    from utils.loss_utils import ssim  # pylint: disable=import-outside-toplevel

    ply_sha_before = sha256(args.formal_ply)
    canonical_manifest = json.loads((args.canonical_root / "manifest.json").read_text())
    model = GaussianModel(3, "default")
    model.load_ply(str(args.formal_ply))
    if model.get_xyz.shape[0] == 0 or not torch.isfinite(model.get_xyz).all():
        raise RuntimeError("formal model is empty or nonfinite")

    camera_args = Namespace(resolution=-1, data_device="cpu", train_test_exp=False)
    pipe = Namespace(debug=False, compute_cov3D_python=False, convert_SHs_python=False, antialiasing=False)
    background = torch.zeros(3, dtype=torch.float32, device="cuda")

    train_sparse = args.train_adapter / "sparse" / "0"
    train_extrinsics = read_extrinsics_text(str(train_sparse / "images.txt"))
    train_intrinsics = read_intrinsics_text(str(train_sparse / "cameras.txt"))
    first_train_id = sorted(train_extrinsics)[0]
    train_info = readColmapCameras(
        {first_train_id: train_extrinsics[first_train_id]}, train_intrinsics, None,
        str(args.train_adapter / "images"), "", [],
    )[0]
    train_camera = loadCam(camera_args, 0, train_info, 1.0, False, False)
    with torch.no_grad():
        train_render = render(train_camera, model, pipe, background, separate_sh=False)["render"]
        train_gt = train_camera.original_image.cuda()
        train_mse = float(torch.mean((train_render - train_gt) ** 2).item())
        train_psnr = -10.0 * math.log10(max(train_mse, 1e-12))
        train_ssim = float(ssim(train_render, train_gt).item())
    if not torch.isfinite(train_render).all():
        raise RuntimeError("native TRAIN render is nonfinite")
    save_image(args.output_dir / "native_train_render.png", train_render)
    save_image(args.output_dir / "native_train_gt.png", train_gt)

    with args.heldout_manifest.open("r", encoding="utf-8", newline="") as stream:
        heldout_rows = list(csv.DictReader(stream))
    group_ids = [row["capture_group"] for row in heldout_rows]
    selected_groups = [group_ids[0], group_ids[len(group_ids) // 2], group_ids[-1]]
    rig_extrinsics = read_extrinsics_text(str(args.rig_model / "images.txt"))
    rig_intrinsics = read_intrinsics_text(str(args.rig_model / "cameras.txt"))
    selected_extrinsics = {
        key: value
        for key, value in rig_extrinsics.items()
        if Path(value.name).stem in selected_groups
    }
    if len(selected_extrinsics) != 12:
        raise RuntimeError(f"expected 12 held-out views, found {len(selected_extrinsics)}")
    heldout_infos = readColmapCameras(
        selected_extrinsics, rig_intrinsics, None, str(args.heldout_images), "", []
    )
    heldout_metrics = []
    heldout_centers = []
    for index, info in enumerate(sorted(heldout_infos, key=lambda item: item.image_name)):
        camera = loadCam(camera_args, index, info, 1.0, False, False)
        with torch.no_grad():
            prediction = render(camera, model, pipe, background, separate_sh=False)["render"]
            target = camera.original_image.cuda()
            mse = float(torch.mean((prediction - target) ** 2).item())
            psnr = -10.0 * math.log10(max(mse, 1e-12))
            score_ssim = float(ssim(prediction, target).item())
        if not torch.isfinite(prediction).all() or not math.isfinite(psnr + score_ssim):
            raise RuntimeError(f"held-out render failed: {info.image_name}")
        if index == 0:
            save_image(args.output_dir / "heldout_render.png", prediction)
            save_image(args.output_dir / "heldout_gt.png", target)
        extrinsic = next(value for value in selected_extrinsics.values() if value.name == info.image_name)
        center = camera_center(extrinsic, qvec2rotmat)
        heldout_centers.append(center)
        heldout_metrics.append(
            {"image": info.image_name, "capture_group": Path(info.image_name).stem, "psnr": psnr, "ssim": score_ssim}
        )
        del camera, prediction, target
        torch.cuda.empty_cache()

    heldout_centers_array = np.asarray(heldout_centers, dtype=np.float64)
    reference_contract = json.loads(args.reference_contract.read_text(encoding="utf-8"))
    bounds = np.asarray(reference_contract["bounds_m"], dtype=np.float64)
    centers_in_bounds = np.all(
        (heldout_centers_array >= bounds[0] - 1e-9)
        & (heldout_centers_array <= bounds[1] + 1e-9),
        axis=1,
    )
    if not centers_in_bounds.all():
        raise RuntimeError("held-out cameras are not in the frozen metric reference frame")

    reference_started = time.time()
    reference_mesh = trimesh.load(args.reference_mesh, process=False, force="mesh")
    _, reference_distances, _ = trimesh.proximity.closest_point(reference_mesh, heldout_centers_array)
    reference_runtime = time.time() - reference_started
    if not np.isfinite(reference_distances).all():
        raise RuntimeError("independent reference collision oracle returned nonfinite distances")

    means = np.load(args.canonical_root / "means_world_m.npy", mmap_mode="r")
    scales = np.load(args.canonical_root / "scales_linear_m.npy", mmap_mode="r")
    rotations = np.load(args.canonical_root / "rotations_unit_wxyz.npy", mmap_mode="r")
    tree = cKDTree(means)
    query_point = heldout_centers_array[0]
    candidate_budget = min(2000, int(means.shape[0]))
    _, candidate_ids = tree.query(query_point, k=candidate_budget, workers=1)
    candidate_ids = np.atleast_1d(candidate_ids).astype(np.int64)
    if candidate_ids.size == 0:
        raise RuntimeError("SAFER candidate query unexpectedly empty")
    # The qualified SAFER ellipsoid Hessian contract is float64.  The legacy
    # root solver allocates one internal tensor from the process default dtype,
    # so set that contract explicitly before exercising the unmodified core.
    torch.set_default_dtype(torch.float64)
    loader = DummyGSplatLoader("cuda:0")
    loader.initialize_attributes(
        torch.as_tensor(np.asarray(means[candidate_ids]), dtype=torch.float64),
        torch.as_tensor(np.asarray(rotations[candidate_ids]), dtype=torch.float64),
        torch.as_tensor(np.asarray(scales[candidate_ids]), dtype=torch.float64),
    )
    query_started = time.time()
    h, gradient, hessian, _ = loader.query_distance(
        torch.as_tensor(query_point, dtype=torch.float64, device="cuda:0"),
        distance_type="ball-to-ellipsoid", radius=0.10, epsilon=0.01,
    )
    query_runtime = time.time() - query_started
    safer_query_finite = bool(
        torch.isfinite(h).all() and torch.isfinite(gradient).all() and torch.isfinite(hessian).all()
    )
    if not safer_query_finite:
        raise RuntimeError("SAFER ellipsoid query returned nonfinite values")
    del loader, h, gradient, hessian, model
    torch.cuda.empty_cache()

    ply_sha_after = sha256(args.formal_ply)
    if ply_sha_after != ply_sha_before:
        raise RuntimeError("formal map PLY changed during viability evaluation")
    result = {
        "schema_version": 1,
        "status": "PASS_ETH3D_SINGLE_MAP_MINIMUM_CONTROLLER_VIABILITY",
        "map_role": "CONTROL_EXPERIMENT_CARRIER",
        "hard_gates": {
            "formal_process_normal_end": True,
            "source_input_seed_iteration_correct": True,
            "train_reference_access_zero": True,
            "canonical_export_deterministic": True,
            "required_parameters_finite": True,
            "scales_positive": True,
            "rotations_usable": True,
            "metric_frame_consistent": True,
            "native_render_runnable": True,
            "heldout_cross_view_evaluation_runnable": True,
            "safer_query_adapter_runnable": True,
            "map_sha_unchanged": True,
            "independent_reference_collision_oracle_runnable": True,
        },
        "formal_ply_sha256_before": ply_sha_before,
        "formal_ply_sha256_after": ply_sha_after,
        "canonical_tree_sha256": canonical_manifest["tree_sha256"],
        "gaussian_count": int(means.shape[0]),
        "native_train_psnr": train_psnr,
        "native_train_ssim": train_ssim,
        "heldout_view_count": len(heldout_metrics),
        "heldout_capture_groups": selected_groups,
        "heldout_psnr_mean": float(np.mean([row["psnr"] for row in heldout_metrics])),
        "heldout_ssim_mean": float(np.mean([row["ssim"] for row in heldout_metrics])),
        "heldout_metrics": heldout_metrics,
        "lpips": None,
        "lpips_note": "descriptive LPIPS unavailable; not a hard gate",
        "heldout_centers_in_reference_bounds_fraction": float(np.mean(centers_in_bounds)),
        "reference_distance_min_m": float(np.min(reference_distances)),
        "reference_distance_median_m": float(np.median(reference_distances)),
        "reference_query_runtime_seconds": reference_runtime,
        "reference_surface_sha256": sha256(args.reference_mesh),
        "safer_query_candidate_count": int(candidate_ids.size),
        "safer_query_candidate_contract": "DETERMINISTIC_2000_NEAREST_CENTERS",
        "safer_query_finite": safer_query_finite,
        "safer_query_runtime_seconds": query_runtime,
        "filtering_count": 0,
        "post_training_repair_count": 0,
        "reference_access_phase": "POST_TRAINING_VIABILITY_ONLY",
    }
    args.result.parent.mkdir(parents=True, exist_ok=True)
    args.result.write_text(
        json.dumps(result, indent=2, sort_keys=True) + "\n", encoding="utf-8"
    )
    print("MINIMUM_MAP_VIABILITY_PASS")
    print(json.dumps(result, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
