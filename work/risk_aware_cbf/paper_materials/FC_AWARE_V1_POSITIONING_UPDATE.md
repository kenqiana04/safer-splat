# FC-Aware V1 Positioning Update

## Current Positioning

FC-Aware V1 is a candidate selection / efficiency support direction. It is not part of the core FAS-CBF theorem line and should not be described as a safety guarantee.

The current evidence supports FC-Aware V1 as future work / design follow-up, not as a closed-loop validated method.

## Why Selected_K-only Adaptive V1 Is Not Enough

Adaptive V1 selected_K scheduling is risk-responsive, but final candidate count remains almost unchanged because forced heading candidates dominate the final union.

The selected_K budget controls the optional risk-ranked remainder. It does not post-cap final unique candidates after forced near, heading, and history sources are unioned.

## Forced Heading Candidate Bottleneck

Read-only inspection confirms:

- heading candidates are forced,
- heading candidates are not limited by selected_K,
- there is no post-union cap,
- heading source dominates final candidate count in targeted DT-risk windows.

This makes heading-aware selection a more relevant efficiency direction than continued selected_K tuning.

## Shadow Audit Interpretation

Aggregate shadow accounting on targeted risk windows shows large theoretical reduction potential:

- cap 2000: reduction ratio mean `0.897607`,
- cap 4000: `0.816687`,
- cap 8000: `0.654847`,
- cap 12000: `0.493007`,
- cap 16000: `0.331167`.

However, risk-window affected fraction is `1.0` for all tested caps and per-candidate recall is unavailable. This means the result supports logging and design work, not immediate closed-loop claims.

## Safe Claims

Safe:

- selected_K-only Adaptive V1 is not sufficient for candidate-count reduction because forced heading candidates dominate final count,
- FC-aware heading selection is a plausible future direction,
- current shadow audit is aggregate-only and offline,
- per-candidate recall logging is required before closed-loop smoke,
- near candidates should remain mandatory.

## Forbidden Claims

Do not claim:

- FC-Aware V1 improves safety,
- FC-Aware V1 improves runtime,
- FC-Aware V1 has closed-loop validation,
- FC-Aware V1 has full100 validation,
- heading cap is safe without fallback,
- aggregate shadow accounting proves candidate-count reduction in closed-loop,
- `h` / `min_safety_h` is metric clearance,
- margin violation is collision.

## If Continued

Minimum next validation steps:

1. add per-candidate heading ID logging,
2. log active / low-h / retained candidate recall,
3. keep all near candidates,
4. implement full heading and full-query fallback,
5. run wrapper-level closed-loop smoke only after recall audit passes,
6. avoid full100 until smoke and flight20 evidence exist.

## If Not Continued

Frame FC-Aware V1 as future work:

"The Adaptive V1 study revealed that forced heading candidates dominate final candidate count, limiting selected_K-only budgeting. A follow-up heading-aware shadow audit suggests potential accounting headroom, but per-candidate recall and closed-loop validation are required before any efficiency claim."
