# ACTIVE_RUNTIME_SMOKE_V2 — blocked evidence report

## Answer first

`FINAL_STATUS=BLOCKED_ACTIVE_RUNTIME_SMOKE_BY_WIRING`

`FINAL_DECISION=PRESERVE_FIRST_SMOKE_EVIDENCE_AND_REPAIR_ONLY_TASK_LOCAL_WIRING`

The fixed smoke stopped fail-closed after trial 10. The real Stonehenge checkpoint loaded on GPU 1, ACTIVE startup passed, one certified terminal action was selected and committed, one trace record was persisted, and the runtime trace finalized to a valid one-record lock. Immediately afterward, the task-local smoke runner accessed `TrialFinalizationResult.lock`; the frozen runtime type exposes `trace_lock`. That `AttributeError` set process exit code 2. No runtime source, controller, map, geometry, solver, or deadline value was changed, and no trial was rerun.

Trials 50 and 90 were not started after the first hard blocker. The only next task is `REPAIR_ACTIVE_SMOKE_WIRING_V2`.

## Frozen upstream and inputs

- PR #132 was independently verified as Open Draft, titled `[Draft] Revalidate active runtime milestone after trace repair V2R1`, with head `8ba397bee31d4c42deebc52104c6409336a96fd9` and base `aa5ffc6216ba92ab0bed5842edcee0b2142faba1`.
- The PR #132 runtime tree is exact (`c60be4c1977932c53b37e500e96c5ddf7cd2d820`) and runtime diff is zero.
- The quick package gate passed 164/164 under the upstream frozen Windows raw-byte semantics. A Linux checkout-only run exposed the known line-ending sensitivity of an old byte lock; its canonical Git tree was identical, so no source repair was made.
- Environment: `/disk1/zlab/conda_envs/safer_splat_official`, Python 3.10.20, PyTorch 2.1.2+cu118, CUDA 11.8, one visible NVIDIA GeForce RTX 4090 through `CUDA_VISIBLE_DEVICES=1`.
- Map identity: `c9eade9ca89b741768a0ca33b3a755b2656402864f121aefdceaed4b0174f7c8`; all three frozen artifact hashes matched.
- Deadline profile identity: `deadline-profile:sha256:49e8978a1263fa6a8b0ce0506dae56c800ed8a39f94f9b2d74484a740c113045`, created from 1.0 s cycle, 0.8 s latest safe commit, 0.2 s warning reserve, no stage budgets, and `MONOTONIC_CLOCK_ACTIVE_SMOKE_V2`.

## Execution telemetry

| Trial | Started | Cycles | Plant commits | Primary | Alternative | Backup | Terminal | Boundary | Finalization | Process |
|---:|---|---:|---:|---:|---:|---:|---:|---:|---|---:|
| 10 | PASS | 1 | 1 | 0 | 0 | 0 | 1 | 0 | runtime `FINALIZED` | 2 |
| 50 | not run | 0 | 0 | 0 | 0 | 0 | 0 | 0 | not run | 2 |
| 90 | not run | 0 | 0 | 0 | 0 | 0 | 0 | 0 | not run | 2 |

The single resolved cycle took 0.129847 s (median/p95/max are identical for n=1). This is engineering telemetry only and supports no real-time or deadline guarantee. Deadline observation counts were not copied into the trial summary because the post-finalization wiring exception occurred before the counter-copy block; they are therefore not reported as zero.

## Trace and hard-stop audit

Trial 10 produced exactly one persisted trace line and a valid runtime lock with `record_count=1` and identity `trace:sha256:89b84f00e43f9e73a7d71fda1eb2ea90150abddb2bcfa2ea5bc2a140ed163fcc`. The trace records matching selected/executed identities for the committed certified-terminal action. The runtime cardinality is exact (1 cycle / 1 trace / 1 locked record).

The child summary's lock fields remain null/zero because its extraction code raised before assigning them. This preserved discrepancy is the first counterexample and is not silently repaired in this task.

GPU 1 had no task-owned process after trial 10. Counts for CUDA OOM, nonfinite values, action-bound violations, selected/executed identity mismatch, evidence-incomplete, and recovery-required were all zero. Scientific oracle, official100, extra trials, and reruns were all zero.

## Evidence boundary

This run does not establish the requested three-trial smoke PASS and does not authorize `ACTIVE_RUNTIME_PILOT_V2`. It also does not establish efficacy, collision reduction, progress improvement, real-time performance, or deployment readiness. It isolates a task-local summary-wiring defect after a valid runtime finalization. The minimal next step is to repair that wiring under a separate authorization while preserving this attempt.
