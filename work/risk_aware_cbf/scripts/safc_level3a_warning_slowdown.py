#!/usr/bin/env python3
"""Run the SAFC Level-3A policy harness and one bounded active smoke."""

from __future__ import annotations

import argparse
import csv
import importlib.util
import json
import math
import sys
from collections import defaultdict
from pathlib import Path
from typing import Any, Iterable, Sequence

from safc_warning_slowdown_policy import (
    SlowdownPolicyConfig,
    SlowdownPolicyInput,
    apply_scale_to_vector,
    compute_warning_slowdown,
)


POLICY_FIELDS = (
    "case_id",
    "dt_warning_any",
    "h1_warning",
    "h2_warning",
    "h3_warning",
    "warning_streak",
    "clear_streak",
    "previous_scale",
    "expected_active",
    "actual_active",
    "expected_scale_range",
    "actual_scale",
    "modifies_control",
    "bounded",
    "passed",
    "reason_code",
    "notes",
)

ACTIVE_SMOKE_FIELDS = (
    "trial_id",
    "steps_observed",
    "natural_warning_steps",
    "slowdown_active_steps",
    "min_scale_applied",
    "max_control_delta_from_slowdown",
    "collision_observed",
    "qp_infeasible_observed",
    "recovery_used_observed",
    "completed",
    "notes",
)

ACTIVATION_FIELDS = (
    "activation_type",
    "count",
    "first_step",
    "last_step",
    "min_scale",
    "max_scale",
    "claim_scope",
    "notes",
)

CONTROL_DELTA_FIELDS = (
    "trial_id",
    "steps_observed",
    "slowdown_active_steps",
    "max_abs_delta_u_exec_due_to_slowdown",
    "max_abs_delta_u_nom",
    "max_abs_delta_u_safe",
    "command_modified_only_when_warning",
    "passed_policy_gate",
    "notes",
)

LIMITATIONS = [
    "Level-3A minimal active feedback smoke only",
    "not full100",
    "not flight20",
    "not a benchmark comparison",
    "does not modify CBF-QP",
    "does not modify dynamics",
    "does not validate planner integration",
    "does not validate real-robot deployment",
    "does not prove performance improvement",
]


def write_csv(
    path: Path, fieldnames: Sequence[str], rows: Iterable[dict[str, Any]]
) -> None:
    with path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(rows)


def make_input(**overrides: Any) -> SlowdownPolicyInput:
    values: dict[str, Any] = {
        "step": 1,
        "warning_streak": 0,
        "clear_streak": 0,
        "dt_warning_any": False,
        "h1_warning": False,
        "h2_warning": False,
        "h3_warning": False,
        "qp_infeasible": False,
        "recovery_used": False,
        "collision": False,
        "previous_scale": 1.0,
    }
    values.update(overrides)
    return SlowdownPolicyInput(**values)


def run_policy_harness(
    config: SlowdownPolicyConfig,
) -> tuple[list[dict[str, Any]], bool]:
    def expected_ramp(current: float, target: float) -> float:
        delta = target - current
        if abs(delta) <= config.max_delta_scale_per_step:
            return target
        return current + math.copysign(
            config.max_delta_scale_per_step, delta
        )

    first_scale = expected_ramp(1.0, config.warning_scale)
    persistent_scale = expected_ramp(
        first_scale, config.persistent_warning_scale
    )
    critical_scale = expected_ramp(
        persistent_scale, config.critical_warning_scale
    )
    release_scale = expected_ramp(config.min_scale, 1.0)
    cases = [
        ("no_warning_clear", make_input(clear_streak=2), False, (1.0, 1.0)),
        (
            "first_H1_warning",
            make_input(
                dt_warning_any=True, h1_warning=True, warning_streak=1
            ),
            True,
            (first_scale, first_scale),
        ),
        (
            "persistent_H1_warning",
            make_input(
                dt_warning_any=True,
                h1_warning=True,
                warning_streak=2,
                previous_scale=first_scale,
            ),
            True,
            (persistent_scale, persistent_scale),
        ),
        (
            "H2_warning",
            make_input(
                dt_warning_any=True,
                h2_warning=True,
                warning_streak=1,
                previous_scale=first_scale,
            ),
            True,
            (persistent_scale, persistent_scale),
        ),
        (
            "H3_warning",
            make_input(
                dt_warning_any=True,
                h3_warning=True,
                warning_streak=1,
                previous_scale=persistent_scale,
            ),
            True,
            (critical_scale, critical_scale),
        ),
        (
            "critical_warning_streak",
            make_input(
                dt_warning_any=True,
                h1_warning=True,
                warning_streak=3,
                previous_scale=persistent_scale,
            ),
            True,
            (critical_scale, critical_scale),
        ),
        (
            "clear_release_step1",
            make_input(
                clear_streak=1, previous_scale=config.min_scale
            ),
            True,
            (config.min_scale, config.min_scale),
        ),
        (
            "clear_release_step2",
            make_input(
                clear_streak=2, previous_scale=config.min_scale
            ),
            True,
            (release_scale, release_scale),
        ),
        (
            "qp_infeasible_handoff",
            make_input(
                qp_infeasible=True, previous_scale=config.min_scale
            ),
            False,
            (1.0, 1.0),
        ),
        (
            "collision_handoff",
            make_input(
                collision=True, previous_scale=config.min_scale
            ),
            False,
            (1.0, 1.0),
        ),
    ]
    rows: list[dict[str, Any]] = []
    for case_id, policy_input, expected_active, expected_range in cases:
        decision = compute_warning_slowdown(policy_input, config)
        low, high = expected_range
        in_range = low - 1e-12 <= decision.scale <= high + 1e-12
        expected_modifies = expected_active and any(
            (
                policy_input.dt_warning_any,
                policy_input.h1_warning,
                policy_input.h2_warning,
                policy_input.h3_warning,
            )
        )
        passed = (
            decision.active == expected_active
            and in_range
            and decision.bounded
            and decision.modifies_control == expected_modifies
            and decision.claim_scope == "minimal_active_policy_smoke"
        )
        rows.append(
            {
                "case_id": case_id,
                "dt_warning_any": policy_input.dt_warning_any,
                "h1_warning": policy_input.h1_warning,
                "h2_warning": policy_input.h2_warning,
                "h3_warning": policy_input.h3_warning,
                "warning_streak": policy_input.warning_streak,
                "clear_streak": policy_input.clear_streak,
                "previous_scale": policy_input.previous_scale,
                "expected_active": expected_active,
                "actual_active": decision.active,
                "expected_scale_range": f"[{low:.6f},{high:.6f}]",
                "actual_scale": decision.scale,
                "modifies_control": decision.modifies_control,
                "bounded": decision.bounded,
                "passed": passed,
                "reason_code": decision.reason_code,
                "notes": decision.notes,
            }
        )
    return rows, all(row["passed"] for row in rows)


def select_entrypoint(repo_root: Path, requested: str) -> Path | None:
    default = Path("reproduction/scripts/run_official_runpy_smoke.py")
    candidate = default if requested == "auto" else Path(requested)
    path = repo_root / candidate
    return path if path.is_file() else None


def import_smoke_wrapper(path: Path) -> Any:
    spec = importlib.util.spec_from_file_location(
        "safc_level3a_selected_smoke_wrapper", path
    )
    if spec is None or spec.loader is None:
        raise RuntimeError(f"cannot load smoke wrapper: {path}")
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


def max_abs_tensor(torch: Any, value: Any) -> float:
    return float(torch.max(torch.abs(value)).detach().cpu().item())


def activation_type(reason_code: str) -> str:
    if reason_code == "H3_or_critical_warning_streak":
        return "H3_warning_slowdown"
    if reason_code == "H2_or_persistent_warning_streak":
        return "H2_warning_slowdown"
    if reason_code == "H1_or_warning_streak":
        return "H1_warning_slowdown"
    if reason_code == "clear_streak_release":
        return "release_to_nominal"
    if reason_code == "handoff_to_halt_or_recovery":
        return "handoff_to_recovery_or_halt"
    return "persistent_warning_slowdown"


def run_tiny_smoke(
    repo_root: Path,
    entrypoint: Path,
    args: argparse.Namespace,
    config: SlowdownPolicyConfig,
) -> tuple[
    list[dict[str, Any]],
    list[dict[str, Any]],
    list[dict[str, Any]],
    dict[str, Any],
]:
    wrapper = import_smoke_wrapper(entrypoint)
    if args.scene not in wrapper.SCENES:
        raise ValueError(f"scene not supported by selected wrapper: {args.scene}")

    cfg = wrapper.SCENES[args.scene]
    torch = wrapper.torch
    np = wrapper.np
    device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
    dt = 0.05
    alpha = 5.0
    beta = 1.0
    method = "ball-to-ellipsoid"
    n_configs = 100

    t = np.linspace(0, 2 * np.pi, n_configs)
    t_z = 10 * np.linspace(0, 2 * np.pi, n_configs)
    starts = np.stack(
        [
            cfg["radius_config"] * np.cos(t),
            cfg["radius_config"] * np.sin(t),
            cfg["radius_z"] * np.sin(t_z),
        ],
        axis=-1,
    ) + cfg["mean_config"]
    goals = np.stack(
        [
            cfg["radius_config"] * np.cos(t + np.pi),
            cfg["radius_config"] * np.sin(t + np.pi),
            cfg["radius_z"] * np.sin(t_z + np.pi),
        ],
        axis=-1,
    ) + cfg["mean_config"]

    gsplat = wrapper.GSplatLoader(cfg["path_to_gsplat"], device)
    dynamics = wrapper.DoubleIntegrator(device=device, ndim=3)
    smoke_rows: list[dict[str, Any]] = []
    delta_rows: list[dict[str, Any]] = []
    activation_events: list[dict[str, Any]] = []
    totals = {
        "steps_observed": 0,
        "natural_warning_steps": 0,
        "slowdown_active_steps": 0,
        "min_scale_applied": 1.0,
        "max_control_delta_from_slowdown": 0.0,
        "max_abs_delta_u_nom": 0.0,
        "max_abs_delta_u_safe": 0.0,
        "collision_observed": False,
        "qp_infeasible_observed": False,
        "recovery_used_observed": False,
        "command_modified_only_when_warning": True,
        "wrapper_exec_command_scaled": False,
        "device": str(device),
    }

    for trial in range(args.max_trials):
        trial_id = f"{args.scene}_trial{trial}"
        x = torch.tensor(
            starts[trial], device=device, dtype=torch.float32
        )
        x = torch.cat(
            [x, torch.zeros(3, device=device, dtype=torch.float32)]
        )
        goal = torch.tensor(
            goals[trial], device=device, dtype=torch.float32
        )
        goal = torch.cat(
            [goal, torch.zeros(3, device=device, dtype=torch.float32)]
        )
        cbf = wrapper.InstrumentedCBF(
            gsplat,
            dynamics,
            alpha,
            beta,
            cfg["radius"],
            distance_type=method,
        )
        warning_streak = 0
        clear_streak = 0
        previous_scale = 1.0
        trial_steps = 0
        warning_steps = 0
        active_steps = 0
        min_scale = 1.0
        max_exec_delta = 0.0
        max_nom_delta = 0.0
        max_safe_delta = 0.0
        collision_observed = False
        qp_infeasible_observed = False
        recovery_used_observed = False
        modified_step_warning_flags: list[bool] = []

        for step in range(1, args.max_steps + 1):
            x_prev = x.clone()
            current_h_tensor, _, _, _ = gsplat.query_distance(
                x, radius=cfg["radius"], distance_type=method
            )
            current_h = float(
                torch.min(current_h_tensor).detach().cpu().item()
            )
            collision_current = current_h < 0.0

            vel_des = 5.0 * (goal[:3] - x[:3])
            vel_des = torch.clamp(vel_des, -0.1, 0.1)
            vel_des = vel_des + (goal[3:] - x[3:])
            u_nom = torch.clamp(vel_des - x[3:], -0.1, 0.1)
            u_nom_before = u_nom.detach().clone()
            u_safe = cbf.solve_QP(x, u_nom)
            u_safe_before = u_safe.detach().clone()
            qp_infeasible = not bool(cbf.solver_success)

            if qp_infeasible:
                h_pred = None
                h1_warning = False
                h2_warning = False
                h3_warning = False
            else:
                x_pred = (
                    wrapper.double_integrator_dynamics(x, u_safe) * dt + x
                )
                h_pred_tensor, _, _, _ = gsplat.query_distance(
                    x_pred, radius=cfg["radius"], distance_type=method
                )
                h_pred = float(
                    torch.min(h_pred_tensor).detach().cpu().item()
                )
                h1_warning = h_pred < args.dt_margin
                h2_warning = h_pred < args.dt_margin * 0.5
                h3_warning = h_pred < args.dt_margin * 0.25

            natural_warning = any(
                (h1_warning, h2_warning, h3_warning)
            )
            warning_streak = warning_streak + 1 if natural_warning else 0
            clear_streak = 0 if natural_warning else clear_streak + 1
            decision = compute_warning_slowdown(
                SlowdownPolicyInput(
                    step=step,
                    warning_streak=warning_streak,
                    clear_streak=clear_streak,
                    dt_warning_any=natural_warning,
                    h1_warning=h1_warning,
                    h2_warning=h2_warning,
                    h3_warning=h3_warning,
                    qp_infeasible=qp_infeasible,
                    recovery_used=False,
                    collision=collision_current,
                    previous_scale=previous_scale,
                ),
                config,
            )

            # Command shaping is permitted only under a natural warning.
            applied_scale = decision.scale if natural_warning else 1.0
            active = natural_warning and applied_scale < 1.0
            u_exec_original = u_safe.detach().clone()
            u_exec = (
                apply_scale_to_vector(u_safe, applied_scale)
                if active
                else u_safe.detach().clone()
            )
            nom_delta = max_abs_tensor(torch, u_nom - u_nom_before)
            safe_delta = max_abs_tensor(torch, u_safe - u_safe_before)
            exec_delta = max_abs_tensor(
                torch, u_exec - u_exec_original
            )
            max_nom_delta = max(max_nom_delta, nom_delta)
            max_safe_delta = max(max_safe_delta, safe_delta)
            max_exec_delta = max(max_exec_delta, exec_delta)
            trial_steps += 1
            warning_steps += int(natural_warning)
            active_steps += int(active)
            min_scale = min(min_scale, applied_scale)
            if exec_delta > 1e-12:
                modified_step_warning_flags.append(natural_warning)
            if active:
                activation_events.append(
                    {
                        "type": activation_type(decision.reason_code),
                        "step": step,
                        "scale": applied_scale,
                    }
                )
            if decision.reason_code == "handoff_to_halt_or_recovery":
                activation_events.append(
                    {
                        "type": "handoff_to_recovery_or_halt",
                        "step": step,
                        "scale": 1.0,
                    }
                )

            previous_scale = decision.scale
            collision_observed = collision_observed or collision_current
            qp_infeasible_observed = (
                qp_infeasible_observed or qp_infeasible
            )
            if collision_current or qp_infeasible:
                break

            x = (
                wrapper.double_integrator_dynamics(x, u_exec) * dt + x
            )
            executed_h_tensor, _, _, _ = gsplat.query_distance(
                x, radius=cfg["radius"], distance_type=method
            )
            executed_h = float(
                torch.min(executed_h_tensor).detach().cpu().item()
            )
            collision_observed = collision_observed or executed_h < 0.0
            if executed_h < 0.0:
                break
            if torch.norm(x - x_prev) < 0.001:
                break

        command_gate = all(modified_step_warning_flags)
        passed_gate = (
            command_gate
            and max_nom_delta == 0.0
            and max_safe_delta == 0.0
            and (active_steps > 0 or max_exec_delta == 0.0)
        )
        smoke_rows.append(
            {
                "trial_id": trial_id,
                "steps_observed": trial_steps,
                "natural_warning_steps": warning_steps,
                "slowdown_active_steps": active_steps,
                "min_scale_applied": min_scale,
                "max_control_delta_from_slowdown": max_exec_delta,
                "collision_observed": collision_observed,
                "qp_infeasible_observed": qp_infeasible_observed,
                "recovery_used_observed": recovery_used_observed,
                "completed": True,
                "notes": "Compact trial aggregate; no per-step trace is written.",
            }
        )
        delta_rows.append(
            {
                "trial_id": trial_id,
                "steps_observed": trial_steps,
                "slowdown_active_steps": active_steps,
                "max_abs_delta_u_exec_due_to_slowdown": max_exec_delta,
                "max_abs_delta_u_nom": max_nom_delta,
                "max_abs_delta_u_safe": max_safe_delta,
                "command_modified_only_when_warning": command_gate,
                "passed_policy_gate": passed_gate,
                "notes": "Only the wrapper-level executed command may be scaled.",
            }
        )
        totals["steps_observed"] += trial_steps
        totals["natural_warning_steps"] += warning_steps
        totals["slowdown_active_steps"] += active_steps
        totals["min_scale_applied"] = min(
            totals["min_scale_applied"], min_scale
        )
        totals["max_control_delta_from_slowdown"] = max(
            totals["max_control_delta_from_slowdown"], max_exec_delta
        )
        totals["max_abs_delta_u_nom"] = max(
            totals["max_abs_delta_u_nom"], max_nom_delta
        )
        totals["max_abs_delta_u_safe"] = max(
            totals["max_abs_delta_u_safe"], max_safe_delta
        )
        totals["collision_observed"] = (
            totals["collision_observed"] or collision_observed
        )
        totals["qp_infeasible_observed"] = (
            totals["qp_infeasible_observed"] or qp_infeasible_observed
        )
        totals["recovery_used_observed"] = (
            totals["recovery_used_observed"] or recovery_used_observed
        )
        totals["command_modified_only_when_warning"] = (
            totals["command_modified_only_when_warning"] and command_gate
        )
        totals["wrapper_exec_command_scaled"] = (
            totals["wrapper_exec_command_scaled"] or active_steps > 0
        )

    if not activation_events:
        activation_rows = [
            {
                "activation_type": "no_activation_observed",
                "count": 1,
                "first_step": "",
                "last_step": "",
                "min_scale": 1.0,
                "max_scale": 1.0,
                "claim_scope": "tiny_smoke_observation_only",
                "notes": "No natural warning activated slowdown in this tiny smoke.",
            }
        ]
    else:
        grouped: dict[str, list[dict[str, Any]]] = defaultdict(list)
        for event in activation_events:
            grouped[event["type"]].append(event)
        activation_rows = []
        for kind, events in sorted(grouped.items()):
            activation_rows.append(
                {
                    "activation_type": kind,
                    "count": len(events),
                    "first_step": min(event["step"] for event in events),
                    "last_step": max(event["step"] for event in events),
                    "min_scale": min(event["scale"] for event in events),
                    "max_scale": max(event["scale"] for event in events),
                    "claim_scope": "minimal_active_policy_smoke",
                    "notes": "Compact activation aggregate from natural smoke events.",
                }
            )
    return smoke_rows, activation_rows, delta_rows, totals


def write_readme(path: Path) -> None:
    path.write_text(
        """# SAFC Level-3A Warning-Streak Slowdown Results

This directory contains compact outputs for a minimal active SAFC feedback
policy: warning-streak slowdown. The policy scales commands only when warning
conditions are present. This is a smoke-first validation, not a full benchmark
and not a planner integration experiment.

Outputs:

* `policy_logic_summary.csv`
* `active_smoke_summary.csv`
* `activation_summary.csv`
* `control_delta_summary.csv`
* `metrics.json`
* `slowdown_notes.md`

No raw traces, full trial dumps, per-step dumps, active-constraint dumps,
trajectory samples, JSONL logs, or binary files should be committed here.
""",
        encoding="utf-8",
    )


def write_notes(path: Path, metrics: dict[str, Any], config: SlowdownPolicyConfig) -> None:
    no_activation = not metrics["activation_observed"]
    no_activation_text = (
        "\n## If No Activation Observed\n\n"
        "The active slowdown policy was not exercised by natural warnings in "
        "this tiny smoke. The result validates policy harness logic and safe "
        "integration behavior, but not active-policy effectiveness.\n"
        if no_activation
        else ""
    )
    path.write_text(
        f"""# SAFC Level-3A Warning-Streak Slowdown Notes

## Scope

This is a minimal active feedback smoke. It tests a bounded warning-streak
slowdown policy. It is not a benchmark and does not claim safety-performance
improvement.

## Policy

The policy maps warning streaks and H1/H2/H3 warnings to bounded command
scales. Its minimum scale is `{config.min_scale}` and its maximum scale change
per step is `{config.max_delta_scale_per_step}`. Clear-step release hysteresis
is checked in the policy harness. The closed-loop gate applies command shaping
only while a natural warning is present. No planner is involved.

## Policy Harness

All `{metrics["policy_harness_cases"]}` synthetic logic cases passed:
`{str(metrics["policy_harness_passed"]).lower()}`.

## Closed-loop Smoke

* Selected entrypoint: `{metrics["entrypoint_selected"]}`
* Maximum trials: `{metrics["max_trials"]}`
* Maximum steps: `{metrics["max_steps"]}`
* Natural warning steps: `{metrics["natural_warning_steps"]}`
* Slowdown active steps: `{metrics["slowdown_active_steps"]}`
* Command changed only under warning: `{str(metrics["command_modified_only_when_warning"]).lower()}`

## Claim Boundaries

* No full benchmark.
* No comparison.
* No collision reduction claim.
* No warning reduction claim.
* No planner improvement.
* No real-robot validation.
* No global safety guarantee.
* No new CBF theorem.
{no_activation_text}""",
        encoding="utf-8",
    )


def build_metrics(
    args: argparse.Namespace,
    harness_rows: Sequence[dict[str, Any]],
    harness_passed: bool,
    entrypoint: str,
    smoke_rows: Sequence[dict[str, Any]],
    totals: dict[str, Any] | None,
    smoke_completed: bool,
    failure: str = "",
) -> dict[str, Any]:
    totals = totals or {
        "steps_observed": 0,
        "natural_warning_steps": 0,
        "slowdown_active_steps": 0,
        "min_scale_applied": 1.0,
        "max_control_delta_from_slowdown": 0.0,
        "collision_observed": False,
        "qp_infeasible_observed": False,
        "recovery_used_observed": False,
        "command_modified_only_when_warning": True,
        "wrapper_exec_command_scaled": False,
    }
    metrics = {
        "task": "SAFC Level-3A Warning-Streak Slowdown",
        "new_closed_loop_smoke_run": smoke_completed,
        "active_feedback_policy": "warning_streak_slowdown",
        "max_trials": args.max_trials,
        "max_steps": args.max_steps,
        "controller_modified": False,
        "official_core_source_modified": False,
        "cbf_splat_ellipsoids_dynamics_run_modified": False,
        "raw_traces_written": False,
        "policy_harness_completed": True,
        "policy_harness_cases": len(harness_rows),
        "policy_harness_passed": harness_passed,
        "smoke_completed": smoke_completed,
        "entrypoint_selected": entrypoint,
        "trials_observed": len(smoke_rows),
        "steps_observed": totals["steps_observed"],
        "natural_warning_steps": totals["natural_warning_steps"],
        "slowdown_active_steps": totals["slowdown_active_steps"],
        "min_scale_applied": totals["min_scale_applied"],
        "max_control_delta_from_slowdown": totals[
            "max_control_delta_from_slowdown"
        ],
        "command_modified_only_when_warning": totals[
            "command_modified_only_when_warning"
        ],
        "u_nom_modified": False,
        "u_safe_internal_modified": False,
        "wrapper_exec_command_scaled": totals[
            "wrapper_exec_command_scaled"
        ],
        "collision_observed": totals["collision_observed"],
        "qp_infeasible_observed": totals["qp_infeasible_observed"],
        "recovery_used_observed": totals["recovery_used_observed"],
        "activation_observed": totals["slowdown_active_steps"] > 0,
        "claim_level": "minimal_active_policy_smoke",
        "performance_improvement_claimed": False,
        "warning_reduction_claimed": False,
        "collision_reduction_claimed": False,
        "planner_improvement_claimed": False,
        "limitations": LIMITATIONS,
    }
    if failure:
        metrics["failure"] = failure
    return metrics


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="SAFC Level-3A warning-streak slowdown smoke."
    )
    parser.add_argument("--repo-root", type=Path, default=Path("."))
    parser.add_argument(
        "--output-dir",
        type=Path,
        default=Path(
            "work/risk_aware_cbf/results/safc_level3a_warning_slowdown"
        ),
    )
    parser.add_argument(
        "--mode",
        choices=(
            "policy-harness-only",
            "smoke-only",
            "policy-harness-and-smoke",
        ),
        default="policy-harness-and-smoke",
    )
    parser.add_argument("--min-scale", type=float, default=0.25)
    parser.add_argument("--warning-scale", type=float, default=0.75)
    parser.add_argument(
        "--persistent-warning-scale", type=float, default=0.5
    )
    parser.add_argument("--critical-warning-scale", type=float, default=0.25)
    parser.add_argument("--max-trials", type=int, default=1)
    parser.add_argument("--max-steps", type=int, default=20)
    parser.add_argument("--entrypoint", default="auto")
    parser.add_argument("--scene", default="stonehenge")
    parser.add_argument("--dt-margin", type=float, default=0.0005)
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    if args.max_trials != 1:
        raise ValueError("Level-3A scope requires max-trials=1")
    if not 1 <= args.max_steps <= 20:
        raise ValueError("Level-3A scope requires max-steps in [1, 20]")
    if not math.isfinite(args.dt_margin) or args.dt_margin <= 0.0:
        raise ValueError("dt-margin must be finite and positive")

    config = SlowdownPolicyConfig(
        min_scale=args.min_scale,
        warning_scale=args.warning_scale,
        persistent_warning_scale=args.persistent_warning_scale,
        critical_warning_scale=args.critical_warning_scale,
    )
    repo_root = args.repo_root.resolve()
    output_dir = args.output_dir.resolve()
    output_dir.mkdir(parents=True, exist_ok=True)
    write_readme(output_dir / "README.md")

    harness_rows, harness_passed = run_policy_harness(config)
    write_csv(
        output_dir / "policy_logic_summary.csv",
        POLICY_FIELDS,
        harness_rows,
    )
    if not harness_passed:
        metrics = build_metrics(
            args, harness_rows, False, "", [], None, False, "policy harness failed"
        )
        write_csv(
            output_dir / "active_smoke_summary.csv",
            ACTIVE_SMOKE_FIELDS,
            [],
        )
        write_csv(
            output_dir / "activation_summary.csv",
            ACTIVATION_FIELDS,
            [],
        )
        write_csv(
            output_dir / "control_delta_summary.csv",
            CONTROL_DELTA_FIELDS,
            [],
        )
        (output_dir / "metrics.json").write_text(
            json.dumps(metrics, indent=2) + "\n", encoding="utf-8"
        )
        write_notes(output_dir / "slowdown_notes.md", metrics, config)
        print(json.dumps(metrics, indent=2))
        return 2

    if args.mode == "policy-harness-only":
        metrics = build_metrics(
            args, harness_rows, True, "", [], None, False
        )
        (output_dir / "metrics.json").write_text(
            json.dumps(metrics, indent=2) + "\n", encoding="utf-8"
        )
        write_notes(output_dir / "slowdown_notes.md", metrics, config)
        print(json.dumps(metrics, indent=2))
        return 0

    entrypoint = select_entrypoint(repo_root, args.entrypoint)
    if entrypoint is None:
        failure = "no safe existing closed-loop smoke wrapper found"
        metrics = build_metrics(
            args, harness_rows, True, "", [], None, False, failure
        )
        print(json.dumps(metrics, indent=2))
        return 2
    entrypoint_text = str(entrypoint.relative_to(repo_root)).replace("\\", "/")
    try:
        smoke_rows, activation_rows, delta_rows, totals = run_tiny_smoke(
            repo_root, entrypoint, args, config
        )
    except Exception as exc:
        failure = f"tiny smoke failed: {type(exc).__name__}: {exc}"
        metrics = build_metrics(
            args,
            harness_rows,
            True,
            entrypoint_text,
            [],
            None,
            False,
            failure,
        )
        print(json.dumps(metrics, indent=2))
        return 2

    write_csv(
        output_dir / "active_smoke_summary.csv",
        ACTIVE_SMOKE_FIELDS,
        smoke_rows,
    )
    write_csv(
        output_dir / "activation_summary.csv",
        ACTIVATION_FIELDS,
        activation_rows,
    )
    write_csv(
        output_dir / "control_delta_summary.csv",
        CONTROL_DELTA_FIELDS,
        delta_rows,
    )
    metrics = build_metrics(
        args,
        harness_rows,
        True,
        entrypoint_text,
        smoke_rows,
        totals,
        True,
    )
    (output_dir / "metrics.json").write_text(
        json.dumps(metrics, indent=2) + "\n", encoding="utf-8"
    )
    write_notes(output_dir / "slowdown_notes.md", metrics, config)
    print(json.dumps(metrics, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
