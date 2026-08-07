## Summary

Freeze a Core causal control-architecture specification from PR #83/#84/#86/#87/#89/#90/#91 evidence. No controller, dynamics, B0-B3, map, dataset, cohort, formal run, oracle, sweep, or implementation is changed.

## Decision

- Preserved mathematical model: position-first Euler; immediate position authority is zero and `p_(k+2)` is first control-affected.
- L0-L5 separates Start-Safe/admission, immediate segment, conceptual L2 future safety, witness recoverability, finite alternatives, and terminal/fail-close.
- Historical B0-B3 are remapped as frozen diagnostics only.
- Four independent reviews select CASE_B.
- **Only next task:** `WRITE_CORE_V2_CAUSAL_INCREMENT_SPECIFICATION_V1`.

## Claim boundary

This is a specification-only local structural-gap decision, not Core V2, a new safety guarantee, or a performance result.
