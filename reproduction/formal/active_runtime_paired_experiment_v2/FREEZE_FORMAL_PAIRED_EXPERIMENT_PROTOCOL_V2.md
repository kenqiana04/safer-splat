# FREEZE_FORMAL_PAIRED_EXPERIMENT_PROTOCOL_V2

**Protocol status:** `CONTENT_FROZEN_PENDING_REPOSITORY_COMMIT`  
**Freeze date:** 2026-09-11  
**Repository:** `kenqiana04/safer-splat`  
**Method source lock:** PR #138 head `606edd1c254f4ffaec48e0b84d8f5e5f29c039ec`  
**Transition authority:** 44 rows; Git blob `612a70ba41e4c291c76bd94e34d235b0c1297375`  
**Formal objective:** Freeze the final paired Stonehenge evaluation before any further final-result collection. No method tuning, map change, metric change, or outcome-conditioned trial selection is allowed after formal collection starts.

---

## 1. Why this protocol is being frozen now

The repaired Active Runtime has passed:
- targeted routing regression;
- 44/44 transition fidelity/dynamic/exact-one checks;
- 179/179 Active Runtime CPU regression;
- the existing 96/96 milestone regression;
- the repaired 10-pair Pilot with 10/10 evaluation-eligible pairs.

The repaired Pilot showed Reference vs Active mean normalized progress `0.340029482 vs 0.340001834`, median `0.232968618 vs 0.232968618`, collision proxy `0/10 vs 0/10`, certification-margin violation `0/10 vs 0/10`, and no new structural liveness blocker. This protocol therefore freezes evaluation rather than continuing method development.

---

## 2. Study architecture

### 2.1 Two frozen paired arms

**REFERENCE_CBF_QP**
- current primary CBF-QP at the frozen method source;
- same map, start, goal, dt, controller parameters and plant dynamics as Active;
- bypasses Active Runtime assurance.

**ACTIVE_RUNTIME_V2**
- current primary CBF-QP;
- exact binary32 actuator-boundary canonicalization;
- `L1 -> P0 -> C0 -> L2 -> L3 -> Supervisor -> PlantCommit`;
- 44-row transition authority including `ARB_BACKUP_GUARD`;
- unchanged frozen trace/finalization path.

The pair differs only by the Active Runtime assurance layer.

### 2.2 Trial universe

Run the frozen Stonehenge IDs `0..99`: **100 pairs / 200 arms**.

However, the primary paper analysis is **85 pairs**, excluding the 15 IDs directly used for PR99 logging-pilot or current Active Runtime pilot/diagnosis decisions:

`[5, 10, 15, 25, 30, 35, 45, 50, 55, 65, 70, 75, 85, 90, 95]`

Primary formal IDs:

`[0, 1, 2, 3, 4, 6, 7, 8, 9, 11, 12, 13, 14, 16, 17, 18, 19, 20, 21, 22, 23, 24, 26, 27, 28, 29, 31, 32, 33, 34, 36, 37, 38, 39, 40, 41, 42, 43, 44, 46, 47, 48, 49, 51, 52, 53, 54, 56, 57, 58, 59, 60, 61, 62, 63, 64, 66, 67, 68, 69, 71, 72, 73, 74, 76, 77, 78, 79, 80, 81, 82, 83, 84, 86, 87, 88, 89, 91, 92, 93, 94, 96, 97, 98, 99]`

The excluded 15 are still run once under the final protocol, but they are a **development-exposed secondary cohort**, not part of the primary 85-pair inference.

This 85-pair cohort must **not** be called a pristine untouched holdout: older-version benchmark information existed during development. It is a prespecified, development-light primary cohort.

### 2.3 Execution order

Trial order is frozen by `random.Random(20260911)`:

`[66, 74, 9, 12, 73, 26, 79, 31, 54, 18, 19, 88, 38, 8, 90, 28, 29, 0, 24, 5, 37, 98, 27, 25, 91, 2, 78, 76, 80, 82, 99, 56, 21, 33, 44, 10, 14, 16, 61, 23, 6, 96, 45, 50, 43, 47, 85, 51, 69, 59, 63, 42, 13, 65, 4, 93, 39, 49, 97, 60, 83, 36, 67, 30, 86, 35, 3, 81, 87, 71, 20, 53, 7, 58, 40, 70, 89, 94, 68, 75, 15, 48, 55, 95, 92, 34, 72, 17, 32, 62, 41, 52, 64, 22, 84, 11, 57, 1, 46, 77]`

Within each pair:
- even trial ID: `REFERENCE -> ACTIVE`;
- odd trial ID: `ACTIVE -> REFERENCE`.

This gives 50/50 first-arm counterbalancing. All arms run serially in separate processes on GPU 1. Parallel formal-arm execution is forbidden.

---

## 3. Exact environment and source lock

### 3.1 Git
- method head: `606edd1c254f4ffaec48e0b84d8f5e5f29c039ec`
- transition-table Git blob: `612a70ba41e4c291c76bd94e34d235b0c1297375`
- worktree must be clean before collection.
- no runtime/production source mutation is allowed after formal collection starts.

### 3.2 Environment
- conda: `/disk1/zlab/conda_envs/safer_splat_official`
- python: `/disk1/zlab/conda_envs/safer_splat_official/bin/python`
- `CUDA_VISIBLE_DEVICES=1`
- `PYTHONHASHSEED=0`
- `PYTHONNOUSERSITE=1`
- `PYTHONDONTWRITEBYTECODE=1`
- `CUBLAS_WORKSPACE_CONFIG=:4096:8`

Before formal collection, record and hash:
- Python version;
- conda/pip package lock;
- PyTorch version;
- CUDA runtime;
- NVIDIA driver;
- GPU model;
- Git head;
- clean-worktree status.

---

## 4. Map lock

Stonehenge path:

`outputs/stonehenge/splatfacto/2024-09-11_100724`

Map identity:

`c9eade9ca89b741768a0ca33b3a755b2656402864f121aefdceaed4b0174f7c8`

Frozen artifacts:

| File | Size | SHA256 |
|---|---:|---|
| `config.yml` | 6933 | `cd6ea45ad01553f0ce1531ad08cfaf8359e95041b39c77291d94e75f2d2f2f8e` |
| `dataparser_transforms.json` | 312 | `92a1af2f195be3b32e0422418aff40cbd426c1cf9d8f7d5da87629519f5a0f8e` |
| `nerfstudio_models/step-000029999.ckpt` | 92344786 | `ac14f5ced354c93f26cf92404540712eff65bd02554d9e9ed0332508e290382d` |

Any mismatch blocks formal collection.

---

## 5. Frozen controller, dynamics and certification

Controller:
- proposal = `CURRENT_PRIMARY_CBF_QP`;
- alpha = `5.0`;
- beta = `1.0`;
- controller radius = `0.015 m`;
- distance method = `ball-to-ellipsoid`;
- actuator bounds = `[-0.1,+0.1]^3`.

Dynamics:
- `POSITION_FIRST_FORWARD_EULER_DOUBLE_INTEGRATOR_V1`;
- `dt=0.05 s`;
- velocity bounds = `[-0.1,+0.1]`.

Certification:
- full GSplat query + conservative signed-distance interval;
- effective certification radius = `0.025 m`;
- `rho_seg=0`;
- terminal velocity tolerance = `1e-12`.

Episode:
- seed = `0`;
- max steps = `500`;
- native termination semantics are frozen to the PR #138 source. They must not be redefined after seeing results.

---

## 6. Frozen deadline profile

- cycle deadline = `1.0 s`;
- latest safe commit = `0.8 s`;
- warning reserve = `0.2 s`;
- stage budgets = empty;
- clock = `MONOTONIC_CLOCK_ACTIVE_SMOKE_V2`.

This is an **experimental engineering deadline profile**, not a hard-real-time or deployment guarantee.

---

## 7. Frozen post-hoc oracle

The oracle is feedback-free and post-hoc only.

### 7.1 Represented-map collision proxy
- swept executed position segments;
- operational radius = `0.015 m`;
- represented-map-relative penetration only;
- do not call it physical collision.

### 7.2 Certification-margin violation
- effective radius = `0.025 m`;
- reported separately from collision proxy.

### 7.3 Liveness
Normalized progress:

`(d_start - d_final) / d_start`

- xyz Euclidean start/final distance to goal;
- no clipping;
- negative values retained.

Goal reached:
- frozen 6D L2 criterion `< 0.001`;
- timeout/native stop is not automatically success.

---

## 8. Evaluation eligibility

An Active arm is evaluation-eligible only if:
- exact trace cardinality;
- `FINALIZED`;
- valid trace lock;
- no `EVIDENCE_INCOMPLETE`;
- no `RECOVERY_REQUIRED`;
- complete identity-consistent executed trajectory.

A Reference arm is eligible only if:
- complete immutable state/action trajectory;
- typed termination;
- complete oracle input.

No imputation is allowed.

An ineligible arm is **UNKNOWN**, never silently counted as safe or successful.

A paired primary datum requires both arms to be eligible.

---

## 9. Prespecified map/task difficulty audit

Before looking at formal outcomes, compute for all 100 trials:
- start clearance at 0.015 m;
- start clearance at 0.025 m;
- goal clearance at 0.015 m;
- goal clearance at 0.025 m;
- straight-line start-to-goal minimum clearance at 0.025 m;
- start-goal Euclidean distance.

Difficulty score = straight-line minimum 0.025-m certification clearance.

Sort ascending, break ties by trial ID:
- lowest 33 = `HARD`;
- next 34 = `MODERATE`;
- highest 33 = `EASY`.

This stratification is secondary interpretation only. It may not be used to exclude trials or alter parameters.

---

## 10. Primary endpoints and pass gates

### Gate A — integrity
Primary cohort must have **85/85 eligible pairs** and no unresolved core runtime integrity failure.

A legitimate typed scientific outcome (timeout, solver failure, backup, terminal, boundary) is not automatically an integrity failure if execution evidence remains complete.

### Gate B — Active represented-map safety
For the 85 primary Active arms:
- represented-map collision-proxy trial count must be `0`;
- certification-margin violation trial count must be `0`;
- Active-only collision discordant pair count must be `0`.

If both Reference and Active have zero events, the conclusion is **safety parity on this benchmark**, not empirical superiority.

### Gate C — liveness non-inferiority
For each eligible primary pair:

`delta_i = progress_active_i - progress_reference_i`

Primary estimand = mean paired delta.

Use 10,000 pair-bootstrap resamples, seed `20260911`, percentile 95% CI.

Frozen non-inferiority margin:

`delta_NI = -0.02`

PASS if:

`lower_95%_CI(mean delta) > -0.02`

This means the protocol tolerates at most a prespecified 2-percentage-point absolute normalized-progress degradation at the lower confidence bound.

Median delta is secondary and does not replace the primary criterion.

---

## 11. Secondary metrics

Per arm/trial:
- collision-proxy trial flag and segment count;
- minimum represented-map clearance;
- certification-margin violation flag;
- minimum certification-margin clearance;
- goal reached;
- normalized progress;
- steps executed;
- typed termination category;
- per-step compute median / p95 / max;
- episode wall time.

Active-only:
- primary / alternative / retained-backup / terminal / boundary counts;
- L1/C0/L2/L3 PASS/FAIL/UNKNOWN;
- QP failure count;
- deadline OPEN/WARNING/EXPIRED;
- token activation and consumption.

Do not add a new metric after formal results are visible and then present it as prespecified.

---

## 12. Statistical analysis

Primary population: `PRIMARY_FORMAL_85`.

Secondary:
- full `ALL100_DESCRIPTIVE`;
- `DEVELOPMENT_EXPOSED_15`;
- prespecified HARD/MODERATE/EASY strata.

Binary paired outcomes:
- report `n00/n01/n10/n11`;
- exact McNemar test only when discordant pairs exist;
- with zero events, report exact Clopper-Pearson 95% upper bound descriptively.

Continuous paired outcomes:
- paired differences;
- mean, median, IQR, min/max;
- 10,000-resample paired bootstrap 95% CI.

Runtime:
- Active/Reference per-trial median-time ratio;
- Active/Reference per-trial p95-time ratio;
- report median ratio and paired bootstrap CI.

No multiplicity-adjusted “significance fishing.” The formal success decision is based on the prespecified integrity/safety gates and progress non-inferiority.

Bootstrap intervals characterize the frozen benchmark cohort; they are not population-level deployment guarantees.

---

## 13. Formal collection conduct

During collection you may inspect only:
- process exit code;
- GPU cleanup;
- trace cardinality;
- file presence/hash;
- map/source identity;
- obvious task-local infrastructure errors.

Do **not** inspect aggregate:
- progress differences;
- collision/margin rates;
- runtime superiority;
- difficulty-stratum performance.

No partial-result-based parameter tuning or trial removal.

Aggregate scientific analysis begins only after all scheduled primary arms complete, unless a protocol-stopping core integrity failure occurs.

---

## 14. Retry and error policy

Allowed without protocol version change:
- path/symlink repair;
- serializer/report fix;
- launcher quoting;
- task-local environment injection;
- summary ordering;
- other changes provably outside runtime/scientific semantics.

Rules:
- preserve every failed attempt;
- record reason;
- rerun only the affected arm;
- never replace a trial ID.

If a **core runtime/method** change is needed after formal collection begins:
- stop collection;
- do not patch-and-continue;
- create a new protocol version;
- do not mix pre-change and post-change formal data.

If oracle/metric definition or frozen experiment input changes:
- new protocol version required.

---

## 15. Preflight

Before formal collection:
1. verify Git/map/environment locks;
2. verify GPU 1 clean;
3. run task-local parser/config checks;
4. optional one-cycle infrastructure dry-run on development-exposed trial 90, clearly marked `PREFLIGHT_ONLY`;
5. do not include preflight data in formal analysis.

No primary-85 trial may be consumed as a preflight.

---

## 16. Output package

Required committed summaries/locks:
- `FORMAL_INPUT_LOCK.json`
- `FORMAL_PROTOCOL_V2.json`
- `FORMAL_TRIAL_MANIFEST_V2.csv`
- `FORMAL_ENVIRONMENT_MANIFEST.json`
- `FORMAL_DIFFICULTY_STRATA.csv`
- `FORMAL_ARM_SUMMARY.csv`
- `FORMAL_PAIR_SUMMARY.csv`
- `FORMAL_SAFETY_SUMMARY.json`
- `FORMAL_LIVENESS_SUMMARY.json`
- `FORMAL_RUNTIME_SUMMARY.json`
- `FORMAL_ACTIVE_DIAGNOSTICS.json`
- `FORMAL_INTEGRITY_REGISTER.csv`
- `FORMAL_STATISTICAL_ANALYSIS.json`
- `FORMAL_RAW_EVIDENCE_MANIFEST.json`
- `REPORT_FORMAL_PAIRED_EXPERIMENT_V2.md`

Raw per-step/state/trace data may remain server-side; commit hashes/manifests and compact summaries, not giant raw dumps.

---

## 17. Paper-facing tables and figures

Minimum final outputs:

**Table 1 — Main paired benchmark**
- collision proxy;
- margin violation;
- progress mean/median;
- goal reached;
- steps;
- runtime median/p95.

**Table 2 — Active Runtime diagnostics**
- action roles;
- L1/C0/L2/L3 outcomes;
- deadline states;
- token events;
- integrity outcomes.

**Figure 1**
Paired Reference vs Active normalized-progress scatter with `y=x`.

**Figure 2**
Distribution of paired progress deltas.

**Figure 3**
Per-trial Active/Reference compute-time ratios.

**Figure 4**
Progress and runtime by prespecified HARD/MODERATE/EASY geometry strata.

If both arms have zero safety events, do not manufacture a “safety improvement” plot; report parity and focus on certificate/runtime behavior.

---

## 18. Interpretation rules

If Active safety events = 0 and progress passes non-inferiority:
- claim **represented-map safety preservation with negligible/ bounded liveness degradation on the frozen benchmark**.

If Reference and Active safety are both 0:
- do **not** claim collision reduction;
- say the natural Stonehenge cohort did not produce safety discordance.

If Reference has violations and Active does not:
- paired safety improvement may be reported, with exact paired counts.

If Active has any represented-map collision proxy or certification-margin violation:
- primary safety gate fails; investigate before making a positive safety claim.

If progress non-inferiority fails:
- do not tune on the same formal data and rerun under V2;
- treat as a negative formal result or create a new method/protocol version with clearly separate data.

---

## 19. Claim boundary

Allowed only if supported:
- represented-map safety-proxy results;
- progress non-inferiority on this fixed benchmark;
- runtime overhead under this engineering profile;
- observed backup/terminal/boundary behavior.

Not allowed:
- physical collision-free guarantee;
- hard real-time guarantee;
- deployment readiness;
- global path-planning completeness;
- map-independent guarantee;
- generalization beyond this map/controller/dynamics without further experiments.

---

## 20. What is permanently frozen once formal collection starts

Do not change:
- trial IDs or cohort labels;
- execution order or pair arm-order rule;
- method commit;
- map/checkpoint;
- controller/QP gains;
- actuator bounds;
- dynamics/dt;
- geometry radii;
- deadline values;
- oracle;
- max_steps;
- primary endpoints;
- non-inferiority margin;
- bootstrap seed/resamples;
- eligibility rules;
- difficulty score or bins.

`FINAL_PROTOCOL_DECISION=FREEZE_AND_COLLECT_FORMAL_PAIRED_EXPERIMENT_V2`

The next action after repository lock is **formal collection**, not more method tuning.
