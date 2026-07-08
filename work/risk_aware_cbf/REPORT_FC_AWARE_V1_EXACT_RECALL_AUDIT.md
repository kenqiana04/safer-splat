# FC-Aware V1 Exact Active/Low-H Recall Audit

## 1. Purpose

This report evaluates whether heading caps and ranking strategies can retain exact dual-active, tight, and low-h candidates in targeted risk windows. It is a no-intervention replay audit only.

## 2. Background

Adaptive V1 selected_K scheduling improved risk response but did not show candidate-count or runtime reduction because forced heading candidates dominate the final union. The heading shadow audit identified reduction headroom, and the exact logging feasibility probe confirmed exact replay logging for candidate IDs, h values, low-h IDs, and Clarabel dual-active IDs.

## 3. Audit Setup

- Target rows: 199
- Target windows: trial 13 steps 107-179; trial 12 steps 96-167; trial 14 steps 53-70; trial 7 steps 121-131; trial 9 steps 87-111.
- Caps: 2000, 4000, 8000, 12000, 16000.
- Deployable rankings: original_order, nearest_first, heading_alignment_first, distance_alignment_hybrid, previous_active_history_first.
- Oracle rankings: low_h_first, active_first, tight_first, low_h_active_hybrid.
- Low-h thresholds: 0.01, 0.001, 0.0005.
- Dual-active definition: Clarabel dual z > 1e-7 mapped to global Gaussian IDs.
- Tight definition: abs(l - A @ u) <= 1e-7 mapped to global Gaussian IDs.
- No capped closed-loop, no full100, and no V4-C recovery were run.

## 4. Exact Sets and Metrics

The hypothetical capped final set is non-heading final candidates union retained heading top-M. Recall is measured for dual-active, tight, low-h, and their combined risk set. Empty target sets are treated as recall 1.0 and reported with their counts.

## 5. Results: Deployable Rankings

| cap | ranking_strategy | reduction_ratio_mean | dual_active_recall_min | tight_recall_min | low_h_recall_min | combined_risk_recall_min | dropped_dual_active_total | dropped_tight_total | dropped_low_h_total |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| 16000 | nearest_first | 0.342879 | 1 | 1 | 1 | 1 | 0 | 0 | 0 |
| 12000 | nearest_first | 0.504877 | 1 | 1 | 0.999694 | 0.999694 | 0 | 0 | 4 |
| 8000 | nearest_first | 0.666876 | 1 | 1 | 0.984589 | 0.984589 | 0 | 0 | 828 |
| 16000 | distance_alignment_hybrid | 0.342879 | 0.666667 | 0.5 | 0.83294 | 0.83294 | 2 | 2 | 24194 |
| 12000 | distance_alignment_hybrid | 0.504877 | 0.5 | 0.5 | 0.733917 | 0.733917 | 5 | 5 | 69333 |
| 8000 | distance_alignment_hybrid | 0.666876 | 0.5 | 0.5 | 0.630246 | 0.630246 | 8 | 8 | 144751 |
| 16000 | original_order | 0.342879 | 0 | 0 | 0.538482 | 0.538482 | 124 | 100 | 224621 |
| 16000 | previous_active_history_first | 0.342879 | 0 | 0 | 0.528937 | 0.528937 | 204 | 170 | 221486 |
| 4000 | nearest_first | 0.828874 | 1 | 1 | 0.493281 | 0.493281 | 0 | 0 | 59413 |
| 4000 | distance_alignment_hybrid | 0.828874 | 0.5 | 0.5 | 0.442475 | 0.442475 | 16 | 14 | 265761 |
| 12000 | original_order | 0.504877 | 0 | 0 | 0.411277 | 0.411277 | 235 | 192 | 332346 |
| 12000 | previous_active_history_first | 0.504877 | 0 | 0 | 0.384808 | 0.384808 | 221 | 182 | 337271 |
| 16000 | heading_alignment_first | 0.342879 | 0 | 0 | 0.324121 | 0.324121 | 61 | 46 | 260263 |
| 8000 | previous_active_history_first | 0.666876 | 0 | 0 | 0.276572 | 0.276572 | 278 | 239 | 464124 |
| 8000 | original_order | 0.666876 | 0 | 0 | 0.272582 | 0.272582 | 329 | 269 | 446197 |
| 12000 | heading_alignment_first | 0.504877 | 0 | 0 | 0.247522 | 0.247522 | 106 | 82 | 333439 |
| 2000 | distance_alignment_hybrid | 0.909873 | 0 | 0 | 0.246702 | 0.246702 | 44 | 31 | 420535 |
| 2000 | nearest_first | 0.909873 | 0 | 0 | 0.246702 | 0.246702 | 9 | 8 | 313253 |
| 8000 | heading_alignment_first | 0.666876 | 0 | 0 | 0.211648 | 0.211648 | 153 | 121 | 398357 |
| 4000 | previous_active_history_first | 0.828874 | 0 | 0 | 0.124958 | 0.124958 | 409 | 348 | 592697 |
| 4000 | original_order | 0.828874 | 0 | 0 | 0.106937 | 0.106937 | 399 | 336 | 580035 |
| 4000 | heading_alignment_first | 0.828874 | 0 | 0 | 0.095315 | 0.095315 | 179 | 143 | 476048 |
| 2000 | previous_active_history_first | 0.909873 | 0 | 0 | 0.0647078 | 0.0647078 | 429 | 363 | 648741 |
| 2000 | original_order | 0.909873 | 0 | 0 | 0.0428249 | 0.0428249 | 441 | 371 | 646905 |
| 2000 | heading_alignment_first | 0.909873 | 0 | 0 | 0.028436 | 0.028436 | 228 | 181 | 578993 |

## 6. Results: Oracle Rankings

| cap | ranking_strategy | reduction_ratio_mean | dual_active_recall_min | tight_recall_min | low_h_recall_min | combined_risk_recall_min | dropped_dual_active_total | dropped_tight_total | dropped_low_h_total |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| 12000 | low_h_active_hybrid | 0.504877 | 1 | 1 | 1 | 1 | 0 | 0 | 0 |
| 12000 | low_h_first | 0.504877 | 1 | 1 | 1 | 1 | 0 | 0 | 0 |
| 16000 | active_first | 0.342879 | 1 | 1 | 1 | 1 | 0 | 0 | 0 |
| 16000 | low_h_active_hybrid | 0.342879 | 1 | 1 | 1 | 1 | 0 | 0 | 0 |
| 16000 | low_h_first | 0.342879 | 1 | 1 | 1 | 1 | 0 | 0 | 0 |
| 16000 | tight_first | 0.342879 | 1 | 1 | 1 | 1 | 0 | 0 | 0 |
| 12000 | active_first | 0.504877 | 1 | 1 | 0.999694 | 0.999694 | 0 | 0 | 4 |
| 12000 | tight_first | 0.504877 | 1 | 1 | 0.999694 | 0.999694 | 0 | 0 | 4 |
| 8000 | low_h_active_hybrid | 0.666876 | 1 | 1 | 0.986438 | 0.986438 | 0 | 0 | 434 |
| 8000 | low_h_first | 0.666876 | 1 | 1 | 0.986438 | 0.986438 | 0 | 0 | 432 |
| 8000 | active_first | 0.666876 | 1 | 1 | 0.984589 | 0.984589 | 0 | 0 | 828 |
| 8000 | tight_first | 0.666876 | 1 | 1 | 0.984589 | 0.984589 | 0 | 0 | 828 |
| 4000 | active_first | 0.828874 | 1 | 1 | 0.493281 | 0.493281 | 0 | 0 | 59413 |
| 4000 | low_h_active_hybrid | 0.828874 | 1 | 1 | 0.493281 | 0.493281 | 0 | 0 | 57468 |
| 4000 | low_h_first | 0.828874 | 1 | 1 | 0.493281 | 0.493281 | 0 | 0 | 57419 |
| 4000 | tight_first | 0.828874 | 1 | 1 | 0.493281 | 0.493281 | 0 | 0 | 59413 |
| 2000 | active_first | 0.909873 | 1 | 1 | 0.246702 | 0.246702 | 0 | 0 | 313253 |
| 2000 | low_h_active_hybrid | 0.909873 | 1 | 1 | 0.246702 | 0.246702 | 0 | 0 | 312722 |
| 2000 | low_h_first | 0.909873 | 0 | 0 | 0.246702 | 0.246702 | 9 | 8 | 312716 |
| 2000 | tight_first | 0.909873 | 0.666667 | 1 | 0.246702 | 0.246702 | 1 | 0 | 313253 |

## 7. Decision

- Recommended action: `RECOMMEND_WRAPPER_LEVEL_CAPPED_CLOSED_LOOP_SMOKE_ONLY`
- Reason: a deployable ranking met the recall thresholds with meaningful reduction on the recall audit
- Best deployable: `nearest_first` at cap `16000`.
- Best oracle: `low_h_active_hybrid` at cap `12000`.
- Full100 is not recommended from recall audit alone.

## 8. Runtime / Logging Overhead

Reported runtimes are logging/replay overhead for this audit, not a runtime-improvement claim for FC-Aware V1.

## 9. Limitations

- Exact recall audit is not closed-loop validation.
- FC-Aware V1 is a candidate selection / efficiency support module, not a safety guarantee.
- Dual-active depends on solver tolerance and should not be described as a theorem-level active set.
- h / min_safety_h is the repository GSplat safety value, not meter clearance.
- Margin violation is not collision.
- Oracle rankings are diagnostic upper bounds and are not directly deployable.
