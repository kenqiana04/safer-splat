# REPORT: V4-C Hierarchical Candidate Evaluation V0

## 1. Purpose

Fixed dense-flight trials 12, 13, and 14 only. This is not flight20, full100, a statistical test, or a generalized claim.

## 2. Difference from Original V4-C

Stage A uses original deterministic families and original `evaluate_sequences`. Stage B would call the untouched full generator/evaluator only when Stage A has no feasible candidate. CBF-QP, controls, clamp, cost, safety query, trigger, fallback, first-control execution, and state update are unchanged.

## 3. Preregistered Configuration

Flight `risk_aware_v1_bestD`; H=3; N=128; `on_margin_violation`; margins 0.0005/0.0008; `dt=0.05`; `max_steps=800`; original weights 1.0/0.2/0.1/10.0; deterministic flags enabled; CEM disabled; original StartGuard projection.

## 4. Contract and Equivalence Checks

All 16 critical checks passed. Stage A has no random/CEM source and does not mutate state/args. Forced Stage-B exactly matched original source list, selection, first control, H sequence, min H, success/failure, and RNG behavior.

## 5. Paired Same-State Audit

Original V4-C controlled the formal trajectory. Hierarchical V0 shadow evaluation had 0 feasibility regressions, 0 margin regressions, 60/60 source matches, 60 Stage-A successes, and 0 Stage-B entries. Paired median recovery runtime: 8.071s original versus 1.653s hierarchical, reduction 79.5%.

## 6. Active A/B Protocol

Six sequential runs used the preregistered order: 12/original, 12/hierarchical, 13/hierarchical, 13/original, 14/original, 14/hierarchical. Warm-up was nonformal and excluded.

## 7. Stage-A and Stage-B Usage

| trial | activations | Stage-A success | Stage-B entry | hierarchical median recovery runtime (s) |
| --- | ---: | ---: | ---: | ---: |
| 12 | 24 | 24 | 0 | 1.591836 |
| 13 | 28 | 28 | 0 | 1.638455 |
| 14 | 8 | 8 | 0 | 1.639150 |

## 8. Candidate-Family Contribution

Original full evaluation generated 7,680 random candidates; 3,216 were feasible but none was selected. Deterministic selected counts were baseline 14, braking 14, repulsive 10, continuity 22, and goal-directed 0. Hierarchical omitted random/CEM and preserved all 60 successful recoveries.

## 9. Safety and Feasibility Guardrails

Both variants had 0 collision, 0 QP infeasible, 0 recovery failure, and 0 executed-horizon violation. H-step feasibility is not route-level safety, and `h` is not meter clearance.

## 10. Runtime Results

Active median recovery runtime was 7.941991s original and 1.638455s hierarchical. Reduction was 0.793697, exceeding the preregistered 20% target.

## 11. Progress and Stop Reasons

Both variants had identical mean goal-distance-reduction ratio 0.258574. All six trial-variant runs ended `stopped_before_goal`; no completion claim is made.

## 12. Negative and Neutral Evidence

Stage B was not exercised on this cohort. The contract is validated, but active fallback frequency is not. Random/CEM is not proven globally redundant.

## 13. Failure-Level Interpretation

F-V4C-3 is locally mitigated for this cohort. F-V4C-4 has stronger local evidence: random evaluation dominated work without selected candidates. Other failure modes remain unresolved.

## 14. Decision

`r_v4c1_decision = retain_hierarchical_v0_for_small_cohort`

## 15. Claim Boundaries

This is local three-trial evidence only. It does not establish generalized runtime/safety effectiveness, collision reduction, completion improvement, planner quality, statistical significance, a CBF theorem, or metric clearance.

R-V4C-1 changes candidate-evaluation order, not the CBF-QP, candidate controls, recovery cost, safety query, or planner.

The fixed three-trial cohort supports retaining hierarchical V4-C V0 for a separate small-cohort validation; generalized runtime and safety effectiveness remain unvalidated.
