#!/usr/bin/env python3
from __future__ import annotations

import argparse
import csv
import json
import math
import sys
import time
import traceback
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[3]
SCRIPT_DIR = Path(__file__).resolve().parent
for path in (ROOT, SCRIPT_DIR):
    if str(path) not in sys.path:
        sys.path.insert(0, str(path))

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
import torch

from dynamics.systems import DoubleIntegrator, double_integrator_dynamics
from splat.gsplat_utils import GSplatLoader

import run_risk_aware_v1_pre_cbf_comparison as v1
import run_v4b_corrective_dt_filter as v4b


TRIAL_FIELDS = [
    "scene",
    "method",
    "trial",
    "use_startguard",
    "start_source",
    "navigation_executed",
    "success",
    "collision",
    "collision_free",
    "stop_reason",
    "num_steps",
    "min_safety_h",
    "base_horizon_margin_violation_count",
    "exec_horizon_margin_violation_count",
    "horizon_margin_violation_reduction",
    "predictive_recovery_used_count",
    "predictive_recovery_success_count",
    "recovery_failed_count",
    "qp_infeasible_count",
    "goal_distance_reduction_ratio",
    "initial_goal_distance",
    "final_goal_distance",
    "closest_goal_distance",
    "runtime_mean",
    "runtime_p95",
    "runtime_recovery_mean",
    "runtime_recovery_p95",
    "control_delta_mean",
    "control_delta_p95",
    "seconds_total",
    "repair_used",
    "repair_success",
    "repair_distance",
    "repair_method",
    "full_query_verified",
    "error",
]

STEP_FIELDS = [
    "scene",
    "method",
    "trial",
    "step",
    "current_h",
    "base_next_h",
    "exec_next_h",
    "actual_next_h",
    "base_horizon_min_h",
    "exec_horizon_min_h",
    "dt_margin",
    "warning_margin",
    "activation_mode",
    "base_horizon_margin_violation",
    "exec_horizon_margin_violation",
    "predictive_recovery_used",
    "predictive_recovery_success",
    "recovery_failed",
    "sequence_count",
    "selected_sequence_id",
    "selected_sequence_source",
    "runtime_step",
    "runtime_recovery",
    "active_constraints_count",
    "collision_step_flag",
    "qp_infeasible",
    "goal_distance",
    "goal_progress_delta",
]

SEQUENCE_FIELDS = [
    "scene",
    "method",
    "trial",
    "step",
    "sequence_id",
    "sequence_source",
    "horizon",
    "sequence_min_h",
    "sequence_final_h",
    "sequence_passed_dt_margin",
    "sequence_cost",
    "sequence_base_deviation",
    "sequence_goal_cost",
    "sequence_smooth_cost",
    "sequence_safety_penalty",
    "selected",
    "controls_json",
    "horizon_h_json",
]

RECOVERY_FIELDS = [
    "scene",
    "method",
    "trial",
    "step",
    "u_base_x",
    "u_base_y",
    "u_base_z",
    "u_exec_x",
    "u_exec_y",
    "u_exec_z",
    "control_delta_norm",
    "base_horizon_min_h",
    "exec_horizon_min_h",
    "horizon_h_improvement",
    "predictive_recovery_used",
    "predictive_recovery_success",
    "recovery_failed",
    "selected_sequence_id",
    "selected_sequence_source",
]

SUMMARY_FIELDS = [
    "scene",
    "method",
    "rows",
    "navigation_executed_count",
    "collision_count",
    "collision_free_count",
    "qp_infeasible_count",
    "num_steps",
    "base_horizon_margin_violation_count",
    "exec_horizon_margin_violation_count",
    "horizon_margin_violation_reduction",
    "predictive_recovery_used_count",
    "predictive_recovery_success_count",
    "recovery_failed_count",
    "progress_mean",
    "runtime_mean",
    "runtime_p95",
    "runtime_recovery_mean",
    "control_delta_mean",
    "min_safety_h_min",
]


@dataclass
class SequenceCandidate:
    source: str
    controls: torch.Tensor


def tensor_to_json(values: torch.Tensor) -> str:
    arr = values.detach().cpu().numpy().astype(float).tolist()
    return json.dumps(arr, separators=(",", ":"))


def floats_to_json(values: list[float]) -> str:
    return json.dumps([float(v) for v in values], separators=(",", ":"))


def sequence_key(controls: torch.Tensor) -> tuple[int, ...]:
    flat = controls.detach().cpu().reshape(-1).numpy()
    return tuple(int(round(float(v) * 1_000_000)) for v in flat)


def add_sequence(
    candidates: list[SequenceCandidate],
    seen: set[tuple[int, ...]],
    source: str,
    controls: torch.Tensor,
) -> None:
    controls = torch.clamp(controls, -0.1, 0.1)
    key = sequence_key(controls)
    if key in seen:
        return
    seen.add(key)
    candidates.append(SequenceCandidate(source=source, controls=controls.detach().clone()))


def repeat_control(u: torch.Tensor, horizon: int) -> torch.Tensor:
    return u.reshape(1, 3).repeat(horizon, 1)


def rollout_sequence(
    *,
    x: torch.Tensor,
    controls: torch.Tensor,
    dt: float,
    gsplat: GSplatLoader,
    scene_cfg: dict[str, Any],
) -> tuple[torch.Tensor, list[float], float]:
    cur = x.detach().clone()
    hs: list[float] = []
    for idx in range(int(controls.shape[0])):
        cur = double_integrator_dynamics(cur, controls[idx]) * float(dt) + cur
        hs.append(v4b.query_h(gsplat, cur[:3], scene_cfg["radius"]))
    min_h = min(hs) if hs else v4b.query_h(gsplat, cur[:3], scene_cfg["radius"])
    return cur, hs, float(min_h)


def braking_sequence(x: torch.Tensor, gain: float, horizon: int, dt: float) -> torch.Tensor:
    cur = x.detach().clone()
    controls: list[torch.Tensor] = []
    for _ in range(horizon):
        u = v4b.clamp_control(-float(gain) * cur[3:6])
        controls.append(u)
        cur = double_integrator_dynamics(cur, u) * float(dt) + cur
    return torch.stack(controls, dim=0)


def goal_directed_control(x: torch.Tensor, goal: torch.Tensor, mag: float) -> torch.Tensor:
    return float(mag) * v4b.unit_or_zero(goal[:3] - x[:3])


def repulsive_control(gsplat: GSplatLoader, x: torch.Tensor, scene_cfg: dict[str, Any], mag: float) -> torch.Tensor:
    _, gid = v4b.query_h_and_critical(gsplat, x[:3], scene_cfg["radius"])
    away = v4b.unit_or_zero(x[:3] - gsplat.means[gid])
    return float(mag) * away


def generate_sequences(
    *,
    args: argparse.Namespace,
    x: torch.Tensor,
    goal: torch.Tensor,
    u_base: torch.Tensor,
    u_nom: torch.Tensor,
    u_prev: torch.Tensor | None,
    gsplat: GSplatLoader,
    scene_cfg: dict[str, Any],
    trial: int,
    step: int,
) -> list[SequenceCandidate]:
    horizon = int(args.horizon)
    candidates: list[SequenceCandidate] = []
    seen: set[tuple[int, ...]] = set()

    add_sequence(candidates, seen, "base_repeated", repeat_control(u_base, horizon))
    add_sequence(candidates, seen, "nominal_repeated", repeat_control(u_nom, horizon))
    for scale in v4b.parse_csv_floats(args.control_scale_list):
        add_sequence(candidates, seen, f"scaled_base_{scale:g}", repeat_control(float(scale) * u_base, horizon))

    if args.include_braking_sequences:
        for gain in (0.25, 0.5, 1.0, 1.5):
            seq = braking_sequence(x, gain, horizon, args.dt)
            add_sequence(candidates, seen, f"braking_{gain:g}", seq)
            mixed = repeat_control(u_base, horizon)
            split = max(1, horizon // 2)
            mixed[:split] = seq[:split]
            add_sequence(candidates, seen, f"brake_then_base_{gain:g}", mixed)

    if args.include_repulsive_sequences:
        try:
            for mag in (0.025, 0.05, 0.1):
                u_rep = repulsive_control(gsplat, x, scene_cfg, mag)
                add_sequence(candidates, seen, f"repulsive_{mag:g}", repeat_control(u_rep, horizon))
                add_sequence(candidates, seen, f"base_plus_repulsive_{mag:g}", repeat_control(u_base + u_rep, horizon))
                mixed = repeat_control(u_base, horizon)
                split = max(1, horizon // 2)
                mixed[:split] = repeat_control(u_rep, split)
                add_sequence(candidates, seen, f"repulse_then_base_{mag:g}", mixed)
        except Exception:
            pass

    if args.include_goal_directed_sequences:
        for mag in (0.025, 0.05, 0.1):
            u_goal = goal_directed_control(x, goal, mag)
            add_sequence(candidates, seen, f"goal_directed_{mag:g}", repeat_control(u_goal, horizon))
            if args.include_repulsive_sequences:
                try:
                    u_rep = repulsive_control(gsplat, x, scene_cfg, mag)
                    mixed = repeat_control(u_goal, horizon)
                    split = max(1, horizon // 2)
                    mixed[:split] = repeat_control(u_rep, split)
                    add_sequence(candidates, seen, f"repulse_then_goal_{mag:g}", mixed)
                except Exception:
                    pass

    if u_prev is not None:
        add_sequence(candidates, seen, "previous_repeated", repeat_control(u_prev, horizon))
        add_sequence(candidates, seen, "smooth_prev_base", repeat_control(0.5 * (u_prev + u_base), horizon))

    rng = np.random.default_rng(73_031 + 1009 * int(trial) + int(step))
    for idx in range(int(args.num_sequences)):
        noise = torch.tensor(rng.normal(size=(horizon, 3)), device=x.device, dtype=x.dtype)
        seq = repeat_control(u_base, horizon) + float(args.sequence_noise_scale) * noise
        add_sequence(candidates, seen, f"random_around_base_{idx}", seq)

    if args.use_cem:
        candidates.extend(generate_cem_sequences(args=args, x=x, goal=goal, u_base=u_base, u_prev=u_prev, gsplat=gsplat, scene_cfg=scene_cfg, trial=trial, step=step, seen=seen))

    return candidates


def generate_cem_sequences(
    *,
    args: argparse.Namespace,
    x: torch.Tensor,
    goal: torch.Tensor,
    u_base: torch.Tensor,
    u_prev: torch.Tensor | None,
    gsplat: GSplatLoader,
    scene_cfg: dict[str, Any],
    trial: int,
    step: int,
    seen: set[tuple[int, ...]],
) -> list[SequenceCandidate]:
    horizon = int(args.horizon)
    rng = np.random.default_rng(91_777 + 3571 * int(trial) + int(step))
    mean_seq = repeat_control(u_base, horizon)
    std = torch.full((horizon, 3), float(args.sequence_noise_scale), device=x.device, dtype=x.dtype)
    out: list[SequenceCandidate] = []
    elite_count = max(1, min(int(args.num_elites), int(args.num_sequences)))
    for cem_iter in range(int(args.cem_iters)):
        sampled: list[tuple[float, torch.Tensor]] = []
        for _ in range(int(args.num_sequences)):
            noise = torch.tensor(rng.normal(size=(horizon, 3)), device=x.device, dtype=x.dtype)
            seq = torch.clamp(mean_seq + noise * std, -0.1, 0.1)
            final_x, hs, min_h = rollout_sequence(x=x, controls=seq, dt=args.dt, gsplat=gsplat, scene_cfg=scene_cfg)
            cost, _, _, _, _ = sequence_cost(args=args, controls=seq, hs=hs, final_x=final_x, goal=goal, u_base=u_base, u_prev=u_prev)
            safety_rank = max(0.0, float(args.dt_margin) - float(min_h))
            sampled.append((float(cost) + 1000.0 * safety_rank, seq))
        sampled.sort(key=lambda item: item[0])
        elites = torch.stack([seq for _, seq in sampled[:elite_count]], dim=0)
        mean_seq = torch.mean(elites, dim=0)
        std = torch.clamp(torch.std(elites, dim=0), min=0.01, max=float(args.sequence_noise_scale))
        for elite_idx, seq in enumerate(elites[: min(8, elite_count)]):
            add_sequence(out, seen, f"cem_iter{cem_iter}_elite{elite_idx}", seq)
    add_sequence(out, seen, "cem_mean", mean_seq)
    return out


def sequence_cost(
    *,
    args: argparse.Namespace,
    controls: torch.Tensor,
    hs: list[float],
    final_x: torch.Tensor,
    goal: torch.Tensor,
    u_base: torch.Tensor,
    u_prev: torch.Tensor | None,
) -> tuple[float, float, float, float, float]:
    base_seq = repeat_control(u_base, int(controls.shape[0]))
    base_dev = float(torch.mean(torch.sum((controls - base_seq) ** 2, dim=1)).detach().cpu().item())
    goal_cost = float(torch.sum((final_x[:3] - goal[:3]) ** 2).detach().cpu().item())
    if int(controls.shape[0]) <= 1:
        smooth_cost = 0.0
    else:
        diffs = controls[1:] - controls[:-1]
        smooth_cost = float(torch.mean(torch.sum(diffs**2, dim=1)).detach().cpu().item())
    if u_prev is not None:
        smooth_cost += float(torch.sum((controls[0] - u_prev) ** 2).detach().cpu().item())
    safety_penalty = float(sum(max(0.0, float(args.dt_margin) - float(h)) ** 2 for h in hs))
    cost = (
        float(args.w_base) * base_dev
        + float(args.w_goal) * goal_cost
        + float(args.w_smooth) * smooth_cost
        + float(args.w_safety) * safety_penalty
    )
    return float(cost), base_dev, goal_cost, smooth_cost, safety_penalty


def evaluate_sequences(
    *,
    args: argparse.Namespace,
    scene: str,
    method: str,
    trial: int,
    step: int,
    x: torch.Tensor,
    goal: torch.Tensor,
    u_base: torch.Tensor,
    u_prev: torch.Tensor | None,
    candidates: list[SequenceCandidate],
    gsplat: GSplatLoader,
    scene_cfg: dict[str, Any],
) -> tuple[SequenceCandidate, torch.Tensor, list[float], float, bool, bool, list[dict[str, Any]], int]:
    rows: list[dict[str, Any]] = []
    best_pass: tuple[float, float, int, SequenceCandidate, torch.Tensor, list[float]] | None = None
    best_h: tuple[float, float, int, SequenceCandidate, torch.Tensor, list[float]] | None = None
    for idx, cand in enumerate(candidates):
        final_x, hs, min_h = rollout_sequence(x=x, controls=cand.controls, dt=args.dt, gsplat=gsplat, scene_cfg=scene_cfg)
        passed = min_h >= float(args.dt_margin)
        cost, base_dev, goal_cost, smooth_cost, safety_penalty = sequence_cost(
            args=args,
            controls=cand.controls,
            hs=hs,
            final_x=final_x,
            goal=goal,
            u_base=u_base,
            u_prev=u_prev,
        )
        row = {
            "scene": scene,
            "method": method,
            "trial": trial,
            "step": step,
            "sequence_id": idx,
            "sequence_source": cand.source,
            "horizon": int(cand.controls.shape[0]),
            "sequence_min_h": min_h,
            "sequence_final_h": hs[-1] if hs else "",
            "sequence_passed_dt_margin": v4b.bool_csv(passed),
            "sequence_cost": cost,
            "sequence_base_deviation": base_dev,
            "sequence_goal_cost": goal_cost,
            "sequence_smooth_cost": smooth_cost,
            "sequence_safety_penalty": safety_penalty,
            "selected": "False",
            "controls_json": tensor_to_json(cand.controls),
            "horizon_h_json": floats_to_json(hs),
        }
        rows.append(row)
        rank = (float(min_h), -float(cost), -idx)
        if best_h is None or rank > (best_h[0], -best_h[1], -best_h[2]):
            best_h = (float(min_h), float(cost), idx, cand, final_x, hs)
        if passed and (best_pass is None or float(cost) < best_pass[1]):
            best_pass = (float(min_h), float(cost), idx, cand, final_x, hs)

    if best_pass is not None:
        selected_min_h, _, selected_idx, selected, _, selected_hs = best_pass
        success = True
        failed = False
    elif best_h is not None:
        selected_min_h, _, selected_idx, selected, _, selected_hs = best_h
        success = False
        failed = True
    else:
        controls = repeat_control(u_base, int(args.horizon))
        final_x, selected_hs, selected_min_h = rollout_sequence(x=x, controls=controls, dt=args.dt, gsplat=gsplat, scene_cfg=scene_cfg)
        selected = SequenceCandidate("empty_fallback_base", controls)
        selected_idx = -1
        success = False
        failed = True

    if selected_idx >= 0:
        rows[selected_idx]["selected"] = "True"
    return selected, selected.controls[0].detach().clone(), selected_hs, float(selected_min_h), success, failed, rows, selected_idx


def should_activate(args: argparse.Namespace, base_horizon_min_h: float) -> bool:
    mode = str(args.activation_mode)
    if mode == "always":
        return True
    if mode == "on_warning":
        return float(base_horizon_min_h) < float(args.warning_margin)
    return float(base_horizon_min_h) < float(args.dt_margin)


def run_trial(
    *,
    args: argparse.Namespace,
    scene: str,
    method: str,
    trial: int,
    scene_cfg: dict[str, Any],
    gsplat: GSplatLoader,
    dynamics: DoubleIntegrator,
    risk_table: v1.RiskScoreTable | None,
    repairs: dict[int, dict[str, str]],
    device: torch.device,
    step_writer: v4b.CsvAppender,
    sequence_writer: v4b.CsvAppender,
    recovery_writer: v4b.CsvAppender,
) -> dict[str, Any]:
    x0, xf = v1.make_start_goal_configs(scene_cfg)
    start_pos, start_meta = v4b.start_for_trial(args=args, trial=trial, x0=x0, repairs=repairs)
    goal_pos = np.asarray(xf[trial], dtype=float)
    x = torch.tensor(start_pos, device=device, dtype=torch.float32)
    x = torch.cat([x, torch.zeros(3, device=device, dtype=torch.float32)])
    goal = torch.tensor(goal_pos, device=device, dtype=torch.float32)
    goal = torch.cat([goal, torch.zeros(3, device=device, dtype=torch.float32)])
    cbf = v4b.make_cbf(args=args, method=method, gsplat=gsplat, dynamics=dynamics, scene_cfg=scene_cfg, risk_table=risk_table)

    safety_values: list[float] = []
    step_times: list[float] = []
    recovery_times: list[float] = []
    control_deltas: list[float] = []
    positions = [x[:3].detach().cpu().numpy()]
    base_violations = 0
    exec_violations = 0
    recovery_used = 0
    recovery_success = 0
    recovery_failed = 0
    qp_infeasible_count = 0
    success = False
    stop_reason = "max_steps"
    u_prev: torch.Tensor | None = None
    start_seconds = time.perf_counter()

    for step_idx in range(int(args.max_steps)):
        step = step_idx + 1
        x_pre = x.clone()
        prev_goal_distance = float(torch.linalg.norm(x_pre[:3] - goal[:3]).detach().cpu().item())
        u_nom = v1.nominal_control(x_pre, goal)
        v1.cuda_sync(device)
        t0 = time.perf_counter()
        u_base = cbf.solve_QP(x_pre, u_nom)
        qp_feasible = bool(cbf.solver_success)
        active_count = int(getattr(cbf, "last_active_constraints_count", 0))
        v1.cuda_sync(device)
        runtime_base = time.perf_counter() - t0
        if not qp_feasible:
            qp_infeasible_count = int(getattr(cbf, "qp_infeasible_count", 1))
            stop_reason = "solver_failed"
            break

        current_h = v4b.query_h(gsplat, x_pre[:3], scene_cfg["radius"])
        base_controls = repeat_control(u_base, int(args.horizon))
        _, base_hs, base_horizon_min_h = rollout_sequence(x=x_pre, controls=base_controls, dt=args.dt, gsplat=gsplat, scene_cfg=scene_cfg)
        base_next_h = base_hs[0] if base_hs else current_h
        base_violation = float(base_horizon_min_h) < float(args.dt_margin)
        if base_violation:
            base_violations += 1

        u_exec = u_base
        exec_hs = list(base_hs)
        exec_horizon_min_h = float(base_horizon_min_h)
        selected_source = "base_no_recovery"
        selected_idx = -1
        activated = should_activate(args, base_horizon_min_h)
        rec_success = False
        rec_failed = False
        sequence_count = 0
        sequence_rows: list[dict[str, Any]] = []
        t_rec = time.perf_counter()
        if activated:
            recovery_used += 1
            candidates = generate_sequences(
                args=args,
                x=x_pre,
                goal=goal,
                u_base=u_base,
                u_nom=u_nom,
                u_prev=u_prev,
                gsplat=gsplat,
                scene_cfg=scene_cfg,
                trial=trial,
                step=step,
            )
            selected, u_exec, exec_hs, exec_horizon_min_h, rec_success, rec_failed, sequence_rows, selected_idx = evaluate_sequences(
                args=args,
                scene=scene,
                method=method,
                trial=trial,
                step=step,
                x=x_pre,
                goal=goal,
                u_base=u_base,
                u_prev=u_prev,
                candidates=candidates,
                gsplat=gsplat,
                scene_cfg=scene_cfg,
            )
            selected_source = selected.source
            sequence_count = len(candidates)
            recovery_success += int(rec_success)
            recovery_failed += int(rec_failed)
            for row in sequence_rows:
                sequence_writer.write(row)
        runtime_recovery = time.perf_counter() - t_rec if activated else 0.0
        recovery_times.append(runtime_recovery)

        x = double_integrator_dynamics(x_pre, u_exec) * float(args.dt) + x_pre
        actual_h = v4b.query_h(gsplat, x[:3], scene_cfg["radius"])
        exec_next_h = exec_hs[0] if exec_hs else actual_h
        safety_values.append(actual_h)
        positions.append(x[:3].detach().cpu().numpy())
        exec_violation = float(exec_horizon_min_h) < float(args.dt_margin)
        if exec_violation:
            exec_violations += 1
        control_delta = float(torch.linalg.norm(u_exec - u_base).detach().cpu().item())
        control_deltas.append(control_delta)
        step_times.append(runtime_base + runtime_recovery)
        goal_distance = float(torch.linalg.norm(x[:3] - goal[:3]).detach().cpu().item())
        goal_progress_delta = prev_goal_distance - goal_distance
        collision_step = actual_h < 0.0

        step_writer.write(
            {
                "scene": scene,
                "method": method,
                "trial": trial,
                "step": step,
                "current_h": current_h,
                "base_next_h": base_next_h,
                "exec_next_h": exec_next_h,
                "actual_next_h": actual_h,
                "base_horizon_min_h": base_horizon_min_h,
                "exec_horizon_min_h": exec_horizon_min_h,
                "dt_margin": args.dt_margin,
                "warning_margin": args.warning_margin,
                "activation_mode": args.activation_mode,
                "base_horizon_margin_violation": v4b.bool_csv(base_violation),
                "exec_horizon_margin_violation": v4b.bool_csv(exec_violation),
                "predictive_recovery_used": v4b.bool_csv(activated),
                "predictive_recovery_success": v4b.bool_csv(rec_success if activated else None),
                "recovery_failed": v4b.bool_csv(rec_failed if activated else None),
                "sequence_count": sequence_count,
                "selected_sequence_id": selected_idx,
                "selected_sequence_source": selected_source,
                "runtime_step": runtime_base + runtime_recovery,
                "runtime_recovery": runtime_recovery,
                "active_constraints_count": active_count,
                "collision_step_flag": v4b.bool_csv(collision_step),
                "qp_infeasible": v4b.bool_csv(False),
                "goal_distance": goal_distance,
                "goal_progress_delta": goal_progress_delta,
            }
        )
        if activated:
            recovery_writer.write(
                {
                    "scene": scene,
                    "method": method,
                    "trial": trial,
                    "step": step,
                    "u_base_x": float(u_base[0].detach().cpu().item()),
                    "u_base_y": float(u_base[1].detach().cpu().item()),
                    "u_base_z": float(u_base[2].detach().cpu().item()),
                    "u_exec_x": float(u_exec[0].detach().cpu().item()),
                    "u_exec_y": float(u_exec[1].detach().cpu().item()),
                    "u_exec_z": float(u_exec[2].detach().cpu().item()),
                    "control_delta_norm": control_delta,
                    "base_horizon_min_h": base_horizon_min_h,
                    "exec_horizon_min_h": exec_horizon_min_h,
                    "horizon_h_improvement": float(exec_horizon_min_h) - float(base_horizon_min_h),
                    "predictive_recovery_used": v4b.bool_csv(activated),
                    "predictive_recovery_success": v4b.bool_csv(rec_success),
                    "recovery_failed": v4b.bool_csv(rec_failed),
                    "selected_sequence_id": selected_idx,
                    "selected_sequence_source": selected_source,
                }
            )
        u_prev = u_exec.detach().clone()

        if torch.linalg.norm(x - x_pre) < float(args.goal_tolerance):
            success = bool(torch.linalg.norm(x_pre - goal) < float(args.goal_tolerance))
            stop_reason = "reached_goal" if success else "stopped_before_goal"
            break
        if step_idx >= int(args.max_steps) - 1:
            success = True
            stop_reason = "max_steps_loose_success"

    qp_infeasible_count = int(getattr(cbf, "qp_infeasible_count", qp_infeasible_count))
    seconds_total = time.perf_counter() - start_seconds
    positions_np = np.asarray(positions, dtype=float)
    goal_distances = np.linalg.norm(positions_np - goal_pos[None, :], axis=1)
    initial_goal_distance = float(np.linalg.norm(np.asarray(start_pos, dtype=float) - goal_pos))
    final_goal_distance = float(goal_distances[-1]) if len(goal_distances) else ""
    closest_goal_distance = float(np.min(goal_distances)) if len(goal_distances) else ""
    ratio = (initial_goal_distance - final_goal_distance) / initial_goal_distance if initial_goal_distance else ""
    min_safety = min(safety_values) if safety_values else ""
    collision = bool(min_safety < 0.0) if min_safety != "" else None
    return {
        "scene": scene,
        "method": method,
        "trial": trial,
        "use_startguard": v4b.bool_csv(args.use_startguard),
        "start_source": start_meta["start_source"],
        "navigation_executed": "True",
        "success": v4b.bool_csv(success),
        "collision": v4b.bool_csv(collision),
        "collision_free": v4b.bool_csv(False if collision is True else (True if collision is False else None)),
        "stop_reason": stop_reason,
        "num_steps": len(safety_values),
        "min_safety_h": min_safety,
        "base_horizon_margin_violation_count": base_violations,
        "exec_horizon_margin_violation_count": exec_violations,
        "horizon_margin_violation_reduction": base_violations - exec_violations,
        "predictive_recovery_used_count": recovery_used,
        "predictive_recovery_success_count": recovery_success,
        "recovery_failed_count": recovery_failed,
        "qp_infeasible_count": qp_infeasible_count,
        "goal_distance_reduction_ratio": ratio,
        "initial_goal_distance": initial_goal_distance,
        "final_goal_distance": final_goal_distance,
        "closest_goal_distance": closest_goal_distance,
        "runtime_mean": v4b.mean(step_times),
        "runtime_p95": v4b.percentile(step_times, 95),
        "runtime_recovery_mean": v4b.mean(recovery_times),
        "runtime_recovery_p95": v4b.percentile(recovery_times, 95),
        "control_delta_mean": v4b.mean(control_deltas),
        "control_delta_p95": v4b.percentile(control_deltas, 95),
        "seconds_total": seconds_total,
        "repair_used": start_meta["repair_used"],
        "repair_success": start_meta["repair_success"],
        "repair_distance": start_meta["repair_distance"],
        "repair_method": start_meta["repair_method"],
        "full_query_verified": start_meta["full_query_verified"],
        "error": "",
    }


def summarize(rows: list[dict[str, Any]]) -> list[dict[str, Any]]:
    if not rows:
        return []
    out = []
    keys = sorted({(r.get("scene", ""), r.get("method", "")) for r in rows})
    for scene, method in keys:
        group = [r for r in rows if r.get("scene") == scene and r.get("method") == method]
        executed = [r for r in group if v4b.parse_bool(r.get("navigation_executed"))]
        h = [v for v in (v4b.parse_float(r.get("min_safety_h")) for r in executed) if v is not None]
        progress = [v for v in (v4b.parse_float(r.get("goal_distance_reduction_ratio")) for r in executed) if v is not None]
        runtime = [v for v in (v4b.parse_float(r.get("runtime_mean")) for r in executed) if v is not None]
        runtime_p95 = [v for v in (v4b.parse_float(r.get("runtime_p95")) for r in executed) if v is not None]
        runtime_rec = [v for v in (v4b.parse_float(r.get("runtime_recovery_mean")) for r in executed) if v is not None]
        control_delta = [v for v in (v4b.parse_float(r.get("control_delta_mean")) for r in executed) if v is not None]
        base_v = sum(int(v4b.parse_float(r.get("base_horizon_margin_violation_count")) or 0) for r in executed)
        exec_v = sum(int(v4b.parse_float(r.get("exec_horizon_margin_violation_count")) or 0) for r in executed)
        out.append(
            {
                "scene": scene,
                "method": method,
                "rows": len(group),
                "navigation_executed_count": len(executed),
                "collision_count": sum(v4b.parse_bool(r.get("collision")) for r in executed),
                "collision_free_count": sum(v4b.parse_bool(r.get("collision_free")) for r in executed),
                "qp_infeasible_count": sum(int(v4b.parse_float(r.get("qp_infeasible_count")) or 0) for r in executed),
                "num_steps": sum(int(v4b.parse_float(r.get("num_steps")) or 0) for r in executed),
                "base_horizon_margin_violation_count": base_v,
                "exec_horizon_margin_violation_count": exec_v,
                "horizon_margin_violation_reduction": base_v - exec_v,
                "predictive_recovery_used_count": sum(int(v4b.parse_float(r.get("predictive_recovery_used_count")) or 0) for r in executed),
                "predictive_recovery_success_count": sum(int(v4b.parse_float(r.get("predictive_recovery_success_count")) or 0) for r in executed),
                "recovery_failed_count": sum(int(v4b.parse_float(r.get("recovery_failed_count")) or 0) for r in executed),
                "progress_mean": v4b.mean(progress),
                "runtime_mean": v4b.mean(runtime),
                "runtime_p95": v4b.mean(runtime_p95),
                "runtime_recovery_mean": v4b.mean(runtime_rec),
                "control_delta_mean": v4b.mean(control_delta),
                "min_safety_h_min": min(h) if h else "",
            }
        )
    return out


def write_plot(output_dir: Path, summary: list[dict[str, Any]]) -> None:
    if not summary:
        return
    row = summary[0]
    fig, axes = plt.subplots(1, 3, figsize=(12, 4))
    axes[0].bar(
        ["base", "exec"],
        [float(row.get("base_horizon_margin_violation_count") or 0.0), float(row.get("exec_horizon_margin_violation_count") or 0.0)],
        color=["#c0504d", "#4f81bd"],
    )
    axes[0].set_title("H-step margin violations")
    axes[1].bar(
        ["used", "success", "failed"],
        [
            float(row.get("predictive_recovery_used_count") or 0.0),
            float(row.get("predictive_recovery_success_count") or 0.0),
            float(row.get("recovery_failed_count") or 0.0),
        ],
    )
    axes[1].set_title("predictive recovery")
    axes[2].bar(
        ["runtime", "recovery"],
        [float(row.get("runtime_mean") or 0.0), float(row.get("runtime_recovery_mean") or 0.0)],
    )
    axes[2].set_title("runtime mean")
    fig.tight_layout()
    fig.savefig(output_dir / "comparison_plot.png", dpi=170)
    plt.close(fig)


def run(args: argparse.Namespace) -> list[dict[str, Any]]:
    output_dir = Path(args.output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)
    logger = v4b.Logger(output_dir / "run_log.txt")
    trial_writer = v4b.CsvAppender(output_dir / "trials.csv", TRIAL_FIELDS)
    step_writer = v4b.CsvAppender(output_dir / "v4c_step_debug.csv", STEP_FIELDS)
    sequence_writer = v4b.CsvAppender(output_dir / "v4c_sequence_debug.csv", SEQUENCE_FIELDS)
    recovery_writer = v4b.CsvAppender(output_dir / "v4c_recovery_debug.csv", RECOVERY_FIELDS)
    try:
        logger.log(f"script={Path(__file__).resolve()}")
        logger.log(f"scene={args.scene} method={args.method} output_dir={output_dir}")
        logger.log(f"horizon={args.horizon} num_sequences={args.num_sequences} activation_mode={args.activation_mode}")
        scene_cfg = v1.SCENES[args.scene]
        trials = v4b.parse_trials(args)
        logger.log(f"trials={trials}")
        device = torch.device(args.device)
        if device.type == "cuda" and not torch.cuda.is_available():
            raise RuntimeError("CUDA requested but unavailable")
        gsplat = GSplatLoader(scene_cfg["path_to_gsplat"], device)
        dynamics = DoubleIntegrator(device=device, ndim=3)
        risk_table = None
        if args.method == "risk_aware_v1_bestD":
            risk_score_table = args.risk_score_table
            if risk_score_table is None:
                risk_score_table = Path(f"work/risk_aware_cbf/results/{args.scene}_risk_score_table_v0.csv")
                if args.scene == "stonehenge":
                    risk_score_table = Path("work/risk_aware_cbf/results/risk_score_table_v0.csv")
            risk_table = v1.RiskScoreTable(risk_score_table, int(gsplat.means.shape[0]))
            logger.log(f"loaded_risk_score_table={risk_score_table}")
        repairs = v4b.load_startguard_repairs(args.startguard_projection_dir) if args.use_startguard else {}
        completed = v4b.completed_trials(output_dir / "trials.csv") if args.resume else set()
        for trial in trials:
            key = (args.scene, args.method, trial)
            if args.skip_existing and key in completed:
                logger.log(f"skip_existing trial={trial}")
                continue
            logger.log(f"start trial={trial}")
            try:
                row = run_trial(
                    args=args,
                    scene=args.scene,
                    method=args.method,
                    trial=trial,
                    scene_cfg=scene_cfg,
                    gsplat=gsplat,
                    dynamics=dynamics,
                    risk_table=risk_table,
                    repairs=repairs,
                    device=device,
                    step_writer=step_writer,
                    sequence_writer=sequence_writer,
                    recovery_writer=recovery_writer,
                )
                logger.log(
                    f"done trial={trial} collision={row['collision']} base_h={row['base_horizon_margin_violation_count']} "
                    f"exec_h={row['exec_horizon_margin_violation_count']} recovery={row['predictive_recovery_used_count']} "
                    f"failed={row['recovery_failed_count']}"
                )
            except Exception as exc:  # noqa: BLE001
                logger.log(f"error trial={trial}: {exc!r}")
                logger.log(traceback.format_exc())
                row = {field: "" for field in TRIAL_FIELDS}
                row.update(
                    {
                        "scene": args.scene,
                        "method": args.method,
                        "trial": trial,
                        "navigation_executed": "False",
                        "success": "False",
                        "stop_reason": "error",
                        "error": repr(exc),
                    }
                )
            trial_writer.write(row)
        rows = v4b.read_rows(output_dir / "trials.csv")
        summary = summarize(rows)
        v4b.write_csv(output_dir / "summary.csv", summary, SUMMARY_FIELDS)
        with (output_dir / "metrics.json").open("w", encoding="utf-8") as fh:
            json.dump(v4b.json_ready({"args": vars(args), "summary": summary}), fh, indent=2)
        write_plot(output_dir, summary)
        logger.log(f"summary={summary}")
        return rows
    finally:
        trial_writer.close()
        step_writer.close()
        sequence_writer.close()
        recovery_writer.close()
        logger.close()


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="V4-C H-step predictive safety recovery.")
    parser.add_argument("--scene", choices=["flight", "stonehenge"], required=True)
    parser.add_argument("--trial-start", type=int, default=None)
    parser.add_argument("--trial-end", type=int, default=None)
    parser.add_argument("--trial-list", type=Path, default=None)
    parser.add_argument("--method", choices=["risk_aware_v1_bestD", "safer_splat_filter"], required=True)
    parser.add_argument("--startguard-projection-dir", type=Path, default=None)
    parser.add_argument("--use-startguard", action="store_true")
    parser.add_argument("--safety-margin", type=float, default=0.0005)
    parser.add_argument("--dt-margin", type=float, default=0.0005)
    parser.add_argument("--warning-margin", type=float, default=0.0008)
    parser.add_argument("--dt", type=float, default=0.05)
    parser.add_argument("--max-steps", type=int, default=800)
    parser.add_argument("--candidate-budget", type=int, default=2000)
    parser.add_argument("--near-distance-threshold", type=float, default=0.05)
    parser.add_argument("--heading-distance-threshold", type=float, default=0.25)
    parser.add_argument("--heading-cos-threshold", type=float, default=0.5)
    parser.add_argument("--risk-score", choices=["risk_v0_active_frequency", "risk_v1_geometry", "risk_v2_hybrid"], default="risk_v2_hybrid")
    parser.add_argument("--risk-score-table", type=Path, default=None)
    parser.add_argument("--min-candidate-budget", type=int, default=200)
    parser.add_argument("--horizon", type=int, default=3)
    parser.add_argument("--num-sequences", type=int, default=128)
    parser.add_argument("--num-elites", type=int, default=16)
    parser.add_argument("--sequence-noise-scale", type=float, default=0.15)
    parser.add_argument("--control-scale-list", type=str, default="0,0.25,0.5,0.75,1.0")
    parser.add_argument("--include-braking-sequences", action="store_true")
    parser.add_argument("--include-repulsive-sequences", action="store_true")
    parser.add_argument("--include-goal-directed-sequences", action="store_true")
    parser.add_argument("--use-cem", action="store_true")
    parser.add_argument("--cem-iters", type=int, default=2)
    parser.add_argument("--w-base", type=float, default=1.0)
    parser.add_argument("--w-goal", type=float, default=0.2)
    parser.add_argument("--w-smooth", type=float, default=0.1)
    parser.add_argument("--w-safety", type=float, default=10.0)
    parser.add_argument("--activation-mode", choices=["always", "on_margin_violation", "on_warning"], default="on_margin_violation")
    parser.add_argument("--goal-tolerance", type=float, default=0.001)
    parser.add_argument("--output-dir", type=Path, required=True)
    parser.add_argument("--resume", action="store_true")
    parser.add_argument("--skip-existing", action="store_true")
    parser.add_argument("--device", choices=["cuda", "cpu"], default="cuda")
    return parser


def main() -> int:
    args = build_parser().parse_args()
    if (args.trial_start is None) != (args.trial_end is None):
        raise ValueError("Provide both --trial-start and --trial-end, or neither")
    if args.trial_start is not None and (args.trial_start < 0 or args.trial_end < args.trial_start or args.trial_end >= 100):
        raise ValueError("trial range must be inclusive within [0, 99]")
    if args.horizon < 1:
        raise ValueError("--horizon must be positive")
    if args.num_elites < 1:
        raise ValueError("--num-elites must be positive")
    run(args)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
