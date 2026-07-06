# Adaptive V1 Balanced Closed-Loop Smoke Test

## 1. Purpose

This report only verifies whether Adaptive V1 balanced can connect to the closed-loop navigation / CBF filtering pipeline. It is not a full benchmark and not an official flight100 result.

## 2. Methodology Context

The full framework remains Certified Feasibility-Aware Start-Safe CBF + Discrete-Time Verification + optional Predictive Recovery. Adaptive V1 is a candidate budgeting and efficiency / risk-response support module. It is not a safety theorem, not a DT Verification replacement, and not a Predictive Recovery replacement.

## 3. Difference From Offline Replay

Offline replay used `selected_K` as a scheduled proxy. In this closed-loop smoke, `selected_K` is written into the V1 candidate selector before candidate selection and CBF matrix construction. This report evaluates only smoke-scale closed-loop integration.

## 4. Experimental Scope

- trial 0 max_steps 5
- trial 0 max_steps 20, if smoke passed
- trial 12 max_steps 20, if trial0 step20 passed
- recovery disabled
- profiles compared: fixed vs adaptive_balanced

## 5. Integration Check

- selected_K_applied_rate balanced: `1.0`
- selected_K integration ok: `True`
- recovery_used_count balanced: `0`
- crash / missing field checks are included in the comparison table.

The selected budget was passed into the V1 selector, but the measured candidate count changed only slightly in these smoke cases because forced near / heading / history candidates dominated the final candidate set. Therefore this smoke validates integration, not closed-loop runtime or candidate-count improvement.

## 6. Smoke Results

### trial0 max_steps 5

| profile | runtime_mean | runtime_p95 | runtime_max | selected_K_mean | selected_K_p95 | selected_K_max | selected_K_applied_rate | measured_candidate_count_mean | measured_candidate_count_p95 | active_constraint_count_mean | collision_count | qp_infeasible_count | min_safety_h_min | H1_margin_violation_count | H2_margin_violation_count | H3_margin_violation_count | fallback_count | progress_mean | crash_count | recovery_used_count |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| fixed | 0.0667413 | 0.0737937 | 0.0742896 | 2000 | 2000 | 2000 | 1 | 25544.4 | 25781 | 187.8 | 0 | 0 | 0.0138523 | 0 | 0 | 0 | 0 | 0.00415089 | 0 | 0 |
| adaptive_balanced | 0.0621459 | 0.0660595 | 0.0671509 | 1000 | 1000 | 1000 | 1 | 25544.4 | 25781 | 187.8 | 0 | 0 | 0.0138523 | 0 | 0 | 0 | 0 | 0.00415089 | 0 | 0 |

### trial0 max_steps 20

| profile | runtime_mean | runtime_p95 | runtime_max | selected_K_mean | selected_K_p95 | selected_K_max | selected_K_applied_rate | measured_candidate_count_mean | measured_candidate_count_p95 | active_constraint_count_mean | collision_count | qp_infeasible_count | min_safety_h_min | H1_margin_violation_count | H2_margin_violation_count | H3_margin_violation_count | fallback_count | progress_mean | crash_count | recovery_used_count |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| fixed | 0.0626724 | 0.0656446 | 0.0710641 | 2000 | 2000 | 2000 | 1 | 28713.3 | 32913.1 | 202.7 | 0 | 0 | 0.0135199 | 0 | 0 | 0 | 0 | 0.0514485 | 0 | 0 |
| adaptive_balanced | 0.0605578 | 0.0627906 | 0.0672688 | 1000 | 1000 | 1000 | 1 | 28713.3 | 32913.1 | 202.7 | 0 | 0 | 0.0135199 | 0 | 0 | 0 | 0 | 0.0514485 | 0 | 0 |

### hotspot max_steps 20

| profile | runtime_mean | runtime_p95 | runtime_max | selected_K_mean | selected_K_p95 | selected_K_max | selected_K_applied_rate | measured_candidate_count_mean | measured_candidate_count_p95 | active_constraint_count_mean | collision_count | qp_infeasible_count | min_safety_h_min | H1_margin_violation_count | H2_margin_violation_count | H3_margin_violation_count | fallback_count | progress_mean | crash_count | recovery_used_count |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| fixed | 0.0575024 | 0.0601482 | 0.0634927 | 2000 | 2000 | 2000 | 1 | 20999.2 | 23365.8 | 260.2 | 0 | 0 | 0.00321891 | 0 | 0 | 0 | 0 | 0.0492433 | 0 | 0 |
| adaptive_balanced | 0.0583943 | 0.0605817 | 0.0640895 | 1000 | 1000 | 1000 | 1 | 20997.2 | 23363.7 | 278.2 | 0 | 0 | 0.00321891 | 0 | 0 | 0 | 0 | 0.0492433 | 0 | 0 |

Mode counts for the final analyzed scope:

| profile | mode | count | fraction |
| --- | --- | --- | --- |
| fixed | fixed | 20 | 1 |
| adaptive_balanced | nominal | 20 | 1 |

Risk response for the final analyzed scope:

| profile | risk_group | rows | selected_K_mean | selected_K_p95 | measured_candidate_count_mean | mode_critical_count | mode_recovery_support_count |
| --- | --- | --- | --- | --- | --- | --- | --- |
| fixed | all_steps | 20 | 2000 | 2000 | 20999.2 | 0 | 0 |
| fixed | dt_warning | 0 |  |  |  | 0 | 0 |
| fixed | non_warning | 20 | 2000 | 2000 | 20999.2 | 0 | 0 |
| fixed | fallback_used | 0 |  |  |  | 0 | 0 |
| adaptive_balanced | all_steps | 20 | 1000 | 1000 | 20997.2 | 0 | 0 |
| adaptive_balanced | dt_warning | 0 |  |  |  | 0 | 0 |
| adaptive_balanced | non_warning | 20 | 1000 | 1000 | 20997.2 | 0 | 0 |
| adaptive_balanced | fallback_used | 0 |  |  |  | 0 | 0 |

## 7. Fixed Vs Adaptive Balanced Comparison

Adaptive balanced closed-loop run status: `True`.

Runtime ratio balanced/fixed: `1.0155099865588708`.

Selected budget application is checked by `selected_K_applied_rate`; recovery remained disabled and `recovery_used_count` is reported separately.

Measured candidate counts should be interpreted cautiously: they are real closed-loop measurements, but in these low-warning smoke cases they are dominated by forced candidate inclusion and do not demonstrate an efficiency gain.

## 8. Decision

- Continue Adaptive V1: `True`
- Recommend flight20 closed-loop: `True`
- Recommend full100 now: `False`
- Paper role: `support_module_or_ablation_until_flight20_closed_loop`

No matter the smoke result, this is not a full benchmark and should not be used as a direct full100 conclusion.

## 9. Limitations

- Closed-loop smoke is not full benchmark.
- Smoke result is not official flight100 result.
- Adaptive V1 does not independently guarantee safety.
- `min_safety_h` is the repository GSplat ellipsoid safety h value, not meter clearance.
- Margin violation is not collision.
- No official SAFER-Splat core source was modified.
- No new CBF theorem is claimed.
- V4-C recovery was disabled.
