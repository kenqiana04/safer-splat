# FC-Aware V1 Exact Recall Audit Design

## Purpose

This audit evaluates whether hypothetical heading-candidate caps can preserve exact dual-active, tight, and low-h Gaussian IDs on targeted Adaptive V1 risk-window rows. It is a logging and recall audit only. It is not a capped closed-loop run, not a full100 benchmark, and not a safety guarantee.

## Motivation

Previous FC-Aware V1 work established that selected_K scheduling changes the candidate budget but does not reduce total candidate count because forced heading candidates dominate the final candidate union. The heading shadow audit showed large theoretical reduction headroom from capping heading candidates, but could not evaluate risk recall without per-candidate exact IDs. The exact logging feasibility probe then confirmed that wrapper-only no-intervention replay can capture exact final candidate IDs, heading distance/cosine, candidate h values, low-h IDs, Clarabel dual-active IDs, and tight IDs for replayed steps. This audit uses that exact logging path over targeted risk windows before any closed-loop cap is considered.

## Exact Sets

- `heading set`: global Gaussian IDs selected by the existing heading-candidate rule in the unmodified V1 selector.
- `retained heading top-M set`: the top M heading IDs under a proposed ranking strategy and cap.
- `dual-active set`: global Gaussian IDs whose replayed Clarabel dual variable satisfies `z > 1e-7`.
- `tight set`: global Gaussian IDs whose replayed QP constraint residual satisfies `abs(l - A @ u) <= 1e-7`.
- `low-h set`: final candidate global Gaussian IDs with repository GSplat safety value `h <= threshold`.
- `combined risk set`: union of dual-active, tight, and low-h sets for a given threshold.

The hypothetical capped final set is `non-heading final candidates union retained heading top-M`. It is computed offline from exact replay logs and does not alter controller output or the saved trajectory.

## Recall Metrics

- `dual_active_recall_at_M = retained_dual_active_count / dual_active_count`, with empty sets treated as 1.0.
- `tight_recall_at_M = retained_tight_count / tight_count`, with empty sets treated as 1.0.
- `low_h_recall_at_M = retained_low_h_count / low_h_count`, with empty sets treated as 1.0.
- `combined_risk_recall_at_M = retained_combined_risk_count / combined_risk_count`, with empty sets treated as 1.0.
- Dropped counts are reported separately for dual-active, tight, low-h, and combined risk IDs.
- Recall-below counts are evaluated for 100%, 99%, and 95% combined-risk recall.

## Reduction Metrics

- `original_final_count`: size of the original unmodified final candidate set.
- `hypothetical_final_count`: size of the offline capped final set.
- `reduction_ratio = 1 - hypothetical_final_count / original_final_count`.
- `affected_steps_fraction`: fraction of audited steps where `heading_count > cap`.

## Ranking Groups

Deployable or pre-QP rankings:

- `original_order`
- `nearest_first`
- `heading_alignment_first`
- `distance_alignment_hybrid`
- `previous_active_history_first`

Diagnostic or oracle upper-bound rankings:

- `low_h_first`
- `active_first`
- `tight_first`
- `low_h_active_hybrid`

Oracle rankings use replay-only information and must not be described as directly deployable unless a future pre-selection design can obtain equivalent signals before candidate selection.

## Decision Thresholds

Wrapper-level capped closed-loop smoke is only considered if a deployable ranking over the targeted risk windows has:

- dual-active recall minimum at least 0.99,
- tight recall minimum at least 0.99,
- low-h recall minimum at least 0.99,
- preferably zero dropped dual-active and tight IDs,
- meaningful mean reduction ratio.

If only oracle rankings satisfy recall, the next step is better deployable score design, not closed-loop. If recall remains poor even at high caps, FC-Aware V1 should remain diagnostic or future work. This audit alone never justifies full100.
