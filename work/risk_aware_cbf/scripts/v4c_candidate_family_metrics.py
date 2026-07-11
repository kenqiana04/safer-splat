#!/usr/bin/env python3
"""Compact candidate-family accounting for the original V4-C source labels."""

from __future__ import annotations

import math
from collections import defaultdict
from typing import Any, Iterable


FAMILY_ORDER = (
    "baseline",
    "braking",
    "repulsive",
    "goal_directed",
    "continuity",
    "random",
    "cem",
    "unknown",
)


def classify_source(source: str) -> str:
    """Map an original V4-C source label to a preregistered family."""

    text = str(source)
    if text in {"base_repeated", "nominal_repeated"} or text.startswith("scaled_base_"):
        return "baseline"
    if text.startswith("braking_") or text.startswith("brake_then_base_"):
        return "braking"
    if text.startswith("repulsive_") or text.startswith("base_plus_repulsive_") or text.startswith("repulse_then_base_"):
        return "repulsive"
    if text.startswith("goal_directed_") or text.startswith("repulse_then_goal_"):
        return "goal_directed"
    if text in {"previous_repeated", "smooth_prev_base"}:
        return "continuity"
    if text.startswith("random_around_base_"):
        return "random"
    if text.startswith("cem_"):
        return "cem"
    return "unknown"


def _float(value: Any) -> float | None:
    try:
        parsed = float(value)
    except (TypeError, ValueError):
        return None
    return parsed if math.isfinite(parsed) else None


def _passed(row: dict[str, Any]) -> bool:
    return str(row.get("sequence_passed_dt_margin", "")).strip().lower() == "true"


def stage_family_snapshot(
    *,
    candidates: Iterable[Any],
    rows: list[dict[str, Any]],
    selected_index: int,
    start_goal_distance: float,
    generation_runtime_sec: float,
    evaluation_runtime_sec: float,
    count_selection: bool,
) -> list[dict[str, Any]]:
    """Return compact per-family counts for one evaluated stage.

    Runtime is apportioned by generated candidate count because the original
    generator/evaluator do not expose per-candidate timers. The caller records
    this attribution method in the aggregate notes.
    """

    candidate_list = list(candidates)
    by_family: dict[str, dict[str, Any]] = defaultdict(
        lambda: {
            "generated_count": 0,
            "feasible_count": 0,
            "selected_count": 0,
            "unique_feasible_step_count": 0,
            "selected_recovery_success_count": 0,
            "selected_min_h_values": [],
            "selected_progress_values": [],
        }
    )
    feasible_families: set[str] = set()
    selected_family: str | None = None
    selected_row: dict[str, Any] | None = None
    for index, candidate in enumerate(candidate_list):
        source = getattr(candidate, "source", "unknown")
        family = classify_source(source)
        by_family[family]["generated_count"] += 1
        row = rows[index] if index < len(rows) else {}
        if _passed(row):
            by_family[family]["feasible_count"] += 1
            feasible_families.add(family)
        if count_selection and index == selected_index:
            selected_family = family
            selected_row = row
    if len(feasible_families) == 1:
        by_family[next(iter(feasible_families))]["unique_feasible_step_count"] += 1
    if selected_family is not None and selected_row is not None:
        selected = by_family[selected_family]
        selected["selected_count"] += 1
        if _passed(selected_row):
            selected["selected_recovery_success_count"] += 1
        min_h = _float(selected_row.get("sequence_min_h"))
        if min_h is not None:
            selected["selected_min_h_values"].append(min_h)
        goal_cost = _float(selected_row.get("sequence_goal_cost"))
        if goal_cost is not None:
            selected["selected_progress_values"].append(start_goal_distance - math.sqrt(max(goal_cost, 0.0)))
    total_generated = max(1, len(candidate_list))
    output: list[dict[str, Any]] = []
    for family in FAMILY_ORDER:
        row = by_family.get(family)
        if not row:
            continue
        share = float(row["generated_count"]) / float(total_generated)
        output.append(
            {
                "family": family,
                "generated_count": row["generated_count"],
                "feasible_count": row["feasible_count"],
                "selected_count": row["selected_count"],
                "unique_feasible_step_count": row["unique_feasible_step_count"],
                "selected_recovery_success_count": row["selected_recovery_success_count"],
                "selected_min_h_values": row["selected_min_h_values"],
                "selected_progress_values": row["selected_progress_values"],
                "generation_runtime_sec": float(generation_runtime_sec) * share,
                "evaluation_runtime_sec": float(evaluation_runtime_sec) * share,
            }
        )
    return output


def aggregate_family_snapshots(
    snapshots: Iterable[dict[str, Any]], method_variant: str
) -> list[dict[str, Any]]:
    """Merge in-memory compact snapshots into the required aggregate schema."""

    totals: dict[str, dict[str, Any]] = defaultdict(
        lambda: {
            "generated_count": 0,
            "feasible_count": 0,
            "selected_count": 0,
            "unique_feasible_step_count": 0,
            "selected_recovery_success_count": 0,
            "selected_min_h_values": [],
            "selected_progress_values": [],
            "generation_runtime_sec": 0.0,
            "evaluation_runtime_sec": 0.0,
        }
    )
    for snapshot in snapshots:
        family = str(snapshot["family"])
        total = totals[family]
        for key in (
            "generated_count",
            "feasible_count",
            "selected_count",
            "unique_feasible_step_count",
            "selected_recovery_success_count",
        ):
            total[key] += int(snapshot[key])
        total["selected_min_h_values"].extend(snapshot["selected_min_h_values"])
        total["selected_progress_values"].extend(snapshot["selected_progress_values"])
        total["generation_runtime_sec"] += float(snapshot["generation_runtime_sec"])
        total["evaluation_runtime_sec"] += float(snapshot["evaluation_runtime_sec"])
    all_runtime = sum(
        total["generation_runtime_sec"] + total["evaluation_runtime_sec"]
        for total in totals.values()
    )
    output: list[dict[str, Any]] = []
    for family in FAMILY_ORDER:
        total = totals.get(family)
        if not total:
            continue
        runtime = total["generation_runtime_sec"] + total["evaluation_runtime_sec"]
        min_hs = total["selected_min_h_values"]
        progress = total["selected_progress_values"]
        output.append(
            {
                "method_variant": method_variant,
                "family": family,
                "generated_count": total["generated_count"],
                "feasible_count": total["feasible_count"],
                "selected_count": total["selected_count"],
                "unique_feasible_step_count": total["unique_feasible_step_count"],
                "selected_recovery_success_count": total["selected_recovery_success_count"],
                "mean_selected_min_h": sum(min_hs) / len(min_hs) if min_hs else None,
                "mean_selected_progress_delta": sum(progress) / len(progress) if progress else None,
                "generation_runtime_sec": total["generation_runtime_sec"],
                "evaluation_runtime_sec": total["evaluation_runtime_sec"],
                "runtime_share": runtime / all_runtime if all_runtime else None,
                "notes": "Runtime is apportioned by generated-candidate count; no raw candidate controls retained.",
            }
        )
    return output
