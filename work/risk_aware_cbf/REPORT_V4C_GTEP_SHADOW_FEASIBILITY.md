# REPORT: V4-C Geometry-Conditioned Tangential Escape Primitive Shadow Feasibility

## 1. Purpose

GTEP V0 was evaluated only as a shadow directional-recovery primitive on the 34 original trial-20 activation contexts. No GTEP control was executed.

## 2. Difference from Existing V4-C Families

The fixed P0-P6 bank uses the existing analytic ball-to-ellipsoid barrier normal and a deterministic tangent basis. It is not radial Gaussian-center repulsion, random perturbation, a planner, or a learned policy.

## 3. Barrier Geometry Semantics

The existing query returns analytic `grad_h = 2 * phi * (x - y)` for each ellipsoid and uses the minimum-h Gaussian as critical. Three representative equivalence checks had zero h and gradient error, matching critical IDs and preserving state.

## 4. Primitive Contract

The bank contained 22 unique fixed candidates per H3 context after deterministic duplicate removal, within the maximum 24. It retained original dynamics, `dt`, clamp, radius, GSplat query, and margin.

## 5. Preregistered Contexts

All 34 original trial-20 activation contexts were evaluated. Formal execution remained the original comparator trajectory.

## 6. Geometry Equivalence

Geometry semantics status was sufficient; equivalence and state isolation both passed. No finite-difference gradient or Gaussian-center substitute was used.

## 7. Trial-20 Shadow Results

GTEP H3 found zero feasible contexts and zero unique tangential opportunities. Gradient-normal-only primitives also found zero opportunities.

## 8. Primitive-Family Contribution

No P0-P6 family reached the fixed `h >= 0.0005` feasibility margin. Thus no progress tradeoff can be attributed to a feasible GTEP candidate.

## 9. Multi-Gaussian Results

P7 was not run: a top-k constraint/normal aggregation semantics was not pre-existing in the original local recovery contract.

## 10. Progress Tradeoffs

There were zero feasible GTEP contexts and zero nonnegative-progress feasible opportunities. This is a diagnostic result, not a planner-quality claim.

## 11. Positive Controls

Positive controls were not run because prior compact held-out artifacts intentionally retain no raw states. This is a declared audit limitation; it does not alter the trial-20 state-isolation result.

## 12. H5 Diagnostic

Since H3 GTEP had zero feasible contexts, H5 was evaluated on three preregistered representative contexts. It found zero feasible contexts. H5 remains shadow-only.

## 13. Failure-Level Interpretation

The verified analytic-normal/tangent bank did not recover the trial-20 contexts under the tested H3 or representative H5 local contracts. This strengthens, but does not prove, the earlier local-recovery-limit diagnosis.

## 14. Decision

`classify_trial20_as_unresolved_local_recovery_limit`. No active GTEP smoke is authorized. This freezes GTEP V0, not the broader directional-recovery research direction.

## 15. Claim Boundaries

This is shadow-only, trial20-specific evidence. It makes no generalized safety, collision avoidance, completion, planner, or controllability claim. Margin violation is not collision, and `h` is not metric clearance. GTEP does not modify formal execution, original V4-C, HCE, CBF-QP, or the planner; R1 was not run.

The current GTEP V0 did not recover the trial-20 contexts. This freezes GTEP V0, not the broader recovery direction, while strengthening the evidence that trial 20 exceeds the tested local recovery contracts.
