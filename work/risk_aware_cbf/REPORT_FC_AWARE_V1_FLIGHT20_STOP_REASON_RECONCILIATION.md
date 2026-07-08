# FC-Aware V1 Flight20 Stop-Reason Reconciliation

## 1. Purpose

This report reconciles why the FC-Aware V1 flight20 candidate evaluation stopped early and records the final freeze decision for the current FC-Aware V1 branch. It does not introduce a new experiment and does not change the official SAFER-Splat core source.

## 2. Context

FC-Aware V1 is a candidate-selection / efficiency support module. It is not the main safety method and does not replace Start-Safe CBF, Discrete-Time Verification, CBF-QP filtering, or optional Predictive Recovery.

Prior FC-Aware evidence was positive in narrower scopes:

- heading shadow audit identified forced heading candidates as the candidate-count bottleneck;
- exact recall audit supported `nearest_first` with `cap=16000` on targeted replay rows;
- capped closed-loop smoke passed trial12 step20, trial13 step20, and trial12 step80;
- targeted risk-window extension passed trial14, trial12, trial13, trial7, and trial9 windows with candidate-count reduction and no monitored safety / DT-metric worsening.

The flight20 run was intended as a broader candidate evaluation before any full100 decision. It was not full100 and not official benchmark validation.

## 3. What Was Run

- Requested trials: 0-19.
- Completed paired comparison: trial0 only.
- Fixed and `fc_aware_nearest_cap16000` both stopped at trial0 step359.
- Recovery: disabled.
- V4-C recovery: disabled.
- Full100: not run.
- Official core source: not modified.
- Forbidden source diff: empty for `cbf/`, `splat/`, `ellipsoids/`, `dynamics/`, and `run.py`.

## 4. Paired Trial0 Results

| profile | step_count | candidate_count_mean | heading_before | heading_after | final_before | final_after | runtime_mean | runtime_p95 | runtime_max | collision_count | qp_infeasible_count | min_safety_h_min | H1/H2/H3 | DT_warning | low_margin | progress_mean | fallback_count |
| --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | --- | ---: | ---: | ---: | ---: |
| fixed | 359 | 21418.6 | 21106.8 | 21106.8 | 21418.6 | 21418.6 | 0.0572675 | 0.0643161 | 0.070312 | 1 | 0 | -7.567e-10 | 262 / 263 / 264 | 263 | 262 | 0.251 | 0 |
| fc_aware_nearest_cap16000 | 359 | 16319.6 | 21106.8 | 16000.0 | 21418.6 | 16319.6 | 0.0600923 | 0.0619172 | 0.0702593 | 1 | 0 | -6.98492e-10 | 262 / 263 / 264 | 263 | 262 | 0.251 | 0 |

## 5. Relative Comparison

| metric | value |
| --- | ---: |
| measured_candidate_count_ratio | 0.761938 |
| final_candidate_count_ratio | 0.761938 |
| heading_count_ratio | 0.758048 |
| runtime_ratio | 1.04933 |
| min_safety_h_delta | +5.82077e-11 |
| H1/H2/H3 violation delta | 0 / 0 / 0 |
| DT_warning_delta | 0 |
| low_margin_delta | 0 |
| progress_delta | -1.14241e-08 |
| fallback_count | 0 |
| unsafe_to_expand | true |
| pass_scope | false |

The capped profile reduced measured, final, and heading candidate counts. The monitored H-step, DT-warning, low-margin, fallback, and progress deltas did not worsen relative to fixed in this paired trial0 comparison.

However, collision occurred in both fixed and capped configurations. From the current evidence, this collision should not be attributed to the FC-Aware cap alone. The correct interpretation is that the broader recovery-disabled flight20 candidate evaluation exposed an unsafe condition in trial0 for both configurations.

## 6. Why Expansion Must Stop

The expansion must stop because collision / negative h exists in the broader evaluation. Even though the capped profile reduced candidate counts and did not increase the monitored H-step / DT-warning / low-margin metrics relative to fixed, the broader evaluation is not safe enough to expand.

Consequences:

- `unsafe_to_expand = true`;
- partial flight20 cannot be reported as flight20 success;
- full100 must not be run from this branch;
- the current FC-Aware V1 branch should be frozen or redesigned before any future broader validation.

## 7. Final FC-Aware V1 Evidence Summary

Positive evidence:

- forced heading bottleneck identified;
- selected_K-only limitation diagnosed;
- exact active / tight / low-h recall passed for nearest_first cap16000 in targeted replay;
- smoke passed without monitored safety / DT metric worsening;
- targeted risk-window extension passed;
- candidate-count reduction was shown in smoke and targeted risk-window scopes.

Negative / blocker evidence:

- broader flight20 candidate evaluation stopped at trial0;
- fixed and capped both encountered collision;
- no complete flight20 evidence exists;
- no full100 evidence exists;
- this branch cannot support benchmark validation claims.

## 8. Final Decision

| decision item | result |
| --- | --- |
| Continue current FC-Aware V1 branch | no |
| Continue experiments now | no |
| Redesign as possible future work | yes |
| Run full100 now | no |
| Use as paper main method | no |
| Paper role | diagnostic / targeted ablation / future efficiency direction |

FC-Aware V1 should be frozen as a diagnostic and ablation branch. The main paper direction should return to Certified Feasibility-Aware Start-Safe CBF, Discrete-Time Verification, and optional triggered V4-C recovery.

## 9. Limitations

- This is partial flight20 only, not complete flight20.
- This is not full100 and not official benchmark validation.
- Collision is not attributed to FC-Aware alone because fixed also collided.
- `h` / `min_safety_h` is repository GSplat ellipsoid safety h, not meter clearance.
- Margin violation is not collision.
- No new CBF theorem is claimed.
- No standalone safety guarantee is claimed.
- No formal runtime improvement is claimed.
- No official core source was modified.
