# Adaptive V1 Final Positioning

## 1. Recommended Paper Role

Adaptive V1 should be described as a risk-responsive candidate-budgeting support module and optional ablation.

It is efficiency-motivated, but efficiency is not proven in the current implementation because final candidate sets are dominated by forced candidates, especially heading candidates.

## 2. Safe Claims

The paper can safely state:

- Adaptive V1 dynamically adjusts selected candidate budget from DT-warning and margin signals.
- In closed-loop pilots, `selected_K` was applied to the V1 budgeting wrapper.
- Adaptive V1 increased `selected_K` in DT-risk windows.
- Tested safety metrics did not degrade in the closed-loop pilots.
- Forced-candidate decomposition explains why `selected_K` did not reduce final candidate count.

## 3. Unsafe Claims

Do not claim:

- Adaptive V1 guarantees safety.
- Adaptive V1 improves runtime.
- Adaptive V1 reduces candidate count.
- Adaptive V1 is a main safety contribution.
- Adaptive V1 replaces Discrete-Time Verification.
- Adaptive V1 replaces Predictive Recovery.
- Adaptive V1 results are full100 benchmark results.
- `selected_K_applied` means final candidate count was reduced.

## 4. Recommended Wording

Possible paper text:

1. "We include an adaptive candidate-budgeting ablation to examine whether risk-responsive Gaussian budgeting can reduce dense CBF construction cost."
2. "The adaptive scheduler increases the selected budget in DT-warning and low-margin states, and the selected budget is passed into the V1 candidate wrapper in closed-loop pilots."
3. "However, candidate-source decomposition shows that final candidate sets are dominated by forced heading candidates, limiting candidate-count reduction in the current implementation."
4. "We therefore treat Adaptive V1 as a support/ablation module rather than a primary safety mechanism."
5. "This diagnostic motivates forced-candidate-aware budgeting as future work."

## 5. Future Work Wording

Forced-candidate-aware budgeting can be framed as future work:

- heading candidate prioritization,
- per-source budget accounting,
- post-union cap with full-query fallback,
- two-stage mandatory safety core plus adaptive auxiliary pool,
- DT Verification guarded candidate pruning.

