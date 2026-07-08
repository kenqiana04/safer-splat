# FC-Aware V1 Flight20 Closed-Loop Candidate Evaluation

## 1. Purpose

This report evaluates nearest_first cap16000 over flight trials 0-19. It is not full100 and not official benchmark validation.

## 2. Background

Selected_K-only Adaptive V1 did not reduce final candidate counts because forced heading candidates dominated. FC-Aware V1 targets that heading bottleneck as a wrapper-level candidate-selection support module. Exact recall, capped smoke, and targeted risk-window extension were completed before this broader flight20 candidate run.

## 3. Setup

- Profiles: fixed vs fc_aware_nearest_cap16000.
- Trials: 0-19.
- Heading cap: 16000.
- Ranking: nearest_first.
- Recovery: disabled.
- V4-C recovery: disabled.
- Full100: not run.

## 3.1 Execution Stop

- Requested trials: 20.
- Completed paired comparison trials: 1.
- Stopped early: True.
- Stop reason: collision_stop_at_trial0.

## 4. Overall Results

| profile | scope | trial_count | step_count | measured_candidate_count_mean | measured_candidate_count_p95 | measured_candidate_count_max | heading_before_mean | heading_after_mean | final_before_mean | final_after_mean | runtime_mean | runtime_p95 | runtime_max | collision_count | qp_infeasible_count | min_safety_h_min | H1_margin_violation_count | H2_margin_violation_count | H3_margin_violation_count | DT_warning_count | low_margin_count | fallback_count | progress_mean | recovery_used_count |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| fixed | all_steps | 1 | 359 | 21418.6 | 31902 | 37171 | 21106.8 | 21106.8 | 21418.6 | 21418.6 | 0.0572675 | 0.0643161 | 0.070312 | 1 | 0 | -7.567e-10 | 262 | 263 | 264 | 263 | 262 | 0 | 0.251 | 0 |
| fc_aware_nearest_cap16000 | all_steps | 1 | 359 | 16319.6 | 16522 | 16523 | 21106.8 | 16000 | 21418.6 | 16319.6 | 0.0600923 | 0.0619172 | 0.0702593 | 1 | 0 | -6.98492e-10 | 262 | 263 | 264 | 263 | 262 | 0 | 0.251 | 0 |

## 5. Comparison Fixed vs FC-Aware

| scope | measured_candidate_count_ratio | final_candidate_count_ratio | heading_count_ratio | runtime_ratio | min_safety_h_delta | H1_violation_delta | H2_violation_delta | H3_violation_delta | DT_warning_delta | low_margin_delta | progress_delta | fallback_count | unsafe_to_expand | pass_scope |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| all_steps | 0.761938 | 0.761938 | 0.758048 | 1.04933 | 5.82077e-11 | 0 | 0 | 0 | 0 | 0 | -1.14241e-08 | 0 | True | False |

## 6. Per-Trial Analysis

| trial_id | measured_candidate_count_ratio | final_candidate_count_ratio | heading_count_ratio | runtime_ratio | min_safety_h_delta | H1_violation_delta | H2_violation_delta | H3_violation_delta | DT_warning_delta | low_margin_delta | progress_delta | fallback_count | unsafe_to_expand | pass_scope |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| 0 | 0.761938 | 0.761938 | 0.758048 | 1.04933 | 5.82077e-11 | 0 | 0 | 0 | 0 | 0 | -1.14241e-08 | 0 | True | False |

## 7. Risk-Window Analysis

Activated risk-window trials: ``.

Risk-window rows are analyzed separately when prior targeted windows are present.

## 8. Runtime Observation

Runtime ratios are observed flight20 measurements only. They are not a formal runtime-improvement claim.

## 9. Decision

- Continue FC-Aware V1: False.
- Recommend full100 candidate next: False.
- Recommend full100 now: False.
- Recommended action: `FREEZE_OR_REDESIGN_FC_AWARE_V1`.
- Reason: safety or candidate-count criterion failed.

## 10. Limitations

- flight20 only, not full100 and not official benchmark validation.
- FC-Aware V1 is a candidate-selection / efficiency support module, not a standalone safety guarantee.
- No new CBF theorem is claimed.
- h / min_safety_h is not metric clearance.
- Margin violation is not collision.
- No official core source was modified.
