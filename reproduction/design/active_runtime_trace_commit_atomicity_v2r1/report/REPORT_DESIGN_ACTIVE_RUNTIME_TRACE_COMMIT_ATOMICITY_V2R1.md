# Report: Design Active Runtime Trace/Commit Atomicity V2R1

## Answer-first decision

`FINAL_STATUS=PASS_ACTIVE_RUNTIME_TRACE_COMMIT_ATOMICITY_V2R1_DESIGN`

`FINAL_DECISION=FREEZE_TRACE_COMMIT_CONSISTENCY_V2R1_AND_ADVANCE_IMPLEMENTATION`

TRACE-F02 is caused by the actual plant-first sequence: the plant and token can mutate before `TraceWriter.append`, so a raising append loses the returned receipt at the Coordinator boundary without undoing execution. TRACE-F03 is caused by `TraceWriter.finalize` publishing `_lock` before disk writes while Coordinator changes the session to FINALIZED only after the call returns.

The mechanically selected architecture is **Option B — SOFTWARE_TRANSACTION_STATE_MACHINE**. It is the minimum option that exposes PREPARED/COMMITTED/TOKEN_APPLIED/TRACE_RECORDED/COMPLETE/RECOVERY_REQUIRED stages, retains confirmed execution facts, and closes the two same-process faults without importing durable filesystem assumptions. Option A lacks mechanically distinguishable transaction stages; Option C is deferred because process-crash/restart recovery is outside the current engineering-smoke evidence boundary.

## Frozen semantics

- Current order: SupervisorDecision -> PlantCommit -> token mutation -> trace append -> return.
- Current finalize order: construct and publish `_lock` -> write trace -> write lock -> return -> session FINALIZED.
- Confirmed commit is never erased by trace/token/finalize failure; no fake rollback or safe-stop claim is allowed.
- `PLANT_OUTCOME_UNRESOLVED` forbids retry and ordinary next-cycle execution.
- `COMMITTED_TOKEN_INCOMPLETE`, `COMMITTED_TRACE_INCOMPLETE`, and `FINALIZATION_INCOMPLETE` force non-ready session states.
- Finalization retry is explicit and idempotent only for an immutable same-trial, same-content record set.
- Memory-only consistency is supported; crash durability and restart recovery are not.
- Smoke decision: `SMOKE_ALLOWED_WITH_MEMORY_ONLY_FAIL_CLOSE`, subject to all downstream gates and separate authorization.
- Journal decision: `JOURNAL_NOT_REQUIRED_FOR_CURRENT_CONTRACT`.
- Shared TraceWriter finalization change means `BYPASS_REVALIDATION_REQUIRED=true`.
- Incomplete or unresolved evidence is `EVALUATION_INELIGIBLE` for the posthoc oracle.

## Design verification

- Failure classes: 13.
- Architecture options compared: 3.
- Invariants: 28.
- Future implementation tests: 24.
- Symbolic scenarios: 46.
- Model counterexamples: 0.
- Validator: PASS_TRACE_COMMIT_CONSISTENCY_DESIGN_V2R1_VALIDATION (40/40).
- Runtime and production source diff: 0.
- Real ACTIVE/GPU/smoke/oracle/official100/real-BYPASS: 0/0/0/0/0/0.

## Implementation boundary

The next task may add `commit_transaction.py`, additive result/state types, and minimal ActiveRunner/Coordinator/TraceWriter wiring. PlantCommitAdapter, BackupTokenStore authority, Supervisor authority, and oracle logic remain unchanged. No implementation was performed here.

Only next task: `IMPLEMENT_ACTIVE_RUNTIME_TRACE_COMMIT_ATOMICITY_V2R1`.
