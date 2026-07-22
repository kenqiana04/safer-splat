# TUM SplaTAM Original SAFER G1 Smoke Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Execute inline in this isolated worktree. Only this task root may be added or modified.

**Goal:** Run the authorized original-SAFER-only SplaTAM G1 smoke through immutable identity, map/query, filter, dynamics, QP, and bounded trial gates.

**Architecture:** Freeze PR #44, map, and original baseline identities; prove static integration before enabling controller code; stop immediately at any contract or execution failure. SplaTAM is the sole G1 map and Gaussian-SLAM remains controller-free.

**Tech Stack:** CUDA float32 PyTorch runtime, task-owned adapters/wrappers, original SAFER source, immutable canonical arrays.

---

### Task 1: Identity and adapter gates

- [ ] Record frozen source/map/config identities and create a read-only SplaTAM adapter.
- [ ] Load/unload/reload the complete map and compare deterministic controller-free queries.

### Task 2: Original baseline gates

- [ ] Recover original filter/controller/dynamics/QP configuration from prior baseline evidence.
- [ ] Build the frozen TUM-pair registry, diagnose initial states without repair, and stop if no safe pair exists.

### Task 3: Bounded execution

- [ ] Validate 6D dynamics and CBF-QP matrices before one QP solve.
- [ ] Run one original-baseline trial only after all prior gates pass; run at most three fixed diagnostics only after full one-trial success.

### Task 4: Evidence and publication

- [ ] Write compact task-owned reports and classification, copy only the REPORT file locally, then publish a Draft PR containing only this task root.
