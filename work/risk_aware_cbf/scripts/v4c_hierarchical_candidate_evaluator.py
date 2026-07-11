#!/usr/bin/env python3
"""Two-stage wrapper that delegates all V4-C generation and ranking to source code."""

from __future__ import annotations

import copy
import math
import time
from dataclasses import dataclass
from typing import Any, Callable

import torch

import run_v4c_hstep_predictive_recovery as v4c
from v4c_candidate_family_metrics import stage_family_snapshot


GenerateFn = Callable[..., list[Any]]
EvaluateFn = Callable[..., tuple[Any, torch.Tensor, list[float], float, bool, bool, list[dict[str, Any]], int]]


@dataclass
class StageEvaluation:
    candidates: list[Any]
    selected_candidate: Any
    selected_first_control: torch.Tensor
    selected_hs: list[float]
    selected_min_h: float
    recovery_success: bool
    recovery_failed: bool
    rows: list[dict[str, Any]]
    selected_index: int
    generated_count: int
    feasible_count: int
    generation_runtime_sec: float
    evaluation_runtime_sec: float
    family_snapshot: list[dict[str, Any]]


@dataclass
class HierarchicalEvaluationResult:
    selected_candidate: Any
    selected_first_control: torch.Tensor
    selected_hs: list[float]
    selected_min_h: float
    recovery_success: bool
    recovery_failed: bool
    stage_a_generated_count: int
    stage_a_feasible_count: int
    stage_a_selected: bool
    stage_a_runtime_sec: float
    stage_b_entered: bool
    stage_b_generated_count: int
    stage_b_feasible_count: int
    stage_b_selected: bool
    stage_b_runtime_sec: float
    total_runtime_sec: float
    selected_family: str
    selected_source: str
    selected_progress_delta: float | None
    stage_a_snapshot: list[dict[str, Any]]
    stage_b_snapshot: list[dict[str, Any]]
    stage_b_sources: tuple[str, ...]


def build_stage_a_args(original_args: Any) -> Any:
    """Copy args and disable only stochastic families required by the protocol."""

    stage_a_args = copy.deepcopy(original_args)
    stage_a_args.num_sequences = 0
    stage_a_args.use_cem = False
    return stage_a_args


def _stage_sources_are_deterministic(candidates: list[Any]) -> bool:
    return all(
        not str(candidate.source).startswith("random_around_base_")
        and not str(candidate.source).startswith("cem_")
        for candidate in candidates
    )


def _evaluate_stage(
    *,
    args: Any,
    scene: str,
    method: str,
    trial: int,
    step: int,
    x: torch.Tensor,
    goal: torch.Tensor,
    u_base: torch.Tensor,
    u_prev: torch.Tensor | None,
    candidates: list[Any],
    gsplat: Any,
    scene_cfg: dict[str, Any],
    generation_runtime_sec: float,
    evaluation_fn: EvaluateFn,
) -> StageEvaluation:
    start = time.perf_counter()
    result = evaluation_fn(
        args=args,
        scene=scene,
        method=method,
        trial=trial,
        step=step,
        x=x,
        goal=goal,
        u_base=u_base,
        u_prev=u_prev,
        candidates=candidates,
        gsplat=gsplat,
        scene_cfg=scene_cfg,
    )
    evaluation_runtime_sec = time.perf_counter() - start
    selected, first_control, hs, min_h, success, failed, rows, selected_index = result
    feasible_count = sum(
        str(row.get("sequence_passed_dt_margin", "")).strip().lower() == "true"
        for row in rows
    )
    start_goal_distance = float(torch.linalg.norm(x[:3] - goal[:3]).detach().cpu().item())
    snapshot = stage_family_snapshot(
        candidates=candidates,
        rows=rows,
        selected_index=selected_index,
        start_goal_distance=start_goal_distance,
        generation_runtime_sec=generation_runtime_sec,
        evaluation_runtime_sec=evaluation_runtime_sec,
        count_selection=bool(success),
    )
    return StageEvaluation(
        candidates=candidates,
        selected_candidate=selected,
        selected_first_control=first_control,
        selected_hs=list(hs),
        selected_min_h=float(min_h),
        recovery_success=bool(success),
        recovery_failed=bool(failed),
        rows=rows,
        selected_index=int(selected_index),
        generated_count=len(candidates),
        feasible_count=feasible_count,
        generation_runtime_sec=float(generation_runtime_sec),
        evaluation_runtime_sec=float(evaluation_runtime_sec),
        family_snapshot=snapshot,
    )


def _selected_progress(stage: StageEvaluation, x: torch.Tensor, goal: torch.Tensor) -> float | None:
    if stage.selected_index < 0 or stage.selected_index >= len(stage.rows):
        return None
    try:
        goal_cost = float(stage.rows[stage.selected_index]["sequence_goal_cost"])
    except (KeyError, TypeError, ValueError):
        return None
    start_distance = float(torch.linalg.norm(x[:3] - goal[:3]).detach().cpu().item())
    return start_distance - math.sqrt(max(goal_cost, 0.0))


def evaluate_hierarchical(
    *,
    original_args: Any,
    scene: str,
    method: str,
    trial: int,
    step: int,
    x: torch.Tensor,
    goal: torch.Tensor,
    u_base: torch.Tensor,
    u_nom: torch.Tensor,
    u_prev: torch.Tensor | None,
    gsplat: Any,
    scene_cfg: dict[str, Any],
    stage_a_candidates: list[Any] | None = None,
    generate_fn: GenerateFn = v4c.generate_sequences,
    evaluate_fn: EvaluateFn = v4c.evaluate_sequences,
) -> HierarchicalEvaluationResult:
    """Evaluate Stage A, then invoke exact original full search only if needed."""

    stage_a_args = build_stage_a_args(original_args)
    if stage_a_candidates is None:
        start = time.perf_counter()
        stage_a_candidates = generate_fn(
            args=stage_a_args,
            x=x,
            goal=goal,
            u_base=u_base,
            u_nom=u_nom,
            u_prev=u_prev,
            gsplat=gsplat,
            scene_cfg=scene_cfg,
            trial=trial,
            step=step,
        )
        stage_a_generation = time.perf_counter() - start
    else:
        stage_a_generation = 0.0
    if not _stage_sources_are_deterministic(stage_a_candidates):
        raise RuntimeError("Stage A contains random or CEM candidate sources")
    stage_a = _evaluate_stage(
        args=stage_a_args,
        scene=scene,
        method=method,
        trial=trial,
        step=step,
        x=x,
        goal=goal,
        u_base=u_base,
        u_prev=u_prev,
        candidates=stage_a_candidates,
        gsplat=gsplat,
        scene_cfg=scene_cfg,
        generation_runtime_sec=stage_a_generation,
        evaluation_fn=evaluate_fn,
    )
    if stage_a.recovery_success:
        return HierarchicalEvaluationResult(
            selected_candidate=stage_a.selected_candidate,
            selected_first_control=stage_a.selected_first_control,
            selected_hs=stage_a.selected_hs,
            selected_min_h=stage_a.selected_min_h,
            recovery_success=True,
            recovery_failed=False,
            stage_a_generated_count=stage_a.generated_count,
            stage_a_feasible_count=stage_a.feasible_count,
            stage_a_selected=True,
            stage_a_runtime_sec=stage_a.generation_runtime_sec + stage_a.evaluation_runtime_sec,
            stage_b_entered=False,
            stage_b_generated_count=0,
            stage_b_feasible_count=0,
            stage_b_selected=False,
            stage_b_runtime_sec=0.0,
            total_runtime_sec=stage_a.generation_runtime_sec + stage_a.evaluation_runtime_sec,
            selected_family=str(stage_a.selected_candidate.source),
            selected_source=str(stage_a.selected_candidate.source),
            selected_progress_delta=_selected_progress(stage_a, x, goal),
            stage_a_snapshot=stage_a.family_snapshot,
            stage_b_snapshot=[],
            stage_b_sources=(),
        )
    start = time.perf_counter()
    stage_b_candidates = generate_fn(
        args=original_args,
        x=x,
        goal=goal,
        u_base=u_base,
        u_nom=u_nom,
        u_prev=u_prev,
        gsplat=gsplat,
        scene_cfg=scene_cfg,
        trial=trial,
        step=step,
    )
    stage_b_generation = time.perf_counter() - start
    stage_b = _evaluate_stage(
        args=original_args,
        scene=scene,
        method=method,
        trial=trial,
        step=step,
        x=x,
        goal=goal,
        u_base=u_base,
        u_prev=u_prev,
        candidates=stage_b_candidates,
        gsplat=gsplat,
        scene_cfg=scene_cfg,
        generation_runtime_sec=stage_b_generation,
        evaluation_fn=evaluate_fn,
    )
    return HierarchicalEvaluationResult(
        selected_candidate=stage_b.selected_candidate,
        selected_first_control=stage_b.selected_first_control,
        selected_hs=stage_b.selected_hs,
        selected_min_h=stage_b.selected_min_h,
        recovery_success=stage_b.recovery_success,
        recovery_failed=stage_b.recovery_failed,
        stage_a_generated_count=stage_a.generated_count,
        stage_a_feasible_count=stage_a.feasible_count,
        stage_a_selected=False,
        stage_a_runtime_sec=stage_a.generation_runtime_sec + stage_a.evaluation_runtime_sec,
        stage_b_entered=True,
        stage_b_generated_count=stage_b.generated_count,
        stage_b_feasible_count=stage_b.feasible_count,
        stage_b_selected=True,
        stage_b_runtime_sec=stage_b.generation_runtime_sec + stage_b.evaluation_runtime_sec,
        total_runtime_sec=(stage_a.generation_runtime_sec + stage_a.evaluation_runtime_sec + stage_b.generation_runtime_sec + stage_b.evaluation_runtime_sec),
        selected_family=str(stage_b.selected_candidate.source),
        selected_source=str(stage_b.selected_candidate.source),
        selected_progress_delta=_selected_progress(stage_b, x, goal),
        stage_a_snapshot=stage_a.family_snapshot,
        stage_b_snapshot=stage_b.family_snapshot,
        stage_b_sources=tuple(str(candidate.source) for candidate in stage_b.candidates),
    )
