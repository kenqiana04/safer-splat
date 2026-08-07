## Summary

Specify the minimal L2/H1 causal increment on the exact PR #92 head while preserving PR #83/#84/#86/#87/#89/#90/#91/#92. No implementation or formal experiment is included.

## Frozen contracts and decision

- Position-first Euler is preserved: `dp_(k+1)/du_k=0`, `dp_(k+2)/du_k=dt^2*I`.
- L1 is the uncontrollable immediate segment; H1/L2 is the first candidate-dependent segment.
- Exact sphere and conservative interval backends can be reused under their frozen map-relative assumptions; sampled/endpoint-only checks remain diagnostic.
- UNKNOWN fails closed and remains distinct from candidate unsafe.
- L2 precedes L3; frozen `ALT_ELIGIBLE` limits L4; L5 terminal and fail-close remain separate.
- H2 and all recursive, real-time, physical-world, performance, and deployment claims remain deferred/prohibited.
- G1-G7 PASS; four independent scoped reviews vote CASE_A.

`FINAL_STATUS=PASS_CORE_V2_L2_H1_CAUSAL_INCREMENT_SPECIFICATION`

`FINAL_DECISION=FREEZE_MINIMAL_L2_H1_SPECIFICATION_AND_VALIDATE_IN_SHADOW_ONLY_MODE`

`Only next task=IMPLEMENT_L2_H1_SHADOW_CERTIFIER_V1`
