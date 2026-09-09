# Repair trace/commit evaluation eligibility gate V2R1

## Answer-first result

`ActiveCycleCoordinator.finalize_trial()` now rejects ordinary finalization for sessions in `EVIDENCE_INCOMPLETE` or `RECOVERY_REQUIRED`. It returns the existing typed `RECOVERY_REQUIRED` result, with `trace_lock=None`, `retry_allowed=false`, `recovery_required=true`, and an explicit `TRIAL_EVALUATION_INELIGIBLE:<status>` reason. It does not call the runner or `TraceWriter` finalizer and preserves the non-ready session state.

The repair closes PR #130's sole C12 blocker without changing shared trace, commit, plant, token, Supervisor, certificate, oracle, or BYPASS semantics. C01-C12 pass 12/12, E01/E02 pass 2/2, PR #129 tests pass 28/28, and the current runtime suite passes 164/164.

The exact frozen PR #119 BYPASS protocol was then rerun with trial order `50,10,30,70,90`, one fresh process per arm. All 5/5 pairs passed across 732/732 joined steps with bit-exact action/state/branch/termination identity, zero mismatches, zero interventions, zero token mutations, and 5/5 complete BYPASS trace locks. `BYPASS_REVALIDATION_REQUIRED=false`.

## Evidence boundary

- Runtime source change: only `reproduction/runtime/active_runtime_assurance_v2/active_cycle.py`.
- Direct test addition: `test_evaluation_eligibility_gate_v2r1.py`.
- Protected runtime diff: 0.
- No WAL, journal, trace schema, oracle, controller, dynamics, map, or certificate change.
- No PR #127 96-scenario rerun.
- No real ACTIVE rollout, ACTIVE GPU rollout, smoke, scientific oracle, or official100 execution.
- The 10 GPU-backed arms were solely the explicitly required frozen BYPASS QA, not ACTIVE scientific trials.

One first invocation exited before any real arm because the new server checkout lacked its inherited `PYTHONPATH` and read-only Stonehenge data link. It produced 0 solver steps, 0 plant commits, 0 trace locks, and 0 comparisons. The directory was preserved; only task packaging was repaired, consistent with PR #119's frozen infrastructure-only exception pattern.

## Decision

`FINAL_STATUS=PASS_REPAIR_TRACE_COMMIT_EVALUATION_ELIGIBILITY_GATE_V2R1`

`FINAL_DECISION=ADVANCE_MILESTONE_RECONFORMANCE_POST_TRACE_V2R1`

Only next task: `REVALIDATE_ACTIVE_RUNTIME_MILESTONE_POST_TRACE_V2R1`.
