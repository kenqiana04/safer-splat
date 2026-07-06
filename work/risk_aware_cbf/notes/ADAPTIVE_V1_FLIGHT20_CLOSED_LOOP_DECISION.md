# Adaptive V1 Flight20 Closed-Loop Decision

## 1. Flight20 Closed-Loop Success

Continue Adaptive V1: `True`.

## 2. selected_K Integration

`selected_K_applied_rate` fixed: `1.0`.

`selected_K_applied_rate` balanced: `1.0`.

This indicates whether selected budgets were passed into V1 candidate budgeting. It does not prove final candidate count reduction.

## 3. Fixed Vs Adaptive Balanced

| profile | trial_count | num_steps | runtime_mean | runtime_p95 | runtime_max | selected_K_mean | selected_K_p95 | selected_K_max | selected_K_applied_rate | measured_candidate_count_mean | measured_candidate_count_p95 | measured_candidate_count_max | active_constraint_count_mean | active_constraint_count_p95 | active_constraint_count_max | collision_count | qp_infeasible_count | min_safety_h_min | H1_margin_violation_count | H2_margin_violation_count | H3_margin_violation_count | DT_warning_count | low_margin_step_count | fallback_count | fallback_fraction | progress_mean | crash_count | recovery_used_count | missing_field_count |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| fixed | 20 | 1755 | 0.0585986 | 0.0634454 | 0.0798746 | 2000 | 2000 | 2000 | 1 | 23346.9 | 28691.9 | 37171 | 176.671 | 307.3 | 390 | 0 | 0 | 0.000327737 | 93 | 98 | 103 | 101 | 90 | 0 | 0 | 0.211536 | 0 | 0 | 0 |
| adaptive_balanced | 20 | 1753 | 0.0583903 | 0.0623556 | 0.0706654 | 1877.35 | 5600 | 8000 | 1 | 23308.6 | 28580.8 | 37171 | 178.056 | 310 | 390 | 0 | 0 | 0.000327737 | 93 | 98 | 103 | 101 | 90 | 88 | 0.0501997 | 0.211668 | 0 | 0 | 0 |

## 4. Crash

Crash counts are reported in the table. A nonzero crash count blocks progression.

## 5. Collision

Collision counts are reported separately from margin violations. Margin violation is not collision.

## 6. QP Infeasibility

QP infeasible counts are reported in the table. A nonzero increase blocks progression.

## 7. Runtime

Runtime ratio balanced/fixed: `0.9964449214477794`.

## 8. Safety Values And DT Margins

`min_safety_h` is the repository GSplat ellipsoid safety h value, not meter clearance. H1/H2/H3 margin violations are sampled-data margin checks, not collisions.

## 9. Mode Switching And Risk Response

DT warning count balanced: `101`.

Low-margin step count balanced: `90`.

Risk response triggered: `True`.

## 10. Full100 Now

Recommendation: `False`. flight20 pilot is not a full100 benchmark.

## 11. Targeted DT-Risk Closed-Loop Next

Recommendation: `True`.

## 12. Paper Method Role

Current role: `support_module_or_ablation_not_main_safety_method`.

## 13. Candidate Decomposition

| profile | selected_K_mean | measured_candidate_count_mean | final_unique_candidate_count_mean | forced_near_candidate_count_mean | heading_candidate_count_mean | history_candidate_count_mean | forced_unique_candidate_count_mean | budget_limited_candidate_count_mean | forced_candidate_fraction_mean | candidate_decomposition_available |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| fixed | 2000 | 23346.9 | 23346.9 | 77.3236 | 23316.2 | 24.1105 | 23346.9 | 0 | 1 | True |
| adaptive_balanced | 1877.35 | 23308.6 | 23308.6 | 78.077 | 23274.8 | 30.822 | 23308.6 | 0 | 1 | True |

## 14. Recommended Wording

- Adaptive V1 balanced was tested in a flight20 closed-loop pilot.
- `selected_K` was passed into V1 candidate budgeting.
- V4-C recovery was disabled.
- Results should be described as a support-module / ablation pilot, not as an independent safety guarantee.

## 15. Forbidden Wording

- Do not claim Adaptive V1 independently guarantees safety.
- Do not claim a new CBF theorem.
- Do not describe margin violation as collision.
- Do not describe `min_safety_h` as meter clearance.
- Do not describe flight20 as a full benchmark or official flight100 result.
- Do not claim final candidate count or runtime improvement unless the measured metrics support it.
