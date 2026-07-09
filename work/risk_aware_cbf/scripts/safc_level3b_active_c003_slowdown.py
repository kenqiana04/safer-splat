#!/usr/bin/env python3
"""Run the fixed-C003 SAFC Level-3B-Active slowdown smoke."""

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
    "work/risk_aware_cbf/REPORT_SAFC_LEVEL3BR_WARNING_RECONCILIATION.md"
)
SOURCE_FIRST_WARNING_STEP = 60

CONTEXT_FIELDS = (
    "candidate_id",
    "scene",
    "trial_id",
    "source_level",
    "source_report",
    "source_first_warning_step",
    "selected_entrypoint",
    "dt_margin",
    "horizon",
    "max_steps",
    "policy",
    "notes",
)
NOOP_FIELDS = (
    "candidate_id",
    "scene",
    "trial_id",
    "steps_observed",
    "natural_warning_steps",
    "first_natural_warning_step",
    "h1_warning_steps",
    "h2_warning_steps",
    "h3_warning_steps",
    "qp_infeasible_steps",
    "collision_steps",
    "u_nom_modified",
    "u_safe_internal_modified",
    "control_modified",
    "confirmed_natural_warning",
    "active_smoke_allowed",
    "notes",
)
ACTIVE_FIELDS = (
    "candidate_id",
    "scene",
    "trial_id",
    "active_smoke_attempted",
    "steps_observed",
    "natural_warning_steps",
    "first_natural_warning_step",
    "slowdown_active_steps",
    "first_slowdown_step",
    "min_scale_applied",
    "max_scale_applied",
    "max_control_delta_from_slowdown",
    "command_modified_only_when_warning",
    "u_nom_modified",
    "u_safe_internal_modified",
    "wrapper_exec_command_scaled",
    "collision_observed",
    "qp_infeasible_observed",
    "recovery_used_observed",
    "activation_observed",
    "notes",
)
TIMING_FIELDS = (
    "candidate_id",
    "first_natural_warning_step_noop",
    "first_natural_warning_step_active",
    "first_slowdown_step",
    "slowdown_after_or_at_warning",
    "slowdown_active_steps",
    "release_observed",
    "notes",
)
CONTROL_FIELDS = (
    "candidate_id",
    "max_abs_delta_u_nom",
    "max_abs_delta_u_safe_internal",
    "max_abs_delta_wrapper_exec_due_to_slowdown",
    "u_nom_modified",
    "u_safe_internal_modified",
    "wrapper_exec_command_scaled",
    "command_modified_only_when_warning",
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
        raise RuntimeError(
            "active-only mode requires an existing Stage-A summary"
        )
    with path.open("r", encoding="utf-8", newline="") as handle:
        rows = list(csv.DictReader(handle))
    if len(rows) != 1:
        raise RuntimeError("Stage-A summary must contain exactly one row")
    return rows[0]


def validate_existing_precheck(
    output_dir: Path,
    args: argparse.Namespace,
    entrypoint: str,
) -> dict[str, str]:
    context = load_single_csv(output_dir / "fixed_candidate_context.csv")
    noop = load_single_csv(output_dir / "noop_precheck_summary.csv")
    exact_expected = {
        "candidate_id": CANDIDATE_ID,
        "scene": SCENE,
        "trial_id": str(TRIAL_ID),
        "selected_entrypoint": entrypoint,
        "horizon": str(args.horizon),
        "max_steps": str(args.max_steps),
    }
    for field, expected in exact_expected.items():
        if str(context.get(field, "")).strip() != expected:
            raise RuntimeError(
                f"active-only refused: Stage-A context mismatch for {field}"
            )
    if not math.isclose(
        float(context.get("dt_margin", "nan")),
        args.dt_margin,
        rel_tol=0.0,
        abs_tol=1e-12,
    ):
        raise RuntimeError(
            "active-only refused: Stage-A context mismatch for dt_margin"
        )
    for field, expected in (
        ("candidate_id", CANDIDATE_ID),
        ("scene", SCENE),
        ("trial_id", str(TRIAL_ID)),
    ):
        if str(noop.get(field, "")).strip() != expected:
            raise RuntimeError(
                f"active-only refused: Stage-A summary mismatch for {field}"
            )
    return noop


def fixed_context(args: argparse.Namespace, entrypoint: str) -> dict[str, Any]:
    return {
        "candidate_id": CANDIDATE_ID,
        "scene": SCENE,
        "trial_id": TRIAL_ID,
        "source_level": "Level-3B-R",
        "source_report": SOURCE_REPORT,
        "source_first_warning_step": SOURCE_FIRST_WARNING_STEP,
        "selected_entrypoint": entrypoint,
        "dt_margin": args.dt_margin,
        "horizon": args.horizon,
        "max_steps": args.max_steps,
        "policy": "warning_streak_slowdown",
        "notes": (
            "Fixed candidate selected because Level-3B-R reproduced a "
            "natural H3 warning at step 60."
        ),
    }


def run_noop_precheck(
    wrapper: Any,
    gsplat: Any,
    dynamics: Any,
    device: Any,
    args: argparse.Namespace,
) -> tuple[dict[str, Any], dict[str, float]]:
    start, goal_position, cfg = candidate_start_goal(
        wrapper, SCENE, TRIAL_ID
    )
    x, goal = build_state(wrapper, device, start, goal_position)
    cbf = make_cbf(wrapper, gsplat, dynamics, cfg)
    dt = 0.05
    method = "ball-to-ellipsoid"
    counts = {
        "steps": 0,
        "natural": 0,
        "h1": 0,
        "h2": 0,
        "h3": 0,
        "qp": 0,
        "collision": 0,
    }
    first_warning: int | None = None
    max_nom_delta = 0.0
    max_safe_delta = 0.0
    max_exec_delta = 0.0

    for step in range(1, args.max_steps + 1):
        x_previous = x.detach().clone()
        current_h = min_query_h(
            wrapper, gsplat, x, cfg["radius"], method
        )
        if current_h < 0.0:
            counts["collision"] += 1
            break
        u_nom, u_safe = nominal_and_safe(wrapper, cbf, x, goal)
        u_nom_before = u_nom.detach().clone()
        u_safe_before = u_safe.detach().clone()
        u_exec_original = u_safe.detach().clone()
        counts["steps"] += 1
        if not bool(cbf.solver_success):
            counts["qp"] += 1
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
        if natural_warning and first_warning is None:
            first_warning = step
        counts["natural"] += int(natural_warning)
        counts["h1"] += int(h1)
        counts["h2"] += int(h2)
        counts["h3"] += int(h3)

        u_exec = u_safe.detach().clone()
        max_nom_delta = max(
            max_nom_delta,
            max_abs_tensor(wrapper, u_nom - u_nom_before),
        )
        max_safe_delta = max(
            max_safe_delta,
            max_abs_tensor(wrapper, u_safe - u_safe_before),
        )
        max_exec_delta = max(
            max_exec_delta,
            max_abs_tensor(wrapper, u_exec - u_exec_original),
        )
        x = wrapper.double_integrator_dynamics(x, u_exec) * dt + x
        if min_query_h(
            wrapper, gsplat, x, cfg["radius"], method
        ) < 0.0:
            counts["collision"] += 1
            break
        if wrapper.torch.norm(x - x_previous) < 0.001:
            break

    confirmed = counts["natural"] >= args.min_natural_warning_steps
    row = {
        "candidate_id": CANDIDATE_ID,
        "scene": SCENE,
        "trial_id": TRIAL_ID,
        "steps_observed": counts["steps"],
        "natural_warning_steps": counts["natural"],
        "first_natural_warning_step": (
            first_warning if first_warning is not None else ""
        ),
        "h1_warning_steps": counts["h1"],
        "h2_warning_steps": counts["h2"],
        "h3_warning_steps": counts["h3"],
        "qp_infeasible_steps": counts["qp"],
        "collision_steps": counts["collision"],
        "u_nom_modified": max_nom_delta != 0.0,
        "u_safe_internal_modified": max_safe_delta != 0.0,
        "control_modified": max_exec_delta != 0.0,
        "confirmed_natural_warning": confirmed,
        "active_smoke_allowed": confirmed,
        "notes": (
            "Natural H1/H2/H3 repeated-control verification; original "
            "u_safe executed unchanged. No slowdown, recovery, or planner."
        ),
    }
    deltas = {
        "max_nom": max_nom_delta,
        "max_safe": max_safe_delta,
        "max_exec": max_exec_delta,
    }
    return row, deltas


def run_active_slowdown(
    wrapper: Any,
    gsplat: Any,
    dynamics: Any,
    device: Any,
    args: argparse.Namespace,
    policy_config: SlowdownPolicyConfig,
) -> tuple[dict[str, Any], dict[str, Any], dict[str, float]]:
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
    natural_warning_steps = 0
    slowdown_active_steps = 0
    first_warning: int | None = None
    first_slowdown: int | None = None
    active_scales: list[float] = []
    max_exec_delta = 0.0
    max_nom_delta = 0.0
    max_safe_delta = 0.0
    collision_observed = False
    qp_infeasible_observed = False
    modified_only_when_warning = True
    release_observed = False

    for step in range(1, args.max_steps + 1):
        x_previous = x.detach().clone()
        current_h = min_query_h(
            wrapper, gsplat, x, cfg["radius"], method
        )
        collision_current = current_h < 0.0
        collision_observed = collision_observed or collision_current
        if collision_current:
            break
        u_nom, u_safe = nominal_and_safe(wrapper, cbf, x, goal)
        u_nom_before = u_nom.detach().clone()
        u_safe_before = u_safe.detach().clone()
        u_exec_original = u_safe.detach().clone()
        steps += 1
        qp_infeasible = not bool(cbf.solver_success)
        qp_infeasible_observed = (
            qp_infeasible_observed or qp_infeasible
        )
        if qp_infeasible:
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
            policy_config,
        )
        if not decision.bounded:
            raise RuntimeError("slowdown policy returned an unbounded scale")
        applied_scale = decision.scale if natural_warning else 1.0
        active = natural_warning and applied_scale < 1.0
        u_exec = (
            apply_scale_to_vector(u_safe, applied_scale)
            if active
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
        natural_warning_steps += int(natural_warning)
        if active:
            slowdown_active_steps += 1
            active_scales.append(float(applied_scale))
            if first_slowdown is None:
                first_slowdown = step
        elif slowdown_active_steps > 0 and not natural_warning:
            release_observed = True
        previous_scale = decision.scale

        x = wrapper.double_integrator_dynamics(x, u_exec) * dt + x
        if min_query_h(
            wrapper, gsplat, x, cfg["radius"], method
        ) < 0.0:
            collision_observed = True
            break
        if wrapper.torch.norm(x - x_previous) < 0.001:
            break

    activation = slowdown_active_steps > 0
    min_scale = min(active_scales) if active_scales else 1.0
    max_scale = max(active_scales) if active_scales else 1.0
    timing_ok = (
        activation
        and first_warning is not None
        and first_slowdown is not None
        and first_slowdown >= first_warning
    )
    row = {
        "candidate_id": CANDIDATE_ID,
        "scene": SCENE,
        "trial_id": TRIAL_ID,
        "active_smoke_attempted": True,
        "steps_observed": steps,
        "natural_warning_steps": natural_warning_steps,
        "first_natural_warning_step": (
            first_warning if first_warning is not None else ""
        ),
        "slowdown_active_steps": slowdown_active_steps,
        "first_slowdown_step": (
            first_slowdown if first_slowdown is not None else ""
        ),
        "min_scale_applied": min_scale,
        "max_scale_applied": max_scale,
        "max_control_delta_from_slowdown": max_exec_delta,
        "command_modified_only_when_warning": modified_only_when_warning,
        "u_nom_modified": max_nom_delta != 0.0,
        "u_safe_internal_modified": max_safe_delta != 0.0,
        "wrapper_exec_command_scaled": activation,
        "collision_observed": collision_observed,
        "qp_infeasible_observed": qp_infeasible_observed,
        "recovery_used_observed": False,
        "activation_observed": activation,
        "notes": (
            "Scale range covers warning-gated active steps only. "
            "No recovery or planner was used."
        ),
    }
    timing = {
        "first_active_warning": first_warning,
        "first_slowdown": first_slowdown,
        "slowdown_after_or_at_warning": timing_ok,
        "release_observed": release_observed,
    }
    deltas = {
        "max_nom": max_nom_delta,
        "max_safe": max_safe_delta,
        "max_exec": max_exec_delta,
    }
    return row, timing, deltas


def non_attempted_active(note: str) -> dict[str, Any]:
    return {
        "candidate_id": CANDIDATE_ID,
        "scene": SCENE,
        "trial_id": TRIAL_ID,
        "active_smoke_attempted": False,
        "steps_observed": 0,
        "natural_warning_steps": 0,
        "first_natural_warning_step": "",
        "slowdown_active_steps": 0,
        "first_slowdown_step": "",
        "min_scale_applied": 1.0,
        "max_scale_applied": 1.0,
        "max_control_delta_from_slowdown": 0.0,
        "command_modified_only_when_warning": True,
        "u_nom_modified": False,
        "u_safe_internal_modified": False,
        "wrapper_exec_command_scaled": False,
        "collision_observed": False,
        "qp_infeasible_observed": False,
        "recovery_used_observed": False,
        "activation_observed": False,
        "notes": note,
    }


def write_readme(path: Path) -> None:
    path.write_text(
        """# SAFC Fixed-Candidate Level-3B-Active C003 Slowdown Results

This directory contains compact outputs for a fixed-candidate targeted
activation smoke using C003 / flight trial 14. The goal is to test whether
warning-streak slowdown activates under naturally observed warning conditions
in the reproduced executable context. This is not a full benchmark and does
not claim performance improvement.

Outputs:

* `fixed_candidate_context.csv`
* `noop_precheck_summary.csv`
* `active_slowdown_summary.csv`
* `activation_timing_summary.csv`
* `control_scope_summary.csv`
* `metrics.json`
* `active_c003_notes.md`

No raw traces, full trial dumps, per-step dumps, active-constraint dumps,
trajectory samples, JSONL logs, images, or binary files should be committed
here.
""",
        encoding="utf-8",
    )


def write_notes(
    path: Path,
    noop: dict[str, Any],
    active: dict[str, Any],
    timing: dict[str, Any],
) -> None:
    attempted = parse_bool(active["active_smoke_attempted"])
    active_text = (
        f"""* Active-run natural warning steps: {active['natural_warning_steps']}
* First active-run warning step: {active['first_natural_warning_step']}
* Slowdown-active steps: {active['slowdown_active_steps']}
* First slowdown step: {active['first_slowdown_step']}
* Active scale range: [{active['min_scale_applied']}, {active['max_scale_applied']}]
* Wrapper-level command scaled: {active['wrapper_exec_command_scaled']}
* Release observed: {timing['release_observed']}
* `u_nom` modified: {active['u_nom_modified']}
* Internal `u_safe` modified: {active['u_safe_internal_modified']}"""
        if attempted
        else f"* Not attempted: {active['notes']}"
    )
    path.write_text(
        f"""# SAFC Fixed-Candidate Level-3B-Active C003 Notes

## Scope

This is a fixed-candidate targeted activation smoke. It tests warning-gated
slowdown activation on C003 only. It is not a benchmark and does not claim
performance improvement.

## Candidate Context

* C003
* flight trial 14
* selected because Level 3B-R reproduced H3 warning at step 60
* H3
* `dt_margin=0.0005`
* current official smoke wrapper
* `max_steps=100`

## No-Op Precheck

* Natural warning reproduced: {noop['confirmed_natural_warning']}
* Natural warning steps: {noop['natural_warning_steps']}
* First warning step: {noop['first_natural_warning_step']}
* Command modified: {noop['control_modified']}

## Active Slowdown Smoke

{active_text}

## Claim Boundaries

* Targeted activation only
* No full benchmark
* No performance improvement
* No collision reduction
* No warning reduction
* No planner integration
* No real-robot validation
* No global safety guarantee
* No new CBF theorem
""",
        encoding="utf-8",
    )


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description=(
            "SAFC fixed-C003 Level-3B-Active warning-gated slowdown smoke."
        )
    )
    parser.add_argument("--repo-root", type=Path, default=Path("."))
    parser.add_argument(
        "--output-dir",
        type=Path,
        default=Path(
            "work/risk_aware_cbf/results/"
            "safc_level3b_active_c003_slowdown"
        ),
    )
    parser.add_argument(
        "--mode",
        choices=(
            "noop-precheck-only",
            "active-only",
            "noop-precheck-then-active",
        ),
        default="noop-precheck-then-active",
    )
    parser.add_argument("--candidate-id", default=CANDIDATE_ID)
    parser.add_argument("--scene", default=SCENE)
    parser.add_argument("--trial-id", type=int, default=TRIAL_ID)
    parser.add_argument("--max-steps", type=int, default=100)
    parser.add_argument("--dt-margin", type=float, default=0.0005)
    parser.add_argument("--horizon", type=int, default=3)
    parser.add_argument(
        "--min-natural-warning-steps", type=int, default=1
    )
    parser.add_argument("--min-scale", type=float, default=0.25)
    parser.add_argument("--warning-scale", type=float, default=0.75)
    parser.add_argument(
        "--persistent-warning-scale", type=float, default=0.5
    )
    parser.add_argument(
        "--critical-warning-scale", type=float, default=0.25
    )
    parser.add_argument("--entrypoint", default="auto")
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
    if args.min_natural_warning_steps < 1:
        raise ValueError("min-natural-warning-steps must be positive")
    if not math.isfinite(args.dt_margin) or args.dt_margin <= 0.0:
        raise ValueError("dt-margin must be finite and positive")


def main() -> int:
    args = parse_args()
    validate_args(args)
    repo_root = args.repo_root.resolve()
    output_dir = args.output_dir.resolve()
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
            f"fixed smoke requires {ENTRYPOINT}, got {entrypoint}"
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

    noop_path = output_dir / "noop_precheck_summary.csv"
    noop_deltas = {"max_nom": 0.0, "max_safe": 0.0, "max_exec": 0.0}
    if args.mode == "active-only":
        noop = validate_existing_precheck(output_dir, args, entrypoint)
        if not parse_bool(noop["confirmed_natural_warning"]):
            raise RuntimeError(
                "active-only refused: Stage-A natural warning was not confirmed"
            )
    else:
        noop, noop_deltas = run_noop_precheck(
            wrapper, gsplat, dynamics, device, args
        )

    active_allowed = parse_bool(noop["confirmed_natural_warning"])
    active_deltas = {"max_nom": 0.0, "max_safe": 0.0, "max_exec": 0.0}
    timing_data = {
        "first_active_warning": None,
        "first_slowdown": None,
        "slowdown_after_or_at_warning": False,
        "release_observed": False,
    }
    should_attempt = (
        args.mode in {"active-only", "noop-precheck-then-active"}
        and active_allowed
    )
    if should_attempt:
        active, timing_data, active_deltas = run_active_slowdown(
            wrapper,
            gsplat,
            dynamics,
            device,
            args,
            policy_config,
        )
    elif args.mode == "noop-precheck-only":
        active = non_attempted_active(
            "No active run requested in noop-precheck-only mode."
        )
    else:
        active = non_attempted_active(
            "Stage-A natural warning gate did not pass; Stage B was not "
            "attempted."
        )

    timing = {
        "candidate_id": CANDIDATE_ID,
        "first_natural_warning_step_noop": noop[
            "first_natural_warning_step"
        ],
        "first_natural_warning_step_active": active[
            "first_natural_warning_step"
        ],
        "first_slowdown_step": active["first_slowdown_step"],
        "slowdown_after_or_at_warning": timing_data[
            "slowdown_after_or_at_warning"
        ],
        "slowdown_active_steps": active["slowdown_active_steps"],
        "release_observed": timing_data["release_observed"],
        "notes": (
            "Slowdown timing is evaluated against the natural warning in "
            "the active run."
        ),
    }
    max_nom = max(noop_deltas["max_nom"], active_deltas["max_nom"])
    max_safe = max(noop_deltas["max_safe"], active_deltas["max_safe"])
    max_exec = active_deltas["max_exec"]
    activation = parse_bool(active["activation_observed"])
    control_scope_passed = (
        max_nom == 0.0
        and max_safe == 0.0
        and parse_bool(active["command_modified_only_when_warning"])
        and ((activation and max_exec > 0.0) or not activation)
    )
    control = {
        "candidate_id": CANDIDATE_ID,
        "max_abs_delta_u_nom": max_nom,
        "max_abs_delta_u_safe_internal": max_safe,
        "max_abs_delta_wrapper_exec_due_to_slowdown": max_exec,
        "u_nom_modified": max_nom != 0.0,
        "u_safe_internal_modified": max_safe != 0.0,
        "wrapper_exec_command_scaled": active[
            "wrapper_exec_command_scaled"
        ],
        "command_modified_only_when_warning": active[
            "command_modified_only_when_warning"
        ],
        "control_scope_passed": control_scope_passed,
        "notes": (
            "Only wrapper-level u_exec may differ, and only under a "
            "natural warning gate."
        ),
    }
    claim_level = (
        "fixed_candidate_activation_smoke"
        if activation
        else (
            "fixed_candidate_active_no_activation"
            if should_attempt
            else "fixed_candidate_warning_not_reproduced"
        )
    )
    limitations = [
        "fixed-candidate targeted activation smoke only",
        "not full100",
        "not flight20",
        "not a benchmark comparison",
        "does not modify CBF-QP",
        "does not modify dynamics",
        "does not validate planner integration",
        "does not validate real-robot deployment",
        "does not prove performance improvement",
    ]
    if not active_allowed:
        limitations.append(
            "fixed candidate did not reproduce warning in precheck"
        )
    metrics = {
        "task": "SAFC Fixed-Candidate Level-3B-Active C003 Slowdown",
        "new_targeted_active_smoke_run": True,
        "active_feedback_policy": "warning_streak_slowdown",
        "candidate_id": CANDIDATE_ID,
        "scene": SCENE,
        "trial_id": TRIAL_ID,
        "selected_entrypoint": entrypoint,
        "max_steps": args.max_steps,
        "dt_margin": args.dt_margin,
        "horizon": args.horizon,
        "controller_modified": False,
        "official_core_source_modified": False,
        "cbf_splat_ellipsoids_dynamics_run_modified": False,
        "raw_traces_written": False,
        "noop_precheck_completed": True,
        "noop_steps_observed": int(noop["steps_observed"]),
        "noop_natural_warning_steps": int(noop["natural_warning_steps"]),
        "noop_first_natural_warning_step": (
            int(noop["first_natural_warning_step"])
            if str(noop["first_natural_warning_step"]).strip()
            else None
        ),
        "confirmed_natural_warning": active_allowed,
        "active_smoke_attempted": parse_bool(
            active["active_smoke_attempted"]
        ),
        "active_steps_observed": int(active["steps_observed"]),
        "active_natural_warning_steps": int(
            active["natural_warning_steps"]
        ),
        "active_first_natural_warning_step": (
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
        "activation_observed": activation,
        "slowdown_after_or_at_warning": parse_bool(
            timing["slowdown_after_or_at_warning"]
        ),
        "min_scale_applied": float(active["min_scale_applied"]),
        "max_scale_applied": float(active["max_scale_applied"]),
        "max_control_delta_from_slowdown": float(
            active["max_control_delta_from_slowdown"]
        ),
        "command_modified_only_when_warning": parse_bool(
            active["command_modified_only_when_warning"]
        ),
        "u_nom_modified": parse_bool(active["u_nom_modified"]),
        "u_safe_internal_modified": parse_bool(
            active["u_safe_internal_modified"]
        ),
        "wrapper_exec_command_scaled": parse_bool(
            active["wrapper_exec_command_scaled"]
        ),
        "collision_observed": parse_bool(active["collision_observed"]),
        "qp_infeasible_observed": parse_bool(
            active["qp_infeasible_observed"]
        ),
        "recovery_used_observed": parse_bool(
            active["recovery_used_observed"]
        ),
        "active_policy_effectiveness_claimed": False,
        "performance_improvement_claimed": False,
        "warning_reduction_claimed": False,
        "collision_reduction_claimed": False,
        "planner_improvement_claimed": False,
        "claim_level": claim_level,
        "limitations": limitations,
    }

    write_csv(
        output_dir / "fixed_candidate_context.csv",
        CONTEXT_FIELDS,
        [fixed_context(args, entrypoint)],
    )
    if args.mode != "active-only":
        write_csv(noop_path, NOOP_FIELDS, [noop])
    write_csv(
        output_dir / "active_slowdown_summary.csv",
        ACTIVE_FIELDS,
        [active],
    )
    write_csv(
        output_dir / "activation_timing_summary.csv",
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
    write_notes(output_dir / "active_c003_notes.md", noop, active, timing)
    print(json.dumps(metrics, indent=2))

    if activation and (
        not timing_data["slowdown_after_or_at_warning"]
        or not control_scope_passed
    ):
        return 2
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
