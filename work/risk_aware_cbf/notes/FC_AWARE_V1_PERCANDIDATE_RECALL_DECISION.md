# FC-Aware V1 Per-Candidate Recall Decision

## Status

Per-candidate source logging / reconstruction completed.

| item | status |
|---|---|
| trace_mode | offline_reconstruction |
| step_count | 1350 |
| candidate IDs exact | yes |
| active IDs exact | no |
| low-h IDs exact | no |
| recall_available | false |
| closed-loop run | no |
| full100 run | no |

## Recall Audit Result

Because active constraint IDs and low-h candidate IDs are not available in saved logs, active recall and low-h recall cannot be computed.

No heading cap or ranking strategy can be recommended for closed-loop use.

## Accounting Result

Targeted risk-window accounting with reconstructed source IDs:

| heading_cap | reduction_ratio_mean | affected_steps_fraction | active_recall | low_h_recall |
|---:|---:|---:|---|---|
| 2000 | 0.909873 | 1.0 | unavailable | unavailable |
| 4000 | 0.828874 | 1.0 | unavailable | unavailable |
| 8000 | 0.666876 | 1.0 | unavailable | unavailable |
| 12000 | 0.504877 | 1.0 | unavailable | unavailable |
| 16000 | 0.342879 | 1.0 | unavailable | unavailable |

The accounting headroom is real, but recall evidence is still missing.

## Decision

| question | answer |
|---|---|
| Continue FC-Aware V1? | Yes, logging/design follow-up only |
| Recommend wrapper-level closed-loop smoke? | No |
| Recommend full100 now? | No |
| Need more logging? | Yes |
| Best ranking strategy? | None defensible |
| Best heading cap? | None defensible |
| Paper role | Future work / support diagnostic |

## Required Additional Logging

Before any closed-loop smoke:

1. log exact active gaussian IDs from QP construction,
2. log per-candidate h values or low-h candidate IDs,
3. log heading distance and heading cosine for heading candidates,
4. log retained top-M heading IDs for each ranking,
5. compute risk-window active and low-h recall,
6. require full heading fallback and full-query fallback.

## Necessary Safety Guards

- keep all near candidates,
- full heading fallback,
- DT Verification guard,
- full-query fallback,
- rollback if min_safety_h or H-step margin worsens,
- no full100 until closed-loop smoke and flight20 evidence exist.

## Paper Positioning

Safe wording:

- "Per-candidate source IDs can be reconstructed offline, confirming the heading candidate bottleneck."
- "Saved logs do not contain exact active or low-h candidate IDs, so recall-preserving heading caps cannot yet be certified."
- "FC-Aware V1 remains a future efficiency direction requiring additional no-intervention logging."

Forbidden wording:

- Do not claim safety improvement.
- Do not claim runtime improvement.
- Do not claim closed-loop validation.
- Do not recommend a cap as safe.
- Do not claim full100 validation.
