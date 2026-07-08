# MPC-style Recovery Positioning Update

## Current Positioning

MPC-style Recovery should remain an optional recovery extension, not a primary paper contribution.

The main paper line remains:

Certified Feasibility-Aware Start-Safe CBF + Discrete-Time Verification + optional triggered Predictive Recovery.

The completed targeted pilot evaluates a primitive-sequence / sampling-based MPC-style recovery idea. It is useful as an exploratory diagnostic, but the current H2_N64 and H3_N64 profiles do not support moving the module into the main method.

## What Can Be Written Safely

Safe paper wording:

- The recovery layer is optional and triggered by DT Verification warnings.
- A lightweight primitive-sequence MPC-style evaluator was tested offline on targeted DT-risk states.
- The evaluator rolls out short recovery sequences, checks GSplat h values, and selects the first action of the best sequence.
- The pilot was targeted and offline; it was not full100 and not closed-loop.
- The primitive H2/H3 N64 profiles left 96 selected H-step margin violations on 199 targeted trigger rows.
- The pilot did not provide evidence of improvement over the existing V4-C R4_H2_N64 direction.
- MPC-style sequence optimization remains future work unless a stronger sequence family or optimizer is introduced.

## What Must Not Be Claimed

Do not claim:

- a new CBF theorem,
- standalone safety guarantees from MPC-style Recovery,
- full nonlinear MPC,
- always-on MPC control,
- replacement of Start-Safe CBF,
- replacement of DT Verification,
- replacement of CBF-QP filtering,
- replacement of V4-C recovery,
- direct improvement over R4_H2_N64,
- full100 benchmark performance,
- collision outcomes from the offline evaluator,
- meter clearance from `min_safety_h` / GSplat h values.

## Relationship To V4-C References

Existing V4-C references:

- `H3_N128` full100: robust reference with closed-loop exec margin violations reduced to 0, but higher runtime than R4.
- `R4_H2_N64` full100: practical dense-flight tested config with closed-loop exec margin violations reduced to 0 and lower runtime.

MPC-style targeted pilot:

- offline only,
- targeted DT-risk states only,
- 199 trigger rows,
- H2_N64 and H3_N64 both left 96 selected H-step margin violations,
- not directly comparable to the V4-C closed-loop references.

The current evidence supports describing V4-C as the stronger optional triggered recovery evidence. The primitive MPC-style version should be framed as an attempted extension whose first offline result was not strong enough to justify closed-loop or full100 escalation.

## If Results Are Used In The Paper

Use as a short limitation / future-work note:

"We also explored a lightweight primitive-sequence MPC-style recovery evaluator over targeted DT-risk states. Although this made the receding-horizon structure explicit, the simple H2/H3 N64 primitive library did not remove all selected H-step margin violations in offline replay. We therefore keep sequence-optimized recovery as future work and retain the main contribution focus on start-safe certification and discrete-time verification."

## Next Research Direction

If this line is revisited, do not run full100 immediately. First improve one or more of:

- sequence family diversity near deep low-margin states,
- safety-first candidate ranking before smoothness/goal terms,
- adaptive horizon or N only for hard windows,
- direct integration with V4-C's successful candidate mechanisms,
- closed-loop smoke on a small targeted subset only after offline selected violations decrease.
