# FC-Aware V1 Per-Candidate Recall Audit Design

## 1. Purpose

This task fills the evidence gap left by the aggregate FC-Aware heading shadow audit: per-candidate IDs and active/risk recall are needed before any heading cap can be considered for wrapper-level closed-loop smoke.

This phase is logging / reconstruction / recall audit only. It is not closed-loop validation and not full100.

## 2. Motivation

Aggregate shadow accounting showed large theoretical candidate-count reduction potential under heading caps. However, every targeted risk-window row is affected by the cap, and existing step logs only expose aggregate source counts. Without per-candidate IDs, we cannot know whether heading top-M would remove active, low-h, near-boundary, or QP-critical candidates.

Therefore, the next required evidence is per-candidate trace logging or offline reconstruction.

## 3. Candidate Trace Fields

Each traced step should record:

- trial_id
- step_id
- dataset
- mode
- risk_window_flag
- dt_warning_flag
- low_margin_flag
- selected_K
- final_candidate_ids
- near_candidate_ids
- heading_candidate_ids
- history_candidate_ids
- optional_risk_ranked_candidate_ids
- active_constraint_ids, if exact IDs are available
- low_h_candidate_ids, if exact IDs are available
- candidate_h_values, if available
- heading_distance_values, if available
- heading_cosine_values, if available
- candidate_scores, if available
- heading_scores, if computed
- heading_rank_order, if ranking data are stored
- final_union_count
- heading_count
- active_count
- low_h_count
- missing_field_flags

The current implementation prioritizes offline reconstruction of source IDs from saved step states. It does not change the controller.

## 4. Recall Definitions

- active_recall_at_M = retained_active_heading_ids / all_active_heading_ids
- low_h_recall_at_M = retained_low_h_heading_ids / all_low_h_heading_ids
- final_recall_at_M = retained_final_heading_ids / all_heading_ids
- risk_recall_at_M = retained_risk_heading_ids / all_risk_heading_ids
- sector_coverage_at_M = retained heading angular sectors / original heading angular sectors, if sectors are available

If active IDs or low-h IDs are unavailable, recall is reported as unavailable and no closed-loop recommendation is allowed.

## 5. Heading Ranking Strategies

Strategies to audit:

- original_order
- nearest_first, if distance is available
- heading_alignment_first, if cosine is available
- low_h_first, if h values are available
- active_history_first, if active history is available
- hybrid_score, if multiple fields are available

If a ranking input is missing, the audit reports the strategy as unavailable rather than inventing recall.

## 6. Cap List

Required heading caps:

- 2000
- 4000
- 8000
- 12000
- 16000

## 7. Decision Criteria

- If risk-window active_recall_at_8000 >= 0.99 and low_h_recall_at_8000 >= 0.99, wrapper-level closed-loop smoke can be considered.
- If recall data are unavailable, do not proceed to closed-loop.
- If recall is clearly insufficient, freeze FC-Aware V1 or redesign ranking.
- If heading cap reduction is large but recall is poor, do not proceed to closed-loop.
- If only cap 16000 preserves recall, continue only if the remaining reduction is still meaningful.

## 8. Safety Boundary

FC-Aware V1 remains a candidate selection / efficiency support module. It does not provide a standalone safety guarantee, does not replace Start-Safe CBF, does not replace DT Verification, does not replace CBF-QP filtering, and does not replace optional Predictive Recovery.
