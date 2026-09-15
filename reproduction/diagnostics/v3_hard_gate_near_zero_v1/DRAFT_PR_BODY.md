## Scope

Post-failure, read-only diagnosis of the four frozen Active V3 `0.015 q` hard-gate violations (trials 22, 28, 57, 59). No method, radius, epsilon, runtime, controller, dynamics, map, paired protocol, or frozen analyzer is changed. The branch has no runtime authority and cannot override the frozen scientific decision.

## Frozen protocol and evidence

- Start: `50cadfe614da70ce0345c4b1789c787dc529287e`
- Protocol freeze: `e704bbe38428e60750155140ab69e2614cc589f0`
- Explicit schema-only revisions: `7add50b5b0d02d379eff621a67015425af3412cc`, `aef9104a5d681948e998c4bb69c00b34e2a0d510`
- External result root: `/disk1/zlab/v3_diagnostic_records/v3_hard_gate_near_zero_v1_20260915`
- Paired evidence byte-preserved; mutation count 0
- Protected source diff count 0

## Findings

No fixed dense/refined audit found deeper segment intrusion. Identical queries were deterministic and negative; all four one-ULP neighborhoods flipped sign. The independent equivalent float64 audit passed its sanity gate and agreed on negative signs at all witness/refined points.

Violations 22/57/59 occurred on retained-backup commits and were immediately followed by boundary cycles. Trial 28 occurred on a primary commit; source and trace semantics establish same-immediate-segment L1 PASS before the posthoc UNSAFE result. Per-cycle certificate payloads are unavailable for the backup commits, so no backup-specific defect is claimed.

`FROZEN_SCIENTIFIC_DECISION_REMAINS=FAIL_V3_HARD_SAFETY_GATE`

`DIAGNOSTIC_FINAL_STATUS=PASS_V3_HARD_GATE_NEAR_ZERO_DIAGNOSTIC_COMPLETE`

Only next task: `DIAGNOSE_RUNTIME_CERTIFICATION_SEMANTIC_GAP`.
