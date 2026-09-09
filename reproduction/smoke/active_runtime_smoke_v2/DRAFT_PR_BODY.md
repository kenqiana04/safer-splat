## Summary

Runs the first authorized real Stonehenge ACTIVE smoke from exact PR #132 and preserves the first fail-closed counterexample.

Trial 10 loaded the frozen map on GPU 1, passed startup, committed one Supervisor-selected certified-terminal action, persisted one trace record, and finalized a valid one-record trace lock. The task-local runner then raised `AttributeError` while reading `TrialFinalizationResult.lock`; the frozen result field is `trace_lock`. The process exited 2, and trials 50/90 were not started. No trial was rerun.

## Evidence boundary

- runtime/production source diff: 0
- controller/map/geometry/solver/deadline changes: 0
- extra trials / reruns: 0 / 0
- scientific oracle / official100: 0 / 0
- GPU 1 released after trial 10: PASS
- executed runtime trace cardinality: 1 cycle / 1 trace / 1 locked record
- three-trial smoke PASS: not established

`FINAL_STATUS=BLOCKED_ACTIVE_RUNTIME_SMOKE_BY_WIRING`

`FINAL_DECISION=PRESERVE_FIRST_SMOKE_EVIDENCE_AND_REPAIR_ONLY_TASK_LOCAL_WIRING`

Only next task: `REPAIR_ACTIVE_SMOKE_WIRING_V2`.
