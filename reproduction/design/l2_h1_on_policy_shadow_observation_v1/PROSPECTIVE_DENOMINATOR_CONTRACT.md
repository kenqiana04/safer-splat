# Prospective Denominator Contract

All counters begin at zero before the frozen manifest is executed and are updated for every intended control step, including incomplete observations.

| Counter | Definition |
|---|---|
| `N_control_steps_all` | All frozen-controller control decisions in the pre-registered manifest. |
| `N_L0_reached/pass/repair/fail` | Explicit worker-runtime L0 progression and outcomes. |
| `N_L1_reached/PASS/FAIL/UNKNOWN` | Explicit worker-runtime immediate-segment progression and outcomes. |
| `N_L2_reached_selected` | Committed selected candidates for which frozen prerequisites reached L2. |
| `N_L2_selected_evaluated` | Reached selected candidates with a completed formal tri-state L2 result. |
| `N_L2_selected_PASS/FAIL/UNKNOWN` | Mutually exclusive partition of the evaluated selected denominator. |
| `N_native_candidates_total/evaluated` | All native pre-observation candidates and completed shadow results. |
| `N_multi_candidate_groups` | Steps with more than one native candidate. |
| `N_multi_candidate_groups_all_evaluated` | Groups in which every native candidate received a result. |
| `N_multi_candidate_groups_status_disagreement` | Groups with at least two distinct tri-state statuses. |
| `N_multi_candidate_groups_PASS_AND_FAIL` | Groups containing both PASS and FAIL. |
| `N_observation_dropped` | Intended payloads not enqueued or evaluated due to instrumentation. |
| `N_logging_error` | Required payload/serialization/alignment failures. |
| `N_shadow_worker_error` | Worker health failures, never L2 UNKNOWN. |

Rates:

- `primary_future_fail_signal_rate = N_L2_selected_FAIL / N_L2_selected_evaluated`;
- `primary_future_unknown_rate = N_L2_selected_UNKNOWN / N_L2_selected_evaluated`;
- `L2_reach_rate = N_L2_reached_selected / N_control_steps_all`;
- `logging_completeness = N_complete_required_payload_steps / N_control_steps_all`.

Every table must print numerator, denominator, and undefined status when denominator is zero. `L2_UNKNOWN`, `L2_NOT_REACHED`, `OBSERVATION_INCOMPLETE`, and `SHADOW_EVALUATION_DROPPED` are never pooled.

**Scope:** DESIGN ONLY | NO ON-POLICY COLLECTION | NO CONTROLLER AUTHORITY | NO DECISION FEEDBACK | NO PERFORMANCE CLAIM.
