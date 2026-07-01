# Risk-Aware V2 Trial 57 Report

## Scope

This report evaluates V2 adaptive budgeting and recovery mode on the flight trial-57 hard case.
It does not modify official SAFER-Splat source code.
It does not claim a new CBF theorem.

## Method

V2 uses adaptive criticality levels: SAFE, WARNING, CRITICAL, and RECOVERY.

The default budget schedule is SAFE=1000, WARNING=2000, CRITICAL=5000, and RECOVERY=full candidate mode.

The near threshold schedule is SAFE=0.05, WARNING=0.08, CRITICAL=0.12, and RECOVERY=0.15. The heading distance schedule is SAFE=0.20, WARNING=0.25, CRITICAL=0.35, and RECOVERY=0.50.

The recovery nominal command is a wrapper-level command:

```text
u_recovery = k_repulse * normalize(robot_position - nearest_gaussian_center)
             - k_damp * robot_velocity
```

The default recovery parameters are k_repulse=1.0, k_damp=0.5, critical lambda=0.5, and unsafe lambda=1.0.

Actual insertion level: partial pre-CBF candidate budgeting plus wrapper-level nominal command replacement before calling the official CBF-QP.

official source modified = no

## Trial 57 Comparison

| config_id | collision_count | min_safety_h_min | progress_mean | runtime_mean | runtime_p95 | qp_infeasible_count | recovery_used_rate | first_recovery_step | safe_recovered_step |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| risk_aware_v1_bestD | 1 | -0.0003094291314 | 0.522682395 | 0.05252950558 | 0.05853408668 | 0 | 0 |  | 10 |
| risk_aware_v2_adaptive | 1 | -0.0003094291314 | 0.5212605302 | 0.04980779126 | 0.1102820958 | 0 | 0 |  | 10 |
| risk_aware_v2_adaptive_recovery | 1 | -0.0003094291314 | 0.50958871 | 0.0476891375 | 0.08779013455 | 0 | 0.06569343066 | 1 | 7 |
| safer_splat_filter | 1 | -0.0003094291314 | 0.5209763612 | 0.1151152839 | 0.1497155702 | 0 | 0 |  | 10 |

Best recovery sweep config:

| config_id | collision_count | min_safety_h_min | progress_mean | runtime_mean | runtime_p95 | qp_infeasible_count | recovery_used_rate | first_recovery_step | safe_recovered_step |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| R1_stronger_repulse | 1 | -0.0003094291314 | 0.509877596 | 0.04797451391 | 0.0887486659 | 0 | 0.06569343066 | 1 | 7 |

## Interpretation

V2 adaptive budgeting alone does not solve trial 57.

V2 adaptive recovery also does not solve trial 57 under the strict collision criterion, because the first recorded step already has negative min_safety_h. Recovery is triggered at step 1 and reaches non-negative safety by step 7, but the trajectory still contains an unsafe sample.

The recovery sweep does not find a configuration with collision_count=0 or positive min_safety_h_min. The design therefore cannot claim hard-case recovery for flight trial 57.

Runtime remains lower than the SAFER-Splat baseline in this single-trial test, but the safety gate is not satisfied. This supports keeping V1 as the main efficiency result and treating V2 as a future-method prototype unless the recovery design is changed at a deeper controller or initialization level.

## Next Decision

KEEP_V1_AS_MAIN_AND_V2_AS_FUTURE

Reason: V2 recovery does not pass the strict trial-57 safety gate; V1 remains the cleaner main efficiency result.
