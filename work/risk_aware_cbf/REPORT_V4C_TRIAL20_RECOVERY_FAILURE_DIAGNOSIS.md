# REPORT: V4-C Trial-20 Recovery Failure Mechanism Diagnosis

## 1. Purpose

This trial-20-only study diagnoses the recovery-capability failure of the original V4-C comparator. All counterfactuals are shadow evaluations; no active redesign was run.

## 2. Why Trial 20 Matters

Trial 20 is the only held-out flight trial with 34 recovery activations that all failed under both original V4-C and the hierarchical wrapper's exact Stage-B fallback. This is separate from HCE efficiency validation.

## 3. Exact Reproduction

The original H3_N128 comparator reproduced 34 activations, 34 recovery failures, 34 executed-horizon margin violations, zero collision, zero QP infeasibility, and `stopped_before_goal`. Margin violation is not collision.

## 4. Activation Streak Structure

All 34 activations form one continuous streak. The nearest-critical geometry spans three stable anonymized Gaussian identifiers, so this is persistent local risk rather than a single fixed Gaussian contact.

## 5. Candidate-Family Failure

Every original candidate family had zero feasible candidates. The best observed H was `0.00048790`, below the `0.0005` margin. Random generated 4,352 candidates and selected none. Because no candidate was feasible and the original evaluator used best-H fallback, scalar cost selection is not the main failure explanation.

## 6. Search-Coverage Diagnosis

On the three comparator-derived representative contexts, original H3/N128, expanded H3/N512, and fixed-configuration H3/CEM each found zero feasible contexts. Expanded random coverage was therefore not sufficient evidence for a candidate-coverage redesign.

## 7. Horizon Diagnosis

H4/N128 and H5/N128 each found zero feasible representative contexts. These are shadow results only and do not establish active H4/H5 effectiveness.

## 8. Earlier-Trigger Diagnosis

The H3/N128 one-step-earlier, two-steps-earlier, and warning-threshold shadows found zero feasible opportunities. This does not support an earlier-trigger prototype for this trial under the fixed local contract.

## 9. Bounded-Reachability Diagnosis

With `dt=0.05` and component acceleration clamp `0.1`, the candidate-independent control-induced position-deviation envelope is 0, 0.000433, 0.001299, 0.002598, and 0.004330 m for H1 through H5. This is a dynamics bound, not a collision, h-improvement, or controllability proof.

## 10. Hypothesis Decisions

H-T20-1 search coverage: not supported. H-T20-2 horizon insufficiency: not supported on representative shadows. H-T20-3 late trigger: not supported. H-T20-4 bounded control authority: partially supported. H-T20-5 family/geometry mismatch: partially supported. H-T20-6 persistent repeated context: partially supported because the streak is continuous but uses three critical IDs.

## 11. Failure-Level Interpretation

The combined evidence is consistent with a local recovery-capability limit: all fixed families, expanded coverage, CEM, H4/H5 shadows, and earlier H3 shadows failed to reach the margin. It is not a formal proof that no safe control exists.

## 12. Selected Redesign Direction

`classify_as_likely_unrecoverable_under_current_local_contract`. No active prototype is authorized by this diagnosis. A future separate study would need a new directional recovery primitive design and a fresh safety contract, rather than parameter tuning.

## 13. What Was Not Tested

No active redesign, R1, planner, full100, flight20, other held-out trials, cost-weight tuning, clamp change, radius change, or GSplat-query change was run.

## 14. Claim Boundaries

This is a single flight-trial diagnosis. It makes no cross-scene, generalized recovery, collision-reduction, planner, or new-CBF-theorem claim. `h` is not metric clearance.

Hierarchical Candidate Evaluation remains retained as a configuration-specific efficiency mechanism. This task diagnoses the separate recovery-capability failure concentrated in trial 20; it does not modify or invalidate R-V4C-1.
