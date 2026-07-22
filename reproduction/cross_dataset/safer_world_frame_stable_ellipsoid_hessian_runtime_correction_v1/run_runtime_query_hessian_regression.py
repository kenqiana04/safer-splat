"""Exercise patched GSplatLoader.query_distance without CBF or dynamics."""
from __future__ import annotations

import argparse
import importlib.util
import json
import sys
from pathlib import Path

import numpy as np
import torch
from ellipsoids.covariance_utils import quaternion_to_rotation_matrix


def load_loader(tag: str, distances: Path, gsplat_utils: Path):
    distance_spec = importlib.util.spec_from_file_location("splat.distances", distances)
    distance_module = importlib.util.module_from_spec(distance_spec)
    assert distance_spec.loader
    sys.modules["splat.distances"] = distance_module
    distance_spec.loader.exec_module(distance_module)
    loader_spec = importlib.util.spec_from_file_location(tag, gsplat_utils)
    loader_module = importlib.util.module_from_spec(loader_spec)
    assert loader_spec.loader
    loader_spec.loader.exec_module(loader_module)
    return loader_module.DummyGSplatLoader


def load_distance(tag: str, path: Path):
    spec = importlib.util.spec_from_file_location(tag, path)
    module = importlib.util.module_from_spec(spec)
    assert spec.loader
    spec.loader.exec_module(module)
    return module.distance_point_ellipsoid


def rotation_matrix(q: np.ndarray) -> np.ndarray:
    q = q / np.linalg.norm(q, axis=1)[:, None]
    w, x, y, z = q.T
    return np.stack((
        np.stack((1 - 2 * (y * y + z * z), 2 * (x * y - z * w), 2 * (x * z + y * w)), 1),
        np.stack((2 * (x * y + z * w), 1 - 2 * (x * x + z * z), 2 * (y * z - x * w)), 1),
        np.stack((2 * (x * z - y * w), 2 * (y * z + x * w), 1 - 2 * (x * x + y * y)), 1),
    ), 1)


def reference_hessian(scales: np.ndarray, local_signed: np.ndarray) -> np.ndarray:
    a2 = scales * scales
    query = (local_signed * local_signed / a2).sum(1) - 1
    outside = query >= 0
    lo = np.where(outside, 0.0, -(scales.min(1) ** 2) * (1 - 1e-15))
    hi = np.where(outside, np.maximum(np.linalg.norm(scales * local_signed / (scales.min(1)[:, None] ** 2), axis=1), 1.0), 0.0)
    for _ in range(30):
        value = (a2 * local_signed * local_signed / (hi[:, None] + a2) ** 2).sum(1) - 1
        hi = np.where(outside & (value > 0), hi * 2, hi)
    for _ in range(240):
        mid = (lo + hi) * 0.5
        value = (a2 * local_signed * local_signed / (mid[:, None] + a2) ** 2).sum(1) - 1
        lo = np.where(value >= 0, mid, lo)
        hi = np.where(value >= 0, hi, mid)
    lam = (lo + hi) * 0.5
    phi = np.where(outside, 1.0, -1.0)
    denom = lam[:, None] + a2
    diagonal = lam[:, None] / denom
    dy_dlam = -a2 * local_signed / denom**2
    dq_dlam = -2 * (a2 * local_signed * local_signed / denom**3).sum(1)
    dq_dx = -2 * dy_dlam
    local = 2 * (np.eye(3)[None] * diagonal[:, None, :] + np.einsum("ni,nj->nij", dy_dlam, dq_dx) / dq_dlam[:, None, None])
    return phi[:, None, None] * local


def stats(values: np.ndarray) -> dict[str, float]:
    return {"median": float(np.median(values)), "p99": float(np.quantile(values, 0.99)), "max": float(np.max(values))}


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--old-distances", type=Path, required=True)
    parser.add_argument("--old-gsplat-utils", type=Path, required=True)
    parser.add_argument("--new-distances", type=Path, required=True)
    parser.add_argument("--new-gsplat-utils", type=Path, required=True)
    parser.add_argument("--out", type=Path, required=True)
    args = parser.parse_args()

    torch.manual_seed(20260722)
    rng = np.random.default_rng(20260716)
    count = 4096
    quats = torch.tensor(rng.normal(size=(count, 4)), dtype=torch.float32, device="cuda:0")
    scales = torch.rand(count, 3, device="cuda:0").mul_(0.25).add_(0.001)
    scales, _ = torch.sort(scales, dim=-1, descending=True)
    torch_seed_rotations = quaternion_to_rotation_matrix(quats)
    local_cases = torch.randn(count, 3, device="cuda:0") * 0.7
    point = torch.zeros(3, device="cuda:0")
    means = -torch.bmm(torch_seed_rotations, (local_cases - 1e-8).unsqueeze(-1)).squeeze(-1)

    Old = load_loader("old_gsplat_utils", args.old_distances, args.old_gsplat_utils)
    old = Old("cuda:0")
    old.initialize_attributes(means, quats, scales)
    old_h, old_grad, old_hess, old_info = old.query_distance(point)
    del old

    New = load_loader("new_gsplat_utils", args.new_distances, args.new_gsplat_utils)
    new = New("cuda:0")
    new.initialize_attributes(means, quats, scales)
    new_h, new_grad, new_hess, new_info = new.query_distance(point)

    direct_distance = load_distance("new_direct_distances", args.new_distances)
    torch_rots = quaternion_to_rotation_matrix(quats)
    torch_scales, torch_order = torch.sort(scales, dim=-1, descending=True)
    torch_rots = torch.gather(torch_rots, 2, torch_order[..., None, :].expand_as(torch_rots))
    torch_local = torch.bmm(torch_rots.transpose(1, 2), (point[None] - means).unsqueeze(-1)).squeeze(-1) + 1e-8
    _, _, torch_first_octant, _ = direct_distance(torch_scales + 1e-8, torch.abs(torch_local))
    torch_flip = torch.where(torch_local < 0, -torch.ones_like(torch_local), torch.ones_like(torch_local))
    torch_phi = torch.sign(torch.sum((1.0 / torch_scales) ** 2 * torch.abs(torch_local) ** 2, dim=-1) - 1.0)
    torch_manual = torch_phi[:, None, None] * torch.bmm(torch_rots, torch.bmm(torch_flip[:, :, None] * torch_first_octant * torch_flip[:, None, :], torch_rots.transpose(1, 2)))

    matrices = quaternion_to_rotation_matrix(quats).detach().cpu().numpy().astype(np.float64)
    raw_scales = scales.cpu().numpy().astype(np.float64)
    order = np.argsort(-raw_scales, axis=1)
    sorted_scales = np.take_along_axis(raw_scales, order, axis=1)
    sorted_matrices = np.take_along_axis(matrices, np.broadcast_to(order[:, None, :], matrices.shape), axis=2)
    local_signed = np.einsum("nji,nj->ni", sorted_matrices, point.cpu().numpy().astype(np.float64)[None] - means.cpu().numpy().astype(np.float64)) + 1e-8
    reference_local = reference_hessian(sorted_scales + 1e-8, local_signed)
    reference = np.einsum("nij,njk,nlk->nil", sorted_matrices, reference_local, sorted_matrices)
    actual = new_hess.detach().cpu().numpy().astype(np.float64)
    actual_local = (torch_phi[:, None, None] * torch_flip[:, :, None] * torch_first_octant * torch_flip[:, None, :]).detach().cpu().numpy().astype(np.float64)
    relative = np.linalg.norm(actual - reference, axis=(1, 2)) / (1 + np.linalg.norm(reference, axis=(1, 2)))
    symmetry = np.linalg.norm(actual - actual.swapaxes(1, 2), axis=(1, 2)) / (1 + np.linalg.norm(actual, axis=(1, 2)))
    directions = rng.normal(size=(32, 3))
    directions /= np.linalg.norm(directions, axis=1)[:, None]
    hvp = np.concatenate([np.linalg.norm(actual @ direction - reference @ direction, axis=1) / (1 + np.linalg.norm(reference @ direction, axis=1)) for direction in directions])

    zero_local = torch.tensor(((1e-8, 0.13, 0.09), (1e-10, 0.13, 0.09), (0.0, 0.13, 0.09), (-1e-8, 0.13, -0.09), (0.13, 1e-8, 0.09), (0.13, 0.09, 1e-8)), device="cuda:0")
    zero_quats = torch.tensor(((0.7, 0.2, -0.3, 0.6),) * 6, device="cuda:0")
    zero_rotations = quaternion_to_rotation_matrix(zero_quats)
    zero_means = -torch.bmm(zero_rotations, (zero_local - 1e-8).unsqueeze(-1)).squeeze(-1)
    zero_scales = torch.tensor(((0.2, 0.1, 0.05),) * 6, device="cuda:0")
    zero_loader = New("cuda:0")
    zero_loader.initialize_attributes(zero_means, zero_quats, zero_scales)
    _, _, zero_hess, _ = zero_loader.query_distance(torch.zeros(3, device="cuda:0"))

    zero_finite = torch.isfinite(zero_hess).reshape(6, -1).all(dim=1)
    out = {
        "case_count": count,
        "forward_h_bitwise_exact": bool(torch.equal(old_h, new_h)),
        "forward_grad_bitwise_exact": bool(torch.equal(old_grad, new_grad)),
        "closest_point_bitwise_exact": bool(torch.equal(old_info["y"], new_info["y"])),
        "active_index_bitwise_exact": bool(torch.argmin(old_h).item() == torch.argmin(new_h).item()),
        "runtime_composition_bitwise_exact": bool(torch.equal(new_hess, torch_manual)),
        "local_reference_max_abs": float(np.max(np.abs(local_signed - torch_local.detach().cpu().numpy().astype(np.float64)))),
        "local_hessian_reference_error": stats(np.linalg.norm(actual_local - reference_local, axis=(1, 2)) / (1 + np.linalg.norm(reference_local, axis=(1, 2)))),
        "phi_zero_count": int((torch_phi == 0).sum().item()),
        "phi_reference_agreement": float((torch_phi.detach().cpu().numpy() == np.where(((local_signed / (sorted_scales + 1e-8)) ** 2).sum(1) >= 1.0, 1.0, -1.0)).mean()),
        "hessian_error": stats(relative),
        "hvp_error": stats(hvp),
        "symmetry_max": float(symmetry.max()),
        "finite_ratio": float(np.isfinite(actual).all(axis=(1, 2)).mean()),
        "zero_component_finite_count": int(zero_finite.sum().item()),
        "zero_component_total": 6,
    }
    out["status"] = "PASS_RUNTIME_QUERY_WORLD_HESSIAN_REGRESSION" if all((out["forward_h_bitwise_exact"], out["forward_grad_bitwise_exact"], out["closest_point_bitwise_exact"], out["active_index_bitwise_exact"], out["runtime_composition_bitwise_exact"], out["hessian_error"]["max"] <= 1e-2, out["hvp_error"]["max"] <= 1e-2, out["symmetry_max"] <= 1e-5, out["finite_ratio"] == 1.0, out["zero_component_finite_count"] == 6)) else "FAIL"
    args.out.write_text(json.dumps(out, indent=2, sort_keys=True) + "\n")
    print(json.dumps(out, sort_keys=True))


if __name__ == "__main__":
    main()
