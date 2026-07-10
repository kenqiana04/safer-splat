#!/usr/bin/env python3
"""Nonfunctional shadow wrapper around the restored V4-C pure functions."""

from __future__ import annotations

import importlib
import random
import time
from dataclasses import dataclass
from pathlib import Path
from typing import Any


_MODULE_CACHE: tuple[Any, Any, Any, Any, Any] | None = None


@dataclass(frozen=True)
class V4CShadowContext:
    scene: str
    method: str
    trial: int
    step: int
    x: Any
    goal: Any
    u_base: Any
    u_nom: Any
    u_prev: Any | None
    gsplat: Any
    scene_cfg: dict[str, Any]


@dataclass(frozen=True)
class V4CShadowResult:
    available: bool
    generation_success: bool
    sequence_count: int
    selected_sequence_id: int
    selected_sequence_source: str
    selected_first_control: tuple[float, ...]
    selected_min_h: float
    recovery_success: bool
    recovery_failed: bool
    progress_proxy: float
    runtime_sec: float
    candidate_sources: tuple[str, ...]
    candidate_first_controls: tuple[tuple[float, ...], ...]
    selected_h_sequence: tuple[float, ...]
    selected_cost: float
    state_unchanged: bool
    rng_restored: bool
    modifies_formal_control: bool
    claim_scope: str


def _tensor_tuple(value: Any) -> tuple[float, ...]:
    return tuple(float(item) for item in value.detach().cpu().reshape(-1).tolist())


def _load_modules() -> tuple[Any, Any, Any, Any, Any]:
    global _MODULE_CACHE
    if _MODULE_CACHE is not None:
        return _MODULE_CACHE
    python_state = random.getstate()
    np = importlib.import_module("numpy")
    torch = importlib.import_module("torch")
    numpy_state = np.random.get_state()
    torch_state = torch.random.get_rng_state().clone()
    cuda_states = torch.cuda.get_rng_state_all() if torch.cuda.is_initialized() else None
    try:
        v1 = importlib.import_module("run_risk_aware_v1_pre_cbf_comparison")
        v4b = importlib.import_module("run_v4b_corrective_dt_filter")
        v4c = importlib.import_module("run_v4c_hstep_predictive_recovery")
    finally:
        random.setstate(python_state)
        np.random.set_state(numpy_state)
        torch.random.set_rng_state(torch_state)
        if cuda_states is not None and torch.cuda.is_initialized():
            torch.cuda.set_rng_state_all(cuda_states)
    _MODULE_CACHE = (np, torch, v1, v4b, v4c)
    return _MODULE_CACHE


def load_named_v4c_config(output_dir: Path | str = Path("/tmp/v4c_shadow_unused")) -> Any:
    """Return the reported H3_N128 configuration without running the CLI."""

    _, _, _, _, v4c = _load_modules()
    return v4c.build_parser().parse_args(
        [
            "--scene",
            "flight",
            "--method",
            "risk_aware_v1_bestD",
            "--horizon",
            "3",
            "--num-sequences",
            "128",
            "--activation-mode",
            "on_margin_violation",
            "--dt-margin",
            "0.0005",
            "--warning-margin",
            "0.0008",
            "--control-scale-list",
            "0,0.25,0.5,0.75,1.0",
            "--include-braking-sequences",
            "--include-repulsive-sequences",
            "--include-goal-directed-sequences",
            "--output-dir",
            str(output_dir),
        ]
    )


def build_shadow_context(
    *,
    scene: str,
    method: str,
    trial: int,
    step: int,
    x: Any,
    goal: Any,
    u_base: Any,
    u_nom: Any,
    u_prev: Any | None,
    gsplat: Any,
    scene_cfg: dict[str, Any],
) -> V4CShadowContext:
    """Clone tensor inputs and retain read-only environment references."""

    return V4CShadowContext(
        scene=scene,
        method=method,
        trial=int(trial),
        step=int(step),
        x=x.detach().clone(),
        goal=goal.detach().clone(),
        u_base=u_base.detach().clone(),
        u_nom=u_nom.detach().clone(),
        u_prev=None if u_prev is None else u_prev.detach().clone(),
        gsplat=gsplat,
        scene_cfg=dict(scene_cfg),
    )


def evaluate_v4c_recovery_mode_shadow(
    *, args: Any, context: V4CShadowContext
) -> V4CShadowResult:
    """Call the original V4-C functions without applying the selected control."""

    np, torch, _, _, v4c = _load_modules()
    python_state = random.getstate()
    numpy_state = np.random.get_state()
    torch_state = torch.random.get_rng_state().clone()
    cuda_states = torch.cuda.get_rng_state_all() if torch.cuda.is_initialized() else None
    x_before = context.x.detach().clone()
    goal_before = context.goal.detach().clone()
    base_before = context.u_base.detach().clone()
    nominal_before = context.u_nom.detach().clone()
    previous_before = None if context.u_prev is None else context.u_prev.detach().clone()
    start_time = time.perf_counter()
    try:
        candidates = v4c.generate_sequences(
            args=args,
            x=context.x,
            goal=context.goal,
            u_base=context.u_base,
            u_nom=context.u_nom,
            u_prev=context.u_prev,
            gsplat=context.gsplat,
            scene_cfg=context.scene_cfg,
            trial=context.trial,
            step=context.step,
        )
        selected, first_control, hs, min_h, success, failed, rows, selected_idx = (
            v4c.evaluate_sequences(
                args=args,
                scene=context.scene,
                method=context.method,
                trial=context.trial,
                step=context.step,
                x=context.x,
                goal=context.goal,
                u_base=context.u_base,
                u_prev=context.u_prev,
                candidates=candidates,
                gsplat=context.gsplat,
                scene_cfg=context.scene_cfg,
            )
        )
        final_x, _, _ = v4c.rollout_sequence(
            x=context.x,
            controls=selected.controls,
            dt=args.dt,
            gsplat=context.gsplat,
            scene_cfg=context.scene_cfg,
        )
        progress = float(
            (
                torch.linalg.norm(context.x[:3] - context.goal[:3])
                - torch.linalg.norm(final_x[:3] - context.goal[:3])
            )
            .detach()
            .cpu()
            .item()
        )
        selected_cost = float(rows[selected_idx]["sequence_cost"]) if selected_idx >= 0 else float("nan")
        state_unchanged = (
            torch.equal(context.x, x_before)
            and torch.equal(context.goal, goal_before)
            and torch.equal(context.u_base, base_before)
            and torch.equal(context.u_nom, nominal_before)
            and (
                (context.u_prev is None and previous_before is None)
                or (
                    context.u_prev is not None
                    and previous_before is not None
                    and torch.equal(context.u_prev, previous_before)
                )
            )
        )
        result = V4CShadowResult(
            available=True,
            generation_success=bool(candidates),
            sequence_count=len(candidates),
            selected_sequence_id=int(selected_idx),
            selected_sequence_source=str(selected.source),
            selected_first_control=_tensor_tuple(first_control),
            selected_min_h=float(min_h),
            recovery_success=bool(success),
            recovery_failed=bool(failed),
            progress_proxy=progress,
            runtime_sec=time.perf_counter() - start_time,
            candidate_sources=tuple(candidate.source for candidate in candidates),
            candidate_first_controls=tuple(
                _tensor_tuple(candidate.controls[0]) for candidate in candidates
            ),
            selected_h_sequence=tuple(float(value) for value in hs),
            selected_cost=selected_cost,
            state_unchanged=state_unchanged,
            rng_restored=True,
            modifies_formal_control=False,
            claim_scope="counterfactual shadow interface only",
        )
    finally:
        random.setstate(python_state)
        np.random.set_state(numpy_state)
        torch.random.set_rng_state(torch_state)
        if cuda_states is not None and torch.cuda.is_initialized():
            torch.cuda.set_rng_state_all(cuda_states)
    return result
