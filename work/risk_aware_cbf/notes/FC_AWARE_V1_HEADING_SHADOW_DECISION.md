# FC-Aware V1 Heading Shadow Decision

## Summary

Forced heading candidate bottleneck is confirmed. Heading candidates are forced, dominate final unique candidate count, are not controlled by `selected_K`, and final union has no post-cap.

The shadow audit shows large theoretical aggregate candidate-count reduction potential, but it does not provide per-candidate recall evidence. Risk-window affected fraction is high, so the next step should be logging rather than closed-loop smoke.

## Key Answers

| question | answer |
|---|---|
| Forced heading bottleneck confirmed? | Yes |
| Heading candidates controlled by selected_K? | No |
| Final union post-cap exists? | No |
| Heading cap has theoretical reduction potential? | Yes |
| Per-candidate recall available? | No |
| Active / risk recall evaluable? | No |
| Risk windows heavily affected? | Yes, affected fraction `1.0` for all tested caps |
| Continue FC-Aware V1? | Yes, design/logging follow-up only |
| First add logging? | Yes |
| Wrapper-level closed-loop smoke now? | No |
| Full100 now? | No |
| More promising than selected_K-only? | Yes as a structural lever, not yet validated |

## Cap Tradeoff On Targeted Risk Windows

| heading cap | hypothetical final mean | reduction ratio mean | risk-window affected fraction |
|---:|---:|---:|---:|
| 2000 | 2536.15 | 0.897607 | 1.0 |
| 4000 | 4536.15 | 0.816687 | 1.0 |
| 8000 | 8536.15 | 0.654847 | 1.0 |
| 12000 | 12536.15 | 0.493007 | 1.0 |
| 16000 | 16536.15 | 0.331167 | 1.0 |

These are aggregate accounting estimates, not measured closed-loop candidate counts.

## Recall Status

Per-candidate recall cannot be measured from current logs. Existing step CSVs contain aggregate source counts but not:

- heading candidate IDs,
- retained top-M heading IDs,
- active constraint IDs,
- low-h candidate IDs,
- sector coverage IDs.

Therefore active constraint recall, previous active recall, low-h candidate recall, and risk-window recall are unavailable.

## Minimum Safety Protections

Any future wrapper-level implementation must include:

1. keep all near candidates,
2. full heading fallback,
3. DT Verification guard,
4. full-query fallback,
5. rollback if min_safety_h or H-step margin worsens,
6. active/risk recall logging before closed-loop,
7. closed-loop smoke before flight20 or full100.

## Paper Wording

Safe:

- "A forced-candidate-aware heading shadow audit indicates that heading candidates dominate final candidate count and are not limited by selected_K."
- "Aggregate shadow accounting suggests substantial candidate-count headroom under heading caps, but per-candidate recall is unavailable."
- "FC-aware selection is a plausible future efficiency direction requiring logging and closed-loop validation."

Forbidden:

- Do not claim candidate-count reduction as a closed-loop result.
- Do not claim runtime improvement.
- Do not claim safety improvement.
- Do not claim FC-Aware V1 guarantees safety.
- Do not claim full100 validation.
- Do not cap near candidates in the first version.
