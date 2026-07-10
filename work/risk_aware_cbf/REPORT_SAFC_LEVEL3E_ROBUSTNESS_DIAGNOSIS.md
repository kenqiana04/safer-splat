# REPORT: SAFC Level-3E Robustness and Failure-Diagnosis Audit

## 1. Purpose

This report performs a bounded robustness and failure-diagnosis audit for
warning-streak slowdown after the Level-3D small targeted cohort produced
mixed outcomes.

This is a bounded diagnostic audit, not a full benchmark. It does not claim
generalized safety-performance improvement, collision reduction, warning
reduction, planning-accuracy improvement, statistical significance,
real-robot readiness, or a new CBF theorem.

SAFC Level 3E validates bounded robustness and failure-diagnosis behavior only.

## 2. Setup

| Item | Value |
| --- | --- |
| Branch | `safc-level3e-robustness-diagnosis` |
| Base branch | `safc-level3d-small-targeted-cohort` |
| Base commit | `5753d7f82ed447b09ac75bab8deb0887b1922557` |
| Included candidates | C003, C004, C002, C001, C006 |
| Variants | current_policy, milder_slowdown, critical_only_slowdown |
| Entrypoint | `reproduction/scripts/run_official_runpy_smoke.py` |
| DT margin | 0.0005 |
| Horizon | H3 |
| Maximum steps | 160 |
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

### 3.1 Diagnostic motivation

Level 3D showed a lower total warning count for the current active slowdown
policy, but also showed mixed candidate-level behavior: C004 became worse,
C006 remained neutral, and no candidate reached the goal. Level 3E therefore
diagnoses robustness and failure modes instead of expanding to a benchmark.

### 3.2 Policy variants

Three pre-registered active variants were evaluated:

| Variant | warning | persistent | critical | min | Interpretation |
| --- | ---: | ---: | ---: | ---: | --- |
| current_policy | 0.75 | 0.50 | 0.25 | 0.25 | Reference Level-3D active slowdown |
| milder_slowdown | 0.85 | 0.70 | 0.50 | 0.50 | Diagnose whether aggressive slowdown contributes to mixed outcomes |
| critical_only_slowdown | 1.00 | 1.00 | 0.50 | 0.50 | Diagnose whether avoiding H1/H2 slowdown changes outcomes |

### 3.3 Diagnostic runs

The audit ran 5 candidates x 3 variants. Each run used wrapper-level command
scaling only after a natural warning gate. It did not modify `u_nom`, internal
`u_safe`, CBF-QP, dynamics, planner logic, recovery logic, or GSplat queries.

Only compact summaries were retained. No raw trace, per-step dump, full
`trials.csv`, active constraints, trajectory samples, JSONL logs, images, or
binary files are included.

## 4. Results

| Metric | Result |
| --- | ---: |
| Diagnostic runs planned | 15 |
| Diagnostic runs completed | 15 |
| current_policy total warning steps | 164 |
| milder_slowdown total warning steps | 182 |
| critical_only_slowdown total warning steps | 182 |
| current_policy completed count | 0 |
| milder_slowdown completed count | 0 |
| critical_only_slowdown completed count | 0 |
| current_policy collision count | 0 |
| milder_slowdown collision count | 0 |
| critical_only_slowdown collision count | 0 |
| current_policy QP infeasible count | 0 |
| milder_slowdown QP infeasible count | 0 |
| critical_only_slowdown QP infeasible count | 0 |
| Control scope all passed | true |
| All slowdown after or at warning | true |
| Progress proxy available | true |

| Candidate | Outcome class | current warnings | milder warnings | critical-only warnings | Best by warnings | Stop reason pattern |
| --- | --- | ---: | ---: | ---: | --- | --- |
| C003 | positive | 10 | 11 | 11 | current_policy | stalled_before_goal for all variants |
| C004 | negative | 68 | 64 | 64 | milder_slowdown / critical_only_slowdown | max_steps for all variants |
| C002 | positive | 24 | 34 | 34 | current_policy | max_steps for all variants |
| C001 | positive | 21 | 32 | 32 | current_policy | max_steps for all variants |
| C006 | neutral | 41 | 41 | 41 | all tied | max_steps for all variants |

The compact progress proxy was `goal_distance_reduction`. It is available for
all runs, but it is a diagnostic scalar only and is not a completion or
planner-quality metric.

## 5. Interpretation

The current policy remains the lowest total-warning variant in this small
targeted cohort, but the result is mixed. C004 remains a negative diagnostic
case for the current policy because its current-policy warning count is 68,
above the Level-3D baseline reference of 64. Milder and critical-only variants
reduce C004 to 64 in this audit, which suggests the C004 negative behavior is
scale-sensitive. This supports policy tuning investigation, not a generalized
performance claim.

C006 remains neutral under all tested variants: current, milder, and
critical-only policies all produce 41 warning steps. This suggests slowdown may
not affect warning behavior in that context.

For C003, C002, and C001, current_policy gives the lowest warning count among
the tested variants. However, no variant reaches the goal in any candidate.
The stop reasons are unchanged by variant in this audit: C003 stalls before
goal, while C004, C002, C001, and C006 reach the maximum step budget.

The best variant is a diagnostic observation over the small targeted cohort,
not benchmark-level evidence.

The variant result is a bounded diagnostic observation over the small targeted
cohort, not generalized evidence.

Because active commands can alter subsequent trajectories, post-activation
comparisons are targeted behavioral observations rather than same-trajectory
causal proof.

## 6. What Level 3E Validates

Level 3E validates only the following:

* pre-registered bounded diagnostic variants were executed;
* mixed candidate-level outcomes were diagnosed;
* command scope remained wrapper-level;
* C004 and C006 behavior was characterized;
* stop-reason and compact progress-proxy limitations were recorded; and
* no CBF-QP, dynamics, planner, recovery, or GSplat query modification was
  made.

## 7. What Level 3E Does Not Validate

Level 3E does not validate:

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

Level 3E is sufficient to prepare a final SAFC method-validation package with
strict claim boundaries. It does not justify expanding active-policy claims or
presenting any variant as a benchmark-validated improvement.

The recommended next packaging step is to retain C004 as negative evidence,
describe C006 as neutral evidence, and present the policy-variant differences
as bounded failure-diagnosis observations only.

## 9. Artifacts

| Artifact | Path |
| --- | --- |
| Runner | `work/risk_aware_cbf/scripts/safc_level3e_robustness_diagnosis.py` |
| Results README | `work/risk_aware_cbf/results/safc_level3e_robustness_diagnosis/README.md` |
| Preregistration | `work/risk_aware_cbf/results/safc_level3e_robustness_diagnosis/diagnosis_preregistration.csv` |
| Variant config | `work/risk_aware_cbf/results/safc_level3e_robustness_diagnosis/variant_config.csv` |
| Per-candidate variant summary | `work/risk_aware_cbf/results/safc_level3e_robustness_diagnosis/per_candidate_variant_summary.csv` |
| Variant aggregate summary | `work/risk_aware_cbf/results/safc_level3e_robustness_diagnosis/variant_aggregate_summary.csv` |
| Mixed outcome diagnosis | `work/risk_aware_cbf/results/safc_level3e_robustness_diagnosis/mixed_outcome_diagnosis.csv` |
| Stop reason diagnosis | `work/risk_aware_cbf/results/safc_level3e_robustness_diagnosis/stop_reason_diagnosis.csv` |
| Control scope summary | `work/risk_aware_cbf/results/safc_level3e_robustness_diagnosis/control_scope_summary.csv` |
| Progress proxy summary | `work/risk_aware_cbf/results/safc_level3e_robustness_diagnosis/progress_proxy_summary.csv` |
| Metrics | `work/risk_aware_cbf/results/safc_level3e_robustness_diagnosis/metrics.json` |
| Notes | `work/risk_aware_cbf/results/safc_level3e_robustness_diagnosis/robustness_notes.md` |
