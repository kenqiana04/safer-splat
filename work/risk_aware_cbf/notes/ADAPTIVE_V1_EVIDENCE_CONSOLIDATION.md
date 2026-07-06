# Adaptive V1 Evidence Consolidation

## 1. Purpose

This file freezes the Adaptive V1 evidence chain for paper-material organization. It is not a new experiment, not a full100 benchmark, and not a new method claim.

Adaptive V1 is treated as a candidate-budgeting / risk-response support module and ablation inside the broader FAS-CBF paper narrative.

## 2. Chronology

1. Initial adaptive design: Adaptive V1 was introduced to schedule the V1 candidate budget from DT-warning and margin signals.
2. Conservative offline replay: confirmed risk-responsive scheduling but overused high-budget fallback; offline replay could not prove closed-loop runtime benefit.
3. Balanced offline replay: reduced over-fallback relative to conservative while preserving risk response; still an offline audit.
4. Closed-loop smoke: confirmed `selected_K` was applied to the V1 budgeting wrapper in true closed-loop navigation.
5. Flight20 closed-loop: tested fixed vs adaptive_balanced on trials 0-19 with recovery disabled.
6. Targeted DT-risk closed-loop: focused on trials 13, 12, 14, 7, and 9, starting from trial starts and using target windows only for analysis.
7. Forced-candidate dominance diagnostic: explained why final candidate count did not follow `selected_K`.

## 3. What Adaptive V1 Proved

Adaptive V1 proved risk-response integration:

- `selected_K_applied_rate = 1.0` in the closed-loop pilots.
- `selected_K` was passed into the V1 selector as candidate budget.
- DT-warning and low-margin windows received larger scheduled budgets.
- Targeted DT-risk risk-window selected_K ratio balanced/fixed was `2.884422`.
- Flight20 and targeted pilots had no collision, no QP infeasibility, and no crash in the tested scopes.
- V4-C recovery was disabled and `recovery_used_count = 0`.
- Reported safety metrics did not degrade relative to fixed V1 in the tested pilots.

## 4. What Adaptive V1 Did Not Prove

Adaptive V1 did not prove:

- candidate-count reduction,
- runtime improvement,
- an independent safety guarantee,
- a new CBF theorem,
- full100 benchmark performance,
- final candidate-count control.

The targeted DT-risk risk-window measured candidate-count ratio balanced/fixed was `0.999773`, despite the selected budget increasing strongly. This blocks any candidate-count reduction claim.

## 5. Forced-Candidate Dominance Explanation

The V1 selector first unions forced near, forced heading, and forced history candidates. Only after this forced union does it use the remaining `candidate_budget` for optional risk-ranked fill.

The diagnostic found:

- targeted risk-window `forced_candidate_fraction_mean = 1.0`,
- targeted risk-window `budget_limited_candidate_count_mean = 0.0`,
- targeted risk-window heading fraction of final candidates = `0.990847`,
- heading candidates dominate final candidate count,
- `selected_K` controls only the optional risk-ranked remainder after forced union,
- final union has no post-cap.

Therefore, `selected_K_applied=True` means the scheduled budget reached the V1 wrapper, but it does not imply final candidate-count reduction.

## 6. Final Decision

- Continue Adaptive V1 as support / ablation: yes.
- Use Adaptive V1 as paper main safety method: no.
- Claim runtime improvement: no.
- Claim candidate-count reduction: no.
- Run full100 now: no.
- FC-aware budgeting: future work or separate design only.

