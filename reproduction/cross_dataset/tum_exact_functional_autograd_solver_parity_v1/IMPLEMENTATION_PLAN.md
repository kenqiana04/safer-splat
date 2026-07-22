# TUM Exact Functional-Autograd Ellipsoid Solver Parity V1 Implementation Plan

> **For agentic workers:** execute only within this isolated worktree and task-owned server root.

**Goal:** Reconstruct the frozen SAFER ellipsoid forward path without in-place autograd breakage while preserving float32 GPU forward bits, then rerun static qualification only if strict parity passes.

**Architecture:** Freeze source and input identities, recover the actual failed functional script, trace official and functional bisection state on synthetic and fixed real cases, implement a trace-derived functional solver, and fail closed if zero forward difference cannot be proven.

**Tech Stack:** PyTorch CUDA float32, frozen SAFER source, deterministic synthetic/real probes, SSH, GitHub Draft PR.

---

- [ ] Freeze PR #40, source blobs, canonical-map manifests, and the actual failed script.
- [ ] Trace every official and functional bisection operation to locate first divergence.
- [ ] Implement and test a source-order-equivalent, non-inplace functional solver.
- [ ] Gate synthetic and real forward/gradient parity before any full 908 rerun.
- [ ] Run exact full-map parity, static-only audit, and G0 classification only if all gates pass.
- [ ] Validate compact evidence, copy only the report, commit, push, and open a Draft PR.
