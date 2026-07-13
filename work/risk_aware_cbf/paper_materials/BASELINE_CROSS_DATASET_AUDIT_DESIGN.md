# SAFER Baseline Cross-Dataset G0-G1 Implementation Plan

> **For agentic workers:** Execute the checked stages in order. Do not enable any method-improvement module or modify official SAFER source.

**Goal:** Audit whether the unmodified SAFER baseline can load independently sourced Gaussian-splat assets and complete a bounded, preregistered smoke protocol.

**Architecture:** The audit is a wrapper-only pipeline. G0 inventories local assets and freezes a source-aware selection before any navigation. G1 checks loader/query, scale, navigation-volume, and parameter-transfer contracts, then runs at most one reference scene plus three independent scenes through the original loader, CBF-QP, controller, and dynamics.

**Tech stack:** Python 3, CSV/JSON/Markdown standard library, NumPy, PyTorch, existing SAFER `GSplatLoader`, `CBF`, and `DoubleIntegrator`.

---

### Task 1: Establish the isolated baseline

**Files:**
- Read: `reproduction/scripts/run_official_runpy_smoke.py`
- Read only: `cbf/`, `splat/`, `ellipsoids/`, `dynamics/`, `run.py`

- [x] Confirm the branch is `safer-baseline-cross-dataset-g0-g1` at `fc3e942c1ab957c910785fdeefae57f537ef3a9f`.
- [x] Confirm the baseline command path is `GSplatLoader -> CBF.solve_QP -> double_integrator_dynamics` with the official nominal controller and `dt=0.05`.

### Task 2: G0 asset and provenance audit

**Files:**
- Create: `work/risk_aware_cbf/scripts/audit_cross_dataset_scene_assets.py`
- Create: `work/risk_aware_cbf/results/safer_baseline_cross_dataset_g0_g1/{README.md,dataset_source_inventory.csv,dataset_selection_score.csv,selected_scene_preregistration.csv,asset_search_summary.csv,source_provenance_notes.md,dataset_acquisition_plan.md}`

- [ ] Search only the predeclared roots, skipping dependency, Git, and trace directories.
- [ ] Mark provenance unverifiable unless source and checkpoint provenance are explicit; folder names are not evidence.
- [ ] Score only pre-execution metadata and select no more than three independent Tier-2/Tier-3 scenes.

### Task 3: G1 compatibility gates and pair admission

**Files:**
- Create: `work/risk_aware_cbf/scripts/validate_cross_dataset_gsplat_compatibility.py`
- Create: `work/risk_aware_cbf/scripts/generate_cross_dataset_baseline_pairs.py`
- Create optional: `work/risk_aware_cbf/scripts/cross_dataset_scene_adapters/<candidate_id>.py`

- [ ] Load only preregistered scenes and preserve the official loader/query behavior.
- [ ] Require a source-justified scale transform and a declared navigation volume before smoke execution.
- [ ] Generate exactly 20 seeded candidate pairs per compatible scene; record all admissions and use the first three admissible IDs.

### Task 4: Parity and bounded original-baseline smoke

**Files:**
- Create: `work/risk_aware_cbf/scripts/run_safer_baseline_cross_dataset_smoke.py`

- [ ] Compare three fixed reference pairs against `reproduction/scripts/run_official_runpy_smoke.py` for 50 steps before cross-dataset smoke.
- [ ] Stop all cross-dataset execution if parity fails.
- [ ] Run at most three preregistered admissible pairs per scene and at most twelve navigation runs total.
- [ ] Treat H1/H2/H3 as non-intervening diagnostics; do not retain per-step or trajectory artifacts.

### Task 5: Compact analysis and claim-bound reporting

**Files:**
- Create: `work/risk_aware_cbf/scripts/analyze_safer_baseline_cross_dataset_g0_g1.py`
- Create: `work/risk_aware_cbf/REPORT_SAFER_BASELINE_CROSS_DATASET_G0_G1.md`
- Create: `work/risk_aware_cbf/notes/NEXT_STEP_AFTER_BASELINE_CROSS_DATASET_G0_G1.md`
- Modify: `REPRODUCIBILITY_MANIFEST.md`

- [ ] Aggregate only compact CSV/JSON summaries.
- [ ] Keep internal GSplat `h` collisions separate from independent geometry collisions.
- [ ] Use `blocked_by_cross_dataset_asset_availability` when no eligible independent asset exists; do not infer a mechanism failure.

### Pre-commit checks

- [ ] Run `python -m compileall work/risk_aware_cbf/scripts/audit_cross_dataset_scene_assets.py work/risk_aware_cbf/scripts/validate_cross_dataset_gsplat_compatibility.py work/risk_aware_cbf/scripts/generate_cross_dataset_baseline_pairs.py work/risk_aware_cbf/scripts/run_safer_baseline_cross_dataset_smoke.py work/risk_aware_cbf/scripts/analyze_safer_baseline_cross_dataset_g0_g1.py`.
- [ ] Run `git diff --check` and verify no forbidden source path changed.
- [ ] Verify no raw trace, dataset, checkpoint, image, or JSONL is staged.
