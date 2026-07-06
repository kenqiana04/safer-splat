# Adaptive V1 Balanced Flight20 Closed-Loop Pilot

## 1. Purpose

This report evaluates Adaptive V1 balanced on a flight20 closed-loop pilot. It is not a full100 benchmark and not an official benchmark result.

## 2. Methodology Context

The full framework remains Certified Feasibility-Aware Start-Safe CBF + Discrete-Time Verification + optional Predictive Recovery. Adaptive V1 is a candidate budgeting and efficiency / risk-response support module. It is not a safety theorem, not a DT Verification replacement, and not a Predictive Recovery replacement.

## 3. Prior Evidence

Offline replay showed that the balanced scheduler preserves DT-warning response while slightly reducing over-fallback relative to the conservative profile. Closed-loop smoke showed `selected_K_applied_rate=1.0` and no crash, collision, QP infeasibility, or H-step margin violation in the smoke scopes. Smoke also showed that measured final candidate count can remain dominated by forced near / heading / history candidates.

## 4. Experimental Scope

- trials 0-19
- profiles: fixed vs adaptive_balanced
- recovery disabled
- closed-loop navigation with CBF filtering
- no official SAFER-Splat core source modification

## 5. Integration Check

- selected_K_applied_rate fixed: `1.0`
- selected_K_applied_rate balanced: `1.0`
- selected_K integration ok: `True`
- recovery_used_count balanced: `0`
- candidate decomposition is reported below when wrapper-visible fields are available.

## 6. Flight20 Closed-Loop Results

| profile | trial_count | num_steps | runtime_mean | runtime_p95 | runtime_max | selected_K_mean | selected_K_p95 | selected_K_max | selected_K_applied_rate | measured_candidate_count_mean | measured_candidate_count_p95 | measured_candidate_count_max | active_constraint_count_mean | active_constraint_count_p95 | active_constraint_count_max | collision_count | qp_infeasible_count | min_safety_h_min | H1_margin_violation_count | H2_margin_violation_count | H3_margin_violation_count | DT_warning_count | low_margin_step_count | fallback_count | fallback_fraction | progress_mean | crash_count | recovery_used_count | missing_field_count |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| fixed | 20 | 1755 | 0.0585986 | 0.0634454 | 0.0798746 | 2000 | 2000 | 2000 | 1 | 23346.9 | 28691.9 | 37171 | 176.671 | 307.3 | 390 | 0 | 0 | 0.000327737 | 93 | 98 | 103 | 101 | 90 | 0 | 0 | 0.211536 | 0 | 0 | 0 |
| adaptive_balanced | 20 | 1753 | 0.0583903 | 0.0623556 | 0.0706654 | 1877.35 | 5600 | 8000 | 1 | 23308.6 | 28580.8 | 37171 | 178.056 | 310 | 390 | 0 | 0 | 0.000327737 | 93 | 98 | 103 | 101 | 90 | 88 | 0.0501997 | 0.211668 | 0 | 0 | 0 |

## 7. Mode Switching and Risk Response

| profile | mode | count | fraction |
| --- | --- | --- | --- |
| fixed | fixed | 1755 | 1 |
| adaptive_balanced | caution | 550 | 0.313748 |
| adaptive_balanced | critical | 124 | 0.0707359 |
| adaptive_balanced | nominal | 991 | 0.565317 |
| adaptive_balanced | recovery_support | 88 | 0.0501997 |

| profile | risk_group | rows | selected_K_mean | selected_K_p95 | measured_candidate_count_mean | mode_critical_count | mode_recovery_support_count |
| --- | --- | --- | --- | --- | --- | --- | --- |
| fixed | all_steps | 1755 | 2000 | 2000 | 23346.9 | 0 | 0 |
| fixed | dt_warning | 101 | 2000 | 2000 | 25173.7 | 0 | 0 |
| fixed | H2_warning | 101 | 2000 | 2000 | 25173.7 | 0 | 0 |
| fixed | H3_warning | 121 | 2000 | 2000 | 24906.6 | 0 | 0 |
| fixed | non_warning | 1654 | 2000 | 2000 | 23235.4 | 0 | 0 |
| fixed | non_warning_no_H2_or_H3_warning | 1634 | 2000 | 2000 | 23231.4 | 0 | 0 |
| fixed | low_margin_current_h_le_dt_margin | 90 | 2000 | 2000 | 25429.1 | 0 | 0 |
| fixed | fallback_used | 0 |  |  |  | 0 | 0 |
| adaptive_balanced | all_steps | 1753 | 1877.35 | 5600 | 23308.6 | 124 | 88 |
| adaptive_balanced | dt_warning | 101 | 7485.15 | 8000 | 25243.7 | 13 | 88 |
| adaptive_balanced | H2_warning | 101 | 7485.15 | 8000 | 25243.7 | 13 | 88 |
| adaptive_balanced | H3_warning | 121 | 6909.09 | 8000 | 24967.1 | 33 | 88 |
| adaptive_balanced | non_warning | 1652 | 1534.5 | 4000 | 23190.3 | 111 | 0 |
| adaptive_balanced | non_warning_no_H2_or_H3_warning | 1632 | 1504.29 | 4000 | 23185.7 | 91 | 0 |
| adaptive_balanced | low_margin_current_h_le_dt_margin | 90 | 7911.11 | 8000 | 25506.2 | 2 | 88 |
| adaptive_balanced | fallback_used | 88 | 8000 | 8000 | 25500.3 | 0 | 88 |

Risk response triggered: `True`.

DT warning count balanced: `101`.

Low-margin step count balanced: `90`.

## 8. Candidate Decomposition

| profile | selected_K_mean | measured_candidate_count_mean | final_unique_candidate_count_mean | forced_near_candidate_count_mean | heading_candidate_count_mean | history_candidate_count_mean | forced_unique_candidate_count_mean | budget_limited_candidate_count_mean | forced_candidate_fraction_mean | candidate_decomposition_available |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| fixed | 2000 | 23346.9 | 23346.9 | 77.3236 | 23316.2 | 24.1105 | 23346.9 | 0 | 1 | True |
| adaptive_balanced | 1877.35 | 23308.6 | 23308.6 | 78.077 | 23274.8 | 30.822 | 23308.6 | 0 | 1 | True |

Measured candidate count ratio balanced/fixed: `0.9983586431600103`.

Candidate count changed materially: `False`.

## 9. Fixed Vs Adaptive Balanced Interpretation

- runtime ratio balanced/fixed: `0.9964449214477794`
- selected_K ratio balanced/fixed: `0.9386765544780377`
- min_safety_h delta balanced-fixed: `0.0`
- H1/H2/H3 margin violation deltas: `0.0`, `0.0`, `0.0`
- progress delta balanced-fixed: `0.00013164233868720454`
- runtime improvement supported: `False`

`selected_K_applied_rate` checks that the scheduled budget entered V1 candidate budgeting. It does not by itself prove final candidate count reduction.

## 10. Decision

- Continue Adaptive V1: `True`
- Recommend full100 now: `False`
- Recommend targeted DT-risk closed-loop next: `True`
- Paper role: `support_module_or_ablation_not_main_safety_method`

## 11. Limitations

- flight20 is not full100 benchmark.
- Adaptive V1 does not independently guarantee safety.
- `min_safety_h` is the repository GSplat ellipsoid safety h value, not meter clearance.
- Margin violation is not collision.
- No official SAFER-Splat core source was modified.
- No new CBF theorem is claimed.
- V4-C recovery was disabled.
- Candidate-count decomposition is limited to wrapper-visible selector logic.
- `selected_K_applied` does not necessarily imply final candidate count reduction.
