# Forced-Candidate Dominance Decision

## 1. Does forced candidate dominance hold?

Yes. In both flight20 and targeted DT-risk closed-loop logs, adaptive-balanced `forced_candidate_fraction_mean` is `1.0` in the relevant scopes. The final unique candidate count is equal to the forced unique candidate count, and `budget_limited_candidate_count_mean` is `0.0`.

## 2. Are heading candidates the main cause?

Yes. Heading candidates dominate final candidate count:

- targeted risk-window heading fraction of final: `0.990847`
- targeted all-step heading fraction of final: `0.996936`
- flight20 all-step heading fraction of final: `0.998618`

Near and history candidates are much smaller than heading candidates in the same scopes.

## 3. What does selected_K currently control?

`selected_K` is passed to `selector.candidate_budget`. It controls the optional risk-ranked remainder after forced near, heading, and history candidates are unioned. The adaptive runner also updates the history support size from `selected_K`.

`selected_K` is not a post-union cap on final unique candidates.

## 4. Why does selected_K not reduce final candidate count?

The selector first adds forced candidates. If the forced union already exceeds `candidate_budget`, the risk-ranked optional pool receives no remaining budget. There is no final cap after this union. Therefore final candidate count can remain near 24k even when `selected_K` is 1000, 2000, 4000, or 8000.

## 5. Why is budget_limited_candidate_count zero?

`budget_limited_candidate_count` records the optional risk-ranked fill count. It stays zero because forced candidates already exceed the scheduled budget, so the `forced_count < candidate_budget` branch does not add risk-ranked candidates.

## 6. Is there evidence for runtime or candidate-count improvement?

No. Targeted risk windows show strong budget response but no candidate-count reduction:

- selected_K ratio balanced/fixed: `2.884422`
- measured candidate-count ratio balanced/fixed: `0.999773`
- runtime ratio balanced/fixed: `0.985188`

The runtime ratio alone is not enough to claim runtime improvement because final candidate count is unchanged and this is a targeted diagnostic, not a benchmark.

## 7. Should Adaptive V1 continue?

Yes, but only as a candidate-budgeting / risk-response support module or ablation.

## 8. Recommend full100 now?

No. Full100 would not answer the current bottleneck. The current bottleneck is forced-candidate dominance, not insufficient trial count.

## 9. Recommend Adaptive V1 as the paper main method?

No. The main method should remain Certified Feasibility-Aware Start-Safe CBF + Discrete-Time Verification + optional Predictive Recovery.

Adaptive V1 can be used as support evidence that risk-aware scheduling is technically integrated and responds to DT-risk signals, with a clear limitation.

## 10. Recommend downgrade to support / ablation?

Yes. Adaptive V1 should be described as a support module or ablation, not as the main safety method and not as an efficiency-improvement contribution in its current form.

## 11. Recommend forced-candidate-aware design?

Yes. The appropriate next design direction is Adaptive V1-FC: forced-candidate-aware budgeting. It should explicitly account for near, heading, history, forced union, risk-ranked optional pool, and final unique count.

## 12. Recommend FC-aware closed-loop pilot now?

No, not immediately. The minimum next step is a wrapper-level design and offline sensitivity with conservative full-query fallback rules. A closed-loop smoke should only follow if the design does not remove plausibly safety-critical forced candidates without fallback.

## 13. Minimum next step

Design an FC-aware selector policy that keeps a mandatory safety core and adds adaptive auxiliary candidates, or a heading-prioritization policy with full-query fallback in low-margin, DT-warning, abnormal-candidate, and selector-uncertainty cases.

## 14. Recommended paper wording

- Adaptive V1 is a risk-aware candidate-budget scheduler integrated into the V1 pre-CBF wrapper.
- `selected_K` is applied to the V1 selector.
- Adaptive V1 increases scheduled budgets in DT-risk windows.
- Current V1 final candidate count is dominated by forced heading candidates.
- The current Adaptive V1 diagnostic does not support candidate-count or runtime improvement claims.
- Forced-candidate-aware budgeting is a limitation and future-work direction.

## 15. Forbidden paper wording

- Do not claim Adaptive V1 is an independent safety guarantee.
- Do not claim a new CBF theorem.
- Do not claim Adaptive V1 replaces Start-Safe CBF.
- Do not claim Adaptive V1 replaces Discrete-Time Verification.
- Do not claim Adaptive V1 replaces optional Predictive Recovery.
- Do not claim selected_K application implies final candidate-count reduction.
- Do not claim runtime improvement from this diagnostic.
- Do not call targeted DT-risk closed-loop a full100 benchmark.
- Do not call offline cap sensitivity a closed-loop result.
- Do not describe margin violation as collision.
- Do not describe `min_safety_h` as meter clearance.

## 16. commands.txt handling

`work/risk_aware_cbf/notes/commands.txt` is an internal task / command record. It should not be cited as paper material and should not be moved into `paper_materials`. It can be kept as an internal log. Do not delete it unless the owner confirms it is no longer useful. Do not clean its staged or untracked state with destructive git commands without explicit user instruction.

