# FC-Aware V1 Recall Positioning Update

## Current Position

FC-Aware V1 remains a candidate selection / efficiency support direction. It is not a main paper contribution and not a safety guarantee.

The heading shadow audit showed aggregate candidate-count headroom. The per-candidate recall audit reconstructed exact source candidate IDs, but active and low-h IDs are still unavailable from saved logs.

## Relationship Between Shadow Audit And Recall Audit

The shadow audit answered:

- heading candidates dominate final candidate count,
- heading caps have large theoretical accounting reduction,
- risk windows are affected by every tested cap.

The recall audit added:

- source candidate IDs can be reconstructed offline,
- active constraint IDs are not available,
- low-h candidate IDs are not available,
- recall_available remains false.

Therefore the evidence is not sufficient for wrapper-level closed-loop smoke.

## Safe Claims

Safe:

- FC-Aware V1 targets a real bottleneck: forced heading candidates.
- Offline reconstruction can recover source candidate IDs.
- Existing saved logs do not support active / low-h recall measurement.
- Additional no-intervention logging is required before closed-loop testing.
- FC-Aware V1 is future work / support diagnostic.

## Forbidden Claims

Do not claim:

- FC-Aware V1 improves runtime,
- FC-Aware V1 improves safety,
- any heading cap is recall-safe,
- closed-loop validation exists,
- full100 validation exists,
- FC-Aware V1 replaces Start-Safe CBF, DT Verification, CBF-QP, or V4-C,
- `h` is metric clearance,
- margin violation is collision.

## If Continued

Next step should be no-intervention logging, not capped closed-loop:

1. active gaussian IDs,
2. candidate h values / low-h IDs,
3. heading distance and cosine,
4. retained top-M IDs for rankings,
5. recall audit on targeted risk windows,
6. wrapper smoke only if risk-window active/low-h recall is high.

## If Frozen

Paper wording:

"Adaptive V1 revealed that selected_K-only scheduling does not reduce final candidate count because forced heading candidates dominate. A follow-up FC-aware audit showed large aggregate headroom, but saved logs lacked exact active and low-h candidate IDs, so recall-preserving heading caps could not be validated. We leave FC-aware candidate selection as future work."
