# MPC-style Recovery Final Positioning

## Recommended Paper Role

MPC-style Recovery should be described as:

- an optional recovery extension explored in targeted offline replay,
- not adopted as the main method,
- not a replacement for existing V4-C,
- not closed-loop validated,
- not full100 validated,
- future work.

The main contribution should remain Start-Safe CBF plus Discrete-Time Verification, with existing V4-C retained as optional triggered recovery evidence.

## Safe Claims

Safe:

- A primitive-sequence MPC-style recovery was evaluated offline on targeted DT-risk trigger states.
- The evaluator rolled out H-step candidate sequences and checked repository GSplat h values.
- It did not provide sufficient evidence to replace existing V4-C recovery.
- The pilot reveals that naive primitive-sequence search often selects nominal or smoothed nominal controls and leaves unresolved margin violations.
- Existing R4_H2_N64 remains the practical recovery reference.
- MPC-style sequence recovery remains a future extension.

## Forbidden Claims

Do not claim:

- MPC-style Recovery improves safety.
- MPC-style Recovery improves runtime.
- MPC-style Recovery outperforms V4-C.
- MPC-style Recovery is closed-loop validated.
- MPC-style Recovery is full100 validated.
- MPC-style Recovery is a main contribution.
- MPC-style Recovery guarantees safety.
- MPC-style Recovery introduces a new CBF theorem.
- Margin violation is collision.
- GSplat h is meter clearance.

## Future Work Wording

Suggested wording:

"A preliminary primitive-sequence MPC-style recovery was explored as a future extension. In targeted offline replay, it did not outperform the existing triggered V4-C recovery reference, suggesting that future sequence-based recovery should incorporate obstacle-aware directions, stronger safety-first selection, and CBF-QP-in-the-loop rollout."

"We therefore keep recovery as an optional triggered module and focus the main contribution on start-safe feasibility certification and discrete-time verification."

## Relationship To Existing V4-C

R4_H2_N64 remains the practical optional recovery reference. H3_N128 remains the robust optional recovery reference. The primitive MPC-style pilot should be treated as negative diagnostic / future-work material, not as replacement evidence.
