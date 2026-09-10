# Report — ACTIVE Runtime Pilot V2

## Answer-first result

The frozen 10-pair/20-arm Pilot completed with complete evaluation evidence and
no runtime-integrity failure.  Neither arm produced a represented-map collision
proxy or a 0.025 m certification-margin violation, and neither arm reached the
frozen 6D goal predicate.  However, ACTIVE exhibited a clear method-level
liveness signal: trials **5, 25, 45, 75, and 85** had one `C0 FAIL`, immediately
committed a certified terminal action, stopped after cycle 1, and made exactly
zero normalized progress.  Only **5/10 ACTIVE trials** ever committed a primary
navigation action.

Therefore this Pilot does **not** authorize freezing the formal paired
experiment protocol.  The next bounded task is to diagnose the observed C0
rejection to early-terminal routing mechanism.  This is a descriptive Pilot
decision, not a superiority claim or significance result.

`FINAL_STATUS=BLOCKED_ACTIVE_RUNTIME_PILOT_BY_METHOD_LEVEL_SIGNAL`

`FINAL_DECISION=DIAGNOSE_ACTIVE_RUNTIME_C0_REJECTION_AND_EARLY_TERMINAL_TAKEOVER_V2`

## Frozen execution

- Direct upstream: PR #133 at `2a8fd73cdc660fccbf9522f4d24e9d85f2e03a2c`.
- Trials: `5, 15, 25, 35, 45, 55, 65, 75, 85, 95`.
- Per-pair order: `REFERENCE_CBF_QP` then `ACTIVE_RUNTIME_V2`.
- Completion: 10/10 pairs and 20/20 arms; separate serial processes on GPU 1.
- Horizon: 500 steps; all 20 arms terminated as `NATIVE_NOT_MOVING` before the
  horizon.
- Frozen map/checkpoint, start/goal construction, desired-control formula,
  current CBF-QP, plant, `dt=0.05`, radii, and oracle were shared between arms.
- Runtime and production diff: zero.

## Descriptive outcomes

| Metric | Reference | ACTIVE |
|---|---:|---:|
| represented-map collision-proxy trials | 0/10 | 0/10 |
| certification-margin violation trials | 0/10 | 0/10 |
| goal reached | 0/10 | 0/10 |
| normalized progress, mean | 0.340029 | 0.135833 |
| normalized progress, median | 0.232969 | 0.001165 |
| normalized progress, min / max | 0.002329 / 0.991212 | 0 / 0.991212 |
| executed steps, total | 1,475 | 603 |
| executed steps, median | 107 | 3.5 |
| per-step compute, median of trial medians | 0.059836 s | 0.164851 s |
| per-step p95, median across trial p95s | 0.070586 s | 0.165702 s |

The paired ACTIVE-minus-Reference progress delta had mean `-0.204197`, median
`-0.033425`, range `[-0.853138, 0]`.  Per-pair compute-median ratios had median
`2.7544` and range `[1.9485, 5.4525]`; p95 ratios had median `2.4948` and range
`[1.6242, 5.0824]`.  These are engineering observations under this small
Pilot, not a real-time guarantee or final performance claim.

## ACTIVE diagnostics

- Completed cycles: 603.
- Primary / alternative / retained-backup / terminal / boundary outcomes:
  `598 / 0 / 0 / 5 / 0`.
- L1 PASS/FAIL/UNKNOWN: `603 / 0 / 0`.
- C0 PASS/FAIL/UNKNOWN: `598 / 5 / 0`.
- L2 PASS/FAIL/UNKNOWN: `598 / 0 / 0`.
- L3 PASS/FAIL/UNKNOWN: `598 / 0 / 0`.
- Primary proposal QP failures: 0; Reference CBF-QP solver failures: 0.
- Deadline OPEN/WARNING/EXPIRED: `2422 / 0 / 0`.
- Backup-token activation / consumption: `598 / 0`.
- Active-constraint count: `NOT_INSTRUMENTED` (no core instrumentation added).

The five zero-progress terminal trials were not caused by proposal-QP failure,
deadline expiry, backup exhaustion, UNKNOWN certificates, or an assurance
boundary.  In each, L1 passed, a primary proposal existed, C0 rejected it, and
the frozen Supervisor path selected an eligible certified terminal action.
This localized pattern motivates the next diagnosis.

## Oracle and evidence integrity

All 20 arms are evaluation-eligible.  Each has an immutable state trajectory,
executed-action log, per-step timings, typed termination, and raw evidence lock;
each ACTIVE arm additionally has a finalized runtime trace and trace lock.
There were zero evidence-incomplete, recovery-required, nonfinite, trace, or
identity failures.  GPU 1 was clean after the final posthoc evaluation.

The oracle was posthoc with `feedback=false`.  Collision used swept executed
position segments at radius 0.015 m; certification-margin violation used 0.025
m; goal used `norm_2(x-goal_6d)<0.001`; progress was unclipped.  A task-local
summary repair replaced a diagnostic parent-interval lower bound with the
minimum resolved 1-Lipschitz leaf bound for min-clearance reporting.  It
re-read locked trajectories only; no arm, state, action, trace, threshold, or
scientific outcome was changed or rerun.

## Claim boundary

Supported: bounded descriptive evidence that the frozen ACTIVE path preserved
represented-map collision and margin proxies in this Pilot, while showing a
five-trial C0-to-terminal liveness pattern and higher per-step computation.

Not supported: statistical significance, method superiority, physical
collision avoidance, real-time guarantees, deployment readiness, or any
official100 conclusion.

## Only next task

`DIAGNOSE_ACTIVE_RUNTIME_C0_REJECTION_AND_EARLY_TERMINAL_TAKEOVER_V2`
