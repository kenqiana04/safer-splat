# Core V2 L2/H1 causal increment specification V1

## Research question

**RQ-V2-L2-H1:** Under the frozen position-first forward-Euler execution model and frozen Gaussian safety semantics, can a minimal candidate-dependent, continuous-segment-aware L2 certificate evaluate `u_k` on `[t_(k+1),t_(k+2)]` without introducing H2, recursive feasibility, backup rollout, or new controller semantics?

**RQ0 / falsification:** If execution timing, map semantics, continuous-segment semantics, or the frozen backend cannot support this contract, do not implement L2; record the typed blocker.

## Decision

The answer is yes at specification level only. `S_H1(x_k,u_k)=Segment(p_(k+1),p_(k+2)(u_k))` is candidate-dependent under the frozen model. Existing exact-analytic or conservative full-segment backends can evaluate those endpoints without a new safety primitive. The new contribution is a causal role and tri-state interface, not new geometry.

The certificate is local, map-relative, first-control-affected-segment evidence. It does not prove H2, recursive feasibility, backup existence, safe stopping, real-time feasibility, physical-world collision avoidance, or performance.
