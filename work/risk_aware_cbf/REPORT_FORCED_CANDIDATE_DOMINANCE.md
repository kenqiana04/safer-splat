# Forced-Candidate Dominance Diagnostic for Adaptive V1

## 1. Purpose

This report diagnoses why Adaptive V1 did not produce measured candidate-count or runtime gains after successful closed-loop integration. The central question is whether final candidate sets are dominated by forced candidates, especially heading-cone candidates, so that `selected_K` changes the scheduled budget but not the final unique candidate count.

## 2. Context

The full method remains Certified Feasibility-Aware Start-Safe CBF + Discrete-Time Verification + optional Predictive Recovery.

Adaptive V1 is a candidate budgeting / efficiency / risk-response support module. It is not a new CBF theorem, not an independent safety guarantee, not a replacement for Start-Safe CBF, not a replacement for Discrete-Time Verification, and not a replacement for optional Predictive Recovery.

This diagnostic uses existing closed-loop logs only. It does not run full100 and does not enable V4-C recovery.

## 3. Prior Evidence

Closed-loop smoke showed that `selected_K` was technically connected to V1 candidate budgeting, with `selected_K_applied_rate=1.0`, recovery disabled, and no crash / collision / QP infeasibility in smoke scopes.

Flight20 closed-loop showed stable integration on trials 0-19. It had no collision, no QP infeasibility, no crash, and no recovery use. However, measured candidate count changed little: balanced/fixed measured candidate ratio was `0.998359` over all steps.

Targeted DT-risk closed-loop focused on trials 13, 12, 14, 7, and 9. In targeted risk windows, balanced/fixed `selected_K` ratio was `2.884422`, but measured candidate-count ratio was `0.999773`. This supports risk response, not efficiency improvement.

## 4. Candidate Decomposition Evidence

Key adaptive-balanced decomposition:

| dataset | scope | steps | selected_K_mean | final_unique_mean | forced_near_mean | heading_mean | history_mean | forced_unique_mean | budget_limited_mean | forced_fraction_mean | heading_fraction_final | selected_K_final_ratio |
| --- | --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| flight20 | all_steps | 1753 | 1877.35 | 23308.62 | 78.08 | 23274.84 | 30.82 | 23308.62 | 0.00 | 1.00 | 0.998618 | 0.080543 |
| flight20 | risk_window | 212 | 5660.38 | 24819.08 | 399.43 | 24598.10 | 127.43 | 24819.08 | 0.00 | 1.00 | 0.991276 | 0.228066 |
| targeted | all_steps | 675 | 2746.67 | 24225.02 | 160.43 | 24148.18 | 52.48 | 24225.02 | 0.00 | 1.00 | 0.996936 | 0.113381 |
| targeted | risk_window | 199 | 5768.84 | 24914.66 | 404.12 | 24682.84 | 132.03 | 24914.66 | 0.00 | 1.00 | 0.990847 | 0.231544 |
| targeted | non_risk_window | 476 | 1483.19 | 23936.70 | 58.55 | 23924.65 | 19.22 | 23936.70 | 0.00 | 1.00 | 0.999482 | 0.061963 |

The forced candidate fraction is `1.0` in the relevant scopes. `budget_limited_candidate_count_mean` is `0.0`. Heading candidates account for roughly `99%` of final candidates in both all-step and risk-window views.

## 5. Scope Analysis

Flight20 all steps:

- balanced/fixed selected_K ratio: `0.938677`
- balanced/fixed measured candidate ratio: `0.998359`
- forced fraction balanced: `1.0`
- heading fraction of final balanced: `0.998618`

Targeted all steps:

- balanced/fixed selected_K ratio: `1.373333`
- balanced/fixed measured candidate ratio: `1.000451`
- forced fraction balanced: `1.0`
- heading fraction of final balanced: `0.996936`

Targeted risk windows:

- balanced/fixed selected_K ratio: `2.884422`
- balanced/fixed measured candidate ratio: `0.999773`
- balanced/fixed runtime ratio: `0.985188`
- balanced/fixed active-constraint ratio: `1.084924`
- forced fraction balanced: `1.0`
- heading fraction of final balanced: `0.990847`

DT-warning / low-margin / fallback scopes:

- DT-warning selected_K ratio: `3.742574`, measured candidate ratio: `1.002781`
- low-margin selected_K ratio: `3.852632`, measured candidate ratio: `1.002899`
- fallback steps exist only for adaptive_balanced in this comparison; all fallback steps still have forced fraction `1.0` and budget-limited count `0.0`

Per-trial targeted risk windows:

- trial 7: final unique mean `18024.45`, heading mean `17987.91`, forced fraction `1.0`
- trial 9: final unique mean `25811.68`, heading mean `25495.04`, forced fraction `1.0`
- trial 12: final unique mean `25185.92`, heading mean `24923.21`, forced fraction `1.0`
- trial 13: final unique mean `25620.47`, heading mean `25366.03`, forced fraction `1.0`
- trial 14: final unique mean `23932.06`, heading mean `23914.00`, forced fraction `1.0`

## 6. Correlation Analysis

Targeted adaptive-balanced risk windows:

| x | y | corr | n | status |
| --- | --- | ---: | ---: | --- |
| selected_K | measured_candidate_count | 0.259707 | 199 | ok |
| selected_K | heading_candidate_count | 0.235039 | 199 | ok |
| selected_K | history_candidate_count | 0.993444 | 199 | ok |
| selected_K | runtime_step | -0.060434 | 199 | ok |
| measured_candidate_count | runtime_step | 0.151925 | 199 | ok |
| heading_candidate_count | runtime_step | 0.165136 | 199 | ok |

The high correlation between `selected_K` and `history_candidate_count` is expected because the adaptive runner updates `history_k` from the selected budget. It does not change the main conclusion, because history candidates remain small compared with heading candidates and final unique count remains forced-dominated.

## 7. Pipeline Inspection

Read-only inspection found:

- `selected_K` is passed to `selector.candidate_budget` in `work/risk_aware_cbf/scripts/run_adaptive_v1_flight20_closed_loop.py:197` and `work/risk_aware_cbf/scripts/run_adaptive_v1_targeted_dt_risk_closed_loop.py:211`.
- `selected_K` controls the V1 selector's `candidate_budget`.
- Forced near candidates are selected by `distances <= self.near_distance_threshold`.
- Forced heading candidates are selected by heading distance and cosine thresholds.
- Forced history candidates are selected from `high_active_ids` within a local history distance.
- Forced near, heading, and history candidates are unioned before risk-ranked fill.
- The optional risk-ranked pool is filled only if `forced_count < self.candidate_budget`.
- There is no post-union cap on `selected_ids`; `final_count = selected_ids.shape[0]`.
- `budget_limited_candidate_count` records the optional risk-ranked fill count. It remains zero when forced candidates already exceed the selected budget.

This explains why `selected_K` can be applied correctly while final unique candidate count remains much larger than `selected_K`.

## 8. Optional Cap Sensitivity

An offline accounting-only sensitivity was run on the targeted results. It does not modify the selector and does not run closed-loop navigation.

Adaptive-balanced targeted risk-window accounting:

| heading_cap | original_final_mean | hypothetical_final_mean | reduction_ratio | affected_steps_fraction | safety_concern |
| ---: | ---: | ---: | ---: | ---: | --- |
| 2000 | 24914.66 | 2231.82 | 0.909927 | 1.0 | True |
| 4000 | 24914.66 | 4231.82 | 0.829007 | 1.0 | True |
| 8000 | 24914.66 | 8231.82 | 0.667167 | 1.0 | True |
| 12000 | 24914.66 | 12231.82 | 0.505327 | 1.0 | True |
| 16000 | 24914.66 | 16231.82 | 0.343487 | 1.0 | True |

This shows there may be large accounting headroom if heading candidates are controlled, but every cap affects forced candidates. Therefore it is not safety evidence and not runtime evidence. Any forced-candidate-aware method would need a conservative fallback design, closed-loop smoke, and DT Verification.

## 9. Interpretation

Adaptive V1 risk response is real: risk windows receive higher `selected_K`, and selected budgets are applied to the V1 wrapper.

Adaptive V1 efficiency evidence is not present in the current implementation: final candidate count does not decrease because the final candidate set is already determined by forced candidates, mainly heading candidates.

The current role of `selected_K` is bounded. It controls the optional risk-ranked remainder and influences history support size, but it does not cap the final union after forced near / heading / history candidates.

Forced-candidate dominance explains why measured candidate count remains unchanged despite risk-responsive scheduling.

## 10. Decision

- Continue Adaptive V1: yes, as a support module / ablation.
- Recommend full100 now: no.
- Recommend Adaptive V1 as paper main method: no.
- Recommend claiming candidate-count or runtime improvement: no.
- Recommend forced-candidate-aware design: yes, as design/future work or a separate offline-to-smoke sequence.
- Recommend FC-aware closed-loop pilot immediately: no. The minimum next step is a safe wrapper-level design with full-query fallback criteria and offline sensitivity, followed by smoke only if the design is defensible.

## 11. Limitations

- This diagnostic is not a full benchmark.
- The cap sensitivity is hypothetical accounting only.
- Adaptive V1 does not independently guarantee safety.
- `min_safety_h` is the repository GSplat ellipsoid safety h value, not metric clearance.
- A margin violation is not a collision.
- No official core source was modified.
- No new CBF theorem is claimed.
- Forced candidate capping may create safety risk and would need full-query fallback, closed-loop validation, and DT Verification if ever implemented.

