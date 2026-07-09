# REPORT: SAFC Level-3D Small Targeted Cohort A/B

## 1. Purpose

This report compares baseline no-op execution and warning-streak slowdown over
a pre-registered warning-rich small targeted cohort.

This is a small targeted cohort, not a full benchmark. It does not claim
generalized safety-performance improvement, collision reduction, warning
reduction, planning-accuracy improvement, statistical significance,
real-robot readiness, or a new CBF theorem.

SAFC Level 3D validates small targeted cohort behavior only.

## 2. Setup

| Item | Value |
| --- | --- |
| Branch | `safc-level3d-small-targeted-cohort` |
| Base branch | `safc-level3c-fixed-c003-ab` |
| Base commit | `dda9d4d9826e7bc7c2d2c17cce97b045518ee7a1` |
| Included candidates | C003, C004, C002, C001, C006 |
| Excluded candidates | C005: `sensitivity_only_warning`; C007: `initial_collision_diagnostic_context` |
| Entrypoint | `reproduction/scripts/run_official_runpy_smoke.py` |
| DT margin | 0.0005 |
| Horizon | H3 |
| Maximum steps | 160 |
| Baseline mode | no-op execution |
| Active mode | warning-streak slowdown |
| Policy scale config | warning 0.75, persistent 0.50, critical 0.25, min 0.25 |
| Official core source modified | false |
| Controller modified | false |
| CBF-QP modified | false |
| Dynamics modified | false |
| Raw traces written | false |

The run used the existing `safer_splat_official` environment on the 4090 host
with `CUDA_VISIBLE_DEVICES=1`. Temporary execution files were placed under
`/disk1/zlab/tmp`; only compact CSV/JSON/Markdown summaries were copied into
the repository.

## 3. Method

### 3.1 Cohort preregistration

The cohort was pre-registered from Level 3B-R default-context warning
reproduction. C001, C002, C003, C004, and C006 were included because they had
default-context warning evidence. C005 was excluded because its warning was
only observed under a sensitivity setting. C007 was excluded because it was an
initial-collision diagnostic context.

The fixed metrics were set before execution: `dt_margin=0.0005`, H3 repeated
control verification, `max_steps=160`, one baseline run per included
candidate, and one active run per included candidate.

### 3.2 Baseline and active runs

The baseline run executed the current official wrapper and original `u_safe`
without slowdown, recovery, replanning, CBF-QP changes, dynamics changes, or
GSplat query changes.

The active run restarted the same candidate context and enabled the existing
warning-streak slowdown policy. The active policy could scale only the
wrapper-level executed command after a natural warning gate. It did not modify
`u_nom`, internal `u_safe`, CBF-QP, dynamics, planner logic, recovery logic,
or GSplat queries.

Only compact summaries were retained. No raw trace, per-step dump, full
`trials.csv`, active constraints, trajectory samples, JSONL logs, images, or
binary files are included.

## 4. Results

| Metric | Result |
| --- | ---: |
| Cohort size | 5 |
| Baseline runs completed | 5 |
| Active runs completed | 5 |
| Baseline total warning steps | 189 |
| Active total warning steps | 164 |
| Delta total warning steps, active minus baseline | -25 |
| Mean delta warning steps, active minus baseline | -5.0 |
| Candidates active less warning | 3 |
| Candidates active equal warning | 1 |
| Candidates active more warning | 1 |
| Candidates with slowdown activation | 5 |
| Baseline collision count | 0 |
| Active collision count | 0 |
| Baseline QP infeasible count | 0 |
| Active QP infeasible count | 0 |
| Baseline completed count | 0 |
| Active completed count | 0 |
| Control scope all passed | true |
| All slowdown after or at warning | true |

| Candidate | Baseline warnings | Active warnings | Delta | Baseline stop | Active stop | Slowdown active steps | Scope pass |
| --------- | ----------------: | --------------: | ----: | ------------- | ----------- | --------------------: | ---------- |
| C003 | 11 | 10 | -1 | `stalled_before_goal` | `stalled_before_goal` | 10 | true |
| C004 | 64 | 68 | 4 | `max_steps` | `max_steps` | 68 | true |
| C002 | 38 | 24 | -14 | `max_steps` | `max_steps` | 24 | true |
| C001 | 35 | 21 | -14 | `max_steps` | `max_steps` | 21 | true |
| C006 | 41 | 41 | 0 | `max_steps` | `max_steps` | 41 | true |

## 5. Interpretation

In this pre-registered small targeted cohort, active slowdown produced fewer
observed warning steps in 3/5 candidates and a total warning-step delta of
-25. This is a targeted cohort observation, not generalized evidence or
statistical proof.

The small cohort also produced mixed targeted behavior: C004 had more observed
warning steps under active slowdown, and C006 had an unchanged warning count.
This supports bounded next-stage diagnosis rather than any general performance
claim.

All five active runs triggered slowdown after or at the natural warning gate.
All five runs preserved the command-scope boundary: `u_nom` and internal
`u_safe` remained unchanged, and only the wrapper-level executed command was
scaled under warning. Neither baseline nor active runs observed collisions or
QP infeasibility. No run reached the goal.

Because active commands can alter subsequent trajectories, post-activation
comparisons are targeted behavioral observations rather than same-trajectory
causal proof.

## 6. What Level 3D Validates

Level 3D validates only the following:

* pre-registered small cohort A/B execution;
* warning-gated slowdown remained bounded in the included candidates;
* slowdown did not precede natural warning timing;
* command scope remained wrapper-level;
* small-cohort targeted behavior differences were recorded; and
* no CBF-QP, dynamics, planner, recovery, or GSplat query modification was
  made.

## 7. What Level 3D Does Not Validate

Level 3D does not validate:

* no full100 benchmark;
* no flight20 benchmark;
* no statistical significance;
* no generalized safety-performance improvement;
* no generalized collision reduction;
* no generalized warning reduction;
* no planner integration;
* no real-robot deployment;
* no global safety guarantee; and
* no new CBF theorem.

## 8. Decision

Level 3D may justify preparing a carefully bounded Level 3E robustness audit
or final method-validation package focused on pre-registered targeted cases,
stop-reason reconciliation, and claim boundaries. It does not justify full100
or benchmark-level claims.

Active slowdown produced fewer observed warning steps in the pre-registered
small targeted cohort; this is a small-cohort targeted observation, not
generalized evidence.

## 9. Artifacts

| Artifact | Path |
| --- | --- |
| Runner | `work/risk_aware_cbf/scripts/safc_level3d_small_targeted_cohort.py` |
| Results README | `work/risk_aware_cbf/results/safc_level3d_small_targeted_cohort/README.md` |
| Preregistration | `work/risk_aware_cbf/results/safc_level3d_small_targeted_cohort/cohort_preregistration.csv` |
| Baseline summary | `work/risk_aware_cbf/results/safc_level3d_small_targeted_cohort/per_candidate_baseline_summary.csv` |
| Active summary | `work/risk_aware_cbf/results/safc_level3d_small_targeted_cohort/per_candidate_active_summary.csv` |
| A/B comparison | `work/risk_aware_cbf/results/safc_level3d_small_targeted_cohort/per_candidate_ab_comparison.csv` |
| Aggregate summary | `work/risk_aware_cbf/results/safc_level3d_small_targeted_cohort/cohort_aggregate_summary.csv` |
| Warning timing | `work/risk_aware_cbf/results/safc_level3d_small_targeted_cohort/warning_timing_summary.csv` |
| Control scope | `work/risk_aware_cbf/results/safc_level3d_small_targeted_cohort/control_scope_summary.csv` |
| Stop reasons | `work/risk_aware_cbf/results/safc_level3d_small_targeted_cohort/stop_reason_summary.csv` |
| Metrics | `work/risk_aware_cbf/results/safc_level3d_small_targeted_cohort/metrics.json` |
| Notes | `work/risk_aware_cbf/results/safc_level3d_small_targeted_cohort/cohort_notes.md` |
