# Replica RGB-D V3 Render Validate Publish Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** formally render all 300 frozen Replica V3 RGB-D frames, validate every byte and identity boundary twice, and atomically publish only an all-pass staging dataset.

**Architecture:** frozen PR #54 inputs are copied byte-for-byte to the server task root and verified before any frame is rendered. A serial parent launches one fresh Python process and one fresh Habitat Simulator per three-yaw location; full integrity, memory/disk, pose, split, and tree checks run before two independent revalidations and same-filesystem publication.

**Tech Stack:** Python 3.9, Habitat-Sim 0.3.3, NumPy, imageio, uint8 PNG RGB, uint16 millimetre PNG depth, SHA-256, fsync, atomic rename.

---

### Task 1: Freeze identity, renderer contract, and server layout

**Files:**
- Create: `freeze_replica_v3_render_input_identity.py`
- Create: `recover_replica_renderer_contract.py`
- Create: `replica_v3_renderer_contract.json`
- Create: `input_identity_summary.json`

- [ ] Verify PR #54 frozen artifacts, scene, navmesh, texture inventory, historical renderer blobs, environment, and absent publication target.
- [ ] Recover RGB/depth save semantics from historical blobs: RGB uint8 RGB PNG and uint16 millimetre depth PNG with 0.001 m decode.
- [ ] Stop before rendering if any identity differs.

### Task 2: Freeze location scheduler and formal renderer

**Files:**
- Create: `build_replica_v3_formal_render_manifest.py`
- Create: `render_replica_v3_location.py`
- Create: `run_replica_v3_formal_render.py`
- Create: `formal_render_manifest_summary.json`
- Create: `replica_rgbd_v3_render_summary.json`

- [ ] Make the 100-location, 300-frame serial schedule from frozen manifest rows only.
- [ ] Render one location’s three frozen yaw frames in one fresh subprocess and Simulator, with no cross-location reuse.
- [ ] Atomically write and reread RGB/depth PNGs; permit only one same-initial-state retry for an infrastructure failure.

### Task 3: Validate integrity and deterministic identities

**Files:**
- Create: `validate_replica_v3_frame.py`
- Create: `validate_replica_v3_full_integrity.py`
- Create: `validate_replica_v3_memory_disk_consistency.py`
- Create: `validate_replica_v3_pose_identity.py`
- Create: `build_replica_v3_tree_identity.py`

- [ ] Check every RGB, depth, pairing, V1 minimum, V3 coverage, pose, split, and no-reuse condition.
- [ ] Keep full SHA manifests server-only; copy only compact summaries to Git.

### Task 4: Double validation and atomic publication

**Files:**
- Create: `run_replica_v3_double_validation.py`
- Create: `publish_replica_v3_atomically.py`
- Create: `validate_published_replica_v3.py`
- Create: `replica_rgbd_v3_double_validation_summary.json`
- Create: `publication_validation_summary.json`
- Create: `replica_rgbd_v3_dataset_identity.json`

- [ ] Run two new-process staging validations and require identical empty failure sets and tree identities.
- [ ] Copy only dataset files to an empty same-filesystem temporary path, fsync, rehash, then atomically rename only after every gate passes.
- [ ] Rehash the published target read-only.

### Task 5: Report, figures, validation, and Draft PR

**Files:**
- Create: `validation_result.json`
- Create: `downstream_handoff.json`
- Create: `REPORT_REPLICA_RGBD_V3_RENDER_VALIDATE_PUBLISH_V1.md`
- Create: `figures/*.png`

- [ ] Generate compact, failure-visible figures and report only verified results.
- [ ] Commit only this task directory, push one branch, and open one Draft PR after the terminal outcome is recorded.

## Scope check and self-review

The plan preserves the PR #54 protocol byte-for-byte, never repurposes preprobe buffers, never changes a pose, threshold, split, or source asset, and never starts mapping, training, SAFER/CBF, or TUM work. Any integrity or identity failure retains formal staging and stops publication; the only all-pass handoff is Gaussian mapping frontend qualification.
