# Failure-Mode Taxonomy for GSplat CBF Navigation Safety

## 1. Scope

This taxonomy applies to planner-agnostic GSplat-based safety filtering
pipelines in which an external nominal command is filtered by a CBF-QP and
executed under sampled-data dynamics. It organizes failure modes at the safety
assurance boundary: start-state admission, instantaneous filtering,
short-horizon execution, and triggered response.

The taxonomy does not cover or claim:

- global planning optimality;
- localization accuracy;
- map reconstruction quality;
- wheel-level control validation; or
- a global formal safety proof.

The repository safety value `h` and the reported `min_safety_h` are GSplat
ellipsoid safety-function values. They are not metric clearance values.

## 2. F1: Start-State Unsafety

**Definition.** Start-state unsafety occurs when the initial state lies in, or
too close to, the unsafe set defined by the repository GSplat safety field and
the selected margin.

**Why it matters.** A CBF filtering pipeline normally reasons about maintaining
an admissible condition. Beginning from an unsafe or low-margin state violates
that operational premise and may leave too little authority for a bounded
control input to recover.

**Why the baseline is insufficient.** The baseline closed-loop path accepts the
provided start and proceeds to nominal command generation and CBF-QP
filtering. It does not make start-state admission a separate certified stage.

**Proposed mitigation.** Start-Safe Feasibility Certification evaluates the
initial state with the repository safety field. When required and supported by
the configured repair procedure, it returns a repaired start candidate and
then performs full-query validation before navigation.

**Evidence type.** Evidence consists of start-state labels, repair success or
failure, repair displacement, full-query validation, and downstream
post-repair navigation outcomes. Synthetic perturbed starts are stress cases,
not official benchmark starts.

**Claim boundary.** Start-Safe certification does not prove global safety. It
only verifies or repairs the start state under the repository safety field and
selected validation queries.

## 3. F2: CBF-QP Feasibility Failure

**Definition.** CBF-QP feasibility failure occurs when the selected CBF
constraints, dynamics model, bounds, and current state do not admit a solver
success and usable filtered action.

**Why it matters.** A nominal action cannot be made safe by the configured
filter if the constrained optimization problem has no feasible solution.
Ignoring this outcome can cause an implementation to execute an undefined,
stale, or inappropriate fallback action.

**Baseline limitation.** Per-step filtering reports solver behavior but does
not by itself explain whether failure originates from an invalid start,
insufficient control authority, model mismatch, numerical behavior, or the
chosen constraints.

**Proposed mitigation.** The assurance layer makes feasibility an explicit
admission and runtime condition. It combines start-state certification or
repair with full-query validation, records `solver_success` and
`qp_infeasible_count`, and requires an explicit stop or fallback when the
filter cannot produce a usable action.

**Evidence type.** Evidence includes per-case certification status,
full-query validation, QP solver status, infeasibility counts, and separate
collision checks.

**Claim boundary.** QP infeasibility is different from collision. Feasibility repair is not a new CBF theorem. It is a repository-scoped certification and
repair procedure evaluated under the selected safety field and dynamics.

## 4. F3: Sampled-Data Margin Risk

**Definition.** Sampled-data margin risk occurs when an action that is feasible
at the current filtering instant produces a predicted low-margin state during
a finite-step discrete rollout.

**Why instantaneous filtering is insufficient.** The action is held and
executed through discrete dynamics between filtering instants. Pointwise QP
feasibility does not directly characterize the minimum predicted safety value
after one or more such updates.

**H-step rollout.** Discrete-Time (DT) Verification rolls out the selected
action under the configured simulation model and evaluates the minimum
repository safety value over a finite horizon.

**H1/H2/H3.** H1, H2, and H3 expose increasing short-horizon views of the same
sampled-data execution model. They are finite verification horizons, not
global look-ahead guarantees. The selected horizon and margin must be reported
with the result.

**DT margin warning.** A warning is raised when the predicted H-step minimum
falls below the configured `dt_margin`. Warning counts and H1/H2/H3 margin
violations are diagnostic verification outputs.

**Collision distinction.** A margin violation is not collision. A collision-free trajectory can still contain DT margin warnings. Conversely, collision must
be determined by the repository collision criterion and reported independently.

**Evidence type.** Evidence includes H1/H2/H3 minimum safety values, margin
violation counts, `DT_warning_count`, collision counts, and QP infeasibility
counts. The verification-only audit and recovery-enabled trajectories must not
be treated as identical trajectory contexts.

**Claim boundary.** DT Verification establishes only the reported finite
horizon result under the selected rollout model, margin, and state estimate. It
is not a global safety proof and is not proof under unmodeled real-robot
dynamics.

## 5. F4: Recovery Insufficiency

**Definition.** Recovery insufficiency occurs when DT Verification detects
short-horizon risk but the execution stack has no mechanism, or no successful
mechanism, for selecting a safer executable response.

**Detection versus response.** Verification supplies a warning and predicted
margin evidence. It does not alter the command. Recovery is the separate
response stage that evaluates alternatives and chooses the command to execute.

**Why always-on recovery is not necessary.** Normal baseline filtering can
continue while the predicted margin remains above the configured threshold.
Triggering recovery only on warning or margin violation preserves the baseline
path when no additional response is required and exposes recovery overhead as
an intervention cost.

**Triggered recovery.** V4-C is activated by the configured warning or margin
condition. It evaluates candidate actions or short action sequences through the
same finite-horizon rollout model.

**Candidate evaluation and execution.** Candidates are ranked using their
predicted short-horizon behavior. Only the first action of the selected
candidate sequence is executed, after which the pipeline re-evaluates the
state and replans the next filtered action.

**Evidence type.** Evidence includes `recovery_used_count`,
`recovery_success_count`, `recovery_failed_count`, base and executed H-step
margin violation counts, runtime, QP infeasibility, and collision outcomes.

**Claim boundary.** V4-C is optional and triggered. It does not replace the nominal controller or CBF-QP. It is an empirical predictive-recovery wrapper in
the tested settings, not a globally optimal MPC method or a global safety
guarantee.

## 6. Summary Table

| ID | Failure mode | Trigger / symptom | Proposed module | Observable metrics | Boundary |
| --- | --- | --- | --- | --- | --- |
| F1 | Start-State Unsafety | Initial `h` is unsafe or below the selected admission margin. | Start-Safe Feasibility Certification / Repair | initial and repaired `min_safety_h`, repair success, full-query validation, repair distance | Start certification only; no global safety proof |
| F2 | CBF-QP Feasibility Failure | Solver failure or no usable bounded filtered action | Feasibility-aware admission, solver-status monitoring, stop/fallback | `solver_success`, `qp_infeasible_count`, validation status, `collision_count` | Infeasibility is not collision; no new CBF theorem |
| F3 | Sampled-Data Margin Risk | Predicted H-step minimum falls below `dt_margin` | H-step DT Verification | H1/H2/H3 minimum `h`, H1/H2/H3 margin violations, `DT_warning_count`, `collision_count` | Warning is not collision; finite-horizon model-specific result |
| F4 | Recovery Insufficiency | Warning exists and normal execution does not satisfy the selected horizon margin | Optional triggered V4-C Predictive Recovery | `recovery_used_count`, `recovery_success_count`, `recovery_failed_count`, executed margin violations, runtime, `collision_count` | Tested empirical response only; not an always-on planner or global guarantee |
