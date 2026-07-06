# Adaptive V1 Closed-Loop Smoke Decision

## 1. Closed-Loop Smoke Success

Smoke success recommendation: `True`.

## 2. selected_K Integration

`selected_K_applied_rate` for balanced: `1.0`. This indicates whether selected budgets were passed into V1 candidate budgeting.

The integration is real, but measured candidate count did not materially decrease in this smoke because forced near / heading / history candidates dominated the final selected set. This blocks any claim of closed-loop efficiency improvement from smoke alone.

## 3. Fixed Vs Adaptive Balanced

| profile | runtime_mean | runtime_p95 | runtime_max | selected_K_mean | selected_K_p95 | selected_K_max | selected_K_applied_rate | measured_candidate_count_mean | measured_candidate_count_p95 | active_constraint_count_mean | collision_count | qp_infeasible_count | min_safety_h_min | H1_margin_violation_count | H2_margin_violation_count | H3_margin_violation_count | fallback_count | progress_mean | crash_count | recovery_used_count |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| fixed | 0.0575024 | 0.0601482 | 0.0634927 | 2000 | 2000 | 2000 | 1 | 20999.2 | 23365.8 | 260.2 | 0 | 0 | 0.00321891 | 0 | 0 | 0 | 0 | 0.0492433 | 0 | 0 |
| adaptive_balanced | 0.0583943 | 0.0605817 | 0.0640895 | 1000 | 1000 | 1000 | 1 | 20997.2 | 23363.7 | 278.2 | 0 | 0 | 0.00321891 | 0 | 0 | 0 | 0 | 0.0492433 | 0 | 0 |

## 4. Crash

Crash counts are reported in the table. A nonzero crash count blocks progression.

## 5. Collision

Collision counts are reported separately from margin violations. Margin violation is not collision.

## 6. QP Infeasibility

QP infeasible counts are reported in the table. A nonzero increase blocks progression.

## 7. Runtime

Runtime ratio balanced/fixed: `1.0155099865588708`.

This smoke does not support a closed-loop runtime improvement claim. It only shows that runtime did not become abnormal at smoke scale.

## 8. Safety Values And DT Margins

`min_safety_h` is the repository GSplat ellipsoid safety h value, not meter clearance. H1/H2/H3 margin violations are sampled-data margin checks, not collisions.

## 9. Flight20 Closed-Loop

Recommendation: `True`.

## 10. Full100 Now

Recommendation: `False`. Smoke is not enough to jump directly to full100.

## 11. Paper Method Role

Current role: `support_module_or_ablation_until_flight20_closed_loop`.

## 12. Ablation / Future Work

If flight20 closed-loop is not yet run, Adaptive V1 should remain a support-module or ablation result rather than a main safety method.

## 13. Recommended Wording

- Adaptive V1 balanced was smoke-tested in closed loop.
- `selected_K` was passed into V1 candidate budgeting during smoke.
- V4-C recovery was disabled.

## 14. Forbidden Wording

- Do not claim Adaptive V1 independently guarantees safety.
- Do not claim a new CBF theorem.
- Do not describe margin violation as collision.
- Do not describe `min_safety_h` as meter clearance.
- Do not describe smoke as a full benchmark or official flight100 result.
- Do not claim full100 readiness from smoke alone.
