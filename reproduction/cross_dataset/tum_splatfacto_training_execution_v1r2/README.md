# Formal TUM Splatfacto Training Execution V1R2 Implementation Plan

> **For agentic workers:** Perform exactly one immutable, authorized execution
> path. Stop after a recorded block, failure, or validated success.

**Goal:** Execute at most one canonical TUM_FR1_ROOM Splatfacto training run
after the required V1R2 preflight, and preserve only compact evidence in this
directory.

**Architecture:** The frozen protocol is read at
`6843fa477adc7f07acdfdb270ad7e4e3349da904`; formal artifacts stay on the
authoritative server. This is the sole V1R2 Git evidence boundary.

**Tech stack:** Git blobs, Bash, tmux, Python 3.10.20, Nerfstudio 1.1.5,
PyTorch 2.1.2+cu118, CUDA 11.8, and gsplat 1.4.0.

## Task 1: Authorize and publish V1R2

- [ ] Record the frozen identity, V1/V1R1 non-reuse, stale-process cleanup,
  and one-attempt semantics.
- [ ] Push this authorization commit and open the required new Draft PR.

## Task 2: Isolated authoritative-server preflight

- [ ] Create the detached V1R2 worktree only after authorization is public.
- [ ] Verify canonical bytes, environment, dataparser-only invariants, output
  absence, disk capacity, CLI schema, and three fresh GPU-1 idle samples.
- [ ] A block records attempt count zero and ends execution without tmux or
  `ns-train`.

## Task 3: Launch and passive monitoring

- [ ] Immediately after the third idle sample, start the frozen command once
  in the prescribed tmux session.
- [ ] Record passive five-minute samples only; never tune, retry, resume, or
  change GPU.

## Task 4: Successful-exit validation only

- [ ] Verify final checkpoint identity, CPU-load integrity, tensors, source
  assets, and metric invariants.
- [ ] Run the frozen evaluation/render commands only if all prior gates pass.

## Task 5: Preserve compact evidence and stop

- [ ] Commit and push only approved V1R2 evidence, update the same Draft PR,
  and copy only the final report to Desktop REPORT.
- [ ] Remove the detached server worktree only after compact evidence is
  copied, hashed, committed, and pushed; never delete the run or record.
