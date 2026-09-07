# Scope

This PR repairs only the task-local QA trace/trial identity plumbing that blocked PR #117 and freezes a new independent BYPASS equivalence protocol V2R1. It runs no real Stonehenge arm and makes no equivalence, safety, performance, or deployment claim.

## Root cause and repair

PR #117 created `TraceWriter("stonehenge-trial-50")` but `RuntimeStateSnapshot("stonehenge-50")` in the same task-local adapter. `ActiveRunner.commit_bypass` completed the plant commit and then strict trace append raised `TRIAL_IDENTITY_MISMATCH`.

One formatter now maps native index 50 to `STONEHENGE_TRIAL_050`. The same value binds snapshot, writer, manifest, trace metadata, and comparison join key. `REFERENCE` and `BYPASS` remain separate arm fields. `TRIAL_IDENTITY_MISMATCH` is unchanged and negative-tested.

## Validation boundary

- CPU repair tests: 11/11 PASS, including real Supervisor/PlantCommit/ActiveRunner/TraceWriter one-step flow.
- PR #116 runtime regression: 78/78 PASS.
- Reference source lock: `PASS_REFERENCE_CONTROL_PLANT_PATH_SOURCE_LOCK`.
- Production/runtime and PR #107–#116 protected diff: 0.
- Real REFERENCE/BYPASS arms, GPU QA, ACTIVE, oracle, official100: 0.
- PR #117 evidence remains immutable historical evidence except the three explicitly allowed task-local QA plumbing files.

## Refrozen V2R1

IDs remain `[10,30,50,70,90]`, sentinel-first `[50,10,30,70,90]`, with fresh processes and fresh pairs. The new counter starts at zero, hard cap is 10 arm executions, correction quota is zero, and old PR #117 traces cannot be paired. Equality remains float32 bit-exact with exact typed solver/branch and termination reason/step.

`FINAL_STATUS=PASS_BYPASS_QA_TRACE_IDENTITY_REPAIR_V2_REFREEZE`

`FINAL_DECISION=FREEZE_REPAIRED_TRACE_IDENTITY_AND_AUTHORIZE_FRESH_BYPASS_EQUIVALENCE_EXECUTION_TASK`

Only next task: `EXECUTE_REFROZEN_BYPASS_EQUIVALENCE_V2R1`. This PR does not execute it.
