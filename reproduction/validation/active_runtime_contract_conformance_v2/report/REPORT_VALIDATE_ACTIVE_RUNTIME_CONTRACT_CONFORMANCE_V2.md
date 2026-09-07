# Report: Validate Active Runtime Contract Conformance V2

## Answer first

- Upstream: PR #119 exact Open Draft head `b4ff579cf6a2bcffd0661cd39eb925aa4f3a5d27`; its `PASS_REFROZEN_BYPASS_EQUIVALENCE_V2R1` evidence remains unchanged (5/5 pairs, 732 compared steps, all mismatch counters zero).
- Public ACTIVE entrypoint: `ActiveRunner(..., RuntimeMode.ACTIVE_RUNTIME_ON).startup()` plus `commit_active_decision(snapshot, decision)`. There is no `run_cycle`/`step`/`execute_cycle`/`process_snapshot`.
- Missing path: no public composition root consumes the complete frozen sequence `I0 → R0 → L1 → P0 → C0 → L2 → L3 → alternative → Supervisor → PlantCommit/backup/terminal/boundary → trace`.
- Selection owner: `Supervisor.arbitrate` at module scope; plant owner: `PlantCommitAdapter.commit` at module scope. These module-level facts are not sufficient for integrated conformance.
- Canonical order: not executable through a public runtime cycle; only C0→L2→L3 is internally present in `Supervisor.certify_candidate`.
- Transition coverage: 43/43 table rows have explicit assertions; critical public-path rows are blocked by the same integration gap.
- E2E: 0/6 genuine runtime cases; they were not fabricated by task-local orchestration.
- First counterexample: `CE-001 INTEGRATION_ORCHESTRATION_GAP`.

## CPU-only evidence boundary

The deterministic tests use only fake geometry/certifier, proposal, clock, and witness backends. They preserve the actual Supervisor, ActiveRunner commit shell, BackupTokenStore, TerminalRuntime, C0Admission, PlantCommitAdapter, and TraceWriter. The public API inspection and startup probe are real runtime calls. No runtime source was modified, no controller or map was changed, and no real ACTIVE/GPU/scientific-oracle/official100 execution occurred.

## Contract findings

Module-scope checks support the frozen geometry (0.015/0.010/0.025 m, rho=0), actuator admission (inclusive ±0.1 and no clipping), L1 once-per-cycle candidate-independent result, H1 equations, L3 preparation-only bundle, Supervisor priority, typed UNKNOWN handling, BackupTokenStore lifecycle, terminal membership/certificate/eligibility separation, assurance-boundary no-plant behavior, and immutable trace/no-oracle edge.

The missing public cycle means the validation cannot establish that all action-producing paths pass through Supervisor, that all phase transitions are enforced in one runtime decision, or that deadline/alternative/backup/terminal routing is integrated. The task therefore stops after the first counterexample and does not claim conformance.

## Final decision

`FINAL_STATUS=BLOCKED_ACTIVE_CONFORMANCE_BY_INTEGRATION_ORCHESTRATION_GAP`

`FINAL_DECISION=DO_NOT_ENTER_ACTIVE_RUNTIME_SMOKE; DESIGN_PUBLIC_ACTIVE_CYCLE_COMPOSITION`

Only next task: `DESIGN_ACTIVE_RUNTIME_PUBLIC_CYCLE_COMPOSITION_V2`.
