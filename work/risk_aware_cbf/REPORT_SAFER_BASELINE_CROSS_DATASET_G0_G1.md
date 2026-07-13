# REPORT: SAFER Baseline Cross-Dataset Generalization Audit G0-G1

## 1. Purpose

本报告审计原始 SAFER baseline 的数据资产可移植性与有界 smoke 前置条件，不评估任何方法改进模块。

## 2. Baseline Definition

固定执行 `simple goal-directed nominal control -> original CBF-QP safety filter -> original double-integrator rollout`。Start-Safe、Risk-Aware、Adaptive、recovery、SAFC、R1、slowdown、VANS 和 planner 均未启用。

## 3. Cross-Scene vs Cross-Dataset Definition

同源场景不计为 cross-dataset；只有可验证的独立数据集来源才可计入 Tier-2/Tier-3。

## 4. Search Scope and Dataset Inventory

搜索根目录为 `/disk1/zlab/projects`、`/disk1/zlab/data`、`/disk1/zlab/datasets`、`/disk1/zlab/checkpoints`、`C:\Users\zlab\Documents` 和 `C:\Users\zlab\Desktop`。本地发现 525 个候选目录。

## 5. Dataset Provenance

来源已验证条目数为 1（含 Tier-R reference）。独立 true cross-dataset family 数为 0。

## 6. Selection Preregistration

预注册 Tier-2/Tier-3 场景数为 0。G0 未使用任何 baseline 运行结果进行选择。

## 7. GSplat Compatibility

兼容 query 场景数为 0；可进入 navigation smoke 的场景数为 0。

## 8. Scale and Coordinate Transfer

没有独立候选达到已验证来源与尺度合同，因此没有猜测尺度或按场景调整 robot radius。

## 9. Navigation-Volume Contract

没有独立候选提供经预注册的可导航自由空间、start region 和 goal region。

## 10. Parameter-Transfer Contract

合同文档已建立；当前 `parameter_transfer_contract_passed=false`，因为尚无合规跨数据集场景进入执行。

## 11. Reference Harness Parity

`reference_parity_run=false`，`reference_parity_passed=false`。G0 阻断后未运行 parity。

## 12. Initial Start/Goal Admission

候选 pair 数为 0，admissible pair 数为 0；未执行 repair。

## 13. Original Baseline Smoke Protocol

`formal_smoke_run_count=0`。没有 full100、flight20 或新的科学实验。

## 14. Dataset-Level Results

没有合规的独立数据集 smoke 结果。

## 15. Safety Evidence

内部 `h` collision 和 geometry-grounded collision 严格分列；当前两者均未测量（`null`）。

## 16. DT Warning Diagnostics

H1/H2/H3 为不干预的诊断项；当前未测量（`null`）。

## 17. Runtime and Constraint Behavior

当前没有 runtime 或 active-constraint 测量。

## 18. Failure-Mode Distribution

blocked_by_cross_dataset_asset_availability：问题位于数据来源、许可、尺度或兼容 GSplat 资产可用性，而不是已测得的 baseline 行为失败。

## 19. Negative and Neutral Evidence

未验证来源的本地文件不能作为 cross-dataset 证据；也不应被解释为 SAFER 机制无法泛化。

## 20. Generalization Interpretation

当前没有 cross-dataset performance claim。loader 或单条 smoke 的成功本身也不会构成泛化结论。

## 21. Decision

`audit_decision=blocked_by_cross_dataset_asset_availability`。不建议进入 G2 small baseline cohort。

## 22. Claim Boundaries

The G0-G1 audit evaluates original SAFER baseline portability and bounded cross-dataset smoke only. It does not validate any of the proposed method-improvement modules.
