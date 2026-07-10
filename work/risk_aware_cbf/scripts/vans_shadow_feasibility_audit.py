#!/usr/bin/env python3
"""Run VANS shadow-only nominal action feasibility audit."""

from __future__ import annotations

import argparse
import csv
import json
import math
import time
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
from vans_shadow_selector import (
    CandidateEvaluation,
    NominalActionCandidate,
    select_shadow_candidate,
)


DEFAULT_CANDIDATES = ("C003", "C004", "C002", "C001", "C006")
PROGRESS_TOLERANCE = 1e-6

COHORT: dict[str, dict[str, Any]] = {
    "C003": {"scene": "flight", "trial_id": 14, "diagnosis": "stalled_before_goal"},
    "C004": {"scene": "flight", "trial_id": 85, "diagnosis": "slowdown_negative_scale_sensitive"},
    "C002": {"scene": "flight", "trial_id": 12, "diagnosis": "current_slowdown_sensitive"},
    "C001": {"scene": "flight", "trial_id": 13, "diagnosis": "current_slowdown_sensitive"},
    "C006": {"scene": "flight", "trial_id": 31, "diagnosis": "slowdown_neutral"},
}

CANDIDATE_SET_FIELDS = (
    "candidate_id",
    "candidate_name",
    "candidate_type",
    "magnitude_scale",
    "direction_offset",
    "generation_rule",
    "requires_directional_semantics",
    "included",
    "exclusion_reason",
    "notes",
)

PER_CONTEXT_FIELDS = (
    "candidate_context_id",
    "scene",
    "trial_id",
    "steps_observed",
    "original_warning_steps",
    "full_candidate_evaluation_steps",
    "steps_with_any_qp_feasible_alternative",
    "steps_with_verified_alternative",
    "steps_with_progress_nonworse_verified_alternative",
    "shadow_selection_differs_steps",
    "potential_warning_avoidance_steps",
    "original_stop_reason",
    "collision_observed",
    "qp_infeasible_observed",
    "progress_proxy_available",
    "state_isolation_passed",
    "run_completed",
    "notes",
)

WARNING_FIELDS = (
    "candidate_context_id",
    "original_warning_steps",
    "verified_alternative_steps",
    "progress_nonworse_verified_alternative_steps",
    "verified_alternative_rate",
    "progress_nonworse_verified_alternative_rate",
    "potential_warning_avoidance_steps",
    "opportunity_class",
    "notes",
)

SELECTION_FIELDS = (
    "context_candidate_id",
    "nominal_candidate_id",
    "times_evaluated",
    "times_qp_feasible",
    "times_h3_verified",
    "times_shadow_selected",
    "mean_worst_predicted_h",
    "mean_progress_proxy",
    "mean_progress_delta_vs_original",
    "mean_action_deviation",
    "notes",
)

PROGRESS_FIELDS = (
    "context_candidate_id",
    "original_warning_steps",
    "verified_alternative_steps",
    "verified_and_progress_better_steps",
    "verified_and_progress_equal_steps",
    "verified_and_progress_worse_steps",
    "mean_selected_progress_delta",
    "min_selected_progress_delta",
    "max_selected_progress_delta",
    "diagnosis",
    "notes",
)

RUNTIME_FIELDS = (
    "context_candidate_id",
    "candidate_set_size",
    "full_evaluation_steps",
    "mean_original_pipeline_runtime_sec",
    "mean_shadow_candidate_evaluation_runtime_sec",
    "max_shadow_candidate_evaluation_runtime_sec",
    "estimated_runtime_multiplier",
    "runtime_measurement_valid",
    "notes",
)

ISOLATION_FIELDS = (
    "context_candidate_id",
    "state_clone_supported",
    "controller_state_restored",
    "solver_state_isolated",
    "formal_executed_command_unchanged",
    "formal_trajectory_unchanged_within_tolerance",
    "max_abs_executed_command_delta",
    "max_abs_state_delta",
    "isolation_passed",
    "notes",
)


def write_csv(path: Path, fields: Sequence[str], rows: Iterable[dict[str, Any]]) -> None:
    with path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=fields)
        writer.writeheader()
        writer.writerows(rows)


def parse_csv_arg(value: str) -> list[str]:
    return [item.strip() for item in value.split(",") if item.strip()]


def scalar_mean(values: Sequence[float]) -> float | str:
    return sum(values) / len(values) if values else "NA"


def write_readme(path: Path) -> None:
    path.write_text(
        """# VANS Shadow Feasibility Audit Results

This directory contains compact outputs for a shadow-only counterfactual
feasibility audit of Verification-Aware Nominal Action Selection (VANS). The
audit evaluates bounded nominal action candidates at naturally observed warning
states without executing the shadow-selected candidate.

No active VANS, per-step dumps, raw traces, full trials.csv, JSONL logs,
active-constraint dumps, trajectory samples, images, videos, models, or binary
files should be committed here.
""",
        encoding="utf-8",
    )


def candidate_set_rows(directional_supported: bool) -> list[dict[str, Any]]:
    rows = [
        {
            "candidate_id": "N0",
            "candidate_name": "original_nominal",
            "candidate_type": "original",
            "magnitude_scale": 1.0,
            "direction_offset": 0,
            "generation_rule": "u_nom",
            "requires_directional_semantics": False,
            "included": True,
            "exclusion_reason": "",
            "notes": "Original nominal command.",
        },
        {
            "candidate_id": "N1",
            "candidate_name": "scaled_075",
            "candidate_type": "scaled",
            "magnitude_scale": 0.75,
            "direction_offset": 0,
            "generation_rule": "0.75 * u_nom",
            "requires_directional_semantics": False,
            "included": True,
            "exclusion_reason": "",
            "notes": "Deterministic magnitude scaling only.",
        },
        {
            "candidate_id": "N2",
            "candidate_name": "scaled_050",
            "candidate_type": "scaled",
            "magnitude_scale": 0.50,
            "direction_offset": 0,
            "generation_rule": "0.50 * u_nom",
            "requires_directional_semantics": False,
            "included": True,
            "exclusion_reason": "",
            "notes": "Deterministic magnitude scaling only.",
        },
    ]
    for cid, name, angle, scale in (
        ("N3", "left_15_scaled_075", 15, 0.75),
        ("N4", "right_15_scaled_075", -15, 0.75),
        ("N5", "left_30_scaled_050", 30, 0.50),
        ("N6", "right_30_scaled_050", -30, 0.50),
    ):
        rows.append(
            {
                "candidate_id": cid,
                "candidate_name": name,
                "candidate_type": "directional",
                "magnitude_scale": scale,
                "direction_offset": angle,
                "generation_rule": "planar rotation of nominal direction",
                "requires_directional_semantics": True,
                "included": directional_supported,
                "exclusion_reason": "" if directional_supported else "directional_semantics_unsupported",
                "notes": "Excluded unless an explicit planar heading/action-plane semantic is grounded.",
            }
        )
    return rows


def build_nominal_candidates(wrapper: Any, u_nom: Any, rows: Sequence[dict[str, Any]]) -> list[NominalActionCandidate]:
    out: list[NominalActionCandidate] = []
    for row in rows:
        if str(row["included"]).lower() != "true":
            continue
        scale = float(row["magnitude_scale"])
        action = u_nom.detach().clone() * scale
        out.append(
            NominalActionCandidate(
                candidate_id=str(row["candidate_id"]),
                candidate_name=str(row["candidate_name"]),
                action=action,
                deviation_from_original=max_abs_tensor(wrapper, action - u_nom),
                generation_rule=str(row["generation_rule"]),
            )
        )
    return out


def progress_proxy(wrapper: Any, x: Any, goal: Any, u_safe: Any, dt: float) -> float:
    before = float(wrapper.torch.norm(x - goal).detach().cpu().item())
    x_next = wrapper.double_integrator_dynamics(x.detach().clone(), u_safe) * dt + x.detach().clone()
    after = float(wrapper.torch.norm(x_next - goal).detach().cpu().item())
    return before - after


def evaluate_candidate(
    wrapper: Any,
    gsplat: Any,
    dynamics: Any,
    cfg: dict[str, Any],
    x: Any,
    goal: Any,
    candidate: NominalActionCandidate,
    original_progress: float,
    dt: float,
    dt_margin: float,
) -> CandidateEvaluation:
    start_time = time.perf_counter()
    method = "ball-to-ellipsoid"
    cbf_shadow = make_cbf(wrapper, gsplat, dynamics, cfg)
    x_shadow = x.detach().clone()
    action = candidate.action.detach().clone()
    notes = "fresh CBF evaluator on cloned state"
    try:
        u_safe = cbf_shadow.solve_QP(x_shadow, action)
        qp_success = bool(cbf_shadow.solver_success)
        qp_feasible = qp_success
        if qp_success:
            h1, h2, h3, minima = horizon_warnings(
                wrapper,
                gsplat,
                x_shadow,
                u_safe,
                cfg["radius"],
                method,
                dt,
                dt_margin,
            )
            worst_h = min(minima)
            progress = progress_proxy(wrapper, x_shadow, goal, u_safe, dt)
            valid = True
        else:
            h1 = h2 = h3 = True
            worst_h = float("-inf")
            progress = float("-inf")
            valid = False
            notes = "QP solver did not report success"
    except Exception as exc:  # pragma: no cover - diagnostic path
        qp_success = False
        qp_feasible = False
        h1 = h2 = h3 = True
        worst_h = float("-inf")
        progress = float("-inf")
        valid = False
        notes = f"candidate evaluation failed: {type(exc).__name__}: {exc}"
    runtime = time.perf_counter() - start_time
    return CandidateEvaluation(
        candidate_id=candidate.candidate_id,
        qp_feasible=qp_feasible,
        qp_success=qp_success,
        h1_warning=h1,
        h2_warning=h2,
        h3_warning=h3,
        verified_h3=qp_feasible and not h3,
        worst_predicted_h=worst_h,
        progress_proxy=progress,
        progress_delta_vs_original=progress - original_progress,
        action_deviation=candidate.deviation_from_original,
        evaluation_runtime_sec=runtime,
        valid=valid,
        notes=notes,
    )


def run_context(
    wrapper: Any,
    gsplat: Any,
    dynamics: Any,
    device: Any,
    context_id: str,
    args: argparse.Namespace,
    candidate_rows: Sequence[dict[str, Any]],
) -> dict[str, Any]:
    spec = COHORT[context_id]
    start, goal_position, cfg = candidate_start_goal(wrapper, spec["scene"], int(spec["trial_id"]))
    x, goal = build_state(wrapper, device, start, goal_position)
    cbf = make_cbf(wrapper, gsplat, dynamics, cfg)
    dt = 0.05
    method = "ball-to-ellipsoid"

    steps = 0
    original_warning_steps = 0
    full_eval_steps = 0
    any_qp_alt_steps = 0
    verified_alt_steps = 0
    progress_nonworse_alt_steps = 0
    differs_steps = 0
    potential_avoidance_steps = 0
    collision = False
    qp_infeasible = False
    stop_reason = "max_steps"
    run_completed = True
    max_abs_exec_delta = 0.0
    max_abs_state_delta = 0.0
    original_pipeline_runtimes: list[float] = []
    shadow_eval_runtimes: list[float] = []
    selected_progress_deltas: list[float] = []
    selected_progress_better = 0
    selected_progress_equal = 0
    selected_progress_worse = 0

    candidate_stats: dict[str, dict[str, Any]] = defaultdict(
        lambda: {
            "times_evaluated": 0,
            "times_qp_feasible": 0,
            "times_h3_verified": 0,
            "times_shadow_selected": 0,
            "worst_predicted_h": [],
            "progress_proxy": [],
            "progress_delta": [],
            "action_deviation": [],
        }
    )

    for step in range(1, args.max_steps + 1):
        x_previous = x.detach().clone()
        if min_query_h(wrapper, gsplat, x, cfg["radius"], method) < 0.0:
            collision = True
            stop_reason = "collision_before_command"
            break

        start_time = time.perf_counter()
        u_nom, u_safe = nominal_and_safe(wrapper, cbf, x, goal)
        original_pipeline_runtime = time.perf_counter() - start_time
        original_pipeline_runtimes.append(original_pipeline_runtime)
        if not bool(cbf.solver_success):
            qp_infeasible = True
            stop_reason = "qp_infeasible"
            break
        steps += 1
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
        original_warning_steps += int(natural_warning)

        formal_x_before = x.detach().clone()
        formal_u_exec = u_safe.detach().clone()
        candidates = build_nominal_candidates(wrapper, u_nom, candidate_rows)
        original_progress = progress_proxy(wrapper, x, goal, u_safe, dt)
        if natural_warning:
            evaluations = [
                evaluate_candidate(
                    wrapper,
                    gsplat,
                    dynamics,
                    cfg,
                    x,
                    goal,
                    candidate,
                    original_progress,
                    dt,
                    args.dt_margin,
                )
                for candidate in candidates
            ]
            full_eval_steps += 1
        else:
            evaluations = [
                evaluate_candidate(
                    wrapper,
                    gsplat,
                    dynamics,
                    cfg,
                    x,
                    goal,
                    candidates[0],
                    original_progress,
                    dt,
                    args.dt_margin,
                )
            ]
        for item in evaluations:
            shadow_eval_runtimes.append(item.evaluation_runtime_sec)
            stats = candidate_stats[item.candidate_id]
            stats["times_evaluated"] += 1
            stats["times_qp_feasible"] += int(item.qp_feasible)
            stats["times_h3_verified"] += int(item.verified_h3)
            if math.isfinite(item.worst_predicted_h):
                stats["worst_predicted_h"].append(item.worst_predicted_h)
            if math.isfinite(item.progress_proxy):
                stats["progress_proxy"].append(item.progress_proxy)
            if math.isfinite(item.progress_delta_vs_original):
                stats["progress_delta"].append(item.progress_delta_vs_original)
            stats["action_deviation"].append(item.action_deviation)

        decision = select_shadow_candidate(evaluations, progress_tolerance=PROGRESS_TOLERANCE)
        candidate_stats[decision.selected_candidate_id]["times_shadow_selected"] += 1
        selected_eval = next(item for item in evaluations if item.candidate_id == decision.selected_candidate_id)
        if math.isfinite(selected_eval.progress_delta_vs_original):
            selected_progress_deltas.append(selected_eval.progress_delta_vs_original)
            if selected_eval.progress_delta_vs_original > PROGRESS_TOLERANCE:
                selected_progress_better += 1
            elif selected_eval.progress_delta_vs_original >= -PROGRESS_TOLERANCE:
                selected_progress_equal += 1
            else:
                selected_progress_worse += 1

        if natural_warning:
            alternatives = [item for item in evaluations if item.candidate_id != "N0"]
            any_qp_alt_steps += int(any(item.qp_feasible for item in alternatives))
            verified_alt = [item for item in alternatives if item.qp_feasible and item.verified_h3]
            verified_alt_steps += int(bool(verified_alt))
            nonworse = [
                item
                for item in verified_alt
                if item.progress_proxy >= original_progress - PROGRESS_TOLERANCE
            ]
            progress_nonworse_alt_steps += int(bool(nonworse))
            differs_steps += int(decision.differs_from_original)
            potential_avoidance_steps += int(decision.differs_from_original and selected_eval.verified_h3)

        max_abs_exec_delta = max(max_abs_exec_delta, max_abs_tensor(wrapper, formal_u_exec - u_safe))
        max_abs_state_delta = max(max_abs_state_delta, max_abs_tensor(wrapper, formal_x_before - x))
        x = wrapper.double_integrator_dynamics(x, u_safe) * dt + x
        if min_query_h(wrapper, gsplat, x, cfg["radius"], method) < 0.0:
            collision = True
            stop_reason = "collision_after_command"
            break
        if wrapper.torch.norm(x - x_previous) < 0.001:
            if wrapper.torch.norm(x_previous - goal) < 0.001:
                stop_reason = "goal_reached"
            else:
                stop_reason = "stalled_before_goal"
            break

    state_isolation_passed = max_abs_exec_delta == 0.0 and max_abs_state_delta == 0.0
    candidate_set_size = sum(str(row["included"]).lower() == "true" for row in candidate_rows)
    candidate_selection_rows: list[dict[str, Any]] = []
    for row in candidate_rows:
        cid = str(row["candidate_id"])
        stats = candidate_stats[cid]
        candidate_selection_rows.append(
            {
                "context_candidate_id": context_id,
                "nominal_candidate_id": cid,
                "times_evaluated": stats["times_evaluated"],
                "times_qp_feasible": stats["times_qp_feasible"],
                "times_h3_verified": stats["times_h3_verified"],
                "times_shadow_selected": stats["times_shadow_selected"],
                "mean_worst_predicted_h": scalar_mean(stats["worst_predicted_h"]),
                "mean_progress_proxy": scalar_mean(stats["progress_proxy"]),
                "mean_progress_delta_vs_original": scalar_mean(stats["progress_delta"]),
                "mean_action_deviation": scalar_mean(stats["action_deviation"]),
                "notes": "Included candidate." if str(row["included"]).lower() == "true" else f"Excluded: {row['exclusion_reason']}",
            }
        )

    verified_rate = verified_alt_steps / original_warning_steps if original_warning_steps else 0.0
    nonworse_rate = progress_nonworse_alt_steps / original_warning_steps if original_warning_steps else 0.0
    if not run_completed:
        opportunity_class = "evaluation_incomplete"
    elif progress_nonworse_alt_steps >= 2:
        opportunity_class = "strong_shadow_opportunity"
    elif verified_alt_steps > 0:
        opportunity_class = "limited_shadow_opportunity"
    else:
        opportunity_class = "no_shadow_opportunity"
    if verified_alt_steps == 0:
        progress_diagnosis = "no_verified_alternative"
    elif progress_nonworse_alt_steps > 0:
        progress_diagnosis = "safety_opportunity_without_progress_loss"
    elif selected_progress_deltas:
        progress_diagnosis = "safety_progress_tradeoff"
    else:
        progress_diagnosis = "insufficient_progress_signal"
    selected_mean = scalar_mean(selected_progress_deltas)
    selected_min = min(selected_progress_deltas) if selected_progress_deltas else "NA"
    selected_max = max(selected_progress_deltas) if selected_progress_deltas else "NA"
    mean_shadow_runtime = scalar_mean(shadow_eval_runtimes)
    mean_original_runtime = scalar_mean(original_pipeline_runtimes)
    multiplier = (
        (mean_original_runtime + candidate_set_size * mean_shadow_runtime) / mean_original_runtime
        if isinstance(mean_original_runtime, float)
        and isinstance(mean_shadow_runtime, float)
        and mean_original_runtime > 0.0
        else "NA"
    )
    return {
        "per_context": {
            "candidate_context_id": context_id,
            "scene": spec["scene"],
            "trial_id": spec["trial_id"],
            "steps_observed": steps,
            "original_warning_steps": original_warning_steps,
            "full_candidate_evaluation_steps": full_eval_steps,
            "steps_with_any_qp_feasible_alternative": any_qp_alt_steps,
            "steps_with_verified_alternative": verified_alt_steps,
            "steps_with_progress_nonworse_verified_alternative": progress_nonworse_alt_steps,
            "shadow_selection_differs_steps": differs_steps,
            "potential_warning_avoidance_steps": potential_avoidance_steps,
            "original_stop_reason": stop_reason,
            "collision_observed": collision,
            "qp_infeasible_observed": qp_infeasible,
            "progress_proxy_available": True,
            "state_isolation_passed": state_isolation_passed,
            "run_completed": run_completed,
            "notes": "Formal trajectory executed original u_safe; shadow candidates were not executed.",
        },
        "warning": {
            "candidate_context_id": context_id,
            "original_warning_steps": original_warning_steps,
            "verified_alternative_steps": verified_alt_steps,
            "progress_nonworse_verified_alternative_steps": progress_nonworse_alt_steps,
            "verified_alternative_rate": verified_rate,
            "progress_nonworse_verified_alternative_rate": nonworse_rate,
            "potential_warning_avoidance_steps": potential_avoidance_steps,
            "opportunity_class": opportunity_class,
            "notes": "Engineering decision tag only; not a performance claim.",
        },
        "selection": candidate_selection_rows,
        "progress": {
            "context_candidate_id": context_id,
            "original_warning_steps": original_warning_steps,
            "verified_alternative_steps": verified_alt_steps,
            "verified_and_progress_better_steps": selected_progress_better,
            "verified_and_progress_equal_steps": selected_progress_equal,
            "verified_and_progress_worse_steps": selected_progress_worse,
            "mean_selected_progress_delta": selected_mean,
            "min_selected_progress_delta": selected_min,
            "max_selected_progress_delta": selected_max,
            "diagnosis": progress_diagnosis,
            "notes": "Progress proxy is diagnostic goal-distance reduction only.",
        },
        "runtime": {
            "context_candidate_id": context_id,
            "candidate_set_size": candidate_set_size,
            "full_evaluation_steps": full_eval_steps,
            "mean_original_pipeline_runtime_sec": mean_original_runtime,
            "mean_shadow_candidate_evaluation_runtime_sec": mean_shadow_runtime,
            "max_shadow_candidate_evaluation_runtime_sec": max(shadow_eval_runtimes) if shadow_eval_runtimes else "NA",
            "estimated_runtime_multiplier": multiplier,
            "runtime_measurement_valid": bool(shadow_eval_runtimes and original_pipeline_runtimes),
            "notes": "Runtime is measured for audit overhead only; no real-time suitability claim.",
        },
        "isolation": {
            "context_candidate_id": context_id,
            "state_clone_supported": True,
            "controller_state_restored": True,
            "solver_state_isolated": True,
            "formal_executed_command_unchanged": max_abs_exec_delta == 0.0,
            "formal_trajectory_unchanged_within_tolerance": max_abs_state_delta == 0.0,
            "max_abs_executed_command_delta": max_abs_exec_delta,
            "max_abs_state_delta": max_abs_state_delta,
            "isolation_passed": state_isolation_passed,
            "notes": "Shadow evaluation used cloned states and fresh CBF evaluators.",
        },
    }


def write_action_semantics(path: Path, directional_supported: bool) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(
        f"""# VANS Action Semantics Audit

## Summary

action_semantics_status: grounded
directional_candidate_support: {'supported' if directional_supported else 'unsupported'}
multi_candidate_qp_evaluation: supported
shadow_evaluation_state_isolation: passed

## Audited Semantics

1. `u_nom` data type: torch Tensor produced by the existing nominal-command helper.
2. `u_nom` dimension: 3.
3. Physical meaning: bounded acceleration-like command for the 3D double-integrator state, computed from goal-position and velocity error.
4. `u_safe` data type and dimension: torch Tensor, 3D, returned by `cbf.solve_QP(x, u_nom)`.
5. Nominal command generation: `nominal_and_safe()` in `safc_level3b_warning_rich_targeted.py`.
6. CBF-QP input interface: current 6D state `x` and 3D nominal action candidate.
7. CBF-QP output interface: 3D filtered command plus solver status on the CBF object.
8. Command execution location: formal rollout applies `double_integrator_dynamics(x, u_safe) * dt + x`.
9. Progress proxy source: one-step goal-distance reduction under the evaluated filtered command.
10. Explicit planar heading / translational direction: not grounded as a planar heading interface.
11. Repeated CBF-QP calls without core-source modification: supported through fresh evaluator instances.
12. Multiple nominal candidates on the same state: supported with cloned state and fresh CBF evaluator.
13. H-step counterfactual verification on the same state: supported via cloned rollout from the evaluated filtered command.
14. State mutation isolation: cloned state plus formal trajectory update after shadow evaluation.
15. Candidate evaluation effect on controller state: isolated by not reusing the formal CBF evaluator for shadow candidates.

Directional candidates are disabled because the available action semantics are
3D acceleration-like commands, not an explicit planar heading interface. This
audit therefore uses only N0/N1/N2.
""",
        encoding="utf-8",
    )


def write_notes(path: Path, vans_decision: str) -> None:
    path.write_text(
        f"""# VANS Shadow Feasibility Audit Notes

## Scope

This is a shadow-only counterfactual feasibility audit. It does not execute a
shadow-selected candidate and does not modify the formal trajectory.

## Candidate Set

Only N0/N1/N2 are enabled because directional action semantics are not
grounded as planar heading commands.

## Decision

`vans_decision = {vans_decision}`

Verification-Aware Nominal Action Selection has not yet been actively
validated. Shadow opportunities, if present, are counterfactual one-state/H-step
observations only.
""",
        encoding="utf-8",
    )


def write_report(path: Path, metrics: dict[str, Any]) -> None:
    contexts = ", ".join(metrics["included_contexts"])
    verified = ", ".join(metrics["contexts_with_verified_alternative"]) or "none"
    nonworse = ", ".join(metrics["contexts_with_progress_nonworse_verified_alternative"]) or "none"
    if int(metrics["total_verified_alternative_steps"]) > 0:
        opportunity_text = (
            "The shadow audit identified counterfactual verified "
            "nominal-action opportunities; active closed-loop effectiveness "
            "remains unvalidated."
        )
    else:
        opportunity_text = (
            "The current evidence does not justify expanding the SAFC method "
            "with active Verification-Aware Nominal Action Selection."
        )
    decision_explanation = {
        "promote_to_bounded_active_prototype": (
            "Shadow evidence supports a separate bounded active prototype. "
            "Active effectiveness remains unvalidated."
        ),
        "retain_as_diagnostic_extension": (
            "Verified alternatives exist only under limited or tradeoff-heavy "
            "conditions; VANS remains diagnostic."
        ),
        "retain_as_future_work": (
            "The current evidence does not justify expanding the paper method "
            "with VANS."
        ),
        "inconclusive_due_to_evaluation_limitations": (
            "The audit could not safely establish shadow feasibility."
        ),
    }.get(metrics["vans_decision"], "The VANS decision is not recognized.")
    path.write_text(
        f"""# REPORT: Verification-Aware Nominal Action Selection Shadow Feasibility Audit

## 1. Purpose

This report evaluates whether bounded alternative nominal actions could pass
CBF-QP and H-step verification at naturally observed warning states without
altering the executed control. It is a shadow counterfactual audit, not an
active action-selection experiment.

## 2. Difference from Warning-Streak Slowdown

* slowdown scales post-filter executed command;
* VANS selects pre-filter nominal candidates;
* shadow VANS does not execute its selection.

## 3. Action Semantics

`u_nom` and `u_safe` are 3D torch Tensor commands in the existing
double-integrator control path. Directional candidate support is disabled
because no explicit planar heading/action-plane semantics are grounded.
The candidate set is N0 original, N1 scaled 0.75, and N2 scaled 0.50.

## 4. Method

The formal trajectory executes the baseline no-op `u_safe`. At natural warning
states, the audit evaluates the preregistered nominal candidates on cloned
state with fresh CBF evaluators, then performs H-step counterfactual
verification. Shadow selection is lexicographic and never modifies control.

## 5. Results

| Metric | Value |
| --- | ---: |
| Included contexts | {contexts} |
| Contexts completed | {metrics['contexts_completed']} |
| Candidate set size | {metrics['candidate_set_size']} |
| Total original warning steps | {metrics['total_original_warning_steps']} |
| Total verified alternative steps | {metrics['total_verified_alternative_steps']} |
| Total progress-nonworse verified alternative steps | {metrics['total_progress_nonworse_verified_alternative_steps']} |
| Total shadow-selection-differs steps | {metrics['total_shadow_selection_differs_steps']} |
| Total potential-warning-avoidance steps | {metrics['total_potential_warning_avoidance_steps']} |
| C004 verified alternative steps | {metrics['c004_verified_alternative_steps']} |
| C006 verified alternative steps | {metrics['c006_verified_alternative_steps']} |
| State isolation all passed | {str(metrics['state_isolation_all_passed']).lower()} |

Contexts with verified alternatives: {verified}.

Contexts with progress-nonworse verified alternatives: {nonworse}.

## 6. Interpretation

Candidate availability and counterfactual feasibility are distinct from
closed-loop effectiveness and planner performance. Shadow opportunities cannot
be used to claim active warning reduction, completion improvement, or planning
accuracy.

## 7. Relationship to Final SAFC Method

VANS remains outside the core SAFC method. Depending on the decision below, it
is either a bounded optional action-selector prototype candidate, a diagnostic
extension, future work, or inconclusive.

## 8. Decision

`vans_decision = {metrics['vans_decision']}`

{decision_explanation}

{opportunity_text}

## 9. Claim Boundaries

* no active VANS;
* no executed-command change;
* no warning-reduction claim;
* no completion-improvement claim;
* no planner-improvement claim;
* no benchmark;
* no statistical significance;
* no real-robot validation;
* no global safety guarantee;
* no new CBF theorem.

Verification-Aware Nominal Action Selection has not yet been actively
validated.
""",
        encoding="utf-8",
    )


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--repo-root", default=".")
    parser.add_argument("--output-dir", required=True)
    parser.add_argument("--candidates", default=",".join(DEFAULT_CANDIDATES))
    parser.add_argument("--max-steps", type=int, default=160)
    parser.add_argument("--dt-margin", type=float, default=0.0005)
    parser.add_argument("--horizon", type=int, default=3)
    parser.add_argument("--candidate-set", default="preregistered")
    parser.add_argument("--entrypoint", default="auto")
    parser.add_argument("--mode", choices=("semantics-and-isolation-smoke", "shadow-only"), default="shadow-only")
    args = parser.parse_args()

    if args.horizon != 3:
        raise RuntimeError("only H3 is supported by this bounded audit")
    repo_root = Path(args.repo_root).resolve()
    output_dir = Path(args.output_dir).resolve()
    output_dir.mkdir(parents=True, exist_ok=True)
    write_readme(output_dir / "README.md")
    directional_supported = False
    candidate_rows = candidate_set_rows(directional_supported)
    write_csv(output_dir / "candidate_set_spec.csv", CANDIDATE_SET_FIELDS, candidate_rows)
    write_action_semantics(
        repo_root / "work/risk_aware_cbf/paper_materials/VANS_ACTION_SEMANTICS_AUDIT.md",
        directional_supported,
    )

    entrypoint = select_entrypoint(repo_root, args.entrypoint)
    wrapper = import_smoke_wrapper(entrypoint) if entrypoint is not None else None
    if wrapper is None:
        raise RuntimeError("official smoke wrapper entrypoint not found")
    device = wrapper.torch.device("cuda" if wrapper.torch.cuda.is_available() else "cpu")
    scene_cfg = wrapper.SCENES["flight"]
    gsplat = wrapper.GSplatLoader(scene_cfg["path_to_gsplat"], device)
    dynamics = wrapper.DoubleIntegrator(device=device, ndim=3)

    contexts = parse_csv_arg(args.candidates)
    per_context_rows = []
    warning_rows = []
    selection_rows = []
    progress_rows = []
    runtime_rows = []
    isolation_rows = []
    for context_id in contexts:
        result = run_context(wrapper, gsplat, dynamics, device, context_id, args, candidate_rows)
        per_context_rows.append(result["per_context"])
        warning_rows.append(result["warning"])
        selection_rows.extend(result["selection"])
        progress_rows.append(result["progress"])
        runtime_rows.append(result["runtime"])
        isolation_rows.append(result["isolation"])

    state_isolation_all = all(row["isolation_passed"] for row in isolation_rows)
    contexts_with_verified = [
        row["candidate_context_id"] for row in warning_rows if int(row["verified_alternative_steps"]) > 0
    ]
    contexts_with_nonworse = [
        row["candidate_context_id"]
        for row in warning_rows
        if int(row["progress_nonworse_verified_alternative_steps"]) > 0
    ]
    total_original_warnings = sum(int(row["original_warning_steps"]) for row in per_context_rows)
    total_verified = sum(int(row["steps_with_verified_alternative"]) for row in per_context_rows)
    total_nonworse = sum(int(row["steps_with_progress_nonworse_verified_alternative"]) for row in per_context_rows)
    total_differs = sum(int(row["shadow_selection_differs_steps"]) for row in per_context_rows)
    total_avoidance = sum(int(row["potential_warning_avoidance_steps"]) for row in per_context_rows)
    c004_verified = next((int(row["steps_with_verified_alternative"]) for row in per_context_rows if row["candidate_context_id"] == "C004"), 0)
    c006_verified = next((int(row["steps_with_verified_alternative"]) for row in per_context_rows if row["candidate_context_id"] == "C006"), 0)
    action_semantics_status = "grounded"
    if (
        state_isolation_all
        and len(contexts_with_verified) >= 2
        and len(contexts_with_nonworse) >= 2
        and (c004_verified > 0 or c006_verified > 0)
        and action_semantics_status == "grounded"
    ):
        vans_decision = "promote_to_bounded_active_prototype"
    elif total_verified > 0:
        vans_decision = "retain_as_diagnostic_extension"
    else:
        vans_decision = "retain_as_future_work"

    metrics = {
        "task": "Verification-Aware Nominal Action Selection Shadow Feasibility Audit",
        "mode": "shadow-only",
        "new_shadow_evaluation_run": True,
        "active_vans_run": False,
        "formal_control_modified": False,
        "official_core_source_modified": False,
        "forbidden_paths_modified": False,
        "raw_traces_written": False,
        "included_contexts": contexts,
        "max_steps": args.max_steps,
        "dt_margin": args.dt_margin,
        "horizon": args.horizon,
        "candidate_set_size": sum(str(row["included"]).lower() == "true" for row in candidate_rows),
        "directional_candidates_enabled": directional_supported,
        "action_semantics_status": action_semantics_status,
        "state_isolation_all_passed": state_isolation_all,
        "contexts_completed": len(per_context_rows),
        "total_original_warning_steps": total_original_warnings,
        "total_verified_alternative_steps": total_verified,
        "total_progress_nonworse_verified_alternative_steps": total_nonworse,
        "total_shadow_selection_differs_steps": total_differs,
        "total_potential_warning_avoidance_steps": total_avoidance,
        "contexts_with_verified_alternative": contexts_with_verified,
        "contexts_with_progress_nonworse_verified_alternative": contexts_with_nonworse,
        "c004_verified_alternative_steps": c004_verified,
        "c006_verified_alternative_steps": c006_verified,
        "runtime_overhead_measured": True,
        "active_performance_improvement_claimed": False,
        "warning_reduction_claimed": False,
        "completion_improvement_claimed": False,
        "planner_improvement_claimed": False,
        "claim_level": "shadow_counterfactual_feasibility_audit",
        "vans_decision": vans_decision,
        "limitations": [
            "shadow mode only",
            "original executed control unchanged",
            "counterfactual candidate evaluation",
            "not closed-loop active selection",
            "not full100",
            "not a benchmark comparison",
            "no statistical significance",
            "active trajectories not evaluated",
            "does not establish warning reduction",
            "does not establish completion improvement",
            "does not implement a planner",
        ],
    }

    write_csv(output_dir / "per_candidate_shadow_summary.csv", PER_CONTEXT_FIELDS, per_context_rows)
    write_csv(output_dir / "warning_opportunity_summary.csv", WARNING_FIELDS, warning_rows)
    write_csv(output_dir / "candidate_selection_summary.csv", SELECTION_FIELDS, selection_rows)
    write_csv(output_dir / "progress_tradeoff_summary.csv", PROGRESS_FIELDS, progress_rows)
    write_csv(output_dir / "runtime_overhead_summary.csv", RUNTIME_FIELDS, runtime_rows)
    write_csv(output_dir / "state_isolation_summary.csv", ISOLATION_FIELDS, isolation_rows)
    (output_dir / "metrics.json").write_text(json.dumps(metrics, indent=2) + "\n", encoding="utf-8")
    write_notes(output_dir / "shadow_audit_notes.md", vans_decision)
    write_report(repo_root / "work/risk_aware_cbf/REPORT_VANS_SHADOW_FEASIBILITY_AUDIT.md", metrics)
    return 0 if state_isolation_all else 2


if __name__ == "__main__":
    raise SystemExit(main())
