# Candidate-dependent future-safety concept specification

Define `FUTURE_SAFE(x_k,u_k,M_k,H,W)` as a conceptual predicate with state, candidate, frozen map snapshot, horizon `H`, and explicit future-control witness/assumption `W`. Its output is one of `CERTIFIED`, `NOT_CERTIFIED`, or `NOT_EVALUABLE`; it is not implemented here.

**H1 FIRST_CONTROL_AFFECTED_SEGMENT (preferred specification target):** check `[t_(k+1),t_(k+2)]`, starting from the frozen position-first state at `t_(k+1)`. Candidate `u_k` affects that segment via `v_(k+1)`. H1 is authority-correct, minimally assumption-bearing, compatible with an explicit segment check, and does not posit a perfect future policy. It is nevertheless not present as a formal Core V1 certification layer.

**H2 SHORT_CONTROL_AFFECTED_HORIZON:** check a finite horizon from `t_(k+1)` onward. H2 may reduce local myopia, but must state every later-control witness/policy and cannot assume a perfect future controller. It is more computationally expensive and has greater witness dependence.

The immediate uncontrollable segment remains L1 and is a prerequisite to, not a substitute for, L2. Future safety is a certification target for a future specification, not an established efficacy claim.
