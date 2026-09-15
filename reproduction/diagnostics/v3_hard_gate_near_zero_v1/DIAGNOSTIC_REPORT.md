# V3 hard-gate near-zero diagnostic report

## Answer-first findings

The four frozen `0.015 q` violations are strict-zero, input-quantization-sensitive boundary findings under the frozen float32 backend; the fixed dense/refined audit found no deeper segment intrusion. All identical-point repeats were deterministic and negative, while every seven-point one-ULP neighborhood changed sign. An independent equivalent float64 implementation passed its predeclared sanity gate and remained negative at all witness/refined points, so the evidence does not justify relabeling them as noise or as physical collision.

Trial 22, 57, and 59 violations align with retained-backup commits and are immediately followed by an assurance-boundary cycle. Trial 28 aligns with a primary commit and has no boundary event. For trial 28, frozen source semantics plus the committed primary reason establish that runtime L1 certified the same immediate executed segment before commit, while the posthoc strict-zero oracle marks it UNSAFE. The frozen trace does not serialize per-cycle L1 evidence for the three backup commits, so their certificate relation remains `CERTIFICATE_NOT_AVAILABLE`.

`FROZEN_SCIENTIFIC_DECISION_REMAINS=FAIL_V3_HARD_SAFETY_GATE`

## Per-trial evidence

| Trial | Segment / cycle | Action | Boundary relation | Frozen witness | Dense-grid min | Refined min | ULP signs | Numerical class | Runtime relation |
|---:|---:|---|---|---:|---:|---:|---|---|---|
| 22 | 410 / 410 | RETAINED_BACKUP | IMMEDIATELY_AFTER | -3.3954472705710614e-09 | -3.3954472705710614e-09 | -3.3954472705710614e-09 | 5 neg / 2 pos | BACKEND_PRECISION_UNRESOLVED | CERTIFICATE_NOT_AVAILABLE |
| 28 | 442 / 442 | PRIMARY_NAVIGATION | NONE | -4.850638484626968e-10 | -4.850638484626968e-10 | -4.850638484626968e-10 | 3 neg / 1 zero / 3 pos | FLOAT32_SIGN_UNSTABLE_NEAR_ZERO | SAME_EXECUTED_SEGMENT_CERTIFIED_PASS |
| 57 | 392 / 392 | RETAINED_BACKUP | IMMEDIATELY_AFTER | -4.850638484626968e-10 | -4.850638484626968e-10 | -4.850638484626968e-10 | 4 neg / 3 pos | BACKEND_PRECISION_UNRESOLVED | CERTIFICATE_NOT_AVAILABLE |
| 59 | 345 / 345 | RETAINED_BACKUP | IMMEDIATELY_AFTER | -3.880511228321337e-09 | -3.880511228321337e-09 | -3.880511228321337e-09 | 5 neg / 2 pos | BACKEND_PRECISION_UNRESOLVED | CERTIFICATE_NOT_AVAILABLE |

The dense negative counts were 512, 1, 513, and 513 respectively. Despite the broad float32 plateaus for trials 22/57/59, neither dense nor four-layer refinement produced a clearance below the frozen witness. Therefore the analyzer's first-negative-return semantics did not conceal a deeper penetration in these fixed audits.

## Precision audit

At witness and refined locations, each of the eight 20-query series was 20/20 bitwise identical, negative, and argmin-stable. Every one-ULP neighborhood contained at least one negative and one positive result (trial 28 also contained zero). The float64 equivalent backend used the exact frozen float32-loaded Gaussian values promoted to float64 and independently reproduced rotation, scale sorting, ellipsoid bisection, signed squared distance, and clearance. Its three predeclared sanity points passed; all eight target signs agreed with float32. Float64 clearances at witness/refined locations were approximately -2.81068e-09 (22), -2.32907e-10 (28), -2.22015e-09 (57), and -5.59305e-09 (59).

This is numerical-boundary ambiguity, not an epsilon-selection result. No epsilon, radius, threshold, Gaussian set, or scientific gate was varied.

## Runtime association and causal scope

- Backup association is established for trials 22/57/59, but a backup-specific certification defect is not established because the frozen runtime trace omits per-cycle L1 certificate payloads.
- A primary same-segment certification discrepancy is established for trial 28: primary navigation commit requires L1 PASS, and runtime L1's segment is the same immediate `p_k -> p_k + dt v_k` segment inspected posthoc.
- L2 uses the future `p_k1 -> p_k2` H1 segment and must not be confused with the immediate executed segment. L3 establishes a prepared backup witness, not a posthoc relabeling authority.
- Boundary events follow the violating backup commits in trials 22/57/59; no boundary occurs in trial 28. They are associations, not proof that the boundary caused the violation.

The evidence supports `NUMERICAL_BOUNDARY_AMBIGUITY` and a targeted `RUNTIME_CERTIFICATION_GAP` hypothesis for trial 28. It does not support a deeper segment intrusion, a physical-collision claim, a guaranteed-safe claim, or changing the formal V3 decision.

## Execution integrity

The successful diagnostic used GPU 1 for read-only map queries only. No Active or Reference trial, controller, plant, frozen analyzer, Official100, or Formal outcome was rerun. The paired root mutation count is zero and protected source diff count is zero. Two schema-only protocol revisions were committed before the successful depth audit; all three failed roots were retained (one pre-query path failure and two pre-depth schema failures).

## Decision

`DIAGNOSTIC_FINAL_STATUS=PASS_V3_HARD_GATE_NEAR_ZERO_DIAGNOSTIC_COMPLETE`

`DIAGNOSTIC_FINAL_INTERPRETATION=All four findings are quantization-sensitive near-zero strict-zero violations with no deeper fixed-scan intrusion; three align with retained-backup commits, while trial 28 provides direct same-executed-segment runtime-L1-PASS versus posthoc-UNSAFE evidence.`

`ONLY_NEXT_TASK=DIAGNOSE_RUNTIME_CERTIFICATION_SEMANTIC_GAP`
