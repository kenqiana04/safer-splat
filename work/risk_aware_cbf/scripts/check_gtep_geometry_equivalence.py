"""Equivalence helper for existing GSplat barrier geometry and the read-only adapter."""

from __future__ import annotations

import torch

from gsplat_barrier_geometry_adapter import query_barrier_geometry


def check_context(gsplat, position: torch.Tensor, radius: float, context_id: int) -> dict:
    before = position.detach().clone()
    h_source, grad_source, _, _ = gsplat.query_distance(position[:3], radius=radius, distance_type="ball-to-ellipsoid")
    adapter = query_barrier_geometry(gsplat, position, radius)
    index = int(torch.argmin(h_source.reshape(-1)).detach().cpu().item())
    source_gradient = grad_source.reshape(-1, 3)[index]
    error = float(torch.max(torch.abs(source_gradient - adapter["critical_gradient"])).detach().cpu().item())
    h_error = abs(float(h_source.reshape(-1)[index].detach().cpu().item()) - adapter["critical_h"])
    return {"context_id": context_id, "h_source": float(h_source.reshape(-1)[index].detach().cpu().item()), "h_adapter": adapter["critical_h"], "h_abs_error": h_error, "critical_id_source": index, "critical_id_adapter": adapter["critical_index"], "gradient_source_available": True, "gradient_adapter": "existing_query_distance_analytic", "gradient_abs_error": error, "normal_increases_h": bool(float(torch.dot(source_gradient, adapter["normal"]).detach().cpu().item()) > 0), "state_unchanged": bool(torch.equal(before, position)), "equivalence_passed": bool(h_error <= 1e-7 and error <= 1e-7 and index == adapter["critical_index"] and torch.equal(before, position)), "notes": "Adapter delegates to existing ball-to-ellipsoid analytic query; no finite differences."}
