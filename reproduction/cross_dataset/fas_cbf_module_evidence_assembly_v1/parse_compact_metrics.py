#!/usr/bin/env python3
"""Recover only protocol-specified compact metrics and confirm their report anchors."""
from __future__ import annotations

from evidence_common import TASK, require_phrase, write_json

METRICS = [
    ("E01_ETH3D_PR80", "minimum_controller_viability", 13, "gate", "all 13 hard gates true", "formal"),
    ("E01_ETH3D_PR80", "terminal_records", 500, "scenario-method terminal record", "500/500", "formal"),
    ("E02_ETH3D_PR81", "candidate_tuples", 200000, "plant-free candidate state tuple", "Candidate tuples: 200000 / 200000", "shadow"),
    ("E02_ETH3D_PR81", "g3_endpoint_unsafe_qp_feasible", 0, "candidate state tuple", '"G3_ENDPOINT_UNSAFE": 0', "shadow"),
    ("E03_REPLICA_PR65", "terminal_records", 500, "route-method terminal record", "500 unique terminal records", "formal"),
    ("E03_REPLICA_PR65", "map_admissible_route_success", 99, "route", "All 495 map-admissible trials succeeded", "formal"),
    ("E05_STARTGUARD_FLIGHT100", "repair_needed", 8, "trial", "repair-needed count: 8", "active"),
    ("E05_STARTGUARD_FLIGHT100", "repair_success", 8, "trial", "repair_success_count: 8", "active"),
    ("E06_ACTIVE_PROJECTION", "full_query_verified_projection", 8, "repair-needed state", "|active_set_verified_projection|8|8|0", "active"),
    ("E07_SYNTHETIC_START_STRESS", "verified_projection_success", 120, "synthetic state", "| active_set_verified_projection | 120 | 120 | 1 | 120", "static"),
    ("E08_RISK_AWARE_STONEHENGE", "baseline_active_constraints_mean", 505.5866495, "trial", "505.5866495", "formal"),
    ("E08_RISK_AWARE_STONEHENGE", "bestd_active_constraints_mean", 252.2219893, "trial", "252.2219893", "formal"),
    ("E08_RISK_AWARE_STONEHENGE", "baseline_runtime_mean_s", 0.06307919365, "trial", "0.06307919365", "formal"),
    ("E08_RISK_AWARE_STONEHENGE", "bestd_runtime_mean_s", 0.04044284326, "trial", "0.04044284326", "formal"),
    ("E11_DT_DETECTION", "h1_margin_violations", 463, "controller step", "| 1 | 100 | 14422 | 463", "active"),
    ("E11_DT_DETECTION", "h2_margin_violations", 488, "controller step", "| 2 | 100 | 14422 | 488", "active"),
    ("E11_DT_DETECTION", "h3_margin_violations", 519, "controller step", "| 3 | 100 | 14422 | 519", "active"),
    ("E12_V4B_NEGATIVE", "one_step_correction_success", 0, "margin-violating step", "|v4b_repair_needed|1197|15|15|0|0", "active"),
    ("E13_V4C_H3", "recovery_success", 236, "recovery activation", "predictive_recovery_success_count | 236", "active"),
    ("E14_V4C_TUNED_H2", "recovery_success", 193, "recovery activation", "| 100 | 0 | 100 | 0 | 193 | 0 | 193 | 193 | 193 | 0", "active"),
    ("E15_HCE_HELDOUT", "heldout_activations", 201, "activation context", "167 of 201", "active"),
    ("E15_HCE_HELDOUT", "activated_runtime_median_s", 1.6425828915089369, "held-out activated trial", "1.6425828915089369", "active"),
    ("E16_TRIAL20_BOUNDARY", "recovery_failures", 34, "recovery activation", "34 recovery failures", "shadow"),
    ("E17_TUM_DT_FORENSICS", "event_precursor_step", 772, "time step", "step 772", "shadow"),
    ("E18_TUM_V4C_INTERVENTION", "heldout_case_pairs", 3, "paired case", "these three held-out pairs", "active"),
]


def main() -> int:
    rows = []
    for evidence_id, metric, value, unit, phrase, activity in METRICS:
        if not require_phrase(evidence_id, phrase):
            raise RuntimeError(f"report anchor missing for {evidence_id}:{metric}")
        rows.append({"evidence_id": evidence_id, "metric": metric, "value": value, "sample_unit": unit, "anchor_phrase": phrase, "activity": activity})
    write_json(TASK / "semantic_alignment/parsed_compact_metrics.json", {"metric_count": len(rows), "metrics": rows})
    print(f"PASS_COMPACT_METRIC_PARSE count={len(rows)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
