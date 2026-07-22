# TUM SplaTAM One-Shot Runtime Recovery G1 V2 Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Execute inline in this isolated worktree. Only this task root may be added or modified.

**Goal:** Preserve the explicitly authorized user reports, synchronize the authoritative checkout to PR #44, and run the bounded original-SAFER G1 smoke without optional safety modules.

**Architecture:** Archive-and-verify the three known reports before removing them from the checkout; gate the detached switch on clean/idle/identity checks; then run map, query, original-filter, dynamics, QP, and bounded rollout stages in order, stopping only on specified real failures.

**Tech Stack:** Git, SSH, Python/PyTorch CUDA, original SAFER code, immutable canonical SplaTAM assets.

---

### Task 1: Archive and synchronization

- [ ] Copy, hash, byte-compare, tar, and relocate only the authorized user reports.
- [ ] Create a rollback branch, fetch/verify PR #44 objects, and switch detached without force/reset/clean.

### Task 2: Preflight and map integration

- [ ] Verify import identity, environment, assets, and the complete SplaTAM map load/unload/reload contract.
- [ ] Stop if frozen query behavior, asset identity, or map initialization fails.

### Task 3: Original-SAFER smoke

- [ ] Recover baseline constants, validate original filter/dynamics/CBF-QP, and run one-step QP.
- [ ] Execute one safe original-baseline trial and at most three fixed diagnostics only after full success.

### Task 4: Evidence and release

- [ ] Classify the bounded outcome, write minimal tracked evidence/report, copy only the report, and publish one Draft PR.
