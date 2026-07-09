#!/usr/bin/env python3
"""Run SAFC Level-3D small targeted cohort paired A/B validation."""

from __future__ import annotations

import argparse
import csv
import json
import math
from collections import Counter, defaultdict
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
INCLUDED_CANDIDATES = {"C001", "C002", "C003", "C004", "C006"}

COHORT: dict[str, dict[str, Any]] = {
    "C001": {
        "candidate_id": "C001",
        "scene": "flight",
        "trial_id": 13,
        "source_level": "Level-3B-R default-context warning reproduction",
        "source_first_warning_step": 114,
        "included": True,
        "exclusion_reason": "",
        "notes": "Included default-context warning-rich candidate.",
    },
    "C002": {
        "candidate_id": "C002",
        "scene": "flight",
        "trial_id": 12,
        "source_level": "Level-3B-R default-context warning reproduction",
        "source_first_warning_step": 102,
        "included": True,
        "exclusion_reason": "",
        "notes": "Included default-context warning-rich candidate.",
    },
    "C003": {
        "candidate_id": "C003",
        "scene": "flight",
        "trial_id": 14,
        "source_level": "Level-3B-R default-context warning reproduction",
        "source_first_warning_step": 60,
        "included": True,
        "exclusion_reason": "",
        "notes": "Included default-context warning-rich candidate; Level 3C fixed A/B already completed.",
    },
    "C004": {
        "candidate_id": "C004",
        "scene": "flight",
        "trial_id": 85,
        "source_level": "Level-3B-R default-context warning reproduction",
        "source_first_warning_step": 71,
        "included": True,
        "exclusion_reason": "",
        "notes": "Included default-context warning-rich candidate.",
    },
    "C005": {
        "candidate_id": "C005",
        "scene": "flight",
        "trial_id": 37,
        "source_level": "Level-3B-R sensitivity setting only",
        "source_first_warning_step": "",
        "included": False,
        "exclusion_reason": "sensitivity_only_warning",
        "notes": "Excluded because warning appeared only in a sensitivity setting.",
    },
    "C006": {
        "candidate_id": "C006",
        "scene": "flight",
        "trial_id": 31,
        "source_level": "Level-3B-R default-context warning reproduction",
        "source_first_warning_step": 120,
        "included": True,
        "exclusion_reason": "",
        "notes": "Included default-context warning-rich candidate.",
    },
    "C007": {
        "candidate_id": "C007",
        "scene": "flight",
        "trial_id": 57,
        "source_level": "Level-3B-R diagnostic context",
        "source_first_warning_step": "",
        "included": False,
        "exclusion_reason": "initial_collision_diagnostic_context",
        "notes": "Excluded because it is an initial-collision diagnostic context.",
    },
}

PREREG_FIELDS = (
    "candidate_id",
    "scene",
    "trial_id",
    "source_level",
    "source_first_warning_step",
    "included",
    "exclusion_reason",
    "dt_margin",
    "horizon",
    "max_steps",
    "planned_baseline_runs",
    "planned_active_runs",
    "notes",
)

BASELINE_FIELDS = (
    "candidate_id",
    "scene",
    "trial_id",
    "steps_observed",
    "natural_warning_steps",
    "first_natural_warning_step",
    "h1_warning_steps",
    "h2_warning_steps",
    "h3_warning_steps",
    "collision_observed",
    "qp_infeasible_observed",
    "recovery_used_observed",
    "completed",
    "stop_reason",
    "u_nom_modified",
    "u_safe_internal_modified",
    "control_modified",
    "run_completed",
    "notes",
)

ACTIVE_FIELDS = (
    "candidate_id",
    "scene",
    "trial_id",
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
    "recovery_used_observed",
    "completed",
    "stop_reason",
    "u_nom_modified",
    "u_safe_internal_modified",
    "wrapper_exec_command_scaled",
    "run_completed",
    "notes",
)

COMPARISON_FIELDS = (
    "candidate_id",
    "baseline_steps_observed",
    "active_steps_observed",
    "baseline_warning_steps",
    "active_warning_steps",
    "delta_warning_steps_active_minus_baseline",
    "baseline_first_warning_step",
    "active_first_warning_step",
    "slowdown_active_steps",
    "first_slowdown_step",
    "slowdown_after_or_at_warning",
    "baseline_collision_observed",
    "active_collision_observed",
    "baseline_qp_infeasible_observed",
    "active_qp_infeasible_observed",
    "baseline_completed",
    "active_completed",
    "baseline_stop_reason",
    "active_stop_reason",
    "targeted_behavior_observation",
    "performance_claim_allowed",
    "notes",
)

AGGREGATE_FIELDS = ("metric", "value", "notes")

TIMING_FIELDS = (
    "candidate_id",
    "baseline_first_warning_step",
    "active_first_warning_step",
    "first_slowdown_step",
    "slowdown_after_or_at_warning",
    "baseline_warning_steps",
    "active_warning_steps",
    "slowdown_active_steps",
    "release_observed",
    "notes",
)

CONTROL_FIELDS = (
    "candidate_id",
    "baseline_u_nom_modified",
    "baseline_u_safe_internal_modified",
    "baseline_control_modified",
    "active_u_nom_modified",
    "active_u_safe_internal_modified",
    "active_wrapper_exec_command_scaled",
    "active_command_modified_only_when_warning",
    "max_abs_delta_u_nom",
    "max_abs_delta_u_safe_internal",
    "max_abs_delta_wrapper_exec_due_to_slowdown",
    "control_scope_passed",
    "notes",
)

STOP_FIELDS = ("mode", "stop_reason", "count", "candidate_ids", "notes")


def write_csv(
    path: Path,
    fields: Sequence[str],
    rows: Iterable[dict[str, Any]],
) -> None:
    with path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=fields)
        writer.writeheader()
        writer.writerows(rows)


def load_csv(path: Path) -> list[dict[str, str]]:
    if not path.is_file():
        raise RuntimeError(f"required compact CSV not found: {path}")
    with path.open("r", encoding="utf-8", newline="") as handle:
        return list(csv.DictReader(handle))


def parse_bool(value: Any) -> bool:
    if isinstance(value, bool):
        return value
    return str(value).strip().lower() in {"true", "1", "yes"}


def maybe_int(value: Any) -> int | None:
    text = str(value).strip()
    if not text:
        return None
    return int(text)


def int_value(row: dict[str, Any], field: str) -> int:
    text = str(row.get(field, "")).strip()
    return int(text) if text else 0


def float_value(row: dict[str, Any], field: str) -> float:
    text = str(row.get(field, "")).strip()
    return float(text) if text else 0.0


def parse_candidates(value: str) -> list[str]:
    candidates = [item.strip() for item in value.split(",") if item.strip()]
    if not candidates:
        raise ValueError("at least one candidate is required")
    unknown = [item for item in candidates if item not in COHORT]
    if unknown:
        raise ValueError(f"unknown candidate(s): {', '.join(unknown)}")
    excluded = [
        item
        for item in candidates
        if item not in INCLUDED_CANDIDATES
    ]
    if excluded:
        raise ValueError(
            "execution is restricted to included candidates only: "
            + ", ".join(excluded)
        )
    return candidates


def preregistration_rows(args: argparse.Namespace) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    for candidate_id in ("C001", "C002", "C003", "C004", "C005", "C006", "C007"):
        candidate = COHORT[candidate_id]
        included = bool(candidate["included"])
        rows.append(
            {
                "candidate_id": candidate_id,
                "scene": candidate["scene"],
                "trial_id": candidate["trial_id"],
                "source_level": candidate["source_level"],
                "source_first_warning_step": candidate[
                    "source_first_warning_step"
                ],
                "included": included,
                "exclusion_reason": candidate["exclusion_reason"],
                "dt_margin": args.dt_margin,
                "horizon": args.horizon,
                "max_steps": args.max_steps,
                "planned_baseline_runs": int(included),
                "planned_active_runs": int(included),
                "notes": candidate["notes"],
            }
        )
    return rows


def write_readme(path: Path) -> None:
    path.write_text(
        """# SAFC Level-3D Small Targeted Cohort Results

This directory contains compact outputs for a pre-registered small targeted
cohort A/B comparison. It compares no-op execution and warning-streak slowdown
on five warning-rich candidates reproduced in Level 3B-R. This is not a full
benchmark and does not claim generalized performance improvement.

Outputs:

* `cohort_preregistration.csv`
* `per_candidate_baseline_summary.csv`
* `per_candidate_active_summary.csv`
* `per_candidate_ab_comparison.csv`
* `cohort_aggregate_summary.csv`
* `warning_timing_summary.csv`
* `control_scope_summary.csv`
* `stop_reason_summary.csv`
* `metrics.json`
* `cohort_notes.md`

No raw traces, full trial dumps, per-step dumps, active-constraint dumps,
trajectory samples, JSONL logs, images, or binary files should be committed
here.
""",
        encoding="utf-8",
    )


def run_rollout(
    wrapper: Any,
    gsplat: Any,
    dynamics: Any,
    device: Any,
    args: argparse.Namespace,
    candidate: dict[str, Any],
    active: bool,
    policy_config: SlowdownPolicyConfig,
) -> tuple[dict[str, Any], dict[str, Any]]:
    scene = str(candidate["scene"])
    trial_id = int(candidate["trial_id"])
    start, goal_position, cfg = candidate_start_goal(
        wrapper, scene, trial_id
    )
    x, goal = build_state(wrapper, device, start, goal_position)
    cbf = make_cbf(wrapper, gsplat, dynamics, cfg)
    dt = 0.05
    method = "ball-to-ellipsoid"
    warning_streak = 0
    clear_streak = 0
    previous_scale = 1.0
    steps = 0
    warning_steps = 0
    h1_steps = 0
    h2_steps = 0
    h3_steps = 0
    slowdown_steps = 0
    first_warning: int | None = None
    first_slowdown: int | None = None
    active_scales: list[float] = []
    max_nom_delta = 0.0
    max_safe_delta = 0.0
    max_exec_delta = 0.0
    modified_only_when_warning = True
    collision = False
    qp_infeasible = False
    completed = False
    stop_reason = "max_steps"
    release_observed = False

    for step in range(1, args.max_steps + 1):
        x_previous = x.detach().clone()
        current_h = min_query_h(
            wrapper, gsplat, x, cfg["radius"], method
        )
        if current_h < 0.0:
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
        warning_steps += int(natural_warning)
        h1_steps += int(h1)
        h2_steps += int(h2)
        h3_steps += int(h3)
        if natural_warning and first_warning is None:
            first_warning = step

        applied_scale = 1.0
        if active:
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
                policy_config,
            )
            if not decision.bounded:
                raise RuntimeError(
                    f"{candidate['candidate_id']} slowdown policy returned an unbounded scale"
                )
            applied_scale = decision.scale if natural_warning else 1.0
            previous_scale = decision.scale

        slowdown_active = active and natural_warning and applied_scale < 1.0
        u_exec = (
            apply_scale_to_vector(u_safe, applied_scale)
            if slowdown_active
            else u_safe.detach().clone()
        )

        nom_delta = max_abs_tensor(wrapper, u_nom - u_nom_before)
        safe_delta = max_abs_tensor(wrapper, u_safe - u_safe_before)
        exec_delta = max_abs_tensor(
            wrapper, u_exec - u_exec_original
        )
        max_nom_delta = max(max_nom_delta, nom_delta)
        max_safe_delta = max(max_safe_delta, safe_delta)
        max_exec_delta = max(max_exec_delta, exec_delta)
        if exec_delta > 1e-12 and not natural_warning:
            modified_only_when_warning = False
        if slowdown_active:
            slowdown_steps += 1
            active_scales.append(float(applied_scale))
            if first_slowdown is None:
                first_slowdown = step
        elif active and slowdown_steps > 0 and not natural_warning:
            release_observed = True

        x = wrapper.double_integrator_dynamics(x, u_exec) * dt + x
        if min_query_h(
            wrapper, gsplat, x, cfg["radius"], method
        ) < 0.0:
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

    common = {
        "candidate_id": candidate["candidate_id"],
        "scene": scene,
        "trial_id": trial_id,
        "steps_observed": steps,
        "natural_warning_steps": warning_steps,
        "first_natural_warning_step": (
            first_warning if first_warning is not None else ""
        ),
        "h1_warning_steps": h1_steps,
        "h2_warning_steps": h2_steps,
        "h3_warning_steps": h3_steps,
        "collision_observed": collision,
        "qp_infeasible_observed": qp_infeasible,
        "recovery_used_observed": False,
        "completed": completed,
        "stop_reason": stop_reason,
        "u_nom_modified": max_nom_delta != 0.0,
        "u_safe_internal_modified": max_safe_delta != 0.0,
    }
    details = {
        "slowdown_active_steps": slowdown_steps,
        "first_slowdown_step": first_slowdown,
        "min_scale_applied": (
            min(active_scales) if active_scales else 1.0
        ),
        "max_scale_applied": (
            max(active_scales) if active_scales else 1.0
        ),
        "max_nom_delta": max_nom_delta,
        "max_safe_delta": max_safe_delta,
        "max_exec_delta": max_exec_delta,
        "modified_only_when_warning": modified_only_when_warning,
        "release_observed": release_observed,
    }
    return common, details


def baseline_row(
    common: dict[str, Any],
    details: dict[str, Any],
) -> dict[str, Any]:
    return {
        **common,
        "control_modified": details["max_exec_delta"] != 0.0,
        "run_completed": True,
        "notes": (
            "Original u_safe executed unchanged; no slowdown, recovery, "
            "or planner. Compact candidate summary only."
        ),
    }


def active_row(
    common: dict[str, Any],
    details: dict[str, Any],
) -> dict[str, Any]:
    activation = details["slowdown_active_steps"] > 0
    return {
        "candidate_id": common["candidate_id"],
        "scene": common["scene"],
        "trial_id": common["trial_id"],
        "steps_observed": common["steps_observed"],
        "natural_warning_steps": common["natural_warning_steps"],
        "first_natural_warning_step": common[
            "first_natural_warning_step"
        ],
        "h1_warning_steps": common["h1_warning_steps"],
        "h2_warning_steps": common["h2_warning_steps"],
        "h3_warning_steps": common["h3_warning_steps"],
        "slowdown_active_steps": details["slowdown_active_steps"],
        "first_slowdown_step": (
            details["first_slowdown_step"]
            if details["first_slowdown_step"] is not None
            else ""
        ),
        "min_scale_applied": details["min_scale_applied"],
        "max_scale_applied": details["max_scale_applied"],
        "max_control_delta_from_slowdown": details["max_exec_delta"],
        "command_modified_only_when_warning": details[
            "modified_only_when_warning"
        ],
        "collision_observed": common["collision_observed"],
        "qp_infeasible_observed": common["qp_infeasible_observed"],
        "recovery_used_observed": common["recovery_used_observed"],
        "completed": common["completed"],
        "stop_reason": common["stop_reason"],
        "u_nom_modified": common["u_nom_modified"],
        "u_safe_internal_modified": common[
            "u_safe_internal_modified"
        ],
        "wrapper_exec_command_scaled": activation,
        "run_completed": True,
        "notes": (
            "Scale range covers warning-gated active steps only. No "
            "recovery, planner, CBF-QP, dynamics, or GSplat query changes."
        ),
    }


def failed_baseline_row(
    candidate: dict[str, Any],
    error: BaseException,
) -> tuple[dict[str, Any], dict[str, Any]]:
    row = {
        "candidate_id": candidate["candidate_id"],
        "scene": candidate["scene"],
        "trial_id": candidate["trial_id"],
        "steps_observed": 0,
        "natural_warning_steps": 0,
        "first_natural_warning_step": "",
        "h1_warning_steps": 0,
        "h2_warning_steps": 0,
        "h3_warning_steps": 0,
        "collision_observed": False,
        "qp_infeasible_observed": False,
        "recovery_used_observed": False,
        "completed": False,
        "stop_reason": "run_failed",
        "u_nom_modified": False,
        "u_safe_internal_modified": False,
        "control_modified": False,
        "run_completed": False,
        "notes": f"Baseline run failed: {type(error).__name__}: {error}",
    }
    details = {
        "max_nom_delta": 0.0,
        "max_safe_delta": 0.0,
        "max_exec_delta": 0.0,
        "release_observed": False,
    }
    return row, details


def failed_active_row(
    candidate: dict[str, Any],
    error: BaseException,
) -> tuple[dict[str, Any], dict[str, Any]]:
    row = {
        "candidate_id": candidate["candidate_id"],
        "scene": candidate["scene"],
        "trial_id": candidate["trial_id"],
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
        "recovery_used_observed": False,
        "completed": False,
        "stop_reason": "run_failed",
        "u_nom_modified": False,
        "u_safe_internal_modified": False,
        "wrapper_exec_command_scaled": False,
        "run_completed": False,
        "notes": f"Active run failed: {type(error).__name__}: {error}",
    }
    details = {
        "max_nom_delta": 0.0,
        "max_safe_delta": 0.0,
        "max_exec_delta": 0.0,
        "release_observed": False,
    }
    return row, details


def not_run_active_row(
    candidate: dict[str, Any],
    note: str,
) -> tuple[dict[str, Any], dict[str, Any]]:
    row = {
        "candidate_id": candidate["candidate_id"],
        "scene": candidate["scene"],
        "trial_id": candidate["trial_id"],
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
        "recovery_used_observed": False,
        "completed": False,
        "stop_reason": "not_run",
        "u_nom_modified": False,
        "u_safe_internal_modified": False,
        "wrapper_exec_command_scaled": False,
        "run_completed": False,
        "notes": note,
    }
    details = {
        "max_nom_delta": 0.0,
        "max_safe_delta": 0.0,
        "max_exec_delta": 0.0,
        "release_observed": False,
    }
    return row, details


def targeted_observation(
    baseline: dict[str, Any],
    active: dict[str, Any],
) -> str:
    delta = (
        int_value(active, "natural_warning_steps")
        - int_value(baseline, "natural_warning_steps")
    )
    if delta < 0:
        warning_text = f"active recorded {-delta} fewer warning steps"
    elif delta > 0:
        warning_text = f"active recorded {delta} more warning steps"
    else:
        warning_text = "warning-step count was unchanged"
    return (
        f"Small-cohort fixed-candidate observation for {baseline['candidate_id']}: "
        f"{warning_text}; baseline stop={baseline['stop_reason']}, "
        f"active stop={active['stop_reason']}."
    )


def slowdown_after_or_at_warning(active: dict[str, Any]) -> bool:
    slowdown_steps = int_value(active, "slowdown_active_steps")
    first_warning = maybe_int(active.get("first_natural_warning_step", ""))
    first_slowdown = maybe_int(active.get("first_slowdown_step", ""))
    if slowdown_steps <= 0:
        return True
    return (
        first_warning is not None
        and first_slowdown is not None
        and first_slowdown >= first_warning
    )


def build_comparison(
    baseline: dict[str, Any],
    active: dict[str, Any],
) -> dict[str, Any]:
    delta = (
        int_value(active, "natural_warning_steps")
        - int_value(baseline, "natural_warning_steps")
    )
    return {
        "candidate_id": baseline["candidate_id"],
        "baseline_steps_observed": baseline["steps_observed"],
        "active_steps_observed": active["steps_observed"],
        "baseline_warning_steps": baseline["natural_warning_steps"],
        "active_warning_steps": active["natural_warning_steps"],
        "delta_warning_steps_active_minus_baseline": delta,
        "baseline_first_warning_step": baseline[
            "first_natural_warning_step"
        ],
        "active_first_warning_step": active[
            "first_natural_warning_step"
        ],
        "slowdown_active_steps": active["slowdown_active_steps"],
        "first_slowdown_step": active["first_slowdown_step"],
        "slowdown_after_or_at_warning": slowdown_after_or_at_warning(
            active
        ),
        "baseline_collision_observed": baseline[
            "collision_observed"
        ],
        "active_collision_observed": active["collision_observed"],
        "baseline_qp_infeasible_observed": baseline[
            "qp_infeasible_observed"
        ],
        "active_qp_infeasible_observed": active[
            "qp_infeasible_observed"
        ],
        "baseline_completed": baseline["completed"],
        "active_completed": active["completed"],
        "baseline_stop_reason": baseline["stop_reason"],
        "active_stop_reason": active["stop_reason"],
        "targeted_behavior_observation": targeted_observation(
            baseline, active
        ),
        "performance_claim_allowed": False,
        "notes": (
            "Post-activation values are small-cohort targeted behavioral "
            "observations, not same-trajectory causal proof."
        ),
    }


def build_timing(
    baseline: dict[str, Any],
    active: dict[str, Any],
    active_details: dict[str, Any],
) -> dict[str, Any]:
    return {
        "candidate_id": baseline["candidate_id"],
        "baseline_first_warning_step": baseline[
            "first_natural_warning_step"
        ],
        "active_first_warning_step": active[
            "first_natural_warning_step"
        ],
        "first_slowdown_step": active["first_slowdown_step"],
        "slowdown_after_or_at_warning": slowdown_after_or_at_warning(
            active
        ),
        "baseline_warning_steps": baseline["natural_warning_steps"],
        "active_warning_steps": active["natural_warning_steps"],
        "slowdown_active_steps": active["slowdown_active_steps"],
        "release_observed": active_details.get(
            "release_observed", False
        ),
        "notes": (
            "Timing is evaluated against natural warnings in the active run; "
            "no slowdown means no pre-warning scaling violation."
        ),
    }


def build_control(
    baseline: dict[str, Any],
    active: dict[str, Any],
    baseline_details: dict[str, Any],
    active_details: dict[str, Any],
) -> dict[str, Any]:
    max_nom_delta = max(
        float(baseline_details.get("max_nom_delta", 0.0)),
        float(active_details.get("max_nom_delta", 0.0)),
    )
    max_safe_delta = max(
        float(baseline_details.get("max_safe_delta", 0.0)),
        float(active_details.get("max_safe_delta", 0.0)),
    )
    max_exec_delta = float(active_details.get("max_exec_delta", 0.0))
    activation = parse_bool(active["wrapper_exec_command_scaled"])
    control_scope_passed = (
        parse_bool(baseline["run_completed"])
        and parse_bool(active["run_completed"])
        and not parse_bool(baseline["u_nom_modified"])
        and not parse_bool(baseline["u_safe_internal_modified"])
        and not parse_bool(baseline["control_modified"])
        and not parse_bool(active["u_nom_modified"])
        and not parse_bool(active["u_safe_internal_modified"])
        and parse_bool(active["command_modified_only_when_warning"])
        and ((activation and max_exec_delta > 0.0) or not activation)
    )
    return {
        "candidate_id": baseline["candidate_id"],
        "baseline_u_nom_modified": baseline["u_nom_modified"],
        "baseline_u_safe_internal_modified": baseline[
            "u_safe_internal_modified"
        ],
        "baseline_control_modified": baseline["control_modified"],
        "active_u_nom_modified": active["u_nom_modified"],
        "active_u_safe_internal_modified": active[
            "u_safe_internal_modified"
        ],
        "active_wrapper_exec_command_scaled": active[
            "wrapper_exec_command_scaled"
        ],
        "active_command_modified_only_when_warning": active[
            "command_modified_only_when_warning"
        ],
        "max_abs_delta_u_nom": max_nom_delta,
        "max_abs_delta_u_safe_internal": max_safe_delta,
        "max_abs_delta_wrapper_exec_due_to_slowdown": max_exec_delta,
        "control_scope_passed": control_scope_passed,
        "notes": (
            "Baseline command remains unchanged; active may alter only "
            "wrapper-level u_exec under a natural warning."
        ),
    }


def stop_reason_rows(
    baseline_rows: Sequence[dict[str, Any]],
    active_rows: Sequence[dict[str, Any]],
) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    for mode, source_rows in (
        ("baseline", baseline_rows),
        ("active", active_rows),
    ):
        by_reason: dict[str, list[str]] = defaultdict(list)
        for row in source_rows:
            by_reason[str(row["stop_reason"])].append(
                str(row["candidate_id"])
            )
        for reason in sorted(by_reason):
            candidates = by_reason[reason]
            rows.append(
                {
                    "mode": mode,
                    "stop_reason": reason,
                    "count": len(candidates),
                    "candidate_ids": ",".join(candidates),
                    "notes": (
                        "Stop reasons are recorded as observed in compact "
                        "candidate summaries."
                    ),
                }
            )
    return rows


def aggregate_rows(
    args: argparse.Namespace,
    candidates: Sequence[str],
    baseline_rows: Sequence[dict[str, Any]],
    active_rows: Sequence[dict[str, Any]],
    comparison_rows: Sequence[dict[str, Any]],
    control_rows: Sequence[dict[str, Any]],
    timing_rows: Sequence[dict[str, Any]],
) -> tuple[list[dict[str, Any]], dict[str, Any]]:
    baseline_completed_runs = sum(
        parse_bool(row["run_completed"]) for row in baseline_rows
    )
    active_completed_runs = sum(
        parse_bool(row["run_completed"]) for row in active_rows
    )
    baseline_total_warnings = sum(
        int_value(row, "natural_warning_steps") for row in baseline_rows
    )
    active_total_warnings = sum(
        int_value(row, "natural_warning_steps") for row in active_rows
    )
    deltas = [
        int_value(row, "delta_warning_steps_active_minus_baseline")
        for row in comparison_rows
    ]
    less = [
        row["candidate_id"]
        for row in comparison_rows
        if int_value(row, "delta_warning_steps_active_minus_baseline") < 0
    ]
    equal = [
        row["candidate_id"]
        for row in comparison_rows
        if int_value(row, "delta_warning_steps_active_minus_baseline") == 0
    ]
    more = [
        row["candidate_id"]
        for row in comparison_rows
        if int_value(row, "delta_warning_steps_active_minus_baseline") > 0
    ]
    slowdown_activation = [
        row["candidate_id"]
        for row in active_rows
        if int_value(row, "slowdown_active_steps") > 0
    ]
    baseline_collision_count = sum(
        parse_bool(row["collision_observed"]) for row in baseline_rows
    )
    active_collision_count = sum(
        parse_bool(row["collision_observed"]) for row in active_rows
    )
    baseline_qp_count = sum(
        parse_bool(row["qp_infeasible_observed"]) for row in baseline_rows
    )
    active_qp_count = sum(
        parse_bool(row["qp_infeasible_observed"]) for row in active_rows
    )
    baseline_goal_count = sum(
        parse_bool(row["completed"]) for row in baseline_rows
    )
    active_goal_count = sum(
        parse_bool(row["completed"]) for row in active_rows
    )
    control_scope_all_passed = bool(control_rows) and all(
        parse_bool(row["control_scope_passed"]) for row in control_rows
    )
    all_slowdown_after_or_at_warning = bool(timing_rows) and all(
        parse_bool(row["slowdown_after_or_at_warning"])
        for row in timing_rows
    )
    delta_total = active_total_warnings - baseline_total_warnings
    mean_delta = (
        sum(deltas) / len(deltas)
        if deltas
        else math.nan
    )
    complete = (
        baseline_completed_runs == len(candidates)
        and active_completed_runs == len(candidates)
    )
    claim_level = (
        "small_targeted_cohort_observation"
        if complete
        else "small_targeted_cohort_incomplete"
    )
    metrics = {
        "task": "SAFC Level-3D Small Targeted Cohort A/B",
        "new_small_targeted_cohort_run": True,
        "cohort_size": len(candidates),
        "included_candidates": list(candidates),
        "excluded_candidates": {
            "C005": "sensitivity_only_warning",
            "C007": "initial_collision_diagnostic_context",
        },
        "entrypoint": ENTRYPOINT,
        "max_steps": args.max_steps,
        "dt_margin": args.dt_margin,
        "horizon": args.horizon,
        "controller_modified": False,
        "official_core_source_modified": False,
        "cbf_splat_ellipsoids_dynamics_run_modified": False,
        "raw_traces_written": False,
        "baseline_runs_completed": baseline_completed_runs,
        "active_runs_completed": active_completed_runs,
        "baseline_total_warning_steps": baseline_total_warnings,
        "active_total_warning_steps": active_total_warnings,
        "delta_total_warning_steps_active_minus_baseline": delta_total,
        "mean_delta_warning_steps_active_minus_baseline": mean_delta,
        "candidates_active_less_warning": less,
        "candidates_active_equal_warning": equal,
        "candidates_active_more_warning": more,
        "candidates_with_slowdown_activation": slowdown_activation,
        "baseline_collision_count": baseline_collision_count,
        "active_collision_count": active_collision_count,
        "baseline_qp_infeasible_count": baseline_qp_count,
        "active_qp_infeasible_count": active_qp_count,
        "baseline_completed_count": baseline_goal_count,
        "active_completed_count": active_goal_count,
        "control_scope_all_passed": control_scope_all_passed,
        "all_slowdown_after_or_at_warning": all_slowdown_after_or_at_warning,
        "performance_improvement_claimed": False,
        "warning_reduction_claimed": False,
        "collision_reduction_claimed": False,
        "planner_improvement_claimed": False,
        "statistical_significance_claimed": False,
        "claim_level": claim_level,
        "limitations": [
            "small targeted cohort only",
            "pre-registered warning-rich candidates",
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
    rows = [
        {
            "metric": "included_candidates",
            "value": len(candidates),
            "notes": ",".join(candidates),
        },
        {
            "metric": "baseline_runs_completed",
            "value": baseline_completed_runs,
            "notes": "Count of baseline compact runs completed without script exception.",
        },
        {
            "metric": "active_runs_completed",
            "value": active_completed_runs,
            "notes": "Count of active compact runs completed without script exception.",
        },
        {
            "metric": "candidates_with_natural_warning_baseline",
            "value": sum(
                int_value(row, "natural_warning_steps") > 0
                for row in baseline_rows
            ),
            "notes": "Baseline candidates with at least one natural H-step warning.",
        },
        {
            "metric": "candidates_with_slowdown_activation",
            "value": len(slowdown_activation),
            "notes": ",".join(slowdown_activation),
        },
        {
            "metric": "candidates_with_active_warning_less_than_baseline",
            "value": len(less),
            "notes": ",".join(less),
        },
        {
            "metric": "candidates_with_active_warning_equal_baseline",
            "value": len(equal),
            "notes": ",".join(equal),
        },
        {
            "metric": "candidates_with_active_warning_greater_than_baseline",
            "value": len(more),
            "notes": ",".join(more),
        },
        {
            "metric": "sum_baseline_warning_steps",
            "value": baseline_total_warnings,
            "notes": "Small-cohort targeted observation only.",
        },
        {
            "metric": "sum_active_warning_steps",
            "value": active_total_warnings,
            "notes": "Small-cohort targeted observation only.",
        },
        {
            "metric": "delta_sum_warning_steps_active_minus_baseline",
            "value": delta_total,
            "notes": "Active minus baseline warning-step count.",
        },
        {
            "metric": "mean_delta_warning_steps_active_minus_baseline",
            "value": mean_delta,
            "notes": "Mean over pre-registered included candidates; no statistical significance claim.",
        },
        {
            "metric": "baseline_collision_count",
            "value": baseline_collision_count,
            "notes": "Observed compact run collision flags.",
        },
        {
            "metric": "active_collision_count",
            "value": active_collision_count,
            "notes": "Observed compact run collision flags.",
        },
        {
            "metric": "baseline_qp_infeasible_count",
            "value": baseline_qp_count,
            "notes": "Observed compact run QP infeasible flags.",
        },
        {
            "metric": "active_qp_infeasible_count",
            "value": active_qp_count,
            "notes": "Observed compact run QP infeasible flags.",
        },
        {
            "metric": "baseline_completed_count",
            "value": baseline_goal_count,
            "notes": "Goal-reached completion only.",
        },
        {
            "metric": "active_completed_count",
            "value": active_goal_count,
            "notes": "Goal-reached completion only.",
        },
        {
            "metric": "performance_claim_allowed",
            "value": False,
            "notes": "No generalized performance claim is allowed.",
        },
    ]
    return rows, metrics


def write_notes(
    path: Path,
    candidates: Sequence[str],
    baseline_rows: Sequence[dict[str, Any]],
    active_rows: Sequence[dict[str, Any]],
    comparison_rows: Sequence[dict[str, Any]],
    metrics: dict[str, Any],
) -> None:
    baseline_warning_text = "\n".join(
        f"* {row['candidate_id']}: {row['natural_warning_steps']} warnings, stop `{row['stop_reason']}`"
        for row in baseline_rows
    )
    active_warning_text = "\n".join(
        f"* {row['candidate_id']}: {row['natural_warning_steps']} warnings, {row['slowdown_active_steps']} slowdown-active steps, stop `{row['stop_reason']}`"
        for row in active_rows
    )
    comparison_text = "\n".join(
        f"* {row['candidate_id']}: delta {row['delta_warning_steps_active_minus_baseline']}, {row['targeted_behavior_observation']}"
        for row in comparison_rows
    )
    path.write_text(
        f"""# SAFC Level-3D Small Targeted Cohort Notes

## Scope

This is a small targeted cohort A/B comparison over pre-registered
warning-rich candidates. It is not a full benchmark and does not claim
generalized performance improvement.

## Preregistered Cohort

* Included candidates: {", ".join(candidates)}
* Excluded candidates: C005 (`sensitivity_only_warning`), C007 (`initial_collision_diagnostic_context`)
* Fixed `dt_margin`: {metrics['dt_margin']}
* Fixed horizon: H{metrics['horizon']}
* Fixed `max_steps`: {metrics['max_steps']}

## Baseline Runs

{baseline_warning_text}

Baseline commands execute the original `u_safe` unchanged. No slowdown,
recovery, planner, CBF-QP, dynamics, or GSplat query modification is enabled.

## Active Runs

{active_warning_text}

Active runs apply warning-streak slowdown only under a natural warning gate.
They do not modify `u_nom`, internal `u_safe`, CBF-QP, dynamics, planner,
or recovery logic.

## Cohort Observation

* Candidates with fewer warning steps under active: {len(metrics['candidates_active_less_warning'])} ({", ".join(metrics['candidates_active_less_warning']) or "none"})
* Candidates with equal warning steps under active: {len(metrics['candidates_active_equal_warning'])} ({", ".join(metrics['candidates_active_equal_warning']) or "none"})
* Candidates with more warning steps under active: {len(metrics['candidates_active_more_warning'])} ({", ".join(metrics['candidates_active_more_warning']) or "none"})
* Total warning-step delta, active minus baseline: {metrics['delta_total_warning_steps_active_minus_baseline']}
* Baseline / active collision counts: {metrics['baseline_collision_count']} / {metrics['active_collision_count']}
* Baseline / active QP infeasible counts: {metrics['baseline_qp_infeasible_count']} / {metrics['active_qp_infeasible_count']}
* Baseline / active completed counts: {metrics['baseline_completed_count']} / {metrics['active_completed_count']}

Per-candidate observations:

{comparison_text}

Because active commands can alter subsequent trajectories, post-activation
comparisons are targeted behavioral observations rather than same-trajectory
causal proof.

## Claim Boundaries

* small targeted cohort only
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


def validate_args(args: argparse.Namespace) -> list[str]:
    candidates = parse_candidates(args.candidates)
    if args.horizon != 3:
        raise ValueError("Level 3D requires horizon=3")
    if not 1 <= args.max_steps <= 160:
        raise ValueError("max-steps must be in [1, 160]")
    if not math.isfinite(args.dt_margin) or args.dt_margin <= 0.0:
        raise ValueError("dt-margin must be finite and positive")
    if args.mode == "active-only" and len(candidates) == 0:
        raise ValueError("active-only requires at least one candidate")
    return candidates


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="SAFC Level-3D small targeted cohort A/B validation."
    )
    parser.add_argument("--repo-root", type=Path, default=Path("."))
    parser.add_argument(
        "--output-dir",
        type=Path,
        default=Path(
            "work/risk_aware_cbf/results/safc_level3d_small_targeted_cohort"
        ),
    )
    parser.add_argument(
        "--mode",
        choices=("baseline-only", "active-only", "paired-ab"),
        default="paired-ab",
    )
    parser.add_argument(
        "--candidates",
        default=",".join(DEFAULT_CANDIDATES),
        help="Comma-separated included candidate IDs.",
    )
    parser.add_argument("--max-steps", type=int, default=160)
    parser.add_argument("--dt-margin", type=float, default=0.0005)
    parser.add_argument("--horizon", type=int, default=3)
    parser.add_argument("--warning-scale", type=float, default=0.75)
    parser.add_argument(
        "--persistent-warning-scale", type=float, default=0.5
    )
    parser.add_argument(
        "--critical-warning-scale", type=float, default=0.25
    )
    parser.add_argument("--min-scale", type=float, default=0.25)
    parser.add_argument("--entrypoint", default="auto")
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    candidates = validate_args(args)
    repo_root = args.repo_root.resolve()
    output_dir = args.output_dir.resolve()
    output_dir.mkdir(parents=True, exist_ok=True)
    write_readme(output_dir / "README.md")
    write_csv(
        output_dir / "cohort_preregistration.csv",
        PREREG_FIELDS,
        preregistration_rows(args),
    )

    entrypoint_path = select_entrypoint(repo_root, args.entrypoint)
    if entrypoint_path is None:
        raise RuntimeError("official smoke wrapper was not found")
    entrypoint = str(entrypoint_path.relative_to(repo_root)).replace(
        "\\", "/"
    )
    if entrypoint != ENTRYPOINT:
        raise RuntimeError(
            f"Level 3D requires {ENTRYPOINT}, got {entrypoint}"
        )
    wrapper = import_smoke_wrapper(entrypoint_path)
    torch = wrapper.torch
    device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
    _, _, first_cfg = candidate_start_goal(
        wrapper,
        COHORT[candidates[0]]["scene"],
        int(COHORT[candidates[0]]["trial_id"]),
    )
    gsplat = wrapper.GSplatLoader(first_cfg["path_to_gsplat"], device)
    dynamics = wrapper.DoubleIntegrator(device=device, ndim=3)
    policy_config = SlowdownPolicyConfig(
        min_scale=args.min_scale,
        warning_scale=args.warning_scale,
        persistent_warning_scale=args.persistent_warning_scale,
        critical_warning_scale=args.critical_warning_scale,
    )

    baseline_rows: list[dict[str, Any]]
    active_rows: list[dict[str, Any]] = []
    baseline_details_by_id: dict[str, dict[str, Any]] = {}
    active_details_by_id: dict[str, dict[str, Any]] = {}

    if args.mode == "active-only":
        baseline_rows = load_csv(
            output_dir / "per_candidate_baseline_summary.csv"
        )
        baseline_details_by_id = {
            row["candidate_id"]: {
                "max_nom_delta": 0.0,
                "max_safe_delta": 0.0,
                "max_exec_delta": 0.0,
                "release_observed": False,
            }
            for row in baseline_rows
        }
    else:
        baseline_rows = []
        for candidate_id in candidates:
            candidate = COHORT[candidate_id]
            try:
                common, details = run_rollout(
                    wrapper,
                    gsplat,
                    dynamics,
                    device,
                    args,
                    candidate,
                    False,
                    policy_config,
                )
                row = baseline_row(common, details)
            except Exception as exc:  # noqa: BLE001 - compact failure record
                row, details = failed_baseline_row(candidate, exc)
            baseline_rows.append(row)
            baseline_details_by_id[candidate_id] = details

    if args.mode == "baseline-only":
        for candidate_id in candidates:
            row, details = not_run_active_row(
                COHORT[candidate_id],
                "Active run was not requested in baseline-only mode.",
            )
            active_rows.append(row)
            active_details_by_id[candidate_id] = details
    else:
        for candidate_id in candidates:
            candidate = COHORT[candidate_id]
            try:
                common, details = run_rollout(
                    wrapper,
                    gsplat,
                    dynamics,
                    device,
                    args,
                    candidate,
                    True,
                    policy_config,
                )
                row = active_row(common, details)
            except Exception as exc:  # noqa: BLE001 - compact failure record
                row, details = failed_active_row(candidate, exc)
            active_rows.append(row)
            active_details_by_id[candidate_id] = details

    baseline_by_id = {row["candidate_id"]: row for row in baseline_rows}
    active_by_id = {row["candidate_id"]: row for row in active_rows}
    comparison_rows = [
        build_comparison(baseline_by_id[candidate_id], active_by_id[candidate_id])
        for candidate_id in candidates
    ]
    timing_rows = [
        build_timing(
            baseline_by_id[candidate_id],
            active_by_id[candidate_id],
            active_details_by_id[candidate_id],
        )
        for candidate_id in candidates
    ]
    control_rows = [
        build_control(
            baseline_by_id[candidate_id],
            active_by_id[candidate_id],
            baseline_details_by_id[candidate_id],
            active_details_by_id[candidate_id],
        )
        for candidate_id in candidates
    ]
    aggregate, metrics = aggregate_rows(
        args,
        candidates,
        baseline_rows,
        active_rows,
        comparison_rows,
        control_rows,
        timing_rows,
    )
    stop_rows = stop_reason_rows(baseline_rows, active_rows)

    write_csv(
        output_dir / "per_candidate_baseline_summary.csv",
        BASELINE_FIELDS,
        baseline_rows,
    )
    write_csv(
        output_dir / "per_candidate_active_summary.csv",
        ACTIVE_FIELDS,
        active_rows,
    )
    write_csv(
        output_dir / "per_candidate_ab_comparison.csv",
        COMPARISON_FIELDS,
        comparison_rows,
    )
    write_csv(
        output_dir / "cohort_aggregate_summary.csv",
        AGGREGATE_FIELDS,
        aggregate,
    )
    write_csv(
        output_dir / "warning_timing_summary.csv",
        TIMING_FIELDS,
        timing_rows,
    )
    write_csv(
        output_dir / "control_scope_summary.csv",
        CONTROL_FIELDS,
        control_rows,
    )
    write_csv(
        output_dir / "stop_reason_summary.csv",
        STOP_FIELDS,
        stop_rows,
    )
    (output_dir / "metrics.json").write_text(
        json.dumps(metrics, indent=2) + "\n",
        encoding="utf-8",
    )
    write_notes(
        output_dir / "cohort_notes.md",
        candidates,
        baseline_rows,
        active_rows,
        comparison_rows,
        metrics,
    )
    print(json.dumps(metrics, indent=2))

    if not parse_bool(metrics["control_scope_all_passed"]):
        return 2
    if not parse_bool(metrics["all_slowdown_after_or_at_warning"]):
        return 2
    if metrics["claim_level"] != "small_targeted_cohort_observation":
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
