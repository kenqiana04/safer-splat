# V4-C Tuned Full100 Analysis

## Direct Answers

1. Tuned R4_H2_N64 full100 keeps collision_count=0: `True`.
2. Tuned R4_H2_N64 full100 keeps qp_infeasible_count=0: `True`.
3. Tuned full100 base_horizon_margin_violation_count: `193`.
4. Tuned full100 exec_horizon_margin_violation_count: `0`.
5. Tuned full100 reduces exec horizon margin violations to 0: `True`.
6. predictive_recovery_used_count: `193`.
7. predictive_recovery_success_count: `193`.
8. recovery_failed_count: `0`.
9. activated_trial_count: `19`.
10. non_activated_trial_count: `81`.
11. runtime_mean ratio R4 vs H3_N128: `0.563137`.
12. runtime_p95 ratio R4 vs H3_N128: `0.440452`.
13. runtime_mean ratio R4 vs V4-A: `1.667038`.
14. Tuned R4 progress changed from H3 `0.448789` to `0.448854`.
15. Tuned R4 min_safety_h_min >= dt_margin: `True`.
16. Top activated trials are listed below for comparison with the H3_N128 hotspots.
17. Top slowest trials are listed below; hotspot trials still dominate the slow tail.
18. Tuned R4 can replace H3_N128 as the recommended dense-flight practical config: `True`.
19. Tuned R4 should be used as a warning/on-margin-triggered recovery module, not an always-on controller.
20. Method/experiment writing decision: `PROCEED_TO_METHOD_AND_EXPERIMENT_WRITING`.

## Runtime Distribution

| runtime_mean | runtime_median | runtime_p75 | runtime_p90 | runtime_p95 | runtime_p99 | runtime_max |
| --- | --- | --- | --- | --- | --- | --- |
| 0.095952 | 0.057895 | 0.059686 | 0.170413 | 0.309428 | 0.593822 | 0.654511 |

## Comparison Table

| run | rows | collision_count | collision_free_count | qp_infeasible_count | horizon | num_sequences | base_horizon_margin_violation_count | exec_horizon_margin_violation_count | reduction | predictive_recovery_used_count | predictive_recovery_success_count | recovery_failed_count | min_safety_h_min | progress_mean | runtime_mean | runtime_p95 | runtime_max | runtime_mean_ratio_vs_V4A | runtime_mean_ratio_vs_H3_N128 |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| V4-A active projection + V1 flight100 | 100 | 0 | 100 | 0 | NA | NA | NA | NA | NA | NA | NA | NA | 0.000197846 | 0.452088 | 0.057558 | 0.064309 | 0.064539 | 1 | 0.337807 |
| V4-C H3_N128 full100 | 100 | 0 | 100 | 0 | 3 | 128 | 236 | 0 | 236 | 236 | 236 | 0 | 0.000500051 | 0.448789 | 0.170388 | 0.702523 | 1.638351 | 2.960273 | 1 |
| V4-C R4_H2_N64 hotspot pilot | 6 | 0 | NA | 0 | 2 | 64 | 134 | 0 | 134 | 134 | 134 | 0 | 0.000500013 | 0.408297 | 0.517519 | 0.649463 | 0.666929 | 8.991223 | 3.037295 |
| V4-C R4_H2_N64 tuned full100 | 100 | 0 | 100 | 0 | 2 | 64 | 193 | 0 | 193 | 193 | 193 | 0 | 0.000500013 | 0.448854 | 0.095952 | 0.309428 | 0.654511 | 1.667038 | 0.563137 |

## Activation Runtime

| activated_runtime_mean | activated_runtime_p95 | non_activated_runtime_mean | non_activated_runtime_p95 |
| --- | --- | --- | --- |
| 0.262288 | 0.599339 | 0.056935 | 0.060076 |

## Top 5 Most Activated Trials

| trial | predictive_recovery_used_count | predictive_recovery_success_count | recovery_failed_count | runtime_mean | runtime_p95 | base_horizon_margin_violation_count | exec_horizon_margin_violation_count | goal_distance_reduction_ratio | min_safety_h |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| 37 | 30 | 30 | 0 | 0.391892 | 3.416798 | 30 | 0 | 0.987913 | 0.000500027 |
| 85 | 30 | 30 | 0 | 0.654511 | 3.401781 | 30 | 0 | 0.303182 | 0.00050002 |
| 13 | 28 | 28 | 0 | 0.593209 | 3.421564 | 28 | 0 | 0.348974 | 0.000500013 |
| 31 | 22 | 22 | 0 | 0.566694 | 3.415046 | 22 | 0 | 0.36863 | 0.000500028 |
| 12 | 16 | 16 | 0 | 0.391344 | 3.393403 | 16 | 0 | 0.349691 | 0.000500075 |

## Top 5 Slowest Trials

| trial | runtime_mean | runtime_p95 | predictive_recovery_used_count | predictive_recovery_success_count | recovery_failed_count | base_horizon_margin_violation_count | exec_horizon_margin_violation_count | goal_distance_reduction_ratio | min_safety_h |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| 85 | 0.654511 | 3.401781 | 30 | 30 | 0 | 30 | 0 | 0.303182 | 0.00050002 |
| 13 | 0.593209 | 3.421564 | 28 | 28 | 0 | 28 | 0 | 0.348974 | 0.000500013 |
| 31 | 0.566694 | 3.415046 | 22 | 22 | 0 | 22 | 0 | 0.36863 | 0.000500028 |
| 14 | 0.450985 | 3.378476 | 8 | 8 | 0 | 8 | 0 | 0.09139 | 0.000500029 |
| 37 | 0.391892 | 3.416798 | 30 | 30 | 0 | 30 | 0 | 0.987913 | 0.000500027 |

## Interpretation

R4_H2_N64 preserved collision-free and QP-feasible behavior on dense flight official100 while reducing all tested executed H-step margin violations to zero. It is substantially cheaper than H3_N128 on this full100 run, but remains slower than the V4-A active projection + V1 navigation baseline because predictive recovery still evaluates H-step sequences on activated steps.
