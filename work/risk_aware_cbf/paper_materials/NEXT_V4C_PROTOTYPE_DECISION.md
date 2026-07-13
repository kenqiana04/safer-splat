# Next V4-C Prototype Decision

## Decision

**Primary: R-V4C-1 Hierarchical Candidate Evaluation.**

It targets the strongest supported failure pressure: repeated activated candidate evaluation dominates V4-C runtime. It is substantively different from original all-family evaluation, preserves original deterministic candidate families, does not change CBF-QP or introduce a planner, and can be tested as a bounded module-only smoke after separate authorization.

**Backup: R-V4C-5 Trigger-Severity-Aware Recovery.**

It is mechanism-distinct from staged candidate evaluation: it changes when full search is entered rather than how an entered search is evaluated. It remains bounded and does not require an R1 selector.

**Deferred: R-V4C-2, R-V4C-3, R-V4C-4.**

Adaptive budgets need family contribution evidence, recovery memory needs recurrence evidence and a safe context key, and Pareto selection needs measured safety-progress tradeoffs. Implementing them now would turn an analysis task into an under-instrumented redesign.

## Primary Prototype Contract

1. Run Stage A only on original baseline, braking, repulsive, goal-directed, and continuity families.
2. Accept the original minimum-cost feasible Stage-A candidate if one exists.
3. Run original random/CEM generation and original evaluation only if Stage A has no feasible candidate.
4. Preserve original clamps, seeds, horizon, safety queries, cost, fallback, first-control execution, and post-step replan.
5. Record compact stage counts/runtime only; do not retain raw controls or traces.

## Falsification and Stop Rules

The later bounded smoke must pre-register a small fixed activated cohort and an original V4-C comparator. It succeeds only if all comparator-feasible contexts remain feasible, there is no collision/QP/execute-horizon-margin regression, and activated-step median recovery runtime is at least 20% lower. It fails if any comparator-feasible context loses feasibility, any safety regression occurs, or the runtime target is not met. A failed smoke stops this branch; it does not authorize budget tuning, R1 work, or a different redesign in the same task.

## Why Not Parameter Tuning

The prior H2/N64 result is useful evidence that sequence-evaluation cost matters, but changing H or N alone is not a module redesign. The primary proposal changes evaluation order while keeping original recovery goal and candidate semantics available as the fallback search.

## Next Boundary

R1 remains paused. The next task, if separately authorized, is one bounded V4-C-only primary-prototype smoke with a fixed cohort and explicit aggregate instrumentation. It must not run flight20/full100, active R1, planner work, or safe-halt work.

## Held-Out Validation Update

R-V4C-1 V0 passed its comparator-defined flight H3_N128 held-out cohort: 16 trials and 201 activation contexts, with zero paired feasibility regression, zero collision/QP regression, unchanged progress, and a 79.47% activated-step median runtime reduction. Stage A selected 167 contexts; Stage B entered the remaining 34 and preserved the original full-search failed outcome. Retain this V0 only as a configuration-specific recovery-efficiency mechanism; R1 remains paused and cross-scene/generalized claims remain unsupported.
