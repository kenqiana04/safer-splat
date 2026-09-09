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

## AF-003 — Direct-child frozen environment propagation

- Scope: task-local process orchestration.
- Symptom: the first continuation invocation of trial 50 called `--one` directly without the parent batch's frozen environment map and stopped before runtime startup with `CUDA_VISIBLE_DEVICES_MUST_EQUAL_1`.
- Fix: preserve the zero-runtime attempt, then invoke the affected trial with the exact existing `SMOKE_CONFIG.json` environment values (`CUDA_VISIBLE_DEVICES=1`, seed/user-site/bytecode settings, and the frozen CUBLAS workspace setting).
- Validation: trial 50 then loaded the exact map, passed startup, exited zero, finalized, and released GPU 1.
- Scientific impact: none; no state, goal, seed, trial ID, runtime, map, controller, solver, or deadline input changed.

## AF-004 — Direct-child GPU-release summary plumbing

- Scope: task-local output wrapper.
- Symptom: direct `--one` summaries leave `gpu_released_after_process` null because that field is normally added by the batch parent after the child exits.
- Fix: record the same post-process GPU UUID query in immutable sidecar files and merge it into corrected summaries.
- Validation: GPU 1 was clear after trials 50 and 90; no expensive trial was repeated for reporting.

## AF-005 — Trial-10 corrected summary reconstruction

- Scope: pure task-local reporting.
- Symptom: the preserved rerun summary carried the false stale-count blocker even though raw runtime evidence showed one committed terminal action, exact 1/1/1 trace cardinality, and `FINALIZED`.
- Fix: reconstruct a corrected summary from the preserved summary, raw trace, raw lock, and GPU-release fact while retaining the original harness exit code and blocker as provenance.
- Validation: selected/executed identity matches, all core hard-gate counters are zero, and no trial-10 GPU rerun was performed in this continuation.
