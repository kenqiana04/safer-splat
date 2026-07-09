# SAFC Level-3A Warning-Streak Slowdown Results

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
