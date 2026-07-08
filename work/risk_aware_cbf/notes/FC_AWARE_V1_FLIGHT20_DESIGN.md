# FC-Aware V1 Flight20 Design

## Purpose

Evaluate the deployable `fc_aware_nearest_cap16000` wrapper in a broader flight closed-loop candidate run over trials 0-19. This is a flight20 candidate evaluation only. It is not full100 and not official benchmark validation.

## Why Flight20

Prior FC-Aware evidence established:

- exact active / low-h recall support for `nearest_first`, `cap=16000`;
- wrapper-level capped closed-loop smoke success;
- targeted risk-window extension success on trials 14, 12, 13, 7, and 9;
- candidate-count reduction without collision, QP infeasibility, or H-step / DT-warning deltas in those targeted scopes.

Flight20 is the next small broader check before any full100 decision. Passing flight20 can only justify a cautious full100 candidate decision, not an automatic full100 run.

## Profiles

- `fixed`: original V1 wrapper behavior, no heading cap, recovery disabled.
- `fc_aware_nearest_cap16000`: heading `nearest_first` top 16000, near keep-all, full-heading fallback enabled, DT guard enabled, recovery disabled.

## Scope

- Scene: `flight`.
- Trials: 0-19.
- Max steps: default 800 unless overridden.
- V4-C recovery: disabled.
- Predictive recovery: disabled.
- Full100: not run.

Known targeted risk-window labels are retained for trials already identified by previous analyses:

- trial 14: steps 53-70
- trial 12: steps 96-167
- trial 13: steps 107-179
- trial 7: steps 121-131
- trial 9: steps 87-111

Other trials have `risk_window_flag=False` unless a future analysis adds explicit windows.

## Safety Guard And Fallback

- Keep all near candidates.
- Apply heading cap 16000 using `nearest_first`.
- Enable full-heading fallback on missing fields or guard violation.
- Enable DT verification guard.
- Stop expansion if a trial has collision, QP infeasibility, crash, or clear safety deterioration.
- Do not enable V4-C recovery.

## Metrics

The runner and analyzer report:

- all-steps metrics;
- risk-window metrics when risk-window rows are present;
- per-trial metrics;
- runtime mean / p95 / max;
- measured, heading, and final candidate counts;
- candidate count ratios;
- cap-applied count / fraction;
- fallback count and reasons;
- collision count;
- QP infeasible count;
- min safety h and capped-minus-fixed delta;
- H1/H2/H3 margin violation counts and deltas;
- DT-warning and low-margin counts and deltas;
- progress mean and delta;
- recovery used count.

## Pass / Fail Criteria

Pass requires:

- no crash;
- no collision;
- no QP infeasible result;
- no min-h degradation beyond tolerance;
- no H1/H2/H3 violation increase;
- no DT-warning or low-margin increase;
- candidate-count reduction;
- non-excessive fallback;
- no material progress degradation.

Fail / freeze conditions:

- any collision;
- any QP infeasible result;
- any crash;
- H-step margin deltas worsen;
- min safety h worsens beyond tolerance;
- final candidate count is not reduced;
- fallback effectively disables the cap;
- progress materially degrades.

## Reporting Constraints

FC-Aware V1 remains a candidate-selection / efficiency support module. It does not replace Start-Safe CBF, DT Verification, CBF-QP filtering, or optional Predictive Recovery. `min_safety_h` is repository GSplat ellipsoid h, not meter clearance. Margin violation is not collision. No official core source is modified.
