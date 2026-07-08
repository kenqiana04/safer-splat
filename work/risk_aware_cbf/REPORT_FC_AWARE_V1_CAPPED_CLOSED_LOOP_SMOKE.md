# FC-Aware V1 Capped Closed-Loop Smoke

## 1. Purpose

This report validates wrapper-level nearest_first cap16000 closed-loop smoke only. It is not full100, not final method validation, and not a safety guarantee.

## 2. Background

Selected_K-only Adaptive V1 did not reduce candidate count because forced heading candidates dominated. The exact recall audit supported nearest_first cap16000 as a deployable smoke candidate with exact risk recall on targeted windows.

## 3. Smoke Setup

- Profiles: fixed baseline and fc_aware_nearest_cap16000.
- Heading cap: 16000.
- Ranking: nearest_first.
- Recovery: disabled.
- Scope: staged smoke runs only; no flight20 and no full100.

## 4. Integration and Closed-Loop Results

| scope | trial_id | measured_candidate_count_ratio | final_candidate_count_ratio | runtime_ratio | min_safety_h_delta | H1_violation_delta | H2_violation_delta | H3_violation_delta | cap_applied_count | unsafe_to_expand | pass_smoke |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| trial12_step20 | 12 | 0.762293 | 0.762293 | 1.01184 | 4.65661e-10 | 0 | 0 | 0 | 20 | False | True |
| trial12_step80 | 12 | 0.646465 | 0.646465 | 1.00723 | 4.42378e-09 | 0 | 0 | 0 | 80 | False | True |
| trial13_step20 | 13 | 0.763017 | 0.763017 | 1.026 | 0 | 0 | 0 | 0 | 20 | False | True |

## 5. Decision

- Recommended action: `RECOMMEND_TARGETED_EXTENSION_ONLY`.
- If safety worsens, freeze. If candidate count reduces and safety is unchanged, only targeted extension is justified.
- Full100 is not recommended from this smoke.

## 6. Limitations

- Smoke only, not benchmark validation.
- FC-Aware V1 is an efficiency support module and does not replace CBF-QP, DT verification, or recovery.
- h / min_safety_h is not metric clearance.
- Margin violation is not collision.
- No official core source was modified.
