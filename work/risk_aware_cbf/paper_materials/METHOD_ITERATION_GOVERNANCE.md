# Method Iteration Governance

This governance file defines a fixed research workflow for future method
iterations. The guiding rule is:

Freeze versions, not directions.

A direction is closed only after the direction-level stop rule is met.

## Stage 0: Hypothesis Definition

Required output:

- named hypothesis;
- mechanism family;
- intended benefit;
- unsupported claims;
- falsification condition.

No implementation starts until the hypothesis can be falsified.

## Stage 1: Design-Space Comparison

Required output:

- at least three candidate designs;
- mechanism difference from prior failed versions;
- required interfaces;
- planner-boundary risk;
- recommendation score.

The selected design must be evidence-based, not chosen because it looks likely
to produce the best result.

## Stage 2: Interface and Semantics Audit

Required output:

- exact command/state semantics;
- mutation/isolation plan;
- core-source modification status;
- unsupported dimensions or modes;
- go/no-go for evaluation.

If semantics are insufficient, stop or redesign before running experiments.

### R1 Interface-Stop Application

The R1 Stage 0 audit applied this rule: a historical report or a text snapshot
is not a callable recovery interface. When an included productive mode cannot
be generated, evaluated, and isolated from cloned state, the audit stops before
shadow execution. That is an interface limitation, not a negative method
result, and it does not authorize a substitute control or reconstructed mode.

## Stage 3: Offline / Shadow Feasibility

Required output:

- formal trajectory unchanged if shadow mode;
- compact aggregate summaries;
- state isolation check;
- opportunity and progress-tradeoff metrics;
- no active performance claim.

No per-step dumps, raw traces, or full trials files should be committed.

## Stage 4: Single-Case Active Smoke

Required output:

- one preregistered target case;
- exact command/mode modification boundary;
- collision/QP infeasible status;
- activation reason;
- stop rule.

Passing a smoke does not justify a cohort.

## Stage 5: Small Preregistered Cohort

Required output:

- fixed candidate list before execution;
- no selective reporting;
- per-candidate positive, neutral, and negative outcomes;
- compact aggregate summaries;
- explicit non-validated claims.

## Stage 6: Robustness / Failure Diagnosis

Required output:

- variant matrix;
- negative and neutral cases preserved;
- failure-level classification;
- stop/freeze decision for the version.

## Stage 7: Direction-Level Decision

Required output:

- versions tested;
- mechanism families tested;
- repeated structural causes;
- remaining credible bounded redesigns;
- open/closed decision for each direction.

Do not close a direction after one failed implementation.

## Governance Principles

- No arbitrary parameter sweep before a smoke.
- No full100 before a targeted smoke.
- No active run before a shadow/interface audit if semantics are uncertain.
- No hidden negative evidence.
- No paper drafting from a diagnostic result alone.
- No complexity growth as a substitute for mechanism novelty.
- No metric-clearance claim when only `h` or `min_safety_h` is available.
