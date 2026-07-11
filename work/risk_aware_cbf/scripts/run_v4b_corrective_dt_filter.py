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


METHOD_TO_V1 = {
    "risk_aware_v1_bestD": "risk_aware_v1_pre_cbf",
    "safer_splat_filter": "safer_splat_filter",
}

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
    "base_margin_violation_count",
    "exec_margin_violation_count",
    "correction_used_count",
    "correction_success_count",
    "correction_failed_count",
    "qp_infeasible_count",
    "goal_distance_reduction_ratio",
    "initial_goal_distance",
    "final_goal_distance",
    "closest_goal_distance",
    "runtime_mean",
    "runtime_p95",
    "runtime_correction_mean",
    "runtime_correction_p95",
    "control_delta_mean",
    "control_delta_p95",
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
    "base_predicted_next_h",
    "exec_predicted_next_h",
    "actual_next_h",
    "dt_margin",
    "base_margin_violation",
    "exec_margin_violation",
    "dt_correction_used",
    "dt_correction_success",
    "correction_failed",
    "candidate_count",
    "selected_candidate_source",
    "runtime_step",
    "runtime_correction",
    "active_constraints_count",
    "collision_step_flag",
    "qp_infeasible",
    "goal_distance",
    "goal_progress_delta",
]

CANDIDATE_FIELDS = [
    "scene",
    "trial",
    "step",
    "candidate_id",
    "candidate_source",
    "candidate_u_x",
    "candidate_u_y",
    "candidate_u_z",
    "candidate_predicted_next_h",
    "candidate_passed_dt_margin",
    "candidate_cost",
    "candidate_base_deviation",
    "candidate_goal_cost",
    "candidate_smooth_cost",
    "selected",
]

CORRECTION_FIELDS = [
    "scene",
    "trial",
    "step",
    "u_base_x",
    "u_base_y",
    "u_base_z",
    "u_exec_x",
    "u_exec_y",
    "u_exec_z",
    "control_delta_norm",
    "base_predicted_next_h",
    "exec_predicted_next_h",
    "h_improvement",
    "dt_correction_used",
    "dt_correction_success",
    "correction_failed",
    "selected_candidate_source",
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
    "base_margin_violation_count",
    "exec_margin_violation_count",
    "margin_violation_reduction",
    "correction_used_count",
    "correction_success_count",
    "correction_failed_count",
    "progress_mean",
    "runtime_mean",
    "runtime_p95",
    "runtime_correction_mean",
    "control_delta_mean",
    "min_safety_h_min",
]


class Logger:
    def __init__(self, path: Path):
        self.path = path
        self.path.parent.mkdir(parents=True, exist_ok=True)
        self._fh = path.open("a", encoding="utf-8")

    def log(self, message: str) -> None:
        line = f"[{datetime.now().isoformat(timespec='seconds')}] {message}"
        print(line, flush=True)
        self._fh.write(line + "\n")
        self._fh.flush()

    def close(self) -> None:
        self._fh.close()


class CsvAppender:
    def __init__(self, path: Path, fieldnames: list[str]):
        self.path = path
        self.fieldnames = fieldnames
        self.path.parent.mkdir(parents=True, exist_ok=True)
        exists = self.path.exists() and self.path.stat().st_size > 0
        self._fh = self.path.open("a", newline="", encoding="utf-8")
        self._writer = csv.DictWriter(self._fh, fieldnames=fieldnames, extrasaction="ignore")
        if not exists:
            self._writer.writeheader()
            self._fh.flush()

    def write(self, row: dict[str, Any]) -> None:
        self._writer.writerow({field: row.get(field, "") for field in self.fieldnames})
        self._fh.flush()

    def close(self) -> None:
        self._fh.close()


def bool_csv(value: bool | None) -> str:
    if value is None:
        return ""
    return "True" if value else "False"


def parse_bool(value: Any) -> bool:
    return str(value).strip().lower() in {"true", "1", "yes"}


def parse_float(value: Any) -> float | None:
    if value in ("", None):
        return None
    try:
        out = float(value)
    except (TypeError, ValueError):
        return None
    return out if math.isfinite(out) else None


def parse_csv_floats(text: str) -> list[float]:
    return [float(v.strip()) for v in str(text).split(",") if v.strip()]


def read_rows(path: Path) -> list[dict[str, str]]:
    if not path.exists():
        return []
    with path.open("r", newline="", encoding="utf-8") as fh:
        return list(csv.DictReader(fh))


def write_csv(path: Path, rows: list[dict[str, Any]], fieldnames: list[str]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", newline="", encoding="utf-8") as fh:
        writer = csv.DictWriter(fh, fieldnames=fieldnames, extrasaction="ignore")
        writer.writeheader()
        for row in rows:
            writer.writerow({field: row.get(field, "") for field in fieldnames})


def json_ready(value: Any) -> Any:
    if isinstance(value, Path):
        return str(value)
    if isinstance(value, dict):
        return {str(k): json_ready(v) for k, v in value.items()}
    if isinstance(value, (list, tuple)):
        return [json_ready(v) for v in value]
    if isinstance(value, np.ndarray):
        return value.tolist()
    if isinstance(value, (np.integer,)):
        return int(value)
    if isinstance(value, (np.floating,)):
        return float(value)
    if isinstance(value, (np.bool_,)):
        return bool(value)
    return value


def mean(values: list[float]) -> float | str:
    clean = [float(v) for v in values if math.isfinite(float(v))]
    return float(np.mean(clean)) if clean else ""


def percentile(values: list[float], q: float) -> float | str:
    clean = [float(v) for v in values if math.isfinite(float(v))]
    return float(np.percentile(np.asarray(clean, dtype=float), q)) if clean else ""


def completed_trials(path: Path) -> set[tuple[str, str, int]]:
    done: set[tuple[str, str, int]] = set()
    for row in read_rows(path):
        try:
            done.add((row.get("scene", ""), row.get("method", ""), int(row.get("trial", "-1"))))
        except ValueError:
            continue
    return done


def parse_trials(args: argparse.Namespace) -> list[int]:
    trials: list[int] = []
    if args.trial_list:
        rows = read_rows(Path(args.trial_list))
        if rows:
            for row in rows:
                if parse_bool(row.get("repair_used")) and (row.get("trial", "").strip().isdigit()):
                    trials.append(int(row["trial"]))
        else:
            with Path(args.trial_list).open("r", encoding="utf-8") as fh:
                for line in fh:
                    line = line.strip()
                    if line and not line.startswith("#"):
                        trials.append(int(line.split(",")[0]))
    if args.trial_start is not None and args.trial_end is not None:
        trials.extend(range(args.trial_start, args.trial_end + 1))
    if not trials:
        raise ValueError("Provide --trial-list or --trial-start/--trial-end")
    unique = sorted(set(trials))
    if any(t < 0 or t >= 100 for t in unique):
        raise ValueError("trial values must be in [0, 99]")
    return unique


def load_startguard_repairs(path: Path | None, method: str = "active_set_verified_projection") -> dict[int, dict[str, str]]:
    if path is None:
        return {}
    csv_path = path / "repair_needed_projection_trials.csv"
    if not csv_path.exists():
        csv_path = path / "projection_trials.csv"
    rows = read_rows(csv_path)
    out: dict[int, dict[str, str]] = {}
    for row in rows:
        if row.get("method") != method:
            continue
        if not parse_bool(row.get("repair_success")) or not parse_bool(row.get("full_query_verified")):
            continue
        try:
            out[int(row["trial"])] = row
        except (KeyError, ValueError):
            continue
    return out


def query_h(gsplat: GSplatLoader, pos: torch.Tensor, radius: float) -> float:
    with torch.no_grad():
        h, _, _, _ = gsplat.query_distance(pos[:3], radius=radius, distance_type="ball-to-ellipsoid")
        return float(torch.min(h.reshape(-1)).detach().cpu().item())


def query_h_and_critical(gsplat: GSplatLoader, pos: torch.Tensor, radius: float) -> tuple[float, int]:
    with torch.no_grad():
        h, _, _, _ = gsplat.query_distance(pos[:3], radius=radius, distance_type="ball-to-ellipsoid")
        h_flat = h.reshape(-1)
        idx = int(torch.argmin(h_flat).detach().cpu().item())
        return float(h_flat[idx].detach().cpu().item()), idx


def clamp_control(u: torch.Tensor) -> torch.Tensor:
    return torch.clamp(u, -0.1, 0.1)


def unit_or_zero(vec: torch.Tensor) -> torch.Tensor:
    norm = torch.linalg.norm(vec)
    if float(norm.detach().cpu().item()) <= 1e-12:
        return torch.zeros_like(vec)
    return vec / norm


def make_cbf(
    *,
    args: argparse.Namespace,
    method: str,
    gsplat: GSplatLoader,
    dynamics: DoubleIntegrator,
    scene_cfg: dict[str, Any],
    risk_table: v1.RiskScoreTable | None,
):
    alpha = 5.0
    beta = 1.0
    distance_type = "ball-to-ellipsoid"
    mapped = METHOD_TO_V1[method]
    if mapped == "safer_splat_filter":
        return v1.DetailedCBF(gsplat, dynamics, alpha, beta, scene_cfg["radius"], distance_type=distance_type)
    if mapped == "risk_aware_v1_pre_cbf":
        if risk_table is None:
            raise ValueError("risk_aware_v1_bestD requires risk score table")
        subset_loader = v1.SubsetGSplatLoader(gsplat)
        selector = v1.V1CandidateSelector(
            gsplat=gsplat,
            risk_table=risk_table,
            candidate_budget=args.candidate_budget,
            near_distance_threshold=args.near_distance_threshold,
            heading_distance_threshold=args.heading_distance_threshold,
            heading_cos_threshold=args.heading_cos_threshold,
            risk_score_name=args.risk_score,
            min_candidate_budget=args.min_candidate_budget,
        )
        return v1.RiskAwareV1PreCBFCBF(
            subset_loader,
            dynamics,
            alpha,
            beta,
            scene_cfg["radius"],
            distance_type=distance_type,
            selector=selector,
            subset_loader=subset_loader,
        )
    raise ValueError(f"Unsupported method: {method}")


@dataclass
class Candidate:
    source: str
    u: torch.Tensor


def add_candidate(candidates: list[Candidate], source: str, u: torch.Tensor, seen: set[tuple[int, int, int]]) -> None:
    u = clamp_control(u)
    key = tuple(int(round(float(v) * 1_000_000)) for v in u.detach().cpu().numpy())
    if key in seen:
        return
    seen.add(key)
    candidates.append(Candidate(source=source, u=u))


def generate_candidates(
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
) -> list[Candidate]:
    candidates: list[Candidate] = []
    seen: set[tuple[int, int, int]] = set()
    scales = parse_csv_floats(args.control_scale_list)
    for scale in scales:
        add_candidate(candidates, f"scaled_base_{scale:g}", float(scale) * u_base, seen)
    add_candidate(candidates, "base", u_base, seen)
    add_candidate(candidates, "nominal_goal_control", u_nom, seen)

    if args.include_goal_directed_controls:
        goal_dir = unit_or_zero(goal[:3] - x[:3])
        for mag in (0.025, 0.05, 0.1):
            add_candidate(candidates, f"goal_directed_{mag:g}", mag * goal_dir, seen)

    if args.include_braking_controls:
        vel = x[3:6]
        for gain in (0.25, 0.5, 1.0, 1.5):
            add_candidate(candidates, f"braking_{gain:g}", -gain * vel, seen)
            add_candidate(candidates, f"base_plus_braking_{gain:g}", u_base - gain * vel, seen)

    if args.include_repulsive_controls:
        try:
            _, gid = query_h_and_critical(gsplat, x[:3], scene_cfg["radius"])
            away = unit_or_zero(x[:3] - gsplat.means[gid])
            for mag in (0.025, 0.05, 0.1):
                add_candidate(candidates, f"repulsive_{mag:g}", mag * away, seen)
                add_candidate(candidates, f"base_plus_repulsive_{mag:g}", u_base + mag * away, seen)
        except Exception:
            pass

    rng = np.random.default_rng(31_337 + 1009 * int(trial) + int(step))
    for idx in range(int(args.num_control_samples)):
        noise = torch.tensor(rng.normal(size=3), device=x.device, dtype=x.dtype)
        noise = float(args.control_noise_scale) * noise
        add_candidate(candidates, f"random_around_base_{idx}", u_base + noise, seen)

    if u_prev is not None:
        add_candidate(candidates, "previous_control", u_prev, seen)
        add_candidate(candidates, "smooth_half_prev_half_base", 0.5 * (u_prev + u_base), seen)
    return candidates


def evaluate_candidates(
    *,
    args: argparse.Namespace,
    scene: str,
    trial: int,
    step: int,
    x: torch.Tensor,
    goal: torch.Tensor,
    u_base: torch.Tensor,
    u_prev: torch.Tensor | None,
    candidates: list[Candidate],
    gsplat: GSplatLoader,
    scene_cfg: dict[str, Any],
) -> tuple[Candidate, float, bool, bool, list[dict[str, Any]]]:
    rows: list[dict[str, Any]] = []
    best_pass: tuple[float, int, Candidate, float] | None = None
    best_h: tuple[float, int, Candidate, float] | None = None
    for idx, cand in enumerate(candidates):
        pred = double_integrator_dynamics(x, cand.u) * float(args.dt) + x
        h_pred = query_h(gsplat, pred[:3], scene_cfg["radius"])
        passed = h_pred >= args.dt_margin
        base_dev = float(torch.sum((cand.u - u_base) ** 2).detach().cpu().item())
        goal_cost = float(torch.sum((pred[:3] - goal[:3]) ** 2).detach().cpu().item())
        smooth_cost = 0.0 if u_prev is None else float(torch.sum((cand.u - u_prev) ** 2).detach().cpu().item())
        cost = float(args.w_base) * base_dev + float(args.w_goal) * goal_cost + float(args.w_smooth) * smooth_cost
        row = {
            "scene": scene,
            "trial": trial,
            "step": step,
            "candidate_id": idx,
            "candidate_source": cand.source,
            "candidate_u_x": float(cand.u[0].detach().cpu().item()),
            "candidate_u_y": float(cand.u[1].detach().cpu().item()),
            "candidate_u_z": float(cand.u[2].detach().cpu().item()),
            "candidate_predicted_next_h": h_pred,
            "candidate_passed_dt_margin": bool_csv(passed),
            "candidate_cost": cost,
            "candidate_base_deviation": base_dev,
            "candidate_goal_cost": goal_cost,
            "candidate_smooth_cost": smooth_cost,
            "selected": "False",
        }
        rows.append(row)
        if best_h is None or h_pred > best_h[0]:
            best_h = (h_pred, idx, cand, cost)
        if passed and (best_pass is None or cost < best_pass[3]):
            best_pass = (h_pred, idx, cand, cost)

    if best_pass is not None:
        selected_h, selected_idx, selected, _ = best_pass
        success = True
        failed = False
    elif best_h is not None:
        selected_h, selected_idx, selected, _ = best_h
        success = False
        failed = True
    else:
        selected = Candidate("empty_fallback_base", u_base)
        selected_h = query_h(gsplat, (double_integrator_dynamics(x, u_base) * float(args.dt) + x)[:3], scene_cfg["radius"])
        selected_idx = -1
        success = False
        failed = True

    if selected_idx >= 0:
        rows[selected_idx]["selected"] = "True"
    return selected, selected_h, success, failed, rows


def start_for_trial(
    *,
    args: argparse.Namespace,
    trial: int,
    x0: np.ndarray,
    repairs: dict[int, dict[str, str]],
) -> tuple[np.ndarray, dict[str, Any]]:
    original = np.asarray(x0[trial], dtype=float)
    if not args.use_startguard or trial not in repairs:
        return original, {
            "start_source": "original_start",
            "repair_used": "False",
            "repair_success": "",
            "repair_distance": 0.0,
            "repair_method": "",
            "full_query_verified": "",
        }
    row = repairs[trial]
    start = np.asarray(
        [float(row["repaired_start_x"]), float(row["repaired_start_y"]), float(row["repaired_start_z"])],
        dtype=float,
    )
    return start, {
        "start_source": "startguard_active_projection",
        "repair_used": "True",
        "repair_success": row.get("repair_success", ""),
        "repair_distance": row.get("repair_distance", ""),
        "repair_method": row.get("method", "active_set_verified_projection"),
        "full_query_verified": row.get("full_query_verified", ""),
    }


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
    step_writer: CsvAppender,
    candidate_writer: CsvAppender,
    correction_writer: CsvAppender,
) -> dict[str, Any]:
    x0, xf = v1.make_start_goal_configs(scene_cfg)
    start_pos, start_meta = start_for_trial(args=args, trial=trial, x0=x0, repairs=repairs)
    goal_pos = np.asarray(xf[trial], dtype=float)
    x = torch.tensor(start_pos, device=device, dtype=torch.float32)
    x = torch.cat([x, torch.zeros(3, device=device, dtype=torch.float32)])
    goal = torch.tensor(goal_pos, device=device, dtype=torch.float32)
    goal = torch.cat([goal, torch.zeros(3, device=device, dtype=torch.float32)])
    cbf = make_cbf(args=args, method=method, gsplat=gsplat, dynamics=dynamics, scene_cfg=scene_cfg, risk_table=risk_table)

    safety_values: list[float] = []
    step_times: list[float] = []
    correction_times: list[float] = []
    control_deltas: list[float] = []
    positions = [x[:3].detach().cpu().numpy()]
    base_violations = 0
    exec_violations = 0
    correction_used = 0
    correction_success = 0
    correction_failed = 0
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
            success = False
            stop_reason = "solver_failed"
            break

        current_h = query_h(gsplat, x_pre[:3], scene_cfg["radius"])
        pred_base = double_integrator_dynamics(x_pre, u_base) * float(args.dt) + x_pre
        base_h = query_h(gsplat, pred_base[:3], scene_cfg["radius"])
        base_violation = base_h < float(args.dt_margin)
        if base_violation:
            base_violations += 1

        u_exec = u_base
        exec_h = base_h
        selected_source = "base_no_correction"
        used = False
        corr_success = False
        corr_failed = False
        candidate_count = 0
        t_corr = time.perf_counter()
        candidate_rows: list[dict[str, Any]] = []
        if base_violation:
            used = True
            correction_used += 1
            candidates = generate_candidates(
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
            selected, exec_h, corr_success, corr_failed, candidate_rows = evaluate_candidates(
                args=args,
                scene=scene,
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
            u_exec = selected.u
            selected_source = selected.source
            candidate_count = len(candidates)
            correction_success += int(corr_success)
            correction_failed += int(corr_failed)
            for row in candidate_rows:
                candidate_writer.write(row)
        runtime_correction = time.perf_counter() - t_corr if used else 0.0
        correction_times.append(runtime_correction)

        x = double_integrator_dynamics(x_pre, u_exec) * float(args.dt) + x_pre
        actual_h = query_h(gsplat, x[:3], scene_cfg["radius"])
        safety_values.append(actual_h)
        positions.append(x[:3].detach().cpu().numpy())
        exec_violation = exec_h < float(args.dt_margin)
        if exec_violation:
            exec_violations += 1
        control_delta = float(torch.linalg.norm(u_exec - u_base).detach().cpu().item())
        control_deltas.append(control_delta)
        step_times.append(runtime_base + runtime_correction)
        goal_distance = float(torch.linalg.norm(x[:3] - goal[:3]).detach().cpu().item())
        goal_progress_delta = prev_goal_distance - goal_distance
        collision_step = actual_h < 0.0

        step_row = {
            "scene": scene,
            "method": method,
            "trial": trial,
            "step": step,
            "current_h": current_h,
            "base_predicted_next_h": base_h,
            "exec_predicted_next_h": exec_h,
            "actual_next_h": actual_h,
            "dt_margin": args.dt_margin,
            "base_margin_violation": bool_csv(base_violation),
            "exec_margin_violation": bool_csv(exec_violation),
            "dt_correction_used": bool_csv(used),
            "dt_correction_success": bool_csv(corr_success if used else None),
            "correction_failed": bool_csv(corr_failed if used else None),
            "candidate_count": candidate_count,
            "selected_candidate_source": selected_source,
            "runtime_step": runtime_base + runtime_correction,
            "runtime_correction": runtime_correction,
            "active_constraints_count": active_count,
            "collision_step_flag": bool_csv(collision_step),
            "qp_infeasible": bool_csv(False),
            "goal_distance": goal_distance,
            "goal_progress_delta": goal_progress_delta,
        }
        step_writer.write(step_row)
        if used:
            correction_writer.write(
                {
                    "scene": scene,
                    "trial": trial,
                    "step": step,
                    "u_base_x": float(u_base[0].detach().cpu().item()),
                    "u_base_y": float(u_base[1].detach().cpu().item()),
                    "u_base_z": float(u_base[2].detach().cpu().item()),
                    "u_exec_x": float(u_exec[0].detach().cpu().item()),
                    "u_exec_y": float(u_exec[1].detach().cpu().item()),
                    "u_exec_z": float(u_exec[2].detach().cpu().item()),
                    "control_delta_norm": control_delta,
                    "base_predicted_next_h": base_h,
                    "exec_predicted_next_h": exec_h,
                    "h_improvement": exec_h - base_h,
                    "dt_correction_used": bool_csv(used),
                    "dt_correction_success": bool_csv(corr_success),
                    "correction_failed": bool_csv(corr_failed),
                    "selected_candidate_source": selected_source,
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
        "use_startguard": bool_csv(args.use_startguard),
        "start_source": start_meta["start_source"],
        "navigation_executed": "True",
        "success": bool_csv(success),
        "collision": bool_csv(collision),
        "collision_free": bool_csv(False if collision is True else (True if collision is False else None)),
        "stop_reason": stop_reason,
        "num_steps": len(safety_values),
        "min_safety_h": min_safety,
        "base_margin_violation_count": base_violations,
        "exec_margin_violation_count": exec_violations,
        "correction_used_count": correction_used,
        "correction_success_count": correction_success,
        "correction_failed_count": correction_failed,
        "qp_infeasible_count": qp_infeasible_count,
        "goal_distance_reduction_ratio": ratio,
        "initial_goal_distance": initial_goal_distance,
        "final_goal_distance": final_goal_distance,
        "closest_goal_distance": closest_goal_distance,
        "runtime_mean": mean(step_times),
        "runtime_p95": percentile(step_times, 95),
        "runtime_correction_mean": mean(correction_times),
        "runtime_correction_p95": percentile(correction_times, 95),
        "control_delta_mean": mean(control_deltas),
        "control_delta_p95": percentile(control_deltas, 95),
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
        executed = [r for r in group if parse_bool(r.get("navigation_executed"))]
        h = [v for v in (parse_float(r.get("min_safety_h")) for r in executed) if v is not None]
        progress = [v for v in (parse_float(r.get("goal_distance_reduction_ratio")) for r in executed) if v is not None]
        runtime = [v for v in (parse_float(r.get("runtime_mean")) for r in executed) if v is not None]
        runtime_p95 = [v for v in (parse_float(r.get("runtime_p95")) for r in executed) if v is not None]
        runtime_corr = [v for v in (parse_float(r.get("runtime_correction_mean")) for r in executed) if v is not None]
        control_delta = [v for v in (parse_float(r.get("control_delta_mean")) for r in executed) if v is not None]
        base_v = sum(int(parse_float(r.get("base_margin_violation_count")) or 0) for r in executed)
        exec_v = sum(int(parse_float(r.get("exec_margin_violation_count")) or 0) for r in executed)
        out.append(
            {
                "scene": scene,
                "method": method,
                "rows": len(group),
                "navigation_executed_count": len(executed),
                "collision_count": sum(parse_bool(r.get("collision")) for r in executed),
                "collision_free_count": sum(parse_bool(r.get("collision_free")) for r in executed),
                "qp_infeasible_count": sum(int(parse_float(r.get("qp_infeasible_count")) or 0) for r in executed),
                "num_steps": sum(int(parse_float(r.get("num_steps")) or 0) for r in executed),
                "base_margin_violation_count": base_v,
                "exec_margin_violation_count": exec_v,
                "margin_violation_reduction": base_v - exec_v,
                "correction_used_count": sum(int(parse_float(r.get("correction_used_count")) or 0) for r in executed),
                "correction_success_count": sum(int(parse_float(r.get("correction_success_count")) or 0) for r in executed),
                "correction_failed_count": sum(int(parse_float(r.get("correction_failed_count")) or 0) for r in executed),
                "progress_mean": mean(progress),
                "runtime_mean": mean(runtime),
                "runtime_p95": mean(runtime_p95),
                "runtime_correction_mean": mean(runtime_corr),
                "control_delta_mean": mean(control_delta),
                "min_safety_h_min": min(h) if h else "",
            }
        )
    return out


def write_plot(output_dir: Path, summary: list[dict[str, Any]]) -> None:
    if not summary:
        return
    row = summary[0]
    labels = ["base", "exec"]
    vals = [int(row.get("base_margin_violation_count", 0)), int(row.get("exec_margin_violation_count", 0))]
    fig, axes = plt.subplots(1, 3, figsize=(12, 4))
    axes[0].bar(labels, vals, color=["#c0504d", "#9bbb59"])
    axes[0].set_title("margin violations")
    axes[1].bar(["used", "success", "failed"], [row.get("correction_used_count", 0), row.get("correction_success_count", 0), row.get("correction_failed_count", 0)])
    axes[1].set_title("corrections")
    axes[2].bar(["runtime", "correction"], [float(row.get("runtime_mean") or 0.0), float(row.get("runtime_correction_mean") or 0.0)])
    axes[2].set_title("runtime mean")
    fig.tight_layout()
    fig.savefig(output_dir / "comparison_plot.png", dpi=170)
    plt.close(fig)


def run(args: argparse.Namespace) -> list[dict[str, Any]]:
    output_dir = Path(args.output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)
    logger = Logger(output_dir / "run_log.txt")
    trial_writer = CsvAppender(output_dir / "trials.csv", TRIAL_FIELDS)
    step_writer = CsvAppender(output_dir / "v4b_step_debug.csv", STEP_FIELDS)
    candidate_writer = CsvAppender(output_dir / "v4b_candidate_debug.csv", CANDIDATE_FIELDS)
    correction_writer = CsvAppender(output_dir / "v4b_correction_debug.csv", CORRECTION_FIELDS)
    try:
        logger.log(f"script={Path(__file__).resolve()}")
        logger.log(f"scene={args.scene} method={args.method} output_dir={output_dir}")
        scene_cfg = v1.SCENES[args.scene]
        trials = parse_trials(args)
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
        repairs = load_startguard_repairs(args.startguard_projection_dir) if args.use_startguard else {}
        completed = completed_trials(output_dir / "trials.csv") if args.resume else set()
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
                    candidate_writer=candidate_writer,
                    correction_writer=correction_writer,
                )
                logger.log(
                    f"done trial={trial} collision={row['collision']} base_v={row['base_margin_violation_count']} "
                    f"exec_v={row['exec_margin_violation_count']} corrections={row['correction_used_count']} "
                    f"failed={row['correction_failed_count']}"
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
        rows = read_rows(output_dir / "trials.csv")
        summary = summarize(rows)
        write_csv(output_dir / "summary.csv", summary, SUMMARY_FIELDS)
        with (output_dir / "metrics.json").open("w", encoding="utf-8") as fh:
            json.dump(json_ready({"args": vars(args), "summary": summary}), fh, indent=2)
        write_plot(output_dir, summary)
        logger.log(f"summary={summary}")
        return rows
    finally:
        trial_writer.close()
        step_writer.close()
        candidate_writer.close()
        correction_writer.close()
        logger.close()


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="V4-B corrective one-step DT safety filter.")
    parser.add_argument("--scene", choices=["flight", "stonehenge"], required=True)
    parser.add_argument("--trial-start", type=int, default=None)
    parser.add_argument("--trial-end", type=int, default=None)
    parser.add_argument("--trial-list", type=Path, default=None)
    parser.add_argument("--method", choices=["risk_aware_v1_bestD", "safer_splat_filter"], required=True)
    parser.add_argument("--startguard-projection-dir", type=Path, default=None)
    parser.add_argument("--use-startguard", action="store_true")
    parser.add_argument("--safety-margin", type=float, default=0.0005)
    parser.add_argument("--dt-margin", type=float, default=0.0005)
    parser.add_argument("--dt", type=float, default=0.05)
    parser.add_argument("--max-steps", type=int, default=800)
    parser.add_argument("--candidate-budget", type=int, default=2000)
    parser.add_argument("--near-distance-threshold", type=float, default=0.05)
    parser.add_argument("--heading-distance-threshold", type=float, default=0.25)
    parser.add_argument("--heading-cos-threshold", type=float, default=0.5)
    parser.add_argument("--risk-score", choices=["risk_v0_active_frequency", "risk_v1_geometry", "risk_v2_hybrid"], default="risk_v2_hybrid")
    parser.add_argument("--risk-score-table", type=Path, default=None)
    parser.add_argument("--min-candidate-budget", type=int, default=200)
    parser.add_argument("--num-control-samples", type=int, default=64)
    parser.add_argument("--control-noise-scale", type=float, default=0.15)
    parser.add_argument("--control-scale-list", type=str, default="0,0.25,0.5,0.75,1.0")
    parser.add_argument("--include-braking-controls", action="store_true")
    parser.add_argument("--include-repulsive-controls", action="store_true")
    parser.add_argument("--include-goal-directed-controls", action="store_true")
    parser.add_argument("--w-base", type=float, default=1.0)
    parser.add_argument("--w-goal", type=float, default=0.1)
    parser.add_argument("--w-smooth", type=float, default=0.1)
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
    run(args)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
