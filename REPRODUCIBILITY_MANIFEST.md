# Reproducibility Manifest

This manifest audits the current GitHub snapshot of `kenqiana04/safer-splat` for a paper-code release branch.

## Release Scope

- Repository base branch: `master`
- Base commit audited: `d77a063`
- Clean branch prepared from that base: `paper-code-release-clean`
- Primary experiment area: `work/risk_aware_cbf/`

This branch does not add large raw traces. It only adds release-facing tracking rules, placeholder directories, and this manifest.

## Tracking Policy

Track:

- paper reports under `work/risk_aware_cbf/`
- lightweight reproduction scripts under `work/risk_aware_cbf/scripts/`
- compact summary or metric artifacts under `work/risk_aware_cbf/results/`
- compact aggregate metrics under `work/risk_aware_cbf/metrics/`
- figures, notes, and paper-material markdown already present in the GitHub snapshot

Do not track:

- raw JSONL traces
- full per-step dumps
- full trial CSV dumps
- active-constraint dumps
- full trajectory samples
- bulky generated experiment outputs

## Current Snapshot Summary

The audited GitHub snapshot currently tracks:

- 50 risk-aware CBF report markdown files
- 166 files under `work/risk_aware_cbf/notes/`
- 32 files under `work/risk_aware_cbf/figures/`
- 55 files under `work/risk_aware_cbf/paper_materials/`

The audited snapshot does not currently track the concrete Python scripts or result summary files referenced by several reports. This branch therefore adds trackable directories and `.gitignore` exceptions, but it does not fabricate missing scripts or summary results.

## Directory Tracking Status

| Path | Status | Notes |
|---|---|---|
| `work/risk_aware_cbf/scripts/` | trackable | Added README and `.gitkeep`; `.gitignore` now allows recursive tracking. |
| `work/risk_aware_cbf/results/` | trackable for summaries | Added README and `.gitkeep`; `.gitignore` allows summaries/metrics/markdown and keeps raw traces ignored. |
| `work/risk_aware_cbf/metrics/` | trackable | Added README and `.gitkeep` for compact aggregate metrics. |

## Report Artifact Matrix

Status meanings:

- `yes`: every referenced artifact in that category is tracked in this GitHub snapshot.
- `no`: the report references artifacts in that category, but none of those referenced artifacts are tracked.
- `partial`: some, but not all, referenced artifacts in that category are tracked.
- `N/A`: the report does not explicitly reference that category.

| Report | Scripts | Summary CSV/MD | Metrics JSON | Notes/Figures |
|---|---|---|---|---|
| `REPORT_ADAPTIVE_V1_BALANCED_FLIGHT20_OFFLINE_REPLAY.md` | N/A | N/A | N/A | N/A |
| `REPORT_ADAPTIVE_V1_BUDGETING_PILOT.md` | N/A | N/A | N/A | N/A |
| `REPORT_ADAPTIVE_V1_CLOSED_LOOP_SMOKE.md` | N/A | N/A | N/A | N/A |
| `REPORT_ADAPTIVE_V1_FLIGHT20_CLOSED_LOOP.md` | N/A | N/A | N/A | N/A |
| `REPORT_ADAPTIVE_V1_TARGETED_DT_RISK_CLOSED_LOOP.md` | N/A | N/A | N/A | N/A |
| `REPORT_BASELINE_DETAILED_LOGGING.md` | no | no | no | yes |
| `REPORT_DISCRETE_TIME_VERIFICATION_CONSOLIDATION.md` | N/A | no | N/A | N/A |
| `REPORT_FAS_CBF_NEXT_STAGE_SUMMARY.md` | N/A | N/A | N/A | N/A |
| `REPORT_FC_AWARE_HEADING_SHADOW_AUDIT.md` | N/A | no | N/A | N/A |
| `REPORT_FC_AWARE_V1_CAPPED_CLOSED_LOOP_SMOKE.md` | N/A | N/A | N/A | N/A |
| `REPORT_FC_AWARE_V1_EXACT_LOGGING_FEASIBILITY.md` | N/A | no | no | N/A |
| `REPORT_FC_AWARE_V1_EXACT_RECALL_AUDIT.md` | N/A | N/A | N/A | N/A |
| `REPORT_FC_AWARE_V1_FLIGHT20.md` | N/A | N/A | N/A | N/A |
| `REPORT_FC_AWARE_V1_FLIGHT20_STOP_REASON_RECONCILIATION.md` | N/A | N/A | N/A | N/A |
| `REPORT_FC_AWARE_V1_PERCANDIDATE_RECALL_AUDIT.md` | N/A | no | no | N/A |
| `REPORT_FC_AWARE_V1_TARGETED_EXTENSION.md` | N/A | N/A | N/A | N/A |
| `REPORT_FLIGHT_TRIAL57_DIAGNOSIS.md` | N/A | N/A | N/A | N/A |
| `REPORT_FORCED_CANDIDATE_DOMINANCE.md` | no | N/A | N/A | N/A |
| `REPORT_MPC_STYLE_RECOVERY_FAILURE_DIAGNOSIS.md` | N/A | N/A | N/A | N/A |
| `REPORT_MPC_STYLE_RECOVERY_TARGETED_PILOT.md` | no | no | no | N/A |
| `REPORT_RISK_AWARE_CBF_PREPARATION.md` | N/A | no | N/A | yes |
| `REPORT_RISK_AWARE_TOPK_V0.md` | no | no | N/A | yes |
| `REPORT_RISK_AWARE_TOPK_V0_100_AND_ABLATION.md` | no | no | N/A | yes |
| `REPORT_RISK_AWARE_V1_100_TRIAL.md` | N/A | N/A | N/A | N/A |
| `REPORT_RISK_AWARE_V1_ABLATION.md` | N/A | no | N/A | N/A |
| `REPORT_RISK_AWARE_V1_BEST_CONFIG_100_TRIAL.md` | N/A | N/A | N/A | N/A |
| `REPORT_RISK_AWARE_V1_FLIGHT_100_TRIAL.md` | N/A | N/A | N/A | N/A |
| `REPORT_RISK_AWARE_V1_PRE_CBF.md` | N/A | N/A | N/A | N/A |
| `REPORT_RISK_AWARE_V1_SECOND_SCENE_FLIGHT.md` | N/A | N/A | N/A | N/A |
| `REPORT_RISK_AWARE_V2_TRIAL57.md` | N/A | N/A | N/A | N/A |
| `REPORT_SAFER_BASELINE_NAVIGATION_STACK_AUDIT.md` | no | no | N/A | N/A |
| `REPORT_STARTGUARD_FLIGHT100.md` | N/A | N/A | N/A | N/A |
| `REPORT_STARTGUARD_TRIAL57.md` | N/A | N/A | N/A | N/A |
| `REPORT_SYNTHETIC_INITIAL_UNSAFE_STRESS_TEST.md` | N/A | N/A | N/A | N/A |
| `REPORT_V4A_ACTIVE_PROJECTION_DT_AUDIT.md` | N/A | N/A | N/A | N/A |
| `REPORT_V4B_CORRECTIVE_DT_FILTER.md` | N/A | N/A | N/A | N/A |
| `REPORT_V4C_FLIGHT100_VALIDATION.md` | N/A | N/A | N/A | N/A |
| `REPORT_V4C_HSTEP_PREDICTIVE_RECOVERY.md` | yes | no | N/A | yes |
| `REPORT_V4C_RUNTIME_TUNING_PILOT.md` | N/A | N/A | N/A | N/A |
| `REPORT_V4C_TUNED_FULL100_VALIDATION.md` | N/A | N/A | N/A | N/A |
| `REPORT_VANS_SHADOW_FEASIBILITY_AUDIT.md` | yes | yes | yes | yes |

## Release Gap List

The following reports explicitly reference scripts or summary/metrics artifacts that are not tracked in the current GitHub snapshot:

- `REPORT_BASELINE_DETAILED_LOGGING.md`
- `REPORT_DISCRETE_TIME_VERIFICATION_CONSOLIDATION.md`
- `REPORT_FC_AWARE_HEADING_SHADOW_AUDIT.md`
- `REPORT_FC_AWARE_V1_EXACT_LOGGING_FEASIBILITY.md`
- `REPORT_FC_AWARE_V1_PERCANDIDATE_RECALL_AUDIT.md`
- `REPORT_FORCED_CANDIDATE_DOMINANCE.md`
- `REPORT_MPC_STYLE_RECOVERY_TARGETED_PILOT.md`
- `REPORT_RISK_AWARE_CBF_PREPARATION.md`
- `REPORT_RISK_AWARE_TOPK_V0.md`
- `REPORT_RISK_AWARE_TOPK_V0_100_AND_ABLATION.md`
- `REPORT_RISK_AWARE_V1_ABLATION.md`
- `REPORT_SAFER_BASELINE_NAVIGATION_STACK_AUDIT.md`

These are release gaps, not validation claims. The reports themselves are tracked, but their referenced executable scripts and compact result summaries should be added in a later release-hardening pass if they are available from the experiment machine. The V4-C runner, sweep, analysis script, and official smoke wrapper were later restored with provenance evidence; its compact raw-result summaries remain intentionally untracked.

## SAFC Method Design Failure Analysis and Redesign Program

These artifacts analyze method-version failures, distinguish local mechanism
failure from research-direction failure, and define evidence-based redesign
decisions. They contain no new experiments and no official core-source
modifications.

- `work/risk_aware_cbf/paper_materials/METHOD_VERSION_FAILURE_LEDGER.md`
- `work/risk_aware_cbf/paper_materials/METHOD_HYPOTHESIS_LEDGER.md`
- `work/risk_aware_cbf/paper_materials/FAILURE_LEVEL_CLASSIFICATION.md`
- `work/risk_aware_cbf/paper_materials/SAFC_DESIGN_SPACE_MAP.md`
- `work/risk_aware_cbf/paper_materials/VERIFICATION_AWARE_DESIGN_SPACE_MAP.md`
- `work/risk_aware_cbf/paper_materials/REDESIGN_CANDIDATE_MATRIX.md`
- `work/risk_aware_cbf/paper_materials/REDESIGN_GO_NO_GO_RULES.md`
- `work/risk_aware_cbf/paper_materials/NEXT_METHOD_PROTOTYPE_DECISION.md`
- `work/risk_aware_cbf/paper_materials/METHOD_ITERATION_GOVERNANCE.md`
- `work/risk_aware_cbf/notes/NEXT_STEP_AFTER_METHOD_REDESIGN_ANALYSIS.md`

The selected next prototype is Verification-Aware Supervisory Mode Selection,
with Persistent-Warning Triggered Recovery Coordination as backup. The program
explicitly freezes failed versions rather than closing whole research
directions after one weak implementation.

## Raw Trace Policy Check

This branch intentionally avoids adding raw trace formats. Common raw result names remain ignored by `.gitignore`, including:

- `work/risk_aware_cbf/results/**/*.jsonl`
- `work/risk_aware_cbf/results/**/*trace*`
- `work/risk_aware_cbf/results/**/trials.csv`
- `work/risk_aware_cbf/results/**/per_step*.csv`
- `work/risk_aware_cbf/results/**/active_constraints.csv`
- `work/risk_aware_cbf/results/**/trajectory_samples.csv`

## Theoretical Systematization Materials

The following theory and paper-organization artifacts structure the existing
method and evidence; they are not new experimental results:

- `work/risk_aware_cbf/paper_materials/THEORETICAL_SYSTEMATIZATION_OVERVIEW.md`
- `work/risk_aware_cbf/paper_materials/FAILURE_MODE_TAXONOMY.md`
- `work/risk_aware_cbf/paper_materials/ASSURANCE_CONTRACTS.md`
- `work/risk_aware_cbf/paper_materials/CLAIM_BOUNDARY_TABLE.md`
- `work/risk_aware_cbf/paper_materials/REAL_ROBOT_INTERFACE_CONTRACT.md`
- `work/risk_aware_cbf/paper_materials/PAPER_THEORETICAL_CONTRIBUTION_INSERT.md`
- `work/risk_aware_cbf/paper_materials/FIGURE_AND_TABLE_CAPTIONS_THEORY.md`
- `work/risk_aware_cbf/notes/NEXT_STEP_AFTER_THEORETICAL_SYSTEMATIZATION.md`

## Safety-Assurance Feedback Coordinator Materials

The following materials extend the theory and paper-organization layer with a
feedback-augmented safety assurance architecture. They are not new
experimental results and do not modify official source code:

- `work/risk_aware_cbf/paper_materials/SAFETY_ASSURANCE_FEEDBACK_COORDINATOR.md`
- `work/risk_aware_cbf/paper_materials/SAFC_STATE_MACHINE_SPEC.md`
- `work/risk_aware_cbf/paper_materials/SAFC_FEEDBACK_CONTRACTS.md`
- `work/risk_aware_cbf/paper_materials/PLANNER_INTERFACE_FOR_SAFETY_FEEDBACK.md`
- `work/risk_aware_cbf/paper_materials/CLOSED_LOOP_ASSURANCE_PIPELINE.md`
- `work/risk_aware_cbf/paper_materials/PAPER_INSERT_SAFC_FEEDBACK_FRAMEWORK.md`
- `work/risk_aware_cbf/paper_materials/FIGURE_AND_TABLE_CAPTIONS_SAFC.md`
- `work/risk_aware_cbf/notes/NEXT_STEP_AFTER_SAFC_FEEDBACK_COORDINATOR.md`

## SAFC Level-1 Offline Reconstruction

The following artifacts validate SAFC at Level 1 by reconstructing
state-machine events from existing reports and compact summaries. They are not
new closed-loop experiments and do not modify official source code:

- `work/risk_aware_cbf/scripts/safc_level1_offline_reconstruction.py`
- `work/risk_aware_cbf/REPORT_SAFC_LEVEL1_OFFLINE_RECONSTRUCTION.md`
- `work/risk_aware_cbf/results/safc_level1_offline_reconstruction/README.md`
- `work/risk_aware_cbf/results/safc_level1_offline_reconstruction/source_inventory.csv`
- `work/risk_aware_cbf/results/safc_level1_offline_reconstruction/event_inventory.csv`
- `work/risk_aware_cbf/results/safc_level1_offline_reconstruction/state_transition_summary.csv`
- `work/risk_aware_cbf/results/safc_level1_offline_reconstruction/feedback_action_summary.csv`
- `work/risk_aware_cbf/results/safc_level1_offline_reconstruction/metrics.json`
- `work/risk_aware_cbf/results/safc_level1_offline_reconstruction/reconstruction_notes.md`

No raw traces, per-step dumps, full `trials.csv`, active-constraint dumps,
trajectory samples, or JSONL logs are included.

## SAFC Level-2 No-Op Instrumentation

The following artifacts validate SAFC at Level 2 by inserting passive no-op
instrumentation into a tiny closed-loop smoke path. This does not activate
feedback policies, does not modify official source code, and does not claim
performance improvement:

- `work/risk_aware_cbf/scripts/safc_noop_state_machine.py`
- `work/risk_aware_cbf/scripts/safc_level2_noop_instrumentation.py`
- `work/risk_aware_cbf/REPORT_SAFC_LEVEL2_NOOP_INSTRUMENTATION.md`
- `work/risk_aware_cbf/results/safc_level2_noop_instrumentation/README.md`
- `work/risk_aware_cbf/results/safc_level2_noop_instrumentation/entrypoint_inventory.csv`
- `work/risk_aware_cbf/results/safc_level2_noop_instrumentation/noop_equivalence_summary.csv`
- `work/risk_aware_cbf/results/safc_level2_noop_instrumentation/state_transition_summary.csv`
- `work/risk_aware_cbf/results/safc_level2_noop_instrumentation/feedback_candidate_summary.csv`
- `work/risk_aware_cbf/results/safc_level2_noop_instrumentation/instrumentation_events_summary.csv`
- `work/risk_aware_cbf/results/safc_level2_noop_instrumentation/metrics.json`
- `work/risk_aware_cbf/results/safc_level2_noop_instrumentation/instrumentation_notes.md`

No raw traces, per-step dumps, full `trials.csv`, active-constraint dumps,
trajectory samples, JSONL logs, or binary files are included.

## R-V4C-1 Held-Out Activated Cohort

The frozen V4-C hierarchical V0 held-out validation is represented by:

- `work/risk_aware_cbf/scripts/select_v4c_heldout_activated_cohort.py`
- `work/risk_aware_cbf/scripts/run_v4c_hierarchical_heldout_paired_audit.py`
- `work/risk_aware_cbf/scripts/run_v4c_hierarchical_heldout_active_ab.py`
- `work/risk_aware_cbf/REPORT_V4C_HIERARCHICAL_HELDOUT_ACTIVATED_COHORT.md`
- `work/risk_aware_cbf/results/v4c_hierarchical_heldout_activated_cohort/`

The compact directory contains the comparator-derived inventory, preregistered cohorts/order, contract and paired gates, aggregate A/B, stage, family, runtime, progress, safety, nonactivated-control summaries, metrics, and notes. No raw comparator `trials.csv`, controls, per-step records, JSONL, traces, trajectory samples, images, models, or checkpoints are included.

## R1 Supervisory Mode Interface Audit

These artifacts record a Stage 0 interface stop for the R1
Verification-Aware Supervisory Mode Selection proposal. A later restoration
recovered the original V4-C and baseline-wrapper artifacts, but the current
branch still lacks two original V4-C helper imports required for isolated M2
evaluation. No shadow or active experiment was run.

- `work/risk_aware_cbf/paper_materials/R1_SUPERVISORY_MODE_SEMANTICS_AUDIT.md`
- `work/risk_aware_cbf/REPORT_R1_SUPERVISORY_MODE_SHADOW_AUDIT.md`
- `work/risk_aware_cbf/results/r1_supervisory_mode_shadow_audit/README.md`
- `work/risk_aware_cbf/results/r1_supervisory_mode_shadow_audit/mode_preregistration.csv`

No selector, shadow runner, raw trace, per-step dump, `trials.csv`, JSONL,
image, model, or binary artifact is included. This is an interface limitation,
not a closed-loop result or a negative V4-C result.

## V4-C Executable Interface Restoration

The following reproducibility-forensics artifacts restore provenance-confirmed,
byte-identical lightweight V4-C execution files. They do not restore raw
results and do not run a new experiment.

- `work/risk_aware_cbf/scripts/run_v4c_hstep_predictive_recovery.py`
- `work/risk_aware_cbf/scripts/run_v4c_hstep_predictive_sweep.py`
- `work/risk_aware_cbf/scripts/analyze_v4c_results.py`
- `reproduction/scripts/run_official_runpy_smoke.py`
- `work/risk_aware_cbf/REPORT_V4C_INTERFACE_RESTORATION.md`
- `work/risk_aware_cbf/results/v4c_interface_restoration/README.md`
- `work/risk_aware_cbf/results/v4c_interface_restoration/source_inventory.csv`
- `work/risk_aware_cbf/results/v4c_interface_restoration/artifact_hashes.csv`
- `work/risk_aware_cbf/results/v4c_interface_restoration/configuration_match.csv`
- `work/risk_aware_cbf/results/v4c_interface_restoration/interface_status.csv`
- `work/risk_aware_cbf/results/v4c_interface_restoration/restoration_notes.md`
- `work/risk_aware_cbf/results/v4c_interface_restoration/metrics.json`

All restored artifact hashes are recorded in `artifact_hashes.csv`. A later
module-analysis branch restores the two exact V1/V4-B helper modules with
Priority-1 SHA256 verification; that branch keeps R1 paused and does not run an
R1 context audit.

## V4-C Module Failure Analysis and Redesign Program

The following artifacts restore only the V4-C helper closure and analyze
V4-C independently as a triggered H-step recovery module. They define failure
modes, candidate-family measurements, and bounded redesign proposals. No new
trial, smoke, raw trace, raw result, image, binary, R1 experiment, or recovery
redesign implementation is included.

- `work/risk_aware_cbf/scripts/run_risk_aware_v1_pre_cbf_comparison.py`
- `work/risk_aware_cbf/scripts/run_v4b_corrective_dt_filter.py`
- `work/risk_aware_cbf/paper_materials/V4C_MODULE_SEMANTICS_AUDIT.md`
- `work/risk_aware_cbf/paper_materials/V4C_FAILURE_MODE_ANALYSIS.md`
- `work/risk_aware_cbf/paper_materials/V4C_CANDIDATE_FAMILY_AUDIT_PLAN.md`
- `work/risk_aware_cbf/paper_materials/V4C_REDESIGN_CANDIDATE_MATRIX.md`
- `work/risk_aware_cbf/paper_materials/NEXT_V4C_PROTOTYPE_DECISION.md`
- `work/risk_aware_cbf/notes/NEXT_STEP_AFTER_V4C_MODULE_ANALYSIS.md`

## R-V4C-1 Hierarchical Candidate Evaluation V0

This bounded paired audit and active A/B evaluates deterministic-first V4-C
candidate ordering on preregistered flight trials 12, 13, and 14. It preserves
the original full search as conditional fallback and includes no full100,
flight20, R1, planner, or core-source change.

- `work/risk_aware_cbf/scripts/v4c_hierarchical_candidate_evaluator.py`
- `work/risk_aware_cbf/scripts/v4c_candidate_family_metrics.py`
- `work/risk_aware_cbf/scripts/check_v4c_hierarchical_contract.py`
- `work/risk_aware_cbf/scripts/run_v4c_hierarchical_paired_audit.py`
- `work/risk_aware_cbf/scripts/run_v4c_hierarchical_active_ab.py`
- `work/risk_aware_cbf/results/v4c_hierarchical_candidate_evaluation_v0/`
- `work/risk_aware_cbf/REPORT_V4C_HIERARCHICAL_CANDIDATE_EVALUATION_V0.md`

## SAFC Level-3C Fixed-C003 Targeted A/B

The following artifacts compare no-op execution and warning-streak slowdown on
fixed C003 only. This is a targeted A/B observation, not a full benchmark, and
does not claim generalized safety performance improvement.

- `work/risk_aware_cbf/scripts/safc_level3c_fixed_c003_ab.py`
- `work/risk_aware_cbf/REPORT_SAFC_LEVEL3C_FIXED_C003_AB.md`
- `work/risk_aware_cbf/results/safc_level3c_fixed_c003_ab/README.md`
- `work/risk_aware_cbf/results/safc_level3c_fixed_c003_ab/ab_context.csv`
- `work/risk_aware_cbf/results/safc_level3c_fixed_c003_ab/baseline_noop_summary.csv`
- `work/risk_aware_cbf/results/safc_level3c_fixed_c003_ab/active_slowdown_summary.csv`
- `work/risk_aware_cbf/results/safc_level3c_fixed_c003_ab/ab_comparison_summary.csv`
- `work/risk_aware_cbf/results/safc_level3c_fixed_c003_ab/warning_timing_summary.csv`
- `work/risk_aware_cbf/results/safc_level3c_fixed_c003_ab/control_scope_summary.csv`
- `work/risk_aware_cbf/results/safc_level3c_fixed_c003_ab/metrics.json`
- `work/risk_aware_cbf/results/safc_level3c_fixed_c003_ab/ab_notes.md`

No raw traces, per-step dumps, full `trials.csv`, active constraints,
trajectory samples, JSONL logs, images, or binary files are included.

## SAFC Final Method-Validation Package

These artifacts consolidate existing methodology and validation evidence. They
do not contain new experimental results and do not modify official core source.

- `work/risk_aware_cbf/paper_materials/SAFC_FINAL_METHOD_VALIDATION_PACKAGE.md`
- `work/risk_aware_cbf/paper_materials/SAFC_EVIDENCE_CHAIN_MATRIX.md`
- `work/risk_aware_cbf/paper_materials/SAFC_FINAL_CLAIM_BOUNDARIES.md`
- `work/risk_aware_cbf/paper_materials/SAFC_NEGATIVE_AND_NEUTRAL_EVIDENCE.md`
- `work/risk_aware_cbf/paper_materials/SAFC_IMPLEMENTATION_VALIDATION_STATUS.md`
- `work/risk_aware_cbf/paper_materials/SAFC_METHOD_COMPLETENESS_AUDIT.md`
- `work/risk_aware_cbf/paper_materials/SAFC_FINAL_METHODOLOGY_DECISION.md`
- `work/risk_aware_cbf/notes/NEXT_STEP_AFTER_SAFC_FINAL_VALIDATION_PACKAGE.md`

No Python, CSV, JSON, raw trace, image, binary, or experiment output is added
by this package.

## SAFC Level-3E Robustness and Failure-Diagnosis Audit

The following artifacts diagnose mixed outcomes from Level 3D using
pre-registered slowdown variants over the small targeted cohort. This is not a
full benchmark, does not modify official source code, and does not claim
generalized performance improvement.

- `work/risk_aware_cbf/scripts/safc_level3e_robustness_diagnosis.py`
- `work/risk_aware_cbf/REPORT_SAFC_LEVEL3E_ROBUSTNESS_DIAGNOSIS.md`
- `work/risk_aware_cbf/results/safc_level3e_robustness_diagnosis/README.md`
- `work/risk_aware_cbf/results/safc_level3e_robustness_diagnosis/diagnosis_preregistration.csv`
- `work/risk_aware_cbf/results/safc_level3e_robustness_diagnosis/variant_config.csv`
- `work/risk_aware_cbf/results/safc_level3e_robustness_diagnosis/per_candidate_variant_summary.csv`
- `work/risk_aware_cbf/results/safc_level3e_robustness_diagnosis/variant_aggregate_summary.csv`
- `work/risk_aware_cbf/results/safc_level3e_robustness_diagnosis/mixed_outcome_diagnosis.csv`
- `work/risk_aware_cbf/results/safc_level3e_robustness_diagnosis/stop_reason_diagnosis.csv`
- `work/risk_aware_cbf/results/safc_level3e_robustness_diagnosis/control_scope_summary.csv`
- `work/risk_aware_cbf/results/safc_level3e_robustness_diagnosis/progress_proxy_summary.csv`
- `work/risk_aware_cbf/results/safc_level3e_robustness_diagnosis/metrics.json`
- `work/risk_aware_cbf/results/safc_level3e_robustness_diagnosis/robustness_notes.md`

No raw traces, per-step dumps, full `trials.csv`, active constraints,
trajectory samples, JSONL logs, images, or binary files are included.

## VANS Shadow Feasibility Audit

The following artifacts audit Verification-Aware Nominal Action Selection in
shadow mode only. The selected counterfactual candidate is never executed, the
formal trajectory keeps the original filtered command, official core source is
not modified, and no active VANS performance claim is made.

- `work/risk_aware_cbf/scripts/vans_shadow_selector.py`
- `work/risk_aware_cbf/scripts/vans_shadow_feasibility_audit.py`
- `work/risk_aware_cbf/REPORT_VANS_SHADOW_FEASIBILITY_AUDIT.md`
- `work/risk_aware_cbf/paper_materials/VANS_ACTION_SEMANTICS_AUDIT.md`
- `work/risk_aware_cbf/results/vans_shadow_feasibility_audit/README.md`
- `work/risk_aware_cbf/results/vans_shadow_feasibility_audit/candidate_set_spec.csv`
- `work/risk_aware_cbf/results/vans_shadow_feasibility_audit/per_candidate_shadow_summary.csv`
- `work/risk_aware_cbf/results/vans_shadow_feasibility_audit/warning_opportunity_summary.csv`
- `work/risk_aware_cbf/results/vans_shadow_feasibility_audit/candidate_selection_summary.csv`
- `work/risk_aware_cbf/results/vans_shadow_feasibility_audit/progress_tradeoff_summary.csv`
- `work/risk_aware_cbf/results/vans_shadow_feasibility_audit/runtime_overhead_summary.csv`
- `work/risk_aware_cbf/results/vans_shadow_feasibility_audit/state_isolation_summary.csv`
- `work/risk_aware_cbf/results/vans_shadow_feasibility_audit/metrics.json`
- `work/risk_aware_cbf/results/vans_shadow_feasibility_audit/shadow_audit_notes.md`

No raw traces, per-step dumps, full `trials.csv`, JSONL logs,
active-constraint dumps, trajectory samples, images, or binary files are
included. `h` and `min_safety_h` remain barrier-function margins, not metric
clearance.

## SAFC Level-3D Small Targeted Cohort A/B

The following artifacts compare no-op execution and warning-streak slowdown
over a pre-registered small targeted warning-rich cohort. This is not a full
benchmark, does not modify official source code, and does not claim
generalized performance improvement.

- `work/risk_aware_cbf/scripts/safc_level3d_small_targeted_cohort.py`
- `work/risk_aware_cbf/REPORT_SAFC_LEVEL3D_SMALL_TARGETED_COHORT.md`
- `work/risk_aware_cbf/results/safc_level3d_small_targeted_cohort/README.md`
- `work/risk_aware_cbf/results/safc_level3d_small_targeted_cohort/cohort_preregistration.csv`
- `work/risk_aware_cbf/results/safc_level3d_small_targeted_cohort/per_candidate_baseline_summary.csv`
- `work/risk_aware_cbf/results/safc_level3d_small_targeted_cohort/per_candidate_active_summary.csv`
- `work/risk_aware_cbf/results/safc_level3d_small_targeted_cohort/per_candidate_ab_comparison.csv`
- `work/risk_aware_cbf/results/safc_level3d_small_targeted_cohort/cohort_aggregate_summary.csv`
- `work/risk_aware_cbf/results/safc_level3d_small_targeted_cohort/warning_timing_summary.csv`
- `work/risk_aware_cbf/results/safc_level3d_small_targeted_cohort/control_scope_summary.csv`
- `work/risk_aware_cbf/results/safc_level3d_small_targeted_cohort/stop_reason_summary.csv`
- `work/risk_aware_cbf/results/safc_level3d_small_targeted_cohort/metrics.json`
- `work/risk_aware_cbf/results/safc_level3d_small_targeted_cohort/cohort_notes.md`

No raw traces, per-step dumps, full `trials.csv`, active constraints,
trajectory samples, JSONL logs, images, or binary files are included.

## SAFC Fixed-Candidate Level-3B-Active C003 Slowdown

The following artifacts test warning-gated slowdown activation on the fixed
C003 candidate identified by Level 3B-R. This is not a full benchmark, does not
modify official source code, and does not claim performance improvement.

- `work/risk_aware_cbf/scripts/safc_level3b_active_c003_slowdown.py`
- `work/risk_aware_cbf/REPORT_SAFC_LEVEL3B_ACTIVE_C003_SLOWDOWN.md`
- `work/risk_aware_cbf/results/safc_level3b_active_c003_slowdown/README.md`
- `work/risk_aware_cbf/results/safc_level3b_active_c003_slowdown/fixed_candidate_context.csv`
- `work/risk_aware_cbf/results/safc_level3b_active_c003_slowdown/noop_precheck_summary.csv`
- `work/risk_aware_cbf/results/safc_level3b_active_c003_slowdown/active_slowdown_summary.csv`
- `work/risk_aware_cbf/results/safc_level3b_active_c003_slowdown/activation_timing_summary.csv`
- `work/risk_aware_cbf/results/safc_level3b_active_c003_slowdown/control_scope_summary.csv`
- `work/risk_aware_cbf/results/safc_level3b_active_c003_slowdown/metrics.json`
- `work/risk_aware_cbf/results/safc_level3b_active_c003_slowdown/active_c003_notes.md`

No raw traces, per-step dumps, full `trials.csv`, active constraints,
trajectory samples, JSONL logs, images, or binary files are included.

## SAFC Level-3B Warning-Rich Targeted Active Slowdown

The following artifacts search for a naturally warning-rich targeted case and
test bounded warning-streak slowdown only if natural warning conditions are
observed. This is not a full benchmark, does not modify official source code,
and does not claim performance improvement.

- `work/risk_aware_cbf/scripts/safc_level3b_warning_rich_discovery.py`
- `work/risk_aware_cbf/scripts/safc_level3b_warning_rich_targeted.py`
- `work/risk_aware_cbf/REPORT_SAFC_LEVEL3B_WARNING_RICH_TARGETED.md`
- `work/risk_aware_cbf/results/safc_level3b_warning_rich_targeted/README.md`
- `work/risk_aware_cbf/results/safc_level3b_warning_rich_targeted/candidate_source_inventory.csv`
- `work/risk_aware_cbf/results/safc_level3b_warning_rich_targeted/warning_rich_candidate_inventory.csv`
- `work/risk_aware_cbf/results/safc_level3b_warning_rich_targeted/targeted_noop_scan_summary.csv`
- `work/risk_aware_cbf/results/safc_level3b_warning_rich_targeted/targeted_active_slowdown_summary.csv`
- `work/risk_aware_cbf/results/safc_level3b_warning_rich_targeted/activation_gate_summary.csv`
- `work/risk_aware_cbf/results/safc_level3b_warning_rich_targeted/control_delta_summary.csv`
- `work/risk_aware_cbf/results/safc_level3b_warning_rich_targeted/metrics.json`
- `work/risk_aware_cbf/results/safc_level3b_warning_rich_targeted/warning_rich_notes.md`

No raw traces, per-step dumps, full `trials.csv`, active constraints,
trajectory samples, JSONL logs, images, or binary files are included.

## SAFC Level-3B-R Warning Evidence Reconciliation

The following artifacts reconcile report-derived warning evidence with
executable no-op scan contexts. This does not run active slowdown, does not
modify official source code, and does not claim performance improvement.

- `work/risk_aware_cbf/scripts/safc_level3br_warning_reconciliation.py`
- `work/risk_aware_cbf/scripts/safc_level3br_bounded_noop_window_scan.py`
- `work/risk_aware_cbf/REPORT_SAFC_LEVEL3BR_WARNING_RECONCILIATION.md`
- `work/risk_aware_cbf/results/safc_level3br_warning_reconciliation/README.md`
- `work/risk_aware_cbf/results/safc_level3br_warning_reconciliation/report_context_inventory.csv`
- `work/risk_aware_cbf/results/safc_level3br_warning_reconciliation/candidate_context_reconciliation.csv`
- `work/risk_aware_cbf/results/safc_level3br_warning_reconciliation/bounded_noop_window_scan_summary.csv`
- `work/risk_aware_cbf/results/safc_level3br_warning_reconciliation/dt_margin_horizon_sensitivity_summary.csv`
- `work/risk_aware_cbf/results/safc_level3br_warning_reconciliation/mismatch_diagnosis_summary.csv`
- `work/risk_aware_cbf/results/safc_level3br_warning_reconciliation/metrics.json`
- `work/risk_aware_cbf/results/safc_level3br_warning_reconciliation/warning_reconciliation_notes.md`

No raw traces, per-step dumps, full `trials.csv`, active constraints,
trajectory samples, JSONL logs, images, or binary files are included.

## SAFC Level-3A Warning-Streak Slowdown

The following artifacts validate a minimal active SAFC feedback policy at
Level 3A. The policy applies bounded warning-streak slowdown in a smoke-first
setting. This is not a full benchmark, does not modify official source code,
and does not claim performance improvement.

- `work/risk_aware_cbf/scripts/safc_warning_slowdown_policy.py`
- `work/risk_aware_cbf/scripts/safc_level3a_warning_slowdown.py`
- `work/risk_aware_cbf/REPORT_SAFC_LEVEL3A_WARNING_SLOWDOWN.md`
- `work/risk_aware_cbf/results/safc_level3a_warning_slowdown/README.md`
- `work/risk_aware_cbf/results/safc_level3a_warning_slowdown/policy_logic_summary.csv`
- `work/risk_aware_cbf/results/safc_level3a_warning_slowdown/active_smoke_summary.csv`
- `work/risk_aware_cbf/results/safc_level3a_warning_slowdown/activation_summary.csv`
- `work/risk_aware_cbf/results/safc_level3a_warning_slowdown/control_delta_summary.csv`
- `work/risk_aware_cbf/results/safc_level3a_warning_slowdown/metrics.json`
- `work/risk_aware_cbf/results/safc_level3a_warning_slowdown/slowdown_notes.md`

No raw traces, per-step dumps, full `trials.csv`, active-constraint dumps,
trajectory samples, JSONL logs, or binary files are included.
