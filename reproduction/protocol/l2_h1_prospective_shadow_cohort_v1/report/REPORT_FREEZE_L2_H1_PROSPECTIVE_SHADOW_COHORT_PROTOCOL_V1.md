# Report: Freeze L2/H1 Prospective Shadow Cohort Protocol V1

## Technical summary

**PASS_L2_H1_PROSPECTIVE_SHADOW_COHORT_PROTOCOL_FREEZE_V1 — CASE_A.** Before any formal prospective navigation or L2 outcome collection, this task freezes the complete Stonehenge official100 manifest, formal identity namespace, QA exclusions, analysis unit, tri-state primary endpoint, final PR #99 join semantics, outcome-blind QC, fail-closed retry policy, trial-cluster bootstrap, retention, claims, and deterministic protocol lock.

This is a protocol-freeze result only. It contains no navigation, formal collection, new research data, L2 outcome analysis, performance metric, or runtime metric.

## The frozen protocol answers Q1–Q22

| Question | Frozen answer |
|---|---|
| Q1 | PR #99 Open Draft，head `17bec44c51207bf7f831db724e108b86adb0ace8`，base `validate-l2-h1-shadow-instrumentation-equivalence-v1`。 |
| Q2 | YES；official100 为 100 个唯一 trial ID，稳定整数顺序 0–99。 |
| Q3 | YES；EQUIVALENCE_QA_ONLY、PILOT_QA_ONLY、FROZEN_HISTORICAL_REPLAY 与 PR #98/#99 QA run IDs 永久排除。 |
| Q4 | YES；pilot IDs 10/30/50/70/90 在 formal100 中重新运行，但使用全新 FORMAL run IDs。 |
| Q5 | 唯一 formal data_role：`FORMAL_PROSPECTIVE_SHADOW_COHORT_V1`。 |
| Q6 | 一个 committed control step 的 selected/executed candidate-state-map tuple。 |
| Q7 | 满足 data role、完整 QC、selected committed control、合法 L1 provenance、L1 PASS、L2 reached/tri-state、map 与 join identity 的全部十项条件。 |
| Q8 | 分子为 eligible rows 中 L2 FAIL；分母为所有 eligible PASS+FAIL+UNKNOWN rows。 |
| Q9 | YES；UNKNOWN 保留在 primary denominator。 |
| Q10 | NO；u_des 是 NOMINAL_REFERENCE，不是 native alternative。 |
| Q11 | YES；join contract 直接冻结 PR #99 最终通过 aggregator 与 PR #97 schema 的真实语义。 |
| Q12 | NO；第一条 formal run 后若需变更 join，必须停止 V1 并创建 V2。 |
| Q13 | QC 只看 step/capture/result 存在性、identity、完整率、schema、health、termination 与 raw hashes；不汇总或查看 scientific outcome distribution。 |
| Q14 | 100 个 formal trials 完成且有效 FORMAL_COLLECTION_LOCK 建立后才解锁。 |
| Q15 | 仅第一条 intended step 前、零 capture/result/scientific row 的 PRE_DATA_INFRA_FAILURE 可自动 retry 一次。 |
| Q16 | NO；产生数据后停止 cohort、保留 partial evidence、记录 deviation，禁止自动 retry。 |
| Q17 | 以 formal trial 为 cluster 的 trial-cluster bootstrap percentile CI。 |
| Q18 | seed=20260831，10,000 valid replicates，每次重采样 100 个 trial clusters，max draws=100,000。 |
| Q19 | NO；raw JSONL/log 仅服务器保留，Git raw-log count=0。 |
| Q20 | `e8ea8f3fda15ab81664829ea6f71fcb37f772ad613c13f61007856c16117791a`。 |
| Q21 | navigation_run_count=0；formal_collection_run_count=0。 |
| Q22 | Only next task：COLLECT_L2_H1_PROSPECTIVE_SHADOW_COHORT_V1。 |

## Exact cohort and identity evidence

- Source manifest: `reproduction/experiment_protocol_freeze_v1/trial_manifests/stonehenge_official100_manifest.csv`
- Source manifest SHA-256: `1b236bba8173c8a37fb7752fd2e2f09fc569191d6820089759b4be547bd6c344`
- Formal trial count / unique count: `100 / 100`
- Stable run order: `0..99`
- Map authority ID: `65c2e4a5ccfd71a0fa8d633c207397215dd8206d5f8fb77a731c05bcb0109af3`
- Combined protocol SHA-256: `e8ea8f3fda15ab81664829ea6f71fcb37f772ad613c13f61007856c16117791a`
- Formal data role: `FORMAL_PROSPECTIVE_SHADOW_COHORT_V1`

The five pilot trial IDs remain in the official100 scientific design but none of their prior QA rows are reused. Fresh FORMAL run identities prevent identity collision.

## Denominator, uncertainty, and collection boundary are fixed

The primary denominator includes every eligible selected/executed row with frozen shadow L1 PASS and completed L2 tri-state PASS/FAIL/UNKNOWN. The primary numerator is L2 FAIL. UNKNOWN cannot be removed after observing results. Trial-cluster bootstrap avoids treating within-trial steps as iid Bernoulli observations.

Collection-stage QC is deliberately outcome-blind: it may validate that an L2 status exists and is typed, but it may not aggregate PASS/FAIL/UNKNOWN, compute the primary endpoint, inspect multi-candidate outcome disagreement, or construct a bootstrap interval.

## Limitations and fail-closed behavior

The future cohort remains a zero-authority shadow observation under the frozen controller. It cannot support causal collision, progress, efficacy, feasibility, real-time, deployment, or physical-safety claims. A post-data infrastructure/QC failure stops V1; neither trial replacement nor hot-fixing and mixing pre/post-change V1 rows is allowed.

No chart is included because this task freezes exact identities and rules and contains no scientific quantitative outcomes; contract tables are the more faithful audit representation.

## Recommended next step

The only permitted next task is `COLLECT_L2_H1_PROSPECTIVE_SHADOW_COHORT_V1`, limited to collection, outcome-blind QC, and data locking. It must verify `e8ea8f3fda15ab81664829ea6f71fcb37f772ad613c13f61007856c16117791a` before the first formal run and must not analyze scientific L2 outcomes.

## Further question

After a valid 100-trial collection lock, scientific analysis remains a separate authorization: `ANALYZE_L2_H1_PROSPECTIVE_SHADOW_COHORT_V1`.
