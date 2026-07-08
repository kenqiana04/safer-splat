# FC-Aware V1 Paper Positioning After Exact Logging Probe

## Current Position

FC-Aware V1 should remain a diagnostic / future efficiency direction until exact recall and closed-loop evidence are available.

The exact logging probe changes the status from "blocked by missing active / low-h fields" to "logging feasible for a follow-up exact recall audit." It does not validate a heading cap.

## Safe Claims

- Selected_K-only Adaptive V1 is risk-responsive but insufficient for candidate-count reduction because forced heading candidates dominate.
- FC-Aware analysis identifies the heading source as the main candidate-count bottleneck.
- Candidate source IDs and heading distance / cosine can be reconstructed exactly from saved states and selector formulas.
- Wrapper-only no-intervention replay can log per-candidate `h`, low-`h` IDs, and solver dual-active IDs without modifying official core source.
- FC-Aware source-aware candidate selection is a promising but unvalidated efficiency direction.

## Claims To Avoid

- FC-Aware V1 improves runtime.
- FC-Aware V1 preserves active constraints under a cap.
- FC-Aware V1 is safe.
- FC-Aware V1 is closed-loop validated.
- A specific heading cap is recommended.
- full100 validates FC-Aware V1.

## If The Exact Recall Audit Succeeds

The paper can state that no-intervention replay provides evidence that a proposed cap / ranking preserves active and low-`h` heading candidates on targeted risk-window rows. This still remains pre-closed-loop evidence unless followed by a capped smoke run.

## If The Exact Recall Audit Fails

The paper should keep FC-Aware V1 as a diagnostic result:

- heading candidates explain why selected_K-only budgeting did not reduce the final candidate set,
- source-aware budgeting needs stronger recall-preserving design,
- exact active / low-`h` logging provides a path for future work.

## Required Framing

FC-Aware V1 is a candidate-selection / efficiency support module. It does not replace Start-Safe CBF, Discrete-Time Verification, CBF-QP filtering, or optional Predictive Recovery.

`h` / `min_safety_h` is the repository GSplat ellipsoid safety value, not meter clearance. A margin violation is not a collision.
