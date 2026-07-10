# Next Method Prototype Decision

## Selected Primary Prototype

Selected prototype: **R1 Verification-Aware Supervisory Mode Selection**.

Selected hypothesis: H7, verification-aware supervisory mode selection can
select among existing bounded modes more effectively than a single slowdown
action.

Candidate modes are limited to:

- execute existing CBF-filtered command;
- warning-gated slowdown;
- existing V4-C recovery;
- safe halt.

This is not a planner. It does not generate waypoints, optimize paths, or add a
new local planner. It is SAFC coordination over already verified or contracted
modes.

## Backup Prototype

Backup prototype: **R4 Persistent-Warning Triggered Recovery Coordination**.

R4 should be used if R1 is too broad for a first smoke. It only changes the
triggering rule around existing V4-C recovery and therefore keeps the strongest
current positive recovery evidence.

## Deferred Designs

- R2 Controller-Compatible Primitive Selection: deferred until action
  semantics for directional/primitive commands are grounded.
- R3 Verifier-Informed Nominal Objective Shaping: deferred because it risks
  nested optimization and planner-boundary crossing.

## Why Previous Versions Do Not Test R1

- Warning-streak slowdown tested only one post-filter magnitude-scaling mode.
- VANS-v0 tested only pre-filter magnitude-scaled nominal candidates in
  shadow mode.
- V4-C tested predictive recovery as a triggered module, not selection among
  slowdown/recovery/halt/normal modes.
- Risk-Aware and FC-Aware versions tested candidate budgeting/selection
  efficiency, not supervisory mode choice.

## Implementation Boundary

The minimum prototype must:

- live under `work/risk_aware_cbf/`;
- avoid modifying `cbf/`, `splat/`, `ellipsoids/`, `dynamics/`, and `run.py`;
- use existing H-step warning signals and existing V4-C configuration;
- use a fixed rule table, not learned or optimized mode selection;
- start in shadow/offline mode before any active execution;
- write compact summaries only.

## Exact Success Criteria

Minimum shadow success:

- formal no-op trajectory unchanged;
- state isolation passes;
- in at least one C004 or C006 warning context, a non-slowdown mode is selected
  by the fixed rule table for an interpretable reason;
- selected mode has verified H-step improvement over the original or slowdown
  alternative in the shadow audit;
- no planner-boundary or core-source modification is required.

Minimum active smoke success:

- one targeted case only;
- no collision or QP infeasible event introduced by the supervisor;
- command/mode scope matches the preregistered rule;
- recovery/halt/slowdown activation is explainable from warning state.

## Exact Failure Criteria

The R1 version fails if:

- the shadow selector never selects a useful non-slowdown mode;
- selected modes do not improve H-step verification in targeted warnings;
- the policy requires new planner semantics;
- V4-C activation cost makes the minimum smoke impractical;
- mode selection reduces to arbitrary parameter tuning.

## Stopping Condition

Stop R1 version after the shadow audit and one targeted smoke if no useful
mode difference appears. Do not run a cohort or full100 before this.

Stop the broader mode-selection family only if a second substantially
different mode-selection rule also fails for the same structural reason under
validated instrumentation.

## Maximum Run Budget

Maximum first-stage budget:

- one semantics/interface audit;
- one shadow audit over at most the five existing C001/C002/C003/C004/C006
  contexts;
- one active smoke on one preselected target context;
- no automatic cohort;
- no full100 or flight20.

## Next Experiment Ladder

1. Stage 0: write H7 and mode table.
2. Stage 1: compare mode-selection design against R2/R3/R4.
3. Stage 2: audit interfaces and mode semantics.
4. Stage 3: run shadow feasibility only.
5. Stage 4: run one active smoke only if Stage 3 passes.
6. Stage 5: small preregistered cohort only after a successful smoke.

## Contribution Status

If successful, R1 could become an optional SAFC coordination contribution. It
should not become the core method unless later evidence shows it is necessary,
bounded, and reproducible beyond targeted smoke.
