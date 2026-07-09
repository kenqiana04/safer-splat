# REPORT: SAFC Level-3B-R Warning Evidence Reproduction Reconciliation

## 1. Purpose

This report explains why warning and recovery evidence in tracked reports did
not reproduce in the Level-3B first-50-step current-wrapper scans.

This is not an active feedback experiment. It does not run slowdown. It does
not claim performance improvement.

## 2. Setup

- Branch: `safc-level3br-warning-reconciliation`
- Base commit: `5cd5c8ca093bbdcd42498574498247cda9191b0e`
- Reports scanned: 9 tracked Markdown reports
- Candidates reconciled: 7
- Maximum candidates: 7
- Maximum trials per candidate: 1
- Maximum steps: 200
- Default DT margin: 0.0005
- Default horizon: H3
- Sensitivity margins: 0.0001, 0.0005, 0.001
- Sensitivity horizons: H1, H2, H3
- Selected entrypoint:
  `reproduction/scripts/run_official_runpy_smoke.py`
- Official core source modified: false
- Controller modified: false
- CBF-QP modified: false
- Dynamics modified: false

The run used the existing `safer_splat_official` environment on GPU 1.
Temporary files and the Matplotlib configuration were directed to
`/disk1/zlab/tmp`.

## 3. Method

### 3.1 Report Context Extraction

The context audit read only tracked Markdown reports and compact Level-3B
summaries. It extracted scene, trial, step-window, horizon, DT margin,
controller, recovery, trajectory, stop-reason, and checkpoint context where
available.

The reports identify Risk-Aware V1, V4-C recovery-enabled, post-repair, and
diagnostic contexts. Exact first-warning steps and exact checkpoints were
generally not reported. No referenced raw trace, full `trials.csv`, per-step
file, trajectory sample, active-constraint file, or JSONL file was read.

### 3.2 Bounded No-Op Extended-Window Scan

All seven report-derived candidates were scanned for at most 200 steps in the
current official smoke-wrapper context. The audit used the original CBF-QP
`u_safe`, recovery disabled, H3 repeated-control verification, and
`dt_margin=0.0005`.

The original command was executed unchanged. No active feedback, slowdown,
recovery, planner, or command scaling was run. Only aggregate counts and the
first warning step were retained.

### 3.3 DT Margin / Horizon Sensitivity Audit

Each candidate was run on one no-op trajectory while warning counters were
accumulated for the 3x3 DT-margin/horizon grid. The grid did not alter the
executed control or trajectory. This is diagnostic context sensitivity, not
benchmark tuning.

## 4. Results

| Metric | Value |
| --- | ---: |
| `sources_scanned` | 9 |
| `candidates_reconciled` | 7 |
| `candidates_window_scanned` | 7 |
| `extended_window_warning_candidates` | 5 |
| `sensitivity_warning_candidates` | 6 |
| `not_reproduced_candidates` | 1 |
| `insufficient_context_candidates` | 7 |
| `any_warning_reproduced` | true |
| `best_reproduced_candidate_id` | C003 |
| `best_reproduced_first_warning_step` | 60 |

Default H3/0.0005 extended-window results were:

| Candidate | Flight trial | Steps observed | H3 warning steps | First warning step | Status |
| --- | ---: | ---: | ---: | ---: | --- |
| C001 | 13 | 179 | 47 | 114 | Reproduced |
| C002 | 12 | 167 | 45 | 102 | Reproduced |
| C003 | 14 | 70 | 11 | 60 | Reproduced |
| C004 | 85 | 167 | 71 | 71 | Reproduced |
| C005 | 37 | 200 | 0 | N/A | Sensitivity-only |
| C006 | 31 | 200 | 60 | 120 | Reproduced |
| C007 | 57 | 0 | 0 | N/A | Initial-collision diagnostic context |

All executed no-op candidates had `u_nom_modified=false`,
`u_safe_modified=false`, and `control_modified=false`. C007 exited before an
executed step because the original trial-57 state was already collision
diagnostic evidence.

## 5. Interpretation

A naturally warning-producing executable context was found under bounded
no-op reconciliation. This is candidate discovery evidence only. It does not
validate active slowdown effectiveness. The next step may be Level 3B-Active
on the fixed reproduced candidate, not Level 3C benchmark.

The first-50-step window was the primary mismatch for C001, C002, C003, C004,
and C006. Their first default-context warnings appeared at steps 60 to 120.
C005 produced warnings only at the alternative diagnostic margin 0.001, so its
evidence remains threshold/context sensitive. C007 is not a usable warning
candidate in the original-start wrapper because it begins in collision.

All seven report contexts remain incomplete relative to the exact originating
experiments because controller, recovery history, trajectory, first-warning
step, or checkpoint fields are missing. Default-context reproduction for five
candidates resolves the bounded-window question but does not make the report
and current trajectories identical.

## 6. What Level 3B-R Validates

- Report context audit was performed.
- A seven-candidate, 200-step bounded no-op scan was performed.
- A no-op DT-margin/horizon sensitivity audit was performed.
- Five candidates reproduced warning evidence under the default context.
- C003 was identified as the earliest fixed executable candidate at step 60.
- The Level-3B first-50 window was too short for those five candidates.

## 7. What Level 3B-R Does Not Validate

- No active slowdown.
- No performance improvement.
- No collision reduction.
- No warning reduction.
- No planner integration.
- No real-robot validation.
- No global safety guarantee.
- No new CBF theorem.

## 8. Decision

Proceed only to a fixed-candidate Level 3B-Active activation smoke using C003
(flight trial 14) and the exact reproduced no-op context. Do not proceed to a
Level 3C benchmark.

SAFC Level 3B-R validates warning evidence/context reconciliation only.

A naturally warning-producing executable context was identified under bounded
no-op reconciliation; active slowdown still requires a separate
fixed-candidate activation smoke.
