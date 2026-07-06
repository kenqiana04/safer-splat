# V4-C Runtime Tuning Pilot Analysis

## Results

| config_id | collision_count | qp_infeasible_count | base_horizon_margin_violation_count | exec_horizon_margin_violation_count | predictive_recovery_success_count | recovery_failed_count | runtime_mean | runtime_p95 | runtime_max | progress_mean | min_safety_h_min | runtime_ratio_vs_R0 |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| R0_H3_N128_baseline | 0 | 0 | 152 | 0 | 152 | 0 | 1.27952 | 1.6106 | 1.66152 | 0.406569 | 0.000500098 | 1 |
| R1_H3_N64 | 0 | 0 | 152 | 0 | 152 | 0 | 0.799017 | 1.01213 | 1.03395 | 0.406569 | 0.000500098 | 0.624466 |
| R2_H3_N32 | 0 | 0 | 152 | 0 | 152 | 0 | 0.567821 | 0.694699 | 0.705759 | 0.406569 | 0.000500098 | 0.443776 |
| R3_H3_N64_conservative | 0 | 0 | 152 | 0 | 152 | 0 | 0.831883 | 1.04604 | 1.07353 | 0.406568 | 0.000500096 | 0.650152 |
| R4_H2_N64 | 0 | 0 | 134 | 0 | 134 | 0 | 0.517519 | 0.649463 | 0.666929 | 0.408297 | 0.000500013 | 0.404463 |
| R5_H3_N64_goal_preserving | 0 | 0 | 150 | 0 | 150 | 0 | 0.820329 | 1.01866 | 1.06004 | 0.4061 | 0.000500098 | 0.641122 |

## Direct answers

1. Lowest runtime config on hotspot trials: `R4_H2_N64`.
2. Lowest runtime config with zero exec H-step margin violations and no failures: `R4_H2_N64`.
3. N=64 keeps safety margin: `True`; N=32 keeps safety margin: `True`.
4. H=2 fails: `False`.
5. Conservative config runtime_mean: `0.8318834542761794`, exec violations: `0`.
6. Goal-preserving progress_mean: `0.4060998624822856` versus R0 `0.4065688447338507`.
7. Worth a future full100 tuned config run: `True`.
8. Recommended tuned config: `R4_H2_N64`.
9. Failed configs: `[]`.

## Recommended decision

PROCEED_TO_TUNED_V4C_FULL100
