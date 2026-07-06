# Adaptive V1 Balanced Scheduler and Flight20 Offline Replay

## 1. Purpose

This report evaluates whether the balanced scheduler is a better next Adaptive V1 profile than the conservative scheduler. The current experiment is offline replay / audit, not closed-loop navigation, and it does not change the FAS-CBF main line.

## 2. Methodology Context

The full framework remains Certified Feasibility-Aware Start-Safe CBF + Discrete-Time Verification + optional Predictive Recovery. Adaptive V1 is an efficiency / risk-response support module. It is not a standalone safety guarantee, not a DT Verification replacement, and not a Predictive Recovery replacement.

## 3. Previous Conservative Pilot Summary

The previous conservative hotspot pilot showed risk-response behavior: H2/H3 warning steps used budgets near `8000`. It also showed high fallback usage and `selected_K_mean` above fixed V1. Because that result was offline replay, it did not prove closed-loop runtime benefit.

## 4. Balanced Scheduler Design

The balanced profile changes escalation:

- DT warning only enters `critical`, not `recovery_support`.
- Low current h only enters `critical`.
- Low current h plus DT warning enters `recovery_support`.
- Recovery active, unresolved risk, or abnormal candidate set still enters `recovery_support`.

## 5. Sanity Check

Scheduler sanity check: `passed`. The balanced fake cases verify nominal, caution, DT-warning-only critical, low-h-only critical, low-h plus DT-warning recovery-support, recovery-active recovery-support, candidate-empty recovery-support, missing-signal fallback, and K clipping.

## 6. Smoke Test

| profile | rows | selected_K_mean | fallback_count | mode_nominal_count | mode_fixed_count |
| --- | --- | --- | --- | --- | --- |
| fixed | 5 | 2000 | 0 | 0 | 5 |
| adaptive_conservative | 5 | 1000 | 0 | 5 | 0 |
| adaptive_balanced | 5 | 1000 | 0 | 5 | 0 |

## 7. Hotspot Offline Replay

Hotspot trials: `85,37,13,31,12,14`.

| profile | selected_K_mean | selected_K_p95 | selected_K_max | fallback_count | fallback_fraction | mode_nominal_count | mode_caution_count | mode_critical_count | mode_recovery_support_count | H2_warning_selected_K_mean | H2_warning_selected_K_p95 | H3_warning_selected_K_mean | H3_warning_selected_K_p95 | low_margin_selected_K_mean | low_margin_selected_K_p95 | non_warning_selected_K_mean | non_warning_selected_K_p95 | collision_count | qp_infeasible_count | H1_margin_violation_count | H2_margin_violation_count | H3_margin_violation_count |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| fixed | 2000 | 2000 | 2000 | 0 | 0 | 0 | 0 | 0 | 0 | 2000 | 2000 | 2000 | 2000 | 2000 | 2000 | 2000 | 2000 | 0 | 0 | 261 | 272 | 283 |
| adaptive_conservative | 3562.67 | 8000 | 8000 | 256 | 0.234218 | 230 | 406 | 201 | 256 | 7676.47 | 8000 | 7533.57 | 8000 | 8000 | 8000 | 2175.31 | 4000 | 0 | 0 | 261 | 272 | 283 |
| adaptive_balanced | 3540.71 | 8000 | 8000 | 250 | 0.228728 | 230 | 406 | 207 | 250 | 7676.47 | 8000 | 7533.57 | 8000 | 7906.25 | 8000 | 2145.68 | 4000 | 0 | 0 | 261 | 272 | 283 |

## 8. Flight20 Offline Replay

Flight20 trials: `0-19`.

| profile | selected_K_mean | selected_K_p95 | selected_K_max | fallback_count | fallback_fraction | mode_nominal_count | mode_caution_count | mode_critical_count | mode_recovery_support_count | H2_warning_selected_K_mean | H2_warning_selected_K_p95 | H3_warning_selected_K_mean | H3_warning_selected_K_p95 | low_margin_selected_K_mean | low_margin_selected_K_p95 | non_warning_selected_K_mean | non_warning_selected_K_p95 | collision_count | qp_infeasible_count | H1_margin_violation_count | H2_margin_violation_count | H3_margin_violation_count |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| fixed | 2000 | 2000 | 2000 | 0 | 0 | 0 | 0 | 0 | 0 | 2000 | 2000 | 2000 | 2000 | 2000 | 2000 | 2000 | 2000 | 0 | 0 | 96 | 101 | 108 |
| adaptive_conservative | 2037.61 | 8000 | 8000 | 93 | 0.0529915 | 796 | 714 | 152 | 93 | 7603.96 | 8000 | 7370.37 | 8000 | 8000 | 8000 | 1687.92 | 4000 | 0 | 0 | 96 | 101 | 108 |
| adaptive_balanced | 2033.05 | 8000 | 8000 | 91 | 0.0518519 | 796 | 714 | 154 | 91 | 7603.96 | 8000 | 7370.37 | 8000 | 7913.98 | 8000 | 1683.06 | 4000 | 0 | 0 | 96 | 101 | 108 |

Mode counts:

| profile | mode | count | fraction |
| --- | --- | --- | --- |
| fixed | fixed | 1755 | 1 |
| adaptive_conservative | caution | 714 | 0.406838 |
| adaptive_conservative | critical | 152 | 0.0866097 |
| adaptive_conservative | nominal | 796 | 0.453561 |
| adaptive_conservative | recovery_support | 93 | 0.0529915 |
| adaptive_balanced | caution | 714 | 0.406838 |
| adaptive_balanced | critical | 154 | 0.0877493 |
| adaptive_balanced | nominal | 796 | 0.453561 |
| adaptive_balanced | recovery_support | 91 | 0.0518519 |

Risk-response groups:

| profile | risk_group | rows | selected_K_mean | selected_K_p95 | fallback_count | critical_count | recovery_support_count |
| --- | --- | --- | --- | --- | --- | --- | --- |
| fixed | all_steps | 1755 | 2000 | 2000 | 0 | 0 | 0 |
| fixed | H2_warning | 101 | 2000 | 2000 | 0 | 0 | 0 |
| fixed | H2_non_warning | 1654 | 2000 | 2000 | 0 | 0 | 0 |
| fixed | H3_warning | 108 | 2000 | 2000 | 0 | 0 | 0 |
| fixed | H3_non_warning | 1647 | 2000 | 2000 | 0 | 0 | 0 |
| fixed | low_margin_current_h_le_dt_margin | 93 | 2000 | 2000 | 0 | 0 | 0 |
| fixed | non_warning_no_H2_or_H3_warning | 1647 | 2000 | 2000 | 0 | 0 | 0 |
| adaptive_conservative | all_steps | 1755 | 2037.61 | 8000 | 93 | 152 | 93 |
| adaptive_conservative | H2_warning | 101 | 7603.96 | 8000 | 91 | 10 | 91 |
| adaptive_conservative | H2_non_warning | 1654 | 1697.7 | 4000 | 2 | 142 | 2 |
| adaptive_conservative | H3_warning | 108 | 7370.37 | 8000 | 91 | 17 | 91 |
| adaptive_conservative | H3_non_warning | 1647 | 1687.92 | 4000 | 2 | 135 | 2 |
| adaptive_conservative | low_margin_current_h_le_dt_margin | 93 | 8000 | 8000 | 93 | 0 | 93 |
| adaptive_conservative | non_warning_no_H2_or_H3_warning | 1647 | 1687.92 | 4000 | 2 | 135 | 2 |
| adaptive_balanced | all_steps | 1755 | 2033.05 | 8000 | 91 | 154 | 91 |
| adaptive_balanced | H2_warning | 101 | 7603.96 | 8000 | 91 | 10 | 91 |
| adaptive_balanced | H2_non_warning | 1654 | 1692.87 | 4000 | 0 | 144 | 0 |
| adaptive_balanced | H3_warning | 108 | 7370.37 | 8000 | 91 | 17 | 91 |
| adaptive_balanced | H3_non_warning | 1647 | 1683.06 | 4000 | 0 | 137 | 0 |
| adaptive_balanced | low_margin_current_h_le_dt_margin | 93 | 7913.98 | 8000 | 91 | 2 | 91 |
| adaptive_balanced | non_warning_no_H2_or_H3_warning | 1647 | 1683.06 | 4000 | 0 | 137 | 0 |

## 9. Risk-Response Vs Budget-Control Tradeoff

Balanced reduces fallback count vs conservative: `True`.

Balanced reduces selected_K mean vs conservative: `True`.

Balanced keeps H2 warning response: `True`.

Balanced keeps H3 warning response: `True`.

Balanced is therefore the better candidate for a closed-loop smoke test if the user wants to continue beyond offline replay.

## 10. Decision

Continue Adaptive V1: `True`.

Recommend closed-loop smoke: `True`.

Recommend flight20 closed-loop now: `False`. Run closed-loop smoke first.

Recommend full100 now: `False`. Reason: Offline replay should not be used to jump directly to full100; run closed-loop smoke first.

Paper role: `ablation_or_support_module_until_closed_loop`. Current evidence supports an ablation or support-module discussion until closed-loop evidence exists.

## 11. Limitations

- Offline replay is not closed-loop navigation.
- `selected_K` is a scheduled budget proxy, not measured closed-loop candidate count.
- Runtime is inherited from the saved trajectory.
- Collision and QP infeasibility are inherited from the saved trajectory.
- H-step margin violations are inherited from the saved trajectory.
- Adaptive V1 does not independently guarantee safety.
- `min_safety_h` is the repository GSplat ellipsoid safety h value, not meter clearance.
- Margin violation is not collision.
- No official SAFER-Splat core source was modified.
- No new CBF theorem is claimed.
