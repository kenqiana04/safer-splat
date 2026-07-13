#!/usr/bin/env python3
"""Derive the held-out V4-C cohort only from an original full100 comparator CSV."""

from __future__ import annotations

import argparse
import csv
from pathlib import Path
from typing import Any


DEVELOPMENT_TRIALS = {12, 13, 14}
EXPECTED_TOTAL_TRIALS = 100
EXPECTED_ACTIVATED_TRIALS = 19
EXPECTED_ACTIVATIONS = 236
EXPECTED_HELDOUT_TRIALS = 16


def as_int(value: Any, field: str, trial: int) -> int:
    try:
        return int(float(str(value)))
    except (TypeError, ValueError) as error:
        raise RuntimeError(f"trial {trial}: invalid {field}={value!r}") from error


def write_csv(path: Path, rows: list[dict[str, Any]], fields: list[str]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=fields, extrasaction="ignore")
        writer.writeheader()
        writer.writerows(rows)


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--input-csv", type=Path, required=True)
    parser.add_argument("--output-dir", type=Path, required=True)
    parser.add_argument("--source-artifact", required=True)
    args = parser.parse_args()

    with args.input_csv.open("r", newline="", encoding="utf-8") as handle:
        source_rows = list(csv.DictReader(handle))
    required = {
        "trial", "predictive_recovery_used_count", "predictive_recovery_success_count",
        "recovery_failed_count", "exec_horizon_margin_violation_count", "runtime_mean",
        "runtime_p95", "goal_distance_reduction_ratio",
    }
    if not source_rows or not required.issubset(source_rows[0]):
        raise RuntimeError("input is not an original V4-C full100 trial summary")
    ordered = sorted(source_rows, key=lambda row: as_int(row["trial"], "trial", -1))
    ids = [as_int(row["trial"], "trial", -1) for row in ordered]
    if len(ordered) != EXPECTED_TOTAL_TRIALS or ids != list(range(EXPECTED_TOTAL_TRIALS)):
        raise RuntimeError("original comparator must contain exactly trial IDs 0..99 once")

    inventory: list[dict[str, Any]] = []
    activated_ids: list[int] = []
    total_activations = 0
    nonactivated_ids: list[int] = []
    for row, trial in zip(ordered, ids):
        activation_count = as_int(row["predictive_recovery_used_count"], "predictive_recovery_used_count", trial)
        activated = activation_count > 0
        total_activations += activation_count
        if activated:
            activated_ids.append(trial)
        else:
            nonactivated_ids.append(trial)
        development = trial in DEVELOPMENT_TRIALS
        inventory.append({
            "trial_id": trial,
            "original_activation_count": activation_count,
            "original_recovery_success_count": as_int(row["predictive_recovery_success_count"], "predictive_recovery_success_count", trial),
            "original_recovery_failed_count": as_int(row["recovery_failed_count"], "recovery_failed_count", trial),
            "original_exec_horizon_violation_count": as_int(row["exec_horizon_margin_violation_count"], "exec_horizon_margin_violation_count", trial),
            "original_runtime_mean": row["runtime_mean"],
            "original_runtime_p95": row["runtime_p95"],
            "original_progress_ratio": row["goal_distance_reduction_ratio"],
            "activated": activated,
            "development_trial": development,
            "heldout_included": activated and not development,
            "exclusion_reason": "development_trial" if development else ("not_activated_in_original_comparator" if not activated else ""),
            "source_artifact": args.source_artifact,
        })
    if len(activated_ids) != EXPECTED_ACTIVATED_TRIALS or total_activations != EXPECTED_ACTIVATIONS:
        raise RuntimeError(
            f"original comparator inventory mismatch: activated_trials={len(activated_ids)}, activations={total_activations}"
        )
    heldout_ids = [trial for trial in activated_ids if trial not in DEVELOPMENT_TRIALS]
    if len(heldout_ids) != EXPECTED_HELDOUT_TRIALS:
        raise RuntimeError(f"held-out cohort must contain {EXPECTED_HELDOUT_TRIALS} trials, got {len(heldout_ids)}")
    if len(nonactivated_ids) != 81:
        raise RuntimeError(f"expected 81 nonactivated trials, got {len(nonactivated_ids)}")
    control_ids = [nonactivated_ids[0], nonactivated_ids[len(nonactivated_ids) // 2], nonactivated_ids[-1]]

    output = args.output_dir
    inventory_fields = list(inventory[0])
    write_csv(output / "full100_activation_inventory.csv", inventory, inventory_fields)
    heldout_rows = [
        {"cohort_index": index, "trial_id": trial, "cohort": "heldout_activated", "selection_rule": "original_comparator_activated_minus_development", "source_artifact": args.source_artifact}
        for index, trial in enumerate(heldout_ids, start=1)
    ]
    write_csv(output / "heldout_cohort_preregistration.csv", heldout_rows, list(heldout_rows[0]))
    control_rows = [
        {"control_position": position, "trial_id": trial, "cohort": "nonactivated_control", "selection_rule": "sorted_original_nonactivated_first_median_last", "source_artifact": args.source_artifact}
        for position, trial in zip(("first", "median", "last"), control_ids)
    ]
    write_csv(output / "nonactivated_control_preregistration.csv", control_rows, list(control_rows[0]))
    run_rows: list[dict[str, Any]] = []
    order_index = 1
    for cohort, trials in (("heldout_activated", heldout_ids), ("nonactivated_control", control_ids)):
        for cohort_index, trial in enumerate(trials, start=1):
            variants = ("original_v4c", "hierarchical_v0") if cohort_index % 2 else ("hierarchical_v0", "original_v4c")
            for variant in variants:
                run_rows.append({"run_index": order_index, "cohort": cohort, "cohort_index": cohort_index, "trial_id": trial, "method_variant": variant, "selection_rule": "ascending_trial_id_alternating_order"})
                order_index += 1
    write_csv(output / "run_order_preregistration.csv", run_rows, list(run_rows[0]))
    readme = "# V4-C Held-Out Activated Cohort\n\nThis directory contains compact preregistration and aggregate outputs only. The cohort is derived exclusively from the original V4-C H3_N128 full100 comparator; no hierarchical result participates in selection. Raw trajectories, controls, traces, and the source comparator `trials.csv` are intentionally excluded.\n"
    (output / "README.md").write_text(readme, encoding="utf-8")
    print("activated_ids=" + ",".join(map(str, activated_ids)))
    print("heldout_ids=" + ",".join(map(str, heldout_ids)))
    print("control_ids=" + ",".join(map(str, control_ids)))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
