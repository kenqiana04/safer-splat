#!/usr/bin/env python3
"""Paired same-state V4-C audit with original V4-C retaining formal control."""

from __future__ import annotations

import argparse
import copy
import csv
import json
import statistics
import sys
import time
from contextlib import contextmanager
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Iterator

import numpy as np
import torch


ROOT = Path(__file__).resolve().parents[3]
SCRIPT_DIR = Path(__file__).resolve().parent
for path in (ROOT, SCRIPT_DIR):
    if str(path) not in sys.path:
        sys.path.insert(0, str(path))

from dynamics.systems import DoubleIntegrator
from splat.gsplat_utils import GSplatLoader

import run_risk_aware_v1_pre_cbf_comparison as v1
import run_v4b_corrective_dt_filter as v4b
import run_v4c_hstep_predictive_recovery as v4c
from v4c_candidate_family_metrics import stage_family_snapshot
from v4c_hierarchical_candidate_evaluator import HierarchicalEvaluationResult, evaluate_hierarchical


FIXED_TRIALS = (12, 13, 14)


class NullWriter:
    """Satisfy the original run_trial writer interface without persisting raw rows."""

    def write(self, _row: dict[str, Any]) -> None:
        return None

    def close(self) -> None:
        return None


@dataclass
class RuntimeContext:
    args: argparse.Namespace
    scene_cfg: dict[str, Any]
    gsplat: GSplatLoader
    dynamics: DoubleIntegrator
    risk_table: v1.RiskScoreTable | None
    repairs: dict[int, dict[str, str]]
    device: torch.device


def write_csv(path: Path, rows: list[dict[str, Any]], fields: list[str]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=fields, extrasaction="ignore")
        writer.writeheader()
        writer.writerows(rows)


def median_or_none(values: list[float]) -> float | None:
    return float(statistics.median(values)) if values else None


def build_preregistered_args(output_dir: Path, trial: int) -> argparse.Namespace:
    """Parse the provenance-confirmed H3_N128 configuration without guessing."""

    tokens = [
        "--scene", "flight", "--trial-start", str(trial), "--trial-end", str(trial),
        "--method", "risk_aware_v1_bestD",
        "--startguard-projection-dir", "work/risk_aware_cbf/results/v4_projection_flight_repair_needed",
        "--use-startguard", "--safety-margin", "0.0005", "--dt-margin", "0.0005",
        "--warning-margin", "0.0008", "--dt", "0.05", "--max-steps", "800",
        "--candidate-budget", "2000", "--near-distance-threshold", "0.05",
        "--heading-distance-threshold", "0.25", "--heading-cos-threshold", "0.5",
        "--risk-score", "risk_v2_hybrid", "--min-candidate-budget", "200",
        "--horizon", "3", "--num-sequences", "128", "--num-elites", "16",
        "--sequence-noise-scale", "0.15", "--control-scale-list", "0,0.25,0.5,0.75,1.0",
        "--include-braking-sequences", "--include-repulsive-sequences",
        "--include-goal-directed-sequences", "--cem-iters", "2", "--w-base", "1.0",
        "--w-goal", "0.2", "--w-smooth", "0.1", "--w-safety", "10.0",
        "--activation-mode", "on_margin_violation", "--goal-tolerance", "0.001",
        "--output-dir", str(output_dir), "--device", "cuda",
    ]
    return v4c.build_parser().parse_args(tokens)


def load_runtime(args: argparse.Namespace) -> RuntimeContext:
    scene_cfg = v1.SCENES[args.scene]
    device = torch.device(args.device)
    if device.type == "cuda" and not torch.cuda.is_available():
        raise RuntimeError("CUDA requested but unavailable")
    gsplat = GSplatLoader(scene_cfg["path_to_gsplat"], device)
    dynamics = DoubleIntegrator(device=device, ndim=3)
    risk_table = None
    if args.method == "risk_aware_v1_bestD":
        risk_path = args.risk_score_table or Path(f"work/risk_aware_cbf/results/{args.scene}_risk_score_table_v0.csv")
        risk_table = v1.RiskScoreTable(risk_path, int(gsplat.means.shape[0]))
    repairs = v4b.load_startguard_repairs(args.startguard_projection_dir) if args.use_startguard else {}
    return RuntimeContext(args, scene_cfg, gsplat, dynamics, risk_table, repairs, device)


def build_initial_context(runtime: RuntimeContext, trial: int) -> dict[str, Any]:
    """Build a real official trial context without propagating a formal state."""

    x0, xf = v1.make_start_goal_configs(runtime.scene_cfg)
    start_pos, _ = v4b.start_for_trial(
        args=runtime.args, trial=trial, x0=x0, repairs=runtime.repairs
    )
    goal_pos = np.asarray(xf[trial], dtype=float)
    x = torch.tensor(start_pos, device=runtime.device, dtype=torch.float32)
    x = torch.cat([x, torch.zeros(3, device=runtime.device, dtype=torch.float32)])
    goal = torch.tensor(goal_pos, device=runtime.device, dtype=torch.float32)
    goal = torch.cat([goal, torch.zeros(3, device=runtime.device, dtype=torch.float32)])
    cbf = v4b.make_cbf(
        args=runtime.args, method=runtime.args.method, gsplat=runtime.gsplat,
        dynamics=runtime.dynamics, scene_cfg=runtime.scene_cfg, risk_table=runtime.risk_table,
    )
    u_nom = v1.nominal_control(x, goal)
    u_base = cbf.solve_QP(x, u_nom)
    if not bool(cbf.solver_success):
        raise RuntimeError("initial context CBF-QP is infeasible")
    return {"x": x, "goal": goal, "u_nom": u_nom, "u_base": u_base, "u_prev": None}


def warm_up(runtime: RuntimeContext) -> None:
    """Run a nonformal trial-11 initial-context evaluation; retain no metric."""

    context = build_initial_context(runtime, 11)
    candidates = v4c.generate_sequences(
        args=runtime.args, trial=11, step=0, gsplat=runtime.gsplat,
        scene_cfg=runtime.scene_cfg, **context,
    )
    v4c.evaluate_sequences(
        args=runtime.args, scene=runtime.args.scene, method=runtime.args.method,
        trial=11, step=0, x=context["x"], goal=context["goal"],
        u_base=context["u_base"], u_prev=None, candidates=candidates,
        gsplat=runtime.gsplat, scene_cfg=runtime.scene_cfg,
    )


def run_original_trial(runtime: RuntimeContext, trial: int) -> dict[str, Any]:
    return v4c.run_trial(
        args=runtime.args, scene=runtime.args.scene, method=runtime.args.method,
        trial=trial, scene_cfg=runtime.scene_cfg, gsplat=runtime.gsplat,
        dynamics=runtime.dynamics, risk_table=runtime.risk_table, repairs=runtime.repairs,
        device=runtime.device, step_writer=NullWriter(), sequence_writer=NullWriter(),
        recovery_writer=NullWriter(),
    )


class PairedShadowHook:
    """Return original evaluation while recording a same-state hierarchical shadow."""

    def __init__(self) -> None:
        self.original_generate = v4c.generate_sequences
        self.original_evaluate = v4c.evaluate_sequences
        self.pending: dict[int, tuple[dict[str, Any], float, float]] = {}
        self.events: list[dict[str, Any]] = []

    def generate(self, **kwargs: Any) -> list[Any]:
        start = time.perf_counter()
        candidates = self.original_generate(**kwargs)
        generated_at = time.perf_counter()
        self.pending[id(candidates)] = (kwargs, start, generated_at)
        return candidates

    def evaluate(self, **kwargs: Any) -> tuple[Any, torch.Tensor, list[float], float, bool, bool, list[dict[str, Any]], int]:
        generation_kwargs, started, generated_at = self.pending.pop(id(kwargs["candidates"]))
        state_before = kwargs["x"].detach().clone()
        args_before = copy.deepcopy(vars(kwargs["args"]))
        original_result = self.original_evaluate(**kwargs)
        original_elapsed = time.perf_counter() - started
        selected, _, _, min_h, success, failed, rows, selected_index = original_result
        start_goal_distance = float(torch.linalg.norm(kwargs["x"][:3] - kwargs["goal"][:3]).detach().cpu().item())
        original_snapshot = stage_family_snapshot(
            candidates=kwargs["candidates"], rows=rows, selected_index=selected_index,
            start_goal_distance=start_goal_distance,
            generation_runtime_sec=generated_at - started,
            evaluation_runtime_sec=time.perf_counter() - generated_at,
            count_selection=bool(success),
        )
        hierarchical = evaluate_hierarchical(
            original_args=kwargs["args"], scene=kwargs["scene"], method=kwargs["method"],
            trial=kwargs["trial"], step=kwargs["step"], x=kwargs["x"], goal=kwargs["goal"],
            u_base=kwargs["u_base"], u_nom=generation_kwargs["u_nom"], u_prev=kwargs["u_prev"],
            gsplat=kwargs["gsplat"], scene_cfg=kwargs["scene_cfg"],
            generate_fn=self.original_generate, evaluate_fn=self.original_evaluate,
        )
        self.events.append(
            {
                "trial": int(kwargs["trial"]), "step": int(kwargs["step"]),
                "original_success": bool(success), "original_failed": bool(failed),
                "original_min_h": float(min_h), "original_source": str(selected.source),
                "original_runtime_sec": original_elapsed, "original_snapshot": original_snapshot,
                "hierarchical": hierarchical,
                "state_isolation": bool(torch.equal(state_before, kwargs["x"])),
                "args_unchanged": args_before == vars(kwargs["args"]),
                "formal_control_unchanged": True,
            }
        )
        return original_result


@contextmanager
def paired_shadow_hook() -> Iterator[PairedShadowHook]:
    hook = PairedShadowHook()
    original_generate, original_evaluate = v4c.generate_sequences, v4c.evaluate_sequences
    v4c.generate_sequences, v4c.evaluate_sequences = hook.generate, hook.evaluate
    try:
        yield hook
    finally:
        v4c.generate_sequences, v4c.evaluate_sequences = original_generate, original_evaluate


def summarize_events(events: list[dict[str, Any]], trial: int, dt_margin: float) -> dict[str, Any]:
    subset = [event for event in events if event["trial"] == trial]
    original_runtime = [float(event["original_runtime_sec"]) for event in subset]
    hierarchical_runtime = [float(event["hierarchical"].total_runtime_sec) for event in subset]
    original_feasible = sum(event["original_success"] for event in subset)
    hierarchical_feasible = sum(event["hierarchical"].recovery_success for event in subset)
    regression = sum(event["original_success"] and not event["hierarchical"].recovery_success for event in subset)
    safety_regression = sum(
        event["original_success"] and event["hierarchical"].selected_min_h < dt_margin
        for event in subset
    )
    source_match = sum(event["original_source"] == event["hierarchical"].selected_source for event in subset)
    h_delta = [event["hierarchical"].selected_min_h - event["original_min_h"] for event in subset]
    progress_delta = [
        event["hierarchical"].selected_progress_delta
        for event in subset if event["hierarchical"].selected_progress_delta is not None
    ]
    original_median, hierarchical_median = median_or_none(original_runtime), median_or_none(hierarchical_runtime)
    reduction = None
    if original_median is not None and original_median > 0 and hierarchical_median is not None:
        reduction = (original_median - hierarchical_median) / original_median
    return {
        "trial_id": trial,
        "activation_count": len(subset),
        "stage_a_success_count": sum(event["hierarchical"].stage_a_selected for event in subset),
        "stage_b_entry_count": sum(event["hierarchical"].stage_b_entered for event in subset),
        "original_feasible_count": original_feasible,
        "hierarchical_feasible_count": hierarchical_feasible,
        "selected_source_match_count": source_match,
        "selected_source_difference_count": len(subset) - source_match,
        "selected_min_h_delta_mean": sum(h_delta) / len(h_delta) if h_delta else None,
        "selected_progress_proxy_delta_mean": sum(progress_delta) / len(progress_delta) if progress_delta else None,
        "original_recovery_runtime_median_sec": original_median,
        "hierarchical_recovery_runtime_median_sec": hierarchical_median,
        "activated_runtime_reduction_fraction": reduction,
        "paired_feasibility_regression_count": regression,
        "safety_margin_regression_count": safety_regression,
        "state_isolation_passed": all(event["state_isolation"] and event["args_unchanged"] for event in subset),
        "formal_control_unchanged": all(event["formal_control_unchanged"] for event in subset),
        "notes": "Formal trajectory executed original V4-C only; hierarchical result is same-state shadow.",
    }


def run_paired_audit(output_dir: Path, trials: tuple[int, ...] = FIXED_TRIALS) -> dict[str, Any]:
    if tuple(trials) != FIXED_TRIALS:
        raise ValueError(f"only fixed trials {FIXED_TRIALS} are allowed")
    runtime = load_runtime(build_preregistered_args(output_dir, trials[0]))
    warm_up(runtime)
    events: list[dict[str, Any]] = []
    trial_rows: list[dict[str, Any]] = []
    for trial in trials:
        runtime.args = build_preregistered_args(output_dir, trial)
        with paired_shadow_hook() as hook:
            run_original_trial(runtime, trial)
        events.extend(hook.events)
        trial_rows.append(summarize_events(hook.events, trial, float(runtime.args.dt_margin)))
    original_runtime = [float(event["original_runtime_sec"]) for event in events]
    hierarchical_runtime = [float(event["hierarchical"].total_runtime_sec) for event in events]
    original_median, hierarchical_median = median_or_none(original_runtime), median_or_none(hierarchical_runtime)
    reduction = None
    if original_median is not None and original_median > 0 and hierarchical_median is not None:
        reduction = (original_median - hierarchical_median) / original_median
    regressions = sum(row["paired_feasibility_regression_count"] for row in trial_rows)
    safety_regressions = sum(row["safety_margin_regression_count"] for row in trial_rows)
    state_ok = all(bool(row["state_isolation_passed"]) for row in trial_rows)
    control_ok = all(bool(row["formal_control_unchanged"]) for row in trial_rows)
    runtime_valid = bool(original_runtime and hierarchical_runtime and all(value > 0 for value in original_runtime + hierarchical_runtime))
    passed = bool(regressions == 0 and safety_regressions == 0 and state_ok and control_ok and runtime_valid and reduction is not None and reduction > 0)
    fields = list(trial_rows[0]) if trial_rows else []
    write_csv(output_dir / "paired_context_summary.csv", trial_rows, fields)
    stage_rows = [
        {
            "trial_id": row["trial_id"], "activation_count": row["activation_count"],
            "stage_a_success_count": row["stage_a_success_count"],
            "stage_a_success_rate": row["stage_a_success_count"] / row["activation_count"] if row["activation_count"] else None,
            "stage_b_entry_count": row["stage_b_entry_count"],
            "stage_b_entry_rate": row["stage_b_entry_count"] / row["activation_count"] if row["activation_count"] else None,
            "stage_a_median_runtime_sec": None, "stage_b_median_runtime_sec": None,
            "total_recovery_median_runtime_sec": row["hierarchical_recovery_runtime_median_sec"],
            "notes": "Paired same-state shadow; stage-specific medians are reported after active A/B.",
        }
        for row in trial_rows
    ]
    write_csv(output_dir / "stage_usage_summary.csv", stage_rows, list(stage_rows[0]))
    gate = {
        "paired_shadow_audit_run": True,
        "activation_count": len(events),
        "stage_a_success_count": sum(event["hierarchical"].stage_a_selected for event in events),
        "stage_b_entry_count": sum(event["hierarchical"].stage_b_entered for event in events),
        "paired_feasibility_regression_count": regressions,
        "safety_margin_regression_count": safety_regressions,
        "state_isolation_passed": state_ok,
        "formal_control_unchanged": control_ok,
        "original_activated_recovery_runtime_median_sec": original_median,
        "hierarchical_activated_recovery_runtime_median_sec": hierarchical_median,
        "activated_runtime_reduction_fraction": reduction,
        "runtime_measurement_valid": runtime_valid,
        "paired_gate_passed": passed,
    }
    write_csv(output_dir / "paired_gate_summary.csv", [gate], list(gate))
    return gate


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output-dir", type=Path, required=True)
    args = parser.parse_args()
    gate = run_paired_audit(args.output_dir)
    print(json.dumps(gate, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
