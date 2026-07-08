# FC-Aware V1 Targeted Risk-Window Closed-Loop Extension

## 1. Purpose

This report validates nearest_first cap16000 in targeted DT-risk / low-margin windows. It is not flight20, not full100, and not official benchmark validation.

## 2. Background

Selected_K-only Adaptive V1 did not reduce candidate count because forced heading candidates dominated. Exact recall and capped smoke supported a staged targeted extension before any broader run.

## 3. Setup

- Profiles: fixed vs fc_aware_nearest_cap16000.
- Heading cap: 16000.
- Ranking: nearest_first.
- Recovery: disabled.
- V4-C recovery: disabled.
- No flight20 and no full100 were run.

## 4. All-Steps Results

| stage | trial_id | scope | measured_candidate_count_ratio | final_candidate_count_ratio | heading_count_ratio | runtime_ratio | min_safety_h_delta | H1_violation_delta | H2_violation_delta | H3_violation_delta | DT_warning_delta | low_margin_delta | fallback_count | unsafe_to_expand | pass_smoke |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| trial14_step80 | 14 | all_steps | 0.726062 | 0.726062 | 0.725672 | 1.04165 | 3.49246e-09 | 0 | 0 | 0 | 0 | 0 | 0 | False | True |
| trial12_step180 | 12 | all_steps | 0.648427 | 0.648427 | 0.646774 | 1.03985 | -5.82077e-10 | 0 | 0 | 0 | 0 | 0 | 0 | False | True |
| trial13_step190 | 13 | all_steps | 0.648575 | 0.648575 | 0.647032 | 1.00058 | 5.82077e-10 | 0 | 0 | 0 | 0 | 0 | 0 | False | True |
| trial7_step140 | 7 | all_steps | 0.69987 | 0.69987 | 0.699545 | 1.03312 | 1.97906e-09 | 0 | 0 | 0 | 0 | 0 | 0 | False | True |
| trial9_step130 | 9 | all_steps | 0.653945 | 0.653945 | 0.652684 | 1.01938 | 1.39698e-09 | 0 | 0 | 0 | 0 | 0 | 0 | False | True |

## 5. Risk-Window Results

| stage | trial_id | scope | measured_candidate_count_ratio | final_candidate_count_ratio | heading_count_ratio | runtime_ratio | min_safety_h_delta | H1_violation_delta | H2_violation_delta | H3_violation_delta | DT_warning_delta | low_margin_delta | fallback_count | unsafe_to_expand | pass_smoke |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| trial14_step80 | 14 | risk_window | 0.669506 | 0.669506 | 0.669064 | 1.01736 | 1.97906e-09 | 0 | 0 | 0 | 0 | 0 | 0 | False | True |
| trial12_step180 | 12 | risk_window | 0.645209 | 0.645209 | 0.641972 | 1.0478 | -1.04774e-09 | 0 | 0 | 0 | 0 | 0 | 0 | False | True |
| trial13_step190 | 13 | risk_window | 0.633929 | 0.633929 | 0.630765 | 1.01208 | 1.39698e-09 | 0 | 0 | 0 | 0 | 0 | 0 | False | True |
| trial7_step140 | 7 | risk_window | 0.889746 | 0.889746 | 0.889486 | 1.05273 | 1.97906e-09 | 0 | 0 | 0 | 0 | 0 | 0 | False | True |
| trial9_step130 | 9 | risk_window | 0.632099 | 0.632099 | 0.627572 | 1.02792 | 1.39698e-09 | 0 | 0 | 0 | 0 | 0 | 0 | False | True |

## 6. Safety / DT Verification Check

- Any unsafe_to_expand: False.
- Collision, QP infeasible, H-step margin deltas, DT-warning deltas, and low-margin deltas are evaluated per completed scope.

## 7. Candidate Reduction Check

- All primary risk-window scopes candidate-reduced: True.

## 8. Runtime Observation

Runtime ratios are observed targeted-extension measurements only. They are not a formal runtime-improvement claim.

## 9. Decision

- Recommended action: `CONTINUE_FC_AWARE_V1_CONSIDER_FLIGHT20_CANDIDATE_CAUTIOUSLY`.
- Reason: targeted risk-window scopes were stable and showed candidate-count reduction.
- Recommend flight20 candidate next: True.
- Recommend full100 now: False.

## 10. Limitations

- Targeted extension only, not full100 and not official benchmark validation.
- FC-Aware V1 is a candidate-selection support module, not a safety guarantee.
- No new CBF theorem is claimed.
- h / min_safety_h is not metric clearance.
- Margin violation is not collision.
- No official core source was modified.
