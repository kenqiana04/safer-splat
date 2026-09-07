# Report: Verify Active Harness BYPASS Equivalence V2

## Answer-first result

`FINAL_STATUS=BLOCKED_BYPASS_EQUIVALENCE_BY_TRACE_SIDE_EFFECT_ON_EXECUTION`

`FINAL_DECISION=FREEZE_PARTIAL_Q1_EVIDENCE_AND_DO_NOT_ADVANCE_VALIDATION_LADDER`

The frozen five-pair equivalence claim is **not established**. Q0 passed 11/11, but sentinel 50 never produced a finalized REFERENCE/BYPASS pair. Before correction, `PlantCommitAdapter` applied ACTIVE actuator admission to a BYPASS-delegated reference action and rejected component `0.10000000149011612` (`3dcccccd`) with `ACTUATOR_ADMISSION_REQUIRED`. The one authorized implementation-only correction restored exact reference delegation for Supervisor rule `BYPASS` while preserving the active rules' unchanged admission guard; 78/78 runtime tests passed afterward. On the fresh post-correction sentinel, the plant committed once, but the task-local QA adapter gave `TraceWriter` and `RuntimeStateSnapshot` different trial identifiers, so trace append raised `TRIAL_IDENTITY_MISMATCH`. Q2 was never started.

## Frozen identity and method boundary

Direct upstream PR #116 remained Open Draft at exact head `a8d7a3c9522583ad61dc9bc87585e41bb71a0f77`, base `design-active-runtime-assurance-implementation-v2` at `44111d32031409338058e5da2f7e7a1f8d873323`. The QA froze Stonehenge trial IDs `[10,30,50,70,90]`, sentinel-first order `[50,10,30,70,90]`, 500 native steps, float32 bit equality, fresh arm processes, and no post-data tolerance change. The task-local Option B reference adapter received `PASS_REFERENCE_CONTROL_PLANT_PATH_SOURCE_LOCK`.

The server used Python 3.10.20, PyTorch 2.1.2+cu118, CUDA 11.8, NumPy 1.26.4, Clarabel 0.10.0, and physical GPU 1 (RTX 4090). Config, dataparser, and checkpoint SHA-256 values matched the environment lock. The initial independent checkout lacked the read-only `data` symlink; that zero-step path-packaging invocation is preserved separately and is not counted as a real QA execution.

## Q1 chronology

1. Pre-correction REFERENCE trial 50: exit 0, 40 committed steps, `NOT_MOVING`.
2. Pre-correction BYPASS trial 50: exit 1 before commit, `M_BYPASS_HARNESS_INTERVENTION`.
3. Bug-only correction: commit `f722b8d108138f4592e4a1d6b21594a43d823adc`; no bound, tolerance, candidate, geometry, deadline, terminal, or oracle change.
4. Post-correction REFERENCE trial 50: exit 0, the same 40 committed-step trace SHA-256 `49321867ec03644e7230d5c168a192360de3c482001a8eaa34650b2c9eb36729`.
5. Post-correction BYPASS trial 50: one plant commit occurred, then task-local trace append failed with `TRIAL_IDENTITY_MISMATCH`; no finalized BYPASS trace or trace lock exists.

There were 4 real Q1 arm invocations. Continuing correctly would require another fresh sentinel pair plus the eight Q2 arms, projecting 14 real invocations and exceeding the frozen hard cap of 12. The runtime correction cap of one is also exhausted. No further run is authorized under this execution lock.

## Comparison and evidence boundary

Total finalized compared steps are 0. Exact reference-action equivalence, supplied/selected/executed equivalence, state-trajectory equivalence, solver/branch equivalence, termination equivalence, and PlantCommit transparency therefore remain `NOT_ESTABLISHED`. Token semantic mutation count is 0; finalized trace-lock count is 0. The mismatch register contains the original `M_BYPASS_HARNESS_INTERVENTION` and the stopping `M_TRACE_SIDE_EFFECT_ON_EXECUTION`.

Protected `run.py`, `cbf/**`, `dynamics/**`, `splat/**`, and frozen specification/design artifacts have zero diff. The only runtime diff is the explicitly authorized `plant_commit.py` correction and its test. Scientific oracle, `ACTIVE_RUNTIME_ON`, and official100 execution counts are all 0. GPU 1 ended at 0% utilization with no task-owned compute process.

## Nonclaims and handoff

This blocked QA supports no Active V2 safety conclusion and no claim of collision reduction, progress improvement, controller efficacy, runtime improvement, zero overhead, real-time behavior, deployment readiness, or physical safety. The narrow observed fact is that the original PR #116 global PlantCommit guard intervened in BYPASS; after its authorized correction, the current task-local trace identity bug prevented completing equivalence.

Remaining blockers are: align the task-local TraceWriter and state-snapshot trial IDs, pre-test trace append through `ActiveRunner.commit_bypass`, and obtain a new frozen execution protocol/count authorization. Only next task: `REPAIR_AND_REFREEZE_BYPASS_QA_TRACE_IDENTITY_V2`. It must preserve all current evidence and may not run ACTIVE, the oracle, or official100.
