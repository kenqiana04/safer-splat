"""Source-order functional reconstruction of the frozen SAFER ellipsoid query.

The forward midpoint deliberately uses ``torch.stack`` then ``torch.mean`` to
match the source's contiguous two-column bound table.  Bound updates are
functional ``where`` operations, so autograd remains valid for the query point.
"""
from __future__ import annotations

import torch
from ellipsoids.covariance_utils import quaternion_to_rotation_matrix


def exact_functional_real_get_root(r: torch.Tensor, z: torch.Tensor, g: torch.Tensor, max_iterations: int = 25, trace: list[dict] | None = None) -> torch.Tensor:
    n = r * z
    lower = z[..., -1] - 1.0
    upper = torch.where(g >= 0, torch.linalg.vector_norm(n, dim=-1) - 1.0, torch.zeros_like(lower))
    for iteration in range(max_iterations):
        # This matches ``torch.mean(s, dim=-1, keepdims=True)`` in real_get_root.
        bounds = torch.stack((lower, upper), dim=-1)
        midpoint_keepdim = torch.mean(bounds, dim=-1, keepdim=True)
        ratio = n / (midpoint_keepdim + r)
        g_iter = torch.sum(ratio**2, dim=-1) - 1.0
        mask = g_iter >= 0
        midpoint = midpoint_keepdim.squeeze(-1)
        if trace is not None:
            trace.append({"iteration": iteration, "lower": lower.detach().cpu(), "upper": upper.detach().cpu(), "midpoint": midpoint.detach().cpu(), "g": g_iter.detach().cpu(), "mask": mask.detach().cpu()})
        lower, upper = torch.where(mask, midpoint, lower), torch.where(mask, upper, midpoint)
    return midpoint_keepdim


def exact_functional_distance_point_ellipsoid(scales: torch.Tensor, point_local: torch.Tensor, trace: list[dict] | None = None) -> tuple[torch.Tensor, torch.Tensor]:
    z = point_local / scales
    g = torch.sum(z**2, dim=-1) - 1.0
    r = (scales / scales[..., -1, None])**2
    lam = exact_functional_real_get_root(r, z, g, trace=trace)
    yhat = r * point_local / (lam + r)
    squared_distance = torch.sum((yhat - point_local)**2, dim=-1)
    return squared_distance, yhat


def exact_functional_ball_to_ellipsoid_query(means: torch.Tensor, quaternions_wxyz: torch.Tensor, scales: torch.Tensor, point: torch.Tensor, radius: float = 0.0, epsilon: float = 0.0, trace: list[dict] | None = None) -> tuple[torch.Tensor, torch.Tensor, torch.Tensor, torch.Tensor]:
    rots = quaternion_to_rotation_matrix(quaternions_wxyz)
    sorted_scales, sorted_indices = torch.sort(scales, dim=-1, descending=True)
    rots = torch.gather(rots, 2, sorted_indices[..., None, :].expand_as(rots))
    local = torch.bmm(rots.transpose(1, 2), (point[:3] - means).unsqueeze(-1)).squeeze(-1) + 1e-8
    flip = torch.sign(local)
    local = torch.abs(local)
    squared_distance, yhat = exact_functional_distance_point_ellipsoid(sorted_scales + 1e-8, local, trace=trace)
    y_world = torch.bmm(rots, (flip * yhat).unsqueeze(-1)).squeeze(-1) + means
    phi = torch.sign(torch.sum((1.0 / sorted_scales)**2 * local**2, dim=-1) - 1.0)
    h = phi * squared_distance - (radius + epsilon)**2
    return h, y_world, phi, sorted_indices
