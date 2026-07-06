# Adaptive V1 Risk-Aware Candidate Budgeting Pilot

## 1. Purpose

This report evaluates whether Adaptive V1 is worth continuing as an efficiency and risk-response support module for FAS-CBF. It does not change the paper main line and does not introduce a new safety theorem.

## 2. Methodology Context

The full framework remains Certified Feasibility-Aware Start-Safe CBF + Discrete-Time Verification + optional Predictive Recovery. Adaptive V1 is a support module for candidate budgeting. It is not a standalone safety guarantee, not a replacement for DT Verification, and not a replacement for optional Predictive Recovery.

## 3. Fixed V1 Limitation

Fixed V1 uses one candidate budget across easy and hard states. Low-risk states may be over-budgeted. High-risk states may need larger candidate coverage. Fixed V1 cannot explicitly react to DT Verification warning flags.

## 4. Adaptive Scheduler Design

The scheduler uses four interpretable modes:

| mode | trigger | selected K | fallback rule |
| --- | --- | ---: | --- |
| nominal | no risk signal active | 1000 | fixed V1 if all signals missing |
| caution | near margin, high speed, high active count, or high density | 2000 | keep fixed-level budget under uncertainty |
| critical | DT warning, critical margin, or critical local complexity | 4000 | escalate if candidate set is unreliable |
| recovery-support / fallback | recovery flag, unresolved risk, too-low h, or empty candidate set | 8000 | max-budget or full-query fallback |

All budgets are clipped into the configured `[K_min, K_max]` range.

## 5. Smoke Test

Smoke was run on trial `0`, max steps `5`, for fixed and adaptive modes. Both runs completed and wrote scheduler decisions. Adaptive selected nominal mode for all smoke steps because no DT warning or low-margin signal was present.

## 6. Pilot Evaluation

This pilot is **offline replay / audit**, not closed-loop navigation. It reads the saved V4-A + V1 no-recovery trajectory and the DT Verification audit. Runtime, collision, QP infeasibility, and safety values are inherited from the saved trajectory. Candidate count is the scheduled `selected_K` proxy, not a measured closed-loop candidate count.

Evaluated trial ids: `12,13,14,31,37,85`. Max steps per trial: `all saved steps`.

## 7. Fixed vs Adaptive Comparison

| run_label | runtime_mean | runtime_p95 | runtime_max | candidate_count_mean | candidate_count_p95 | active_constraint_count_mean | collision_count | qp_infeasible_count | min_safety_h_min | H1_margin_violation_count | H2_margin_violation_count | H3_margin_violation_count | fallback_count |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| fixed | 0.0590048 | 0.062837 | 0.0764928 | 2000 | 2000 | 154.796 | 0 | 0 | 0.000197846 | 261 | 272 | 283 | 0 |
| adaptive | 0.0590048 | 0.062837 | 0.0764928 | 3562.67 | 8000 | 154.796 | 0 | 0 | 0.000197846 | 261 | 272 | 283 | 256 |
| adaptive_minus_fixed | 0 | 0 | 0 | 1562.67 | 6000 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 256 |
| adaptive_over_fixed | 1 | 1 | 1 | 1.78134 | 4 | 1 |  |  | 1 | 1 | 1 | 1 |  |

Mode counts:

| run_label | mode | count | fraction |
| --- | --- | --- | --- |
| fixed | fixed | 1093 | 1 |
| adaptive | caution | 406 | 0.371455 |
| adaptive | critical | 201 | 0.183898 |
| adaptive | nominal | 230 | 0.21043 |
| adaptive | recovery_support | 256 | 0.234218 |

## 8. Risk-Response Behavior

| risk_group | rows | selected_K_mean | selected_K_p95 | critical_count | recovery_support_count | fallback_count |
| --- | --- | --- | --- | --- | --- | --- |
| all_adaptive_steps | 1093 | 3562.67 | 8000 | 201 | 256 | 256 |
| H2_DT_warning_true | 272 | 7676.47 | 8000 | 22 | 250 | 250 |
| H2_DT_warning_false | 821 | 2199.76 | 4000 | 179 | 6 | 6 |
| H3_DT_warning_true | 283 | 7533.57 | 8000 | 33 | 250 | 250 |
| H3_DT_warning_false | 810 | 2175.31 | 4000 | 168 | 6 | 6 |
| current_h_le_dt_margin_0.0005 | 256 | 8000 | 8000 | 0 | 256 | 256 |
| current_h_le_h_critical_0.00075 | 455 | 6250.55 | 8000 | 199 | 256 | 256 |
| active_constraints_ge_250 | 181 | 2110.5 | 4000 | 10 | 0 | 0 |
| speed_ge_0.09 | 0 |  |  | 0 | 0 | 0 |

Adaptive increases budget on H2 DT-warning steps: `True`.

## 9. Decision

Recommendation to continue: `True`.

Recommendation to enter flight20: `True`.

Recommendation to enter full100 now: `False`. Reason: Do not jump from offline replay/audit directly to full100; run flight20 or closed-loop pilot first.

Paper role: `support_module_after_additional_pilot`. Based on this offline replay, Adaptive V1 is best described as an efficiency / risk-response support module or ablation candidate until additional flight20 or closed-loop evidence is available.

## 10. Limitations

- This pilot is not a full benchmark unless full100 is explicitly run.
- Offline replay is not closed-loop navigation.
- Adaptive V1 does not independently guarantee safety.
- `min_safety_h` is the repository GSplat ellipsoid safety h value, not meter clearance.
- Margin violation is not collision.
- Official SAFER-Splat core source is not modified.
- No new CBF theorem is claimed.
