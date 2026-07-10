#!/usr/bin/env python3
"""Run SAFC Level-3E robustness and failure-diagnosis audit."""

from __future__ import annotations

import argparse
import csv
import json
import math
from collections import defaultdict
from pathlib import Path
from typing import Any, Iterable, Sequence

from safc_level3b_warning_rich_targeted import (
    build_state,
    candidate_start_goal,
    horizon_warnings,
    import_smoke_wrapper,
    make_cbf,
    max_abs_tensor,
    min_query_h,
    nominal_and_safe,
    select_entrypoint,
)
from safc_warning_slowdown_policy import (
    SlowdownPolicyConfig,
    SlowdownPolicyInput,
    apply_scale_to_vector,
    compute_warning_slowdown,
)


ENTRYPOINT = "reproduction/scripts/run_official_runpy_smoke.py"
DEFAULT_CANDIDATES = ("C003", "C004", "C002", "C001", "C006")
DEFAULT_VARIANTS = (
    "current_policy",
    "milder_slowdown",
    "critical_only_slowdown",
)

COHORT = {
    "C003": {"scene": "flight", "trial_id": 14, "outcome": "positive"},
    "C004": {"scene": "flight", "trial_id": 85, "outcome": "negative"},
    "C002": {"scene": "flight", "trial_id": 12, "outcome": "positive"},
    "C001": {"scene": "flight", "trial_id": 13, "outcome": "positive"},
    "C006": {"scene": "flight", "trial_id": 31, "outcome": "neutral"},
}

VARIANTS = {
    "current_policy": {
        "variant_id": "A",
        "variant_name": "current_policy",
        "warning_scale": 0.75,
        "persistent_warning_scale": 0.50,
        "critical_warning_scale": 0.25,
        "min_scale": 0.25,
        "activation_rule": "H1/H2/H3 warning-streak slowdown",
        "hypothesis": "Reference Level-3D active policy.",
    },
    "milder_slowdown": {
        "variant_id": "B",
        "variant_name": "milder_slowdown",
        "warning_scale": 0.85,
        "persistent_warning_scale": 0.70,
        "critical_warning_scale": 0.50,
        "min_scale": 0.50,
        "activation_rule": "H1/H2/H3 warning-streak slowdown with milder scales",
        "hypothesis": "Diagnose whether aggressive slowdown contributes to stalling or warning increase.",
    },
    "critical_only_slowdown": {
        "variant_id": "C",
        "variant_name": "critical_only_slowdown",
        "warning_scale": 1.00,
        "persistent_warning_scale": 1.00,
        "critical_warning_scale": 0.50,
        "min_scale": 0.50,
        "activation_rule": "Only H3 or critical warning-streak slowdown changes wrapper command",
        "hypothesis": "Diagnose whether avoiding H1/H2 slowdown changes mixed outcomes.",
    },
}

PREREG_FIELDS = (
    "candidate_id",
    "scene",
    "trial_id",
    "level3d_outcome_class",
    "level3d_baseline_warning",
    "level3d_active_warning",
    "level3d_delta",
    "level3d_baseline_stop_reason",
    "level3d_active_stop_reason",
    "included",
    "diagnosis_question",
    "notes",
)

VARIANT_FIELDS = (
    "variant_id",
    "variant_name",
    "warning_scale",
    "persistent_warning_scale",
    "critical_warning_scale",
    "min_scale",
    "activation_rule",
    "included",
    "hypothesis",
    "notes",
)

SUMMARY_FIELDS = (
    "candidate_id",
    "variant_id",
    "variant_name",
    "steps_observed",
    "natural_warning_steps",
    "first_natural_warning_step",
    "h1_warning_steps",
    "h2_warning_steps",
    "h3_warning_steps",
    "slowdown_active_steps",
    "first_slowdown_step",
    "min_scale_applied",
    "max_scale_applied",
    "max_control_delta_from_slowdown",
    "command_modified_only_when_warning",
    "collision_observed",
    "qp_infeasible_observed",
    "completed",
    "stop_reason",
    "progress_proxy",
    "u_nom_modified",
    "u_safe_internal_modified",
    "wrapper_exec_command_scaled",
    "control_scope_passed",
    "run_completed",
    "notes",
)

AGGREGATE_FIELDS = (
    "variant_id",
    "variant_name",
    "runs_completed",
    "total_warning_steps",
    "mean_warning_steps",
    "candidates_less_than_level3d_baseline",
    "candidates_equal_to_level3d_baseline",
    "candidates_more_than_level3d_baseline",
    "collision_count",
    "qp_infeasible_count",
    "completed_count",
    "stalled_count",
    "max_steps_count",
    "mean_progress_proxy",
    "control_scope_all_passed",
    "all_slowdown_after_or_at_warning",
    "performance_claim_allowed",
    "notes",
)

MIXED_FIELDS = (
    "candidate_id",
    "level3d_outcome_class",
    "best_variant_by_warning_count",
    "worst_variant_by_warning_count",
    "current_policy_warning",
    "milder_policy_warning",
    "critical_only_warning",
    "diagnosis",
    "recommended_policy_interpretation",
    "notes",
)

STOP_FIELDS = (
    "candidate_id",
    "variant_id",
    "stop_reason",
    "completed",
    "collision_observed",
    "qp_infeasible_observed",
    "progress_proxy",
    "stalled_or_max_steps",
    "diagnosis",
    "notes",
)

CONTROL_FIELDS = (
    "candidate_id",
    "variant_id",
    "u_nom_modified",
    "u_safe_internal_modified",
    "wrapper_exec_command_scaled",
    "command_modified_only_when_warning",
    "max_abs_delta_u_nom",
    "max_abs_delta_u_safe_internal",
    "max_abs_delta_wrapper_exec_due_to_slowdown",
    "control_scope_passed",
    "notes",
)

PROGRESS_FIELDS = (
    "candidate_id",
    "variant_id",
    "progress_proxy_available",
    "progress_proxy_name",
    "progress_proxy_value",
    "stop_reason",
    "diagnosis",
    "notes",
)


def write_csv(path: Path, fields: Sequence[str], rows: Iterable[dict[str, Any]]) -> None:
    with path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=fields)
        writer.writeheader()
        writer.writerows(rows)


def read_csv(path: Path) -> list[dict[str, str]]:
    if not path.is_file():
        raise RuntimeError(f"required compact CSV not found: {path}")
    with path.open("r", encoding="utf-8", newline="") as handle:
        return list(csv.DictReader(handle))


def parse_bool(value: Any) -> bool:
    if isinstance(value, bool):
        return value
    return str(value).strip().lower() in {"true", "1", "yes"}


def parse_float(value: Any) -> float:
    text = str(value).strip()
    return float(text) if text and text != "NA" else math.nan


def parse_int(value: Any) -> int:
    text = str(value).strip()
    return int(text) if text else 0


def parse_csv_arg(value: str) -> list[str]:
    return [item.strip() for item in value.split(",") if item.strip()]


def load_level3d_reference(
    repo_root: Path,
    level3d_results_dir: Path | None,
) -> tuple[dict[str, dict[str, str]], dict[str, dict[str, str]]]:
    base = (
        level3d_results_dir.resolve()
        if level3d_results_dir is not None
        else repo_root / "work/risk_aware_cbf/results/safc_level3d_small_targeted_cohort"
    )
    baseline = {
        row["candidate_id"]: row
        for row in read_csv(base / "per_candidate_baseline_summary.csv")
    }
    comparison = {
        row["candidate_id"]: row
        for row in read_csv(base / "per_candidate_ab_comparison.csv")
    }
    return baseline, comparison


def write_readme(path: Path) -> None:
    path.write_text(
        """# SAFC Level-3E Robustness and Failure-Diagnosis Results

This directory contains compact outputs for a bounded robustness and
failure-diagnosis audit over the Level-3D small targeted cohort. It evaluates
pre-registered slowdown variants to diagnose mixed outcomes, especially C004
and C006. This is not a benchmark and does not claim generalized performance
improvement.

Outputs:

* `diagnosis_preregistration.csv`
* `variant_config.csv`
* `per_candidate_variant_summary.csv`
* `variant_aggregate_summary.csv`
* `mixed_outcome_diagnosis.csv`
* `stop_reason_diagnosis.csv`
* `control_scope_summary.csv`
* `progress_proxy_summary.csv`
* `metrics.json`
* `robustness_notes.md`

No raw traces, full trial dumps, per-step dumps, active-constraint dumps,
trajectory samples, JSONL logs, images, or binary files should be committed
here.
""",
        encoding="utf-8",
    )


def preregistration_rows(
    candidates: Sequence[str],
    level3d_baseline: dict[str, dict[str, str]],
    level3d_comparison: dict[str, dict[str, str]],
) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    for candidate_id in candidates:
        candidate = COHORT[candidate_id]
        base = level3d_baseline[candidate_id]
        comp = level3d_comparison[candidate_id]
        outcome = candidate["outcome"]
        if outcome == "negative":
            question = "Diagnose why active warning steps increased under current policy."
        elif outcome == "neutral":
            question = "Diagnose whether any pre-registered variant changes warning count."
        else:
            question = "Check whether positive Level-3D behavior is robust to milder variants."
        rows.append(
            {
                "candidate_id": candidate_id,
                "scene": candidate["scene"],
                "trial_id": candidate["trial_id"],
                "level3d_outcome_class": outcome,
                "level3d_baseline_warning": base["natural_warning_steps"],
                "level3d_active_warning": comp["active_warning_steps"],
                "level3d_delta": comp["delta_warning_steps_active_minus_baseline"],
                "level3d_baseline_stop_reason": comp["baseline_stop_reason"],
                "level3d_active_stop_reason": comp["active_stop_reason"],
                "included": True,
                "diagnosis_question": question,
                "notes": "Pre-registered Level-3E diagnostic candidate.",
            }
        )
    return rows


def variant_rows(variants: Sequence[str]) -> list[dict[str, Any]]:
    return [
        {
            **VARIANTS[name],
            "included": True,
            "notes": "Pre-registered bounded diagnostic variant.",
        }
        for name in variants
    ]


def variant_config(name: str) -> SlowdownPolicyConfig:
    spec = VARIANTS[name]
    return SlowdownPolicyConfig(
        min_scale=spec["min_scale"],
        warning_scale=spec["warning_scale"],
        persistent_warning_scale=spec["persistent_warning_scale"],
        critical_warning_scale=spec["critical_warning_scale"],
    )


def run_variant(
    wrapper: Any,
    gsplat: Any,
    dynamics: Any,
    device: Any,
    args: argparse.Namespace,
    candidate_id: str,
    variant_name: str,
) -> tuple[dict[str, Any], dict[str, Any]]:
    candidate = COHORT[candidate_id]
    variant = VARIANTS[variant_name]
    start, goal_position, cfg = candidate_start_goal(
        wrapper, candidate["scene"], int(candidate["trial_id"])
    )
    x, goal = build_state(wrapper, device, start, goal_position)
    initial_distance = float(wrapper.torch.norm(x - goal).detach().cpu().item())
    cbf = make_cbf(wrapper, gsplat, dynamics, cfg)
    policy = variant_config(variant_name)
    dt = 0.05
    method = "ball-to-ellipsoid"
    warning_streak = 0
    clear_streak = 0
    previous_scale = 1.0
    steps = 0
    warnings = 0
    h1_count = 0
    h2_count = 0
    h3_count = 0
    slowdown_steps = 0
    first_warning: int | None = None
    first_slowdown: int | None = None
    active_scales: list[float] = []
    max_nom_delta = 0.0
    max_safe_delta = 0.0
    max_exec_delta = 0.0
    command_modified_only_when_warning = True
    collision = False
    qp_infeasible = False
    completed = False
    stop_reason = "max_steps"

    for step in range(1, args.max_steps + 1):
        x_previous = x.detach().clone()
        if min_query_h(wrapper, gsplat, x, cfg["radius"], method) < 0.0:
            collision = True
            stop_reason = "collision_before_command"
            break

        u_nom, u_safe = nominal_and_safe(wrapper, cbf, x, goal)
        u_nom_before = u_nom.detach().clone()
        u_safe_before = u_safe.detach().clone()
        u_exec_original = u_safe.detach().clone()
        steps += 1

        if not bool(cbf.solver_success):
            qp_infeasible = True
            stop_reason = "qp_infeasible"
            break

        h1, h2, h3, _ = horizon_warnings(
            wrapper,
            gsplat,
            x,
            u_safe,
            cfg["radius"],
            method,
            dt,
            args.dt_margin,
        )
        natural_warning = h1 or h2 or h3
        warnings += int(natural_warning)
        h1_count += int(h1)
        h2_count += int(h2)
        h3_count += int(h3)
        if natural_warning and first_warning is None:
            first_warning = step

        warning_streak = warning_streak + 1 if natural_warning else 0
        clear_streak = 0 if natural_warning else clear_streak + 1
        decision = compute_warning_slowdown(
            SlowdownPolicyInput(
                step=step,
                warning_streak=warning_streak,
                clear_streak=clear_streak,
                dt_warning_any=natural_warning,
                h1_warning=h1,
                h2_warning=h2,
                h3_warning=h3,
                qp_infeasible=False,
                recovery_used=False,
                collision=False,
                previous_scale=previous_scale,
            ),
            policy,
        )
        if not decision.bounded:
            raise RuntimeError(f"{candidate_id}/{variant_name} returned an unbounded scale")
        applied_scale = decision.scale if natural_warning else 1.0
        previous_scale = decision.scale
        slowdown_active = natural_warning and applied_scale < 1.0
        u_exec = apply_scale_to_vector(u_safe, applied_scale) if slowdown_active else u_safe.detach().clone()

        nom_delta = max_abs_tensor(wrapper, u_nom - u_nom_before)
        safe_delta = max_abs_tensor(wrapper, u_safe - u_safe_before)
        exec_delta = max_abs_tensor(wrapper, u_exec - u_exec_original)
        max_nom_delta = max(max_nom_delta, nom_delta)
        max_safe_delta = max(max_safe_delta, safe_delta)
        max_exec_delta = max(max_exec_delta, exec_delta)
        if exec_delta > 1e-12 and not natural_warning:
            command_modified_only_when_warning = False
        if slowdown_active:
            slowdown_steps += 1
            active_scales.append(float(applied_scale))
            if first_slowdown is None:
                first_slowdown = step

        x = wrapper.double_integrator_dynamics(x, u_exec) * dt + x
        if min_query_h(wrapper, gsplat, x, cfg["radius"], method) < 0.0:
            collision = True
            stop_reason = "collision_after_command"
            break
        if wrapper.torch.norm(x - x_previous) < 0.001:
            if wrapper.torch.norm(x_previous - goal) < 0.001:
                completed = True
                stop_reason = "goal_reached"
            else:
                stop_reason = "stalled_before_goal"
            break

    final_distance = float(wrapper.torch.norm(x - goal).detach().cpu().item())
    progress_proxy = initial_distance - final_distance
    first_slowdown_value = first_slowdown if first_slowdown is not None else ""
    first_warning_value = first_warning if first_warning is not None else ""
    timing_ok = (
        slowdown_steps == 0
        or (
            first_warning is not None
            and first_slowdown is not None
            and first_slowdown >= first_warning
        )
    )
    control_scope_passed = (
        max_nom_delta == 0.0
        and max_safe_delta == 0.0
        and command_modified_only_when_warning
        and timing_ok
        and ((slowdown_steps > 0 and max_exec_delta > 0.0) or slowdown_steps == 0)
    )
    summary = {
        "candidate_id": candidate_id,
        "variant_id": variant["variant_id"],
        "variant_name": variant["variant_name"],
        "steps_observed": steps,
        "natural_warning_steps": warnings,
        "first_natural_warning_step": first_warning_value,
        "h1_warning_steps": h1_count,
        "h2_warning_steps": h2_count,
        "h3_warning_steps": h3_count,
        "slowdown_active_steps": slowdown_steps,
        "first_slowdown_step": first_slowdown_value,
        "min_scale_applied": min(active_scales) if active_scales else 1.0,
        "max_scale_applied": max(active_scales) if active_scales else 1.0,
        "max_control_delta_from_slowdown": max_exec_delta,
        "command_modified_only_when_warning": command_modified_only_when_warning,
        "collision_observed": collision,
        "qp_infeasible_observed": qp_infeasible,
        "completed": completed,
        "stop_reason": stop_reason,
        "progress_proxy": progress_proxy,
        "u_nom_modified": max_nom_delta != 0.0,
        "u_safe_internal_modified": max_safe_delta != 0.0,
        "wrapper_exec_command_scaled": slowdown_steps > 0,
        "control_scope_passed": control_scope_passed,
        "run_completed": True,
        "notes": "Compact diagnostic run; progress_proxy is goal_distance_reduction only.",
    }
    details = {
        "max_nom_delta": max_nom_delta,
        "max_safe_delta": max_safe_delta,
        "max_exec_delta": max_exec_delta,
        "timing_ok": timing_ok,
        "progress_proxy": progress_proxy,
    }
    return summary, details


def failed_summary(candidate_id: str, variant_name: str, error: BaseException) -> tuple[dict[str, Any], dict[str, Any]]:
    variant = VARIANTS[variant_name]
    return (
        {
            "candidate_id": candidate_id,
            "variant_id": variant["variant_id"],
            "variant_name": variant["variant_name"],
            "steps_observed": 0,
            "natural_warning_steps": 0,
            "first_natural_warning_step": "",
            "h1_warning_steps": 0,
            "h2_warning_steps": 0,
            "h3_warning_steps": 0,
            "slowdown_active_steps": 0,
            "first_slowdown_step": "",
            "min_scale_applied": 1.0,
            "max_scale_applied": 1.0,
            "max_control_delta_from_slowdown": 0.0,
            "command_modified_only_when_warning": True,
            "collision_observed": False,
            "qp_infeasible_observed": False,
            "completed": False,
            "stop_reason": "run_failed",
            "progress_proxy": "NA",
            "u_nom_modified": False,
            "u_safe_internal_modified": False,
            "wrapper_exec_command_scaled": False,
            "control_scope_passed": False,
            "run_completed": False,
            "notes": f"Diagnostic run failed: {type(error).__name__}: {error}",
        },
        {"max_nom_delta": 0.0, "max_safe_delta": 0.0, "max_exec_delta": 0.0, "timing_ok": True},
    )


def aggregate_rows(
    variants: Sequence[str],
    rows: Sequence[dict[str, Any]],
    details: dict[tuple[str, str], dict[str, Any]],
    level3d_baseline: dict[str, dict[str, str]],
) -> tuple[list[dict[str, Any]], dict[str, dict[str, Any]]]:
    out: list[dict[str, Any]] = []
    metrics_by_variant: dict[str, dict[str, Any]] = {}
    for name in variants:
        spec = VARIANTS[name]
        subset = [row for row in rows if row["variant_name"] == name]
        completed = [row for row in subset if parse_bool(row["run_completed"])]
        warnings = [parse_int(row["natural_warning_steps"]) for row in subset]
        less, equal, more = [], [], []
        progress_values = []
        for row in subset:
            baseline_warning = parse_int(level3d_baseline[row["candidate_id"]]["natural_warning_steps"])
            value = parse_int(row["natural_warning_steps"])
            if value < baseline_warning:
                less.append(row["candidate_id"])
            elif value == baseline_warning:
                equal.append(row["candidate_id"])
            else:
                more.append(row["candidate_id"])
            progress = parse_float(row["progress_proxy"])
            if math.isfinite(progress):
                progress_values.append(progress)
        collision_count = sum(parse_bool(row["collision_observed"]) for row in subset)
        qp_count = sum(parse_bool(row["qp_infeasible_observed"]) for row in subset)
        completed_count = sum(parse_bool(row["completed"]) for row in subset)
        stalled_count = sum(row["stop_reason"] == "stalled_before_goal" for row in subset)
        max_steps_count = sum(row["stop_reason"] == "max_steps" for row in subset)
        control_ok = bool(subset) and all(parse_bool(row["control_scope_passed"]) for row in subset)
        timing_ok = bool(subset) and all(details[(row["candidate_id"], name)]["timing_ok"] for row in subset)
        mean_progress = sum(progress_values) / len(progress_values) if progress_values else "NA"
        variant_metrics = {
            "runs_completed": len(completed),
            "total_warning_steps": sum(warnings),
            "completed_count": completed_count,
            "collision_count": collision_count,
            "qp_infeasible_count": qp_count,
        }
        metrics_by_variant[name] = variant_metrics
        out.append(
            {
                "variant_id": spec["variant_id"],
                "variant_name": name,
                "runs_completed": len(completed),
                "total_warning_steps": sum(warnings),
                "mean_warning_steps": sum(warnings) / len(warnings) if warnings else "NA",
                "candidates_less_than_level3d_baseline": ",".join(less),
                "candidates_equal_to_level3d_baseline": ",".join(equal),
                "candidates_more_than_level3d_baseline": ",".join(more),
                "collision_count": collision_count,
                "qp_infeasible_count": qp_count,
                "completed_count": completed_count,
                "stalled_count": stalled_count,
                "max_steps_count": max_steps_count,
                "mean_progress_proxy": mean_progress,
                "control_scope_all_passed": control_ok,
                "all_slowdown_after_or_at_warning": timing_ok,
                "performance_claim_allowed": False,
                "notes": "Variant aggregate is diagnostic only, not generalized evidence.",
            }
        )
    return out, metrics_by_variant


def mixed_diagnosis_rows(
    candidates: Sequence[str],
    rows: Sequence[dict[str, Any]],
    level3d_baseline: dict[str, dict[str, str]],
) -> list[dict[str, Any]]:
    by_candidate = defaultdict(dict)
    for row in rows:
        by_candidate[row["candidate_id"]][row["variant_name"]] = row
    output = []
    for candidate_id in candidates:
        outcome = COHORT[candidate_id]["outcome"]
        warnings = {
            name: parse_int(by_candidate[candidate_id][name]["natural_warning_steps"])
            for name in DEFAULT_VARIANTS
        }
        best_value = min(warnings.values())
        worst_value = max(warnings.values())
        best = ",".join(name for name, value in warnings.items() if value == best_value)
        worst = ",".join(name for name, value in warnings.items() if value == worst_value)
        baseline_warning = parse_int(level3d_baseline[candidate_id]["natural_warning_steps"])
        current = warnings["current_policy"]
        milder = warnings["milder_slowdown"]
        critical = warnings["critical_only_slowdown"]
        if current > baseline_warning and milder <= baseline_warning:
            diagnosis = "milder_policy_helpful"
            interpretation = "C004-like warning increase appears scale-sensitive under milder slowdown."
        elif current > baseline_warning and critical <= baseline_warning:
            diagnosis = "critical_only_helpful"
            interpretation = "Warning increase may be tied to H1/H2 slowdown activation."
        elif current < baseline_warning and best_value < baseline_warning:
            diagnosis = "current_policy_helpful" if current == best_value else "candidate_sensitive"
            interpretation = "At least one variant preserves lower warning count than baseline in this diagnostic case."
        elif current == baseline_warning and milder == baseline_warning and critical == baseline_warning:
            diagnosis = "slowdown_neutral"
            interpretation = "All tested variants match baseline warning count in this context."
        elif worst_value > baseline_warning and best_value >= baseline_warning:
            diagnosis = "slowdown_potentially_harmful"
            interpretation = "No tested variant improves warning count relative to Level-3D baseline."
        else:
            diagnosis = "candidate_sensitive"
            interpretation = "Variant ordering changes across this candidate; do not generalize."
        notes = "C004 negative evidence is retained." if candidate_id == "C004" else "Small-cohort diagnostic candidate."
        if candidate_id == "C006":
            notes = "C006 neutral behavior is checked across all variants."
        output.append(
            {
                "candidate_id": candidate_id,
                "level3d_outcome_class": outcome,
                "best_variant_by_warning_count": best,
                "worst_variant_by_warning_count": worst,
                "current_policy_warning": current,
                "milder_policy_warning": milder,
                "critical_only_warning": critical,
                "diagnosis": diagnosis,
                "recommended_policy_interpretation": interpretation,
                "notes": notes,
            }
        )
    return output


def stop_reason_rows(rows: Sequence[dict[str, Any]]) -> list[dict[str, Any]]:
    out = []
    for row in rows:
        stop = row["stop_reason"]
        stalled_or_max = stop in {"stalled_before_goal", "max_steps", "max_steps_while_moving"}
        if parse_bool(row["completed"]):
            diagnosis = "completed"
        elif parse_bool(row["collision_observed"]):
            diagnosis = "collision_stop"
        elif parse_bool(row["qp_infeasible_observed"]):
            diagnosis = "qp_infeasible_stop"
        elif stalled_or_max:
            diagnosis = "active_variant_did_not_complete"
        else:
            diagnosis = "stop_reason_recorded"
        out.append(
            {
                "candidate_id": row["candidate_id"],
                "variant_id": row["variant_id"],
                "stop_reason": stop,
                "completed": row["completed"],
                "collision_observed": row["collision_observed"],
                "qp_infeasible_observed": row["qp_infeasible_observed"],
                "progress_proxy": row["progress_proxy"],
                "stalled_or_max_steps": stalled_or_max,
                "diagnosis": diagnosis,
                "notes": "Progress proxy is compact goal-distance reduction; no per-step trace is retained.",
            }
        )
    return out


def control_rows(rows: Sequence[dict[str, Any]], details: dict[tuple[str, str], dict[str, Any]]) -> list[dict[str, Any]]:
    out = []
    for row in rows:
        key = (row["candidate_id"], row["variant_name"])
        detail = details[key]
        out.append(
            {
                "candidate_id": row["candidate_id"],
                "variant_id": row["variant_id"],
                "u_nom_modified": row["u_nom_modified"],
                "u_safe_internal_modified": row["u_safe_internal_modified"],
                "wrapper_exec_command_scaled": row["wrapper_exec_command_scaled"],
                "command_modified_only_when_warning": row["command_modified_only_when_warning"],
                "max_abs_delta_u_nom": detail["max_nom_delta"],
                "max_abs_delta_u_safe_internal": detail["max_safe_delta"],
                "max_abs_delta_wrapper_exec_due_to_slowdown": detail["max_exec_delta"],
                "control_scope_passed": row["control_scope_passed"],
                "notes": "Only wrapper-level u_exec may change under a natural warning gate.",
            }
        )
    return out


def progress_rows(rows: Sequence[dict[str, Any]]) -> list[dict[str, Any]]:
    return [
        {
            "candidate_id": row["candidate_id"],
            "variant_id": row["variant_id"],
            "progress_proxy_available": row["progress_proxy"] != "NA",
            "progress_proxy_name": "goal_distance_reduction",
            "progress_proxy_value": row["progress_proxy"],
            "stop_reason": row["stop_reason"],
            "diagnosis": "compact_progress_proxy_available" if row["progress_proxy"] != "NA" else "insufficient_progress_signal",
            "notes": "Positive values indicate final state is closer to goal than initial state; this is diagnostic only.",
        }
        for row in rows
    ]


def write_notes(
    path: Path,
    rows: Sequence[dict[str, Any]],
    mixed: Sequence[dict[str, Any]],
    metrics: dict[str, Any],
) -> None:
    c004 = next(row for row in mixed if row["candidate_id"] == "C004")
    c006 = next(row for row in mixed if row["candidate_id"] == "C006")
    variant_lines = "\n".join(
        f"* {name}: warning={VARIANTS[name]['warning_scale']}, persistent={VARIANTS[name]['persistent_warning_scale']}, critical={VARIANTS[name]['critical_warning_scale']}, min={VARIANTS[name]['min_scale']}"
        for name in DEFAULT_VARIANTS
    )
    summary_lines = "\n".join(
        f"* {row['candidate_id']} / {row['variant_name']}: warnings={row['natural_warning_steps']}, stop=`{row['stop_reason']}`, progress_proxy={row['progress_proxy']}"
        for row in rows
    )
    path.write_text(
        f"""# SAFC Level-3E Robustness and Failure-Diagnosis Notes

## Scope

This is a bounded robustness and failure-diagnosis audit over the Level-3D
small targeted cohort. It is not a full benchmark and does not claim
generalized performance improvement.

## Why Level 3E Was Needed

Level 3D overall warning steps decreased, but C004 became worse, C006 was
neutral, and no run completed. Therefore robustness and failure diagnosis is
needed before any final method-validation package.

## Preregistered Variants

{variant_lines}

These variants diagnose whether slowdown scale aggressiveness changes warning
count, stop reason, or compact progress behavior.

## Mixed Outcome Diagnosis

* C004: {c004['diagnosis']}; current={c004['current_policy_warning']}, milder={c004['milder_policy_warning']}, critical-only={c004['critical_only_warning']}. Negative evidence is retained.
* C006: {c006['diagnosis']}; current={c006['current_policy_warning']}, milder={c006['milder_policy_warning']}, critical-only={c006['critical_only_warning']}.
* Positive candidates C003/C002/C001 are reported in compact tables; variant differences remain diagnostic only.

Per-run compact summaries:

{summary_lines}

## Stop Reason Diagnosis

Completed counts are current={metrics['current_policy_completed_count']},
milder={metrics['milder_policy_completed_count']}, critical-only={metrics['critical_only_completed_count']}.
The compact progress proxy is available as goal-distance reduction, but it is
not a proof of task completion or planner quality. Stop-reason effects remain
diagnostic observations.

## Claim Boundaries

* diagnostic audit only
* no full benchmark
* no statistical significance
* no generalized performance improvement
* no generalized collision reduction
* no generalized warning reduction
* no planner integration
* no real-robot validation
* no global safety guarantee
* no new CBF theorem
""",
        encoding="utf-8",
    )


def validate_args(args: argparse.Namespace) -> tuple[list[str], list[str]]:
    candidates = parse_csv_arg(args.candidates)
    variants = parse_csv_arg(args.variants)
    unknown_candidates = [item for item in candidates if item not in COHORT]
    unknown_variants = [item for item in variants if item not in VARIANTS]
    if unknown_candidates:
        raise ValueError(f"unknown candidate(s): {', '.join(unknown_candidates)}")
    if unknown_variants:
        raise ValueError(f"unknown variant(s): {', '.join(unknown_variants)}")
    if args.horizon != 3:
        raise ValueError("Level 3E requires horizon=3")
    if not 1 <= args.max_steps <= 160:
        raise ValueError("max-steps must be in [1, 160]")
    if not math.isfinite(args.dt_margin) or args.dt_margin <= 0.0:
        raise ValueError("dt-margin must be finite and positive")
    if str(args.reuse_level3d_baseline).lower() != "true":
        raise ValueError("Level 3E currently requires --reuse-level3d-baseline true")
    return candidates, variants


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="SAFC Level-3E robustness and failure-diagnosis audit."
    )
    parser.add_argument("--repo-root", type=Path, default=Path("."))
    parser.add_argument(
        "--output-dir",
        type=Path,
        default=Path("work/risk_aware_cbf/results/safc_level3e_robustness_diagnosis"),
    )
    parser.add_argument(
        "--mode",
        choices=("diagnostic-variants", "preregistration-only"),
        default="diagnostic-variants",
    )
    parser.add_argument("--candidates", default=",".join(DEFAULT_CANDIDATES))
    parser.add_argument("--variants", default=",".join(DEFAULT_VARIANTS))
    parser.add_argument("--max-steps", type=int, default=160)
    parser.add_argument("--dt-margin", type=float, default=0.0005)
    parser.add_argument("--horizon", type=int, default=3)
    parser.add_argument("--entrypoint", default="auto")
    parser.add_argument("--reuse-level3d-baseline", default="true")
    parser.add_argument("--level3d-results-dir", type=Path, default=None)
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    candidates, variants = validate_args(args)
    repo_root = args.repo_root.resolve()
    output_dir = args.output_dir.resolve()
    output_dir.mkdir(parents=True, exist_ok=True)

    level3d_baseline, level3d_comparison = load_level3d_reference(
        repo_root,
        args.level3d_results_dir,
    )
    write_readme(output_dir / "README.md")
    write_csv(
        output_dir / "diagnosis_preregistration.csv",
        PREREG_FIELDS,
        preregistration_rows(candidates, level3d_baseline, level3d_comparison),
    )
    write_csv(output_dir / "variant_config.csv", VARIANT_FIELDS, variant_rows(variants))
    if args.mode == "preregistration-only":
        return 0

    entrypoint_path = select_entrypoint(repo_root, args.entrypoint)
    if entrypoint_path is None:
        raise RuntimeError("official smoke wrapper was not found")
    entrypoint = str(entrypoint_path.relative_to(repo_root)).replace("\\", "/")
    if entrypoint != ENTRYPOINT:
        raise RuntimeError(f"Level 3E requires {ENTRYPOINT}, got {entrypoint}")

    wrapper = import_smoke_wrapper(entrypoint_path)
    torch = wrapper.torch
    device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
    _, _, cfg = candidate_start_goal(
        wrapper,
        COHORT[candidates[0]]["scene"],
        int(COHORT[candidates[0]]["trial_id"]),
    )
    gsplat = wrapper.GSplatLoader(cfg["path_to_gsplat"], device)
    dynamics = wrapper.DoubleIntegrator(device=device, ndim=3)

    rows: list[dict[str, Any]] = []
    details: dict[tuple[str, str], dict[str, Any]] = {}
    for candidate_id in candidates:
        for variant_name in variants:
            try:
                row, detail = run_variant(
                    wrapper,
                    gsplat,
                    dynamics,
                    device,
                    args,
                    candidate_id,
                    variant_name,
                )
            except Exception as exc:  # noqa: BLE001 - compact failure record
                row, detail = failed_summary(candidate_id, variant_name, exc)
            rows.append(row)
            details[(candidate_id, variant_name)] = detail

    aggregate, variant_metrics = aggregate_rows(variants, rows, details, level3d_baseline)
    mixed = mixed_diagnosis_rows(candidates, rows, level3d_baseline)
    stop_rows = stop_reason_rows(rows)
    controls = control_rows(rows, details)
    progress = progress_rows(rows)
    control_scope_all_passed = bool(controls) and all(parse_bool(row["control_scope_passed"]) for row in controls)
    all_timing_ok = bool(rows) and all(details[(row["candidate_id"], row["variant_name"])]["timing_ok"] for row in rows)
    progress_available = all(row["progress_proxy_available"] for row in progress)

    def metric_for(variant_name: str, field: str) -> int:
        return int(variant_metrics[variant_name][field])

    by_candidate_variant = {
        (row["candidate_id"], row["variant_name"]): row for row in rows
    }
    metrics = {
        "task": "SAFC Level-3E Robustness and Failure-Diagnosis Audit",
        "new_diagnostic_variant_runs": True,
        "cohort_size": len(candidates),
        "included_candidates": candidates,
        "variants": variants,
        "entrypoint": entrypoint,
        "max_steps": args.max_steps,
        "dt_margin": args.dt_margin,
        "horizon": args.horizon,
        "controller_modified": False,
        "official_core_source_modified": False,
        "cbf_splat_ellipsoids_dynamics_run_modified": False,
        "raw_traces_written": False,
        "diagnostic_runs_planned": len(candidates) * len(variants),
        "diagnostic_runs_completed": sum(parse_bool(row["run_completed"]) for row in rows),
        "control_scope_all_passed": control_scope_all_passed,
        "all_slowdown_after_or_at_warning": all_timing_ok,
        "current_policy_total_warning_steps": metric_for("current_policy", "total_warning_steps"),
        "milder_policy_total_warning_steps": metric_for("milder_slowdown", "total_warning_steps"),
        "critical_only_total_warning_steps": metric_for("critical_only_slowdown", "total_warning_steps"),
        "current_policy_completed_count": metric_for("current_policy", "completed_count"),
        "milder_policy_completed_count": metric_for("milder_slowdown", "completed_count"),
        "critical_only_completed_count": metric_for("critical_only_slowdown", "completed_count"),
        "current_policy_collision_count": metric_for("current_policy", "collision_count"),
        "milder_policy_collision_count": metric_for("milder_slowdown", "collision_count"),
        "critical_only_collision_count": metric_for("critical_only_slowdown", "collision_count"),
        "current_policy_qp_infeasible_count": metric_for("current_policy", "qp_infeasible_count"),
        "milder_policy_qp_infeasible_count": metric_for("milder_slowdown", "qp_infeasible_count"),
        "critical_only_qp_infeasible_count": metric_for("critical_only_slowdown", "qp_infeasible_count"),
        "c004_current_warning_steps": parse_int(by_candidate_variant[("C004", "current_policy")]["natural_warning_steps"]),
        "c004_milder_warning_steps": parse_int(by_candidate_variant[("C004", "milder_slowdown")]["natural_warning_steps"]),
        "c004_critical_only_warning_steps": parse_int(by_candidate_variant[("C004", "critical_only_slowdown")]["natural_warning_steps"]),
        "c006_current_warning_steps": parse_int(by_candidate_variant[("C006", "current_policy")]["natural_warning_steps"]),
        "c006_milder_warning_steps": parse_int(by_candidate_variant[("C006", "milder_slowdown")]["natural_warning_steps"]),
        "c006_critical_only_warning_steps": parse_int(by_candidate_variant[("C006", "critical_only_slowdown")]["natural_warning_steps"]),
        "progress_proxy_available": progress_available,
        "performance_improvement_claimed": False,
        "warning_reduction_claimed": False,
        "collision_reduction_claimed": False,
        "planner_improvement_claimed": False,
        "statistical_significance_claimed": False,
        "claim_level": "robustness_failure_diagnosis",
        "limitations": [
            "bounded diagnostic audit only",
            "small targeted cohort",
            "pre-registered variants",
            "not full100",
            "not flight20",
            "not a benchmark comparison",
            "no statistical significance",
            "active trajectories may diverge after slowdown",
            "does not establish generalized performance improvement",
            "does not modify CBF-QP",
            "does not modify dynamics",
            "does not validate planner integration",
            "does not validate real-robot deployment",
            "does not prove global safety",
        ],
    }

    write_csv(output_dir / "per_candidate_variant_summary.csv", SUMMARY_FIELDS, rows)
    write_csv(output_dir / "variant_aggregate_summary.csv", AGGREGATE_FIELDS, aggregate)
    write_csv(output_dir / "mixed_outcome_diagnosis.csv", MIXED_FIELDS, mixed)
    write_csv(output_dir / "stop_reason_diagnosis.csv", STOP_FIELDS, stop_rows)
    write_csv(output_dir / "control_scope_summary.csv", CONTROL_FIELDS, controls)
    write_csv(output_dir / "progress_proxy_summary.csv", PROGRESS_FIELDS, progress)
    (output_dir / "metrics.json").write_text(json.dumps(metrics, indent=2) + "\n", encoding="utf-8")
    write_notes(output_dir / "robustness_notes.md", rows, mixed, metrics)
    print(json.dumps(metrics, indent=2))

    if not control_scope_all_passed or not all_timing_ok:
        return 2
    if metrics["diagnostic_runs_completed"] != metrics["diagnostic_runs_planned"]:
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
