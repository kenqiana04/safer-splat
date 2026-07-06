# Synthetic Initial-Unsafe Stress Analysis

## Generation protocol

- Source trials: 30
- Synthetic cases retained: 120
- Category counts: `{'synthetic_unsafe': 88, 'synthetic_margin_violating': 17, 'synthetic_near_unsafe': 15}`
- Perturbation magnitudes: `[0.005, 0.01, 0.02, 0.05, 0.075, 0.1]`
- Directions used: `['nearest', 'random_0', 'random_1', 'risky']`
- Every retained synthetic start is labeled by a full GSplat safety query. `min_safety_h` is the repository GSplat ellipsoid safety h value, not meter clearance.

## Repair-only ablation

| method | num_cases | repair_success_count | repair_success_rate | full_query_verified_count | repair_distance_mean | repair_distance_p95 | repair_distance_max |
| --- | --- | --- | --- | --- | --- | --- | --- |
| active_set_verified_projection | 120 | 120 | 1 | 120 | 0.033625 | 0.1 | 0.1 |
| heuristic_repulsion | 120 | 115 | 0.958333 | 115 | 0.0272678 | 0.0596651 | 0.144053 |
| no_repair | 120 | 15 | 0.125 | 15 | 0 | 0 | 0 |
| verified_projection | 120 | 120 | 1 | 120 | 0.033625 | 0.1 | 0.1 |

Grouped repair summary:

| method | synthetic_category | perturbation_magnitude | num_cases | repair_success_count | repair_success_rate | full_query_verified_count | repair_distance_mean | repair_distance_p95 |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
| active_set_verified_projection | synthetic_margin_violating | 0.01 | 2 | 2 | 1 | 2 | 0.005 | 0.005 |
| active_set_verified_projection | synthetic_margin_violating | 0.02 | 2 | 2 | 1 | 2 | 0.00499999 | 0.00499999 |
| active_set_verified_projection | synthetic_margin_violating | 0.05 | 8 | 8 | 1 | 8 | 0.00874999 | 0.01 |
| active_set_verified_projection | synthetic_margin_violating | 0.075 | 4 | 4 | 1 | 4 | 0.00624999 | 0.00924999 |
| active_set_verified_projection | synthetic_margin_violating | 0.1 | 1 | 1 | 1 | 1 | 0.01 | 0.01 |
| active_set_verified_projection | synthetic_near_unsafe | 0.005 | 4 | 4 | 1 | 4 | 5.24043e-09 | 7.13952e-09 |
| active_set_verified_projection | synthetic_near_unsafe | 0.01 | 3 | 3 | 1 | 3 | 7.05073e-09 | 1.09504e-08 |
| active_set_verified_projection | synthetic_near_unsafe | 0.05 | 1 | 1 | 1 | 1 | 3.18245e-09 | 3.18245e-09 |
| active_set_verified_projection | synthetic_near_unsafe | 0.075 | 4 | 4 | 1 | 4 | 8.49376e-09 | 1.18996e-08 |
| active_set_verified_projection | synthetic_near_unsafe | 0.1 | 3 | 3 | 1 | 3 | 6.65038e-09 | 1.24641e-08 |
| active_set_verified_projection | synthetic_unsafe | 0.02 | 4 | 4 | 1 | 4 | 0.015 | 0.02 |
| active_set_verified_projection | synthetic_unsafe | 0.05 | 15 | 15 | 1 | 15 | 0.036 | 0.05 |
| active_set_verified_projection | synthetic_unsafe | 0.075 | 29 | 29 | 1 | 29 | 0.0424138 | 0.05 |
| active_set_verified_projection | synthetic_unsafe | 0.1 | 40 | 40 | 1 | 40 | 0.052 | 0.1 |
| heuristic_repulsion | synthetic_margin_violating | 0.01 | 2 | 2 | 1 | 2 | 0.005 | 0.005 |
| heuristic_repulsion | synthetic_margin_violating | 0.02 | 2 | 2 | 1 | 2 | 0.00500001 | 0.00500002 |
| heuristic_repulsion | synthetic_margin_violating | 0.05 | 8 | 8 | 1 | 8 | 0.00925841 | 0.0126456 |
| heuristic_repulsion | synthetic_margin_violating | 0.075 | 4 | 4 | 1 | 4 | 0.00624997 | 0.00924991 |
| heuristic_repulsion | synthetic_margin_violating | 0.1 | 1 | 1 | 1 | 1 | 0.00999982 | 0.00999982 |
| heuristic_repulsion | synthetic_near_unsafe | 0.005 | 4 | 4 | 1 | 4 | 5.24043e-09 | 7.13952e-09 |
| heuristic_repulsion | synthetic_near_unsafe | 0.01 | 3 | 3 | 1 | 3 | 7.05073e-09 | 1.09504e-08 |
| heuristic_repulsion | synthetic_near_unsafe | 0.05 | 1 | 1 | 1 | 1 | 3.18245e-09 | 3.18245e-09 |
| heuristic_repulsion | synthetic_near_unsafe | 0.075 | 4 | 4 | 1 | 4 | 8.49376e-09 | 1.18996e-08 |
| heuristic_repulsion | synthetic_near_unsafe | 0.1 | 3 | 3 | 1 | 3 | 6.65038e-09 | 1.24641e-08 |

## Post-repair navigation validation

| method | use_v4c | selected_cases | collision_count | collision_free_count | qp_infeasible_count | min_safety_h_min | progress_mean | runtime_mean | runtime_p95 | base_horizon_margin_violation_count | exec_horizon_margin_violation_count | predictive_recovery_used_count | predictive_recovery_success_count | recovery_failed_count |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| active_set_verified_projection+risk_aware_v1_bestD | False | 40 | 0 | 40 | 0 | 0.000267967 | 0.480099 | 0.0563943 | 0.0641089 | 155 | 155 | 0 | 0 | 0 |
| active_set_verified_projection+risk_aware_v1_bestD+V4C_H3 | True | 40 | 0 | 40 | 0 | 0.000500073 | 0.479913 | 0.442551 | 1.44541 | 120 | 0 | 120 | 120 | 0 |

## Direct answers

1. Synthetic stress generation cases: 120.
2. Category counts: near-unsafe=15, margin-violating=17, unsafe=88.
3. `synthetic_initial_h` distribution is shown in `figures/synthetic_stress_generation_distribution.png` and grouped by perturbation magnitude in the generation summary.
4. Repair success rates are listed in the repair-only ablation table above.
5. Active-set projection improves over heuristic repulsion: True.
6. Active-set full-query verification matches repair success: True.
7. Repair distance by perturbation magnitude is shown in `figures/synthetic_repair_distance_by_magnitude.png`.
8. Active-set repair failures: [].
9. Post-repair navigation collision count: 0.
10. Post-repair navigation QP infeasible count: 0.
11. V4-C post-repair horizon margin reduction: 120.
12. Synthetic stress supports FAS-Project generality: True.
13. Need to tune active-set projection: False.
14. Need to tune V4-C runtime overhead: evaluated separately in the V4-C runtime tuning pilot.

## Recommended decision

PROCEED_TO_METHOD_AND_EXPERIMENT_WRITING
