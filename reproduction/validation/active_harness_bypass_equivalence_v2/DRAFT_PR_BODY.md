# Scope

This PR freezes and executes the bounded `ACTIVE_HARNESS_BYPASS` equivalence QA from exact PR #116 (`a8d7a3c9522583ad61dc9bc87585e41bb71a0f77`). It does not enable `ACTIVE_RUNTIME_ON`, use the scientific oracle, run official100, or make efficacy claims.

## Frozen QA and Q0

- Trial IDs: `[10, 30, 50, 70, 90]`; sentinel 50 first.
- Exact float32 action/state/branch/termination comparison; no tolerance substitution.
- Q0: `PASS_BYPASS_EQUIVALENCE_Q0_PREFLIGHT` (11/11).
- Reference runner: task-local Option B adapter, `PASS_REFERENCE_CONTROL_PLANT_PATH_SOURCE_LOCK`.

## Q1 evidence and authorized correction

The pre-correction reference sentinel completed 40 committed steps and terminated `NOT_MOVING`. BYPASS rejected cycle 0 because the frozen reference action contained component `0.10000000149011612` (`3dcccccd`) and the global PlantCommit actuator guard raised `ACTUATOR_ADMISSION_REQUIRED`. This is `M_BYPASS_HARNESS_INTERVENTION`, not scientific evidence against the reference action.

The one authorized correction (`f722b8d`) exempts only Supervisor rule `BYPASS` from ACTIVE actuator admission. All non-BYPASS rules retain the exact existing guard; bounds and tolerances are unchanged. Runtime tests pass 78/78.

The fresh post-correction sentinel then reached the first BYPASS plant commit but the task-local adapter used different trial IDs for `TraceWriter` and `RuntimeStateSnapshot`. Trace append raised `TRIAL_IDENTITY_MISMATCH`, classified as `M_TRACE_SIDE_EFFECT_ON_EXECUTION`. The pair did not finalize; Q2 never started. The correction cap is exhausted, and a fresh sentinel plus Q2 would project 14 real executions against the frozen hard cap of 12, so no further rerun was performed.

## Boundary and decision

- `run.py`, `cbf/**`, `dynamics/**`, `splat/**`, frozen specifications/designs: unchanged.
- Scientific oracle / ACTIVE / official100 counts: `0 / 0 / 0`.
- GPU 1 final task-owned compute processes: 0.
- Exact BYPASS equivalence: not established.
- No collision reduction, progress improvement, runtime improvement, real-time, deployment, or Active V2 safety claim is supported.

`FINAL_STATUS=BLOCKED_BYPASS_EQUIVALENCE_BY_TRACE_SIDE_EFFECT_ON_EXECUTION`

`FINAL_DECISION=FREEZE_PARTIAL_Q1_EVIDENCE_AND_DO_NOT_ADVANCE_VALIDATION_LADDER`

Only next task: `REPAIR_AND_REFREEZE_BYPASS_QA_TRACE_IDENTITY_V2`.
