# SAFC Level-3D Small Targeted Cohort Notes

## Scope

This is a small targeted cohort A/B comparison over pre-registered
warning-rich candidates. It is not a full benchmark and does not claim
generalized performance improvement.

## Preregistered Cohort

* Included candidates: C003, C004, C002, C001, C006
* Excluded candidates: C005 (`sensitivity_only_warning`), C007 (`initial_collision_diagnostic_context`)
* Fixed `dt_margin`: 0.0005
* Fixed horizon: H3
* Fixed `max_steps`: 160

## Baseline Runs

* C003: 11 warnings, stop `stalled_before_goal`
* C004: 64 warnings, stop `max_steps`
* C002: 38 warnings, stop `max_steps`
* C001: 35 warnings, stop `max_steps`
* C006: 41 warnings, stop `max_steps`

Baseline commands execute the original `u_safe` unchanged. No slowdown,
recovery, planner, CBF-QP, dynamics, or GSplat query modification is enabled.

## Active Runs

* C003: 10 warnings, 10 slowdown-active steps, stop `stalled_before_goal`
* C004: 68 warnings, 68 slowdown-active steps, stop `max_steps`
* C002: 24 warnings, 24 slowdown-active steps, stop `max_steps`
* C001: 21 warnings, 21 slowdown-active steps, stop `max_steps`
* C006: 41 warnings, 41 slowdown-active steps, stop `max_steps`

Active runs apply warning-streak slowdown only under a natural warning gate.
They do not modify `u_nom`, internal `u_safe`, CBF-QP, dynamics, planner,
or recovery logic.

## Cohort Observation

* Candidates with fewer warning steps under active: 3 (C003, C002, C001)
* Candidates with equal warning steps under active: 1 (C006)
* Candidates with more warning steps under active: 1 (C004)
* Total warning-step delta, active minus baseline: -25
* Baseline / active collision counts: 0 / 0
* Baseline / active QP infeasible counts: 0 / 0
* Baseline / active completed counts: 0 / 0

Per-candidate observations:

* C003: delta -1, Small-cohort fixed-candidate observation for C003: active recorded 1 fewer warning steps; baseline stop=stalled_before_goal, active stop=stalled_before_goal.
* C004: delta 4, Small-cohort fixed-candidate observation for C004: active recorded 4 more warning steps; baseline stop=max_steps, active stop=max_steps.
* C002: delta -14, Small-cohort fixed-candidate observation for C002: active recorded 14 fewer warning steps; baseline stop=max_steps, active stop=max_steps.
* C001: delta -14, Small-cohort fixed-candidate observation for C001: active recorded 14 fewer warning steps; baseline stop=max_steps, active stop=max_steps.
* C006: delta 0, Small-cohort fixed-candidate observation for C006: warning-step count was unchanged; baseline stop=max_steps, active stop=max_steps.

Because active commands can alter subsequent trajectories, post-activation
comparisons are targeted behavioral observations rather than same-trajectory
causal proof.

## Claim Boundaries

* small targeted cohort only
* no full benchmark
* no statistical significance
* no generalized performance improvement
* no generalized collision reduction
* no generalized warning reduction
* no planner integration
* no real-robot validation
* no global safety guarantee
* no new CBF theorem
