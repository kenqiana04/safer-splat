# Figure and Table Captions for Theoretical Systematization

## 1. Figure: Safety Assurance Pipeline

**English caption.** **Safety assurance pipeline for GSplat-based navigation.**
An external or baseline nominal command source and the existing GSplat CBF-QP
form the baseline path. The proposed assurance modules are Start-Safe
Feasibility Certification, H-step Discrete-Time Verification, and optional
warning-triggered V4-C Predictive Recovery. Adaptive V1, FC-Aware V1, and
primitive MPC-style recovery are shown, if included, only as diagnostic or
ablation branches. The pipeline states module-level, model- and
configuration-dependent assurances; it is not a global safety guarantee.

**中文解释。** 图中应把外部/基线 nominal command 与现有 GSplat CBF-QP 标为
baseline，把 Start-Safe、H-step DT Verification 和可选触发式 V4-C 标为本文
提出的 assurance modules。Adaptive、FC-Aware 与 primitive MPC-style 只能放在
诊断/消融支线，不能画成主方法。图注必须明确这是模块级、模型相关的保障流程，
不是全局安全保证。

## 2. Figure: Failure-Mode Taxonomy

**English caption.** **Deployment-relevant failure-mode taxonomy.** The
taxonomy separates F1 start-state unsafety, F2 CBF-QP feasibility failure, F3
sampled-data margin risk, and F4 recovery insufficiency. Baseline filtering
exposes the command and instantaneous-QP interfaces; the proposed Start-Safe,
DT Verification, and triggered recovery modules address the corresponding
assurance gaps. Diagnostic branches are excluded from the main chain. The
taxonomy distinguishes infeasibility, margin warning, and collision and does
not constitute a global safety proof.

**中文解释。** 该图按执行阶段展示四类 failure modes，并把每类问题映射到对应
模块。baseline 负责 nominal command 与瞬时 CBF-QP；本文模块负责起点认证、
离散时间验证和风险触发恢复。图中必须把 QP infeasibility、DT margin warning
和 collision 分开，且说明 taxonomy 不是全局形式化证明。

## 3. Table: Failure Mode to Module Mapping

**English caption.** **Mapping from deployment failure modes to assurance
modules and evidence.** The table links each baseline limitation to a proposed
response, observable metrics, and tracked evidence source. Start-Safe, H-step
DT Verification, and optional triggered V4-C are proposed modules; the
nominal-command source and CBF-QP are baseline interfaces; Adaptive, FC-Aware,
and primitive MPC-style variants are diagnostic-only evidence. Reported
coverage is empirical and contract-bounded, not a global safety guarantee.

**中文解释。** 表格用于证明“每个模块解决一个明确问题”，同时列出观测指标和
证据来源。应明确 baseline、proposed modules 与 diagnostic-only 分支，避免把
消融模块包装成最终方法，也避免把实验覆盖范围写成全局保证。

## 4. Table: Assurance Contract Summary

**English caption.** **Module-level assurance contracts.** Each row specifies
the input, output, assumption, assurance scope, failure condition, and
non-claim for the nominal-command interface, Start-Safe certification,
baseline CBF-QP filtering, H-step DT Verification, triggered V4-C recovery,
and the future real-robot adapter. The proposed contracts structure component
responsibilities but do not compose automatically into a global safety
guarantee.

**中文解释。** 该表覆盖 baseline nominal/CBF-QP、本文 Start-Safe/DT
Verification/V4-C，以及未来真实小车 adapter。诊断分支不应获得主方法 contract。
每行都要写清输入输出、假设、失败条件与 non-claim；多个 contract 拼接不等于
自动得到全局安全定理。

## 5. Table: Claim Boundary Table

**English caption.** **Claim boundary and evidence table.** Candidate claims
are classified as supported, unsupported, or not yet validated and rewritten
to match the available evidence. Supported claims concern repository-scoped
start certification, finite-horizon verification, tested triggered recovery,
and planner-agnostic interfacing. Planner, localization, four-wheel dynamics,
diagnostic-branch success, and global safety claims are excluded. This table
is a reporting safeguard, not an additional safety guarantee.

**中文解释。** 该表把能说、不能说和尚未验证的 claim 分开。可支持内容限于
仓库安全场下的起点认证、有限时域验证、已测试的触发式恢复和 planner-agnostic
接口；global/local planner、localization、four-wheel dynamics、诊断分支成功和
global safety 都不能过度声称。表本身是论文写作约束，不是新的安全保证。
