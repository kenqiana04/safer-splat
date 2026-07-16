# Formal TUM Splatfacto Training Execution V1R1 Implementation Plan

> **For agentic workers:** Execute this plan inline with one immutable formal attempt and stop after its recorded outcome.

**Goal:** Execute at most one already-canonicalized formal TUM_FR1_ROOM Splatfacto run, then record only compact evidence and the allowed checkpoint/evaluation audits.

**Architecture:** This directory is the sole Git evidence boundary. The frozen protocol is read from commit `6843fa477adc7f07acdfdb270ad7e4e3349da904`; training and large artifacts remain in the authoritative server worktree and formal output root.

**Tech Stack:** Git blobs, Bash, tmux, Python 3.10, Nerfstudio 1.1.5, PyTorch 2.1.2+cu118, CUDA 11.8.

---

### Task 1: Authorize and publish the execution identity

- [ ] Record the immutable protocol, canonical hashes, prior blocked PR #24, and one-attempt rule.
- [ ] Push this authorization commit and create one Draft PR based on the protocol branch.

### Task 2: Preflight in an isolated authoritative-server worktree

- [ ] Verify Git-blob and LF checkout identity, environment, dataparser-only invariants, output absence, disk capacity, CLI schema, and three idle GPU checks.
- [ ] If any preflight check blocks, record attempt count zero and stop without tmux or `ns-train`.

### Task 3: Launch and passively monitor the single attempt

- [ ] Start the frozen command exactly once only after all preflight checks pass.
- [ ] Preserve stdout/stderr, exit status, timestamps, and passive five-minute monitor samples; never tune, retry, resume, or change GPU.

### Task 4: Validate a successful exit only

- [ ] Audit final checkpoint identity/integrity and metric/data invariants before invoking the frozen val evaluation and render commands.
- [ ] Record the 60-frame render integrity, metrics, geometry-sanity boundary, and validator result.

### Task 5: Preserve evidence and stop

- [ ] Commit only compact V1R1 evidence, push the existing V1R1 Draft PR, copy only the final Markdown report to Desktop REPORT, then remove the detached server worktree after evidence is preserved.
