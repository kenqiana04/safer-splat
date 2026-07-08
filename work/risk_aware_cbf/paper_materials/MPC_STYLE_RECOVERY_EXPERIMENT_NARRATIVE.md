# MPC-style Recovery Experiment Narrative

## Why MPC-style Recovery Was Considered

The existing V4-C recovery already performs triggered H-step predictive evaluation. A natural extension is to make the receding-horizon structure explicit by evaluating length-H control sequences rather than only single-step or repeated action candidates.

This was considered as an optional extension after Start-Safe CBF and Discrete-Time Verification were already closed as the main paper line.

## How It Was Tested

A primitive-sequence MPC-style evaluator was implemented under `work/risk_aware_cbf/`.

The evaluator:

- reads targeted DT-risk trigger states,
- generates H-step primitive control sequences,
- rolls each sequence forward with repository dynamics,
- queries GSplat h values at rollout steps,
- selects a safety-feasible sequence or best-improving sequence,
- records only the first control as the recovery action.

The test was offline replay only. It was not closed-loop and not full100.

## What It Showed

Both H2_N64 and H3_N64 were evaluated on 199 targeted trigger rows.

Both profiles produced:

- 103 successes,
- 0 improved-but-unresolved cases,
- 96 no-improvement cases,
- 96 selected H-step margin violations.

H3 increased average h improvement but did not reduce the selected violation count. The dominant selected sequence types were `nominal_hold` and `smooth_previous_nominal`, indicating that the primitive search often did not find a useful avoidance action.

## Why It Was Not Adopted

The current primitive MPC-style profile was not adopted because:

- it leaves many unresolved selected margin violations,
- it has no closed-loop evidence,
- it is not directly comparable to R4_H2_N64,
- it has high offline per-trigger runtime,
- H3 does not improve the unresolved count over H2,
- the selected controls are dominated by nominal-like behavior.

## How This Supports Keeping V4-C

The result supports keeping existing V4-C as the optional triggered recovery evidence. R4_H2_N64 remains the practical reference and H3_N128 remains the robust reference.

The primitive MPC-style pilot is useful because it prevents overclaiming: simply wrapping primitive sequence search around DT-risk states is not enough to replace the existing recovery evidence.

## How To Avoid Overclaiming

Do not describe this pilot as closed-loop, full100, safety-guaranteeing, or better than V4-C. It should be mentioned only as an optional extension that was explored and frozen as future work.
