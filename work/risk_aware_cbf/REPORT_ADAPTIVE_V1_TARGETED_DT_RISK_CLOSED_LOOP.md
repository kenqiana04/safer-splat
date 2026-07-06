# Adaptive V1 Targeted DT-Risk Closed-Loop Diagnostic

## 1. Purpose

This report diagnoses Adaptive V1 balanced on targeted DT-risk / low-margin closed-loop trials. It is not a full100 benchmark and not an official benchmark result.

## 2. Methodology Context

The full framework remains Certified Feasibility-Aware Start-Safe CBF + Discrete-Time Verification + optional Predictive Recovery. Adaptive V1 is a candidate budgeting and efficiency / risk-response support module. It is not a standalone safety guarantee, not a DT Verification replacement, and not a Predictive Recovery replacement.

## 3. Prior Flight20 Closed-Loop Evidence

Flight20 showed `selected_K_applied_rate=1.0`, collision / QP / crash counts of zero, DT warning count of 101, low-margin count of 90, and candidate decomposition dominated by forced candidates. It did not justify a runtime or candidate-count improvement claim.

## 4. Target Selection

Target trials: `[7, 9, 12, 13, 14]`.

The runner starts from each trial start. Target windows are analysis windows only; no mid-trial state initialization is claimed.

| profile | trial_id | num_steps | dt_warning_count | low_margin_step_count | min_safety_h_min | H1_margin_violation_count | H2_margin_violation_count | H3_margin_violation_count | fallback_count | progress |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| fixed | 13 | 179 | 46 | 42 | 0.000327737 | 43 | 45 | 47 | 0 | 0.356224 |
| fixed | 12 | 167 | 43 | 40 | 0.000341621 | 41 | 43 | 45 | 0 | 0.358452 |
| fixed | 14 | 70 | 10 | 8 | 0.000341767 | 9 | 10 | 11 | 0 | 0.0954932 |
| fixed | 7 | 131 | 2 | 0 | 0.000511227 | 0 | 0 | 0 | 0 | 0.315061 |
| fixed | 9 | 128 | 0 | 0 | 0.000507401 | 0 | 0 | 0 | 0 | 0.306306 |
| adaptive_balanced | 13 | 179 | 46 | 42 | 0.000327737 | 43 | 45 | 47 | 41 | 0.356224 |
| adaptive_balanced | 12 | 167 | 43 | 40 | 0.00034162 | 41 | 43 | 45 | 39 | 0.358452 |
| adaptive_balanced | 14 | 70 | 10 | 8 | 0.000341767 | 9 | 10 | 11 | 8 | 0.0954932 |
| adaptive_balanced | 7 | 131 | 2 | 0 | 0.000511231 | 0 | 0 | 0 | 0 | 0.31506 |
| adaptive_balanced | 9 | 128 | 0 | 0 | 0.000507403 | 0 | 0 | 0 | 0 | 0.306306 |

## 5. Experimental Setup

- profiles: fixed vs adaptive_balanced
- recovery disabled
- selected_K applied before V1 candidate selection
- wrapper-visible candidate decomposition recorded
- no official core source modification

## 6. Targeted Closed-Loop Results

| profile | scope | trial_count | num_steps | runtime_mean | runtime_p95 | runtime_max | selected_K_mean | selected_K_p95 | selected_K_max | selected_K_applied_rate | measured_candidate_count_mean | measured_candidate_count_p95 | measured_candidate_count_max | active_constraint_count_mean | active_constraint_count_p95 | collision_count | qp_infeasible_count | min_safety_h_min | H1_margin_violation_count | H2_margin_violation_count | H3_margin_violation_count | DT_warning_count | low_margin_step_count | fallback_count | fallback_fraction | progress_mean | crash_count | recovery_used_count |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| fixed | all_steps | 5 | 675 | 0.0591772 | 0.0642848 | 0.0772143 | 2000 | 2000 | 2000 | 1 | 24214.1 | 27688.1 | 29280 | 172.532 | 284.9 | 0 | 0 | 0.000327737 | 93 | 98 | 103 | 101 | 95 | 0 | 0 | 0.286307 | 0 | 0 |
| adaptive_balanced | all_steps | 5 | 675 | 0.0576865 | 0.06105 | 0.0808075 | 2746.67 | 8000 | 8000 | 1 | 24225 | 27684.7 | 29272 | 173.707 | 296.3 | 0 | 0 | 0.000327737 | 93 | 98 | 103 | 101 | 95 | 88 | 0.13037 | 0.286307 | 0 | 0 |

## 7. Risk-Window Focused Analysis

| profile | scope | trial_count | num_steps | runtime_mean | runtime_p95 | runtime_max | selected_K_mean | selected_K_p95 | selected_K_max | selected_K_applied_rate | measured_candidate_count_mean | measured_candidate_count_p95 | measured_candidate_count_max | active_constraint_count_mean | active_constraint_count_p95 | collision_count | qp_infeasible_count | min_safety_h_min | H1_margin_violation_count | H2_margin_violation_count | H3_margin_violation_count | DT_warning_count | low_margin_step_count | fallback_count | fallback_fraction | progress_mean | crash_count | recovery_used_count |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| fixed | risk_window | 5 | 123 | 0.0577969 | 0.0619944 | 0.0692613 | 2000 | 2000 | 2000 | 1 | 24920.3 | 26610.6 | 27063 | 102.325 | 202 | 0 | 0 | 0.000327737 | 93 | 98 | 103 | 101 | 95 | 0 | 0 |  | 0 | 0 |
| fixed | non_risk_window | 5 | 552 | 0.0594847 | 0.0644546 | 0.0772143 | 2000 | 2000 | 2000 | 1 | 24056.7 | 27756.8 | 29280 | 188.176 | 291 | 0 | 0 | 0.000507401 | 0 | 0 | 0 | 0 | 0 | 0 | 0 |  | 0 | 0 |
| adaptive_balanced | risk_window | 5 | 199 | 0.0569408 | 0.0620914 | 0.0808075 | 5768.84 | 8000 | 8000 | 1 | 24914.7 | 26900.2 | 29171 | 111.015 | 206.1 | 0 | 0 | 0.000327737 | 93 | 98 | 103 | 101 | 95 | 88 | 0.442211 |  | 0 | 0 |
| adaptive_balanced | non_risk_window | 5 | 476 | 0.0579983 | 0.0608465 | 0.0750129 | 1483.19 | 2000 | 2000 | 1 | 23936.7 | 27719.8 | 29272 | 199.916 | 300.25 | 0 | 0 | 0.000719097 | 0 | 0 | 0 | 0 | 0 | 0 | 0 |  | 0 | 0 |

Target-window table:

| profile | scope | trial_count | num_steps | runtime_mean | runtime_p95 | runtime_max | selected_K_mean | selected_K_p95 | selected_K_max | selected_K_applied_rate | measured_candidate_count_mean | measured_candidate_count_p95 | measured_candidate_count_max | active_constraint_count_mean | active_constraint_count_p95 | collision_count | qp_infeasible_count | min_safety_h_min | H1_margin_violation_count | H2_margin_violation_count | H3_margin_violation_count | DT_warning_count | H2_warning_count | H3_warning_count | low_margin_step_count | mode_fixed_count | mode_nominal_count | mode_caution_count | mode_critical_count | mode_recovery_support_count | fallback_count | fallback_fraction | forced_near_candidate_count_mean | heading_candidate_count_mean | history_candidate_count_mean | forced_unique_candidate_count_mean | final_unique_candidate_count_mean | budget_limited_candidate_count_mean | forced_candidate_fraction_mean | recovery_used_count | missing_field_count | progress_mean | crash_count | trial_id | window_id | start_step | end_step |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| fixed | target_window | 1 | 11 | 0.0555368 | 0.0576591 | 0.0589284 | 2000 | 2000 | 2000 | 1 | 18004.7 | 19002.5 | 19089 | 118.091 | 132.5 | 0 | 0 | 0.000511227 | 0 | 0 | 0 | 2 | 2 | 6 | 0 | 11 | 0 | 0 | 0 | 0 | 0 | 0 | 369.364 | 17987.9 | 23.1818 | 18004.7 | 18004.7 | 0 | 1 | 0 | 0 |  | 0 | 7 | 3 | 121 | 131 |
| fixed | target_window | 1 | 25 | 0.0593386 | 0.0629163 | 0.0632392 | 2000 | 2000 | 2000 | 1 | 25801.7 | 29134 | 29165 | 176.24 | 192.6 | 0 | 0 | 0.000507401 | 0 | 0 | 0 | 0 | 0 | 3 | 0 | 25 | 0 | 0 | 0 | 0 | 0 | 0 | 528.84 | 25495.1 | 27.44 | 25801.7 | 25801.7 | 0 | 1 | 0 | 0 |  | 0 | 9 | 4 | 87 | 111 |
| fixed | target_window | 1 | 72 | 0.0572592 | 0.0619755 | 0.0675037 | 2000 | 2000 | 2000 | 1 | 25133.5 | 26214.1 | 26467 | 92.8056 | 108.45 | 0 | 0 | 0.000341621 | 41 | 43 | 45 | 43 | 43 | 48 | 42 | 72 | 0 | 0 | 0 | 0 | 0 | 0 | 381.847 | 24923.2 | 31.8056 | 25133.5 | 25133.5 | 0 | 1 | 0 | 0 |  | 0 | 12 | 7 | 96 | 167 |
| fixed | target_window | 1 | 73 | 0.058063 | 0.0632949 | 0.0692613 | 2000 | 2000 | 2000 | 1 | 25568 | 26634 | 26859 | 88.863 | 103.4 | 0 | 0 | 0.000327737 | 43 | 45 | 47 | 46 | 46 | 51 | 44 | 73 | 0 | 0 | 0 | 0 | 0 | 0 | 392.918 | 25366 | 31.7123 | 25568 | 25568 | 0 | 1 | 0 | 0 |  | 0 | 13 | 8 | 107 | 179 |
| fixed | target_window | 1 | 18 | 0.0585768 | 0.0593722 | 0.0595037 | 2000 | 2000 | 2000 | 1 | 23922.6 | 24107.3 | 24126 | 224 | 274.9 | 0 | 0 | 0.000341767 | 9 | 10 | 11 | 10 | 10 | 13 | 9 | 18 | 0 | 0 | 0 | 0 | 0 | 0 | 386.611 | 23914 | 25 | 23922.6 | 23922.6 | 0 | 1 | 0 | 0 |  | 0 | 14 | 9 | 53 | 70 |
| adaptive_balanced | target_window | 1 | 11 | 0.0554234 | 0.0594411 | 0.0618104 | 4000 | 4000 | 4000 | 1 | 18024.5 | 19020 | 19106 | 116.727 | 129.5 | 0 | 0 | 0.000511231 | 0 | 0 | 0 | 2 | 2 | 6 | 0 | 0 | 0 | 0 | 11 | 0 | 0 | 0 | 369.364 | 17987.9 | 51.2727 | 18024.5 | 18024.5 | 0 | 1 | 0 | 0 |  | 0 | 7 | 3 | 121 | 131 |
| adaptive_balanced | target_window | 1 | 25 | 0.0590058 | 0.0621977 | 0.0625353 | 4000 | 4000 | 4000 | 1 | 25811.7 | 29140 | 29171 | 174.16 | 190.6 | 0 | 0 | 0.000507403 | 0 | 0 | 0 | 0 | 0 | 3 | 0 | 0 | 0 | 0 | 25 | 0 | 0 | 0 | 528.84 | 25495 | 54.04 | 25811.7 | 25811.7 | 0 | 1 | 0 | 0 |  | 0 | 9 | 4 | 87 | 111 |
| adaptive_balanced | target_window | 1 | 72 | 0.0559642 | 0.0620958 | 0.0777564 | 6166.67 | 8000 | 8000 | 1 | 25185.9 | 26293.1 | 26546 | 88.75 | 110 | 0 | 0 | 0.00034162 | 41 | 43 | 45 | 43 | 43 | 48 | 42 | 0 | 0 | 0 | 33 | 39 | 39 | 0.541667 | 381.847 | 24923.2 | 152.208 | 25185.9 | 25185.9 | 0 | 1 | 0 | 0 |  | 0 | 12 | 7 | 96 | 167 |
| adaptive_balanced | target_window | 1 | 73 | 0.0570952 | 0.0609798 | 0.0808075 | 6246.58 | 8000 | 8000 | 1 | 25620.5 | 26714.2 | 26938 | 86.5753 | 103.8 | 0 | 0 | 0.000327737 | 43 | 45 | 47 | 46 | 46 | 51 | 44 | 0 | 0 | 0 | 32 | 41 | 41 | 0.561644 | 392.918 | 25366 | 155.466 | 25620.5 | 25620.5 | 0 | 1 | 0 | 0 |  | 0 | 13 | 8 | 107 | 179 |
| adaptive_balanced | target_window | 1 | 18 | 0.0582805 | 0.0601895 | 0.0642556 | 5777.78 | 8000 | 8000 | 1 | 23932.1 | 24110.3 | 24129 | 208 | 244.45 | 0 | 0 | 0.000341767 | 9 | 10 | 11 | 10 | 10 | 13 | 9 | 0 | 0 | 0 | 10 | 8 | 8 | 0.444444 | 386.611 | 23914 | 113.944 | 23932.1 | 23932.1 | 0 | 1 | 0 | 0 |  | 0 | 14 | 9 | 53 | 70 |

Adaptive balanced increases selected_K in risk windows: `True`.

## 8. Candidate Dominance Diagnostic

| profile | scope | selected_K_mean | measured_candidate_count_mean | final_unique_candidate_count_mean | forced_near_candidate_count_mean | heading_candidate_count_mean | history_candidate_count_mean | forced_unique_candidate_count_mean | budget_limited_candidate_count_mean | forced_candidate_fraction_mean |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| fixed | all_steps | 2000 | 24214.1 | 24214.1 | 160.428 | 24148.2 | 26.2563 | 24214.1 | 0 | 1 |
| fixed | risk_window | 2000 | 24920.3 | 24920.3 | 379.065 | 24734.5 | 30.2276 | 24920.3 | 0 | 1 |
| fixed | non_risk_window | 2000 | 24056.7 | 24056.7 | 111.71 | 24017.5 | 25.3714 | 24056.7 | 0 | 1 |
| adaptive_balanced | all_steps | 2746.67 | 24225 | 24225 | 160.428 | 24148.2 | 52.48 | 24225 | 0 | 1 |
| adaptive_balanced | risk_window | 5768.84 | 24914.7 | 24914.7 | 404.116 | 24682.8 | 132.03 | 24914.7 | 0 | 1 |
| adaptive_balanced | non_risk_window | 1483.19 | 23936.7 | 23936.7 | 58.5504 | 23924.7 | 19.2227 | 23936.7 | 0 | 1 |

Forced candidates still dominate: `True`.

Budget-limited candidate count zero: `True`.

Candidate count changed in risk windows: `False`.

## 9. Interpretation

Adaptive V1 remains valid as a risk-response budgeting module because it increases `selected_K` in DT-risk windows and does not degrade the reported safety metrics. However, final candidate count remains dominated by forced candidates, especially heading candidates, so this diagnostic does not provide closed-loop efficiency evidence.

## 10. Decision

- Continue Adaptive V1: `True`
- Recommend full100 now: `False`
- Recommend forced-candidate dominance follow-up: `True`
- Paper role: `support_module_or_ablation_not_main_safety_method`

## 11. Limitations

- targeted DT-risk closed-loop is not full100 benchmark.
- Adaptive V1 does not independently guarantee safety.
- `min_safety_h` is the repository GSplat ellipsoid safety h value, not meter clearance.
- Margin violation is not collision.
- No official SAFER-Splat core source was modified.
- No new CBF theorem is claimed.
- V4-C recovery was disabled.
- Candidate decomposition is wrapper-visible only.
- `selected_K_applied` does not imply final candidate count reduction.
- Forced candidate dominance may limit efficiency gains.
