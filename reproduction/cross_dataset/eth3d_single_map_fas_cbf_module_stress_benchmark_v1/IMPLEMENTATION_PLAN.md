# ETH3D Single-Map FAS-CBF Module Stress Benchmark V1 Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Execute this plan task-by-task in the current session. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Train exactly one official 3DGS map from the frozen ETH3D TRAIN-only COLMAP input, then compare SAFER and four cumulative FAS-CBF module configurations on one frozen, method-independent 100-scenario registry.

**Architecture:** The Windows worktree stores only compact code, manifests, tables, figures, and reports. Large assets, source, environment, map, checkpoints, trajectories, and logs remain on `zlab-4090` in task-owned roots. Every stage writes atomic machine-readable evidence and the next stage verifies upstream identities before running.

**Tech Stack:** Python, official graphdeco-inria Gaussian Splatting at `54c035f7834b564019656c3e3fcc3646292f727d`, CUDA on physical GPU 1, NumPy/SciPy/Clarabel, Git/GitHub CLI, Matplotlib.

---

### Task 1: Freeze PR #79 and server inputs

**Files:**
- Create: `freeze_pr79_inputs.py`
- Create: `input_freeze/pr79_and_data_identity.json`

- [x] Verify PR #79 is Open Draft, mergeable, unmerged, and at `4694a7cbfa062a53ac270c1c1c5654a2d1b5f166`.
- [x] Hash the PR #79 report, compact artifact manifest, Protocol V2, split, TRAIN-only COLMAP tree, reference surface, contracts, and DATA_ROOT identity.
- [x] Require training/environment/map/controller counts to be zero before this task.
- [x] Run `python -B freeze_pr79_inputs.py --server-root /disk1/zlab/maintenance_records/eth3d_single_map_fas_cbf_module_stress_benchmark_v1` and require `PR79_INPUT_FREEZE_PASS`.

### Task 2: Provision the isolated official 3DGS source and environment

**Files:**
- Create: `qualify_official_3dgs_environment.py`
- Create: `environment/environment_identity.json`
- Create: `environment/explicit_packages.txt`

- [x] Clone or reconstruct the official source at the frozen commit into `/disk1/zlab/source_snapshots/official_gaussian_splatting_54c035f` and verify detached HEAD, tree, submodules, and license.
- [x] Create `/disk1/zlab/conda_envs/eth3d_official_3dgs_v1` without modifying any existing environment.
- [x] Install/build only source-compatible dependencies and record an explicit package list and CUDA-extension identities.
- [x] Run import, CUDA rasterizer, simple render, COLMAP loader, one optimization step, save/load, and GPU-cleanup probes.
- [x] Require `OFFICIAL_3DGS_ENVIRONMENT_QUALIFIED` before smoke training.

### Task 3: Build the frozen training adapter and run smoke

**Files:**
- Create: `build_official_3dgs_train_input.py`
- Create: `run_official_3dgs_smoke.py`
- Create: `smoke/smoke_result.json`
- Create: `audit_training_reference_access.py`

- [x] Build only symlinks/adapter metadata from frozen `TRAIN_INPUT_ROOT`; never copy or modify the 9 archives or extracted dataset.
- [x] Deny reads from HELDOUT, GUARD, DSLR, depth, scan, mesh, and occlusion roots during training.
- [x] Run the frozen seed `20260804` for exactly 500 smoke iterations on physical GPU 1.
- [x] Allow engineering-only smoke repair and repeat, while keeping the formal command/config unchanged.
- [x] Require terminal smoke success, finite loss, produced point cloud, zero reference reads, and no remaining GPU process.

### Task 4: Execute the only formal 30K map attempt

**Files:**
- Create: `run_official_3dgs_formal_once.py`
- Create: `formal_map/formal_attempt_identity.json`
- Create: `formal_map/formal_result.json`

- [x] Freeze the exact official default loss/densification command with seed `20260804`, iterations `30000`, and checkpoints `7000,15000,30000`.
- [x] Atomically preregister `formal_attempt_count=1`, then start exactly one formal process.
- [x] Monitor the same process; infrastructure interruption may resume the same checkpoint, but scientific failure must not reinitialize or start attempt 2.
- [x] Require iteration 30000, normal exit, finite loss, reference/GT-depth reads equal zero, and capture runtime, VRAM, and Gaussian count.

### Task 5: Export and qualify the learned map

**Files:**
- Create: `export_canonical_gaussians.py`
- Create: `validate_canonical_export.py`
- Create: `evaluate_minimum_map_viability.py`
- Create: `build_safer_map_adapter.py`
- Create: `canonical_export/canonical_validation.json`
- Create: `canonical_export/manifest.json`
- Create: `minimum_map_viability.json`

- [x] Export unfiltered iteration-30000 means, scales, rotations, opacity, and SH/color in the frozen metric frame.
- [x] Produce three fresh exports and require identical tree SHA-256, finite arrays, positive scales, valid rotations, and no pruning/filtering.
- [x] Run native render, heldout/cross-view diagnostics, SAFER static query/G0, and independent reference-oracle probes.
- [x] Treat PSNR/SSIM/LPIPS, depth, risk-coverage, and ETH3D surface metrics as descriptive only.
- [x] Fail only on the catastrophic minimum-viability conditions defined by the protocol.

### Task 6: Inventory and unit-test the cumulative method matrix

**Files:**
- Create: `inventory_fas_cbf_modules.py`
- Create: `eth3d_controller_core.py`
- Create: `test_start_safe.py`
- Create: `test_feasibility_aware.py`
- Create: `test_discrete_time_verifier.py`
- Create: `test_predictive_recovery.py`
- Create: `method_inventory/module_inventory.json`

- [x] Preserve the SAFER baseline core SHA and import/copy only auditable task-specific adapters.
- [x] Freeze `M0 SAFER_BASELINE`, `M1 FAS_START_SAFE_ONLY`, `M2 +FEASIBILITY_AWARE`, `M3 +DISCRETE_TIME_VERIFICATION`, and `M4 FULL_FAS_CBF`.
- [x] Run the specified Start-Safe, feasibility-aware, exact segment, predictive recovery, fairness, and no-reference-leak unit tests.
- [x] Stop with `BLOCKED_BY_FAS_CBF_MODULE_IMPLEMENTATION_GAP` if two or more core modules are genuinely absent.

### Task 7: Freeze the method-independent stress registry and smoke matrix

**Files:**
- Create: `generate_eth3d_fas_cbf_stress_scenarios.py`
- Create: `validate_scenario_registry.py`
- Create: `run_controller_smoke_matrix.py`
- Create: `scenario_generation/scenario_registry.json`
- Create: `smoke_controller/run_manifest.json`

- [x] Generate G0-G4 from the frozen map, reference oracle, UNKNOWN contract, robot/dynamics, nominal controller, and PR #79 node pool without reading rollout metrics.
- [x] Target 20 scenarios per group, allow 10-19, and mark total below 70 as activation-insufficient without changing map or dataset.
- [x] Freeze registry and config SHA before any controller run.
- [x] Run exactly 50 smoke cases (5 methods x 5 groups x 2) to validate interfaces and activation; never tune from smoke outcomes.

### Task 8: Run the formal paired benchmark and analysis

**Files:**
- Create: `run_formal_paired_controller_benchmark.py`
- Create: `analyze_paired_module_effects.py`
- Create: `analyze_smoothness_diagnostics.py`
- Create: `select_final_decision.py`

- [x] Run every method on every frozen scenario serially with identical map, oracle, dynamics, nominal inputs, bounds, horizon, max steps, timeout, UNKNOWN policy, and logging.
- [x] Preserve all terminal results and failures; never delete or replace a scenario.
- [x] Analyze at scenario grain with paired differences, win/tie/loss, scenario bootstrap 95% CIs, collision contingency, progress, feasibility, activation, and runtime.
- [x] Classify each module as SUPPORTED, PROMISING, NOT_SUPPORTED, REGRESSION, or INACTIVE using only preregistered rules.
- [x] Record smoothness, map-confidence, and residual-budget diagnostics without changing the formal methods.

### Task 9: Generate compact evidence, validate, and publish

**Files:**
- Create: `formal_controller/run_manifest.json`
- Create: `report/validation_result.json`
- Create: `report/downstream_handoff.json`
- Create: `report/REPORT_TRAIN_ONE_ETH3D_3DGS_MAP_AND_RUN_FAS_CBF_MODULE_STRESS_BENCHMARK_V1.md`
- Create: `figures/*.png`

- [x] Generate all 25 required figures with honest scales, source metadata, and adjacent report interpretation.
- [x] Select exactly one protocol Case A-D and state `FINAL_STATUS`, `FINAL_DECISION`, unresolved evidence, and the only next task.
- [x] Independently recompute high-impact counts, paired summaries, collision regressions, execution boundaries, and artifact hashes.
- [x] Copy back only the compact task root; exclude raw assets, environment, source, checkpoints, map arrays, dense renders, credentials, trajectories, and large logs.
- [x] Stage only `reproduction/cross_dataset/eth3d_single_map_fas_cbf_module_stress_benchmark_v1/`, commit with the authorized message, push once, and create one Open Draft PR against `eth3d-delivery-area-provision-7zz-resume-assets-v1`.

## Self-review

- Spec coverage: all source/environment, training, export, viability, module, registry, smoke, formal, statistics, claim, report, execution-count, and Git requirements map to Tasks 1-9.
- Placeholder scan: no deferred implementation or unspecified test step remains.
- Identity consistency: all stages use one dataset, scene, split, frontend, formal seed/map, registry, nominal controller, physical GPU, and reference oracle.
- Stop discipline: source/data drift, TRAIN reference leakage, unfair pairing, SAFER-core mutation, catastrophic map failure, and module regressions remain fail-closed.
