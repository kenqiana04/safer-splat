# Prospective Analysis Plan

## Primary endpoint

The single primary endpoint is selected/executed-candidate `PROSPECTIVE_L1_PASS_L2_FAIL` prevalence among `N_L2_selected_evaluated`, with stored runtime shadow L1 PASS and explicit L2 reach.

## Secondary endpoints

1. selected-candidate L2 UNKNOWN prevalence;
2. L2 selected reach rate over all control steps;
3. required-payload logging completeness and instrumentation-error composition;
4. native multi-candidate-group prevalence;
5. multi-candidate certificate disagreement and PASS+FAIL prevalence;
6. selected versus non-selected native-candidate L2 status, without causal comparison;
7. exact/conservative/other frozen backend use and source/trial heterogeneity.

Candidate-step point estimates retain exact numerator/denominator. Uncertainty uses trial-cluster bootstrap with trial as the resampling unit and a pre-frozen seed/replicate count, plus trial-level prevalence summaries. Step-level iid Wilson intervals are not the primary uncertainty calculation. No p-value is required to call the result a mechanism signal.

All analysis includes outcome-independent retained steps, explicit missingness tables, environment/trial cluster IDs, and separate pilot/formal labels. Phase 1 and Phase 2 are excluded from the formal cohort unless a protocol frozen before either phase explicitly permits inclusion under zero modifications; the default is exclusion.

Multi-candidate questions are prevalence, endpoint diversity, certificate disagreement, and selected-vs-nonselected status. They are certificate discrimination opportunity, not alternative-search efficacy.

No result-dependent trial extension, early stop on FAIL count, high-risk-only retention, margin filtering, collision-only retention, or post-hoc cohort construction is permitted.

**Scope:** DESIGN ONLY | NO ON-POLICY COLLECTION | NO CONTROLLER AUTHORITY | NO DECISION FEEDBACK | NO PERFORMANCE CLAIM.
