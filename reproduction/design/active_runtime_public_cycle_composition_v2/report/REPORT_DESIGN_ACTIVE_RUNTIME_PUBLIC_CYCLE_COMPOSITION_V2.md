# REPORT_DESIGN_ACTIVE_RUNTIME_PUBLIC_CYCLE_COMPOSITION_V2

## Answer-first decision

- **Upstream:** PR #120 exact Open Draft head `6c5c59dd083dc83661e56c4ddd3e62fa12497652`; blocker preserved.
- **Root cause:** `MISSING_PUBLIC_ACTIVE_CYCLE_ORCHESTRATION` (CE-001). Existing module contracts are present, but no runtime-owned public API composes trial admission, typed per-cycle stages, routing, arbitration, commit, token update, trace, and cycle result.
- **Composition owner:** future `ActiveCycleCoordinator` (design only), with no safety policy. `Supervisor.route_transition` owns routing, `Supervisor.arbitrate` owns selection, and `PlantCommitAdapter.commit` owns plant effects.
- **Order:** `CYCLE_BEGIN -> L1 -> P0 -> fresh binding -> C0 -> L2 -> L3 -> routing/arbitration -> commit -> token update -> trace -> result`.
- **Deadline:** `DeadlineTracker` observes; Supervisor interprets. Warning forbids new high-cost search; expired forbids new search and is not an unsafe/collision claim.
- **Alternative/backup/terminal:** native existing alternatives only and fresh C0/L2/L3 binding; backup is validated before Supervisor selection; terminal is route-admitted; goal-hold disabled.
- **Boundary:** `ASSURANCE_BOUNDARY_NO_CERTIFIED_ACTION` means no PlantCommit, one no-action trace, `committed=false`, and no executed next state.
- **Validation:** 43-rule exact-one routing design, 32 scenarios, 30 PCC invariants, zero model-check counterexamples, static validator PASS. Runtime/protected diff, rollout, GPU, oracle, and scientific metrics are all zero.

## Why this is not an implementation or experiment

PR #120 explicitly found genuine E2E 0/6 because the public composition root is
absent. This task therefore freezes an implementation-ready interface and
validation ladder only. It does not call runtime modules, alter controller or
map semantics, revalidate conformance, run smoke, or authorize an active
experiment. The next task must implement the composition and then revalidate
the active contracts before any smoke.

## Required handoff

Implement `active_cycle.py` (and only additive route/type APIs if needed),
reuse existing ActiveRunner token/trace/commit boundaries, preserve BYPASS, and
stop on any authority ambiguity. Follow `POST_COMPOSITION_VALIDATION_LADDER_V2.md`.

**FINAL_STATUS:** `PASS_ACTIVE_RUNTIME_PUBLIC_CYCLE_COMPOSITION_V2_DESIGN`

**FINAL_DECISION:** `FREEZE_PUBLIC_CYCLE_COMPOSITION_DESIGN_AND_ADVANCE_IMPLEMENTATION_DAG`

**Only next task:** `IMPLEMENT_ACTIVE_RUNTIME_PUBLIC_CYCLE_COMPOSITION_V2`
