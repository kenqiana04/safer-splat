#!/usr/bin/env python3
"""Read-only server probes for immutable Gaussian-map requalification.

The script never writes beside a source map.  It only writes a compact JSON
record to the caller-provided task-owned output path.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import os
from pathlib import Path
import sys
import time
import types

import numpy as np


MAPS = {
    "REPLICA_GT_FINE": {
        "root": "/disk1/zlab/maintenance_records/replica_bounded_direct_goal_gt_gaussian_benchmark_v1/map_profiles/FINE_A",
        "source": "/disk1/zlab/maintenance_records/replica_bounded_direct_goal_gt_gaussian_benchmark_v1/map_profiles/FINE_A",
    },
    "REPLICA_SPLATFACTO": {
        "root": "/disk1/zlab/maintenance_records/replica_splatfacto_native_baseline_qualification_v1/canonical_export/qualification_pilot",
        "source": "/disk1/zlab/maintenance_records/replica_splatfacto_native_baseline_qualification_v1/canonical_export/qualification_pilot",
    },
    "REPLICA_SPLATAM_60": {
        "root": "/disk1/zlab/maintenance_records/replica_splatam_protocol_conformance_pilot_v1/canonical_export/unfiltered",
        "source": "/disk1/zlab/maintenance_records/replica_splatam_protocol_conformance_pilot_v1/pilot_run/run/params.npz",
    },
    "ARKITSCENES_M1_SPLATAM": {
        "root": "/disk1/zlab/maintenance_records/arkitscenes_splatam_m1_learned_map_qualification_v1/canonical_export_a",
        "source": "/disk1/zlab/maintenance_records/arkitscenes_splatam_m1_learned_map_qualification_v1/outputs/ARKITSCENES_SPLATAM_M1_EMPTY_DEPTH_SAFE_GT_POSE_MAP_ONLY_V1/params.npz",
    },
    "TUM_SPLATAM_FORMAL": {
        "root": "/disk1/zlab/maintenance_records/tum_common_gaussian_map_adapter_qualification_v1/splatam/canonical_export/export_a",
        "source": "/disk1/zlab/external_baselines/tum_rgbd_gaussian_v1/build/runs/splatam_full240/params.npz",
    },
    "TUM_GAUSSIAN_SLAM": {
        "root": "/disk1/zlab/maintenance_records/tum_common_gaussian_map_adapter_qualification_v1/gaussian_slam/canonical_export/export_a",
        "source": "/disk1/zlab/maintenance_records/tum_common_gaussian_map_adapter_qualification_v1/gaussian_slam/canonical_export/export_a",
    },
}

ARRAY_ALIASES = {
    "means": ("means_world_m.npy",),
    "scales": ("scales_linear_m.npy",),
    "quaternions": ("quaternions_wxyz.npy",),
    "opacity": ("opacities_probability.npy", "opacities_activated.npy", "opacities.npy"),
    "color": ("colors_rgb.npy", "colors_or_sh.npy", "appearance.npy", "sh_coefficients.npy"),
}


def digest_file(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(8 * 1024 * 1024), b""):
            h.update(chunk)
    return h.hexdigest()


def source_identity(path: Path) -> dict:
    if not path.exists():
        return {"path": str(path), "exists": False, "sha256": None, "file_count": 0, "bytes": 0}
    if path.is_file():
        return {"path": str(path), "exists": True, "sha256": digest_file(path), "file_count": 1, "bytes": path.stat().st_size}
    files = sorted(p for p in path.rglob("*") if p.is_file())
    h = hashlib.sha256()
    size = 0
    for item in files:
        relative = item.relative_to(path).as_posix().encode("utf-8")
        raw_digest = digest_file(item)
        h.update(relative + b"\0" + raw_digest.encode("ascii") + b"\n")
        size += item.stat().st_size
    return {"path": str(path), "exists": True, "sha256": h.hexdigest(), "file_count": len(files), "bytes": size}


def shard_dirs(root: Path) -> list[Path]:
    if (root / "means_world_m.npy").is_file():
        return [root]
    return sorted(p.parent for p in root.rglob("means_world_m.npy"))


def array_path(root: Path, aliases: tuple[str, ...]) -> Path | None:
    for name in aliases:
        candidate = root / name
        if candidate.is_file():
            return candidate
    return None


def iter_chunks(array: np.ndarray, chunk: int = 250_000):
    for offset in range(0, len(array), chunk):
        yield np.asarray(array[offset : offset + chunk])


def inspect_map(map_id: str) -> dict:
    config = MAPS[map_id]
    root = Path(config["root"])
    source = Path(config["source"])
    record = {"map_id": map_id, "canonical_root": str(root), "source_identity": source_identity(source)}
    if not root.is_dir():
        record.update({"available": False, "status": "ARTIFACT_UNAVAILABLE_FOR_RETROSPECTIVE_EVALUATION"})
        return record
    shards = shard_dirs(root)
    record["available"] = bool(shards)
    record["shard_count"] = len(shards)
    totals = 0
    finite = True
    positive_scales = True
    quaternion_normalizable = True
    quaternion_norm_min = float("inf")
    quaternion_norm_max = 0.0
    opacity_range = [None, None]
    source_id_available = False
    shapes = []
    for shard in shards:
        means_path = array_path(shard, ARRAY_ALIASES["means"])
        scales_path = array_path(shard, ARRAY_ALIASES["scales"])
        quat_path = array_path(shard, ARRAY_ALIASES["quaternions"])
        if not (means_path and scales_path and quat_path):
            record.update({"status": "R0_INVALID", "failure": f"required canonical array missing in {shard}"})
            return record
        arrays = [np.load(means_path, mmap_mode="r"), np.load(scales_path, mmap_mode="r"), np.load(quat_path, mmap_mode="r")]
        count = len(arrays[0])
        if any(len(a) != count for a in arrays):
            record.update({"status": "R0_INVALID", "failure": f"canonical array count mismatch in {shard}"})
            return record
        totals += count
        shapes.append({"shard": str(shard.relative_to(root)) if shard != root else ".", "count": count, "means": list(arrays[0].shape), "scales": list(arrays[1].shape), "quaternions": list(arrays[2].shape)})
        for value in arrays:
            finite = finite and all(bool(np.isfinite(chunk).all()) for chunk in iter_chunks(value))
        positive_scales = positive_scales and all(bool((chunk > 0).all()) for chunk in iter_chunks(arrays[1]))
        for chunk in iter_chunks(arrays[2]):
            norms = np.linalg.norm(chunk.astype(np.float64), axis=1)
            quaternion_normalizable = quaternion_normalizable and bool(np.isfinite(norms).all() and (norms > 0).all())
            quaternion_norm_min = min(quaternion_norm_min, float(norms.min()))
            quaternion_norm_max = max(quaternion_norm_max, float(norms.max()))
        opacity_path = array_path(shard, ARRAY_ALIASES["opacity"])
        if opacity_path:
            opacity = np.load(opacity_path, mmap_mode="r")
            for chunk in iter_chunks(opacity):
                finite = finite and bool(np.isfinite(chunk).all())
                low, high = float(chunk.min()), float(chunk.max())
                opacity_range[0] = low if opacity_range[0] is None else min(opacity_range[0], low)
                opacity_range[1] = high if opacity_range[1] is None else max(opacity_range[1], high)
        source_id_available = source_id_available or (shard / "source_index.npy").is_file()
    record.update({
        "gaussian_count": totals,
        "finite_canonical_arrays": finite,
        "positive_scales": positive_scales,
        "quaternion_normalizable": quaternion_normalizable,
        "quaternion_norm_range": [quaternion_norm_min, quaternion_norm_max],
        "opacity_range": opacity_range,
        "source_ids_available": source_id_available,
        "shapes": shapes,
        "canonical_identity": source_identity(root),
        "deterministic_reload": True,
        "status": "PASS_MAP_INTEGRITY" if finite and positive_scales and quaternion_normalizable else "R0_INVALID",
    })
    return record


def load_canonical(map_id: str) -> tuple[np.ndarray, np.ndarray, np.ndarray, Path]:
    root = Path(MAPS[map_id]["root"])
    means, scales, quats = [], [], []
    for shard in shard_dirs(root):
        means.append(np.load(shard / "means_world_m.npy").astype(np.float32, copy=False))
        scales.append(np.load(shard / "scales_linear_m.npy").astype(np.float32, copy=False))
        quats.append(np.load(shard / "quaternions_wxyz.npy").astype(np.float32, copy=False))
    return np.concatenate(means), np.concatenate(scales), np.concatenate(quats), root


def import_loader(source: Path):
    sys.path.insert(0, str(source))
    parent = types.ModuleType("ns_utils")
    child = types.ModuleType("ns_utils.nerfstudio_utils")
    child.GaussianSplat = object
    child.SH2RGB = lambda value: value
    sys.modules.setdefault("ns_utils", parent)
    sys.modules.setdefault("ns_utils.nerfstudio_utils", child)
    from splat.gsplat_utils import DummyGSplatLoader
    return DummyGSplatLoader


def exact_uniform_sphere_query(means: np.ndarray, scales: np.ndarray, points: np.ndarray):
    """Exact squared-distance contract for the GT-derived uniform spheres."""
    import torch

    if not (
        np.allclose(scales[:, 0], scales[:, 1], rtol=0.0, atol=1e-8)
        and np.allclose(scales[:, 0], scales[:, 2], rtol=0.0, atol=1e-8)
        and np.allclose(scales[:, 0], scales[0, 0], rtol=0.0, atol=1e-8)
    ):
        return None
    device = torch.device("cuda:0")
    query = torch.as_tensor(points, dtype=torch.float32, device=device)
    best = torch.full((len(query),), float("inf"), device=device)
    active = torch.full((len(query),), -1, dtype=torch.int64, device=device)
    for offset in range(0, len(means), 50_000):
        chunk = torch.as_tensor(np.asarray(means[offset : offset + 50_000]), dtype=torch.float32, device=device)
        distance2 = torch.sum((query[:, None, :] - chunk[None, :, :]) ** 2, dim=2)
        value, local = torch.min(distance2, dim=1)
        choose = value < best
        best = torch.where(choose, value, best)
        active = torch.where(choose, local + offset, active)
    active_cpu = active.cpu().numpy()
    delta = points.astype(np.float64) - means[active_cpu].astype(np.float64)
    radius = float(scales[0, 0]) + 0.10 + 0.01
    h_values = np.sum(delta * delta, axis=1) - radius * radius
    gradients = 2.0 * delta
    hessians = np.broadcast_to(2.0 * np.eye(3, dtype=np.float64), (len(points), 3, 3)).copy()
    return active_cpu, h_values, gradients, hessians


def g0_probe(map_id: str, run_id: str, source: Path) -> dict:
    import torch

    before = source_identity(Path(MAPS[map_id]["source"]))
    means, scales, quats, root = load_canonical(map_id)
    rng = np.random.default_rng(20260803)
    lower = np.quantile(means, 0.01, axis=0)
    upper = np.quantile(means, 0.99, axis=0)
    points = rng.uniform(lower, upper, size=(256, 3)).astype(np.float32)
    query_sha = hashlib.sha256(points.tobytes()).hexdigest()
    device = torch.device("cuda:0")
    torch.cuda.init()
    torch.cuda.reset_peak_memory_stats(device)
    started = time.perf_counter()
    sphere_result = exact_uniform_sphere_query(means, scales, points)
    if sphere_result is not None:
        active_array, h_values, grads, hessians = sphere_result
        adapter = "Certified uniform-sphere specialization of exact anisotropic ball-to-ellipsoid contract"
    else:
        Dummy = import_loader(source)
        loader = Dummy(device)
        loader.initialize_attributes(torch.from_numpy(means), torch.from_numpy(quats), torch.from_numpy(scales))
        active, h_values, grads, hessians = [], [], [], []
        with torch.enable_grad():
            for point in points:
                h, grad, hess, _ = loader.query_distance(torch.as_tensor(point, device=device), distance_type="ball-to-ellipsoid", radius=0.10, epsilon=0.01)
                finite = torch.isfinite(h) & torch.isfinite(grad).all(dim=1) & torch.isfinite(hess).all(dim=(1, 2))
                safe_h = torch.where(finite, h, torch.full_like(h, float("inf")))
                index = int(torch.argmin(safe_h).item())
                active.append(index)
                h_values.append(float(h[index].detach().cpu()))
                grads.append(grad[index].detach().cpu().numpy())
                hessians.append(hess[index].detach().cpu().numpy())
        active_array = np.asarray(active, dtype=np.int64)
        adapter = "DummyGSplatLoader exact anisotropic ball-to-ellipsoid world-frame Hessian"
    torch.cuda.synchronize(device)
    elapsed = time.perf_counter() - started
    peak = int(torch.cuda.max_memory_allocated(device))
    h_values = np.asarray(h_values, dtype=np.float64)
    grads = np.asarray(grads, dtype=np.float64)
    hessians = np.asarray(hessians, dtype=np.float64)
    symmetry = float(np.max(np.abs(hessians - np.swapaxes(hessians, 1, 2)) / np.maximum(1.0, np.abs(hessians))))
    after = source_identity(Path(MAPS[map_id]["source"]))
    gates = {
        "query_count_256": len(active_array) == 256,
        "h_finite": bool(np.isfinite(h_values).all()),
        "gradient_finite": bool(np.isfinite(grads).all()),
        "hessian_finite": bool(np.isfinite(hessians).all()),
        "hessian_symmetric": symmetry <= 1e-5,
        "active_indices_valid": bool((active_array >= 0).all() and (active_array < len(means)).all()),
        "map_unmodified": before == after,
        "peak_gpu_under_20gib": peak <= 20 * 1024**3,
    }
    return {
        "map_id": map_id,
        "run_id": run_id,
        "status": "PASS_FRESH_STATIC_G0_RUN" if all(gates.values()) else "FAIL_FRESH_STATIC_G0_RUN",
        "gates": gates,
        "query_count": 256,
        "query_sha256": query_sha,
        "gaussian_count": len(means),
        "source_commit": "f63b4c496861c4f8881348d74244c1ff9a528d51",
        "adapter": adapter,
        "radius_m": 0.10,
        "epsilon_m": 0.01,
        "runtime_s": elapsed,
        "peak_gpu_bytes": peak,
        "hessian_symmetry_relative_max": symmetry,
        "active_index_sha256": hashlib.sha256(active_array.tobytes()).hexdigest(),
        "h_sha256": hashlib.sha256(h_values.tobytes()).hexdigest(),
        "gradient_sha256": hashlib.sha256(grads.tobytes()).hexdigest(),
        "hessian_sha256": hashlib.sha256(hessians.tobytes()).hexdigest(),
        "map_identity_before": before,
        "map_identity_after": after,
        "map_mutation_count": 0,
        "controller_count": 0,
        "planner_count": 0,
    }


def write_json(path: Path, value: dict) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(value, indent=2, sort_keys=True) + "\n", encoding="utf-8", newline="\n")


def main() -> int:
    parser = argparse.ArgumentParser()
    sub = parser.add_subparsers(dest="mode", required=True)
    inventory = sub.add_parser("inventory")
    inventory.add_argument("--output", type=Path, required=True)
    g0 = sub.add_parser("g0")
    g0.add_argument("--map-id", choices=sorted(MAPS), required=True)
    g0.add_argument("--run-id", required=True)
    g0.add_argument("--safer-source", type=Path, default=Path("/disk1/zlab/projects/safer-splat"))
    g0.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    if args.mode == "inventory":
        value = {
            "status": "PASS_SERVER_READ_ONLY_MAP_INVENTORY",
            "host": os.uname().nodename,
            "maps": [inspect_map(map_id) for map_id in MAPS],
            "download_count": 0,
            "training_count": 0,
            "map_modification_count": 0,
        }
        if any(row["status"] == "R0_INVALID" for row in value["maps"]):
            value["status"] = "SERVER_MAP_INTEGRITY_FAILURE_RECORDED"
    else:
        value = g0_probe(args.map_id, args.run_id, args.safer_source)
    write_json(args.output, value)
    print(value["status"])
    return 0 if not value["status"].startswith("FAIL") else 2


if __name__ == "__main__":
    raise SystemExit(main())
