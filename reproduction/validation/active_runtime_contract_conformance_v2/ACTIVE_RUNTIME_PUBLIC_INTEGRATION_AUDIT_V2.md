# ACTIVE Runtime Public Integration Audit V2

## Scope

This is a CPU-only conformance audit of the immutable PR #116 runtime at PR #119 exact head. No runtime source, controller, plant, map, candidate library, or experiment was modified or executed.

## Public entrypoint

`ACTIVE_RUNTIME_ON` is selected by `ActiveRunner(mode=RuntimeMode.ACTIVE_RUNTIME_ON, ...)`; `startup()` validates authorities and requires an explicit `RuntimeDeadlineProfile`. The public methods are `commit_active_decision, commit_bypass, finalize_trace, startup`. There is no public `run_cycle`, `step`, `execute_cycle`, `process_snapshot`, or `run_active_cycle` entrypoint.

`commit_active_decision(snapshot, decision)` is a commit shell. Its caller must already provide the `SupervisorDecision`; it does not consume a state snapshot and execute the frozen sequence. `Supervisor.arbitrate` likewise consumes precomputed candidate, L3, backup, terminal, and deadline objects and does not call StartAdmission, L1, proposal, C0, L2, L3, alternative enumeration, or deadline tracking.

## Required frozen cycle versus available path

The normative path is `I0a/I0b → R0 → L1 → P0 → C0 → L2/H1 → L3 → alternative (if lawful) → Supervisor arbitration → PlantCommit/backup/terminal/boundary → trace`. The PR #116 modules provide individually callable adapters and a Supervisor, but no public composition root that performs that whole cycle. The validation harness therefore does not compose a fake cycle; the missing public path is recorded as the first integration counterexample.

## Authority audit

Static/module tests support Supervisor as the only `arbitrate` owner and PlantCommitAdapter as the only plant/dynamics owner. This does not establish integrated conformance because the runtime does not itself route all producers through those owners. No L2/L3/alternative/oracle import directly commits plant state, and no post-hoc oracle is imported.

## Decision

`BLOCKED_ACTIVE_CONFORMANCE_BY_INTEGRATION_ORCHESTRATION_GAP`. The six E2E cases cannot be credited as genuine public-runtime executions. No runtime correction is attempted; the first counterexample is preserved in `first_counterexample.json`.
