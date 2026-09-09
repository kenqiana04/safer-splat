# TASK_LOCAL_NONCORE_AUTOFIX_LOG

## AF-001 — Frozen finalization API field

- Scope: task-local smoke runner.
- Symptom: `TrialFinalizationResult.lock` raised after successful runtime finalization.
- Fix: use the unique frozen field `TrialFinalizationResult.trace_lock` for identity and record count.
- Validation: dataclass field check PASS; no runtime source changed.
- Evidence handling: the first trial-10 trace, lock, summary, and report were preserved.

## AF-002 — Stale plant commit summary ordering

- Scope: task-local smoke summary/counter ordering.
- Symptom: the runner evaluated initialized `summary["plant_commit_count"] == 0` before copying `stack["plant"].commit_count == 1`.
- Fix: refresh finalization, trace, token, plant, stage, and deadline telemetry before count-dependent gates.
- Consistency gate: require plant count to match the runtime stack, trace count to match the writer, lock count to match trace count, and committed action-role counts to sum to the plant count.
- Validation: syntax/import, task-local dataclass wiring, and synthetic consistency checks must pass before continuing GPU trials.
- Evidence handling: the preserved trial-10 raw result is sufficient; trial 10 is not rerun.

No runtime, method, controller, map, geometry, dynamics, solver, deadline, oracle, or scientific-contract change is authorized or made by these fixes.
