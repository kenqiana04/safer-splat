
# Active Runtime Public Cycle Composition V2 (DESIGN ONLY)

This package freezes a future composition root for the active runtime. It is
derived from PR #120 exact head `6c5c59dd083dc83661e56c4ddd3e62fa12497652`.
The PR #120 blocker is preserved: module-level implementations exist, but no
runtime-owned public API composes a complete active cycle.

The proposed owner is `ActiveCycleCoordinator`. It orchestrates typed frozen
stages, delegates every routing/selection decision to `Supervisor`, and uses
the existing `ActiveRunner.commit_active_decision` and trace/token mechanics.
No safety mathematics, candidate synthesis, controller change, rollout, GPU
execution, oracle, or performance claim is part of this task.

Read `PUBLIC_CYCLE_COMPOSITION_CONTRACT_V2.md` first. The implementation
ladder is deliberately Design -> Implement -> Revalidate -> Smoke; this task
stops at Design and validation.
