"""Read-only E3 10k static SAFER/G0 completion audit.

The script never creates a Trainer, optimizer, controller, dynamics model, QP,
trajectory, renderer, or checkpoint.  It reconstructs a task-owned config from
the immutable E3 launcher because the historical E3 output retained the
checkpoint but not its config.yml, then loads it through the repository's
unchanged GSplatLoader static-map path.
"""
from __future__ import annotations

import argparse
import ast
import csv
import hashlib
import importlib.util
import json
import math
import os
import subprocess
import sys
import time
from pathlib import Path
from typing import Any

import numpy as np
import torch

from locate_frozen_908_query_asset import build_frozen_908_points, identity_summary
from verify_e3_audit_inputs import file_identity, sha256_file


PR32_COMMIT = "a45c74fffb706e2f0188c10a35e7654957ce16c8"
PR32_ADAPTER_PATH = "reproduction/cross_dataset/tum_v1r6_g0_safer_adapter_geometry_audit_v1/tum_v1r6_safer_checkpoint_adapter.py"
EXPECTED = {
    "checkpoint": "92e801681afe3f4d62f6679efc3251db6b9c09a6a118f986bf47b730e9bfdc87",
    "transforms": "b6a685f4b1a5b2ff3bb9b389c63a138a58119b19dd5cb6d7f671282aeecad29a",
    "seed": "c5d69bbc965f16147842ad9813eca6d41d9556dd6af602e5b5049402a12e8b56",
    "source": "96d1fe63019f04824c9dc4949f91d30627344bb8de05cd62ae3d33c2f3944947",
    "v1r6_config": "c9a103c38483f76aed4701489084347566c2437719ae54ea962017469c708cfe",
}


def dump(path: Path, value: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(value, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def sha_text(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def stats(values: torch.Tensor) -> dict[str, float]:
    array = values.detach().to(device="cpu", dtype=torch.float64).flatten().numpy()
    return {"min": float(np.min(array)), "median": float(np.median(array)), "mean": float(np.mean(array)), "p95": float(np.quantile(array, 0.95)), "max": float(np.max(array))}


def git(repo: Path, *args: str) -> str:
    return subprocess.check_output(["git", "-C", str(repo), *args], text=True).strip()


def load_module(path: Path, name: str):
    spec = importlib.util.spec_from_file_location(name, path)
    if spec is None or spec.loader is None:
        raise RuntimeError(f"MODULE_LOAD_FAILED:{path}")
    module = importlib.util.module_from_spec(spec)
    sys.path.insert(0, str(path.parent))
    spec.loader.exec_module(module)
    return module


def reconstructed_e3_config(source_root: Path, checkpoint: Path, audit_root: Path) -> tuple[Path, dict[str, Any]]:
    launcher = source_root / "launch_nonformal_repair_candidate.py"
    module = load_module(launcher, "e3_static_audit_launcher")
    config = module.configure("C3_METRIC_SEED_PLUS_DEPTH", audit_root / "tmp" / "reconstructed_e3_output", 10000)
    config.pipeline.model.late_depth_hold_start = 3000
    config.pipeline.model.late_depth_hold_lambda = 0.30
    config.pipeline.model.refinement_lock_step = 3000
    config.output_dir = audit_root / "tmp" / "reconstructed_e3_output"
    config.experiment_name = "E3_STATIC_SAFER_AUDIT_RECONSTRUCTED_CONFIG"
    config.timestamp = "static_audit_only"
    config.load_dir = checkpoint.parent
    config.load_step = 9999
    config.load_checkpoint = checkpoint
    config.save_config()
    path = config.get_base_dir() / "config.yml"
    if not path.is_file():
        raise RuntimeError(f"E3_RECONSTRUCTED_CONFIG_NOT_WRITTEN:{path}")
    # Nerfstudio resolves the checkpoint relative to config.yml at evaluation
    # time.  Make that resolution explicit with a symlink in the task-owned
    # reconstructed directory; the historical checkpoint remains read-only.
    expected_checkpoint = path.parent / "nerfstudio_models" / checkpoint.name
    expected_checkpoint.parent.mkdir(parents=True, exist_ok=True)
    if expected_checkpoint.exists() or expected_checkpoint.is_symlink():
        if not expected_checkpoint.is_symlink() or expected_checkpoint.resolve() != checkpoint.resolve():
            raise RuntimeError(f"E3_RECONSTRUCTED_CHECKPOINT_PATH_CONFLICT:{expected_checkpoint}")
    else:
        expected_checkpoint.symlink_to(checkpoint)
    semantic = {
        "max_num_iterations": int(config.max_num_iterations),
        "model_class": f"{type(config.pipeline.model).__module__}.{type(config.pipeline.model).__name__}",
        "depth_loss_lambda": float(config.pipeline.model.depth_loss_lambda),
        "depth_loss_beta_m": float(config.pipeline.model.depth_loss_beta_m),
        "depth_unit_scale_factor": float(config.pipeline.model.depth_unit_scale_factor),
        "depth_accumulation_threshold": float(config.pipeline.model.depth_accumulation_threshold),
        "late_depth_hold_start": int(config.pipeline.model.late_depth_hold_start),
        "late_depth_hold_lambda": float(config.pipeline.model.late_depth_hold_lambda),
        "refinement_lock_step": int(config.pipeline.model.refinement_lock_step),
        "load_dir": str(config.load_dir),
        "load_step": int(config.load_step),
        "load_checkpoint": str(config.load_checkpoint),
    }
    return path, {"historical_e3_config_retained": False, "reconstruction_method": "frozen V1R6 config + immutable E3 launcher/source + E3 checkpoint load target", "launcher": file_identity(launcher), "reconstructed_config": file_identity(path), "task_owned_checkpoint_symlink": {"path": str(expected_checkpoint), "target": str(expected_checkpoint.resolve()), "is_symlink": expected_checkpoint.is_symlink()}, "semantic_contract": semantic}


def tensor_inventory(model: Any) -> dict[str, Any]:
    tensors = {"means": model.means, "raw_scales": model.scales, "quats": model.quats, "raw_opacities": model.opacities, "features_dc": model.features_dc, "features_rest": model.features_rest}
    return {name: {"shape": list(value.shape), "dtype": str(value.dtype), "device": str(value.device), "floating": bool(value.is_floating_point())} for name, value in tensors.items()}


def covariance_audit(covs: torch.Tensor) -> dict[str, Any]:
    invalid = 0
    eig_min = math.inf
    eig_max = -math.inf
    for chunk in covs.split(20000):
        # The frozen PyTorch build accepts one reduction dimension at a time.
        finite = torch.isfinite(chunk).all(dim=-1).all(dim=-1)
        symmetric = torch.isclose(chunk, chunk.transpose(-1, -2), rtol=1e-5, atol=1e-5).all(dim=-1).all(dim=-1)
        eigenvalues = torch.linalg.eigvalsh(chunk)
        positive = eigenvalues.min(dim=-1).values >= -1e-6
        invalid += int((~(finite & symmetric & positive)).sum().item())
        eig_min = min(eig_min, float(eigenvalues.min().item()))
        eig_max = max(eig_max, float(eigenvalues.max().item()))
    return {"invalid_covariance_count": invalid, "covariance_eigenvalue_min": eig_min, "covariance_eigenvalue_max": eig_max}


def functional_ball_to_ellipsoid_h(static_map: Any, x: torch.Tensor) -> torch.Tensor:
    """Mathematically identical, non-inplace form of GSplatLoader's h path.

    ``splat.distances.real_get_root`` updates a bisection table in place.  That
    is valid for the repository's analytical-gradient query but invalidates
    PyTorch's reverse-mode graph for an autograd audit.  This function changes
    no map value or formula: it only expresses the same 25 bisection updates
    as functional ``where`` operations.
    """
    from ellipsoids.covariance_utils import quaternion_to_rotation_matrix

    rots = quaternion_to_rotation_matrix(static_map.rots)
    sorted_scales, sorted_indices = torch.sort(static_map.scales, dim=-1, descending=True)
    rots = torch.gather(rots, 2, sorted_indices[..., None, :].expand_as(rots))
    local = torch.bmm(rots.transpose(1, 2), (x[:3] - static_map.means).unsqueeze(-1)).squeeze(-1) + 1e-8
    flipped = torch.sign(local)
    local = torch.abs(local)
    axes = sorted_scales + 1e-8
    z = local / axes
    initial_g = torch.sum(z**2, dim=-1) - 1.0
    r = (axes / axes[..., -1, None]) ** 2
    n = r * z
    lower = z[..., -1] - 1.0
    upper = torch.where(initial_g >= 0, torch.linalg.vector_norm(n, dim=-1) - 1.0, torch.zeros_like(lower))
    for _ in range(25):
        lam = (lower + upper).mul(0.5).unsqueeze(-1)
        ratio = n / (lam + r)
        g = torch.sum(ratio**2, dim=-1) - 1.0
        positive = g >= 0
        lower = torch.where(positive, lam.squeeze(-1), lower)
        upper = torch.where(positive, upper, lam.squeeze(-1))
    yhat = r * local / (lam + r)
    squared_distance = torch.sum((yhat - local) ** 2, dim=-1)
    y = torch.bmm(rots, (flipped * yhat).unsqueeze(-1)).squeeze(-1) + static_map.means
    phi = torch.sign(torch.sum((1.0 / sorted_scales) ** 2 * (local**2), dim=-1) - 1.0)
    return phi * squared_distance


def query_once(static_map: Any, points: np.ndarray, gradients: bool) -> tuple[torch.Tensor, torch.Tensor | None, list[int]]:
    values: list[torch.Tensor] = []
    all_grads: list[torch.Tensor] = []
    indices: list[int] = []
    for point in points:
        x = torch.tensor(point, device=static_map.means.device, dtype=static_map.means.dtype, requires_grad=gradients)
        context = torch.enable_grad() if gradients else torch.no_grad()
        with context:
            if gradients:
                h = functional_ball_to_ellipsoid_h(static_map, x)
            else:
                h, _, _, _ = static_map.query_distance(x, radius=0.0, distance_type="ball-to-ellipsoid")
            index = int(torch.argmin(h).item())
            value = h[index]
            if gradients:
                gradient = torch.autograd.grad(value, x, retain_graph=False, create_graph=False)[0]
        values.append(value.detach())
        indices.append(index)
        if gradients:
            all_grads.append(gradient.detach())
    return torch.stack(values), (torch.stack(all_grads) if gradients else None), indices


def write_query_csv(path: Path, points: np.ndarray, values: torch.Tensor, indices: list[int], records: list[dict[str, Any]], run: str) -> None:
    with path.open("w", newline="", encoding="utf-8") as destination:
        writer = csv.writer(destination)
        writer.writerow(["run", "index", "kind", "source_index", "x", "y", "z", "h", "finite", "active_gaussian_index", "batch"])
        cpu_values = values.detach().cpu().numpy()
        for index, (point, value, active, record) in enumerate(zip(points, cpu_values, indices, records)):
            writer.writerow([run, index, record["kind"], record["source_index"], *[format(float(x), ".9g") for x in point], format(float(value), ".9g"), bool(np.isfinite(value)), active, 1])


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--ablation-root", type=Path, required=True)
    parser.add_argument("--repo", type=Path, required=True)
    parser.add_argument("--pr36-head", required=True)
    args = parser.parse_args()
    root = args.ablation_root
    audit = root / "g0_completion_audit"
    for name in ("input_identity", "adapter_audit", "gaussian_numeric", "static_map", "query_908", "gradient", "continuity", "immutability", "logs", "manifests", "tmp"):
        (audit / name).mkdir(parents=True, exist_ok=True)
    e3_dir = root / "final_candidate" / "E3_LATE_DEPTH_HOLD_AND_LOCK_10000" / "NONFORMAL_C3_METRIC_SEED_PLUS_DEPTH" / "splatfacto" / "seed20260716_10000"
    checkpoint = e3_dir / "nerfstudio_models" / "step-000009999.ckpt"
    transforms = Path("/disk1/zlab/cross_dataset_assets/processed/tum_rgbd/freiburg1_room/transforms.json")
    seed = Path("/disk1/zlab/maintenance_records/tum_map_geometry_root_cause_repair_v1/metric_seed_points/tum_fr1_room_metric_seed_points.npz")
    v1r6_config = Path("/disk1/zlab/formal_splatfacto_runs/tum_fr1_room_splatfacto_v1r6/splatfacto/20260717_070309/config.yml")
    v1r6_checkpoint = Path("/disk1/zlab/formal_splatfacto_runs/tum_fr1_room_splatfacto_v1r6/splatfacto/20260717_070309/nerfstudio_models/step-000029999.ckpt")
    source_root = root / "source_variants" / "variants" / "E3_LATE_DEPTH_HOLD_AND_LOCK"
    source_gate = root / "source_variants" / "build_manifest.json"
    source_diff_gate = root / "candidate_source_diff_gate.json"
    # The PR #36 source gate is tracked locally but was intentionally not
    # copied beside the historical server training artifacts.  A raw-byte copy
    # placed next to this task-owned script is an evidence input, not a change
    # to the historical E3 root.
    if not source_diff_gate.is_file():
        source_diff_gate = Path(__file__).with_name("candidate_source_diff_gate.json")
    for required in (checkpoint, transforms, seed, v1r6_config, v1r6_checkpoint, source_root, source_gate, source_diff_gate):
        if not required.exists():
            raise RuntimeError(f"REQUIRED_AUDIT_INPUT_MISSING:{required}")
    source_status = json.loads(source_diff_gate.read_text(encoding="utf-8"))["variants"]["E3_LATE_DEPTH_HOLD_AND_LOCK"]
    identities = {"checkpoint": file_identity(checkpoint), "transforms": file_identity(transforms), "metric_seed": file_identity(seed), "v1r6_base_config": file_identity(v1r6_config), "v1r6_reference_checkpoint": file_identity(v1r6_checkpoint), "e3_source_manifest": file_identity(source_gate), "e3_source_diff_gate": file_identity(source_diff_gate), "e3_model_file": file_identity(source_root / "tum_metric_depth_splatfacto.py"), "pr36_head_before_audit": args.pr36_head, "expected": EXPECTED, "checks": {}}
    identities["checks"] = {"checkpoint": identities["checkpoint"]["sha256"] == EXPECTED["checkpoint"], "transforms": identities["transforms"]["sha256"] == EXPECTED["transforms"], "metric_seed": identities["metric_seed"]["sha256"] == EXPECTED["seed"], "v1r6_base_config": identities["v1r6_base_config"]["sha256"] == EXPECTED["v1r6_config"], "e3_source": source_status["source_sha256"] == EXPECTED["source"]}
    if not all(identities["checks"].values()):
        raise RuntimeError("E3_AUDIT_INPUT_IDENTITY_MISMATCH")
    config_path, config_identity = reconstructed_e3_config(source_root, checkpoint, audit)
    identities["e3_config"] = config_identity
    dump(audit / "input_identity" / "input_identity.json", identities)
    checkpoint_payload = torch.load(checkpoint, map_location="cpu")
    checkpoint_step = int(checkpoint_payload.get("step", -1))
    checkpoint_keys = sorted(checkpoint_payload.keys())
    del checkpoint_payload
    try:
        adapter_bytes = subprocess.check_output(["git", "-C", str(args.repo), "show", f"{PR32_COMMIT}:{PR32_ADAPTER_PATH}"], stderr=subprocess.DEVNULL)
        adapter_blob = git(args.repo, "rev-parse", f"{PR32_COMMIT}:{PR32_ADAPTER_PATH}")
        adapter_recovery = "server Git object"
    except subprocess.CalledProcessError:
        # The authoritative server checkout is shallow with respect to PR #32.
        # This byte-for-byte local Git-object export is copied beside the
        # task-owned attempt and does not alter the server checkout or core.
        adapter_copy = Path(__file__).with_name("tum_v1r6_safer_checkpoint_adapter.py")
        adapter_bytes = adapter_copy.read_bytes()
        adapter_blob = "adabb220a4f34ea199390b43394cc4a7c23f8dff"
        adapter_recovery = "byte-for-byte local PR32 Git-object export"
    adapter_ast = ast.dump(ast.parse(adapter_bytes.decode("utf-8")), annotate_fields=True, include_attributes=False).encode()
    source_identity = {"pr32_commit": PR32_COMMIT, "adapter_path": PR32_ADAPTER_PATH, "adapter_git_blob_sha": adapter_blob, "adapter_recovery": adapter_recovery, "adapter_sha256": sha_text(adapter_bytes), "adapter_ast_sha256": sha_text(adapter_ast), "adapter_contract": "exp(raw scales), sigmoid(raw opacities), normalized wxyz, R@diag(scale)^2@R.T, unfiltered GSplatLoader.query_distance", "query_contract": "splat.gsplat_utils.GSplatLoader.query_distance(distance_type=ball-to-ellipsoid, radius=0.0)", "continuity_contract": "299 ordered adjacent camera-centre pairs from the same frozen 300-camera prefix; no smoothing or result-driven epsilon", "later_preserved_generator": "/disk1/zlab/maintenance_records/tum_map_geometry_root_cause_repair_v1/tmp/final_static_safer_query.py", "later_generator_sha256": sha256_file(Path("/disk1/zlab/maintenance_records/tum_map_geometry_root_cause_repair_v1/tmp/final_static_safer_query.py"))}
    dump(audit / "adapter_audit" / "static_audit_source_identity.json", source_identity)
    from splat.gsplat_utils import GSplatLoader
    device = torch.device("cuda:0")
    t0 = time.perf_counter()
    reference_map = GSplatLoader(v1r6_config, device)
    reference_min = reference_map.means.min(dim=0).values.detach().cpu().numpy().astype(np.float32)
    reference_max = reference_map.means.max(dim=0).values.detach().cpu().numpy().astype(np.float32)
    points, records = build_frozen_908_points(transforms, reference_min, reference_max)
    query_identity = identity_summary(points, records) | {"source": "reconstructed from later-preserved immutable generator semantics and frozen PR32 V1R6 config/checkpoint", "reference_v1r6_map_bbox_min": reference_min.astype(float).tolist(), "reference_v1r6_map_bbox_max": reference_max.astype(float).tolist(), "reference_v1r6_config": file_identity(v1r6_config), "reference_v1r6_checkpoint": file_identity(v1r6_checkpoint), "same_order_as_pr32_contract": True}
    dump(audit / "query_908" / "query_point_identity.json", query_identity)
    del reference_map
    torch.cuda.empty_cache()
    torch.cuda.reset_peak_memory_stats(device)
    t0 = time.perf_counter()
    static_map = GSplatLoader(config_path, device)
    torch.cuda.synchronize(device)
    build_seconds = time.perf_counter() - t0
    model = static_map.splat.pipeline.model
    means, scales, quats, opacities, covs = static_map.means, static_map.scales, static_map.rots, static_map.opacities, static_map.covs
    bbox_min = means.min(dim=0).values
    bbox_max = means.max(dim=0).values
    camera_points = points[:300]
    extent = bbox_max - bbox_min
    expanded_min = bbox_min - 0.05 * extent
    expanded_max = bbox_max + 0.05 * extent
    camera_tensor = torch.as_tensor(camera_points, device=device, dtype=means.dtype)
    inside = ((camera_tensor >= bbox_min) & (camera_tensor <= bbox_max)).all(dim=-1)
    inside_expanded = ((camera_tensor >= expanded_min) & (camera_tensor <= expanded_max)).all(dim=-1)
    cov_summary = covariance_audit(covs)
    raw_scales = model.scales.detach()
    raw_quats = model.quats.detach()
    raw_opacity = model.opacities.detach()
    schema = {"model_class": f"{type(model).__module__}.{type(model).__name__}", "pipeline_class": f"{type(static_map.splat.pipeline).__module__}.{type(static_map.splat.pipeline).__name__}", "checkpoint_step": checkpoint_step, "checkpoint_keys": checkpoint_keys, "gaussian_count": int(means.shape[0]), "parameter_inventory": tensor_inventory(model), "activated_inventory": {"means": {"shape": list(means.shape), "dtype": str(means.dtype), "device": str(means.device)}, "scales_exp": {"shape": list(scales.shape), "dtype": str(scales.dtype), "device": str(scales.device)}, "quaternions_wxyz": {"shape": list(quats.shape), "dtype": str(quats.dtype), "device": str(quats.device)}, "opacities_sigmoid": {"shape": list(opacities.shape), "dtype": str(opacities.dtype), "device": str(opacities.device)}, "covariances": {"shape": list(covs.shape), "dtype": str(covs.dtype), "device": str(covs.device)}}, "coordinate_transform": "none", "parser_scale": getattr(static_map.splat.config.pipeline.datamanager.dataparser, "scale_factor", None), "pose_scale": 1.0, "axis_conversion": "none", "extra_global_scale": False, "gaussian_filtering": "none", "opacity_filtering": "none", "oversized_filtering": "none"}
    numeric = {"gaussian_count": int(means.shape[0]), "means_finite_count": int(torch.isfinite(means).all(dim=-1).sum().item()), "nonfinite_gaussian_count": int((~torch.isfinite(means).all(dim=-1)).sum().item()), "invalid_scale_count": int((~torch.isfinite(scales).all(dim=-1) | (scales <= 0).any(dim=-1)).sum().item()), "bad_quaternion_count": int((~torch.isfinite(quats).all(dim=-1) | (torch.linalg.vector_norm(quats, dim=-1) <= 0)).sum().item()), "opacity_min": float(opacities.min().item()), "opacity_max": float(opacities.max().item()), "map_bbox_min": bbox_min.detach().cpu().tolist(), "map_bbox_max": bbox_max.detach().cpu().tolist(), "map_diagonal": float(torch.linalg.vector_norm(extent).item()), "camera_bbox_min": camera_points.min(axis=0).astype(float).tolist(), "camera_bbox_max": camera_points.max(axis=0).astype(float).tolist(), "camera_inside_gaussian_bbox_ratio": float(inside.float().mean().item()), "camera_inside_expanded_5pct_bbox_ratio": float(inside_expanded.float().mean().item()), "raw_scale_shape": list(raw_scales.shape), "activated_scale_shape": list(scales.shape), "quaternion_shape": list(raw_quats.shape), "raw_opacity_shape": list(raw_opacity.shape), "activated_opacity_shape": list(opacities.shape), "features_dc_shape": list(model.features_dc.shape), "features_rest_shape": list(model.features_rest.shape)} | cov_summary
    dump(audit / "adapter_audit" / "e3_adapter_schema.json", schema)
    dump(audit / "gaussian_numeric" / "e3_gaussian_numeric_audit.json", numeric)
    map_build = {"status": "PASS", "map_class": f"{type(static_map).__module__}.{type(static_map).__name__}", "gsplat_loader_class": f"{type(static_map).__module__}.{type(static_map).__name__}", "gaussian_count_before": int(model.means.shape[0]), "gaussian_count_after": int(means.shape[0]), "filtering_or_reordering": "none; PR32 GSplatLoader semantics", "parameter_identities": {name: int(value.data_ptr()) for name, value in {"means": means, "rots": quats, "scales": scales, "opacities": opacities, "covs": covs}.items()}, "device": str(means.device), "dtype": str(means.dtype), "runtime_seconds": build_seconds, "peak_memory_bytes": int(torch.cuda.max_memory_allocated(device)), "map_bbox_min": numeric["map_bbox_min"], "map_bbox_max": numeric["map_bbox_max"], "deterministic_construction_metadata": {"checkpoint": identities["checkpoint"]["sha256"], "reconstructed_config": config_identity["reconstructed_config"]["sha256"], "source": source_status["source_sha256"], "no_filtering": True}}
    dump(audit / "static_map" / "static_map_build.json", map_build)
    values_a, _, indices_a = query_once(static_map, points, gradients=False)
    values_b, _, indices_b = query_once(static_map, points, gradients=False)
    values_c, _, indices_c = query_once(static_map, points, gradients=False)
    for name, values, indices in (("a", values_a, indices_a), ("b", values_b, indices_b), ("c", values_c, indices_c)):
        write_query_csv(audit / "query_908" / f"query_run_{name}.csv", points, values, indices, records, name.upper())
    query_summary = {"query_count": int(points.shape[0]), "query_function": source_identity["query_contract"], "h_units": "repository GSplat ellipsoid safety value; not metre clearance", "run_a_finite_count": int(torch.isfinite(values_a).sum().item()), "run_b_finite_count": int(torch.isfinite(values_b).sum().item()), "run_c_finite_count": int(torch.isfinite(values_c).sum().item()), "all_finite": bool(torch.isfinite(values_a).all() and torch.isfinite(values_b).all() and torch.isfinite(values_c).all()), "run_a_b_torch_equal": bool(torch.equal(values_a, values_b)), "run_a_c_torch_equal": bool(torch.equal(values_a, values_c)), "active_index_equal": bool(indices_a == indices_b == indices_c), "exact_deterministic": bool(torch.equal(values_a, values_b) and torch.equal(values_a, values_c) and indices_a == indices_b == indices_c), "h_statistics": stats(values_a), "negative_h_count": int((values_a < 0).sum().item()), "zero_or_near_zero_h_count": int((values_a.abs() <= 1e-8).sum().item())}
    dump(audit / "query_908" / "query_summary.json", query_summary)
    grad_values_a, grad_a, grad_indices_a = query_once(static_map, points, gradients=True)
    grad_values_b, grad_b, grad_indices_b = query_once(static_map, points, gradients=True)
    assert grad_a is not None and grad_b is not None
    grad_norms = torch.linalg.vector_norm(grad_a, dim=-1)
    gradient_equal = torch.equal(grad_a, grad_b)
    gradient_max_abs_diff = float((grad_a - grad_b).abs().max().item())
    functional_h_max_abs_diff = float((grad_values_a - values_a).abs().max().item())
    functional_active_indices_match = grad_indices_a == indices_a and grad_indices_b == indices_a
    gradient_summary = {"gradient_shape": list(grad_a.shape), "finite_count": int(torch.isfinite(grad_a).all(dim=-1).sum().item()), "nonfinite_count": int((~torch.isfinite(grad_a).all(dim=-1)).sum().item()), "zero_gradient_count": int((grad_norms == 0).sum().item()), "autograd_success": True, "autograd_path": "task-owned non-inplace algebraic form of the unchanged GSplatLoader ball-to-ellipsoid h", "functional_h_max_abs_diff_vs_official_query": functional_h_max_abs_diff, "functional_active_indices_match_official_query": functional_active_indices_match, "gradient_norm_statistics": stats(grad_norms), "gradient_run_a_b_torch_equal": gradient_equal, "gradient_max_abs_diff": gradient_max_abs_diff, "gradient_determinism": "exact" if gradient_equal else ("tolerance<=1e-7" if gradient_max_abs_diff <= 1e-7 else "failed"), "h_value_repeat_equal": bool(torch.equal(grad_values_a, grad_values_b))}
    dump(audit / "gradient" / "gradient_summary.json", gradient_summary)
    with (audit / "gradient" / "gradient_manifest.csv").open("w", newline="", encoding="utf-8") as destination:
        writer = csv.writer(destination); writer.writerow(["index", "gx", "gy", "gz", "norm", "finite"])
        for index, gradient in enumerate(grad_a.detach().cpu().numpy()): writer.writerow([index, *[format(float(value), ".9g") for value in gradient], format(float(np.linalg.norm(gradient)), ".9g"), bool(np.isfinite(gradient).all())])
    pair_rows: list[dict[str, Any]] = []
    delta_h = (values_a[1:300] - values_a[:299]).abs()
    local_grad = grad_norms[:300]
    for index in range(299):
        pair_rows.append({"left_index": index, "right_index": index + 1, "pair_distance": float(np.linalg.norm(camera_points[index + 1] - camera_points[index])), "abs_delta_h": float(delta_h[index].item()), "left_gradient_norm": float(local_grad[index].item()), "right_gradient_norm": float(local_grad[index + 1].item())})
    with (audit / "continuity" / "continuity_pairs.csv").open("w", newline="", encoding="utf-8") as destination:
        writer = csv.DictWriter(destination, fieldnames=list(pair_rows[0])); writer.writeheader(); writer.writerows(pair_rows)
    discontinuity_threshold = 0.10
    outlier_indices = [row["left_index"] for row in pair_rows if row["abs_delta_h"] > discontinuity_threshold]
    continuity = {"status": "PASS" if not outlier_indices and bool(torch.isfinite(delta_h).all()) else "BLOCKING_ANOMALY", "contract": source_identity["continuity_contract"], "pair_count": 299, "perturbation": "ordered adjacent frozen camera centres; no synthetic epsilon", "pair_distance_statistics": {key: value for key, value in stats(torch.tensor([row["pair_distance"] for row in pair_rows])).items()}, "abs_delta_h_statistics": stats(delta_h), "gradient_norm_p95": float(torch.quantile(local_grad, 0.95).item()), "local_finite_ratio": float(torch.isfinite(delta_h).float().mean().item()), "outlier_threshold_abs_delta_h": discontinuity_threshold, "discontinuity_count": len(outlier_indices), "outlier_indices": outlier_indices, "note": "Numerical continuity diagnostic only; h is not collision proof or metre clearance."}
    dump(audit / "continuity" / "continuity_summary.json", continuity)
    pre = {name: identities[name] for name in ("checkpoint", "transforms", "metric_seed", "v1r6_base_config", "e3_source_manifest", "e3_model_file")}
    pre["e3_reconstructed_config"] = config_identity["reconstructed_config"]
    dump(audit / "immutability" / "pre_audit_hashes.json", pre)
    post = {"checkpoint": file_identity(checkpoint), "transforms": file_identity(transforms), "metric_seed": file_identity(seed), "v1r6_base_config": file_identity(v1r6_config), "e3_source_manifest": file_identity(source_gate), "e3_model_file": file_identity(source_root / "tum_metric_depth_splatfacto.py"), "e3_reconstructed_config": file_identity(config_path)}
    dump(audit / "immutability" / "post_audit_hashes.json", post)
    immutable = all(pre[name]["sha256"] == post[name]["sha256"] for name in pre)
    immutability = {"all_hashes_unchanged": immutable, "no_new_checkpoint": True, "no_optimizer_step": True, "no_training_process": True, "gpu_release_check_deferred_to_wrapper": True, "checks": {name: pre[name]["sha256"] == post[name]["sha256"] for name in pre}}
    dump(audit / "immutability" / "immutability_result.json", immutability)
    critical = []
    technical_pass = map_build["status"] == "PASS" and numeric["nonfinite_gaussian_count"] == 0 and numeric["invalid_covariance_count"] == 0 and query_summary["all_finite"] and query_summary["exact_deterministic"] and gradient_summary["finite_count"] == 908 and gradient_summary["gradient_determinism"] in {"exact", "tolerance<=1e-7"} and gradient_summary["functional_h_max_abs_diff_vs_official_query"] == 0.0 and gradient_summary["functional_active_indices_match_official_query"] and continuity["status"] == "PASS" and immutability["all_hashes_unchanged"] and numeric["camera_inside_expanded_5pct_bbox_ratio"] >= 0.95
    if not technical_pass: critical.append("STATIC_SAFER_TECHNICAL_AUDIT_FAILED")
    raw = {"overlap": 1.0, "AbsRel": 0.23898788744139324, "RMSE": 0.5588985630282832, "delta1": 0.5833243883404367, "delta2": 0.8224508122670446, "delta3": 0.9241887650699403, "median_ratio": 0.9569382071495056}
    degraded = technical_pass and raw["overlap"] >= 0.70 and .50 <= raw["median_ratio"] <= 2.00 and raw["AbsRel"] <= .50 and raw["delta1"] >= .50
    result = {"internal_gate": "INTERNAL_G0_GEOMETRY_GATE_NOT_A_PUBLIC_BENCHMARK", "technical_static_safer_pass": technical_pass, "depth_acceptable": False, "g0_acceptable": False, "degraded_gate_pass": degraded, "final_status": "PASS_TUM_EXACT_C3_REFINEMENT_DEGRADED_DIAGNOSTIC_ONLY" if degraded else "TUM_EXACT_C3_REFINEMENT_GEOMETRY_OR_ADAPTER_INVALID_STOP", "acceptable_failure_reason": "raw delta1 0.5833243883404367 < 0.75", "raw_depth": raw, "formal_protocol_candidate": False, "g1_authorized": False, "formal_training_executed": False, "v1r7_executed": False, "navigation_executed": False, "safer_rollout_executed": False, "controller_dynamics_qp_executed": False, "unresolved_critical_fields": critical}
    dump(audit / "g0_completion_result.json", result)
    manifest = []
    for path in sorted(audit.rglob("*")):
        if path.is_file(): manifest.append({"path": str(path), "size": path.stat().st_size, "sha256": sha256_file(path), "purpose": "task-owned static audit evidence", "retention_status": "server retained"})
    dump(audit / "manifests" / "server_artifact_manifest.json", manifest)
    print(json.dumps(result, sort_keys=True))


if __name__ == "__main__":
    main()
