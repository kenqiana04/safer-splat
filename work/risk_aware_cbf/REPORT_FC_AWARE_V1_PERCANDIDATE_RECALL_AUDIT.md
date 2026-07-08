# FC-Aware V1 Per-Candidate Heading Recall Audit

## 1. Purpose

This report evaluates whether a heading top-M cap would preserve active / low-h / safety-critical candidates before any FC-aware wrapper-level closed-loop smoke.

This is not closed-loop validation, not full100, and not a runtime or safety guarantee.

## 2. Background

Selected_K-only Adaptive V1 is risk-responsive but does not reduce final candidate count because forced heading candidates dominate the final union.

The FC-Aware heading shadow audit showed large aggregate reduction headroom, but every targeted risk-window row was affected by heading caps and existing logs lacked per-candidate IDs. This audit addresses the next evidence gap by reconstructing per-candidate source IDs offline.

## 3. Trace Logging / Reconstruction

Trace output:

- `work/risk_aware_cbf/results/fc_aware_v1_percandidate_recall_audit/candidate_trace_steps.jsonl`
- `work/risk_aware_cbf/results/fc_aware_v1_percandidate_recall_audit/candidate_trace_summary.csv`
- `work/risk_aware_cbf/results/fc_aware_v1_percandidate_recall_audit/candidate_trace_metrics.json`

Trace mode: `offline_reconstruction`.

The reconstruction uses saved step states and the V1 selector source-mask formulas to reconstruct:

- final candidate IDs,
- near candidate IDs,
- heading candidate IDs,
- history candidate IDs,
- optional risk-ranked candidate IDs.

Trace summary:

| field | value |
|---|---:|
| step_count | 1350 |
| written_step_count | 1350 |
| dataset_count | 2 |
| candidate_ids_exact | true |
| active_ids_exact | false |
| low_h_ids_exact | false |

Active constraint IDs and low-h candidate IDs are not exact because the saved logs do not contain per-candidate active IDs or per-candidate h values. The run did not alter controller behavior.

## 4. Recall Definitions

- active_recall_at_M = retained_active_heading_ids / all_active_heading_ids
- low_h_recall_at_M = retained_low_h_heading_ids / all_low_h_heading_ids
- final_recall_at_M = retained_final_heading_ids / all_heading_ids
- risk_recall_at_M = retained_risk_heading_ids / all_risk_heading_ids

Because active IDs and low-h IDs are unavailable, active and low-h recall are reported as unavailable.

## 5. Ranking Strategies

Requested strategies:

- original_order
- nearest_first
- heading_alignment_first
- low_h_first
- active_history_first
- hybrid_score

The current trace stores exact source ID lists but not per-heading distances, cosine values, per-candidate h values, or active-history labels. Therefore no ranking strategy can be recommended based on recall. Reduction accounting is identical across strategies when recall data are unavailable.

## 6. Results By Cap

Targeted risk-window results using reconstructed source IDs:

| heading_cap | heading_count_mean | hypothetical_final_count_mean | reduction_ratio_mean | active_recall_mean | low_h_recall_mean | affected_steps_fraction | recall_available |
|---:|---:|---:|---:|---:|---:|---:|---|
| 2000 | 24669.55 | 2231.24 | 0.909873 | NA | NA | 1.0 | false |
| 4000 | 24669.55 | 4231.24 | 0.828874 | NA | NA | 1.0 | false |
| 8000 | 24669.55 | 8231.24 | 0.666876 | NA | NA | 1.0 | false |
| 12000 | 24669.55 | 12231.24 | 0.504877 | NA | NA | 1.0 | false |
| 16000 | 24669.55 | 16231.24 | 0.342879 | NA | NA | 1.0 | false |

The accounting reduction remains large. However, active and low-h recall cannot be evaluated.

## 7. Risk-Window Results

Risk-window rows remain the key blocker:

- risk-window affected fraction is `1.0` for all tested caps,
- active recall is unavailable,
- low-h recall is unavailable,
- recall_below_99_count is unavailable,
- recall_below_95_count is unavailable.

Therefore there is no cap that can be called safe or recall-preserving from the current evidence.

## 8. Decision

| question | decision |
|---|---|
| Continue FC-Aware V1? | Yes, logging/design only |
| Recommend closed-loop smoke? | No |
| Recommend full100 now? | No |
| Need more logging? | Yes |
| Best cap / ranking? | None defensible because recall is unavailable |

Accounting max reduction is at cap 2000, but this is not a recommended cap because active / low-h recall is unavailable.

Minimum next evidence before closed-loop:

- exact active constraint IDs,
- per-candidate h or low-h IDs,
- heading distance / cosine fields for ranking,
- retained top-M heading IDs by strategy,
- recall audit showing high risk-window recall.

## 9. Limitations

- Recall audit is not closed-loop.
- No runtime evidence is produced.
- No safety guarantee is claimed.
- Candidate source IDs are reconstructed offline.
- Active IDs are not exact.
- Low-h IDs are not exact.
- No official core source was modified.
- `h` / `min_safety_h` is not metric clearance.
- Margin violation is not collision.
