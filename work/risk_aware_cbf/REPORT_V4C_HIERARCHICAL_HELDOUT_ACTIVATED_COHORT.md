# REPORT: V4-C Hierarchical Candidate Evaluation Held-Out Activated Cohort

## 1. Purpose

This report validates the frozen V4-C hierarchical candidate-evaluation V0 on the comparator-defined held-out activation cohort. It is not a full100 rerun, a statistical-significance test, a planner evaluation, or a generalized runtime/collision claim.

## 2. Development/Held-Out Separation

Development trials were 12, 13, and 14. The held-out set was selected only from original-comparator recovery activations before hierarchical outcomes were observed.

## 3. Original Full100 Activation Inventory

Original comparator inventory: 100 trials, 19 activated trials, and 236 activation contexts.

## 4. Preregistered Cohort

Held-out activated trials: `[20, 27, 31, 32, 34, 35, 36, 37, 38, 59, 61, 71, 85, 86, 93, 94]`. Nonactivated controls: `[0, 52, 99]`. The order was fixed before formal execution.

## 5. Fixed Method Contract

Frozen contract passed: `True`. No candidate family, acceptance, fallback, seed, H/N, threshold, cost, clamp, StartGuard, CBF-QP, GSplat query, or max-step setting was changed.

## 6. Paired Same-State Audit

Paired gate passed: `True`. Feasibility regressions: `0`. Formal paired trajectories executed the original comparator controls only.

## 7. Active A/B Protocol

The active run used 38 sequential preregistered runs: 16 held-out activated trials times two variants, then three nonactivated controls times two variants. No GPU trial runs were parallelized.

## 8. Stage-A Generalization

Stage-A selected 167 of 201 held-out activation contexts (rate 0.8308457711442786).

## 9. Stage-B Evidence

Stage-B entries/successes/failures were 34/0/34.

## 10. Candidate-Family Contribution

Random selected count: 0; random unique-feasible count: 0. Candidate-family summaries are compact aggregates only.

## 11. Safety and Feasibility

Hierarchical collision/QP-infeasible/recovery-failed/executed-H-violation counts: 0/0/34/34. `h` is the repository safety-field value, not meter clearance.

## 12. Runtime Distribution

| variant | activated median (s) | activated mean (s) | p95 (s) |
| --- | ---: | ---: | ---: |
| original_v4c | 7.9996402324177325 | 7.98348905867897 | 8.149398593930528 |
| hierarchical_v0 | 1.6425828915089369 | 2.127287316310685 | 3.6281134872697294 |

Aggregate median runtime reduction: `0.7946679045824416`. Positive per-trial reductions: `15/16`; reductions of at least 20%: `15/16`.

## 13. Progress and Stop Reasons

Progress mean/median deltas were `0.0` and `0.0`; positive-to-nonpositive flips: `0`. Progress is an engineering diagnostic, not a planner-quality claim.

## 14. Non-Activated Controls

Controls had no recovery activation and exact behavior checks: `True`. Their wrapper overhead is reported separately.

## 15. Negative and Neutral Evidence

Stage B entered observed contexts and reproduced the original full-search outcome there; it did not convert the original recovery failures into successes.

## 16. Failure-Level Interpretation

This validation is configuration-specific to flight H3_N128. It does not establish cross-scene effectiveness, completion improvement, collision reduction, or generalized runtime improvement.

## 17. Decision

`retain_hierarchical_v0_as_validated_configuration_specific_mechanism`

## 18. Claim Boundaries

The held-out cohort evaluates a frozen hierarchical V4-C V0; no method parameters or candidate semantics were changed after observing development-trial results.

The held-out activated cohort supports retaining hierarchical V4-C V0 as a configuration-specific recovery-efficiency mechanism. Cross-scene and generalized effectiveness remain unvalidated.
