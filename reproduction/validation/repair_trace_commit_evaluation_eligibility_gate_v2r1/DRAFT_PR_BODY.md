## Purpose

Close PR #130's sole `CORE_VALIDATION_EVALUATION_ELIGIBILITY_GAP` with a minimal trial-lifecycle guard, then rerun the exact core and frozen PR #119 BYPASS evidence required by the protocol.

## Repair

- Only `active_cycle.py` changes at runtime.
- `finalize_trial()` returns the existing `TrialFinalizationResult(RECOVERY_REQUIRED, ...)` for `EVIDENCE_INCOMPLETE` and `RECOVERY_REQUIRED` sessions.
- No runner/TraceWriter finalization call, no ordinary lock, no `FINALIZED` transition, no retry, and the original non-ready session status is preserved.
- READY, evidence-complete BLOCKED, exact same-content retry, FINALIZING, and FINALIZED semantics remain unchanged.

## Validation

- C01-C12: 12/12 PASS; C12 closed.
- E01/E02: 2/2 PASS.
- Lightweight properties: 6/6 PASS.
- PR #129 tests: 28/28 PASS.
- Current runtime regression: 164/164 PASS.
- Frozen PR #119 BYPASS: 5/5 pairs PASS, 732/732 joined steps exact, 0 mismatches/interventions/token mutations, 5/5 trace locks complete.
- Protected runtime diff: 0.
- `BYPASS_REVALIDATION_REQUIRED=false`.

The first server invocation was preserved as an infrastructure-only packaging event: it ended before any real arm with zero solver steps, plant commits, traces, or comparisons. The final run used unchanged source/protocol/locks/data and the frozen 10-arm cap.

## Scope boundary

No PR #127 96-case rerun, real ACTIVE trial, ACTIVE GPU rollout, smoke, oracle, official100, WAL/journal, trace schema, map, controller, dynamics, or certificate change.

`FINAL_STATUS=PASS_REPAIR_TRACE_COMMIT_EVALUATION_ELIGIBILITY_GATE_V2R1`

`FINAL_DECISION=ADVANCE_MILESTONE_RECONFORMANCE_POST_TRACE_V2R1`

Only next task: `REVALIDATE_ACTIVE_RUNTIME_MILESTONE_POST_TRACE_V2R1`.
