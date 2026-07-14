"""Fixed, deterministic GTEP primitive bank using verified analytic normals."""

from __future__ import annotations

from typing import Any

import torch

import run_v4b_corrective_dt_filter as v4b
import run_v4c_hstep_predictive_recovery as v4c


def _unit(value: torch.Tensor) -> torch.Tensor:
    norm = torch.linalg.norm(value)
    return value / norm if float(norm.detach().cpu().item()) > 1e-12 else torch.zeros_like(value)


def tangent_basis(normal: torch.Tensor, goal_direction: torch.Tensor) -> tuple[torch.Tensor, torch.Tensor]:
    raw = goal_direction - torch.dot(goal_direction, normal) * normal
    if float(torch.linalg.norm(raw).detach().cpu().item()) <= 1e-12:
        axes = torch.eye(3, device=normal.device, dtype=normal.dtype)
        axis = axes[int(torch.argmin(torch.abs(axes @ normal)).detach().cpu().item())]
        raw = torch.cross(normal, axis, dim=0)
    t_goal = _unit(raw)
    return t_goal, _unit(torch.cross(normal, t_goal, dim=0))


def primitive_bank(x: torch.Tensor, goal: torch.Tensor, normal: torch.Tensor, horizon: int) -> list[Any]:
    """Return at most 24 preregistered candidates, each through original clamp."""

    n = _unit(normal)
    g = _unit(goal[:3] - x[:3])
    t_goal, t_side = tangent_basis(n, g)
    v_toward = torch.clamp(-torch.dot(x[3:], n), min=0.0)
    controls: list[tuple[str, torch.Tensor]] = []
    for mn in (0.025, 0.05):
        normal_u = mn * n
        brake_u = mn * n + 0.5 * v_toward * n
        controls.extend([(f"gtep_p0_normal_{mn:g}", normal_u), (f"gtep_p1_brake_{mn:g}", brake_u)])
        for mt in (0.05, 0.1):
            tangent = mt * t_goal + brake_u
            controls.extend([(f"gtep_p2_goal_tangent_n{mn:g}_t{mt:g}", tangent), (f"gtep_p3_side_plus_n{mn:g}_t{mt:g}", mt * t_side + brake_u), (f"gtep_p4_side_minus_n{mn:g}_t{mt:g}", -mt * t_side + brake_u)])
            first = v4b.clamp_control(brake_u)
            later = v4b.clamp_control(tangent)
            controls.append((f"gtep_p5_brake_then_tangent_n{mn:g}_t{mt:g}", torch.stack([first] + [later] * max(0, horizon - 1))))
            goal_u = v4b.clamp_control(v4c.goal_directed_control(x, goal, mt))
            controls.append((f"gtep_p6_tangent_then_goal_n{mn:g}_t{mt:g}", torch.stack([later] * max(1, horizon - 1) + [goal_u])))
    out: list[Any] = []
    seen: set[tuple[int, ...]] = set()
    for source, value in controls:
        sequence = value if value.ndim == 2 else v4c.repeat_control(v4b.clamp_control(value), horizon)
        key = tuple(torch.round(sequence.detach().cpu().reshape(-1) * 1e8).to(torch.int64).tolist())
        if key not in seen:
            seen.add(key); out.append(v4c.SequenceCandidate(source, sequence))
    if len(out) > 24:
        raise RuntimeError(f"primitive bank exceeds preregistered limit: {len(out)}")
    return out
