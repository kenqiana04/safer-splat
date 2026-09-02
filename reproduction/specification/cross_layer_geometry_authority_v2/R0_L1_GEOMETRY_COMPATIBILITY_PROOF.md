# R0/L1 Geometry Compatibility Proof

## Premises

1. R0 queries the current position `p_k` with the canonical V2 point view: effective radius `0.025 m`, G3 map authority, and the frozen sign convention.
2. L1 certifies the closed immediate segment `[p_k,p_{k+1}]` with the canonical V2 segment view: the same effective radius and map authority, plus `rho_seg=0.0 m`.
3. A valid closed-segment PASS certifies every point on that segment under the same geometry contract.
4. `p_k` is an endpoint of `[p_k,p_{k+1}]`.

## Result

Under identical G0/G1/G3 identity and sign semantics, `L1_PASS` implies the canonical current-point predicate at `p_k` is PASS. Therefore R0 is logically redundant as a gating layer and remains only a cheap diagnostic or health precheck, matching PR #107.

This implication does not collapse I0a or I0b: admission and repair verification occur at distinct architecture boundaries. It also does not permit an R0 failure to replace L1, alter the committed action, or define a different geometry.

Verdict: `PASS_SAME_CONTRACT_R0_L1_COMPATIBILITY`.
