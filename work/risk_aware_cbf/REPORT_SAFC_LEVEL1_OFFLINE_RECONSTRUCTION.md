# REPORT: SAFC Level-1 Offline Event Reconstruction

## 1. Purpose

This report evaluates whether the proposed SAFC state machine and feedback
contracts can consistently organize safety-relevant events already recorded in
the repository's tracked reports. It reconstructs report-level aggregate
events for start admission, CBF-QP status, finite-horizon warnings, recovery,
collision, diagnostic escalation, and candidate feedback actions.

This is not a new closed-loop experiment. It does not modify the controller. It
does not claim new performance improvement.

## 2. Inputs

The reconstruction scanned and used the following 11 tracked reports:

1. `REPORT_SYNTHETIC_INITIAL_UNSAFE_STRESS_TEST.md`
2. `REPORT_STARTGUARD_FLIGHT100.md`
3. `REPORT_STARTGUARD_TRIAL57.md`
4. `REPORT_DISCRETE_TIME_VERIFICATION_CONSOLIDATION.md`
5. `REPORT_V4A_ACTIVE_PROJECTION_DT_AUDIT.md`
6. `REPORT_V4C_HSTEP_PREDICTIVE_RECOVERY.md`
7. `REPORT_V4C_FLIGHT100_VALIDATION.md`
8. `REPORT_V4C_TUNED_FULL100_VALIDATION.md`
9. `REPORT_FC_AWARE_V1_FLIGHT20_STOP_REASON_RECONCILIATION.md`
10. `REPORT_MPC_STYLE_RECOVERY_TARGETED_PILOT.md`
11. `REPORT_SAFER_BASELINE_NAVIGATION_STACK_AUDIT.md`

All designated reports were present; `sources_missing` is zero. The default
run used report Markdown and its embedded compact tables only.
`--include-local-results` remained `false`, so no optional local summary or
metrics files were read. No raw trace, trial-level dump, per-step dump,
active-constraint dump, trajectory sample, or JSONL file was used.

## 3. Reconstruction Method

The standard-library analysis script performs six deterministic stages:

1. scan the designated existing reports and record source availability;
2. parse explicit Markdown tables, metric/value tables, and report key-value
   lines;
3. reconstruct safety-relevant aggregate events without inferring per-step
   trajectories;
4. map each event to SAFC source and destination states, bounded feedback
   action, claim scope, and confidence;
5. aggregate state transitions and feedback actions; and
6. write compact CSV, JSON, and Markdown artifacts.

The parser contains explicit event/state/action/scope enumerations and fails on
unknown values or empty evidence text. Two consecutive runs produced identical
SHA256 hashes for every output artifact.

## 4. SAFC State Mapping

| Event class | SAFC transition | Feedback action | Claim scope |
| --- | --- | --- | --- |
| Certified or full-query-valid start | S0 Pre-Execution -> S1 Nominal Filtering | `admit_task` | implemented/supported or offline reconstruction only |
| Successful verified repair | S0 Pre-Execution -> S1 Nominal Filtering | `admit_task` | implemented/supported |
| Aggregate zero QP infeasibility | S1 Nominal Filtering -> S2 Verified Execution | `no_feedback` | source-dependent reconstruction |
| Positive H1/H2/H3 or horizon-margin warning | S2 Verified Execution -> S3 Warning-Aware Execution | slowdown candidate or recovery activation | offline reconstruction only |
| Named V4-C activation | S3 Warning-Aware -> S4 Recovery | `activate_recovery` | implemented/supported for the named configuration |
| Named recovery success with resolved executed margin | S4 Recovery -> S2 Verified Execution | `activate_recovery` plus re-verification | implemented/supported for the named configuration |
| Positive collision evidence | S2 execution context -> S6 Safe Halt/Abort | `safe_halt_candidate` | diagnostic only |
| Persistent warning, recovery-disabled collision, or unresolved diagnostic recovery | S3/S4 -> S5 Replan Requested | `replan_request_candidate` | interface-level or diagnostic only |

The mapping does not reinterpret a DT warning as collision. It also does not
reinterpret an interface-level replan candidate as an implemented planner.

## 5. Results

The default reconstruction produced:

| Metric | Value |
| --- | ---: |
| `sources_scanned` | 11 |
| `sources_used` | 11 |
| `sources_missing` | 0 |
| `events_reconstructed` | 88 |
| `state_transitions_reconstructed` | 86 |
| `feedback_actions_reconstructed` | 88 |
| `dt_warning_events_reconstructed` | 15 |
| `recovery_events_reconstructed` | 14 |
| `safe_halt_candidates` | 6 |
| `replan_request_candidates` | 6 |

The 86 transition-bearing event rows form 14 grouped
`from_state/to_state/event_type` summaries. The 88 feedback-bearing event rows
form seven grouped feedback-action summaries. These counts describe
reconstructed report evidence, not independent trials, causal effects, or
performance gains.

## 6. Key Findings

**Finding 1.** Existing reports contain sufficient aggregate evidence to
instantiate SAFC states for start admission, nominal-filter success,
warning-aware execution, named triggered recovery, and diagnostic halt/replan
candidates. This supports operational mappability at report level.

**Finding 2.** DT Verification evidence maps consistently to S2 -> S3
warning-aware transitions. The reconstructed 15 warning events remain
finite-horizon margin warnings rather than collisions.

**Finding 3.** Named V4-C reports support the S3 -> S4 -> S2 recovery path for
their reported configurations. Primitive MPC-style offline events remain
diagnostic and are not promoted to supported V4-C behavior.

**Finding 4.** FC-Aware and primitive MPC-style negative evidence can populate
diagnostic halt/replan-candidate states. The reconstruction does not attribute
FC-Aware collision causality to the cap and does not interpret a replan
candidate as implemented planner integration.

## 7. What Level 1 Validates

Level 1 validates only that:

- the SAFC state taxonomy is operationally mappable to existing report-level
  evidence;
- feedback actions can be reconstructed as supported, candidate, or diagnostic
  decisions according to evidence scope; and
- existing reports can be organized under a
  signal -> state -> bounded-feedback-contract structure.

SAFC Level 1 validates operational mappability of the proposed state machine
over existing evidence.

## 8. What Level 1 Does Not Validate

Level 1 provides:

- no new control-performance evidence;
- no evidence that SAFC reduces collision;
- no evidence that SAFC reduces warnings;
- no planner improvement or planning-accuracy evidence;
- no closed-loop SAFC validation;
- no real-robot deployment evidence;
- no global safety guarantee; and
- no new CBF theorem.

## 9. Artifacts

- `source_inventory.csv`
- `event_inventory.csv`
- `state_transition_summary.csv`
- `feedback_action_summary.csv`
- `metrics.json`
- `reconstruction_notes.md`

All artifacts are under
`work/risk_aware_cbf/results/safc_level1_offline_reconstruction/`.

## 10. Decision

Level 1 is sufficient to retain SAFC as a validated offline
event-reconstruction framework, but not sufficient to claim performance
improvement. Level 2 would require no-op closed-loop instrumentation; Level 3
would require a minimal active feedback policy such as warning-streak slowdown.
