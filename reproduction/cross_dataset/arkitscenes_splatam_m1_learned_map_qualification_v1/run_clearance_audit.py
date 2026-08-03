#!/usr/bin/env python3
"""Accelerated-but-exact ellipsoid/mesh clearance audit with brute-force certification."""

from __future__ import annotations

import argparse
import hashlib
import json
import sys
import time
import types
from pathlib import Path

import numpy as np
import open3d as o3d
from scipy.spatial import cKDTree
import torch


def load_safer(source: Path):
    sys.path.insert(0, str(source))
    # GSplatLoader imports Nerfstudio adapters that the canonical-array path does
    # not use.  Supply import-only sentinels without altering the query source.
    if "ns_utils.nerfstudio_utils" not in sys.modules:
        parent = types.ModuleType("ns_utils"); child = types.ModuleType("ns_utils.nerfstudio_utils")
        child.GaussianSplat = object; child.SH2RGB = lambda value: value
        sys.modules["ns_utils"] = parent; sys.modules["ns_utils.nerfstudio_utils"] = child
    from ellipsoids.covariance_utils import quaternion_to_rotation_matrix
    from splat.distances import distance_point_ellipsoid
    from splat.gsplat_utils import DummyGSplatLoader
    return quaternion_to_rotation_matrix, distance_point_ellipsoid, DummyGSplatLoader


def signed_pairs(points: np.ndarray, indices: np.ndarray, means: np.ndarray, scales: np.ndarray, quats: np.ndarray,
                 quaternion_to_rotation_matrix, distance_point_ellipsoid) -> np.ndarray:
    flat_idx = indices.reshape(-1)
    flat_points = np.repeat(points, indices.shape[1], axis=0)
    output = np.empty(len(flat_idx), dtype=np.float64)
    device = torch.device("cuda:0")
    for start in range(0, len(flat_idx), 200000):
        stop = min(start + 200000, len(flat_idx)); ids = flat_idx[start:stop]
        x = torch.as_tensor(flat_points[start:stop], dtype=torch.float64, device=device)
        m = torch.as_tensor(means[ids], dtype=torch.float64, device=device)
        s = torch.as_tensor(scales[ids], dtype=torch.float64, device=device)
        q = torch.as_tensor(quats[ids], dtype=torch.float64, device=device)
        rots = quaternion_to_rotation_matrix(q)
        sorted_scales, sorted_inds = torch.sort(s, dim=-1, descending=True)
        rots = torch.gather(rots, 2, sorted_inds[..., None, :].expand_as(rots))
        local = torch.bmm(torch.transpose(rots, 1, 2), (x - m).unsqueeze(-1)).squeeze(-1) + 1e-8
        phi = torch.sign(torch.sum((1.0 / sorted_scales) ** 2 * local ** 2, dim=-1) - 1.0)
        dist, _, _, _ = distance_point_ellipsoid(sorted_scales + 1e-8, torch.abs(local))
        signed = phi * torch.sqrt(torch.clamp(dist, min=0))
        output[start:stop] = signed.detach().cpu().numpy()
    return output.reshape(indices.shape)


def accelerated(points: np.ndarray, means: np.ndarray, scales: np.ndarray, quats: np.ndarray, qrot, solver) -> tuple[np.ndarray, np.ndarray, dict]:
    tree = cKDTree(means)
    max_scale = float(np.max(scales))
    best_all = np.empty(len(points), dtype=np.float64); active_all = np.empty(len(points), dtype=np.int64)
    max_k = 0; total_pairs = 0
    for offset in range(0, len(points), 2048):
        chunk = points[offset:offset + 2048]
        k = min(16, len(means))
        while True:
            _, idx = tree.query(chunk, k=k, workers=4)
            if k == 1:
                idx = idx[:, None]
            signed = signed_pairs(chunk, np.asarray(idx), means, scales, quats, qrot, solver)
            local_choice = np.argmin(signed, axis=1); best = signed[np.arange(len(chunk)), local_choice]
            radii = max_scale + np.maximum(best, 0.0)
            counts = np.asarray(tree.query_ball_point(chunk, radii, return_length=True, workers=4))
            needed = int(counts.max())
            if needed <= k:
                break
            k = min(len(means), needed)
        best_all[offset:offset + len(chunk)] = best
        active_all[offset:offset + len(chunk)] = idx[np.arange(len(chunk)), local_choice]
        max_k = max(max_k, k); total_pairs += len(chunk) * k
    return best_all, active_all, {"global_max_scale_m": max_scale, "maximum_conservative_candidate_count": max_k, "evaluated_pair_count": total_pairs, "acceleration_safe": True}


def actual_bruteforce(points: np.ndarray, means: np.ndarray, scales: np.ndarray, quats: np.ndarray, DummyGSplatLoader) -> tuple[np.ndarray, np.ndarray]:
    loader = DummyGSplatLoader(torch.device("cuda:0"))
    loader.initialize_attributes(torch.as_tensor(means, dtype=torch.float64), torch.as_tensor(quats, dtype=torch.float64), torch.as_tensor(scales, dtype=torch.float64))
    values, active = [], []
    for point in points:
        h, _, _, info = loader.query_distance(torch.as_tensor(point, dtype=torch.float64, device="cuda:0"), distance_type="ball-to-ellipsoid", radius=0.0, epsilon=0.0)
        signed = info["phi"] * torch.sqrt(torch.clamp(torch.abs(h), min=0))
        index = int(torch.argmin(signed).item())
        values.append(float(signed[index].item())); active.append(index)
    return np.asarray(values), np.asarray(active, dtype=np.int64)


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--map-dir", type=Path, required=True)
    parser.add_argument("--registry", type=Path, required=True)
    parser.add_argument("--registry-freeze", type=Path, required=True)
    parser.add_argument("--mesh", type=Path, required=True)
    parser.add_argument("--safer-source", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    qrot, solver, dummy = load_safer(args.safer_source)
    means = np.load(args.map_dir / "means_world_m.npy").astype(np.float64)
    scales = np.load(args.map_dir / "scales_linear_m.npy").astype(np.float64)
    quats = np.load(args.map_dir / "quaternions_wxyz.npy").astype(np.float64)
    registry = np.load(args.registry); points = registry["points_m"].astype(np.float64); classes = registry["class_code"]
    freeze = json.loads(args.registry_freeze.read_text(encoding="utf-8"))
    mesh = o3d.io.read_triangle_mesh(str(args.mesh)); mesh.transform(np.asarray(freeze["world_from_apple"], dtype=np.float64))
    scene = o3d.t.geometry.RaycastingScene(); scene.add_triangles(o3d.t.geometry.TriangleMesh.from_legacy(mesh))
    d_mesh = np.asarray(scene.compute_distance(o3d.core.Tensor(points.astype(np.float32))).numpy(), dtype=np.float64)
    torch.cuda.reset_peak_memory_stats(); started = time.perf_counter()
    d_gaussian, active, acceleration = accelerated(points, means, scales, quats, qrot, solver)
    elapsed = time.perf_counter() - started; peak = int(torch.cuda.max_memory_allocated())
    audit_indices = np.linspace(0, len(points) - 1, 256, dtype=np.int64)
    brute_values, brute_active = actual_bruteforce(points[audit_indices], means, scales, quats, dummy)
    brute_diff = np.abs(brute_values - d_gaussian[audit_indices])
    eplus = np.maximum(0.0, d_gaussian - d_mesh)
    false_free = (d_gaussian >= 0.11) & (d_mesh < 0.11)
    false_points = points[false_free]
    largest_cluster = 0.0
    if len(false_points):
        tree = cKDTree(false_points); pairs = tree.query_pairs(0.05)
        parent = np.arange(len(false_points))
        def find(x):
            while parent[x] != x:
                parent[x] = parent[parent[x]]; x = parent[x]
            return x
        for a, b in pairs:
            ra, rb = find(a), find(b)
            if ra != rb: parent[rb] = ra
        for root in {find(i) for i in range(len(false_points))}:
            group = false_points[[find(i) == root for i in range(len(false_points))]]
            largest_cluster = max(largest_cluster, float(np.linalg.norm(group.max(axis=0) - group.min(axis=0))))
    gates = {
        "registry_at_least_120k": len(points) >= 120000,
        "accelerated_final_exact": acceleration["acceleration_safe"],
        "bruteforce_256_max_diff": float(brute_diff.max()) <= 1e-6,
        "finite": bool(np.isfinite(d_mesh).all() and np.isfinite(d_gaussian).all()),
        "p95_eplus": float(np.quantile(eplus, 0.95)) <= 0.03,
        "p99_eplus": float(np.quantile(eplus, 0.99)) <= 0.06,
        "max_eplus": float(eplus.max()) <= 0.12,
        "fraction_eplus_gt_0p05": float(np.mean(eplus > 0.05)) <= 0.01,
        "largest_false_free_cluster": largest_cluster <= 0.25,
        "peak_gpu_under_20gib": peak <= 20 * 1024 ** 3,
    }
    result = {
        "status": "PASS_ARKITSCENES_M1_CLEARANCE_AUDIT" if all(gates.values()) else "NO_ARKITSCENES_M1_LEARNED_GAUSSIAN_MAP_QUALIFIED_UNDER_FROZEN_CONTRACT",
        "pass": all(gates.values()), "gates": gates, "query_count": len(points), "robot_radius_m": 0.10, "epsilon_base_m": 0.01,
        "distance_contract": "dM unsigned Apple mesh distance; dG signed SAFER anisotropic union-ellipsoid surface distance; eplus=max(0,dG-dM)",
        "metrics": {"p95_eplus_m": float(np.quantile(eplus, .95)), "p99_eplus_m": float(np.quantile(eplus, .99)), "max_eplus_m": float(eplus.max()),
                    "fraction_eplus_gt_0p05": float(np.mean(eplus > .05)), "false_free_count": int(false_free.sum()), "largest_false_free_cluster_diameter_m": largest_cluster,
                    "bruteforce_max_abs_diff_m": float(brute_diff.max()), "bruteforce_active_match_count": int(np.sum(brute_active == active[audit_indices]))},
        "acceleration": acceleration, "runtime_s": elapsed, "peak_gpu_bytes": peak,
        "empirical_epsilon_candidate_m": float(np.quantile(eplus, .99)),
        "claim_boundary": "empirical qualification only; not a proof of global safety or unseen-space completeness",
        "per_class": {str(code): {"count": int((classes == code).sum()), "p99_eplus_m": float(np.quantile(eplus[classes == code], .99))} for code in np.unique(classes)},
        "active_index_sha256": hashlib.sha256(active.tobytes()).hexdigest(),
    }
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(result, indent=2, sort_keys=True) + "\n", encoding="utf-8", newline="\n")
    print(result["status"])
    if not result["pass"]:
        raise SystemExit(3)


if __name__ == "__main__":
    main()

