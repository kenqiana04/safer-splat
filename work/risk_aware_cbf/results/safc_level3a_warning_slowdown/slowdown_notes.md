# SAFC Level-3A Warning-Streak Slowdown Notes

## Scope

This is a minimal active feedback smoke. It tests a bounded warning-streak
slowdown policy. It is not a benchmark and does not claim safety-performance
improvement.

## Policy

The policy maps warning streaks and H1/H2/H3 warnings to bounded command
scales. Its minimum scale is `0.25` and its maximum scale change
per step is `0.25`. Clear-step release hysteresis
is checked in the policy harness. The closed-loop gate applies command shaping
only while a natural warning is present. No planner is involved.

## Policy Harness

All `10` synthetic logic cases passed:
`true`.

## Closed-loop Smoke

* Selected entrypoint: `reproduction/scripts/run_official_runpy_smoke.py`
* Maximum trials: `1`
* Maximum steps: `20`
* Natural warning steps: `0`
* Slowdown active steps: `0`
* Command changed only under warning: `true`

## Claim Boundaries

* No full benchmark.
* No comparison.
* No collision reduction claim.
* No warning reduction claim.
* No planner improvement.
* No real-robot validation.
* No global safety guarantee.
* No new CBF theorem.

## If No Activation Observed

The active slowdown policy was not exercised by natural warnings in this tiny smoke. The result validates policy harness logic and safe integration behavior, but not active-policy effectiveness.
