# Risk-Aware V2 Trial 57 Analysis

Generated: 2026-07-01T16:24:00

## Main Trial 57 Comparison

| config_id | collision_count | min_safety_h_min | progress_mean | runtime_mean | runtime_p95 | qp_infeasible_count | recovery_used_rate | first_recovery_step | safe_recovered_step |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| risk_aware_v1_bestD | 1 | -0.0003094291314 | 0.522682395 | 0.05252950558 | 0.05853408668 | 0 | 0 |  | 10 |
| risk_aware_v2_adaptive | 1 | -0.0003094291314 | 0.5212605302 | 0.04980779126 | 0.1102820958 | 0 | 0 |  | 10 |
| risk_aware_v2_adaptive_recovery | 1 | -0.0003094291314 | 0.50958871 | 0.0476891375 | 0.08779013455 | 0 | 0.06569343066 | 1 | 7 |
| safer_splat_filter | 1 | -0.0003094291314 | 0.5209763612 | 0.1151152839 | 0.1497155702 | 0 | 0 |  | 10 |

## Recovery Sweep

| config_id | collision_count | min_safety_h_min | progress_mean | runtime_mean | runtime_p95 | qp_infeasible_count | recovery_used_rate | first_recovery_step | safe_recovered_step |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| R0_default | 1 | -0.0003094291314 | 0.50958871 | 0.04955767943 | 0.08731463701 | 0 | 0.06569343066 | 1 | 7 |
| R1_stronger_repulse | 1 | -0.0003094291314 | 0.509877596 | 0.04797451391 | 0.0887486659 | 0 | 0.06569343066 | 1 | 7 |
| R2_more_damping | 1 | -0.0003094291314 | 0.5094952283 | 0.04932124058 | 0.08789029568 | 0 | 0.06569343066 | 1 | 7 |
| R3_larger_recovery_near | 1 | -0.0003094291314 | 0.50958871 | 0.04890004464 | 0.09092257544 | 0 | 0.06569343066 | 1 | 7 |
| R4_full_conservative | 1 | -0.0003094291314 | 0.5097904043 | 0.04975853345 | 0.08936677687 | 0 | 0.06569343066 | 1 | 7 |

## Answers

- V2 adaptive budgeting alone solves trial 57: False
- V2 recovery solves trial 57: False
- If solved, safe recovery step: 7
- If not solved, violation magnitude reduced: False
- Recovery progress trade-off: -0.011387651155820966
- Recovery runtime trade-off: -0.0674261464434403
- QP infeasible observed: False
- Best recovery sweep config: R1_stronger_repulse

The first recorded step is already unsafe. Recovery starts at step 1 and can move the state back to non-negative safety by step 7, but collision_count remains 1 because the trajectory already contains a negative min_safety_h sample.
