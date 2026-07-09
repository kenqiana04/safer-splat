#!/usr/bin/env python3
"""Run tiny no-op SAFC instrumentation around an existing smoke wrapper."""

from __future__ import annotations

import argparse
import csv
import importlib.util
import json
import sys
from collections import defaultdict
from dataclasses import asdict
from pathlib import Path
from typing import Any, Iterable, Sequence

from safc_noop_state_machine import (
    ClaimScope,
    FeedbackCandidate,
    SAFCDecision,
    SAFCEventSnapshot,
    SAFCState,
    decide_next_state,
)


ENTRYPOINT_FIELDS = (
    "entrypoint_id",
    "path",
    "entrypoint_type",
    "exists",
    "selected",
    "reason",
    "expected_scope",
    "modifies_control",
    "notes",
)

EQUIVALENCE_FIELDS = (
    "trial_id",
    "steps_observed",
    "equivalence_check_strength",
    "max_abs_delta_u_nom",
    "max_abs_delta_u_safe",
    "max_abs_delta_u_exec",
    "all_decisions_no_op",
    "any_modifies_control",
    "passed",
    "notes",
)

TRANSITION_FIELDS = (
    "from_state",
    "to_state",
    "count",
    "first_step",
    "last_step",
    "reason_codes",
    "claim_scopes",
    "notes",
)

FEEDBACK_FIELDS = (
    "feedback_candidate",
    "count",
    "first_step",
    "last_step",
    "claim_scopes",
    "modifies_control_any",
    "notes",
)

EVENT_SUMMARY_FIELDS = (
    "trial_id",
    "steps_observed",
    "dt_warning_steps",
    "recovery_candidate_steps",
    "safe_halt_candidate_steps",
    "replan_request_candidate_steps",
    "collision_steps",
    "qp_infeasible_steps",
    "notes",
)


def parse_bool(value: str) -> bool:
    normalized = value.strip().lower()
    if normalized in {"true", "1", "yes", "on"}:
        return True
    if normalized in {"false", "0", "no", "off"}:
        return False
    raise argparse.ArgumentTypeError(f"expected true/false, got {value!r}")


def write_csv(
    path: Path, fieldnames: Sequence[str], rows: Iterable[dict[str, Any]]
) -> None:
    with path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(rows)


def audit_entrypoints(repo_root: Path) -> list[dict[str, Any]]:
    candidates = [
        {
            "entrypoint_id": "EP001",
            "path": "reproduction/scripts/run_official_runpy_smoke.py",
            "entrypoint_type": "existing_smoke_wrapper",
            "reason": "Existing one-trial official smoke wrapper with bounded n_steps.",
            "expected_scope": "one official trajectory with configurable short step limit",
            "modifies_control": False,
            "notes": "Preferred; imported as a module so its raw-output main is not invoked.",
        },
        {
            "entrypoint_id": "EP002",
            "path": "run.py",
            "entrypoint_type": "official_run_entrypoint",
            "reason": "Official entrypoint has no short-run CLI and defaults to a 100-trajectory run.",
            "expected_scope": "full official run",
            "modifies_control": False,
            "notes": "Not selected and never edited.",
        },
        {
            "entrypoint_id": "EP003",
            "path": "work/risk_aware_cbf/scripts/run_v4c_hstep_predictive_recovery.py",
            "entrypoint_type": "report_referenced_command",
            "reason": "Referenced by tracked V4-C report.",
            "expected_scope": "V4-C recovery evaluation",
            "modifies_control": True,
            "notes": "Present on the execution host but unsuitable for no-op Level 2; not selected.",
        },
        {
            "entrypoint_id": "EP004",
            "path": "work/risk_aware_cbf/scripts/safc_level1_offline_reconstruction.py",
            "entrypoint_type": "unsuitable",
            "reason": "Tracked Level-1 analysis is offline and has no closed-loop execution.",
            "expected_scope": "report-level offline reconstruction",
            "modifies_control": False,
            "notes": "Not a Level-2 execution entrypoint.",
        },
        {
            "entrypoint_id": "EP005",
            "path": "reproduction/REPORT_OFFICIAL_RUN_SMOKE.md",
            "entrypoint_type": "report_referenced_command",
            "reason": "Documents the established one-trial smoke wrapper and environment.",
            "expected_scope": "textual smoke evidence",
            "modifies_control": False,
            "notes": "Evidence source, not executable.",
        },
    ]
    for candidate in candidates:
        candidate["exists"] = (repo_root / candidate["path"]).is_file()
        candidate["selected"] = False
    return candidates


def select_entrypoint(
    inventory: list[dict[str, Any]], requested: str
) -> dict[str, Any] | None:
    if requested == "auto":
        for item in inventory:
            if item["entrypoint_type"] == "existing_smoke_wrapper" and item["exists"]:
                item["selected"] = True
                return item
        return None
    for item in inventory:
        if item["path"] == requested and item["exists"]:
            item["selected"] = True
            return item
    return None


def import_smoke_wrapper(path: Path) -> Any:
    spec = importlib.util.spec_from_file_location("safc_selected_smoke_wrapper", path)
    if spec is None or spec.loader is None:
        raise RuntimeError(f"cannot load smoke wrapper: {path}")
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


def max_abs_delta(module: Any, before: Any, after: Any) -> float:
    if before.size == 0 and after.size == 0:
        return 0.0
    return float(module.np.max(module.np.abs(after - before)))


def decision_record(step: int, trial_id: str, decision: SAFCDecision) -> dict[str, Any]:
    record = asdict(decision)
    for key in ("from_state", "to_state", "feedback_candidate", "claim_scope"):
        value = record[key]
        record[key] = value.value if isinstance(value, (SAFCState, FeedbackCandidate, ClaimScope)) else value
    record["step"] = step
    record["trial_id"] = trial_id
    return record


def summarize_transitions(decisions: Sequence[dict[str, Any]]) -> list[dict[str, Any]]:
    groups: dict[tuple[str, str], list[dict[str, Any]]] = defaultdict(list)
    for decision in decisions:
        groups[(decision["from_state"], decision["to_state"])].append(decision)
    rows: list[dict[str, Any]] = []
    for (from_state, to_state), group in sorted(groups.items()):
        steps = [int(item["step"]) for item in group]
        rows.append(
            {
                "from_state": from_state,
                "to_state": to_state,
                "count": len(group),
                "first_step": min(steps),
                "last_step": max(steps),
                "reason_codes": ";".join(sorted({item["reason_code"] for item in group})),
                "claim_scopes": ";".join(sorted({item["claim_scope"] for item in group})),
                "notes": "Compact aggregate; no per-step timeline is committed.",
            }
        )
    return rows


def summarize_feedback(decisions: Sequence[dict[str, Any]]) -> list[dict[str, Any]]:
    groups: dict[str, list[dict[str, Any]]] = defaultdict(list)
    for decision in decisions:
        groups[decision["feedback_candidate"]].append(decision)
    rows: list[dict[str, Any]] = []
    for feedback, group in sorted(groups.items()):
        steps = [int(item["step"]) for item in group]
        rows.append(
            {
                "feedback_candidate": feedback,
                "count": len(group),
                "first_step": min(steps),
                "last_step": max(steps),
                "claim_scopes": ";".join(sorted({item["claim_scope"] for item in group})),
                "modifies_control_any": any(item["modifies_control"] for item in group),
                "notes": "Candidate logging only; no feedback action is executed.",
            }
        )
    return rows


def write_notes(
    path: Path,
    selected_entrypoint: str,
    completed: bool,
    equivalence_strength: str,
    max_deltas: dict[str, float | None],
    observed_states: Sequence[str],
    reason: str,
) -> None:
    state_text = ", ".join(observed_states) if observed_states else "none"
    path.write_text(
        f"""# SAFC Level-2 No-Op Instrumentation Notes

## Scope

This is Level-2 no-op closed-loop instrumentation. It inserts passive SAFC
state logging into a tiny smoke execution/evaluation path. It does not modify
executed controls and does not claim performance improvement.

## Entry Point

- Selected entrypoint: `{selected_entrypoint or "none"}`
- Instrumentation completed: `{str(completed).lower()}`
- Reason: {reason}

The selected existing wrapper is imported as a module. Its bounded scene and
core objects are reused, but its `main` function is not called because that
function writes a trajectory CSV and plot. Official source is not modified.

## No-Op Guarantee

The SAFC helper accepts only scalar/Boolean event snapshots and emits
supervisory decisions and candidates. It neither accepts nor returns action
vectors. The runner reads the original command variables before and after each
SAFC decision and executes the original baseline `u` variable.

## Equivalence Check

- Strength: `{equivalence_strength}`
- `max_abs_delta_u_nom`: `{max_deltas.get("u_nom")}`
- `max_abs_delta_u_safe`: `{max_deltas.get("u_safe")}`
- `max_abs_delta_u_exec`: `{max_deltas.get("u_exec")}`

The check is successful only when every delta is zero, every decision has
`no_op=true`, and no decision has `modifies_control=true`.

## Logged State Behavior

Observed states: {state_text}.

Only grouped transitions and candidate counts are committed. No per-step
timeline or full trial dump is written.

## Claim Boundaries

- No active feedback.
- No slowdown.
- No replanning.
- No planner improvement.
- No warning reduction claim.
- No collision reduction claim.
- No real-robot validation.
- No global safety guarantee.

## Limitations

- Tiny smoke only.
- Not full100.
- Not flight20.
- Not Level 3.
- Not an active policy.
- Not planner integration.
- Not real-robot deployment.
""",
        encoding="utf-8",
    )


def incomplete_outputs(
    output_dir: Path,
    inventory: Sequence[dict[str, Any]],
    args: argparse.Namespace,
    reason: str,
) -> dict[str, Any]:
    write_csv(output_dir / "entrypoint_inventory.csv", ENTRYPOINT_FIELDS, inventory)
    write_csv(
        output_dir / "noop_equivalence_summary.csv",
        EQUIVALENCE_FIELDS,
        [
            {
                "trial_id": "",
                "steps_observed": 0,
                "equivalence_check_strength": "incomplete",
                "max_abs_delta_u_nom": "",
                "max_abs_delta_u_safe": "",
                "max_abs_delta_u_exec": "",
                "all_decisions_no_op": False,
                "any_modifies_control": False,
                "passed": False,
                "notes": reason,
            }
        ],
    )
    write_csv(output_dir / "state_transition_summary.csv", TRANSITION_FIELDS, [])
    write_csv(output_dir / "feedback_candidate_summary.csv", FEEDBACK_FIELDS, [])
    write_csv(
        output_dir / "instrumentation_events_summary.csv",
        EVENT_SUMMARY_FIELDS,
        [],
    )
    metrics = {
        "task": "SAFC Level-2 No-Op Closed-Loop Instrumentation",
        "new_closed_loop_smoke_run": False,
        "max_trials": args.max_trials,
        "max_steps": args.max_steps,
        "controller_modified": False,
        "official_core_source_modified": False,
        "cbf_splat_ellipsoids_dynamics_run_modified": False,
        "raw_traces_written": False,
        "mode": args.mode,
        "instrumentation_completed": False,
        "entrypoint_selected": "",
        "trials_observed": 0,
        "steps_observed": 0,
        "safc_decisions_logged": 0,
        "state_transition_groups": 0,
        "feedback_candidate_groups": 0,
        "equivalence_check_strength": "incomplete",
        "max_abs_delta_u_nom": None,
        "max_abs_delta_u_safe": None,
        "max_abs_delta_u_exec": None,
        "all_decisions_no_op": False,
        "any_modifies_control": False,
        "noop_equivalence_passed": False,
        "dt_warning_steps_observed": 0,
        "recovery_candidate_steps_observed": 0,
        "safe_halt_candidate_steps_observed": 0,
        "replan_request_candidate_steps_observed": 0,
        "collision_steps_observed": 0,
        "qp_infeasible_steps_observed": 0,
        "limitations": [
            "Level-2 no-op instrumentation incomplete",
            reason,
            "does not modify control",
            "does not claim safety-performance improvement",
            "does not validate active feedback",
            "does not validate planner integration",
            "does not validate real-robot deployment",
        ],
    }
    (output_dir / "metrics.json").write_text(
        json.dumps(metrics, indent=2) + "\n", encoding="utf-8"
    )
    write_notes(
        output_dir / "instrumentation_notes.md",
        "",
        False,
        "incomplete",
        {"u_nom": None, "u_safe": None, "u_exec": None},
        [],
        reason,
    )
    return metrics


def run_tiny_smoke(
    repo_root: Path,
    selected: dict[str, Any],
    args: argparse.Namespace,
) -> tuple[
    dict[str, Any],
    list[dict[str, Any]],
    list[dict[str, Any]],
    list[dict[str, Any]],
    list[dict[str, Any]],
]:
    wrapper = import_smoke_wrapper(repo_root / selected["path"])
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
    x0 = np.stack(
        [
            cfg["radius_config"] * np.cos(t),
            cfg["radius_config"] * np.sin(t),
            cfg["radius_z"] * np.sin(t_z),
        ],
        axis=-1,
    ) + cfg["mean_config"]
    xf = np.stack(
        [
            cfg["radius_config"] * np.cos(t + np.pi),
            cfg["radius_config"] * np.sin(t + np.pi),
            cfg["radius_z"] * np.sin(t_z + np.pi),
        ],
        axis=-1,
    ) + cfg["mean_config"]

    gsplat = wrapper.GSplatLoader(cfg["path_to_gsplat"], device)
    dynamics = wrapper.DoubleIntegrator(device=device, ndim=3)

    all_decisions: list[dict[str, Any]] = []
    equivalence_rows: list[dict[str, Any]] = []
    event_rows: list[dict[str, Any]] = []
    global_deltas = {"u_nom": 0.0, "u_safe": 0.0, "u_exec": 0.0}

    for trial in range(args.max_trials):
        trial_id = f"{args.scene}_trial{trial}"
        start = x0[trial]
        goal_pos = xf[trial]
        x = torch.tensor(start, device=device, dtype=torch.float32)
        x = torch.cat([x, torch.zeros(3, device=device, dtype=torch.float32)])
        goal = torch.tensor(goal_pos, device=device, dtype=torch.float32)
        goal = torch.cat([goal, torch.zeros(3, device=device, dtype=torch.float32)])
        cbf = wrapper.InstrumentedCBF(
            gsplat,
            dynamics,
            alpha,
            beta,
            cfg["radius"],
            distance_type=method,
        )

        initial_h_tensor, _, _, _ = gsplat.query_distance(
            x, radius=cfg["radius"], distance_type=method
        )
        initial_h = float(torch.min(initial_h_tensor).detach().cpu().item())
        previous_state = SAFCState.S0_PreExecutionCertification
        warning_streak = 0
        clear_streak = 0
        recovery_streak = 0
        trial_decisions: list[dict[str, Any]] = []
        trial_deltas = {"u_nom": 0.0, "u_safe": 0.0, "u_exec": 0.0}
        dt_warning_steps = 0
        recovery_candidate_steps = 0
        safe_halt_steps = 0
        replan_steps = 0
        collision_steps = 0
        qp_infeasible_steps = 0
        initial_goal_distance = float(torch.norm(x[:3] - goal[:3]).detach().cpu())

        for step in range(1, args.max_steps + 1):
            x_prev = x.clone()
            vel_des = 5.0 * (goal[:3] - x[:3])
            vel_des = torch.clamp(vel_des, -0.1, 0.1)
            vel_des = vel_des + 1.0 * (goal[3:] - x[3:])
            u_nom = 1.0 * (vel_des - x[3:])
            u_nom = torch.clamp(u_nom, -0.1, 0.1)
            u_safe = cbf.solve_QP(x, u_nom)
            solver_success = bool(cbf.solver_success)
            qp_infeasible = not solver_success

            if solver_success:
                x_pred = wrapper.double_integrator_dynamics(x, u_safe) * dt + x
                h_tensor, _, _, _ = gsplat.query_distance(
                    x_pred, radius=cfg["radius"], distance_type=method
                )
                h_current = float(torch.min(h_tensor).detach().cpu().item())
                dt_warning = h_current < args.dt_margin
                collision = h_current < 0.0
            else:
                x_pred = x
                h_current = None
                dt_warning = False
                collision = False

            warning_streak = warning_streak + 1 if dt_warning else 0
            clear_streak = 0 if dt_warning else clear_streak + 1
            progress = 1.0 - (
                float(torch.norm(x[:3] - goal[:3]).detach().cpu())
                / max(initial_goal_distance, 1e-12)
            )

            snapshot = SAFCEventSnapshot(
                step=step,
                trial_id=trial_id,
                source=selected["path"],
                start_certified=(initial_h >= 0.0) if step == 1 else None,
                solver_success=solver_success,
                qp_infeasible=qp_infeasible,
                h_current=h_current,
                h1_warning=dt_warning,
                h2_warning=None,
                h3_warning=None,
                dt_warning_any=dt_warning,
                recovery_available=False,
                recovery_used=False,
                recovery_success=None,
                recovery_failed=False,
                collision=collision,
                progress=progress,
                pose_valid=True,
                map_frame_valid=True,
                command_adapter_valid=True,
            )

            u_exec = u_safe
            before = {
                "u_nom": u_nom.detach().cpu().numpy().copy(),
                "u_safe": u_safe.detach().cpu().numpy().copy(),
                "u_exec": u_exec.detach().cpu().numpy().copy(),
            }
            decision = decide_next_state(
                snapshot,
                previous_state,
                warning_streak,
                clear_streak,
                recovery_streak,
            )
            after = {
                "u_nom": u_nom.detach().cpu().numpy().copy(),
                "u_safe": u_safe.detach().cpu().numpy().copy(),
                "u_exec": u_exec.detach().cpu().numpy().copy(),
            }
            for name in trial_deltas:
                delta = max_abs_delta(wrapper, before[name], after[name])
                trial_deltas[name] = max(trial_deltas[name], delta)
                global_deltas[name] = max(global_deltas[name], delta)

            record = decision_record(step, trial_id, decision)
            trial_decisions.append(record)
            all_decisions.append(record)
            previous_state = decision.to_state

            dt_warning_steps += int(dt_warning)
            recovery_candidate_steps += int(
                decision.feedback_candidate
                == FeedbackCandidate.activate_recovery_candidate
            )
            safe_halt_steps += int(
                decision.feedback_candidate == FeedbackCandidate.safe_halt_candidate
            )
            replan_steps += int(
                decision.feedback_candidate == FeedbackCandidate.replan_request_candidate
            )
            collision_steps += int(collision)
            qp_infeasible_steps += int(qp_infeasible)

            if not solver_success:
                break

            # Execute the original baseline command variable, not a SAFC output.
            x = x_pred
            if torch.norm(x - x_prev) < 0.001:
                break

        all_noop = all(item["no_op"] for item in trial_decisions)
        any_modifies = any(item["modifies_control"] for item in trial_decisions)
        passed = (
            all_noop
            and not any_modifies
            and all(value == 0.0 for value in trial_deltas.values())
        )
        equivalence_rows.append(
            {
                "trial_id": trial_id,
                "steps_observed": len(trial_decisions),
                "equivalence_check_strength": "strong_action_delta_check",
                "max_abs_delta_u_nom": trial_deltas["u_nom"],
                "max_abs_delta_u_safe": trial_deltas["u_safe"],
                "max_abs_delta_u_exec": trial_deltas["u_exec"],
                "all_decisions_no_op": all_noop,
                "any_modifies_control": any_modifies,
                "passed": passed,
                "notes": "Before/after commands read from unchanged original variables around each passive decision.",
            }
        )
        event_rows.append(
            {
                "trial_id": trial_id,
                "steps_observed": len(trial_decisions),
                "dt_warning_steps": dt_warning_steps,
                "recovery_candidate_steps": recovery_candidate_steps,
                "safe_halt_candidate_steps": safe_halt_steps,
                "replan_request_candidate_steps": replan_steps,
                "collision_steps": collision_steps,
                "qp_infeasible_steps": qp_infeasible_steps,
                "notes": "Compact trial aggregate; no per-step trace is written.",
            }
        )

    transition_rows = summarize_transitions(all_decisions)
    feedback_rows = summarize_feedback(all_decisions)
    all_noop = all(item["no_op"] for item in all_decisions)
    any_modifies = any(item["modifies_control"] for item in all_decisions)
    equivalence_passed = (
        bool(all_decisions)
        and all_noop
        and not any_modifies
        and all(value == 0.0 for value in global_deltas.values())
        and all(row["passed"] for row in equivalence_rows)
    )
    metrics = {
        "task": "SAFC Level-2 No-Op Closed-Loop Instrumentation",
        "new_closed_loop_smoke_run": True,
        "max_trials": args.max_trials,
        "max_steps": args.max_steps,
        "controller_modified": False,
        "official_core_source_modified": False,
        "cbf_splat_ellipsoids_dynamics_run_modified": False,
        "raw_traces_written": False,
        "mode": args.mode,
        "instrumentation_completed": True,
        "entrypoint_selected": selected["path"],
        "scene": args.scene,
        "device": str(device),
        "trials_observed": len(equivalence_rows),
        "steps_observed": sum(row["steps_observed"] for row in equivalence_rows),
        "safc_decisions_logged": len(all_decisions),
        "state_transition_groups": len(transition_rows),
        "feedback_candidate_groups": len(feedback_rows),
        "equivalence_check_strength": "strong_action_delta_check",
        "max_abs_delta_u_nom": global_deltas["u_nom"],
        "max_abs_delta_u_safe": global_deltas["u_safe"],
        "max_abs_delta_u_exec": global_deltas["u_exec"],
        "all_decisions_no_op": all_noop,
        "any_modifies_control": any_modifies,
        "noop_equivalence_passed": equivalence_passed,
        "dt_warning_steps_observed": sum(row["dt_warning_steps"] for row in event_rows),
        "recovery_candidate_steps_observed": sum(
            row["recovery_candidate_steps"] for row in event_rows
        ),
        "safe_halt_candidate_steps_observed": sum(
            row["safe_halt_candidate_steps"] for row in event_rows
        ),
        "replan_request_candidate_steps_observed": sum(
            row["replan_request_candidate_steps"] for row in event_rows
        ),
        "collision_steps_observed": sum(row["collision_steps"] for row in event_rows),
        "qp_infeasible_steps_observed": sum(
            row["qp_infeasible_steps"] for row in event_rows
        ),
        "limitations": [
            "Level-2 no-op instrumentation only",
            "tiny smoke scope",
            "does not modify control",
            "does not claim safety-performance improvement",
            "does not validate active feedback",
            "does not validate planner integration",
            "does not validate real-robot deployment",
        ],
    }
    return metrics, equivalence_rows, transition_rows, feedback_rows, event_rows


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Tiny SAFC no-op closed-loop instrumentation smoke."
    )
    parser.add_argument("--repo-root", type=Path, default=Path("."))
    parser.add_argument(
        "--output-dir",
        type=Path,
        default=Path(
            "work/risk_aware_cbf/results/safc_level2_noop_instrumentation"
        ),
    )
    parser.add_argument("--max-trials", type=int, default=1)
    parser.add_argument("--max-steps", type=int, default=20)
    parser.add_argument("--mode", choices=("noop",), default="noop")
    parser.add_argument("--entrypoint", default="auto")
    parser.add_argument(
        "--dry-run-entrypoint-audit", type=parse_bool, default=False
    )
    parser.add_argument(
        "--allow-official-run-wrapper", type=parse_bool, default=False
    )
    parser.add_argument("--scene", default="stonehenge")
    parser.add_argument("--dt-margin", type=float, default=0.0005)
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    if args.max_trials < 1 or args.max_trials > 1:
        raise ValueError("Level-2 scope requires max-trials=1")
    if args.max_steps < 1 or args.max_steps > 20:
        raise ValueError("Level-2 scope requires max-steps in [1, 20]")

    repo_root = args.repo_root.resolve()
    output_dir = args.output_dir.resolve()
    output_dir.mkdir(parents=True, exist_ok=True)
    inventory = audit_entrypoints(repo_root)
    selected = select_entrypoint(inventory, args.entrypoint)
    write_csv(output_dir / "entrypoint_inventory.csv", ENTRYPOINT_FIELDS, inventory)

    if args.dry_run_entrypoint_audit:
        metrics = incomplete_outputs(
            output_dir, inventory, args, "entrypoint audit requested without execution"
        )
        print(json.dumps(metrics, indent=2))
        return 2
    if selected is None:
        metrics = incomplete_outputs(
            output_dir, inventory, args, "no safe existing closed-loop smoke wrapper found"
        )
        print(json.dumps(metrics, indent=2))
        return 2

    try:
        metrics, equivalence_rows, transition_rows, feedback_rows, event_rows = (
            run_tiny_smoke(repo_root, selected, args)
        )
    except Exception as exc:
        reason = f"selected smoke entrypoint failed: {type(exc).__name__}: {exc}"
        metrics = incomplete_outputs(output_dir, inventory, args, reason)
        print(json.dumps(metrics, indent=2))
        return 2
    write_csv(
        output_dir / "noop_equivalence_summary.csv",
        EQUIVALENCE_FIELDS,
        equivalence_rows,
    )
    write_csv(
        output_dir / "state_transition_summary.csv",
        TRANSITION_FIELDS,
        transition_rows,
    )
    write_csv(
        output_dir / "feedback_candidate_summary.csv",
        FEEDBACK_FIELDS,
        feedback_rows,
    )
    write_csv(
        output_dir / "instrumentation_events_summary.csv",
        EVENT_SUMMARY_FIELDS,
        event_rows,
    )
    (output_dir / "metrics.json").write_text(
        json.dumps(metrics, indent=2) + "\n", encoding="utf-8"
    )
    write_notes(
        output_dir / "instrumentation_notes.md",
        selected["path"],
        True,
        metrics["equivalence_check_strength"],
        {
            "u_nom": metrics["max_abs_delta_u_nom"],
            "u_safe": metrics["max_abs_delta_u_safe"],
            "u_exec": metrics["max_abs_delta_u_exec"],
        },
        sorted(
            {
                state
                for row in transition_rows
                for state in (row["from_state"], row["to_state"])
            }
        ),
        "Existing bounded official smoke wrapper imported successfully.",
    )
    print(json.dumps(metrics, indent=2))
    return 0 if metrics["noop_equivalence_passed"] else 3


if __name__ == "__main__":
    raise SystemExit(main())
