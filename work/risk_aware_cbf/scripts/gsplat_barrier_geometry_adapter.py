"""Read-only adapter for the existing ball-to-ellipsoid analytic geometry."""

from __future__ import annotations

from typing import Any

import torch


def query_barrier_geometry(gsplat: Any, position: torch.Tensor, radius: float) -> dict[str, Any]:
    """Return the source h/gradient and the critical constraint without mutation.

    `GSplatLoader.query_distance` computes the existing analytic gradient
    `2 * phi * (x - y)` for every Gaussian. Its minimum h index is the
    critical barrier used by the original `query_h_and_critical` helper.
    """

    h, gradient, _, info = gsplat.query_distance(
        position[:3], radius=radius, distance_type="ball-to-ellipsoid"
    )
    flat_h = h.reshape(-1)
    critical_index = int(torch.argmin(flat_h).detach().cpu().item())
    critical_gradient = gradient.reshape(-1, 3)[critical_index]
    norm = torch.linalg.norm(critical_gradient)
    normal = critical_gradient / norm if float(norm.detach().cpu().item()) > 1e-12 else torch.zeros_like(critical_gradient)
    return {
        "h": h,
        "gradient": gradient,
        "critical_index": critical_index,
        "critical_h": float(flat_h[critical_index].detach().cpu().item()),
        "critical_gradient": critical_gradient,
        "normal": normal,
        "info": info,
    }
