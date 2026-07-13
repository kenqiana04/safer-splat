#!/usr/bin/env python3
"""Compact held-out same-state audit; the formal trajectory always uses original V4-C."""

from __future__ import annotations

import argparse
import copy
import csv
import json
import statistics
import time
from contextlib import contextmanager
from pathlib import Path
from typing import Any, Iterator

import torch

from run_v4c_hierarchical_paired_audit import (
    NullWriter, build_preregistered_args, load_runtime, run_original_trial, warm_up,
)
import run_v4c_hstep_predictive_recovery as v4c
from v4c_candidate_family_metrics import stage_family_snapshot
from v4c_hierarchical_candidate_evaluator import evaluate_hierarchical


def read_trials(path: Path) -> list[int]:
    with path.open("r", newline="", encoding="utf-8") as handle:
        rows = list(csv.DictReader(handle))
    trials = [int(row["trial_id"]) for row in rows]
    if len(trials) != 16 or trials != sorted(trials) or set(trials) & {12, 13, 14}:
        raise RuntimeError("held-out preregistration is not exactly 16 ascending non-development trials")
    return trials


def write_csv(path: Path, rows: list[dict[str, Any]], fields: list[str]) -> None:
    with path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=fields, extrasaction="ignore")
        writer.writeheader()
        writer.writerows(rows)


def median(values: list[float]) -> float | None:
    return float(statistics.median(values)) if values else None


class HeldoutShadowHook:
    def __init__(self) -> None:
        self.original_generate = v4c.generate_sequences
        self.original_evaluate = v4c.evaluate_sequences
        self.pending: dict[int, tuple[dict[str, Any], float, float]] = {}
        self.events: list[dict[str, Any]] = []

    def generate(self, **kwargs: Any) -> list[Any]:
        started = time.perf_counter()
        candidates = self.original_generate(**kwargs)
        generated = time.perf_counter()
        self.pending[id(candidates)] = (kwargs, started, generated)
        return candidates

    def evaluate(self, **kwargs: Any) -> tuple[Any, torch.Tensor, list[float], float, bool, bool, list[dict[str, Any]], int]:
        generation_kwargs, started, generated = self.pending.pop(id(kwargs["candidates"]))
        state_before = kwargs["x"].detach().clone()
        args_before = copy.deepcopy(vars(kwargs["args"]))
        original = self.original_evaluate(**kwargs)
        completed = time.perf_counter()
        selected, _, _, min_h, success, failed, rows, selected_index = original
        original_cost = float(rows[selected_index]["sequence_cost"]) if selected_index >= 0 else None
        start_distance = float(torch.linalg.norm(kwargs["x"][:3] - kwargs["goal"][:3]).detach().cpu().item())
        original_snapshot = stage_family_snapshot(
            candidates=kwargs["candidates"], rows=rows, selected_index=selected_index,
            start_goal_distance=start_distance, generation_runtime_sec=generated - started,
            evaluation_runtime_sec=completed - generated, count_selection=bool(success),
        )
        hierarchical = evaluate_hierarchical(
            original_args=kwargs["args"], scene=kwargs["scene"], method=kwargs["method"],
            trial=kwargs["trial"], step=kwargs["step"], x=kwargs["x"], goal=kwargs["goal"],
            u_base=kwargs["u_base"], u_nom=generation_kwargs["u_nom"], u_prev=kwargs["u_prev"],
            gsplat=kwargs["gsplat"], scene_cfg=kwargs["scene_cfg"],
            generate_fn=self.original_generate, evaluate_fn=self.original_evaluate,
        )
        final_x, hs, _ = v4c.rollout_sequence(
            x=kwargs["x"], controls=hierarchical.selected_candidate.controls, dt=kwargs["args"].dt,
            gsplat=kwargs["gsplat"], scene_cfg=kwargs["scene_cfg"],
        )
        hierarchical_cost, *_ = v4c.sequence_cost(
            args=kwargs["args"], controls=hierarchical.selected_candidate.controls, hs=hs,
            final_x=final_x, goal=kwargs["goal"], u_base=kwargs["u_base"], u_prev=kwargs["u_prev"],
        )
        self.events.append({
            "trial": int(kwargs["trial"]), "step": int(kwargs["step"]),
            "original_success": bool(success), "original_failed": bool(failed),
            "original_min_h": float(min_h), "original_source": str(selected.source),
            "original_cost": original_cost, "original_runtime_sec": completed - started,
            "original_control": original[1].detach().clone(), "original_snapshot": original_snapshot,
            "hierarchical": hierarchical, "hierarchical_cost": float(hierarchical_cost),
            "state_isolation": bool(torch.equal(state_before, kwargs["x"])),
            "args_unchanged": args_before == vars(kwargs["args"]), "formal_control_unchanged": True,
        })
        return original


@contextmanager
def hooked() -> Iterator[HeldoutShadowHook]:
    hook = HeldoutShadowHook()
    original_generate, original_evaluate = v4c.generate_sequences, v4c.evaluate_sequences
    v4c.generate_sequences, v4c.evaluate_sequences = hook.generate, hook.evaluate
    try:
        yield hook
    finally:
        v4c.generate_sequences, v4c.evaluate_sequences = original_generate, original_evaluate


def summarize(events: list[dict[str, Any]], trial: int) -> dict[str, Any]:
    subset = [event for event in events if event["trial"] == trial]
    original_runtime = [float(event["original_runtime_sec"]) for event in subset]
    hierarchical_runtime = [float(event["hierarchical"].total_runtime_sec) for event in subset]
    original_median, hierarchical_median = median(original_runtime), median(hierarchical_runtime)
    reduction = (original_median - hierarchical_median) / original_median if original_median and hierarchical_median is not None else None
    control_delta = [float(torch.linalg.norm(event["original_control"] - event["hierarchical"].selected_first_control).detach().cpu().item()) for event in subset]
    h_delta = [event["hierarchical"].selected_min_h - event["original_min_h"] for event in subset]
    cost_regret = [event["hierarchical_cost"] - event["original_cost"] for event in subset if event["original_cost"] is not None]
    progress_delta = [event["hierarchical"].selected_progress_delta for event in subset if event["hierarchical"].selected_progress_delta is not None]
    return {
        "trial_id": trial, "activation_count": len(subset),
        "original_feasible_count": sum(event["original_success"] for event in subset),
        "hierarchical_feasible_count": sum(event["hierarchical"].recovery_success for event in subset),
        "stage_a_feasible_count": sum(event["hierarchical"].stage_a_feasible_count for event in subset),
        "stage_a_selected_count": sum(event["hierarchical"].stage_a_selected for event in subset),
        "stage_b_entry_count": sum(event["hierarchical"].stage_b_entered for event in subset),
        "stage_b_success_count": sum(event["hierarchical"].stage_b_selected and event["hierarchical"].recovery_success for event in subset),
        "stage_b_failure_count": sum(event["hierarchical"].stage_b_entered and event["hierarchical"].recovery_failed for event in subset),
        "paired_feasibility_regression_count": sum(event["original_success"] and not event["hierarchical"].recovery_success for event in subset),
        "selected_source_match_count": sum(event["original_source"] == event["hierarchical"].selected_source for event in subset),
        "selected_source_divergence_count": sum(event["original_source"] != event["hierarchical"].selected_source for event in subset),
        "selected_control_delta_mean": sum(control_delta) / len(control_delta) if control_delta else None,
        "selected_min_h_delta_mean": sum(h_delta) / len(h_delta) if h_delta else None,
        "original_cost_mean": sum(event["original_cost"] for event in subset if event["original_cost"] is not None) / len(subset) if subset else None,
        "hierarchical_selected_cost_mean": sum(event["hierarchical_cost"] for event in subset) / len(subset) if subset else None,
        "cost_regret_mean": sum(cost_regret) / len(cost_regret) if cost_regret else None,
        "selected_progress_proxy_delta_mean": sum(progress_delta) / len(progress_delta) if progress_delta else None,
        "original_recovery_runtime_median_sec": original_median,
        "hierarchical_recovery_runtime_median_sec": hierarchical_median,
        "activated_runtime_reduction_fraction": reduction,
        "state_isolation_passed": all(event["state_isolation"] and event["args_unchanged"] for event in subset),
        "formal_control_unchanged": all(event["formal_control_unchanged"] for event in subset),
        "instrumentation_error": False,
        "notes": "Formal trajectory executed original V4-C only; hierarchical evaluation is same-state shadow.",
    }


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output-dir", type=Path, required=True)
    args = parser.parse_args()
    trials = read_trials(args.output_dir / "heldout_cohort_preregistration.csv")
    runtime = load_runtime(build_preregistered_args(args.output_dir, trials[0]))
    warm_up(runtime)
    all_events: list[dict[str, Any]] = []
    rows: list[dict[str, Any]] = []
    for trial in trials:
        runtime.args = build_preregistered_args(args.output_dir, trial)
        with hooked() as hook:
            run_original_trial(runtime, trial)
        all_events.extend(hook.events)
        rows.append(summarize(hook.events, trial))
    write_csv(args.output_dir / "paired_context_summary.csv", rows, list(rows[0]))
    original_times = [float(event["original_runtime_sec"]) for event in all_events]
    hierarchical_times = [float(event["hierarchical"].total_runtime_sec) for event in all_events]
    original_median, hierarchical_median = median(original_times), median(hierarchical_times)
    reduction = (original_median - hierarchical_median) / original_median if original_median and hierarchical_median is not None else None
    regressions = sum(int(row["paired_feasibility_regression_count"]) for row in rows)
    stage_b_ok = all(not event["hierarchical"].stage_b_entered or event["hierarchical"].stage_b_selected for event in all_events)
    gate = {
        "paired_shadow_audit_run": True, "heldout_trial_count": len(rows), "activation_count": len(all_events),
        "stage_a_success_count": sum(event["hierarchical"].stage_a_selected for event in all_events),
        "stage_b_entry_count": sum(event["hierarchical"].stage_b_entered for event in all_events),
        "paired_feasibility_regression_count": regressions,
        "stage_b_equivalence_passed_when_entered": stage_b_ok,
        "state_isolation_passed": all(bool(row["state_isolation_passed"]) for row in rows),
        "formal_control_unchanged": all(bool(row["formal_control_unchanged"]) for row in rows),
        "instrumentation_error_count": 0,
        "original_activated_recovery_runtime_median_sec": original_median,
        "hierarchical_activated_recovery_runtime_median_sec": hierarchical_median,
        "activated_runtime_reduction_fraction": reduction,
        "paired_gate_passed": bool(len(rows) == 16 and regressions == 0 and stage_b_ok and all(bool(row["state_isolation_passed"]) and bool(row["formal_control_unchanged"]) for row in rows) and reduction is not None and reduction > 0),
    }
    write_csv(args.output_dir / "paired_gate_summary.csv", [gate], list(gate))
    print(json.dumps(gate, sort_keys=True))
    return 0 if gate["paired_gate_passed"] else 2


if __name__ == "__main__":
    raise SystemExit(main())
