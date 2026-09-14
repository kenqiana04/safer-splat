# Refreeze Active Runtime V3 Paired Execution Harness R1 Implementation Plan

> **For agentic workers:** Use this plan only for the CPU-only harness freeze; no collection or analyzer execution is authorized.

**Goal:** Create a fresh, immutable, repaired-runtime execution harness for the exact frozen 85-trial V3 paired protocol without running outcomes.

**Architecture:** Start from the accepted PR #146 runtime baseline in a separate worktree. Copy the old harness logic into a new task-local directory, then pin the repaired runtime, protocol, map/reference identities, fresh result root, and protected-diff rules. Add deterministic relative-path plumbing, immutable evidence/resume checks, an integrity-only monitor, and CPU validator evidence.

**Tech Stack:** Python 3.10, Bash, Git, JSON/CSV SHA-256 locks, tmux launcher (future use only).

---

### Task 1: Pin upstream and frozen inputs

**Files:** `V3_PAIRED_EXECUTION_R1_LOCK.json`, `V3_PAIRED_EXECUTION_R1_LOCK.sha256`, `REPAIR_SOURCE_LOCK.json`

- [ ] Record PR #146 repaired head/parent, PR #144 protocol identity, exact 85/order/dev15, map/checkpoint/reference identities, environment, V3 geometry, analyzer constants, and zero execution counts.
- [ ] Record hashes for all task-local harness files after they are finalized and generate the lock checksum.

### Task 2: Implement isolated runner and evidence contract

**Files:** `run_active_runtime_v3_paired_validation_r1.py`, `execution_evidence_schema.json`

- [ ] Add static preflight checks for repaired source, protocol, map, reference, protected diff, symlinks, and absent fresh result root.
- [ ] Add idempotent `data/stonehenge` and `outputs/stonehenge` symlink validation/creation without copying content.
- [ ] Retain CPU-only, GPU-preflight, one-trial, batch, and integrity-summary modes; require exact repaired baseline and reject incomplete existing trial directories.
- [ ] Require one trace per completed cycle, including legitimate no-action boundary cycles; keep scientific outcomes/analyzer out of the runner.

### Task 3: Freeze analyzer and launcher/monitor boundaries

**Files:** `analyze_active_runtime_v3_paired_validation_r1.py`, `start_v3_paired_validation_r1_tmux.sh`, `monitor_v3_paired_validation_r1.sh`

- [ ] Preserve the original 0.015 hard gate, 0.025 diagnostic-only shell, 85-pair NI constants, and no outcome feedback.
- [ ] Make the launcher refuse first-use result-root collisions, establish symlinks, run only future preflight then batch, and never invoke the analyzer.
- [ ] Make the monitor read only the authoritative integrity summary rather than raw evidence locks.

### Task 4: Add CPU validator and documentation

**Files:** `validate_v3_paired_execution_harness_r1.py`, `EXECUTION_HARNESS_R1_REPORT.md`, `DRAFT_PR_BODY.md`, `downstream_handoff.json`

- [ ] Validate exact branch/head, frozen protocol, repaired source lock, protected paths, 85/order/dev15, map/reference/environment, hashes, future-root absence, and all zero execution counters.
- [ ] Run py_compile, bash -n, validator, and git diff check; write explicit PASS evidence without starting GPU or analyzer.

### Task 5: Commit and publish

- [ ] Stage only `reproduction/validation/active_runtime_paired_validation_v3_execution_r1/`.
- [ ] Commit the refreeze, push the requested branch, and create one Draft PR against PR #146’s repair branch.
- [ ] Recheck remote head and preserve old harness/result roots read-only.
