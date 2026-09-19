# Bounded Local Recovery Smoke Retry2 Protocol Freeze Implementation Plan

> **For agentic workers:** Execute each checked task inline; this plan authorizes protocol-freeze artifacts only and never authorizes GPU execution.

**Goal:** Freeze an independent Retry2 engineering-smoke protocol that can later test the repaired multi-candidate canonical L2 evidence path without executing any trial now.

**Architecture:** Reuse the frozen Retry1 harness structure in a new task-local directory. Bind every future action to the repair HEAD, a distinct result root, tmux name, token, cohort, and execution lock; keep analysis post-run and read-only with explicit L2 evidence/reachability gates.

**Tech Stack:** Python 3, JSON/JSONL, Git, tmux launcher contract, deterministic SHA-256 locks.

---

### Task 1: Freeze protocol and harness sources

**Files:** Create all task-local protocol, runner, launcher, validator, monitor, analyzer, README, and freeze-generator files.

- [x] Copy the Retry1 harness structure without copying its results or authority identities.
- [x] Replace branch, result-root, tmux, token, implementation, schema, and filename identities with Retry2 identities.
- [x] Add candidate-scoped L2 evidence, rewrite-regression, recovery-L2, rank-progression, and hard-zero contracts.
- [x] Keep trial execution unreachable without the exact future authorization token.
- [x] Verify Python syntax and run freeze-mode CPU validation.
- [x] Commit as `Freeze bounded recovery smoke retry2 protocol` before generating the lock.

### Task 2: Freeze execution lock and validation evidence

**Files:** Create the execution lock, `results_freeze/*.json`, and final report.

- [x] Hash the committed protocol and harness files.
- [x] Record protocol commit, repair authority, lineage, map, geometry, F1, local bindings, and zero execution counts.
- [x] Run prelaunch validation with the result root and tmux still absent.
- [x] Audit protected diffs against `2102c8401b61ca8fe74123ab51e8fc9c27ed0895`.
- [x] Verify `python -m py_compile`, validator, and `git diff --check`.
- [x] Commit as `Freeze bounded recovery smoke retry2 execution lock`, push, and verify remote/local HEAD equality.
