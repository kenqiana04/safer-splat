# Figure and Table Captions for SAFC

## 1. Figure: Feedback-Augmented Safety Assurance Architecture

**English caption.** **Feedback-augmented GSplat safety assurance
architecture.** The Safety-Assurance Feedback Coordinator (SAFC) aggregates
Start-Safe admission status, CBF-QP feasibility and intervention signals,
H-step verification warnings, recovery outcomes, and deployment-interface
validity. It emits bounded command-shaping, recovery, planner-feedback,
target-rejection, and halt actions. Start-Safe, CBF-QP, DT Verification, and
named triggered V4-C behavior form the current evidence-backed path; planner
feedback and robot deployment arrows denote interfaces or future integration,
not implemented planning or a global safety guarantee.

**中文解释。** 图中 SAFC 汇总 Start-Safe、CBF-QP、DT Verification、Recovery
和部署接口信号，并输出有界 slowdown、recovery trigger、replan/risk-cost、
target rejection 与 halt。必须用线型或颜色区分已有主方法、接口级功能和未来
真实小车/规划器集成，不能把接口箭头解释成已实现 planner 或全局安全保证。

## 2. Figure: SAFC Finite-State Machine

**English caption.** **Finite-state supervisory specification for SAFC.** The
state machine separates S0 pre-execution certification, S1 nominal filtering,
S2 verified execution, S3 warning-aware execution, S4 recovery, S5 external
replan request, and S6 safe halt/abort. Hysteresis requires a clear streak
before returning from warning mode, post-recovery execution is re-verified,
and invalid interfaces or unrecoverable failures transition conservatively to
S6. The diagram is an architecture specification, not evidence of a fully
implemented supervisor or global safety proof.

**中文解释。** 图中应完整展示 S0–S6、`K_enter/K_exit` 滞回、recovery 后重新
verification，以及 invalid interface / unrecoverable failure 到 S6 的保守转移。
S5 只向外部 planner 发请求，不表示仓库实现了 planner；状态机整体目前是理论
规格，不是已完成实验模块。

## 3. Table: SAFC Input and Output Signals

**English caption.** **SAFC signal interface.** Inputs are grouped by
Start-Safe, CBF-QP, H-step DT Verification, Triggered Recovery, nominal
command/external planner, and deployment validity. Outputs are grouped into
command slowdown, recovery trigger, replan request, risk-cost update,
waypoint/goal rejection, and safe halt. Status labels identify current support,
interface-level definitions, and future extensions; a DT margin warning remains
distinct from collision.

**中文解释。** 表格要按六类来源列出输入，并按六类反馈动作列出输出，同时增加
status 与 non-claim。特别标注 DT warning 不是 collision，planner/deployment
信号是接口，不是已完成实现。

## 4. Table: Feedback Contract Summary

**English caption.** **Contract-level mapping from safety evidence to bounded
feedback actions.** Each feedback contract records its input, trigger, output,
assumptions, assurance scope, implementation status, and non-claim.
Verification-to-recovery is supported in named V4-C settings, whereas generic
command shaping, replanning, risk-cost integration, waypoint screening, and
robot halt require interface-specific or future validation. Contract
composition does not establish a global safety guarantee.

**中文解释。** 每个 feedback action 都必须有 trigger、output、scope、status
和 non-claim。只有已追踪 V4-C 配置支持 verification-to-recovery；其他规划器
反馈和机器人 halt 仍是接口或未来工作，不能由 contract 表推导出全局安全。

## 5. Table: Implemented vs Interface vs Future Work

**English caption.** **Evidence and implementation boundary of the
feedback-augmented framework.** The table separates current method components
and tracked support, architectural interfaces, future planner integration, and
future real-robot validation. It prevents planner-facing feedback or deployment
contracts from being reported as completed planner, localization, four-wheel,
or end-to-end navigation results.

**中文解释。** 表格用于明确 current method / supported、interface-level 和
future work。应把 Start-Safe、CBF-QP、DT Verification、已命名 V4-C 证据与
SAFC 整体状态机、planner feedback、real-robot adapter 分开，防止把理论接口
写成已经完成的 planner、localization、四轮动力学或完整导航栈验证。
