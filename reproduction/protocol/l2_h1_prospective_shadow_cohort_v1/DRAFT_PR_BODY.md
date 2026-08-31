## Result

`PASS_L2_H1_PROSPECTIVE_SHADOW_COHORT_PROTOCOL_FREEZE_V1` (`CASE_A`).

## Frozen scope

- Exact upstream: PR #99 at `17bec44c51207bf7f831db724e108b86adb0ace8`
- official100: 100 unique trials, stable order 0–99
- Manifest SHA-256: `1b236bba8173c8a37fb7752fd2e2f09fc569191d6820089759b4be547bd6c344`
- Formal data role: `FORMAL_PROSPECTIVE_SHADOW_COHORT_V1`
- Pilot/equivalence/historical QA rows permanently excluded
- UNKNOWN retained in primary denominator
- Final PR #99 join semantics frozen without redesign
- Trial-cluster bootstrap: 10,000 valid replicates, seed 20260831
- Navigation/formal collection/new research data: 0/0/0
- Combined protocol SHA-256: `e8ea8f3fda15ab81664829ea6f71fcb37f772ad613c13f61007856c16117791a`

## Boundary

This PR freezes the protocol only. It does not collect or analyze formal L2 outcomes and makes no efficacy, collision, progress, real-time, deployment, or physical-safety claim.

## Decision

- `FINAL_DECISION=FREEZE_PROTOCOL_AND_COLLECT_FORMAL_PROSPECTIVE_SHADOW_COHORT`
- `Only next task=COLLECT_L2_H1_PROSPECTIVE_SHADOW_COHORT_V1`

The next task was not executed.
