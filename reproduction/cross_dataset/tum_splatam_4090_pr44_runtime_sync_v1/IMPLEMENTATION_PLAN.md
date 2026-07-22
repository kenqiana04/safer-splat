# TUM SplaTAM 4090 PR44 Runtime Sync Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Execute inline in this isolated worktree. Only this task root may be added or modified.

**Goal:** Safely place the authoritative 4090 checkout at the exact PR #44 detached commit and emit a non-execution G1 reauthorization preflight.

**Architecture:** Audit clean/idle/lock state before any checkout mutation, create only a local rollback branch, verify the fetched target objects, then perform one ordinary detached switch. Evidence is written outside the checkout and no map or controller runtime is instantiated.

**Tech Stack:** Git, SSH, read-only Python imports, SHA-256, task-owned JSON evidence.

---

### Task 1: Safety audit

- [ ] Capture authoritative checkout status, locks, remote identity, and repository-using processes.
- [ ] Stop without mutation if dirty, active, locked, or remote identity is wrong.

### Task 2: Verified synchronization

- [ ] Create an unpushed rollback branch at the audited head.
- [ ] Fetch PR #44, verify commit and all four target blobs, then run only `git switch --detach`.

### Task 3: Non-execution preflight

- [ ] Verify post-switch source/V2 identity, import paths, environment, and asset metadata without loading maps or querying.
- [ ] Classify whether separate G1 reauthorization is ready.

### Task 4: Evidence

- [ ] Write compact task-owned summaries and report; publish only this task root in a Draft PR.
