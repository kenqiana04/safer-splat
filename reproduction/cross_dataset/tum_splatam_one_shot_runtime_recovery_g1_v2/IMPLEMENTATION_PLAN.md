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

---

## Continuation under PR #47 authorization

### Task 5: Archive the frozen remaining untracked set

- [ ] Re-read detached PR #44 identity and freeze `git status --porcelain=v2 --untracked-files=all` into `authorized_untracked_paths.txt`.
- [ ] Admit only `.vscode/extensions.json` and `work/risk_aware_cbf/` paths; record `lstat` metadata and content identities without following external symlinks.
- [ ] Build `remaining_checkout_untracked.tar`, extract it in a task-owned verification tree, and compare every path, mode, mtime, link target, byte sequence, aggregate count, and aggregate size.
- [ ] Remove only frozen, successfully verified source paths; leave all nonempty parent directories and every path outside the explicit relocation scope untouched.

### Task 6: Resume the bounded original-SAFER execution

- [ ] Require an empty post-relocation status, PR #44 HEAD/four-blob identity, no repository lock/foreign checkout process, and no conflicting GPU 1 compute process.
- [ ] Verify the prescribed environment/import and immutable asset identities; load/reload the exact 5,464,102-Gaussian SplaTAM canonical map.
- [ ] Run frozen radius-zero comparison, original-filter comparison, trial registry/initial diagnosis, dynamics and CBF-QP contracts, one-step QP, one original rollout, then at most three diagnostics.
- [ ] Stop only at a specified integrity, contract, resource, collision, infeasibility, nonfinite, timeout, or execution outcome; do not substitute optional safety modules.

### Task 7: Record and publish the continuation result

- [ ] Update only this task root's structured summaries, taxonomy, handoff, and report with actual evidence and explicit `NOT_RUN` fields for any gated stages.
- [ ] Validate JSON and report byte identity, copy only the report to `C:\\Users\\zlab\\Desktop\\REPORT`, then make one ordinary commit and push the existing branch.
- [ ] Update Draft PR #47 only; do not create, merge, amend, force-push, or mark any PR ready.
