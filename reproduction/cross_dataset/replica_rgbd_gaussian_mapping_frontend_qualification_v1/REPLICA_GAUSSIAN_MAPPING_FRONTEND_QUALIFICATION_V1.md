# Replica Gaussian Mapping Frontend Qualification V1 Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Execute this plan inline, task by task. Each stage writes an atomic compact result before the next stage may run.

**Goal:** Qualify the existing SplaTAM and Gaussian-SLAM assets on the published Replica RGB-D V3 dataset using a frozen GT-pose map-only 60-frame pilot, a shared Gaussian evaluator, and static SAFER G0 queries.

**Architecture:** The task-owned Python package is a thin audit and adapter layer. It never changes the published dataset or frontend repositories: it freezes V3 input identity, deterministic pilot selection, input coordinates, and frontend configurations before serial frontend execution. It writes full runtime artifacts only under the server maintenance root and commits compact JSON, scripts, figures, and the report.

**Tech Stack:** Python 3.9, NumPy, Pillow, PyTorch/CUDA from existing frontend environments, existing SplaTAM/Gaussian-SLAM archives, Git, SSH, and the existing SAFER static Gaussian-distance runtime.

---

## File map

- `freeze_replica_mapping_input_identity.py`: read-only V3 tree, manifest, split, and pose identity verification.
- `discover_replica_gaussian_frontends.py`: bounded source/config/entrypoint inventory for the two fixed candidates.
- `audit_replica_frontend_environments.py`: import/config/CUDA/load audits without mapping.
- `qualify_replica_frontend_capabilities.py`: GT-pose, map-only, export, renderer, and metric-depth capability gates.
- `build_replica_mapping_input_contract.py`: exact pinhole intrinsics, coordinate convention, and four-frame round-trip proof.
- `freeze_replica_frontend_pilot_registry.py`: deterministic 30-location farthest-point registry with 60 mapping and 30 holdout frames.
- `build_replica_map_only_ingestion_order.py`: float64 MST and deterministic DFS mapping order.
- `freeze_frontend_pilot_configuration.py`: immutable frontend configuration contract, including no-tracking/no-pose-update assertions.
- `run_*_replica_smoke.py` and `run_*_replica_qualification_pilot.py`: serial task-owned launchers; each accepts only frozen inputs and writes task-owned outputs.
- `export_*_canonical_map.py`: no-filter canonical Gaussian exports.
- `build_common_gaussian_evaluator.py`, `evaluate_replica_frontend_geometry.py`, `audit_replica_frontend_map_structure.py`: shared rendering/metrics/map checks.
- `qualify_replica_frontend_safer_g0.py`: three identical static 256-point G0 passes, with no controller execution.
- `classify_replica_frontends.py`: the sole final-status/decision writer and compact report generator.
- `.gitignore`: excludes checkpoints, arrays, raw renders, logs, caches, and task-owned server outputs.

## Task 1: Freeze the source and input identities

**Files:**
- Create: `freeze_replica_mapping_input_identity.py`, `input_identity_summary.json`, `frontend_run_manifest.json`

- [ ] Verify PR #55 head with `gh pr view 55 --json headRefOid` and record the actual SHA.
- [ ] Hash every published metadata file and calculate the RGB, depth, content, and complete trees using `relative-path NUL size NUL SHA-256` rows in POSIX lexical order.
- [ ] Require 300 manifest rows, 300 distinct frame IDs, 300 RGB/depth disk pairs, 90/10 train/eval locations, 270/30 train/eval frames, and exact frozen SHA values.
- [ ] Atomically write `BLOCKED_BY_REPLICA_MAPPING_INPUT_IDENTITY_MISMATCH` on any discrepancy; do not create or launch frontend outputs.

Expected command: `python -B freeze_replica_mapping_input_identity.py --dataset /disk1/zlab/cross_dataset_assets/processed/replica/apartment_0.rendering_v3`.

## Task 2: Inventory the two assets and their immutable environments

**Files:**
- Create: `discover_replica_gaussian_frontends.py`, `audit_replica_frontend_environments.py`, `frontend_asset_inventory.json`, `frontend_environment_audit.json`

- [ ] Search only the protocol-bounded roots plus previously registered official archives; record absence instead of downloading substitutes.
- [ ] For each candidate record source path, source/archive identity, remote/branch/commit when available, dirty state, submodules, README/license, RGB-D loader, GT-pose/map-only/tracking controls, export/render entrypoints, and prior artifacts.
- [ ] Run import-only, config parse, dry adapter, existing CUDA-extension load, renderer import, and checkpoint/export import in the existing environment.
- [ ] Classify each environment as READY, REPAIRABLE, or UNAVAILABLE. Limit repairs to one task-owned wrapper or environment-variable correction and preserve initial failure logs.

Expected result: every reported frontend is either `FRONTEND_ENVIRONMENT_READY`, an explicitly bounded repairable case, or an asset/environment failure—not a surrogate method.

## Task 3: Freeze comparable RGB-D, pose, pilot, and order contracts

**Files:**
- Create: `qualify_replica_frontend_capabilities.py`, `build_replica_mapping_input_contract.py`, `freeze_replica_frontend_pilot_registry.py`, `build_replica_map_only_ingestion_order.py`, `freeze_frontend_pilot_configuration.py`
- Create: `frontend_capability_gate.json`, `replica_mapping_input_contract.json`, `replica_frontend_pilot_registry.json`, `replica_frontend_map_only_order.json`, `frontend_pilot_configuration_contract.json`

- [ ] Reconstruct PR #54's pinhole ray convention, calculate `fx`, `fy`, `cx`, and `cy`, and compare nine fixed rays.
- [ ] For four frozen frames prove metric depth backproject/reproject median error at most `1e-4` pixel and depth round-trip at most `1e-6` m, with translation ratio exactly one.
- [ ] Select 30 locations only from the 90 train locations using the specified SHA seed and deterministic float64 farthest-point rule.
- [ ] Construct the MST with deterministic hash tie breaks; use the DFS preorder and per-location yaw `0, -60` order. Reserve yaw `+60` solely as holdout.
- [ ] Freeze identical frame lists, intrinsics, poses, depth scale, seed, no tracking, no pose optimization, no Sim(3), and no scale fitting for both frontend launches.

Expected result: official eval usage remains zero and all run manifests remain `NOT_STARTED` until the contracts are present.

## Task 4: Freeze a shared evaluator before scientific results

**Files:**
- Create: `build_common_gaussian_evaluator.py`, `common_gaussian_evaluator_contract.json`

- [ ] Audit the prior common Gaussian evaluator and use it only if it reads both canonical export schemas.
- [ ] Otherwise implement a task-owned renderer with one fixed rasterization backend, depth definition, valid mask, near/far range, pixel-center convention, and deterministic settings.
- [ ] Reject method-native depth scores as a frontend-selection basis.

Expected command: `python -B build_common_gaussian_evaluator.py --contract replica_mapping_input_contract.json` and expected `COMMON_EVALUATOR_READY`.

## Task 5: Execute each frontend serially through smoke and qualification

**Files:**
- Create: `run_splatam_replica_smoke.py`, `run_gaussian_slam_replica_smoke.py`, `run_splatam_replica_qualification_pilot.py`, `run_gaussian_slam_replica_qualification_pilot.py`
- Create: `splatam_smoke_summary.json`, `gaussian_slam_smoke_summary.json`, `splatam_pilot_summary.json`, `gaussian_slam_pilot_summary.json`

- [ ] Launch only an asset/environment/capability/config-qualified frontend, on physical GPU 1 and never concurrently.
- [ ] Enforce smoke: 16 mapping plus 8 holdout frames, 30-minute cap, GT poses, zero tracking and pose updates, reloadable checkpoint, finite loss/map, nonempty map, export, and render.
- [ ] For each `SMOKE_PASS`, run precisely one 60-mapping/30-holdout qualification pilot with the 120-minute cap and frozen configuration.
- [ ] Preserve failed logs and allow a new output directory only for the single permitted infrastructure retry; do not retry scientific results.

Expected result: every non-authorized later stage says `NOT_AUTHORIZED_DUE_TO_<GATE>` rather than a synthetic pass.

## Task 6: Canonical export, shared geometry, map structure, and static SAFER G0

**Files:**
- Create: `export_splatam_canonical_map.py`, `export_gaussian_slam_canonical_map.py`, `evaluate_replica_frontend_geometry.py`, `audit_replica_frontend_map_structure.py`, `qualify_replica_frontend_safer_g0.py`
- Create: `splatam_canonical_export_summary.json`, `gaussian_slam_canonical_export_summary.json`, `splatam_geometry_evaluation.json`, `gaussian_slam_geometry_evaluation.json`, `frontend_geometry_comparison.json`, `splatam_map_structure_audit.json`, `gaussian_slam_map_structure_audit.json`, `splatam_safer_g0_summary.json`, `gaussian_slam_safer_g0_summary.json`

- [ ] Export only means, linear scales, WXYZ quaternions, opacities, and appearance/SH arrays; record all source and array identities without filtering or re-optimization.
- [ ] Evaluate both maps with the frozen common evaluator on exactly the 30 internal yaw `+60` holdouts using the same valid-pixel mask.
- [ ] Audit finite arrays, positive covariance, metric scale, and map structure.
- [ ] Query the same static 256-point G0 set three times per map at radius `0.015`; require finite `h`, gradients, Hessians, deterministic active Gaussians, symmetry at most `1e-5`, and no map mutation.

Expected result: qualification gates use only coverage, AbsRel, delta1, median-depth-ratio, nonfinite count, and static G0 compatibility stated by the protocol.

## Task 7: Validate, report, and publish compact evidence

**Files:**
- Create: `classify_replica_frontends.py`, `frontend_qualification_result.json`, `validation_result.json`, `downstream_handoff.json`, `REPORT_REPLICA_GAUSSIAN_MAPPING_FRONTEND_QUALIFICATION_V1.md`
- Create: `figures/frontend_stage_gate_summary.png`, `figures/pilot_location_selection.png`, `figures/pilot_mst_ingestion_order.png`, `figures/pilot_mapping_holdout_views.png`, `figures/geometry_absrel_per_frame.png`, `figures/geometry_delta1_per_frame.png`, `figures/depth_ratio_per_frame.png`, `figures/predicted_depth_coverage.png`, `figures/gaussian_count_and_map_size.png`, `figures/scale_distribution_comparison.png`, `figures/runtime_and_peak_memory.png`, `figures/safer_g0_query_summary.png`, `figures/frontend_qualification_decision.png`

- [ ] Validate all compact JSON files, compile every Python file, verify all prohibited execution counts are zero, and check GPU 1 for task-owned compute processes.
- [ ] Compute exactly one final status/decision/next task from the protocol’s four-case table.
- [ ] Stage only this tracked root, commit `test(reproduction): qualify Replica Gaussian mapping frontends`, push once, and create one Open Draft PR against `replica-rgbd-v3-render-validate-publish-v1`.

## Self-review

- [ ] Input tree and all frozen V3 metadata are checked before any frontend can launch.
- [ ] Both candidates retain independent outcomes; one failure does not suppress the other authorized pilot.
- [ ] Official eval, full 270-frame mapping, tracking, pose optimization, scale fitting, navigation, CBF, recovery, and TUM are all represented by explicit zero counts.
- [ ] No checkpoint, Gaussian array, raw render, cache, or complete log is added to Git.
