# Sample Size and Stopping Rule

PR #95 supplies planning priors, not a transportability claim. The historical selected/executed rate is `6/566 = 1.0601%`; the broader L1 PASS/L2 FAIL rate is `18/788 = 2.2843%`. Both are biased by source selection and missing payloads. Under an iid calculation used only for scale intuition, a 1.0601% event rate gives 282 evaluated candidates for a 95% chance of at least one event and 217 for 90% (ceiling of the exact logarithmic calculation). These are not power guarantees because steps cluster within trials.

## Plan A — selected primary plan: fixed trial manifest

Freeze the mature Stonehenge `run.py` baseline's complete 100 deterministic indexed trials, starts/goals, order, `dt=0.05`, 500-step cap, termination rules, controller config, static map content identity, and no-random-sampling seed policy before results. Observe every accepted step. Stop only when every frozen trial is terminal. Do not stop based on L2 FAIL/UNKNOWN or any interim rate.

This plan is selected because it preserves the existing on-policy distribution, gives trial clusters a defensible meaning, and avoids treating correlated steps as a sample-size counter. PR #89 E5's 100 locked one-step states provide provenance context but do not replace the rollout manifest.

## Plan B — fallback: fixed reached-selected target plus trial cap

Pre-register `N_L2_selected_evaluated = 566` as a planning-scale target, together with the same fixed ordered Stonehenge trial manifest and a 100-trial/500-step cap. Stop only after the current trial finishes once the target is met, or after the fixed trial cap. Never stop by the number or pattern of FAIL results. Report the achieved trial count and cluster distribution.

Plan B may be chosen only before collection if Phase 2 shows Plan A is infeasible for instrumentation/logging reasons without changing the scientific controller. It cannot be selected after inspecting L2 outcomes.

## Uncertainty

The final point estimate is candidate-step prevalence. Primary uncertainty is a cluster-aware bootstrap over complete trials or trial-level aggregation, with algorithm, seed, and replicate count frozen in the Phase 3 analysis manifest. The planning iid calculation is not reused as inferential evidence.

**Scope:** DESIGN ONLY | NO ON-POLICY COLLECTION | NO CONTROLLER AUTHORITY | NO DECISION FEEDBACK | NO PERFORMANCE CLAIM.
