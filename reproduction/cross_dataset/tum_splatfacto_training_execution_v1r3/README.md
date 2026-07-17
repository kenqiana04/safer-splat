# Formal TUM Splatfacto Training Execution V1R3 Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Execute this authorized plan inline, task-by-task, and stop after one terminal outcome. No retry is permitted.

**Goal:** Run at most one canonical TUM_FR1_ROOM Splatfacto training attempt only after V1R3 prepares a writable execution-record root before GPU sampling.

**Architecture:** This directory is the sole V1R3 Git evidence boundary. The
frozen protocol is read unchanged from commit
`6843fa477adc7f07acdfdb270ad7e4e3349da904`; all large artifacts remain in
the authoritative server run and execution-record roots.

**Tech Stack:** Git blobs, Bash, tmux, Python 3.10.20, Nerfstudio 1.1.5,
PyTorch 2.1.2+cu118, CUDA 11.8, and gsplat 1.4.0.

---

## File structure

- `EXECUTION_AUTHORIZATION_V1R3.md`: explicit authorization and non-reuse.
- `execution_contract.json`: immutable execution limits and paths.
- `infrastructure_preflight.json`: record-parent/root preparation evidence.
- `*_preflight.json`: compact identity, environment, data, GPU, disk, and
  output evidence.
- `scripts/`: server-side preflight, launch, passive monitoring, validation,
  and compact-audit helpers; never stores artifacts in Git.
- `REPORT_TUM_SPLATFACTO_TRAINING_EXECUTION_V1R3.md`: terminal audit report.

### Task 1: Publish immutable V1R3 authorization

- [ ] Create only the V1R3 authorization files and frozen wrappers.
- [ ] Commit `docs(reproduction): authorize formal TUM training execution V1R3`.
- [ ] Push the new branch and open the required Draft PR before server work.

### Task 2: Prepare isolated server and record infrastructure

- [ ] Add a detached worktree at
  `/disk1/zlab/formal_execution_worktrees/tum_splatfacto_training_execution_v1r3`
  from the authorization commit and verify it is clean.
- [ ] Before GPU sampling, create/verify
  `/disk1/zlab/formal_execution_records` and create the unique V1R3 record
  root. Verify directory permissions with a temporary write probe; retain the
  root thereafter.

### Task 3: Run all non-training preflight gates

- [ ] Verify canonical Git blobs, exact SHA-256 bytes, LF checkout, and
  transforms.
- [ ] Verify environment versions, dataparser-only 300/240/60 invariants,
  output absence, at least 20 GiB disk, shell syntax, and CLI help.
- [ ] On any failure, record attempt zero and stop without tmux or `ns-train`.

### Task 4: Gate and launch the sole attempt

- [ ] Write T−60, T−30, and T−0 GPU samples directly into the record root.
- [ ] If all three compute counts are zero, immediately start the prescribed
  tmux session using only the frozen command; otherwise stop attempt zero.
- [ ] Mark attempt one only after a real `ns-train` PID is observed.

### Task 5: Passively monitor and validate the terminal result

- [ ] Capture five-minute passive monitor rows while training runs.
- [ ] On a nonzero exit, preserve evidence and classify without retry.
- [ ] On exit zero, perform T1–T6 identity, completion, checkpoint, metric,
  eval/render, and geometry checks before emitting the sole allowed PASS.

### Task 6: Preserve evidence and stop

- [ ] Commit only compact V1R3 evidence, push the same Draft PR, and copy only
  the Markdown report to Desktop REPORT.
- [ ] Remove only the detached V1R3 worktree after evidence is committed,
  pushed, and hashes are verified; retain the formal run and record root.
