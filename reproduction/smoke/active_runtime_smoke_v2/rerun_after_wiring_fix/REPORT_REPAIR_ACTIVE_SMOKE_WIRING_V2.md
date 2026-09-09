# REPAIR_ACTIVE_SMOKE_WIRING_V2 — fail-closed rerun report

## Answer first

`FINAL_STATUS=BLOCKED_ACTIVE_RUNTIME_SMOKE_BY_WIRING`

`FINAL_DECISION=PRESERVE_RERUN_EVIDENCE_AND_REPAIR_STALE_COMMIT_COUNT_WIRING_ONLY`

The requested `finalization.lock` to `finalization.trace_lock` repair is correct, and the task-local API wiring check passed. The exact frozen rerun then exposed a second task-local runner ordering defect: trial 10 made one real certified-terminal plant commit and finalized an exact one-record trace lock, but the runner evaluated its no-active-commit gate before copying the actual plant commit count into the summary. It therefore returned `INCONCLUSIVE_NO_ACTIVE_COMMIT` despite the preserved summary showing `plant_commit_count=1`.

Per the frozen first-hard-block rule, trials 50 and 90 were not started. No second repair, second rerun, runtime modification, pilot, oracle, or official100 execution occurred.

Only next task: `REPAIR_ACTIVE_SMOKE_PLANT_COMMIT_COUNT_ORDERING_V2`.

## First attempt versus rerun

| Evidence | first_attempt | rerun_after_wiring_fix |
|---|---|---|
| Startup | PASS | PASS |
| Completed cycles | 1 | 1 |
| Plant commits | 1 | 1 |
| Action role | CERTIFIED_TERMINAL | CERTIFIED_TERMINAL |
| Runtime trace cardinality | 1 / 1 / 1 | 1 / 1 / 1 |
| Runtime finalization | FINALIZED | FINALIZED |
| `trace_lock` captured in summary | no, original typo raised | yes |
| Unhandled exception | task-local `AttributeError` after finalization | 0 |
| Stop cause | missing `trace_lock` API wiring | stale summary count checked before actual plant count copy |

The raw trace and trace-lock hashes are identical across attempts, which is consistent with deterministic execution of the same frozen trial 10; this is engineering evidence only.

## Rerun telemetry

| Trial | Startup | Cycles | Plant | Primary | Backup | Terminal | Boundary | Finalization | Process |
|---:|---|---:|---:|---:|---:|---:|---:|---|---:|
| 10 | PASS | 1 | 1 | 0 | 0 | 1 | 0 | FINALIZED | 2 |
| 50 | not run | 0 | 0 | 0 | 0 | 0 | 0 | not run | 2 |
| 90 | not run | 0 | 0 | 0 | 0 | 0 | 0 | not run | 2 |

Trial 10 deadline observations were OPEN/WARNING/EXPIRED = 5/0/0. The final trace reason was `ELIGIBLE_CURRENT_CERTIFIED_TERMINAL_ACTION`; the current runner does not persist the final routing rule ID, so that field is reported as `NOT_CAPTURED_BY_CURRENT_RUNNER` rather than inferred.

Exceptions, nonfinite values, selected/executed identity mismatches, action-bound violations, evidence-incomplete states, recovery-required states, and CUDA OOM were all zero. GPU 1 was released after the child process.

## Root evidence

The task-local runner initializes `summary["plant_commit_count"]` to zero. After finalization, it tests that summary value and may set `INCONCLUSIVE_NO_ACTIVE_COMMIT`; only later does it assign `summary["plant_commit_count"] = stack["plant"].commit_count`. In this rerun the final copied value is 1, directly contradicting the earlier blocker. This establishes `SMOKE-WIRING-002_STALE_PLANT_COMMIT_COUNT_CHECK` without implicating the frozen runtime.

## Evidence boundary

The three-trial smoke is not complete, the aggregate primary-navigation adequacy gate is not evaluable, and `ACTIVE_RUNTIME_PILOT_V2` is not authorized. No claim is made about collision, progress, success, real-time performance, or deployment readiness.
