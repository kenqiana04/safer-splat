# TUM Tuned Surface Geometry Ablation V1 Implementation Plan

> **For agentic workers:** Execute these checked steps sequentially in this isolated worktree. Preserve every failed nonformal attempt; never resume a failed run.

**Goal:** Evaluate only the deterministic RGB-D surface-oriented initializer and metric point-to-plane loss against frozen tuned baseline `C_L050_K2000_B020`.

**Architecture:** Recover the exact PR #37 source snapshot, produce task-owned train-only prior assets, and create four independently materialized source variants. Gate all runs on identity, minimal source difference, unit tests, and 100-step smoke before the prescribed 6K screens, optional single fresh 10K, static audit, and publication.

**Tech Stack:** Git raw objects, Python 3.10, NumPy/SciPy cKDTree, PyTorch/Nerfstudio 1.1.5, gsplat overlay, SSH.

---

### Task 1: Freeze inputs and source

**Files:**
- Create: `input_identity_summary.json`, `verify_tuned_surface_inputs.py`, `restore_tuned_baseline_source.py`

- [ ] Verify PR #37 head and every specified immutable SHA on the server.
- [ ] Restore the exact tuned source only from the PR #37 Git object, calculate a raw-blob manifest, and reject any mismatch.
- [ ] Record the exact checkpoint/config paths discovered from PR #37 evidence rather than guessing them.

### Task 2: Build deterministic task-owned assets

**Files:**
- Create: `build_surface_oriented_prior.py`, `build_tum_surface_targets.py`, `surface_prior_summary.json`, `train_surface_target_summary.json`

- [ ] Verify SciPy/cKDTree without installation.
- [ ] Build the fixed k=17 (16 non-self) PCA prior twice and require byte/array identity while preserving seed xyz/rgb/order/count.
- [ ] Build train-only targets twice from exactly the 240 frozen train frames, then verify that no eval frame or eval path enters the train manifest.

### Task 3: Materialize and prove the four variants

**Files:**
- Create: `build_tuned_surface_variants.py`, `verify_tuned_surface_candidate_diffs.py`, `candidate_matrix.json`, `candidate_source_diff_gate.json`

- [ ] Materialize byte-identical S0, prior-only S1, loss-only S2, and combined S3 source trees.
- [ ] Permit only quaternion/log-scale injection for S1 and only target-backed point-to-plane loss for S2.
- [ ] Run byte, AST, import, function, call-graph, and frozen-config checks before allowing a training command.

### Task 4: Test and smoke

**Files:**
- Create: `test_tuned_surface_geometry_ablation.py`, `launch_tuned_surface_candidate.py`, `smoke_validation.json`

- [ ] Test identity preservation, quaternion/scale contracts, train-only targets, differentiable loss, and absence of forbidden changes.
- [ ] Run S0, S1, S2, S3 in order for exactly 100 nonformal iterations in fresh task-owned outputs.
- [ ] Require step 99, finite loss, applicable surface-loss presence, optimizer update, and GPU/process release.

### Task 5: Execute screens and select once

**Files:**
- Create: `evaluate_tuned_surface_geometry.py`, `analyze_tuned_surface_factor_effects.py`, `baseline_reproducibility.json`, `candidate_6000_comparison.json`, `tuned_surface_factor_analysis.json`, `selected_candidate.json`

- [ ] Run S0 first and compare with PR #37 archived 6K metrics under the registered tolerances.
- [ ] Run S1, S2, S3 exactly once each for 6000 nonformal iterations and evaluate every candidate over the fixed 60 frames.
- [ ] Classify candidates with the registered depth/surface screen and fixed ranking; do not run 10K when none qualifies.

### Task 6: Validate final candidate and publish

**Files:**
- Create: `final_candidate_summary.json`, `final_surface_metrics.json`, `static_safer_query_summary.json`, `geometry_gate_result.json`, `validation_result.json`, `downstream_handoff.json`, `REPORT_TUM_TUNED_SURFACE_GEOMETRY_ABLATION_V1.md`

- [ ] If and only if one non-S0 screen qualifies, run one new 10000-step output and perform the specified fixed60, surface, Gaussian, static-query, gradient, continuity, immutability, and G0 checks.
- [ ] Copy only the final Markdown report to the Desktop report folder and verify its SHA-256.
- [ ] Stage only this task root, commit, push, and open one Draft PR based on PR #37 without starting a formal training or G1 action.
