# TUM SplaTAM Global Progress-Limitation Offline Audit V1 Implementation Plan

> **For agentic workers:** Execute inline in this isolated branch. Never launch, resume, replay, or tune a scientific rollout; all analysis reads existing evidence and writes only below AUDIT_ROOT.

**Goal:** Normalize every complete existing TUM Original-SAFER and strict-DT-triggered V4-C trajectory, attribute its progress limitation offline, compare matched pairs, and make one evidence-bounded paired20 resume recommendation.

**Architecture:** Task-owned inventory code verifies immutable source identities and locates terminal summaries/step logs from sources A--D. Deterministic normalization and metrics programs consume only those saved records; independent aggregation renders compact evidence and figures without modifying a source root or invoking CBF/QP/V4-C execution.

**Tech Stack:** Python 3, JSON/JSONL, NumPy, Matplotlib, SHA-256, existing server maintenance evidence, Git/GitHub CLI.

---

### Task 1: Freeze evidence identities and inventory complete trajectories

**Files:**
- Create: `reproduction/cross_dataset/tum_splatam_global_progress_limitation_audit_v1/inventory_completed_trajectories.py`
- Create: `reproduction/cross_dataset/tum_splatam_global_progress_limitation_audit_v1/input_identity_summary.json`
- Create: `reproduction/cross_dataset/tum_splatam_global_progress_limitation_audit_v1/trajectory_inventory_summary.json`

- [ ] Verify PR #47/#48/#49 identities, map/transforms identities, frozen dynamics/CBF/V4-C/trigger contract, and paused paired20 manifest SHA/state without writing under sources A--D.
- [ ] Discover only records containing both an unambiguous terminal summary and complete existing step/control log; canonicalize duplicates with pair, arm, state/control SHA, and source identity.
- [ ] Test inventory uniqueness, expected minimum coverage of ten trajectories, and paused-state invariants `2/2/0` with no sequence-3 summary or step file.

### Task 2: Normalize saved logs and verify progress semantics

**Files:**
- Create: `reproduction/cross_dataset/tum_splatam_global_progress_limitation_audit_v1/normalize_existing_trajectory_logs.py`
- Create: `reproduction/cross_dataset/tum_splatam_global_progress_limitation_audit_v1/verify_progress_semantics.py`
- Create: `reproduction/cross_dataset/tum_splatam_global_progress_limitation_audit_v1/normalization_summary.json`
- Create: `reproduction/cross_dataset/tum_splatam_global_progress_limitation_audit_v1/progress_semantics_contract.json`
- Server-only: `$AUDIT_ROOT/normalized/*.jsonl`

- [ ] Convert fields from saved rows into a single schema, preserving null and provenance for unrecoverable values; derive only saved-state quantities using `p_next=p+dt*v` and `v_next=v+dt*u_executed` when reconstruction is necessary.
- [ ] Compare official reported progress with geometric progress `(initial_distance-distance_k)/initial_distance` for every usable trajectory and document any non-equivalence.
- [ ] Test that normalized IDs are unique, no absent field is replaced with zero, and no normalizer imports/calls an online controller, CBF, QP, or V4-C executor.

### Task 3: Compute fixed per-trajectory, stall, attribution, and oscillation diagnostics

**Files:**
- Create: `reproduction/cross_dataset/tum_splatam_global_progress_limitation_audit_v1/compute_per_trajectory_progress_metrics.py`
- Create: `reproduction/cross_dataset/tum_splatam_global_progress_limitation_audit_v1/detect_stall_onset.py`
- Create: `reproduction/cross_dataset/tum_splatam_global_progress_limitation_audit_v1/analyze_controller_cbf_recovery_attribution.py`
- Create: `reproduction/cross_dataset/tum_splatam_global_progress_limitation_audit_v1/analyze_trajectory_oscillation.py`
- Create: `reproduction/cross_dataset/tum_splatam_global_progress_limitation_audit_v1/per_trajectory_metrics_summary.json`
- Create: `reproduction/cross_dataset/tum_splatam_global_progress_limitation_audit_v1/stall_onset_summary.json`
- Create: `reproduction/cross_dataset/tum_splatam_global_progress_limitation_audit_v1/controller_cbf_recovery_attribution.json`
- Create: `reproduction/cross_dataset/tum_splatam_global_progress_limitation_audit_v1/oscillation_diagnosis.json`
- Create: `reproduction/cross_dataset/tum_splatam_global_progress_limitation_audit_v1/trajectory_progress_classifications.json`

- [ ] Derive the prescribed distance/progress, radial-control, control-correction, safety-boundary, recovery, path, and 25/50/100/200-step metrics from normalized records.
- [ ] Apply the fixed W=100 three-consecutive-window stall predicate and fixed classification criteria; return `INSUFFICIENT_LOG_EVIDENCE` rather than substituting values.
- [ ] Test the classifications against synthetic raw arrays representing proxy stop, horizon progression, CBF suppression, oscillation, recovery-preserved limitation, and trigger-neutral equivalence.

### Task 4: Compare complete pairs and aggregate global root causes

**Files:**
- Create: `reproduction/cross_dataset/tum_splatam_global_progress_limitation_audit_v1/compare_paired_progress.py`
- Create: `reproduction/cross_dataset/tum_splatam_global_progress_limitation_audit_v1/aggregate_global_progress_causes.py`
- Create: `reproduction/cross_dataset/tum_splatam_global_progress_limitation_audit_v1/decide_paired20_resume_gate.py`
- Create: `reproduction/cross_dataset/tum_splatam_global_progress_limitation_audit_v1/paired_progress_comparison.json`
- Create: `reproduction/cross_dataset/tum_splatam_global_progress_limitation_audit_v1/global_progress_root_cause.json`
- Create: `reproduction/cross_dataset/tum_splatam_global_progress_limitation_audit_v1/paired20_resume_decision.json`

- [ ] Match only complete baseline/intervention pair identities; verify state/control hash equality for untriggered pairs and distinguish float32 proxy avoidance from certified robust-overlap avoidance.
- [ ] Aggregate frozen cohorts, select one global primary cause and at most two secondary causes, list pair-specific exceptions, and apply only the specified A--D paired20 decision gate.
- [ ] Test that no unpaired or shadow-only record contributes to paired endpoints and that a missing log cannot produce a resume recommendation stronger than evidence allows.

### Task 5: Render, validate, report, and publish one Draft PR

**Files:**
- Create: `reproduction/cross_dataset/tum_splatam_global_progress_limitation_audit_v1/render_global_progress_figures.py`
- Create: `reproduction/cross_dataset/tum_splatam_global_progress_limitation_audit_v1/validation_result.json`
- Create: `reproduction/cross_dataset/tum_splatam_global_progress_limitation_audit_v1/downstream_handoff.json`
- Create: `reproduction/cross_dataset/tum_splatam_global_progress_limitation_audit_v1/REPORT_TUM_SPLATAM_GLOBAL_PROGRESS_LIMITATION_AUDIT_V1.md`

- [ ] Render raw-plus-optional-rolling-mean requested figures, retaining bulk normalized/per-step data only on AUDIT_ROOT.
- [ ] Recheck source identities, paused manifest SHA/state, no sequence-3 terminal/step file, no new trajectory directory, Python/JSON validity, unique IDs, and zero online QP/V4-C/scientific execution count.
- [ ] Copy only the report to `C:\\Users\\zlab\\Desktop\\REPORT\\`, stage only this audit root, commit the specified message, push the isolated branch, and open one Draft PR against PR #49's branch.

## Self-review

- Every requested identity, inventory, normalization, metric, stall, attribution, oscillation, paired, aggregate, decision, figure, report, validation, and Git artifact is covered.
- No task creates a new state, calls CBF/QP/V4-C, resumes paired20, edits source evidence, or hides the scheduler-race boundary.
- All safety claims distinguish float32 proxy stops from existing float64 certification and all navigation claims distinguish safety from goal completion.
