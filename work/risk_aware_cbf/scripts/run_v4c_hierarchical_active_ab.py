#!/usr/bin/env python3
"""Sequential preregistered active A/B for original V4-C and hierarchical V0."""

from __future__ import annotations

import argparse
import csv
import json
import statistics
import time
from contextlib import contextmanager
from pathlib import Path
from typing import Any, Iterator

import torch

import run_v4c_hstep_predictive_recovery as v4c
from run_v4c_hierarchical_paired_audit import (
    FIXED_TRIALS,
    build_preregistered_args,
    load_runtime,
    median_or_none,
    run_original_trial,
    warm_up,
)
from v4c_candidate_family_metrics import aggregate_family_snapshots, stage_family_snapshot
from v4c_hierarchical_candidate_evaluator import build_stage_a_args, evaluate_hierarchical


ACTIVE_ORDER = (
    (12, "original_v4c"),
    (12, "hierarchical_v0"),
    (13, "hierarchical_v0"),
    (13, "original_v4c"),
    (14, "original_v4c"),
    (14, "hierarchical_v0"),
)


def write_csv(path: Path, rows: list[dict[str, Any]], fields: list[str]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=fields, extrasaction="ignore")
        writer.writeheader()
        writer.writerows(rows)


def percentile(values: list[float], q: float) -> float | None:
    if not values:
        return None
    return float(v4c.v4b.percentile(values, q))


class OriginalCaptureHook:
    """Record compact original activation metrics without changing output."""

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
        _, started, generated = self.pending.pop(id(kwargs["candidates"]))
        result = self.original_evaluate(**kwargs)
        completed = time.perf_counter()
        selected, _, _, min_h, success, failed, rows, selected_index = result
        start_distance = float(torch.linalg.norm(kwargs["x"][:3] - kwargs["goal"][:3]).detach().cpu().item())
        snapshot = stage_family_snapshot(
            candidates=kwargs["candidates"], rows=rows, selected_index=selected_index,
            start_goal_distance=start_distance, generation_runtime_sec=generated - started,
            evaluation_runtime_sec=completed - generated, count_selection=bool(success),
        )
        self.events.append(
            {
                "trial": int(kwargs["trial"]), "runtime_sec": completed - started,
                "success": bool(success), "failed": bool(failed), "min_h": float(min_h),
                "source": str(selected.source), "snapshot": snapshot,
            }
        )
        return result


class HierarchicalActiveHook:
    """Feed Stage-A candidates to original run_trial and conditionally invoke Stage B."""

    def __init__(self) -> None:
        self.original_generate = v4c.generate_sequences
        self.original_evaluate = v4c.evaluate_sequences
        self.pending: dict[int, tuple[dict[str, Any], float, float]] = {}
        self.events: list[dict[str, Any]] = []

    def generate(self, **kwargs: Any) -> list[Any]:
        stage_args = build_stage_a_args(kwargs["args"])
        started = time.perf_counter()
        candidates = self.original_generate(
            args=stage_args, x=kwargs["x"], goal=kwargs["goal"], u_base=kwargs["u_base"],
            u_nom=kwargs["u_nom"], u_prev=kwargs["u_prev"], gsplat=kwargs["gsplat"],
            scene_cfg=kwargs["scene_cfg"], trial=kwargs["trial"], step=kwargs["step"],
        )
        generated = time.perf_counter()
        self.pending[id(candidates)] = (kwargs, started, generated)
        return candidates

    def evaluate(self, **kwargs: Any) -> tuple[Any, torch.Tensor, list[float], float, bool, bool, list[dict[str, Any]], int]:
        generation_kwargs, started, generated = self.pending.pop(id(kwargs["candidates"]))
        result = evaluate_hierarchical(
            original_args=kwargs["args"], scene=kwargs["scene"], method=kwargs["method"],
            trial=kwargs["trial"], step=kwargs["step"], x=kwargs["x"], goal=kwargs["goal"],
            u_base=kwargs["u_base"], u_nom=generation_kwargs["u_nom"], u_prev=kwargs["u_prev"],
            gsplat=kwargs["gsplat"], scene_cfg=kwargs["scene_cfg"],
            stage_a_candidates=kwargs["candidates"], generate_fn=self.original_generate,
            evaluate_fn=self.original_evaluate,
        )
        stage_a_generation = generated - started
        result.stage_a_runtime_sec += stage_a_generation
        result.total_runtime_sec += stage_a_generation
        total_generated = max(1, result.stage_a_generated_count)
        for snapshot in result.stage_a_snapshot:
            snapshot["generation_runtime_sec"] += stage_a_generation * float(snapshot["generated_count"]) / total_generated
        self.events.append(
            {
                "trial": int(kwargs["trial"]), "runtime_sec": result.total_runtime_sec,
                "result": result,
            }
        )
        return (
            result.selected_candidate, result.selected_first_control, result.selected_hs,
            result.selected_min_h, result.recovery_success, result.recovery_failed,
            [], -1,
        )


@contextmanager
def hook_context(hook: Any) -> Iterator[Any]:
    original_generate, original_evaluate = v4c.generate_sequences, v4c.evaluate_sequences
    v4c.generate_sequences, v4c.evaluate_sequences = hook.generate, hook.evaluate
    try:
        yield hook
    finally:
        v4c.generate_sequences, v4c.evaluate_sequences = original_generate, original_evaluate


def read_single_csv(path: Path) -> dict[str, str]:
    with path.open("r", newline="", encoding="utf-8") as handle:
        rows = list(csv.DictReader(handle))
    if len(rows) != 1:
        raise RuntimeError(f"expected one row in {path}")
    return rows[0]


def read_contract_passed(path: Path) -> bool:
    with path.open("r", newline="", encoding="utf-8") as handle:
        rows = list(csv.DictReader(handle))
    return bool(rows) and all(
        row["passed"].strip().lower() == "true"
        for row in rows if row["critical"].strip().lower() == "true"
    )


def bool_text(value: Any) -> bool:
    return str(value).strip().lower() in {"true", "1", "yes"}


def trial_summary(row: dict[str, Any], trial: int, variant: str, events: list[dict[str, Any]]) -> dict[str, Any]:
    runtimes = [float(event["runtime_sec"]) for event in events]
    if variant == "original_v4c":
        stage_a_success, stage_b_entry = 0, 0
    else:
        stage_a_success = sum(event["result"].stage_a_selected for event in events)
        stage_b_entry = sum(event["result"].stage_b_entered for event in events)
    return {
        "scene": "flight", "trial_id": trial, "method_variant": variant,
        "navigation_executed": row["navigation_executed"], "num_steps": row["num_steps"],
        "stop_reason": row["stop_reason"], "collision": row["collision"],
        "qp_infeasible_count": row["qp_infeasible_count"],
        "base_horizon_margin_violation_count": row["base_horizon_margin_violation_count"],
        "exec_horizon_margin_violation_count": row["exec_horizon_margin_violation_count"],
        "recovery_used_count": row["predictive_recovery_used_count"],
        "recovery_success_count": row["predictive_recovery_success_count"],
        "recovery_failed_count": row["recovery_failed_count"],
        "stage_a_success_count": stage_a_success, "stage_b_entry_count": stage_b_entry,
        "goal_distance_reduction_ratio": row["goal_distance_reduction_ratio"],
        "runtime_mean": row["runtime_mean"], "runtime_recovery_mean": sum(runtimes) / len(runtimes) if runtimes else None,
        "runtime_recovery_median": median_or_none(runtimes), "runtime_recovery_p95": percentile(runtimes, 95),
        "seconds_total": row["seconds_total"], "notes": "Activated-step runtime uses compact hook timing only.",
    }


def write_report(output_dir: Path, metrics: dict[str, Any], active_rows: list[dict[str, Any]]) -> None:
    decision = metrics["r_v4c1_decision"]
    lines = [
        "# REPORT: V4-C Hierarchical Candidate Evaluation V0", "",
        "## 1. Purpose", "",
        "This is a fixed three-trial paired and active audit of R-V4C-1. It is not flight20, full100, a statistical test, a planner evaluation, or a generalized safety/runtime claim.", "",
        "## 2. Difference from Original V4-C", "",
        "Stage A evaluates only original deterministic families. Stage B invokes the untouched original full generator and evaluator only when Stage A has no feasible candidate. CBF-QP, candidate controls, cost, safety query, trigger threshold, fallback, and post-step update are unchanged.", "",
        "## 3. Contract and Paired Audit", "",
        f"Contract checks passed: `{metrics['contract_checks_passed']}`. Stage-B equivalence passed: `{metrics['stage_b_equivalence_passed']}`. Paired feasibility regressions: `{metrics['paired_feasibility_regression_count']}`.", "",
        "## 4. Active A/B Results", "",
        "| variant | trials | activations | recovery failures | exec-horizon violations | collisions | QP infeasible | activated median runtime (s) |", "| --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: |",
    ]
    for variant in ("original_v4c", "hierarchical_v0"):
        rows = [row for row in active_rows if row["method_variant"] == variant]
        runtime_key = (
            "original_activated_recovery_runtime_median_sec"
            if variant == "original_v4c"
            else "hierarchical_activated_recovery_runtime_median_sec"
        )
        lines.append(
            f"| {variant} | {len(rows)} | {sum(int(row['recovery_used_count']) for row in rows)} | {sum(int(row['recovery_failed_count']) for row in rows)} | {sum(int(row['exec_horizon_margin_violation_count']) for row in rows)} | {sum(bool_text(row['collision']) for row in rows)} | {sum(int(row['qp_infeasible_count']) for row in rows)} | {metrics[runtime_key]} |"
        )
    lines.extend([
        "", "## 5. Stage Usage and Decision", "",
        f"Stage-A success count: `{metrics['stage_a_success_count']}`. Stage-B entry count: `{metrics['stage_b_entry_count']}`. Activated-step runtime reduction: `{metrics['activated_runtime_reduction_fraction']}`. Decision: `{decision}`.", "",
        "## 6. Claim Boundaries", "",
        "The evidence is local to fixed flight trials 12, 13, and 14. It does not establish collision reduction, route-level safety, completion improvement, planner quality, statistical significance, generalized runtime improvement, or meter clearance. `h` is the repository GSplat safety-field value, not metric clearance.",
    ])
    (output_dir.parent.parent / "REPORT_V4C_HIERARCHICAL_CANDIDATE_EVALUATION_V0.md").write_text("\n".join(lines) + "\n", encoding="utf-8")


def run_active_ab(output_dir: Path) -> dict[str, Any]:
    contract_ok = read_contract_passed(output_dir / "contract_check.csv")
    paired = read_single_csv(output_dir / "paired_gate_summary.csv")
    paired_ok = bool_text(paired["paired_gate_passed"])
    if not contract_ok or not paired_ok:
        raise RuntimeError("active A/B gate failed; no active run is permitted")
    runtime = load_runtime(build_preregistered_args(output_dir, 12))
    warm_up(runtime)
    active_rows: list[dict[str, Any]] = []
    snapshots: dict[str, list[dict[str, Any]]] = {"original_v4c": [], "hierarchical_v0": []}
    stage_rows: list[dict[str, Any]] = []
    for trial, variant in ACTIVE_ORDER:
        runtime.args = build_preregistered_args(output_dir, trial)
        if variant == "original_v4c":
            with hook_context(OriginalCaptureHook()) as hook:
                row = run_original_trial(runtime, trial)
            events = hook.events
            snapshots[variant].extend(snapshot for event in events for snapshot in event["snapshot"])
        else:
            with hook_context(HierarchicalActiveHook()) as hook:
                row = run_original_trial(runtime, trial)
            events = hook.events
            snapshots[variant].extend(snapshot for event in events for snapshot in event["result"].stage_a_snapshot + event["result"].stage_b_snapshot)
        active_rows.append(trial_summary(row, trial, variant, events))
        if variant == "hierarchical_v0":
            stage_a_times = [event["result"].stage_a_runtime_sec for event in events]
            stage_b_times = [event["result"].stage_b_runtime_sec for event in events if event["result"].stage_b_entered]
            total_times = [event["runtime_sec"] for event in events]
            stage_rows.append(
                {
                    "trial_id": trial, "activation_count": len(events),
                    "stage_a_success_count": sum(event["result"].stage_a_selected for event in events),
                    "stage_a_success_rate": sum(event["result"].stage_a_selected for event in events) / len(events) if events else None,
                    "stage_b_entry_count": sum(event["result"].stage_b_entered for event in events),
                    "stage_b_entry_rate": sum(event["result"].stage_b_entered for event in events) / len(events) if events else None,
                    "stage_a_median_runtime_sec": median_or_none(stage_a_times),
                    "stage_b_median_runtime_sec": median_or_none(stage_b_times),
                    "total_recovery_median_runtime_sec": median_or_none(total_times),
                    "notes": "Active hierarchical trajectory; no raw candidate records retained.",
                }
            )
    active_fields = [
        "scene", "trial_id", "method_variant", "navigation_executed", "num_steps", "stop_reason",
        "collision", "qp_infeasible_count", "base_horizon_margin_violation_count",
        "exec_horizon_margin_violation_count", "recovery_used_count", "recovery_success_count",
        "recovery_failed_count", "stage_a_success_count", "stage_b_entry_count",
        "goal_distance_reduction_ratio", "runtime_mean", "runtime_recovery_mean",
        "runtime_recovery_median", "runtime_recovery_p95", "seconds_total", "notes",
    ]
    write_csv(output_dir / "active_ab_trial_summary.csv", active_rows, active_fields)
    write_csv(output_dir / "stage_usage_summary.csv", stage_rows, list(stage_rows[0]))
    family_rows = aggregate_family_snapshots(snapshots["original_v4c"], "original_v4c") + aggregate_family_snapshots(snapshots["hierarchical_v0"], "hierarchical_v0")
    family_fields = [
        "method_variant", "family", "generated_count", "feasible_count", "selected_count",
        "unique_feasible_step_count", "selected_recovery_success_count", "mean_selected_min_h",
        "mean_selected_progress_delta", "generation_runtime_sec", "evaluation_runtime_sec",
        "runtime_share", "notes",
    ]
    write_csv(output_dir / "candidate_family_summary.csv", family_rows, family_fields)
    runtime_rows: list[dict[str, Any]] = []
    progress_rows: list[dict[str, Any]] = []
    safety_rows: list[dict[str, Any]] = []
    aggregate: dict[str, dict[str, Any]] = {}
    for variant in ("original_v4c", "hierarchical_v0"):
        rows = [row for row in active_rows if row["method_variant"] == variant]
        medians = [float(row["runtime_recovery_median"]) for row in rows if row["runtime_recovery_median"] is not None]
        all_runtime = [float(row["runtime_recovery_mean"]) for row in rows if row["runtime_recovery_mean"] is not None]
        aggregate[variant] = {
            "collision_count": sum(bool_text(row["collision"]) for row in rows),
            "qp_infeasible_count": sum(int(row["qp_infeasible_count"]) for row in rows),
            "recovery_failed_count": sum(int(row["recovery_failed_count"]) for row in rows),
            "exec_horizon_margin_violation_count": sum(int(row["exec_horizon_margin_violation_count"]) for row in rows),
            "activation_count": sum(int(row["recovery_used_count"]) for row in rows),
            "runtime_median": median_or_none(medians),
            "runtime_mean": sum(all_runtime) / len(all_runtime) if all_runtime else None,
            "progress_mean": sum(float(row["goal_distance_reduction_ratio"]) for row in rows) / len(rows) if rows else None,
        }
        runtime_rows.append({"method_variant": variant, **aggregate[variant]})
        progress_rows.append({"method_variant": variant, "trial_count": len(rows), "goal_distance_reduction_ratio_mean": aggregate[variant]["progress_mean"], "stop_reasons": json.dumps({reason: sum(row["stop_reason"] == reason for row in rows) for reason in sorted({row["stop_reason"] for row in rows})}), "notes": "Progress is reported, not a success criterion."})
        safety_rows.append({"method_variant": variant, **{key: aggregate[variant][key] for key in ("collision_count", "qp_infeasible_count", "recovery_failed_count", "exec_horizon_margin_violation_count")}, "guardrail_passed": aggregate[variant]["collision_count"] == 0 and aggregate[variant]["qp_infeasible_count"] == 0})
    write_csv(output_dir / "runtime_summary.csv", runtime_rows, list(runtime_rows[0]))
    write_csv(output_dir / "progress_summary.csv", progress_rows, list(progress_rows[0]))
    write_csv(output_dir / "safety_guardrail_summary.csv", safety_rows, list(safety_rows[0]))
    original_median = aggregate["original_v4c"]["runtime_median"]
    hierarchical_median = aggregate["hierarchical_v0"]["runtime_median"]
    reduction = None
    if original_median is not None and original_median > 0 and hierarchical_median is not None:
        reduction = (original_median - hierarchical_median) / original_median
    stage_a_success = sum(int(row["stage_a_success_count"]) for row in active_rows if row["method_variant"] == "hierarchical_v0")
    stage_b_entry = sum(int(row["stage_b_entry_count"]) for row in active_rows if row["method_variant"] == "hierarchical_v0")
    success = bool(
        aggregate["hierarchical_v0"]["collision_count"] == 0
        and aggregate["hierarchical_v0"]["qp_infeasible_count"] == 0
        and aggregate["hierarchical_v0"]["recovery_failed_count"] <= aggregate["original_v4c"]["recovery_failed_count"]
        and aggregate["hierarchical_v0"]["exec_horizon_margin_violation_count"] <= aggregate["original_v4c"]["exec_horizon_margin_violation_count"]
        and stage_a_success > 0 and reduction is not None and reduction >= 0.20
    )
    decision = "retain_hierarchical_v0_for_small_cohort" if success else "stop_current_hierarchical_version"
    metrics = {
        "task": "R-V4C-1 Hierarchical Candidate Evaluation V0",
        "new_scientific_experiment_run": True, "paired_shadow_audit_run": True, "active_ab_run": True,
        "scene": "flight", "trials": list(FIXED_TRIALS), "comparator": "original_v4c_h3_n128",
        "prototype": "hierarchical_candidate_evaluation_v0", "contract_checks_passed": contract_ok,
        "stage_b_equivalence_passed": contract_ok, "state_isolation_passed": bool_text(paired["state_isolation_passed"]),
        "official_core_source_modified": False, "forbidden_paths_modified": False, "raw_traces_written": False,
        "original_activation_count": aggregate["original_v4c"]["activation_count"], "hierarchical_activation_count": aggregate["hierarchical_v0"]["activation_count"],
        "stage_a_success_count": stage_a_success, "stage_b_entry_count": stage_b_entry,
        "paired_feasibility_regression_count": int(paired["paired_feasibility_regression_count"]),
        "original_collision_count": aggregate["original_v4c"]["collision_count"], "hierarchical_collision_count": aggregate["hierarchical_v0"]["collision_count"],
        "original_qp_infeasible_count": aggregate["original_v4c"]["qp_infeasible_count"], "hierarchical_qp_infeasible_count": aggregate["hierarchical_v0"]["qp_infeasible_count"],
        "original_recovery_failed_count": aggregate["original_v4c"]["recovery_failed_count"], "hierarchical_recovery_failed_count": aggregate["hierarchical_v0"]["recovery_failed_count"],
        "original_exec_horizon_margin_violation_count": aggregate["original_v4c"]["exec_horizon_margin_violation_count"], "hierarchical_exec_horizon_margin_violation_count": aggregate["hierarchical_v0"]["exec_horizon_margin_violation_count"],
        "original_activated_recovery_runtime_median_sec": original_median, "hierarchical_activated_recovery_runtime_median_sec": hierarchical_median,
        "activated_runtime_reduction_fraction": reduction, "runtime_target_met": bool(reduction is not None and reduction >= 0.20),
        "progress_reported": True, "performance_improvement_claimed": False, "generalized_runtime_improvement_claimed": False,
        "r_v4c1_decision": decision,
        "limitations": ["three targeted flight trials only", "configuration-specific H3_N128 evidence", "not flight20", "not full100", "no statistical significance", "not a planner", "does not establish generalized runtime improvement", "does not establish completion improvement"],
    }
    (output_dir / "metrics.json").write_text(json.dumps(metrics, indent=2) + "\n", encoding="utf-8")
    (output_dir / "analysis_notes.md").write_text("# Analysis Notes\n\nCandidate-family runtime is apportioned by generated-candidate count because the original V4-C functions do not expose per-candidate timers. Activated-step runtime is measured around candidate generation/evaluation only. No raw controls or per-step records are retained.\n", encoding="utf-8")
    write_report(output_dir, metrics, active_rows)
    return metrics


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output-dir", type=Path, required=True)
    args = parser.parse_args()
    metrics = run_active_ab(args.output_dir)
    print(json.dumps({"decision": metrics["r_v4c1_decision"], "runtime_target_met": metrics["runtime_target_met"]}, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
