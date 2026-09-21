# Formal85 Retry3 结果解释（post-collection analysis）

## 结论先行

- 分析状态：`PASS_POST_REPAIR_V3_BOUNDED_RECOVERY_PAIRED_VALIDATION_ON_FROZEN_STONEHENGE_BENCHMARK`。
- 这是固定 Stonehenge、85 对、冻结 Reference 的 post-collection 分析；没有重跑 Active、Reference 或任何 trial。
- 进度非劣效：严格比较规则 `lower95 > -0.02`，bootstrap 95% CI 下界为 `0.045098153562`，高于 margin `-0.02`，因此 `strict_ni_pass=true`。`equality_at_margin=FAIL` 仅表示没有“恰好等于 margin”，不是该严格 NI 判据失败。
- 代表图硬安全与完整性：硬违规段 `0`、硬 UNKNOWN 段 `0`、active-only discordant pair `0`，hard gate PASS。

## 硬安全与完整性

`global_min_hard_clearance_q=4.591307551154856e-09`，在 `epsilon=null`、`negative_tolerance=null` 的冻结合约下仍为正；但其数量级非常接近零，属于 near-boundary engineering signal，不能解读为安全裕度充足。30/30 个冻结 hard-zero continuity/integrity gate 均为零，Recovery L2 evidence rewrite、candidate-scoped 缺失/冲突、legacy Primary flat evidence corruption、identity/state/routing/process/trace/token 等均未见非零项。

## 进度非劣效与历史对照

本次 85 对：mean delta `0.091345522702`，median `0.032053357817`，min `-0.834309191930`，positive/zero/negative=`80/0/5`，bootstrap 95% CI=`[0.045098153562, 0.139868982848]`。

冻结的上一版 repaired-Active historical comparator 仍是 `FAIL_POST_REPAIR_V3_PROGRESS_NONINFERIORITY_GATE`：mean delta `0.017854900314`、CI=`[-0.035388219429, 0.069346557643]`。本次 mean delta 变化为 `0.073490622388`，CI 下界变化为 `0.080486372992`。这些是同一冻结 Stonehenge 85 对上的描述性比较，不是因果归因，也不改变历史 verdict。

## Routing 与 Recovery

35343 个 public cycles 中，角色 commit 总数为 `35309`，另有 boundary/no-plant `34`。角色计数与角色分母比例：Primary `26682` / `0.755671358577`、retained Backup `5623` / `0.159251182418`、Recovery `840` / `0.023789968563`、Terminal `2164` / `0.061287490442`。角色比例的分母是 `35309` 个角色 commit；若以全部 public cycles 为分母，Terminal share 为 `0.061228531817`。历史 comparator 的 terminal fraction 为 `0.629882352941`（历史角色总数 `42500`）。差异只能作为机制诊断信号，不能宣称 Recovery 导致改善。

Recovery 计数：eligibility/scans/attempts=`874/874/970`；L2 enter/result/pass/fail/unknown/exception=`970/970/874/96/0/0`；L3 result/pass/fail/unknown/exception=`874/874/0/0/0`；selected/PlantCommit=`840/840`。比率为 selected/eligibility=`0.961098398169`、PlantCommit/selected=`1.000000000000`、attempts/eligibility=`1.109839816934`；rank-resume=`96`，exhaustion=`0`。这确认修复后的 candidate-scoped L2 路径可完成分析闭环，但不是 efficacy 结论。

## Boundary 记录

Boundary rows=`34`，trial IDs（按实际 boundary evidence 顺序）为：`74, 12, 73, 79, 54, 29, 0, 24, 98, 78, 82, 56, 21, 33, 44, 14, 61, 43, 47, 51, 42, 13, 49, 97, 53, 58, 34, 17, 62, 52, 22, 84, 57, 46`。`typed_boundary_contract_valid` 无效数为 `0`。boundary 最后实际 committed progress 分布：min=`0.000000000000`、median=`0.102422443685`、max=`0.863114471869`。部分 trial 在早期无 plant commit，部分在较晚周期进入 boundary；分析保留其最后 committed state，没有插值或排除。若 boundary row 的 `final_supervisor_reason` 显示 `ROUTING_RULE_MISSING`，它仍按 frozen typed boundary contract 记账，不被改写成 hard-safety failure；同时这是后续 routing diagnosis 的明确工程信号。

## 研究边界与下一步

在当前冻结统计合约下，bounded-recovery Retry3 的严格 NI 判据通过，因此相对于旧版 NI failure，当前分析给出“本次 85 对未复现该统计门失败”的结果；这不等于因果证明，也不改变旧版历史 verdict。证据边界是“repeatedly exposed frozen Stonehenge 85”；不支持跨场景泛化、pristine holdout、物理世界安全、部署 readiness 或 hard real-time guarantee。下一步应先审计/修复 boundary routing rule coverage，并对 near-zero hard clearance 做定向工程诊断；之后如仍需要，才在不改 frozen contracts 的前提下设计独立复现实验。不得把本结果包装成 collision reduction、controller efficacy 或因果性能改进。
