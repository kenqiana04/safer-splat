#!/usr/bin/env python3
"""Run the fixed-C003 SAFC Level-3C targeted A/B comparison."""

from __future__ import annotations

import argparse
import csv
import json
import math
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


CANDIDATE_ID = "C003"
SCENE = "flight"
TRIAL_ID = 14
ENTRYPOINT = "reproduction/scripts/run_official_runpy_smoke.py"
SOURCE_REPORT = (
    "work/risk_aware_cbf/REPORT_SAFC_LEVEL3B_ACTIVE_C003_SLOWDOWN.md; "
    "work/risk_aware_cbf/REPORT_SAFC_LEVEL3BR_WARNING_RECONCILIATION.md"
)

CONTEXT_FIELDS = (
    "candidate_id",
    "scene",
    "trial_id",
    "source_level",
    "source_report",
    "entrypoint",
    "dt_margin",
    "horizon",
    "max_steps",
    "baseline_mode",
    "active_mode",
    "policy",
    "notes",
)
BASELINE_FIELDS = (
    "candidate_id",
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
    "notes",
)
ACTIVE_FIELDS = (
    "candidate_id",
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
    "baseline_collision_observed",
    "active_collision_observed",
    "baseline_qp_infeasible_observed",
    "active_qp_infeasible_observed",
    "baseline_completed",
    "active_completed",
    "baseline_stop_reason",
    "active_stop_reason",
    "slowdown_active_steps",
    "max_control_delta_from_slowdown",
    "targeted_behavior_observation",
    "performance_claim_allowed",
    "notes",
)
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


def write_csv(
    path: Path,
    fields: Sequence[str],
    rows: Iterable[dict[str, Any]],
) -> None:
    with path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=fields)
        writer.writeheader()
        writer.writerows(rows)


def parse_bool(value: Any) -> bool:
    if isinstance(value, bool):
        return value
    return str(value).strip().lower() in {"true", "1", "yes"}


def load_single_csv(path: Path) -> dict[str, str]:
    if not path.is_file():
        raise RuntimeError(f"required compact summary not found: {path}")
    with path.open("r", encoding="utf-8", newline="") as handle:
        rows = list(csv.DictReader(handle))
    if len(rows) != 1:
        raise RuntimeError(f"expected exactly one data row: {path}")
    return rows[0]


def validate_level3b_gate(path: Path) -> None:
    metrics = json.loads(path.read_text(encoding="utf-8"))
    expected = {
        "candidate_id": CANDIDATE_ID,
        "scene": SCENE,
        "trial_id": TRIAL_ID,
        "selected_entrypoint": ENTRYPOINT,
        "max_steps": 100,
        "horizon": 3,
    }
    for field, value in expected.items():
        if metrics.get(field) != value:
            raise RuntimeError(
                f"Level-3B-Active prerequisite mismatch: {field}"
            )
    if not math.isclose(
        float(metrics.get("dt_margin", math.nan)),
        0.0005,
        rel_tol=0.0,
        abs_tol=1e-12,
    ):
        raise RuntimeError(
            "Level-3B-Active prerequisite mismatch: dt_margin"
        )
    required_true = (
        "confirmed_natural_warning",
        "active_smoke_attempted",
        "activation_observed",
        "slowdown_after_or_at_warning",
        "wrapper_exec_command_scaled",
        "command_modified_only_when_warning",
    )
    if not all(parse_bool(metrics.get(field)) for field in required_true):
        raise RuntimeError(
            "Level-3B-Active prerequisite gate is not satisfied"
        )
    if parse_bool(metrics.get("u_nom_modified")) or parse_bool(
        metrics.get("u_safe_internal_modified")
    ):
        raise RuntimeError(
            "Level-3B-Active prerequisite failed control-scope invariants"
        )


def context_row(
    args: argparse.Namespace,
    entrypoint: str,
) -> dict[str, Any]:
    return {
        "candidate_id": CANDIDATE_ID,
        "scene": SCENE,
        "trial_id": TRIAL_ID,
        "source_level": "Level-3B-Active / Level-3B-R",
        "source_report": SOURCE_REPORT,
        "entrypoint": entrypoint,
        "dt_margin": args.dt_margin,
        "horizon": args.horizon,
        "max_steps": args.max_steps,
        "baseline_mode": "noop",
        "active_mode": "warning_streak_slowdown",
        "policy": (
            f"warning={args.warning_scale}; "
            f"persistent={args.persistent_warning_scale}; "
            f"critical={args.critical_warning_scale}; "
            f"min={args.min_scale}"
        ),
        "notes": (
            "Single fixed-C003 targeted A/B context; no benchmark or "
            "generalized performance claim."
        ),
    }


def validate_existing_context(
    output_dir: Path,
    args: argparse.Namespace,
    entrypoint: str,
) -> dict[str, str]:
    context = load_single_csv(output_dir / "ab_context.csv")
    expected = {
        "candidate_id": CANDIDATE_ID,
        "scene": SCENE,
        "trial_id": str(TRIAL_ID),
        "entrypoint": entrypoint,
        "horizon": str(args.horizon),
        "max_steps": str(args.max_steps),
        "baseline_mode": "noop",
    }
    for field, value in expected.items():
        if str(context.get(field, "")).strip() != value:
            raise RuntimeError(
                f"active-only refused: A/B context mismatch for {field}"
            )
    if not math.isclose(
        float(context.get("dt_margin", "nan")),
        args.dt_margin,
        rel_tol=0.0,
        abs_tol=1e-12,
    ):
        raise RuntimeError(
            "active-only refused: A/B context mismatch for dt_margin"
        )
    return load_single_csv(output_dir / "baseline_noop_summary.csv")


def run_rollout(
    wrapper: Any,
    gsplat: Any,
    dynamics: Any,
    device: Any,
    args: argparse.Namespace,
    active: bool,
    policy_config: SlowdownPolicyConfig,
) -> tuple[dict[str, Any], dict[str, Any]]:
    start, goal_position, cfg = candidate_start_goal(
        wrapper, SCENE, TRIAL_ID
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
                    "slowdown policy returned an unbounded scale"
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
        if step == args.max_steps:
            completed = True
            stop_reason = "max_steps_while_moving"

    common = {
        "candidate_id": CANDIDATE_ID,
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
        "notes": (
            "Original u_safe executed unchanged; no slowdown, recovery, "
            "or planner. Completion follows official run.py loose semantics."
        ),
    }


def active_row(
    common: dict[str, Any],
    details: dict[str, Any],
) -> dict[str, Any]:
    activation = details["slowdown_active_steps"] > 0
    return {
        "candidate_id": common["candidate_id"],
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
        "notes": (
            "Scale range covers warning-gated active steps only. No "
            "recovery or planner. Completion follows official run.py."
        ),
    }


def unavailable_active_row(reason: str) -> dict[str, Any]:
    row = {
        field: ""
        for field in ACTIVE_FIELDS
    }
    row.update(
        {
            "candidate_id": CANDIDATE_ID,
            "steps_observed": 0,
            "natural_warning_steps": 0,
            "h1_warning_steps": 0,
            "h2_warning_steps": 0,
            "h3_warning_steps": 0,
            "slowdown_active_steps": 0,
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
            "notes": reason,
        }
    )
    return row


def targeted_observation(
    baseline: dict[str, Any],
    active: dict[str, Any],
) -> str:
    baseline_warnings = int(baseline["natural_warning_steps"])
    active_warnings = int(active["natural_warning_steps"])
    delta = active_warnings - baseline_warnings
    if delta < 0:
        warning_text = (
            f"active recorded {-delta} fewer warning steps"
        )
    elif delta > 0:
        warning_text = (
            f"active recorded {delta} more warning steps"
        )
    else:
        warning_text = "warning-step count was unchanged"
    return (
        f"Fixed C003 observation: {warning_text}; baseline stop="
        f"{baseline['stop_reason']}, active stop={active['stop_reason']}; "
        f"baseline collision={baseline['collision_observed']}, active "
        f"collision={active['collision_observed']}."
    )


def build_comparison(
    baseline: dict[str, Any],
    active: dict[str, Any],
) -> dict[str, Any]:
    delta = (
        int(active["natural_warning_steps"])
        - int(baseline["natural_warning_steps"])
    )
    return {
        "candidate_id": CANDIDATE_ID,
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
        "slowdown_active_steps": active["slowdown_active_steps"],
        "max_control_delta_from_slowdown": active[
            "max_control_delta_from_slowdown"
        ],
        "targeted_behavior_observation": targeted_observation(
            baseline, active
        ),
        "performance_claim_allowed": False,
        "notes": (
            "Post-activation values are fixed-case behavioral "
            "observations, not same-trajectory causal proof."
        ),
    }


def write_readme(path: Path) -> None:
    path.write_text(
        """# SAFC Level-3C Fixed-C003 Targeted A/B Results

This directory contains compact outputs for a fixed-C003 targeted A/B
comparison between no-op execution and warning-streak slowdown. This is a
single fixed-case targeted comparison, not a full benchmark and not evidence
of generalized performance improvement.

Outputs:

* `ab_context.csv`
* `baseline_noop_summary.csv`
* `active_slowdown_summary.csv`
* `ab_comparison_summary.csv`
* `warning_timing_summary.csv`
* `control_scope_summary.csv`
* `metrics.json`
* `ab_notes.md`

No raw traces, full trial dumps, per-step dumps, active-constraint dumps,
trajectory samples, JSONL logs, images, or binary files should be committed
here.
""",
        encoding="utf-8",
    )


def write_notes(
    path: Path,
    baseline: dict[str, Any],
    active: dict[str, Any],
    comparison: dict[str, Any],
    timing: dict[str, Any],
) -> None:
    path.write_text(
        f"""# SAFC Level-3C Fixed-C003 Targeted A/B Notes

## Scope

This is a fixed-C003 targeted A/B comparison between no-op execution and
warning-streak slowdown. It is not a full benchmark and does not claim
generalized performance improvement.

## Fixed Candidate

* C003
* flight trial 14
* selected from Level 3B-R and Level 3B-Active
* H3
* `dt_margin=0.0005`
* current official smoke wrapper
* `max_steps=100`

## Baseline No-Op

* Warning steps: {baseline['natural_warning_steps']}
* First warning step: {baseline['first_natural_warning_step']}
* Collision: {baseline['collision_observed']}
* QP infeasible: {baseline['qp_infeasible_observed']}
* Completed: {baseline['completed']}
* Stop reason: `{baseline['stop_reason']}`
* Command modified: {baseline['control_modified']}

## Active Slowdown

* Warning steps: {active['natural_warning_steps']}
* First warning step: {active['first_natural_warning_step']}
* Slowdown-active steps: {active['slowdown_active_steps']}
* First slowdown step: {active['first_slowdown_step']}
* Active scale range: [{active['min_scale_applied']}, {active['max_scale_applied']}]
* Wrapper-level command scaled: {active['wrapper_exec_command_scaled']}
* `u_nom` modified: {active['u_nom_modified']}
* Internal `u_safe` modified: {active['u_safe_internal_modified']}

## A/B Observation

* Warning-step delta, active minus baseline:
  {comparison['delta_warning_steps_active_minus_baseline']}
* Baseline / active collision:
  {baseline['collision_observed']} / {active['collision_observed']}
* Baseline / active QP infeasible:
  {baseline['qp_infeasible_observed']} / {active['qp_infeasible_observed']}
* Baseline / active completed:
  {baseline['completed']} / {active['completed']}
* Release observed: {timing['release_observed']}
* {comparison['targeted_behavior_observation']}

Because the active command can alter the subsequent trajectory,
post-activation comparisons are targeted behavioral observations rather than
same-trajectory causal proof.

## Claim Boundaries

* Targeted A/B only
* Single fixed candidate
* No full benchmark
* No statistical significance
* No generalized performance improvement
* No general collision reduction claim
* No general warning reduction claim
* No planner integration
* No real-robot validation
* No global safety guarantee
* No new CBF theorem
""",
        encoding="utf-8",
    )


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="SAFC Level-3C fixed-C003 targeted A/B comparison."
    )
    parser.add_argument("--repo-root", type=Path, default=Path("."))
    parser.add_argument(
        "--output-dir",
        type=Path,
        default=Path(
            "work/risk_aware_cbf/results/safc_level3c_fixed_c003_ab"
        ),
    )
    parser.add_argument(
        "--mode",
        choices=("baseline-only", "active-only", "paired-ab"),
        default="paired-ab",
    )
    parser.add_argument("--candidate-id", default=CANDIDATE_ID)
    parser.add_argument("--scene", default=SCENE)
    parser.add_argument("--trial-id", type=int, default=TRIAL_ID)
    parser.add_argument("--max-steps", type=int, default=100)
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
    parser.add_argument(
        "--level3b-metrics",
        type=Path,
        default=None,
        help=(
            "Optional read-only Level-3B-Active metrics path; defaults to "
            "the canonical path under repo-root."
        ),
    )
    return parser.parse_args()


def validate_args(args: argparse.Namespace) -> None:
    if (
        args.candidate_id != CANDIDATE_ID
        or args.scene != SCENE
        or args.trial_id != TRIAL_ID
    ):
        raise ValueError("this runner is fixed to C003 / flight trial 14")
    if not 1 <= args.max_steps <= 100:
        raise ValueError("max-steps must be in [1, 100]")
    if args.horizon != 3:
        raise ValueError("this runner requires horizon=3")
    if not math.isfinite(args.dt_margin) or args.dt_margin <= 0.0:
        raise ValueError("dt-margin must be finite and positive")


def main() -> int:
    args = parse_args()
    validate_args(args)
    repo_root = args.repo_root.resolve()
    output_dir = args.output_dir.resolve()
    level3b_metrics = (
        args.level3b_metrics.resolve()
        if args.level3b_metrics is not None
        else (
            repo_root
            / "work/risk_aware_cbf/results/"
            "safc_level3b_active_c003_slowdown/metrics.json"
        )
    )
    validate_level3b_gate(level3b_metrics)
    output_dir.mkdir(parents=True, exist_ok=True)
    write_readme(output_dir / "README.md")

    entrypoint_path = select_entrypoint(repo_root, args.entrypoint)
    if entrypoint_path is None:
        raise RuntimeError("official smoke wrapper was not found")
    entrypoint = str(entrypoint_path.relative_to(repo_root)).replace(
        "\\", "/"
    )
    if entrypoint != ENTRYPOINT:
        raise RuntimeError(
            f"fixed comparison requires {ENTRYPOINT}, got {entrypoint}"
        )
    wrapper = import_smoke_wrapper(entrypoint_path)
    torch = wrapper.torch
    device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
    _, _, cfg = candidate_start_goal(wrapper, SCENE, TRIAL_ID)
    gsplat = wrapper.GSplatLoader(cfg["path_to_gsplat"], device)
    dynamics = wrapper.DoubleIntegrator(device=device, ndim=3)
    policy_config = SlowdownPolicyConfig(
        min_scale=args.min_scale,
        warning_scale=args.warning_scale,
        persistent_warning_scale=args.persistent_warning_scale,
        critical_warning_scale=args.critical_warning_scale,
    )

    baseline_run_completed = False
    active_run_completed = False
    baseline_details = {
        "max_nom_delta": 0.0,
        "max_safe_delta": 0.0,
        "max_exec_delta": 0.0,
    }
    active_details = {
        "max_nom_delta": 0.0,
        "max_safe_delta": 0.0,
        "max_exec_delta": 0.0,
        "release_observed": False,
    }
    if args.mode == "active-only":
        baseline = validate_existing_context(
            output_dir, args, entrypoint
        )
        baseline_run_completed = True
    else:
        baseline_common, baseline_details = run_rollout(
            wrapper,
            gsplat,
            dynamics,
            device,
            args,
            False,
            policy_config,
        )
        baseline = baseline_row(baseline_common, baseline_details)
        baseline_run_completed = True

    if args.mode in {"active-only", "paired-ab"}:
        active_common, active_details = run_rollout(
            wrapper,
            gsplat,
            dynamics,
            device,
            args,
            True,
            policy_config,
        )
        active = active_row(active_common, active_details)
        active_run_completed = True
    else:
        active = unavailable_active_row(
            "Active run was not requested in baseline-only mode."
        )

    comparison_available = (
        baseline_run_completed and active_run_completed
    )
    if comparison_available:
        comparison = build_comparison(baseline, active)
    else:
        comparison = {
            field: ""
            for field in COMPARISON_FIELDS
        }
        comparison.update(
            {
                "candidate_id": CANDIDATE_ID,
                "performance_claim_allowed": False,
                "notes": "Paired A/B comparison is incomplete.",
            }
        )

    first_active_warning = str(
        active["first_natural_warning_step"]
    ).strip()
    first_slowdown = str(active["first_slowdown_step"]).strip()
    activation = int(active["slowdown_active_steps"] or 0) > 0
    timing_ok = (
        activation
        and bool(first_active_warning)
        and bool(first_slowdown)
        and int(first_slowdown) >= int(first_active_warning)
    )
    timing = {
        "candidate_id": CANDIDATE_ID,
        "baseline_first_warning_step": baseline[
            "first_natural_warning_step"
        ],
        "active_first_warning_step": active[
            "first_natural_warning_step"
        ],
        "first_slowdown_step": active["first_slowdown_step"],
        "slowdown_after_or_at_warning": timing_ok,
        "baseline_warning_steps": baseline["natural_warning_steps"],
        "active_warning_steps": active["natural_warning_steps"],
        "slowdown_active_steps": active["slowdown_active_steps"],
        "release_observed": active_details.get(
            "release_observed", False
        ),
        "notes": (
            "Timing is evaluated against the natural warning observed in "
            "the active run."
        ),
    }
    max_nom_delta = max(
        float(baseline_details.get("max_nom_delta", 0.0)),
        float(active_details.get("max_nom_delta", 0.0)),
    )
    max_safe_delta = max(
        float(baseline_details.get("max_safe_delta", 0.0)),
        float(active_details.get("max_safe_delta", 0.0)),
    )
    max_exec_delta = float(
        active_details.get("max_exec_delta", 0.0)
    )
    control_scope_passed = (
        not parse_bool(baseline["u_nom_modified"])
        and not parse_bool(baseline["u_safe_internal_modified"])
        and not parse_bool(baseline["control_modified"])
        and not parse_bool(active["u_nom_modified"])
        and not parse_bool(active["u_safe_internal_modified"])
        and parse_bool(active["command_modified_only_when_warning"])
        and ((activation and max_exec_delta > 0.0) or not activation)
    )
    control = {
        "candidate_id": CANDIDATE_ID,
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
            "Baseline command must remain unchanged; active may alter only "
            "wrapper-level u_exec under a natural warning."
        ),
    }
    delta_warnings = (
        int(active["natural_warning_steps"])
        - int(baseline["natural_warning_steps"])
        if comparison_available
        else None
    )
    metrics = {
        "task": "SAFC Level-3C Fixed-C003 Targeted A/B Comparison",
        "new_targeted_ab_run": True,
        "candidate_id": CANDIDATE_ID,
        "scene": SCENE,
        "trial_id": TRIAL_ID,
        "entrypoint": entrypoint,
        "max_steps": args.max_steps,
        "dt_margin": args.dt_margin,
        "horizon": args.horizon,
        "controller_modified": False,
        "official_core_source_modified": False,
        "cbf_splat_ellipsoids_dynamics_run_modified": False,
        "raw_traces_written": False,
        "baseline_run_completed": baseline_run_completed,
        "active_run_completed": active_run_completed,
        "baseline_steps_observed": int(baseline["steps_observed"]),
        "active_steps_observed": int(active["steps_observed"]),
        "baseline_warning_steps": int(
            baseline["natural_warning_steps"]
        ),
        "active_warning_steps": int(active["natural_warning_steps"]),
        "delta_warning_steps_active_minus_baseline": delta_warnings,
        "baseline_first_warning_step": (
            int(baseline["first_natural_warning_step"])
            if str(baseline["first_natural_warning_step"]).strip()
            else None
        ),
        "active_first_warning_step": (
            int(active["first_natural_warning_step"])
            if str(active["first_natural_warning_step"]).strip()
            else None
        ),
        "slowdown_active_steps": int(active["slowdown_active_steps"]),
        "first_slowdown_step": (
            int(active["first_slowdown_step"])
            if str(active["first_slowdown_step"]).strip()
            else None
        ),
        "slowdown_after_or_at_warning": timing_ok,
        "min_scale_applied": float(active["min_scale_applied"]),
        "max_scale_applied": float(active["max_scale_applied"]),
        "max_control_delta_from_slowdown": float(
            active["max_control_delta_from_slowdown"]
        ),
        "baseline_collision_observed": parse_bool(
            baseline["collision_observed"]
        ),
        "active_collision_observed": parse_bool(
            active["collision_observed"]
        ),
        "baseline_qp_infeasible_observed": parse_bool(
            baseline["qp_infeasible_observed"]
        ),
        "active_qp_infeasible_observed": parse_bool(
            active["qp_infeasible_observed"]
        ),
        "baseline_completed": parse_bool(baseline["completed"]),
        "active_completed": parse_bool(active["completed"]),
        "baseline_stop_reason": baseline["stop_reason"],
        "active_stop_reason": active["stop_reason"],
        "u_nom_modified": (
            parse_bool(baseline["u_nom_modified"])
            or parse_bool(active["u_nom_modified"])
        ),
        "u_safe_internal_modified": (
            parse_bool(baseline["u_safe_internal_modified"])
            or parse_bool(active["u_safe_internal_modified"])
        ),
        "wrapper_exec_command_scaled": parse_bool(
            active["wrapper_exec_command_scaled"]
        ),
        "command_modified_only_when_warning": parse_bool(
            active["command_modified_only_when_warning"]
        ),
        "control_scope_passed": control_scope_passed,
        "targeted_ab_observation_recorded": comparison_available,
        "performance_improvement_claimed": False,
        "warning_reduction_claimed": False,
        "collision_reduction_claimed": False,
        "planner_improvement_claimed": False,
        "claim_level": (
            "fixed_candidate_targeted_ab_observation"
            if comparison_available
            else "fixed_candidate_ab_incomplete"
        ),
        "limitations": [
            "fixed-C003 targeted A/B only",
            "not full100",
            "not flight20",
            "not a benchmark comparison",
            "single fixed candidate",
            "active trajectory may diverge after slowdown",
            "does not establish generalized performance improvement",
            "does not modify CBF-QP",
            "does not modify dynamics",
            "does not validate planner integration",
            "does not validate real-robot deployment",
            "does not prove global safety",
        ],
    }

    write_csv(
        output_dir / "ab_context.csv",
        CONTEXT_FIELDS,
        [context_row(args, entrypoint)],
    )
    if args.mode != "active-only":
        write_csv(
            output_dir / "baseline_noop_summary.csv",
            BASELINE_FIELDS,
            [baseline],
        )
    write_csv(
        output_dir / "active_slowdown_summary.csv",
        ACTIVE_FIELDS,
        [active],
    )
    write_csv(
        output_dir / "ab_comparison_summary.csv",
        COMPARISON_FIELDS,
        [comparison],
    )
    write_csv(
        output_dir / "warning_timing_summary.csv",
        TIMING_FIELDS,
        [timing],
    )
    write_csv(
        output_dir / "control_scope_summary.csv",
        CONTROL_FIELDS,
        [control],
    )
    (output_dir / "metrics.json").write_text(
        json.dumps(metrics, indent=2) + "\n",
        encoding="utf-8",
    )
    write_notes(
        output_dir / "ab_notes.md",
        baseline,
        active,
        comparison,
        timing,
    )
    print(json.dumps(metrics, indent=2))

    if comparison_available and (
        not activation
        or not timing_ok
        or not control_scope_passed
    ):
        return 2
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
