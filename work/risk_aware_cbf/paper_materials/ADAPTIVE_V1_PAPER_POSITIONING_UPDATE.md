# Adaptive V1 Paper Positioning Update

## Safest Current Positioning

Adaptive V1 should be positioned as a candidate budgeting and risk-response support module. The balanced profile is currently supported by offline replay evidence, not closed-loop navigation.

## Results That Can Be Written

- The scheduler reacts to DT Verification warnings and low-margin states.
- Balanced scheduling reduces over-fallback relative to the conservative profile in offline replay.
- `selected_K` can be reported as a scheduled budget proxy.

## Results That Cannot Be Written Yet

- Do not claim closed-loop runtime improvement.
- Do not claim Adaptive V1 independently guarantees safety.
- Do not claim it replaces DT Verification or optional Predictive Recovery.
- Do not claim full benchmark performance without full100.

## Offline Replay Wording

Use: "offline replay / audit on saved V4-A + V1 trajectory." State that runtime, collision, QP infeasibility, and H-step margin counts are inherited from the saved trajectory.

## If Closed-Loop Succeeds Later

If a smoke-gated closed-loop pilot succeeds, Adaptive V1 can move from ablation-only toward an efficiency support module in Method and Experiments. It should still remain below Start-Safe CBF, DT Verification, and optional Predictive Recovery in the method hierarchy.
