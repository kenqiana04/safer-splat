# ACTIVE Runtime Smoke V2 — task-local autofix closeout

## Outcome

`FINAL_STATUS=PASS_ACTIVE_RUNTIME_SMOKE_V2`

`FINAL_DECISION=ADVANCE_ACTIVE_RUNTIME_PILOT_V2`

The frozen three-trial engineering smoke is complete. Trial 10 reused its preserved, internally complete runtime evidence rather than running again. Trials 50 and 90 were executed serially in separate official-environment processes on GPU 1. All three have credible summaries, `FINALIZED` trace locks, exact cycle/trace/lock cardinality, and clean GPU release. Trial 90 supplied 200 primary-navigation commits, satisfying the aggregate adequacy requirement.

Only next task: `ACTIVE_RUNTIME_PILOT_V2`.

## Task-local autofixes

1. `TrialFinalizationResult.lock` was replaced by the unique frozen `trace_lock` field.
2. plant/token/stage/deadline/trace/finalization telemetry is refreshed before count-dependent smoke gates.
3. commit-role, plant, trace, and lock counts are checked for internal consistency.
4. direct `--one` continuation processes receive the exact frozen batch environment.
5. post-process GPU UUID checks are merged into corrected summaries through task-local sidecars.
6. trial 10 was reconstructed from preserved raw evidence; it was not rerun in this task.

The first trial-50 continuation command lacked the batch parent's environment variables and stopped before runtime startup. That zero-runtime attempt was preserved, then the exact frozen environment was supplied. No experiment input changed.

## Final engineering telemetry

| Trial | Evidence | Cycles | Plant | Primary | Backup | Terminal | Boundary | Trace/lock | Finalization |
|---:|---|---:|---:|---:|---:|---:|---:|---|---|
| 10 | reused preserved raw | 1 | 1 | 0 | 0 | 1 | 0 | 1/1 | FINALIZED |
| 50 | fresh continuation | 1 | 1 | 0 | 0 | 1 | 0 | 1/1 | FINALIZED |
| 90 | fresh continuation | 200 | 200 | 200 | 0 | 0 | 0 | 200/200 | FINALIZED |

Aggregate: 202 completed cycles, 202 plant commits, 200 primary navigation commits, 2 certified-terminal commits, and 0 backup/boundary outcomes. Deadline OPEN/WARNING/EXPIRED = 811/0/0.

Exceptions, CUDA OOM, nonfinite state/action, selected/executed mismatch, action-bound violation, unauthorized or duplicate plant commit, evidence incomplete, recovery required, finalization failed, stale-backup normal reuse, trace-cardinality mismatch, and precommit deadline expiry are all zero.

Per-trial cycle timing summaries are retained as engineering telemetry only. No aggregate quantile was reconstructed without the raw 202-value timing vector, and no real-time claim is made.

## Evidence boundary

Runtime/production source diff is zero. No map, controller, solver, geometry, dynamics, deadline profile, state, goal, seed, or trial order was changed. No pilot, scientific oracle, collision/progress analysis, formal statistics, baseline comparison, or official100 was run. Smoke PASS establishes engineering execution coverage only, not safety efficacy or deployment readiness.
