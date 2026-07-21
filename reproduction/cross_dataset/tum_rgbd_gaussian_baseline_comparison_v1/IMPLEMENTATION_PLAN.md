# TUM RGB-D Gaussian Baseline Comparison V1 Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Determine whether dedicated official RGB-D Gaussian baselines can exceed the internal TUM delta1 plateau under the identical fixed 240/60 GT-pose map-only protocol.

**Architecture:** Freeze PR #38 and TUM identities first, then audit the two official repositories in isolated task-owned locations. Run SplaTAM only as GT-pose map-only when its official interface supports it; classify Gaussian-SLAM separately unless a <=100-line non-mapping tracking bypass is feasible. Preserve native metrics, and run the shared static adapter only after parameter semantics are proven.

**Tech Stack:** Git/GitHub CLI, SSH, task-owned Conda or Docker environments, official SplaTAM and Gaussian-SLAM source, PyTorch/CUDA, JSON/Markdown evidence.

---

### Task 1: Freeze upstream, official source, and dataset identities

- [x] Verify PR #38 state/head and no prohibited execution.
- [x] Clone or locate only official SplaTAM and Gaussian-SLAM sources; record commit, submodules, license, manifest, and clean state.
- [x] Build the fixed 300-frame registry and prove the 240/60 split, GT poses, RGB/depth identities, and metric depth scale.

### Task 2: Isolate and qualify external environments

- [x] Create only task-owned per-method environments or use official containers.
- [x] Record package/CUDA/GPU/import identities and complete import/build smoke checks.

### Task 3: Establish comparability and minimal adapters

- [x] Audit official entry points for fixed GT-pose map-only operation.
- [x] Keep official clones clean and store any allowed minimal patch task-side.
- [x] Classify each method as MAP_ONLY_COMPARABLE, SYSTEM_LEVEL_ONLY, or NOT_REPRODUCIBLE before a full run.

### Task 4: Execute bounded baseline runs

- [x] Run 5-frame and 30-frame smoke gates.
- [x] Run at most one empty-output 240-frame map-only full run for each comparable method.
- [x] Keep system-level results isolated and do not mix them with primary rankings.

### Task 5: Evaluate and audit comparable maps

- [x] Render only the fixed 60 held-out GT-pose frames using native semantics and raw metric depth.
- [x] Audit common Gaussian semantics; only then run the static map/query/gradient/continuity audit.
- [x] Apply the frozen decision rules without Sim(3), scale fitting, frame filtering, or threshold changes.

### Task 6: Report, validate, and publish

- [x] Generate only compact tracked evidence and a desktop Markdown report.
- [ ] Validate boundaries, commit only the task root, push, and open the required Draft PR.
