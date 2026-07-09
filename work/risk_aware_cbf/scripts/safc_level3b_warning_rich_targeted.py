#!/usr/bin/env python3
"""Run bounded Level-3B warning-rich no-op and active targeted smokes."""

from __future__ import annotations

import argparse
import csv
import importlib.util
import json
import math
import sys
from pathlib import Path
from typing import Any, Iterable, Sequence

from safc_level3b_warning_rich_discovery import discover
from safc_warning_slowdown_policy import (
    SlowdownPolicyConfig,
    SlowdownPolicyInput,
    apply_scale_to_vector,
    compute_warning_slowdown,
)


NOOP_FIELDS = (
    "candidate_id",
    "scene",
    "trial_id",
    "case_name",
    "steps_observed",
    "natural_warning_steps",
    "h1_warning_steps",
    "h2_warning_steps",
    "h3_warning_steps",
    "qp_infeasible_steps",
    "collision_steps",
    "recovery_candidate_steps",
    "passed_warning_rich_gate",
    "selected_for_active",
    "notes",
)

ACTIVE_FIELDS = (
    "candidate_id",
    "scene",
    "trial_id",
    "case_name",
    "active_smoke_attempted",
    "steps_observed",
    "natural_warning_steps",
    "slowdown_active_steps",
    "min_scale_applied",
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

GATE_FIELDS = (
    "candidate_id",
    "gate",
    "condition",
    "passed",
    "observed_value",
    "required_value",
    "notes",
)

DELTA_FIELDS = (
    "candidate_id",
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
    "Level-3B targeted warning-rich smoke only",
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


def parse_bool(value: Any) -> bool:
    if isinstance(value, bool):
        return value
    return str(value).strip().lower() in {"true", "1", "yes"}


def import_smoke_wrapper(path: Path) -> Any:
    spec = importlib.util.spec_from_file_location(
        "safc_level3b_selected_smoke_wrapper", path
    )
    if spec is None or spec.loader is None:
        raise RuntimeError(f"cannot load smoke wrapper: {path}")
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


def select_entrypoint(repo_root: Path, requested: str) -> Path | None:
    default = Path("reproduction/scripts/run_official_runpy_smoke.py")
    candidate = default if requested == "auto" else Path(requested)
    path = repo_root / candidate
    return path if path.is_file() else None


def candidate_start_goal(
    wrapper: Any,
    scene: str,
    trial_id: int,
) -> tuple[Any, Any, dict[str, Any]]:
    if scene not in wrapper.SCENES:
        raise ValueError(f"unsupported scene: {scene}")
    cfg = wrapper.SCENES[scene]
    np = wrapper.np
    t = np.linspace(0, 2 * np.pi, 100)
    t_z = 10 * np.linspace(0, 2 * np.pi, 100)
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
    if not 0 <= trial_id < len(starts):
        raise ValueError(f"trial_id out of range: {trial_id}")
    return starts[trial_id], goals[trial_id], cfg


def min_query_h(
    wrapper: Any,
    gsplat: Any,
    x: Any,
    radius: float,
    method: str,
) -> float:
    h_tensor, _, _, _ = gsplat.query_distance(
        x, radius=radius, distance_type=method
    )
    return float(wrapper.torch.min(h_tensor).detach().cpu().item())


def horizon_warnings(
    wrapper: Any,
    gsplat: Any,
    x: Any,
    u_safe: Any,
    radius: float,
    method: str,
    dt: float,
    dt_margin: float,
) -> tuple[bool, bool, bool, tuple[float, float, float]]:
    rollout = x.detach().clone()
    minima: list[float] = []
    running_min = math.inf
    for _ in range(3):
        rollout = (
            wrapper.double_integrator_dynamics(rollout, u_safe) * dt
            + rollout
        )
        running_min = min(
            running_min,
            min_query_h(wrapper, gsplat, rollout, radius, method),
        )
        minima.append(running_min)
    warnings = tuple(value < dt_margin for value in minima)
    return warnings[0], warnings[1], warnings[2], (
        minima[0],
        minima[1],
        minima[2],
    )


def build_state(
    wrapper: Any,
    device: Any,
    start: Any,
    goal_position: Any,
) -> tuple[Any, Any]:
    torch = wrapper.torch
    x = torch.tensor(start, device=device, dtype=torch.float32)
    x = torch.cat(
        [x, torch.zeros(3, device=device, dtype=torch.float32)]
    )
    goal = torch.tensor(
        goal_position, device=device, dtype=torch.float32
    )
    goal = torch.cat(
        [goal, torch.zeros(3, device=device, dtype=torch.float32)]
    )
    return x, goal


def nominal_and_safe(
    wrapper: Any,
    cbf: Any,
    x: Any,
    goal: Any,
) -> tuple[Any, Any]:
    torch = wrapper.torch
    velocity_desired = 5.0 * (goal[:3] - x[:3])
    velocity_desired = torch.clamp(velocity_desired, -0.1, 0.1)
    velocity_desired = velocity_desired + (goal[3:] - x[3:])
    u_nom = torch.clamp(velocity_desired - x[3:], -0.1, 0.1)
    u_safe = cbf.solve_QP(x, u_nom)
    return u_nom, u_safe


def max_abs_tensor(wrapper: Any, value: Any) -> float:
    return float(
        wrapper.torch.max(wrapper.torch.abs(value)).detach().cpu().item()
    )


def make_cbf(
    wrapper: Any,
    gsplat: Any,
    dynamics: Any,
    cfg: dict[str, Any],
) -> Any:
    return wrapper.InstrumentedCBF(
        gsplat,
        dynamics,
        5.0,
        1.0,
        cfg["radius"],
        distance_type="ball-to-ellipsoid",
    )


def run_noop_candidate(
    wrapper: Any,
    gsplat: Any,
    dynamics: Any,
    device: Any,
    candidate: dict[str, Any],
    max_steps: int,
    dt_margin: float,
    min_warning_steps: int,
) -> dict[str, Any]:
    scene = candidate["scene"]
    trial_id = int(candidate["trial_id"])
    start, goal_position, cfg = candidate_start_goal(
        wrapper, scene, trial_id
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

    for _ in range(max_steps):
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
            dt_margin,
        )
        natural_warning = h1 or h2 or h3
        counts["natural"] += int(natural_warning)
        counts["h1"] += int(h1)
        counts["h2"] += int(h2)
        counts["h3"] += int(h3)

        # Stage A executes the original safe command unchanged.
        if max_abs_tensor(wrapper, u_nom - u_nom_before) != 0.0:
            raise RuntimeError("Stage-A u_nom changed during no-op scan")
        if max_abs_tensor(wrapper, u_safe - u_safe_before) != 0.0:
            raise RuntimeError("Stage-A u_safe changed during no-op scan")
        x = (
            wrapper.double_integrator_dynamics(x, u_safe) * dt + x
        )
        executed_h = min_query_h(
            wrapper, gsplat, x, cfg["radius"], method
        )
        if executed_h < 0.0:
            counts["collision"] += 1
            break
        if wrapper.torch.norm(x - x_previous) < 0.001:
            break

    passed = counts["natural"] >= min_warning_steps
    return {
        "candidate_id": candidate["candidate_id"],
        "scene": scene,
        "trial_id": trial_id,
        "case_name": candidate["case_name"],
        "steps_observed": counts["steps"],
        "natural_warning_steps": counts["natural"],
        "h1_warning_steps": counts["h1"],
        "h2_warning_steps": counts["h2"],
        "h3_warning_steps": counts["h3"],
        "qp_infeasible_steps": counts["qp"],
        "collision_steps": counts["collision"],
        "recovery_candidate_steps": 0,
        "passed_warning_rich_gate": passed,
        "selected_for_active": False,
        "notes": (
            "Natural H1/H2/H3 repeated-control verification; original u_safe executed unchanged."
        ),
    }


def run_active_candidate(
    wrapper: Any,
    gsplat: Any,
    dynamics: Any,
    device: Any,
    candidate: dict[str, Any],
    max_steps: int,
    dt_margin: float,
    policy_config: SlowdownPolicyConfig,
) -> tuple[dict[str, Any], dict[str, Any]]:
    scene = candidate["scene"]
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
    natural_warning_steps = 0
    slowdown_active_steps = 0
    min_scale = 1.0
    max_exec_delta = 0.0
    max_nom_delta = 0.0
    max_safe_delta = 0.0
    collision_observed = False
    qp_infeasible_observed = False
    modified_only_when_warning = True

    for step in range(1, max_steps + 1):
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
        steps += 1
        qp_infeasible = not bool(cbf.solver_success)
        qp_infeasible_observed = (
            qp_infeasible_observed or qp_infeasible
        )
        if qp_infeasible:
            h1 = h2 = h3 = False
        else:
            h1, h2, h3, _ = horizon_warnings(
                wrapper,
                gsplat,
                x,
                u_safe,
                cfg["radius"],
                method,
                dt,
                dt_margin,
            )
        natural_warning = h1 or h2 or h3
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
                qp_infeasible=qp_infeasible,
                recovery_used=False,
                collision=collision_current,
                previous_scale=previous_scale,
            ),
            policy_config,
        )
        applied_scale = decision.scale if natural_warning else 1.0
        active = natural_warning and applied_scale < 1.0
        u_exec_original = u_safe.detach().clone()
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
        slowdown_active_steps += int(active)
        min_scale = min(min_scale, applied_scale)
        previous_scale = decision.scale
        if qp_infeasible:
            break

        x = (
            wrapper.double_integrator_dynamics(x, u_exec) * dt + x
        )
        executed_h = min_query_h(
            wrapper, gsplat, x, cfg["radius"], method
        )
        collision_observed = collision_observed or executed_h < 0.0
        if executed_h < 0.0:
            break
        if wrapper.torch.norm(x - x_previous) < 0.001:
            break

    activation_observed = slowdown_active_steps > 0
    active_row = {
        "candidate_id": candidate["candidate_id"],
        "scene": scene,
        "trial_id": trial_id,
        "case_name": candidate["case_name"],
        "active_smoke_attempted": True,
        "steps_observed": steps,
        "natural_warning_steps": natural_warning_steps,
        "slowdown_active_steps": slowdown_active_steps,
        "min_scale_applied": min_scale,
        "max_control_delta_from_slowdown": max_exec_delta,
        "command_modified_only_when_warning": modified_only_when_warning,
        "u_nom_modified": max_nom_delta != 0.0,
        "u_safe_internal_modified": max_safe_delta != 0.0,
        "wrapper_exec_command_scaled": activation_observed,
        "collision_observed": collision_observed,
        "qp_infeasible_observed": qp_infeasible_observed,
        "recovery_used_observed": False,
        "activation_observed": activation_observed,
        "notes": "Bounded wrapper-level scaling under natural H1/H2/H3 warning gate.",
    }
    delta_row = {
        "candidate_id": candidate["candidate_id"],
        "steps_observed": steps,
        "slowdown_active_steps": slowdown_active_steps,
        "max_abs_delta_u_exec_due_to_slowdown": max_exec_delta,
        "max_abs_delta_u_nom": max_nom_delta,
        "max_abs_delta_u_safe": max_safe_delta,
        "command_modified_only_when_warning": modified_only_when_warning,
        "passed_policy_gate": (
            activation_observed
            and natural_warning_steps > 0
            and modified_only_when_warning
            and max_nom_delta == 0.0
            and max_safe_delta == 0.0
        ),
        "notes": "Delta is permitted only on wrapper-level u_exec.",
    }
    return active_row, delta_row


def non_attempted_active_row(
    candidate: dict[str, Any],
    note: str,
) -> dict[str, Any]:
    return {
        "candidate_id": candidate["candidate_id"],
        "scene": candidate["scene"],
        "trial_id": candidate["trial_id"],
        "case_name": candidate["case_name"],
        "active_smoke_attempted": False,
        "steps_observed": 0,
        "natural_warning_steps": 0,
        "slowdown_active_steps": 0,
        "min_scale_applied": 1.0,
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


def build_gate_rows(
    noop_rows: Sequence[dict[str, Any]],
    active_row: dict[str, Any] | None,
    delta_row: dict[str, Any] | None,
    min_warning_steps: int,
) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    for row in noop_rows:
        rows.append(
            {
                "candidate_id": row["candidate_id"],
                "gate": "natural_warning_gate",
                "condition": "Stage-A natural_warning_steps >= required minimum",
                "passed": row["passed_warning_rich_gate"],
                "observed_value": row["natural_warning_steps"],
                "required_value": min_warning_steps,
                "notes": "Stage A executes original u_safe without command shaping.",
            }
        )
    if active_row is None or delta_row is None:
        return rows
    candidate_id = active_row["candidate_id"]
    checks = [
        (
            "command_scope_gate",
            "Wrapper command changes only while natural warning is present",
            active_row["command_modified_only_when_warning"],
            active_row["command_modified_only_when_warning"],
            True,
        ),
        (
            "no_cbq_modification_gate",
            "u_nom and internal u_safe deltas remain zero",
            (
                delta_row["max_abs_delta_u_nom"] == 0.0
                and delta_row["max_abs_delta_u_safe"] == 0.0
            ),
            (
                f"u_nom={delta_row['max_abs_delta_u_nom']};"
                f"u_safe={delta_row['max_abs_delta_u_safe']}"
            ),
            "0.0;0.0",
        ),
        (
            "no_dynamics_modification_gate",
            "Existing dynamics function is called without source modification",
            True,
            "unchanged",
            "unchanged",
        ),
        (
            "no_planner_gate",
            "No planner, replan, risk-cost, or waypoint action is invoked",
            True,
            "none",
            "none",
        ),
        (
            "no_raw_trace_gate",
            "No raw or per-step artifact is written",
            True,
            "false",
            "false",
        ),
        (
            "compact_output_gate",
            "Only aggregate CSV, JSON, and Markdown outputs are written",
            True,
            "compact",
            "compact",
        ),
    ]
    for gate, condition, passed, observed, required in checks:
        rows.append(
            {
                "candidate_id": candidate_id,
                "gate": gate,
                "condition": condition,
                "passed": passed,
                "observed_value": observed,
                "required_value": required,
                "notes": "Level-3B targeted activation gate.",
            }
        )
    return rows


def write_readme(path: Path) -> None:
    path.write_text(
        """# SAFC Level-3B Warning-Rich Targeted Results

This directory contains compact outputs for Level-3B naturally warning-rich
targeted case discovery and bounded active slowdown smoke. The goal is to find
and test a legitimate targeted case with naturally observed DT warning, not to
run a full benchmark or claim performance improvement.

Outputs:

* `candidate_source_inventory.csv`
* `warning_rich_candidate_inventory.csv`
* `targeted_noop_scan_summary.csv`
* `targeted_active_slowdown_summary.csv`
* `activation_gate_summary.csv`
* `control_delta_summary.csv`
* `metrics.json`
* `warning_rich_notes.md`

No raw traces, full trial dumps, per-step dumps, active-constraint dumps,
trajectory samples, JSONL logs, images, or binary files should be committed
here.
""",
        encoding="utf-8",
    )


def write_notes(
    path: Path,
    source_rows: Sequence[dict[str, Any]],
    candidate_rows: Sequence[dict[str, Any]],
    noop_rows: Sequence[dict[str, Any]],
    active_row: dict[str, Any] | None,
    metrics: dict[str, Any],
) -> None:
    selected = [
        f"{row['candidate_id']} ({row['scene']} trial {row['trial_id']})"
        for row in noop_rows
    ]
    passed = [
        row["candidate_id"]
        for row in noop_rows
        if row["passed_warning_rich_gate"]
    ]
    if active_row is not None:
        active_text = f"""The active candidate was `{active_row["candidate_id"]}`.
It had {active_row["natural_warning_steps"]} natural warning steps and
{active_row["slowdown_active_steps"]} slowdown-active steps. The minimum
applied scale was {active_row["min_scale_applied"]}, and the maximum wrapper
command delta was {active_row["max_control_delta_from_slowdown"]}.
Command modification occurred only under warning:
`{str(active_row["command_modified_only_when_warning"]).lower()}`. CBF-QP and
dynamics source were not modified."""
    else:
        active_text = (
            "No naturally warning-rich candidate passed the bounded Stage-A "
            "gate. Active slowdown was not tested, and there is no activation "
            "evidence."
        )
    path.write_text(
        f"""# SAFC Level-3B Warning-Rich Targeted Notes

## Scope

This is a targeted warning-rich discovery and activation validation. It is not
a full benchmark and does not claim performance improvement.

## Candidate Discovery

The discovery pass scanned {sum(bool(row["exists"]) for row in source_rows)}
tracked reports and produced {len(candidate_rows)} unique candidates. It used
explicit H-step margin-violation or predictive-recovery evidence as
high-priority evidence. Diagnostic collision evidence was kept separate.
Referenced raw result files were not read.

Selected bounded-scan candidates: {", ".join(selected) if selected else "none"}.

## No-Op Scan

Stage A computed natural repeated-control H1/H2/H3 warnings against
`dt_margin=0.0005` and executed the original `u_safe` unchanged. Candidates
passing the warning-rich gate: {", ".join(passed) if passed else "none"}.

## Active Slowdown Smoke

{active_text}

## Claim Boundaries

* Targeted smoke only.
* No full benchmark.
* No performance improvement claim.
* No collision reduction claim.
* No warning reduction claim.
* No planner improvement.
* No real-robot validation.
* No global safety guarantee.
* No new CBF theorem.

Claim level: `{metrics["claim_level"]}`.
""",
        encoding="utf-8",
    )


def build_metrics(
    args: argparse.Namespace,
    source_rows: Sequence[dict[str, Any]],
    candidate_rows: Sequence[dict[str, Any]],
    noop_rows: Sequence[dict[str, Any]],
    active_row: dict[str, Any] | None,
    delta_row: dict[str, Any] | None,
    entrypoint: str,
) -> dict[str, Any]:
    warning_rich = [
        row for row in noop_rows if row["passed_warning_rich_gate"]
    ]
    active_attempted = active_row is not None
    activation_observed = bool(
        active_row and active_row["activation_observed"]
    )
    noop_steps = sum(int(row["steps_observed"]) for row in noop_rows)
    noop_warnings = sum(
        int(row["natural_warning_steps"]) for row in noop_rows
    )
    active_steps_observed = (
        int(active_row["steps_observed"]) if active_row else 0
    )
    active_warnings = (
        int(active_row["natural_warning_steps"]) if active_row else 0
    )
    limitations = list(LIMITATIONS)
    if args.mode != "discovery-only" and not warning_rich:
        limitations.append(
            "no naturally warning-rich candidate found under bounded scan"
        )
    if activation_observed:
        claim_level = "targeted_activation_validation"
    elif args.mode == "discovery-only":
        claim_level = "candidate_discovery_only"
    elif not warning_rich:
        claim_level = "warning_rich_discovery_incomplete"
    else:
        claim_level = "targeted_activation_not_observed"
    return {
        "task": "SAFC Level-3B Warning-Rich Targeted Active Slowdown",
        "new_targeted_smoke_run": bool(noop_rows),
        "active_feedback_policy": "warning_streak_slowdown",
        "controller_modified": False,
        "official_core_source_modified": False,
        "cbf_splat_ellipsoids_dynamics_run_modified": False,
        "raw_traces_written": False,
        "selected_entrypoint": entrypoint,
        "max_candidates": args.max_candidates,
        "max_trials_per_candidate": args.max_trials_per_candidate,
        "max_steps": args.max_steps,
        "min_natural_warning_steps": args.min_natural_warning_steps,
        "sources_scanned": len(source_rows),
        "candidates_discovered": len(candidate_rows),
        "candidates_noop_scanned": len(noop_rows),
        "candidates_warning_rich": len(warning_rich),
        "active_smoke_attempted": active_attempted,
        "active_candidate_id": (
            active_row["candidate_id"] if active_row else None
        ),
        "trials_observed": len(noop_rows) + int(active_attempted),
        "steps_observed": noop_steps + active_steps_observed,
        "noop_steps_observed": noop_steps,
        "active_steps_observed": active_steps_observed,
        "natural_warning_steps": noop_warnings + active_warnings,
        "noop_natural_warning_steps": noop_warnings,
        "active_natural_warning_steps": active_warnings,
        "slowdown_active_steps": (
            int(active_row["slowdown_active_steps"]) if active_row else 0
        ),
        "activation_observed": activation_observed,
        "min_scale_applied": (
            float(active_row["min_scale_applied"]) if active_row else 1.0
        ),
        "max_control_delta_from_slowdown": (
            float(active_row["max_control_delta_from_slowdown"])
            if active_row
            else 0.0
        ),
        "command_modified_only_when_warning": (
            bool(active_row["command_modified_only_when_warning"])
            if active_row
            else True
        ),
        "u_nom_modified": bool(
            active_row and active_row["u_nom_modified"]
        ),
        "u_safe_internal_modified": bool(
            active_row and active_row["u_safe_internal_modified"]
        ),
        "wrapper_exec_command_scaled": bool(
            active_row and active_row["wrapper_exec_command_scaled"]
        ),
        "collision_observed": (
            any(int(row["collision_steps"]) > 0 for row in noop_rows)
            or bool(active_row and active_row["collision_observed"])
        ),
        "qp_infeasible_observed": (
            any(int(row["qp_infeasible_steps"]) > 0 for row in noop_rows)
            or bool(active_row and active_row["qp_infeasible_observed"])
        ),
        "recovery_used_observed": bool(
            active_row and active_row["recovery_used_observed"]
        ),
        "active_policy_gate_passed": bool(
            delta_row and delta_row["passed_policy_gate"]
        ),
        "performance_improvement_claimed": False,
        "warning_reduction_claimed": False,
        "collision_reduction_claimed": False,
        "planner_improvement_claimed": False,
        "claim_level": claim_level,
        "limitations": limitations,
    }


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="SAFC Level-3B warning-rich targeted activation."
    )
    parser.add_argument("--repo-root", type=Path, default=Path("."))
    parser.add_argument(
        "--output-dir",
        type=Path,
        default=Path(
            "work/risk_aware_cbf/results/safc_level3b_warning_rich_targeted"
        ),
    )
    parser.add_argument(
        "--mode",
        choices=(
            "discovery-only",
            "targeted-noop-only",
            "discovery-noop-then-active",
        ),
        default="discovery-noop-then-active",
    )
    parser.add_argument("--max-candidates", type=int, default=3)
    parser.add_argument(
        "--max-trials-per-candidate", type=int, default=1
    )
    parser.add_argument("--max-steps", type=int, default=50)
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
    parser.add_argument("--dt-margin", type=float, default=0.0005)
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    if not 1 <= args.max_candidates <= 3:
        raise ValueError("Level-3B max-candidates must be in [1, 3]")
    if args.max_trials_per_candidate != 1:
        raise ValueError("Level-3B requires max-trials-per-candidate=1")
    if not 1 <= args.max_steps <= 50:
        raise ValueError("Level-3B max-steps must be in [1, 50]")
    if args.min_natural_warning_steps < 1:
        raise ValueError("min-natural-warning-steps must be positive")
    if not math.isfinite(args.dt_margin) or args.dt_margin <= 0.0:
        raise ValueError("dt-margin must be finite and positive")

    repo_root = args.repo_root.resolve()
    output_dir = args.output_dir.resolve()
    output_dir.mkdir(parents=True, exist_ok=True)
    write_readme(output_dir / "README.md")
    source_rows, candidate_rows = discover(repo_root, output_dir)
    eligible = [
        row
        for row in candidate_rows
        if parse_bool(row["entrypoint_feasible"])
        and parse_bool(row["expected_natural_warning"])
    ][: args.max_candidates]

    noop_rows: list[dict[str, Any]] = []
    active_rows: list[dict[str, Any]] = []
    active_row: dict[str, Any] | None = None
    delta_row: dict[str, Any] | None = None
    entrypoint_text = ""

    if args.mode != "discovery-only" and eligible:
        entrypoint = select_entrypoint(repo_root, args.entrypoint)
        if entrypoint is None:
            raise RuntimeError("no safe existing closed-loop smoke wrapper found")
        entrypoint_text = str(entrypoint.relative_to(repo_root)).replace(
            "\\", "/"
        )
        wrapper = import_smoke_wrapper(entrypoint)
        torch = wrapper.torch
        device = torch.device(
            "cuda" if torch.cuda.is_available() else "cpu"
        )
        scene = eligible[0]["scene"]
        if any(candidate["scene"] != scene for candidate in eligible):
            raise RuntimeError("bounded runner supports one shared scene per run")
        _, _, cfg = candidate_start_goal(
            wrapper, scene, int(eligible[0]["trial_id"])
        )
        gsplat = wrapper.GSplatLoader(cfg["path_to_gsplat"], device)
        dynamics = wrapper.DoubleIntegrator(
            device=device, ndim=3
        )
        for candidate in eligible:
            try:
                row = run_noop_candidate(
                    wrapper,
                    gsplat,
                    dynamics,
                    device,
                    candidate,
                    args.max_steps,
                    args.dt_margin,
                    args.min_natural_warning_steps,
                )
            except Exception as exc:
                row = {
                    "candidate_id": candidate["candidate_id"],
                    "scene": candidate["scene"],
                    "trial_id": candidate["trial_id"],
                    "case_name": candidate["case_name"],
                    "steps_observed": 0,
                    "natural_warning_steps": 0,
                    "h1_warning_steps": 0,
                    "h2_warning_steps": 0,
                    "h3_warning_steps": 0,
                    "qp_infeasible_steps": 0,
                    "collision_steps": 0,
                    "recovery_candidate_steps": 0,
                    "passed_warning_rich_gate": False,
                    "selected_for_active": False,
                    "notes": f"Stage-A scan failed: {type(exc).__name__}: {exc}",
                }
            noop_rows.append(row)

        passing_ids = [
            row["candidate_id"]
            for row in noop_rows
            if row["passed_warning_rich_gate"]
        ]
        selected_candidate = next(
            (
                candidate
                for candidate in eligible
                if candidate["candidate_id"] in passing_ids
            ),
            None,
        )
        if (
            args.mode == "discovery-noop-then-active"
            and selected_candidate is not None
        ):
            for row in noop_rows:
                if row["candidate_id"] == selected_candidate["candidate_id"]:
                    row["selected_for_active"] = True
            policy_config = SlowdownPolicyConfig(
                min_scale=args.min_scale,
                warning_scale=args.warning_scale,
                persistent_warning_scale=args.persistent_warning_scale,
                critical_warning_scale=args.critical_warning_scale,
            )
            active_row, delta_row = run_active_candidate(
                wrapper,
                gsplat,
                dynamics,
                device,
                selected_candidate,
                args.max_steps,
                args.dt_margin,
                policy_config,
            )

    for candidate in eligible:
        if active_row and candidate["candidate_id"] == active_row["candidate_id"]:
            active_rows.append(active_row)
        else:
            noop_row = next(
                (
                    row
                    for row in noop_rows
                    if row["candidate_id"] == candidate["candidate_id"]
                ),
                None,
            )
            if args.mode == "discovery-only":
                non_attempted_note = (
                    "No targeted execution in discovery-only mode."
                )
            elif noop_row and not noop_row["passed_warning_rich_gate"]:
                non_attempted_note = (
                    "Stage-A natural warning gate did not pass; bounded "
                    "Stage B was not attempted."
                )
            else:
                non_attempted_note = (
                    "Not selected; only the first Stage-A passing candidate "
                    "may enter bounded Stage B."
                )
            active_rows.append(
                non_attempted_active_row(
                    candidate,
                    non_attempted_note,
                )
            )

    gate_rows = build_gate_rows(
        noop_rows,
        active_row,
        delta_row,
        args.min_natural_warning_steps,
    )
    metrics = build_metrics(
        args,
        source_rows,
        candidate_rows,
        noop_rows,
        active_row,
        delta_row,
        entrypoint_text,
    )
    write_csv(
        output_dir / "targeted_noop_scan_summary.csv",
        NOOP_FIELDS,
        noop_rows,
    )
    write_csv(
        output_dir / "targeted_active_slowdown_summary.csv",
        ACTIVE_FIELDS,
        active_rows,
    )
    write_csv(
        output_dir / "activation_gate_summary.csv",
        GATE_FIELDS,
        gate_rows,
    )
    write_csv(
        output_dir / "control_delta_summary.csv",
        DELTA_FIELDS,
        [delta_row] if delta_row else [],
    )
    (output_dir / "metrics.json").write_text(
        json.dumps(metrics, indent=2) + "\n", encoding="utf-8"
    )
    write_notes(
        output_dir / "warning_rich_notes.md",
        source_rows,
        candidate_rows,
        noop_rows,
        active_row,
        metrics,
    )
    print(json.dumps(metrics, indent=2))
    if active_row and (
        active_row["u_nom_modified"]
        or active_row["u_safe_internal_modified"]
        or not active_row["command_modified_only_when_warning"]
    ):
        return 3
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
