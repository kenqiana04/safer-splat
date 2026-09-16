# Validation Plan

## Stage 0 — static scope and authority

- Verify exact authority base and all evidence-lock identities.
- Verify only implementation-manifest-authorized files change.
- Verify no geometry, map, controller, dynamics, dt, Supervisor priority, deadline, oracle, or statistics drift.

## Stage 1 — CPU/unit identity validation

- Syntax and schema validation.
- Archived and randomized bitwise `T_exec` versus plant-transition fixtures.
- L1 action-independence tests over actuator-bound representatives.
- L2 sequential-state and causal-sensitivity tests.
- Typed mismatch fail-closed tests.
- Bundle/token/trace identity completeness tests.

## Stage 2 — archived four-trial offline validation

Use only frozen evidence for trials 22, 28, 57, and 59. Reconstruct no new rollout. Require canonical predecessor L2 and next realized L1 endpoints to be bitwise identical, with identical certifier segment identities. Preserve any resulting FAIL verdict.

## Stage 3 — future GPU smoke

Only after a separately frozen small protocol: confirm zero identity mismatches, complete trace/finalization, 0.015 q runtime geometry, and no 0.025 q runtime authority. This is engineering validation, not efficacy evidence.

## Stage 4 — prospective validation

Freeze a new protocol, execution lock, result root, and analysis plan before data. Reference-arm reuse is not authorized unless independently frozen. Retain the 0.015 q hard-safety gate and the previously frozen noninferiority plan unchanged before outcomes.

No stage may retroactively modify the frozen V3 paired result.
