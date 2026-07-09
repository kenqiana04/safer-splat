# SAFC Level-3B-R Warning Evidence Reconciliation Notes

## Scope

This is warning evidence reproduction reconciliation. It does not run active
slowdown and does not claim performance improvement.

## Report-Derived Warning Evidence

The audit scanned 9 tracked reports and reconciled
7 candidates. It extracted scene, trial, horizon,
margin, controller, recovery, trajectory, window, and checkpoint context where
the reports stated them. Exact first-warning steps, checkpoints, and executed
start-state history were commonly missing. No raw trace was read.

## Context Reconciliation

Scene and trial identifiers match the current wrapper candidates, but the main
warning reports use Risk-Aware V1, V4-C recovery-enabled trajectories, or
post-repair contexts. The current scan uses official CBF command construction,
recovery disabled, original generated starts/goals, and an independent no-op
trajectory. All 7 candidates retain
at least one unresolved report-context field.

## Bounded No-Op Window Scan

The scan covered 7 candidates for at most
200 steps with `dt_margin=0.0005` and H3. Warnings outside
the first 50 were found for 5
candidates. No command, `u_nom`, or internal `u_safe` modification was allowed.

## DT Margin / Horizon Sensitivity

The diagnostic grid was margins 0.0001,0.0005,0.001
and horizons 1,2,3. Warnings appeared
for 6 candidates under at least one
grid setting. Each candidate used one no-op trajectory while all grid counters
were accumulated; this is context sensitivity analysis, not benchmark tuning.

## Mismatch Diagnosis

Most likely reasons: controller_context_mismatch, dt_margin_horizon_mismatch, step_window_too_short. The diagnosis
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
