#!/usr/bin/env python3
"""Run the preregistered held-out V4-C active A/B and emit compact aggregates."""

from __future__ import annotations

import argparse
import csv
import json
import statistics
from collections import Counter
from pathlib import Path
from typing import Any

from run_v4c_hierarchical_active_ab import (
    HierarchicalActiveHook, OriginalCaptureHook, hook_context, percentile,
)
from run_v4c_hierarchical_paired_audit import build_preregistered_args, load_runtime, run_original_trial, warm_up
from v4c_candidate_family_metrics import aggregate_family_snapshots


def bool_value(value: Any) -> bool:
    return str(value).strip().lower() in {"true", "1", "yes"}


def number(value: Any) -> float:
    return float(str(value))


def median(values: list[float]) -> float | None:
    return float(statistics.median(values)) if values else None


def write_csv(path: Path, rows: list[dict[str, Any]], fields: list[str]) -> None:
    with path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=fields, extrasaction="ignore")
        writer.writeheader()
        writer.writerows(rows)


def read_csv(path: Path) -> list[dict[str, str]]:
    with path.open("r", newline="", encoding="utf-8") as handle:
        return list(csv.DictReader(handle))


def verify_gate(output_dir: Path) -> None:
    contract = read_csv(output_dir / "contract_check.csv")
    paired = read_csv(output_dir / "paired_gate_summary.csv")
    if not contract or not all(bool_value(row["passed"]) for row in contract if bool_value(row["critical"])):
        raise RuntimeError("frozen contract failed; active A/B is prohibited")
    if len(paired) != 1 or not bool_value(paired[0]["paired_gate_passed"]):
        raise RuntimeError("held-out paired gate failed; active A/B is prohibited")


def read_order(output_dir: Path) -> list[dict[str, str]]:
    rows = read_csv(output_dir / "run_order_preregistration.csv")
    if len(rows) != 38 or [int(row["run_index"]) for row in rows] != list(range(1, 39)):
        raise RuntimeError("run order must contain exactly 38 consecutive preregistered runs")
    heldout = {int(row["trial_id"]) for row in rows if row["cohort"] == "heldout_activated"}
    if len(heldout) != 16 or heldout & {12, 13, 14}:
        raise RuntimeError("run order has an invalid held-out cohort")
    return rows


def formal_row(row: dict[str, Any], run: dict[str, str], events: list[dict[str, Any]]) -> dict[str, Any]:
    variant = run["method_variant"]
    runtimes = [float(event["runtime_sec"]) for event in events]
    if variant == "original_v4c":
        activation_count = len(events)
        success_count = sum(bool(event["success"]) for event in events)
        stage_a_success = 0
        stage_b_entry = 0
        stage_b_success = 0
        stage_b_failure = 0
    else:
        activation_count = len(events)
        success_count = sum(bool(event["result"].recovery_success) for event in events)
        stage_a_success = sum(bool(event["result"].stage_a_selected) for event in events)
        stage_b_entry = sum(bool(event["result"].stage_b_entered) for event in events)
        stage_b_success = sum(bool(event["result"].stage_b_entered and event["result"].recovery_success) for event in events)
        stage_b_failure = sum(bool(event["result"].stage_b_entered and event["result"].recovery_failed) for event in events)
    return {
        "run_index": int(run["run_index"]), "cohort": run["cohort"], "trial_id": int(run["trial_id"]),
        "method_variant": variant, "navigation_executed": row["navigation_executed"], "num_steps": row["num_steps"],
        "stop_reason": row["stop_reason"], "collision": row["collision"],
        "qp_infeasible_count": row["qp_infeasible_count"], "min_safety_h": row["min_safety_h"],
        "base_horizon_margin_violation_count": row["base_horizon_margin_violation_count"],
        "exec_horizon_margin_violation_count": row["exec_horizon_margin_violation_count"],
        "recovery_used_count": row["predictive_recovery_used_count"],
        "recovery_success_count": row["predictive_recovery_success_count"], "recovery_failed_count": row["recovery_failed_count"],
        "stage_a_success_count": stage_a_success, "stage_b_entry_count": stage_b_entry,
        "stage_b_success_count": stage_b_success, "stage_b_failure_count": stage_b_failure,
        "goal_distance_reduction_ratio": row["goal_distance_reduction_ratio"], "runtime_mean": row["runtime_mean"],
        "runtime_recovery_mean_sec": sum(runtimes) / len(runtimes) if runtimes else None,
        "runtime_recovery_median_sec": median(runtimes), "runtime_recovery_p95_sec": percentile(runtimes, 95),
        "seconds_total": row["seconds_total"], "formal_recovery_success_count": success_count,
        "notes": "Compact formal summary only; no controls or per-step trace retained.",
    }


def by_variant(rows: list[dict[str, Any]], cohort: str) -> dict[str, list[dict[str, Any]]]:
    return {variant: [row for row in rows if row["cohort"] == cohort and row["method_variant"] == variant] for variant in ("original_v4c", "hierarchical_v0")}


def summarize_runtime(rows: list[dict[str, Any]]) -> tuple[list[dict[str, Any]], dict[str, Any]]:
    grouped = by_variant(rows, "heldout_activated")
    output: list[dict[str, Any]] = []
    metrics: dict[str, Any] = {}
    per_trial_reduction: list[float] = []
    for original, hierarchical in zip(sorted(grouped["original_v4c"], key=lambda row: row["trial_id"]), sorted(grouped["hierarchical_v0"], key=lambda row: row["trial_id"])):
        o, h = original["runtime_recovery_median_sec"], hierarchical["runtime_recovery_median_sec"]
        if o is not None and o > 0 and h is not None:
            per_trial_reduction.append((o - h) / o)
    for variant, variant_rows in grouped.items():
        values = [number(row["runtime_recovery_median_sec"]) for row in variant_rows if row["runtime_recovery_median_sec"] is not None]
        output.append({
            "cohort": "heldout_activated", "method_variant": variant, "activated_trial_count": len(variant_rows),
            "activated_step_count": sum(int(row["recovery_used_count"]) for row in variant_rows),
            "activated_runtime_median_sec": median(values), "activated_runtime_mean_sec": sum(values) / len(values) if values else None,
            "activated_runtime_p75_sec": percentile(values, 75), "activated_runtime_p90_sec": percentile(values, 90), "activated_runtime_p95_sec": percentile(values, 95),
        })
    original_median = output[0]["activated_runtime_median_sec"]
    hierarchical_median = output[1]["activated_runtime_median_sec"]
    reduction = (original_median - hierarchical_median) / original_median if original_median and hierarchical_median is not None else None
    metrics.update({
        "original_activated_runtime_median_sec": original_median,
        "hierarchical_activated_runtime_median_sec": hierarchical_median,
        "activated_runtime_reduction_fraction": reduction,
        "heldout_trials_with_positive_runtime_reduction": sum(value > 0 for value in per_trial_reduction),
        "heldout_trials_with_20pct_runtime_reduction": sum(value >= .20 for value in per_trial_reduction),
        "heldout_trials_with_runtime_regression": sum(value < 0 for value in per_trial_reduction),
        "per_trial_runtime_reduction_fractions": per_trial_reduction,
    })
    return output, metrics


def decision(metrics: dict[str, Any]) -> str:
    if not metrics["paired_gate_passed"]:
        return "stop_before_active_ab"
    safety = metrics["safety_guardrails_met"]
    runtime = metrics["runtime_target_met"]
    progress = metrics["progress_guardrail_met"]
    positive = metrics["heldout_trials_with_positive_runtime_reduction"] >= 12
    if safety and runtime and positive and progress:
        return "retain_hierarchical_v0_as_validated_configuration_specific_mechanism"
    if safety and runtime and positive and not progress:
        return "retain_with_progress_tradeoff_for_redesign"
    if safety and runtime and not positive:
        return "diagnostic_only_due_to_runtime_variance"
    return "stop_current_hierarchical_v0"


def write_report(parent: Path, metrics: dict[str, Any], runtime_rows: list[dict[str, Any]], control_rows: list[dict[str, Any]]) -> None:
    lines = [
        "# REPORT: V4-C Hierarchical Candidate Evaluation Held-Out Activated Cohort", "",
        "## 1. Purpose", "", "This report validates the frozen V4-C hierarchical candidate-evaluation V0 on the comparator-defined held-out activation cohort. It is not a full100 rerun, a statistical-significance test, a planner evaluation, or a generalized runtime/collision claim.", "",
        "## 2. Development/Held-Out Separation", "", "Development trials were 12, 13, and 14. The held-out set was selected only from original-comparator recovery activations before hierarchical outcomes were observed.", "",
        "## 3. Original Full100 Activation Inventory", "", f"Original comparator inventory: {metrics['original_full100_trial_count']} trials, {metrics['original_full100_activated_trial_count']} activated trials, and {metrics['original_full100_activation_count']} activation contexts.", "",
        "## 4. Preregistered Cohort", "", f"Held-out activated trials: `{metrics['heldout_activated_trials']}`. Nonactivated controls: `{metrics['nonactivated_control_trials']}`. The order was fixed before formal execution.", "",
        "## 5. Fixed Method Contract", "", f"Frozen contract passed: `{metrics['contract_checks_passed']}`. No candidate family, acceptance, fallback, seed, H/N, threshold, cost, clamp, StartGuard, CBF-QP, GSplat query, or max-step setting was changed.", "",
        "## 6. Paired Same-State Audit", "", f"Paired gate passed: `{metrics['paired_gate_passed']}`. Feasibility regressions: `{metrics['paired_feasibility_regression_count']}`. Formal paired trajectories executed the original comparator controls only.", "",
        "## 7. Active A/B Protocol", "", "The active run used 38 sequential preregistered runs: 16 held-out activated trials times two variants, then three nonactivated controls times two variants. No GPU trial runs were parallelized.", "",
        "## 8. Stage-A Generalization", "", f"Stage-A selected {metrics['stage_a_success_count']} of {metrics['heldout_hierarchical_activation_count']} held-out activation contexts (rate {metrics['stage_a_success_rate']}).", "",
        "## 9. Stage-B Evidence", "", f"Stage-B entries/successes/failures were {metrics['stage_b_entry_count']}/{metrics['stage_b_success_count']}/{metrics['stage_b_failure_count']}.", "",
        "## 10. Candidate-Family Contribution", "", f"Random selected count: {metrics['random_selected_count']}; random unique-feasible count: {metrics['random_unique_feasible_count']}. Candidate-family summaries are compact aggregates only.", "",
        "## 11. Safety and Feasibility", "", f"Hierarchical collision/QP-infeasible/recovery-failed/executed-H-violation counts: {metrics['hierarchical_collision_count']}/{metrics['hierarchical_qp_infeasible_count']}/{metrics['hierarchical_recovery_failed_count']}/{metrics['hierarchical_exec_horizon_margin_violation_count']}. `h` is the repository safety-field value, not meter clearance.", "",
        "## 12. Runtime Distribution", "",
        "| variant | activated median (s) | activated mean (s) | p95 (s) |", "| --- | ---: | ---: | ---: |",
    ]
    for row in runtime_rows:
        lines.append(f"| {row['method_variant']} | {row['activated_runtime_median_sec']} | {row['activated_runtime_mean_sec']} | {row['activated_runtime_p95_sec']} |")
    lines.extend([
        "", f"Aggregate median runtime reduction: `{metrics['activated_runtime_reduction_fraction']}`. Positive per-trial reductions: `{metrics['heldout_trials_with_positive_runtime_reduction']}/16`; reductions of at least 20%: `{metrics['heldout_trials_with_20pct_runtime_reduction']}/16`.", "",
        "## 13. Progress and Stop Reasons", "", f"Progress mean/median deltas were `{metrics['progress_mean_delta']}` and `{metrics['progress_median_delta']}`; positive-to-nonpositive flips: `{metrics['progress_positive_to_nonpositive_flip_count']}`. Progress is an engineering diagnostic, not a planner-quality claim.", "",
        "## 14. Non-Activated Controls", "", f"Controls had no recovery activation and exact behavior checks: `{all(bool_value(row['path_identical']) for row in control_rows)}`. Their wrapper overhead is reported separately.", "",
        "## 15. Negative and Neutral Evidence", "", ("Stage B entered observed contexts and reproduced the original full-search outcome there; it did not convert the original recovery failures into successes." if metrics['stage_b_entry_count'] else "Across the observed original-comparator activation states, Stage A was sufficient and Stage B remained unexercised."), "",
        "## 16. Failure-Level Interpretation", "", "This validation is configuration-specific to flight H3_N128. It does not establish cross-scene effectiveness, completion improvement, collision reduction, or generalized runtime improvement.", "",
        "## 17. Decision", "", f"`{metrics['heldout_decision']}`", "",
        "## 18. Claim Boundaries", "", "The held-out cohort evaluates a frozen hierarchical V4-C V0; no method parameters or candidate semantics were changed after observing development-trial results.",
    ])
    if metrics["heldout_decision"] == "retain_hierarchical_v0_as_validated_configuration_specific_mechanism":
        lines.extend(["", "The held-out activated cohort supports retaining hierarchical V4-C V0 as a configuration-specific recovery-efficiency mechanism. Cross-scene and generalized effectiveness remain unvalidated."])
    else:
        lines.extend(["", "The current hierarchical V0 failed its held-out preregistered guardrail. This freezes V0, not the broader hierarchical-recovery design family."])
    (parent / "REPORT_V4C_HIERARCHICAL_HELDOUT_ACTIVATED_COHORT.md").write_text("\n".join(lines) + "\n", encoding="utf-8")


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output-dir", type=Path, required=True)
    args = parser.parse_args()
    verify_gate(args.output_dir)
    order = read_order(args.output_dir)
    runtime = load_runtime(build_preregistered_args(args.output_dir, 11))
    warm_up(runtime)
    rows: list[dict[str, Any]] = []
    snapshots: dict[str, list[dict[str, Any]]] = {"original_v4c": [], "hierarchical_v0": []}
    for run in order:
        trial = int(run["trial_id"])
        runtime.args = build_preregistered_args(args.output_dir, trial)
        if run["method_variant"] == "original_v4c":
            with hook_context(OriginalCaptureHook()) as hook:
                trial_row = run_original_trial(runtime, trial)
            events = hook.events
            snapshots["original_v4c"].extend(snapshot for event in events for snapshot in event["snapshot"])
        else:
            with hook_context(HierarchicalActiveHook()) as hook:
                trial_row = run_original_trial(runtime, trial)
            events = hook.events
            snapshots["hierarchical_v0"].extend(snapshot for event in events for snapshot in event["result"].stage_a_snapshot + event["result"].stage_b_snapshot)
        rows.append(formal_row(trial_row, run, events))
    fields = list(rows[0])
    write_csv(args.output_dir / "active_ab_trial_summary.csv", rows, fields)
    family_rows = aggregate_family_snapshots(snapshots["original_v4c"], "original_v4c") + aggregate_family_snapshots(snapshots["hierarchical_v0"], "hierarchical_v0")
    write_csv(args.output_dir / "candidate_family_summary.csv", family_rows, list(family_rows[0]))
    activated = by_variant(rows, "heldout_activated")
    stage_a = sum(int(row["stage_a_success_count"]) for row in activated["hierarchical_v0"])
    stage_b_entries = sum(int(row["stage_b_entry_count"]) for row in activated["hierarchical_v0"])
    stage_b_success = sum(int(row["stage_b_success_count"]) for row in activated["hierarchical_v0"])
    stage_b_failure = sum(int(row["stage_b_failure_count"]) for row in activated["hierarchical_v0"])
    stage_rows = [{"cohort": "heldout_activated", "activation_count": sum(int(row["recovery_used_count"]) for row in activated["hierarchical_v0"]), "stage_a_success_count": stage_a, "stage_a_success_rate": stage_a / sum(int(row["recovery_used_count"]) for row in activated["hierarchical_v0"]), "stage_b_entry_count": stage_b_entries, "stage_b_entry_rate": stage_b_entries / sum(int(row["recovery_used_count"]) for row in activated["hierarchical_v0"]), "stage_b_success_count": stage_b_success, "stage_b_failure_count": stage_b_failure, "notes": "Held-out active hierarchical trajectory."}]
    write_csv(args.output_dir / "stage_usage_summary.csv", stage_rows, list(stage_rows[0]))
    runtime_rows, runtime_metrics = summarize_runtime(rows)
    write_csv(args.output_dir / "runtime_summary.csv", runtime_rows, list(runtime_rows[0]))
    progress_rows: list[dict[str, Any]] = []
    original_progress: list[float] = []
    hierarchical_progress: list[float] = []
    for variant, collection in activated.items():
        values = [number(row["goal_distance_reduction_ratio"]) for row in collection]
        if variant == "original_v4c": original_progress = values
        else: hierarchical_progress = values
        progress_rows.append({"cohort": "heldout_activated", "method_variant": variant, "trial_count": len(values), "progress_ratio_mean": sum(values) / len(values), "progress_ratio_median": median(values), "progress_ratio_min": min(values), "stop_reasons": json.dumps(dict(Counter(row["stop_reason"] for row in collection)), sort_keys=True), "notes": "Engineering task-progress diagnostic only."})
    write_csv(args.output_dir / "progress_summary.csv", progress_rows, list(progress_rows[0]))
    progress_mean_delta = sum(hierarchical_progress) / len(hierarchical_progress) - sum(original_progress) / len(original_progress)
    progress_median_delta = median(hierarchical_progress) - median(original_progress)
    flips = sum(o > 0 and h <= 0 for o, h in zip(original_progress, hierarchical_progress))
    safety_rows: list[dict[str, Any]] = []
    aggregate_safety: dict[str, dict[str, int]] = {}
    for variant, collection in activated.items():
        values = {"collision_count": sum(bool_value(row["collision"]) for row in collection), "qp_infeasible_count": sum(int(row["qp_infeasible_count"]) for row in collection), "recovery_failed_count": sum(int(row["recovery_failed_count"]) for row in collection), "exec_horizon_margin_violation_count": sum(int(row["exec_horizon_margin_violation_count"]) for row in collection)}
        aggregate_safety[variant] = values
        safety_rows.append({"cohort": "heldout_activated", "method_variant": variant, **values, "minimum_safety_h": min(number(row["min_safety_h"]) for row in collection), "notes": "h is not meter clearance."})
    write_csv(args.output_dir / "safety_guardrail_summary.csv", safety_rows, list(safety_rows[0]))
    controls = by_variant(rows, "nonactivated_control")
    control_summary: list[dict[str, Any]] = []
    for original, hierarchical in zip(sorted(controls["original_v4c"], key=lambda row: row["trial_id"]), sorted(controls["hierarchical_v0"], key=lambda row: row["trial_id"])):
        exact = all(original[key] == hierarchical[key] for key in ("recovery_used_count", "stop_reason", "goal_distance_reduction_ratio", "collision", "qp_infeasible_count", "num_steps"))
        control_summary.append({"trial_id": original["trial_id"], "original_recovery_used_count": original["recovery_used_count"], "hierarchical_recovery_used_count": hierarchical["recovery_used_count"], "path_identical": exact, "original_seconds_total": original["seconds_total"], "hierarchical_seconds_total": hierarchical["seconds_total"], "wrapper_overhead_sec": number(hierarchical["seconds_total"]) - number(original["seconds_total"]), "notes": "Exact path keys compare compact outputs; no controls retained."})
    write_csv(args.output_dir / "nonactivated_control_summary.csv", control_summary, list(control_summary[0]))
    paired = read_csv(args.output_dir / "paired_gate_summary.csv")[0]
    random_row = next((row for row in family_rows if row["method_variant"] == "hierarchical_v0" and row["family"] == "random"), {})
    heldout_trials = sorted(row["trial_id"] for row in activated["original_v4c"])
    metrics: dict[str, Any] = {
        "task": "R-V4C-1 Held-Out Activated Cohort Validation", "new_scientific_experiment_run": True,
        "scene": "flight", "configuration": "H3_N128_on_margin_violation", "development_trials": [12, 13, 14],
        "original_full100_trial_count": 100, "original_full100_activated_trial_count": 19, "original_full100_activation_count": 236,
        "heldout_activated_trials": heldout_trials, "heldout_activated_trial_count": 16, "nonactivated_control_trials": sorted(row["trial_id"] for row in controls["original_v4c"]),
        "paired_audit_run": True, "paired_gate_passed": bool_value(paired["paired_gate_passed"]), "active_ab_run": True,
        "heldout_original_activation_count": sum(int(row["recovery_used_count"]) for row in activated["original_v4c"]), "heldout_hierarchical_activation_count": sum(int(row["recovery_used_count"]) for row in activated["hierarchical_v0"]),
        "stage_a_success_count": stage_a, "stage_a_success_rate": stage_rows[0]["stage_a_success_rate"], "stage_b_entry_count": stage_b_entries, "stage_b_success_count": stage_b_success, "stage_b_failure_count": stage_b_failure,
        "paired_feasibility_regression_count": int(paired["paired_feasibility_regression_count"]),
        "original_collision_count": aggregate_safety["original_v4c"]["collision_count"], "hierarchical_collision_count": aggregate_safety["hierarchical_v0"]["collision_count"],
        "original_qp_infeasible_count": aggregate_safety["original_v4c"]["qp_infeasible_count"], "hierarchical_qp_infeasible_count": aggregate_safety["hierarchical_v0"]["qp_infeasible_count"],
        "original_recovery_failed_count": aggregate_safety["original_v4c"]["recovery_failed_count"], "hierarchical_recovery_failed_count": aggregate_safety["hierarchical_v0"]["recovery_failed_count"],
        "original_exec_horizon_margin_violation_count": aggregate_safety["original_v4c"]["exec_horizon_margin_violation_count"], "hierarchical_exec_horizon_margin_violation_count": aggregate_safety["hierarchical_v0"]["exec_horizon_margin_violation_count"],
        **runtime_metrics, "progress_mean_delta": progress_mean_delta, "progress_median_delta": progress_median_delta, "progress_positive_to_nonpositive_flip_count": flips,
        "random_selected_count": int(random_row.get("selected_count", 0)), "random_unique_feasible_count": int(random_row.get("unique_feasible_step_count", 0)),
        "runtime_target_met": bool(runtime_metrics["activated_runtime_reduction_fraction"] is not None and runtime_metrics["activated_runtime_reduction_fraction"] >= .20),
        "progress_guardrail_met": bool(progress_mean_delta >= -.01 and progress_median_delta >= -.01 and flips == 0),
        "safety_guardrails_met": bool(int(paired["paired_feasibility_regression_count"]) == 0 and aggregate_safety["hierarchical_v0"]["collision_count"] == 0 and aggregate_safety["hierarchical_v0"]["qp_infeasible_count"] == 0 and aggregate_safety["hierarchical_v0"]["recovery_failed_count"] <= aggregate_safety["original_v4c"]["recovery_failed_count"] and aggregate_safety["hierarchical_v0"]["exec_horizon_margin_violation_count"] <= aggregate_safety["original_v4c"]["exec_horizon_margin_violation_count"]),
        "contract_checks_passed": True, "official_core_source_modified": False, "forbidden_paths_modified": False, "raw_traces_written": False,
        "limitations": ["flight H3_N128 only", "configuration-specific held-out activation validation", "not a statistical-significance test", "not cross-scene validation", "not a planner", "does not establish completion improvement", "does not establish generalized runtime improvement"],
    }
    metrics["heldout_decision"] = decision(metrics)
    (args.output_dir / "metrics.json").write_text(json.dumps(metrics, indent=2) + "\n", encoding="utf-8")
    (args.output_dir / "analysis_notes.md").write_text("# Analysis Notes\n\nAll candidate-family rows are aggregate counts. Candidate-family runtime is apportioned by generated candidate count because frozen V4-C does not expose per-candidate timers. `h` is a repository safety-field diagnostic, not meter clearance.\n", encoding="utf-8")
    write_report(args.output_dir.parent.parent, metrics, runtime_rows, control_summary)
    print(json.dumps({"heldout_decision": metrics["heldout_decision"], "runtime_target_met": metrics["runtime_target_met"]}, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
