# Report: Repair and Refreeze BYPASS QA Trace Identity V2

## Answer-first result

`FINAL_STATUS=PASS_BYPASS_QA_TRACE_IDENTITY_REPAIR_V2_REFREEZE`

`FINAL_DECISION=FREEZE_REPAIRED_TRACE_IDENTITY_AND_AUTHORIZE_FRESH_BYPASS_EQUIVALENCE_EXECUTION_TASK`

The PR #117 blocker had one deterministic task-local cause: the BYPASS adapter bound `TraceWriter` to `stonehenge-trial-50` but bound `RuntimeStateSnapshot` to `stonehenge-50`. The real PlantCommit completed before strict trace append rejected the mismatch. The runtime guard behaved correctly and remains unchanged.

The repaired adapter creates `STONEHENGE_TRIAL_050` once through `make_canonical_trial_identity(50)` and directly reuses it for the runtime snapshot, writer, arm manifest, trace metadata, and `(canonical_trial_id, cycle_index)` comparison key. `REFERENCE` and `BYPASS` are independent arm metadata and never enter the trial ID.

## Verification

The CPU-only repair suite passed 11/11. It exercised the real `Supervisor.bypass_decision`, `PlantCommitAdapter`, `ActiveRunner.commit_bypass`, `TraceWriter.append`, finalize, and immutable trace lock with one commit and one record. Five frozen native IDs pair across both arms. Negative cases prove mismatched trial IDs, arm-encoded writer IDs, and append-after-finalize still fail.

The PR #117 BYPASS-only PlantCommit correction remains unchanged: the reference component `0.10000000149011612` delegates bit-exactly in BYPASS, while non-BYPASS/ACTIVE admission stays strict. All 78 PR #116 runtime tests pass. Reference control, QP, plant transition, and termination anchors retain `PASS_REFERENCE_CONTROL_PLANT_PATH_SOURCE_LOCK`.

Production/runtime, `run.py`, `cbf/**`, `dynamics/**`, `splat/**`, authority specifications, and designs have zero diff from PR #117. The only PR #117 task-local edits are identity metadata in the adapter, manifest runner, and comparator. Historical locks, mismatch evidence, execution ledger, report, and failed traces remain immutable and cannot serve as V2R1 paired evidence.

## Refrozen protocol and boundary

V2R1 freezes IDs `[10,30,50,70,90]`, order `[50,10,30,70,90]`, fresh arm processes, fresh pairs, float32 bit-exact action/state checks, exact typed solver/branch equality, and exact termination reason/step. The independent counter starts at zero; hard cap is exactly 10 real arm executions and correction quota is zero. Sentinel failure blocks all remaining trials and cannot be repaired or rerun inside that execution task.

This task executed zero real REFERENCE arms, zero real BYPASS arms, zero GPU QA, zero ACTIVE, zero scientific oracle, and zero official100. It does not establish BYPASS equivalence. The future input/execution files are inactive templates; only the next independently authorized task may instantiate them before `REF50_new`.

Only next task: `EXECUTE_REFROZEN_BYPASS_EQUIVALENCE_V2R1`.
