# SAFC Level-3B-R Warning Evidence Reconciliation Results

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
