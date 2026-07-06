# Adaptive V1 Forced-Candidate Positioning Update

## Paper Positioning After Forced-Candidate Diagnostic

Adaptive V1 should remain a method-support or ablation component. It demonstrates that a risk-aware scheduler can be integrated into the V1 pre-CBF candidate wrapper and can respond to DT-risk signals, but the current implementation does not provide candidate-count or runtime improvement evidence.

The main paper method should remain Certified Feasibility-Aware Start-Safe CBF + Discrete-Time Verification + optional Predictive Recovery.

## Safe To Include

- Adaptive V1 is a risk-aware candidate-budget scheduler.
- `selected_K` is applied to the V1 candidate selector.
- DT-risk and low-margin scopes receive higher scheduled budgets.
- Closed-loop smoke, flight20, and targeted DT-risk pilots did not show collision / QP / crash degradation in the reported scopes.
- Final candidate count is dominated by forced candidates in the current V1 wrapper.
- Heading candidates are the dominant forced source.
- `budget_limited_candidate_count_mean = 0.0` in the relevant scopes.
- The current result supports risk-response integration, not efficiency improvement.

## Still Not Safe To Claim

- Do not claim Adaptive V1 is a new CBF theorem.
- Do not claim Adaptive V1 independently guarantees safety.
- Do not claim Adaptive V1 replaces Start-Safe CBF.
- Do not claim Adaptive V1 replaces Discrete-Time Verification.
- Do not claim Adaptive V1 replaces optional Predictive Recovery.
- Do not claim candidate-count reduction.
- Do not claim runtime improvement.
- Do not describe targeted DT-risk closed-loop as a full100 benchmark.
- Do not describe offline cap sensitivity as closed-loop evidence.
- Do not call margin violations collisions.
- Do not describe `min_safety_h` as meter clearance.

## How To Explain selected_K Applied But Candidate Count Not Reduced

The scheduler's `selected_K` is passed into the V1 selector as `candidate_budget`. The selector first unions forced near, forced heading, and forced history candidates. Only if that forced union is smaller than `candidate_budget` does the selector add optional risk-ranked candidates. There is no post-union cap on final unique candidates. In flight20 and targeted DT-risk logs, the forced union already exceeds `selected_K`, and heading candidates dominate that union. Therefore `selected_K` can be applied correctly while final candidate count remains nearly unchanged.

## Method Support Description

Adaptive V1 can be described as:

> a risk-responsive candidate-budgeting support module whose current wrapper-level implementation is limited by forced-candidate dominance, especially heading-cone candidates.

This wording keeps the module useful without overstating it.

## Ablation Description

Adaptive V1 is suitable as an ablation that asks whether scheduled candidate budgets respond to DT-risk signals and whether this response changes closed-loop behavior. The current answer is:

- risk response: yes
- safety degradation in reported pilot scopes: no
- candidate-count improvement: no evidence
- runtime improvement: no evidence

## Future Work: Adaptive V1-FC

Forced-candidate-aware budgeting can be introduced as future work:

- separate mandatory safety-core candidates from auxiliary candidates
- account for near, heading, history, forced union, risk-ranked pool, and final unique count
- add heading-candidate prioritization only with conservative full-query fallback
- trigger fallback on low margin, DT warning, abnormal candidate counts, selector uncertainty, or unresolved risk
- validate with closed-loop smoke and DT Verification before any benchmark claim

## If Adaptive V1 Is Not Advanced Further

Describe it as a support study that revealed an important systems limitation: risk-responsive budget scheduling alone is insufficient when the downstream candidate selector admits a large forced heading set without a final cap. This limitation motivates forced-candidate-aware selector design but does not weaken the main Start-Safe CBF + DT Verification safety narrative.

