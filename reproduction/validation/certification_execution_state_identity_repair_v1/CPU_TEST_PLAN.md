# CPU Test Plan

- Canonical torch.float32 transition versus the frozen plant reference on 20 deterministic state/action pairs.
- L1 immediate-position bitwise action independence.
- L2 first-position action independence, second-position causal sensitivity, and second-step-action position irrelevance.
- Repaired L2 to next-cycle repaired L1 bitwise segment continuity.
- Synthetic canonical identity mismatch blocks before plant commit.
- Frozen Active runtime, token, trace, commit-transaction, V3 geometry, and trace-cardinality CPU regressions run unchanged.

No rollout, controller/QP call, coordinator cycle, scientific analyzer, or GPU is part of the CPU suite.
