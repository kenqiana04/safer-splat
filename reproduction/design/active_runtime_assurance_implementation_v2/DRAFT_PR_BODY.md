## Scope

Design-only freeze for an additive Active Runtime Assurance V2 implementation. Exact base: PR #114 / `c924a959b1aa18b446a1d3c85afbe4f897604a84`. PR #107–#114 remain untouched.

## Frozen design

- `ADDITIVE_ACTIVE_RUNTIME_DRIVER`; production edit requirement is zero.
- `Supervisor.arbitrate` is the sole selection authority.
- `PlantCommitAdapter.commit` is the sole dynamics/plant authority.
- successful Clarabel CBF-QP is the primary proposal; `u_des` is reference only.
- C0 rejects out-of-box proposals under inclusive `[-0.1,0.1]^3`; no clip.
- one candidate-independent L1 result per cycle with fresh per-attempt bindings.
- every candidate follows C0 → L2 → L3; V2 injects G3 / 0.025 m / rho_seg=0 and bans the V1 0.11 loader.
- current native-alternative inventory is zero; no synthetic source is introduced.
- immutable bundle and mutable backup-token handle remain separate, with atomic post-commit handoff.
- terminal selection requires exact certificate and eligibility; goal-hold stays disabled.
- numeric deadline profile is an ACTIVE startup prerequisite; no number is invented here.
- exact action roles are logged; immutable trace locks before the separate PR #114 oracle runs; no feedback edge exists.
- all 43 frozen transition rules map exactly once; 30 invariants and 28 scenarios are frozen.

## Evidence boundary

No runtime implementation, production mutation, GPU, rollout, smoke, pilot, benchmark, formal collection, or tuning. This PR establishes no efficacy, collision reduction, real-time, physical-safety, or deployment claim.

## Validation

- abstract architecture model checker: 0 counterexamples
- static design validator: `PASS_ACTIVE_RUNTIME_ASSURANCE_IMPLEMENTATION_V2_DESIGN_VALIDATION`
- reviewer: `PASS_ACTIVE_RUNTIME_ASSURANCE_IMPLEMENTATION_DESIGN_FROZEN`

`FINAL_STATUS=PASS_ACTIVE_RUNTIME_ASSURANCE_IMPLEMENTATION_V2_DESIGN`

`FINAL_DECISION=FREEZE_ACTIVE_RUNTIME_IMPLEMENTATION_DESIGN_AND_ADVANCE_IMPLEMENTATION_DAG`

Only next task: `IMPLEMENT_ACTIVE_RUNTIME_ASSURANCE_V2` (not executed here).
