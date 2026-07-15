#!/usr/bin/env python3
"""Derive the frozen trial manifests from existing preregistration artifacts."""
from __future__ import annotations

import csv
from pathlib import Path

ROOT = Path(__file__).resolve().parents[3]
OUT = ROOT / "reproduction" / "experiment_protocol_freeze_v1" / "trial_manifests"


def write_csv(path: Path, fields: list[str], rows: list[dict[str, object]]) -> None:
    with path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=fields)
        writer.writeheader()
        writer.writerows(rows)


def main() -> None:
    OUT.mkdir(parents=True, exist_ok=True)
    heldout_source = ROOT / "work/risk_aware_cbf/results/v4c_hierarchical_heldout_activated_cohort/heldout_cohort_preregistration.csv"
    heldout = list(csv.DictReader(heldout_source.open(encoding="utf-8", newline="")))
    rows = [{"trial": row["trial_id"], "cohort": "heldout_activated", "source": heldout_source.relative_to(ROOT).as_posix(), "trial_order": index + 1, "seed": "unresolved", "original_or_post_repair": "post_repair_wrapper_context", "development_excluded": "true"} for index, row in enumerate(heldout) if row.get("cohort") == "heldout_activated"]
    write_csv(OUT / "heldout_activated_16.csv", list(rows[0]), rows)
    control_source = ROOT / "work/risk_aware_cbf/results/v4c_hierarchical_heldout_activated_cohort/nonactivated_control_preregistration.csv"
    controls = list(csv.DictReader(control_source.open(encoding="utf-8", newline="")))
    control_rows = [{"trial": row["trial_id"], "cohort": "nonactivated_control", "source": control_source.relative_to(ROOT).as_posix(), "trial_order": index + 1, "seed": "unresolved", "original_or_post_repair": "post_repair_wrapper_context", "development_excluded": "true"} for index, row in enumerate(controls)]
    write_csv(OUT / "nonactivated_controls.csv", list(control_rows[0]), control_rows)
    context_source = ROOT / "work/risk_aware_cbf/results/v4c_gtep_shadow_audit/trial20_context_preregistration.csv"
    contexts = list(csv.DictReader(context_source.open(encoding="utf-8", newline="")))
    context_rows = [{"trial": 20, "activation_index": row["activation_index"], "trajectory_step": row["trajectory_step"], "source": context_source.relative_to(ROOT).as_posix(), "order_status": "original_comparator_order", "usage": "diagnostic_only_not_tuning", "seed": "unresolved"} for row in contexts]
    write_csv(OUT / "trial20_activation_contexts.csv", list(context_rows[0]), context_rows)
    official = [{"trial": trial, "cohort": "official100", "order": trial, "start_goal_source": "unresolved_exact_file", "seed": "unresolved", "result_family": "original_or_post_repair_must_be_labeled"} for trial in range(100)]
    write_csv(OUT / "flight_official100_manifest.csv", list(official[0]), official)
    stonehenge = [{"trial": trial, "cohort": "official100", "order": trial, "start_goal_source": "unresolved_exact_file", "seed": "unresolved", "result_family": "original_baseline"} for trial in range(100)]
    write_csv(OUT / "stonehenge_official100_manifest.csv", list(stonehenge[0]), stonehenge)


if __name__ == "__main__":
    main()
