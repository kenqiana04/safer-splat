# TUM SplaTAM DT-Triggered V4-C Recovery V1 Implementation Plan

> **For agentic workers:** execute inline with the frozen PR #47/PR #48 evidence; do not alter either upstream branch or server checkout.

**Goal:** Test the recovered V4-C mechanism only when a frozen H3 float32 full-map forecast predicts strict overlap, then certify every boundary outcome offline in float64.

**Architecture:** Task-owned Python adapters import the immutable server checkout, preserve its CBF/QP and V4-C candidate/evaluation functions, and write all large traces only under the maintenance root.  Compact JSON summaries capture source identity, trigger semantics, paired results, and classification for Git.

**Tech Stack:** Python 3, PyTorch CUDA on physical GPU 1, NumPy, frozen SAFER source, canonical SplaTAM arrays, JSON/CSV, GitHub Draft PR.

---

### Task 1: Freeze identities and protocol

**Files:** `recover_frozen_v4c_identity.py`, `freeze_dt_strict_trigger_contract.py`, `input_identity_summary.json`, `v4c_recovery_identity.json`, `dt_trigger_contract.json`.

- [ ] Verify the server checkout and frozen blobs before any rollout.
- [ ] Record V4-C commit/blob/SHA, H=3 candidate generation, cost, bounds, first-control execution, and fallback semantics.
- [ ] Freeze `margin_warning = min_h3 < 0.0005` as log-only and `strict_trigger = current_h > 0 and min_h3 < 0` as the sole recovery entry condition.

### Task 2: Build immutable-data adapters and registry

**Files:** `build_heldout_pair_registry.py`, `run_dt_triggered_v4c_rollout.py`, `heldout_pair_registry.json`.

- [ ] Load only canonical map arrays and frozen transforms into a task-owned loader; retain original CBF/QP and explicit-Euler update.
- [ ] Enumerate safe transform-frame pairs in original order, exclude 0→50, and freeze the first three satisfying safety, separation, finite, and bbox predicates.
- [ ] Implement baseline and strict-triggered arms with full per-step maintenance logs, 90-minute watchdog, no Start-Safe, no Risk-Aware, and no Top-K adaptation.

### Task 3: Execute and certify development intervention

**Files:** `development_pair_summary.json`, `certify_recovery_float64_boundaries.py`, `development_float64_certification.json`.

- [ ] Run only the strict-triggered intervention for 0→50; cite PR #47/48 for the two frozen non-intervention arms.
- [ ] Certify trigger neighborhoods, every episode boundary, negative float32 state, minimum, and terminal state with independent float64 KKT bisection and Newton+bisection.
- [ ] Preserve the distinction between float32 stop proxy and robust geometric classification.

### Task 4: Execute fixed held-out paired diagnostics and classify

**Files:** `heldout_baseline_summary.json`, `heldout_intervention_summary.json`, `compare_baseline_recovery_pairs.py`, `paired_comparison_summary.json`, `classify_dt_triggered_recovery_result.py`, `validation_result.json`, `downstream_handoff.json`.

- [ ] Run exactly baseline and intervention once for each pre-frozen held-out pair; stop additional expansion if intervention creates a new robust overlap.
- [ ] Apply the same float64 certification set to intervention boundaries and report paired progress, trigger, runtime, and overlap differences.
- [ ] Classify the outcome without generalizing a four-pair proof-of-mechanism into a benchmark conclusion.

### Task 5: Validate, report, and publish

**Files:** `REPORT_TUM_SPLATAM_DT_TRIGGERED_V4C_RECOVERY_V1.md` plus all compact summaries above.

- [ ] Validate JSON and Python syntax, copy the report to the Desktop REPORT directory, and record its SHA-256.
- [ ] Stage only this tracked root, commit without amend, push the new branch, and open one Draft PR against `tum-splatam-g1-boundary-dt-forensics-v1`.
