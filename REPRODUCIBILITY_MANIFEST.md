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

- 40 risk-aware CBF report markdown files
- 163 files under `work/risk_aware_cbf/notes/`
- 32 files under `work/risk_aware_cbf/figures/`
- 23 files under `work/risk_aware_cbf/paper_materials/`

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
| `REPORT_V4C_HSTEP_PREDICTIVE_RECOVERY.md` | no | no | N/A | yes |
| `REPORT_V4C_RUNTIME_TUNING_PILOT.md` | N/A | N/A | N/A | N/A |
| `REPORT_V4C_TUNED_FULL100_VALIDATION.md` | N/A | N/A | N/A | N/A |

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
- `REPORT_V4C_HSTEP_PREDICTIVE_RECOVERY.md`

These are release gaps, not validation claims. The reports themselves are tracked, but their referenced executable scripts and compact result summaries should be added in a later release-hardening pass if they are available from the experiment machine.

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
