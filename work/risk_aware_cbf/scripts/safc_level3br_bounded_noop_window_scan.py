#!/usr/bin/env python3
"""Run bounded no-op warning-window and diagnostic sensitivity scans."""

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
    import_smoke_wrapper,
    make_cbf,
    max_abs_tensor,
    min_query_h,
    nominal_and_safe,
    select_entrypoint,
)


WINDOW_FIELDS = (
    "candidate_id",
    "scene",
    "trial_id",
    "case_name",
    "steps_observed",
    "natural_warning_steps",
    "first_warning_step",
    "h1_warning_steps",
    "h2_warning_steps",
    "h3_warning_steps",
    "qp_infeasible_steps",
    "collision_steps",
    "recovery_used_steps",
    "u_nom_modified",
    "u_safe_modified",
    "control_modified",
    "warning_found",
    "notes",
)

SENSITIVITY_FIELDS = (
    "candidate_id",
    "scene",
    "trial_id",
    "dt_margin",
    "horizon",
    "steps_observed",
    "natural_warning_steps",
    "first_warning_step",
    "warning_found",
    "notes",
)

DIAGNOSIS_FIELDS = (
    "candidate_id",
    "report_warning_evidence",
    "first50_warning_found",
    "extended_window_warning_found",
    "sensitivity_warning_found",
    "most_likely_mismatch_reason",
    "reproduction_status",
    "next_required_context",
    "notes",
)

LIMITATIONS = [
    "bounded no-op reconciliation only",
    "not full100",
    "not flight20",
    "not a benchmark comparison",
    "does not execute active slowdown",
    "does not modify CBF-QP",
    "does not modify dynamics",
    "does not validate planner integration",
    "does not validate real-robot deployment",
    "does not prove performance improvement",
]


def write_csv(
    path: Path, fields: Sequence[str], rows: Iterable[dict[str, Any]]
) -> None:
    with path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=fields)
        writer.writeheader()
        writer.writerows(rows)


def load_csv(path: Path) -> list[dict[str, str]]:
    if not path.is_file():
        return []
    with path.open("r", encoding="utf-8", newline="") as handle:
        return list(csv.DictReader(handle))


def parse_bool(value: str) -> bool:
    normalized = value.strip().lower()
    if normalized in {"true", "1", "yes", "on"}:
        return True
    if normalized in {"false", "0", "no", "off"}:
        return False
    raise argparse.ArgumentTypeError(f"expected true/false, got {value!r}")


def parse_float_grid(value: str) -> list[float]:
    values = [float(item.strip()) for item in value.split(",") if item.strip()]
    if not values or not all(math.isfinite(item) and item > 0.0 for item in values):
        raise argparse.ArgumentTypeError("dt-margin-grid requires positive values")
    return sorted(set(values))


def parse_int_grid(value: str) -> list[int]:
    values = [int(item.strip()) for item in value.split(",") if item.strip()]
    if not values or any(item not in {1, 2, 3} for item in values):
        raise argparse.ArgumentTypeError("horizon-grid supports only 1,2,3")
    return sorted(set(values))


def rollout_minima(
    wrapper: Any,
    gsplat: Any,
    x: Any,
    u_safe: Any,
    radius: float,
    max_horizon: int,
) -> list[float]:
    rollout = x.detach().clone()
    minima: list[float] = []
    running_min = math.inf
    for _ in range(max_horizon):
        rollout = (
            wrapper.double_integrator_dynamics(rollout, u_safe) * 0.05
            + rollout
        )
        running_min = min(
            running_min,
            min_query_h(
                wrapper,
                gsplat,
                rollout,
                radius,
                "ball-to-ellipsoid",
            ),
        )
        minima.append(running_min)
    return minima


def run_candidate(
    wrapper: Any,
    gsplat: Any,
    dynamics: Any,
    device: Any,
    candidate: dict[str, str],
    max_steps: int,
    settings: Sequence[tuple[float, int]],
    default_margin: float,
) -> dict[str, Any]:
    scene = candidate["scene"]
    trial_id = int(candidate["trial_id"])
    start, goal_position, cfg = candidate_start_goal(
        wrapper, scene, trial_id
    )
    x, goal = build_state(wrapper, device, start, goal_position)
    cbf = make_cbf(wrapper, gsplat, dynamics, cfg)
    max_horizon = max(3, max(horizon for _, horizon in settings))
    stats = {
        setting: {"count": 0, "first": None} for setting in settings
    }
    h_counts = {1: 0, 2: 0, 3: 0}
    steps = 0
    qp_steps = 0
    collision_steps = 0
    max_nom_delta = 0.0
    max_safe_delta = 0.0
    max_control_delta = 0.0

    for step in range(1, max_steps + 1):
        x_previous = x.detach().clone()
        current_h = min_query_h(
            wrapper,
            gsplat,
            x,
            cfg["radius"],
            "ball-to-ellipsoid",
        )
        if current_h < 0.0:
            collision_steps += 1
            break
        u_nom, u_safe = nominal_and_safe(wrapper, cbf, x, goal)
        u_nom_before = u_nom.detach().clone()
        u_safe_before = u_safe.detach().clone()
        u_exec = u_safe.detach().clone()
        steps += 1
        if not bool(cbf.solver_success):
            qp_steps += 1
            break

        minima = rollout_minima(
            wrapper,
            gsplat,
            x,
            u_safe,
            cfg["radius"],
            max_horizon,
        )
        for horizon in (1, 2, 3):
            h_counts[horizon] += int(
                minima[horizon - 1] < default_margin
            )
        for setting in settings:
            margin, horizon = setting
            if minima[horizon - 1] < margin:
                stats[setting]["count"] += 1
                if stats[setting]["first"] is None:
                    stats[setting]["first"] = step

        max_nom_delta = max(
            max_nom_delta,
            max_abs_tensor(wrapper, u_nom - u_nom_before),
        )
        max_safe_delta = max(
            max_safe_delta,
            max_abs_tensor(wrapper, u_safe - u_safe_before),
        )
        max_control_delta = max(
            max_control_delta,
            max_abs_tensor(wrapper, u_exec - u_safe_before),
        )
        x = (
            wrapper.double_integrator_dynamics(x, u_exec) * 0.05 + x
        )
        executed_h = min_query_h(
            wrapper,
            gsplat,
            x,
            cfg["radius"],
            "ball-to-ellipsoid",
        )
        if executed_h < 0.0:
            collision_steps += 1
            break
        if wrapper.torch.norm(x - x_previous) < 0.001:
            break

    return {
        "candidate": candidate,
        "steps": steps,
        "stats": stats,
        "h_counts": h_counts,
        "qp_steps": qp_steps,
        "collision_steps": collision_steps,
        "max_nom_delta": max_nom_delta,
        "max_safe_delta": max_safe_delta,
        "max_control_delta": max_control_delta,
    }


def run_grid(
    repo_root: Path,
    candidates: Sequence[dict[str, str]],
    entrypoint_requested: str,
    max_steps: int,
    settings: Sequence[tuple[float, int]],
    default_margin: float,
) -> tuple[list[dict[str, Any]], str]:
    entrypoint = select_entrypoint(repo_root, entrypoint_requested)
    if entrypoint is None:
        raise RuntimeError("no safe existing closed-loop smoke wrapper found")
    wrapper = import_smoke_wrapper(entrypoint)
    device = wrapper.torch.device(
        "cuda" if wrapper.torch.cuda.is_available() else "cpu"
    )
    scenes = {candidate["scene"] for candidate in candidates}
    if scenes != {"flight"}:
        raise RuntimeError(f"expected only flight candidates, got {scenes}")
    _, _, cfg = candidate_start_goal(
        wrapper, "flight", int(candidates[0]["trial_id"])
    )
    gsplat = wrapper.GSplatLoader(cfg["path_to_gsplat"], device)
    dynamics = wrapper.DoubleIntegrator(device=device, ndim=3)
    results = [
        run_candidate(
            wrapper,
            gsplat,
            dynamics,
            device,
            candidate,
            max_steps,
            settings,
            default_margin,
        )
        for candidate in candidates
    ]
    return results, str(entrypoint.relative_to(repo_root)).replace("\\", "/")


def window_rows(
    results: Sequence[dict[str, Any]],
    margin: float,
    horizon: int,
) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    for result in results:
        candidate = result["candidate"]
        selected = result["stats"][(margin, horizon)]
        modified = (
            result["max_nom_delta"] != 0.0
            or result["max_safe_delta"] != 0.0
            or result["max_control_delta"] != 0.0
        )
        rows.append(
            {
                "candidate_id": candidate["candidate_id"],
                "scene": candidate["scene"],
                "trial_id": candidate["trial_id"],
                "case_name": candidate["case_name"],
                "steps_observed": result["steps"],
                "natural_warning_steps": selected["count"],
                "first_warning_step": (
                    selected["first"]
                    if selected["first"] is not None
                    else ""
                ),
                "h1_warning_steps": result["h_counts"][1],
                "h2_warning_steps": result["h_counts"][2],
                "h3_warning_steps": result["h_counts"][3],
                "qp_infeasible_steps": result["qp_steps"],
                "collision_steps": result["collision_steps"],
                "recovery_used_steps": 0,
                "u_nom_modified": result["max_nom_delta"] != 0.0,
                "u_safe_modified": result["max_safe_delta"] != 0.0,
                "control_modified": modified,
                "warning_found": selected["count"] > 0,
                "notes": (
                    "Extended-window no-op audit; original u_safe executed unchanged."
                ),
            }
        )
    return rows


def sensitivity_rows(
    results: Sequence[dict[str, Any]],
    settings: Sequence[tuple[float, int]],
) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    for result in results:
        candidate = result["candidate"]
        for margin, horizon in settings:
            selected = result["stats"][(margin, horizon)]
            rows.append(
                {
                    "candidate_id": candidate["candidate_id"],
                    "scene": candidate["scene"],
                    "trial_id": candidate["trial_id"],
                    "dt_margin": margin,
                    "horizon": horizon,
                    "steps_observed": result["steps"],
                    "natural_warning_steps": selected["count"],
                    "first_warning_step": (
                        selected["first"]
                        if selected["first"] is not None
                        else ""
                    ),
                    "warning_found": selected["count"] > 0,
                    "notes": (
                        "Diagnostic sensitivity on one no-op trajectory; not benchmark tuning."
                    ),
                }
            )
    return rows


def truth(value: Any) -> bool:
    return str(value).strip().lower() in {"true", "1", "yes"}


def build_diagnosis(
    candidates: Sequence[dict[str, str]],
    first50_rows: Sequence[dict[str, str]],
    window_scan_rows: Sequence[dict[str, str]],
    sensitivity_scan_rows: Sequence[dict[str, str]],
    reconciliation_rows: Sequence[dict[str, str]],
) -> list[dict[str, Any]]:
    first50 = {row["candidate_id"]: row for row in first50_rows}
    extended = {row["candidate_id"]: row for row in window_scan_rows}
    reconciliation = {
        row["candidate_id"]: row for row in reconciliation_rows
    }
    sensitivity_ids = {
        row["candidate_id"]
        for row in sensitivity_scan_rows
        if truth(row["warning_found"])
    }
    rows: list[dict[str, Any]] = []
    for candidate in candidates:
        candidate_id = candidate["candidate_id"]
        first_found = (
            int(first50.get(candidate_id, {}).get("natural_warning_steps", 0))
            > 0
        )
        extended_found = truth(
            extended.get(candidate_id, {}).get("warning_found", False)
        )
        sensitivity_found = candidate_id in sensitivity_ids
        context = reconciliation.get(candidate_id, {})
        if extended_found:
            reason = "step_window_too_short"
            status = "reproduced_in_extended_window"
            next_context = (
                "fix this candidate and exact default no-op context for a "
                "separate Level 3B-Active smoke"
            )
        elif sensitivity_found:
            reason = "dt_margin_horizon_mismatch"
            status = "reproduced_only_under_sensitivity_setting"
            next_context = (
                "need the exact report dt_margin and horizon before active testing"
            )
        elif not truth(context.get("report_context_complete", False)):
            reason = context.get(
                "likely_mismatch_reason", "report_context_insufficient"
            )
            status = "insufficient_context"
            next_context = context.get(
                "recommended_next_scan",
                "need original V4-C execution context",
            )
        else:
            reason = "unknown"
            status = "not_reproduced"
            next_context = "need tracked compact per-event summary"
        rows.append(
            {
                "candidate_id": candidate_id,
                "report_warning_evidence": candidate[
                    "warning_evidence_text"
                ],
                "first50_warning_found": first_found,
                "extended_window_warning_found": extended_found,
                "sensitivity_warning_found": sensitivity_found,
                "most_likely_mismatch_reason": reason,
                "reproduction_status": status,
                "next_required_context": next_context,
                "notes": (
                    "Report evidence and current wrapper identifiers were "
                    "reconciled without reading raw traces."
                ),
            }
        )
    return rows


def best_reproduction(
    window_rows_data: Sequence[dict[str, str]],
    sensitivity_data: Sequence[dict[str, str]],
) -> tuple[str | None, int | None]:
    default_hits = [
        row for row in window_rows_data if truth(row["warning_found"])
    ]
    if default_hits:
        best = min(
            default_hits,
            key=lambda row: int(row["first_warning_step"]),
        )
        return best["candidate_id"], int(best["first_warning_step"])
    sensitivity_hits = [
        row for row in sensitivity_data if truth(row["warning_found"])
    ]
    if sensitivity_hits:
        best = min(
            sensitivity_hits,
            key=lambda row: (
                int(row["first_warning_step"]),
                abs(float(row["dt_margin"]) - 0.0005),
                abs(int(row["horizon"]) - 3),
            ),
        )
        return best["candidate_id"], int(best["first_warning_step"])
    return None, None


def build_metrics(
    args: argparse.Namespace,
    report_rows: Sequence[dict[str, str]],
    reconciliation_rows: Sequence[dict[str, str]],
    window_scan_rows: Sequence[dict[str, str]],
    sensitivity_scan_rows: Sequence[dict[str, str]],
    diagnosis_rows: Sequence[dict[str, Any]],
    entrypoint: str,
) -> dict[str, Any]:
    extended_ids = {
        row["candidate_id"]
        for row in window_scan_rows
        if truth(row["warning_found"])
    }
    sensitivity_ids = {
        row["candidate_id"]
        for row in sensitivity_scan_rows
        if truth(row["warning_found"])
    }
    all_candidate_ids = {
        row["candidate_id"] for row in reconciliation_rows
    }
    not_reproduced = all_candidate_ids - extended_ids - sensitivity_ids
    insufficient = {
        row["candidate_id"]
        for row in reconciliation_rows
        if not truth(row["report_context_complete"])
    }
    best_id, best_step = best_reproduction(
        window_scan_rows, sensitivity_scan_rows
    )
    return {
        "task": "SAFC Level-3B-R Warning Evidence Reproduction Reconciliation",
        "new_bounded_noop_scans_run": bool(window_scan_rows),
        "active_feedback_run": False,
        "active_slowdown_run": False,
        "controller_modified": False,
        "official_core_source_modified": False,
        "cbf_splat_ellipsoids_dynamics_run_modified": False,
        "raw_traces_written": False,
        "selected_entrypoint": entrypoint,
        "sources_scanned": len(report_rows),
        "candidates_reconciled": len(reconciliation_rows),
        "candidates_window_scanned": len(window_scan_rows),
        "max_steps": args.max_steps,
        "dt_margin_default": 0.0005,
        "horizon_default": 3,
        "extended_window_warning_candidates": len(extended_ids),
        "sensitivity_warning_candidates": len(sensitivity_ids),
        "not_reproduced_candidates": len(not_reproduced),
        "insufficient_context_candidates": len(insufficient),
        "any_warning_reproduced": bool(extended_ids or sensitivity_ids),
        "best_reproduced_candidate_id": best_id,
        "best_reproduced_first_warning_step": best_step,
        "active_policy_effectiveness_claimed": False,
        "performance_improvement_claimed": False,
        "warning_reduction_claimed": False,
        "collision_reduction_claimed": False,
        "planner_improvement_claimed": False,
        "claim_level": "warning_evidence_reconciliation",
        "limitations": LIMITATIONS,
    }


def write_readme(path: Path) -> None:
    path.write_text(
        """# SAFC Level-3B-R Warning Evidence Reconciliation Results

This directory contains compact outputs for reconciling report-derived warning
evidence with executable no-op scan contexts. The goal is to identify why
warning/recovery evidence from tracked reports did not reproduce in Level-3B
bounded scans, not to test active slowdown or claim performance improvement.

Outputs:

* `report_context_inventory.csv`
* `candidate_context_reconciliation.csv`
* `bounded_noop_window_scan_summary.csv`
* `dt_margin_horizon_sensitivity_summary.csv`
* `mismatch_diagnosis_summary.csv`
* `metrics.json`
* `warning_reconciliation_notes.md`

No raw traces, full trial dumps, per-step dumps, active-constraint dumps,
trajectory samples, JSONL logs, images, or binary files should be committed
here.
""",
        encoding="utf-8",
    )


def write_notes(
    path: Path,
    report_rows: Sequence[dict[str, str]],
    reconciliation_rows: Sequence[dict[str, str]],
    window_rows_data: Sequence[dict[str, str]],
    sensitivity_data: Sequence[dict[str, str]],
    diagnosis_rows: Sequence[dict[str, Any]],
    metrics: dict[str, Any],
    margin_grid: Sequence[float],
    horizon_grid: Sequence[int],
) -> None:
    reasons = sorted(
        {row["most_likely_mismatch_reason"] for row in diagnosis_rows}
    )
    path.write_text(
        f"""# SAFC Level-3B-R Warning Evidence Reconciliation Notes

## Scope

This is warning evidence reproduction reconciliation. It does not run active
slowdown and does not claim performance improvement.

## Report-Derived Warning Evidence

The audit scanned {len(report_rows)} tracked reports and reconciled
{len(reconciliation_rows)} candidates. It extracted scene, trial, horizon,
margin, controller, recovery, trajectory, window, and checkpoint context where
the reports stated them. Exact first-warning steps, checkpoints, and executed
start-state history were commonly missing. No raw trace was read.

## Context Reconciliation

Scene and trial identifiers match the current wrapper candidates, but the main
warning reports use Risk-Aware V1, V4-C recovery-enabled trajectories, or
post-repair contexts. The current scan uses official CBF command construction,
recovery disabled, original generated starts/goals, and an independent no-op
trajectory. All {metrics["insufficient_context_candidates"]} candidates retain
at least one unresolved report-context field.

## Bounded No-Op Window Scan

The scan covered {len(window_rows_data)} candidates for at most
{metrics["max_steps"]} steps with `dt_margin=0.0005` and H3. Warnings outside
the first 50 were found for {metrics["extended_window_warning_candidates"]}
candidates. No command, `u_nom`, or internal `u_safe` modification was allowed.

## DT Margin / Horizon Sensitivity

The diagnostic grid was margins {",".join(str(value) for value in margin_grid)}
and horizons {",".join(str(value) for value in horizon_grid)}. Warnings appeared
for {metrics["sensitivity_warning_candidates"]} candidates under at least one
grid setting. Each candidate used one no-op trajectory while all grid counters
were accumulated; this is context sensitivity analysis, not benchmark tuning.

## Mismatch Diagnosis

Most likely reasons: {", ".join(reasons) if reasons else "none"}. The diagnosis
keeps extended-window reproduction separate from sensitivity-only warning
evidence and unresolved report context.

## Claim Boundaries

* No active feedback.
* No slowdown execution.
* No performance improvement.
* No collision reduction.
* No warning reduction.
* No planner integration.
* No real-robot validation.
* No global safety guarantee.
* No new CBF theorem.
""",
        encoding="utf-8",
    )


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="SAFC Level-3B-R bounded no-op warning reconciliation."
    )
    parser.add_argument("--repo-root", type=Path, default=Path("."))
    parser.add_argument(
        "--output-dir",
        type=Path,
        default=Path(
            "work/risk_aware_cbf/results/safc_level3br_warning_reconciliation"
        ),
    )
    parser.add_argument("--max-candidates", type=int, default=7)
    parser.add_argument(
        "--max-trials-per-candidate", type=int, default=1
    )
    parser.add_argument("--max-steps", type=int, default=200)
    parser.add_argument("--dt-margin", type=float, default=0.0005)
    parser.add_argument("--horizon", type=int, default=3)
    parser.add_argument(
        "--dt-margin-grid",
        type=parse_float_grid,
        default=parse_float_grid("0.0001,0.0005,0.001"),
    )
    parser.add_argument(
        "--horizon-grid",
        type=parse_int_grid,
        default=parse_int_grid("1,2,3"),
    )
    parser.add_argument("--entrypoint", default="auto")
    parser.add_argument("--candidate-inventory", type=Path)
    parser.add_argument("--first50-summary", type=Path)
    parser.add_argument(
        "--sensitivity-only", type=parse_bool, default=False
    )
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    if not 1 <= args.max_candidates <= 7:
        raise ValueError("max-candidates must be in [1, 7]")
    if args.max_trials_per_candidate != 1:
        raise ValueError("max-trials-per-candidate must be 1")
    if not 1 <= args.max_steps <= 200:
        raise ValueError("max-steps must be in [1, 200]")
    if args.horizon not in {1, 2, 3}:
        raise ValueError("horizon must be 1, 2, or 3")
    if not math.isfinite(args.dt_margin) or args.dt_margin <= 0.0:
        raise ValueError("dt-margin must be finite and positive")

    repo_root = args.repo_root.resolve()
    output_dir = args.output_dir.resolve()
    output_dir.mkdir(parents=True, exist_ok=True)
    write_readme(output_dir / "README.md")
    candidate_path = (
        args.candidate_inventory.resolve()
        if args.candidate_inventory
        else (
            repo_root
            / "work/risk_aware_cbf/results/safc_level3b_warning_rich_targeted"
            / "warning_rich_candidate_inventory.csv"
        )
    )
    candidates = load_csv(candidate_path)[: args.max_candidates]
    if not candidates:
        raise RuntimeError("no Level-3B candidates available")
    report_rows = load_csv(output_dir / "report_context_inventory.csv")
    reconciliation_rows = load_csv(
        output_dir / "candidate_context_reconciliation.csv"
    )
    if not report_rows or not reconciliation_rows:
        raise RuntimeError("run context reconciliation before no-op scans")

    entrypoint = ""
    if args.sensitivity_only:
        settings = [
            (margin, horizon)
            for margin in args.dt_margin_grid
            for horizon in args.horizon_grid
        ]
        results, entrypoint = run_grid(
            repo_root,
            candidates,
            args.entrypoint,
            args.max_steps,
            settings,
            0.0005,
        )
        sensitivity_data = sensitivity_rows(results, settings)
        write_csv(
            output_dir / "dt_margin_horizon_sensitivity_summary.csv",
            SENSITIVITY_FIELDS,
            sensitivity_data,
        )
    else:
        settings = [(args.dt_margin, args.horizon)]
        results, entrypoint = run_grid(
            repo_root,
            candidates,
            args.entrypoint,
            args.max_steps,
            settings,
            args.dt_margin,
        )
        window_data = window_rows(
            results, args.dt_margin, args.horizon
        )
        if any(
            row["u_nom_modified"]
            or row["u_safe_modified"]
            or row["control_modified"]
            for row in window_data
        ):
            raise RuntimeError("no-op control invariance failed")
        write_csv(
            output_dir / "bounded_noop_window_scan_summary.csv",
            WINDOW_FIELDS,
            window_data,
        )
        sensitivity_path = (
            output_dir / "dt_margin_horizon_sensitivity_summary.csv"
        )
        if not sensitivity_path.exists():
            write_csv(sensitivity_path, SENSITIVITY_FIELDS, [])

    window_rows_data = load_csv(
        output_dir / "bounded_noop_window_scan_summary.csv"
    )
    sensitivity_data = load_csv(
        output_dir / "dt_margin_horizon_sensitivity_summary.csv"
    )
    if not window_rows_data:
        raise RuntimeError("bounded default scan summary is missing")
    first50_path = (
        args.first50_summary.resolve()
        if args.first50_summary
        else (
            repo_root
            / "work/risk_aware_cbf/results/safc_level3b_warning_rich_targeted"
            / "targeted_noop_scan_summary.csv"
        )
    )
    first50_rows = load_csv(first50_path)
    diagnosis_rows = build_diagnosis(
        candidates,
        first50_rows,
        window_rows_data,
        sensitivity_data,
        reconciliation_rows,
    )
    write_csv(
        output_dir / "mismatch_diagnosis_summary.csv",
        DIAGNOSIS_FIELDS,
        diagnosis_rows,
    )
    metrics = build_metrics(
        args,
        report_rows,
        reconciliation_rows,
        window_rows_data,
        sensitivity_data,
        diagnosis_rows,
        entrypoint,
    )
    (output_dir / "metrics.json").write_text(
        json.dumps(metrics, indent=2) + "\n", encoding="utf-8"
    )
    write_notes(
        output_dir / "warning_reconciliation_notes.md",
        report_rows,
        reconciliation_rows,
        window_rows_data,
        sensitivity_data,
        diagnosis_rows,
        metrics,
        args.dt_margin_grid,
        args.horizon_grid,
    )
    print(json.dumps(metrics, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
