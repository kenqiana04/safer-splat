# REPORT: SAFC Level-3C Fixed-C003 Targeted A/B Comparison

## 1. Purpose

This report records a fixed-candidate targeted A/B comparison between no-op
execution and warning-streak slowdown for candidate C003 in the flight scene.

SAFC Level 3C validates fixed-C003 targeted A/B behavior only.

This is not a full benchmark. It does not claim generalized safety
performance improvement, collision reduction, warning reduction, planner
accuracy improvement, real-robot readiness, or a new CBF theorem.

## 2. Setup

| Item | Value |
| --- | --- |
| Branch | `safc-level3c-fixed-c003-ab` |
| Base branch | `safc-level3b-active-c003-slowdown` |
| Base commit | `e8d708a0bf0edf840e019604458d0b41926b5f00` |
| Candidate | C003 |
| Scene / trial | flight / 14 |
| Entrypoint | `reproduction/scripts/run_official_runpy_smoke.py` |
| Mode | paired fixed-case A/B |
| Baseline | no-op execution |
| Active policy | warning-streak slowdown |
| DT margin | 0.0005 |
| Horizon | H3 |
| Maximum steps | 100 |
| CUDA device | 1 |
| Official core source modified | false |
| Controller modified | false |
| `cbf/`, `splat/`, `ellipsoids/`, `dynamics/`, `run.py` modified | false |
| Raw traces committed | false |

The run used the existing `safer_splat_official` environment on the 4090 host.
Temporary execution files were placed under `/disk1/zlab/tmp`; only compact
CSV/JSON/Markdown summaries were copied into the repository.

## 3. Method

### 3.1 Baseline no-op

The baseline run executed the fixed C003 context without modifying the
nominal command, internal CBF-QP output, wrapper-level executed command,
planner, dynamics, or GSplat query. It recorded natural warning timing,
collision status, QP infeasibility status, completion state, and stop reason.

### 3.2 Active slowdown

The active run restarted the same fixed C003 context and enabled the existing
warning-streak slowdown policy. Slowdown was allowed only after a naturally
observed warning gate. The policy could scale only the wrapper-level executed
command. It did not modify `u_nom`, the internal `u_safe`, the CBF-QP
implementation, dynamics, GSplat queries, planner logic, recovery logic, or
official source code.

Because the active command can alter the subsequent trajectory,
post-activation comparisons are targeted behavioral observations rather than
same-trajectory causal proof.

## 4. Results

| Metric | Baseline no-op | Active slowdown |
| --- | ---: | ---: |
| Steps observed | 70 | 69 |
| Natural warning steps | 11 | 10 |
| First warning step | 60 | 60 |
| Collision observed | false | false |
| QP infeasible observed | false | false |
| Completed | false | false |
| Stop reason | `stalled_before_goal` | `stalled_before_goal` |
| `u_nom` modified | false | false |
| Internal `u_safe` modified | false | false |
| Wrapper executed command scaled | false | true |

| Active-only metric | Result |
| --- | ---: |
| Slowdown-active steps | 10 |
| First slowdown step | 60 |
| Slowdown after or at warning | true |
| Minimum scale applied | 0.25 |
| Maximum scale applied | 0.75 |
| Maximum control delta from slowdown | 0.018518980592489243 |
| Command modified only when warning | true |
| Control scope passed | true |

Active slowdown produced fewer observed warning steps in the fixed C003
targeted run; this is a fixed-case observation, not generalized evidence.

## 5. Interpretation

The active slowdown policy triggered at the same step as the first warning
observed in the active run, step 60. It remained within the configured scale
bounds and changed only the wrapper-level executed command. The baseline and
active runs both avoided observed collision and QP infeasibility, but neither
completed the task; both stopped with `stalled_before_goal`.

The active run recorded one fewer warning step than the baseline. This is a
targeted behavioral observation for fixed C003 only. It must not be described
as a general warning-reduction result because this task ran a single fixed
candidate, and the active command can alter the subsequent trajectory after
activation.

## 6. What Level 3C Validates

For fixed C003 only:

* the same targeted context can be run in no-op and active modes;
* warning-streak slowdown activates no earlier than the natural warning gate;
* active scale values stay within the configured bounds;
* active control changes are confined to the wrapper-level executed command;
* `u_nom` and internal `u_safe` remain unchanged; and
* no forbidden official source or core algorithm file was modified.

## 7. What Level 3C Does Not Validate

* No full100 benchmark
* No flight20 benchmark
* No statistical significance
* No generalized warning reduction
* No generalized collision reduction
* No completion improvement
* No planner integration
* No real-robot deployment readiness
* No global safety proof
* No new CBF theorem

## 8. Decision

Level 3C supports a future Level 3D small targeted cohort only if the next
stage predefines candidate selection, fixed metrics, stop-reason handling,
and claim boundaries before execution. It does not justify a full100 run or
benchmark-level claims by itself.

## 9. Artifacts

| Artifact | Path |
| --- | --- |
| Runner | `work/risk_aware_cbf/scripts/safc_level3c_fixed_c003_ab.py` |
| Results README | `work/risk_aware_cbf/results/safc_level3c_fixed_c003_ab/README.md` |
| Context CSV | `work/risk_aware_cbf/results/safc_level3c_fixed_c003_ab/ab_context.csv` |
| Baseline CSV | `work/risk_aware_cbf/results/safc_level3c_fixed_c003_ab/baseline_noop_summary.csv` |
| Active CSV | `work/risk_aware_cbf/results/safc_level3c_fixed_c003_ab/active_slowdown_summary.csv` |
| A/B CSV | `work/risk_aware_cbf/results/safc_level3c_fixed_c003_ab/ab_comparison_summary.csv` |
| Warning timing CSV | `work/risk_aware_cbf/results/safc_level3c_fixed_c003_ab/warning_timing_summary.csv` |
| Control scope CSV | `work/risk_aware_cbf/results/safc_level3c_fixed_c003_ab/control_scope_summary.csv` |
| Metrics JSON | `work/risk_aware_cbf/results/safc_level3c_fixed_c003_ab/metrics.json` |
| Notes | `work/risk_aware_cbf/results/safc_level3c_fixed_c003_ab/ab_notes.md` |

No raw traces, full trial dumps, per-step dumps, active-constraint dumps,
trajectory samples, JSONL logs, images, or binary files are included.
