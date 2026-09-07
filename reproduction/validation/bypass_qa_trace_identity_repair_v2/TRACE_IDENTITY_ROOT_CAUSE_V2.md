# Trace Identity Root Cause V2

## Single root cause

PR #117's task-local `run_trial` function independently formatted the same native trial index twice. At upstream `reference_trial_adapter.py:155`, the BYPASS writer was bound as `stonehenge-trial-{trial_id}`. At upstream line 231, the runtime snapshot was bound as `stonehenge-{trial_id}`. For native index 50 these became `stonehenge-trial-50` and `stonehenge-50`.

This is one deterministic task-local identity-plumbing defect: two formatter authorities represented one trial. It is not a runtime, controller, plant, actuator, geometry, deadline, terminal, backup, alternative, or oracle defect.

## Exact flow

1. The native trial index comes from the frozen pipeline order `[(Q1,50),(Q2,10),(Q2,30),(Q2,70),(Q2,90)]` and the CLI `--trial-id` integer.
2. REFERENCE and BYPASS both enter the same task-local `run_trial(arm, trial_id, ...)` adapter. REFERENCE records the native integer but does not use `TraceWriter`.
3. Before repair, BYPASS constructed `TraceWriter(f"stonehenge-trial-{trial_id}")`.
4. Before repair, every BYPASS cycle constructed `RuntimeStateSnapshot.create(f"stonehenge-{trial_id}", ...)`.
5. The arm name was not literally embedded in either string, but the two identities were independently normalized and therefore diverged.
6. `ActiveRunner.commit_bypass` first obtains the real `Supervisor.bypass_decision`, then calls `PlantCommitAdapter.commit`, and only after a successful plant commit calls `_append`.
7. `_append` creates a `TraceStepRecord` with `snapshot.trial_id`. `TraceWriter.append` compares it strictly to the writer-bound trial ID and raises `TRIAL_IDENTITY_MISMATCH`.
8. Consequently the post-correction PR #117 invocation had one plant commit before the trace exception, but no finalized comparable trace.

## Repair boundary

The repair creates one formatter, `make_canonical_trial_identity(native_trial_index)`, before either arm-specific path. Its result binds the snapshot, writer, per-step metadata, manifest, comparison join key, and trace lock. `REFERENCE` and `BYPASS` remain separate arm metadata and never enter the canonical trial string.

`TraceWriter.append` and `TRIAL_IDENTITY_MISMATCH` are unchanged. No exception is caught, coerced, normalized, or weakened. The protected reference control/plant/termination expressions and all PR #116 runtime modules remain unchanged.

**Root-cause verdict:** `UNIQUE_TASK_LOCAL_DUAL_FORMATTER_IDENTITY_DIVERGENCE`.
