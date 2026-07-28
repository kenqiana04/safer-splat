# Replica Splatfacto SAFER-Native Baseline Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Qualify only the frozen SAFER-native Splatfacto path on Replica RGB-D V3 with metric GT poses, a 16/8 operational smoke, a gated 60/30 geometry pilot, and dual-path static G0 checks.

**Architecture:** All task-owned Python entry points write compact atomic JSON under `/disk1/zlab/maintenance_records/replica_splatfacto_native_baseline_qualification_v1`. The source dataset, PR #56 pilot registry, Nerfstudio package, and SAFER runtime are read-only. A shared helper module will centralize immutable identities, manifest transitions, and zero-count boundary checks; all later stages consume only frozen artifacts.

**Tech Stack:** Python, Nerfstudio/Splatfacto, PyTorch/CUDA, gsplat, NumPy, task-owned JSON/transforms adapters, GitHub CLI.

---

### Task 1: Freeze upstream and input identities

**Files:**
- Create: `reproduction/cross_dataset/replica_splatfacto_native_baseline_qualification_v1/freeze_replica_splatfacto_input_identity.py`
- Create: `reproduction/cross_dataset/replica_splatfacto_native_baseline_qualification_v1/input_identity_summary.json`

- [ ] Verify PR #56 head, published Replica V3 hashes, 300 RGB/depth files, split, and the copied PR #56 pilot registry/order before any runtime launch.
- [ ] Require exact expected SHA-256 values and emit `BLOCKED_BY_REPLICA_SPLATFACTO_INPUT_IDENTITY_MISMATCH` on any mismatch.
- [ ] Verify by parsing the compact JSON and asserting `status == "PASS_REPLICA_SPLATFACTO_INPUT_IDENTITY"`.

### Task 2: Discover the frozen native asset and authority

**Files:**
- Create: `discover_safer_native_splatfacto_assets.py`, `audit_splatfacto_native_environment.py`, `freeze_splatfacto_configuration_authority.py`
- Create: `splatfacto_native_asset_inventory.json`, `splatfacto_native_environment_audit.json`, `splatfacto_native_configuration_authority.json`

- [ ] Search only the four authorized server roots; do not download, pull, upgrade, or mutate an environment.
- [ ] Require one existing environment that can load the official SAFER Splatfacto checkpoint and one uniquely recoverable authority config.
- [ ] Verify by importing the frozen package and parsing each compact JSON; otherwise atomically terminalize the manifest with the applicable blocking status.

### Task 3: Prove the metric dataparser contract

**Files:**
- Create: `build_splatfacto_metric_dataparser.py`, `validate_splatfacto_metric_dataparser.py`, `build_splatfacto_pilot_adapters.py`
- Create: `splatfacto_metric_dataparser_contract.json`, `splatfacto_dataset_adapter_identity.json`

- [ ] Build only symlink/transforms adapters for the frozen 16/8 and 60/30 frame lists.
- [ ] Execute the actual frozen dataparser and assert scale 1, no orientation/centering, exact intrinsics/poses, and the stated reprojection/depth/pairwise-distance tolerances.
- [ ] Verify that train/eval lists are disjoint and contain no official-eval frame or depth input consumed by Splatfacto training.

### Task 4: Bind the pre-frozen common evaluator and run contract

**Files:**
- Create: `bind_splatfacto_common_evaluator.py`, `freeze_splatfacto_run_contract.py`
- Create: `splatfacto_common_evaluator_binding.json`, `splatfacto_run_contract.json`

- [ ] Recover the PR #56 evaluator contract unchanged and run the required SplaTAM smoke regression before accepting a Splatfacto schema adapter.
- [ ] Freeze seed 20260728, GPU 1, smoke/pilot budgets, zero camera/depth/scale controls, and one-run semantics.
- [ ] Verify every frozen field and atomically mark the run manifest before training.

### Task 5: Execute only the technical smoke gate

**Files:**
- Create: `run_splatfacto_smoke.py`, `export_splatfacto_smoke_canonical_map.py`, `evaluate_splatfacto_smoke_diagnostic.py`
- Create: `splatfacto_smoke_summary.json`, `splatfacto_smoke_canonical_export_summary.json`, `splatfacto_smoke_geometry_diagnostic.json`

- [ ] Run one serial 16-frame smoke with the authority configuration and task-owned output; retain logs/checkpoint server-side.
- [ ] Require operational/reload/export/render/finite checks only. Record but do not gate pilot on smoke AbsRel, delta1, ratio, PSNR, or SSIM.
- [ ] Verify checkpoint reload, unfiltered canonical-array identity, 8 holdout predictions, and zero camera/pose mutation.

### Task 6: Execute the gated pilot and common geometry evaluation

**Files:**
- Create: `run_splatfacto_qualification_pilot.py`, `export_splatfacto_pilot_canonical_map.py`, `evaluate_splatfacto_pilot_geometry.py`, `audit_splatfacto_pilot_map_structure.py`
- Create: `splatfacto_pilot_summary.json`, `splatfacto_pilot_canonical_export_summary.json`, `splatfacto_pilot_geometry_evaluation.json`, `splatfacto_pilot_map_structure_audit.json`

- [ ] Start exactly one 60-frame pilot only after an operational smoke pass; otherwise create explicit `NOT_AUTHORIZED_DUE_TO_SMOKE` artifacts.
- [ ] Evaluate exactly the 30 frozen holdouts with the bound evaluator and frozen geometry thresholds.
- [ ] Verify no filtering, scale fitting, normalization, or scientific retry occurred.

### Task 7: Run native-loader and canonical dual-path G0

**Files:**
- Create: `load_splatfacto_with_safer_native_loader.py`, `run_splatfacto_safer_native_g0.py`, `run_splatfacto_safer_canonical_g0.py`, `compare_splatfacto_dual_path_g0.py`
- Create: `splatfacto_safer_native_loader_summary.json`, `splatfacto_safer_native_g0_summary.json`, `splatfacto_safer_canonical_g0_summary.json`, `splatfacto_dual_path_g0_consistency.json`

- [ ] Load only a completed pilot checkpoint through the frozen SAFER-native path and verify required SAFER source identities.
- [ ] Run the same 256 static queries three times through native and canonical loaders; do not run controller or navigation code.
- [ ] Verify finite/repeatable values, no map mutation, and cross-path h/gradient/Hessian tolerances.

### Task 8: Classify, validate, publish, and stop

**Files:**
- Create: `classify_splatfacto_native_baseline.py`, all required compact terminal JSON, 14 figures, `REPORT_REPLICA_SPLATFACTO_NATIVE_BASELINE_QUALIFICATION_V1.md`

- [ ] Materialize every required compact JSON with an explicit terminal or gate status; exclude raw arrays, checkpoints, renders, logs, caches, and environment copies from Git.
- [ ] Parse all JSON, compile every Python file, validate all zero-count boundaries and GPU cleanup, then create exactly one Draft PR from the requested branch.
- [ ] Commit only `reproduction/cross_dataset/replica_splatfacto_native_baseline_qualification_v1/` using `test(reproduction): qualify Replica Splatfacto native baseline`.

## Self-review

- [ ] Input identity, PR #56 pilot reuse, metric-pose proof, common-evaluator regression, smoke-only technical gating, pilot-only geometry gating, native/canonical G0 separation, TUM boundary, and Git boundary each have a dedicated task.
- [ ] All task file names and statuses are exact protocol names; no full-map, navigation, CBF-QP, depth supervision, pose optimization, scale fitting, or scientific retry is authorized.
- [ ] The tracked output contains compact evidence only; remote raw scientific outputs remain server-side.
