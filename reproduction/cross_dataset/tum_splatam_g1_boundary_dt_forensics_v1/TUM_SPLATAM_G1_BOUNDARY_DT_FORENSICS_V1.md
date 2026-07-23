# TUM SplaTAM G1 Boundary and Discrete-Time Forensics Plan

**Goal:** Certify the PR #47 terminal boundary event without changing its controller or trajectory.

**Architecture:** Freeze PR #47 evidence, reconstruct the explicit-Euler state sequence from logged controls, evaluate the fixed event window against full-map/filter and independent float64 references, then run frozen H1/H2/H3 only as shadow instrumentation.

**Tech Stack:** Python, NumPy, PyTorch CUDA, canonical SplaTAM arrays, original SAFER source, immutable server evidence.

### Task 1: Freeze and reconstruct

- [ ] Hash PR #47 trajectory evidence and all frozen source/map identities.
- [ ] Reconstruct `x[k+1] = x[k] + 0.05 * [v[k], u[k]]` from frames 0 to 50 and logged safe controls; save only compact identity/error summaries.

### Task 2: Boundary certification

- [ ] Evaluate steps 740--773 with full-map and original-filter semantics.
- [ ] Independently solve candidate ellipsoid distance in float64 with bisection and Newton-plus-bisection, recording residuals and classification.

### Task 3: Shadow verification and publication

- [ ] Run frozen H1/H2/H3 without changing state/control, classify warning lead time, and verify state/control hashes are unchanged.
- [ ] Write compact summaries/report, copy the report, commit, push, and open exactly one Draft PR.
