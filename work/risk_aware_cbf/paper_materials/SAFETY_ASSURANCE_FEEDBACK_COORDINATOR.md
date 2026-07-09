# Safety-Assurance Feedback Coordinator

## 1. Motivation

The existing Start-Safe, DT Verification, and Triggered Recovery modules form a
minimal safety assurance chain, but a deployable navigation safety layer also
requires feedback. Verification warnings, CBF-QP status, low-margin
observations, and recovery outcomes should not remain passive logs. They should
be converted into bounded feedback actions that can shape nominal commands,
trigger recovery, request replanning, update planner risk costs, reject unsafe
waypoints, or command a safe halt.

We therefore define the **Safety-Assurance Feedback Coordinator (SAFC)** as a
contract-based supervisory feedback layer. SAFC is not a planner, localization
module, or new CBF theorem. It does not replace the CBF-QP, the nominal
controller, or V4-C Recovery, and it does not validate four-wheel dynamics.
Instead, it defines how existing assurance signals may be aggregated, assigned
to explicit state-machine conditions, and converted into bounded actions whose
scope and non-claims are recorded.

This feedback framing closes the architectural loop between certification,
instantaneous filtering, finite-horizon verification, optional recovery, and
external deployment interfaces. It does not imply that every feedback action
is currently implemented or empirically validated. Current support,
interface-level specifications, and future extensions are distinguished
explicitly in the companion contract and pipeline documents.

## 2. Definition

> The Safety-Assurance Feedback Coordinator is a contract-based supervisory
> layer that aggregates start-state certification, CBF-QP status, H-step
> verification warnings, recovery outcomes, and deployment-interface validity
> into bounded feedback actions, including command shaping, recovery
> triggering, replanning requests, risk-cost updates, waypoint rejection, and
> emergency fallback.

SAFC consumes status signals and emits supervisory decisions. It does not
generate a route, estimate robot pose, redefine the CBF, or directly establish
a global safety guarantee. Each output must be interpreted through its
declared contract and implementation status.

## 3. Input Signals

### I1. Start-Safe Signals

- `start_certified`
- `start_repaired`
- `repair_distance`
- `initial_h_min`
- `start_qp_feasible`

These signals determine whether a task may begin, whether a repair was required
and validated, and whether the supplied start should be admitted, rejected, or
returned to an external task/planning interface for another start selection.
`initial_h_min` is the repository safety-function value, not metric clearance.

### I2. CBF-QP Signals

- `solver_success`
- `qp_infeasible_count`
- `active_constraint_count`
- `u_nom`
- `u_safe`
- `control_deviation = ||u_safe - u_nom||`
- `current_h_min`

These signals expose whether the nominal command is repeatedly or substantially
modified, whether the active constraint set is persistently large, and whether
the CBF-QP is feasible. High control deviation or repeated infeasibility may
indicate that the nominal command source and the safety filter are in persistent
conflict. QP infeasibility remains distinct from collision.

### I3. DT Verification Signals

- `H1_min_h`
- `H2_min_h`
- `H3_min_h`
- `H1_warning`
- `H2_warning`
- `H3_warning`
- `dt_margin`
- `warning_streak`
- `clear_streak`

These signals summarize predicted finite-horizon margin behavior under the
selected sampled-data rollout model. `warning_streak` supports persistent-risk
decisions, whereas `clear_streak` prevents immediate return to nominal mode
after a single clear observation. A DT margin warning is not collision; warning
and collision outcomes must be logged and claimed separately.

### I4. Recovery Signals

- `recovery_used`
- `recovery_success`
- `recovery_failed`
- `recovery_runtime`
- `recovery_action_type`
- `post_recovery_H_min`
- `recovery_used_streak`

These signals distinguish occasional recovery from systematic incompatibility
between the current nominal route and the safety layer. A successful recovery
must be followed by verification. Repeated use, high runtime, failed recovery,
or an unresolved post-recovery margin can escalate to a replan request or safe
halt according to the declared policy.

### I5. Nominal Command / Planner Signals

- `command_source`
- `goal_direction`
- `distance_to_goal`
- `progress`
- `nominal_speed`
- `nominal_heading`
- `planner_available`
- `replanning_available`

These signals define the external command boundary. They allow SAFC to return
feedback to a baseline nominal controller or external planner without
implementing either component. Poor progress under repeated safety
interventions can be treated as a route-level symptom, provided it is reported
as interface feedback rather than planner performance.

### I6. Deployment Validity Signals

- `pose_valid`
- `pose_confidence`
- `map_frame_valid`
- `command_adapter_valid`
- `emergency_stop_available`
- `robot_speed_limit`
- `rollout_adapter_valid`

These signals gate physical execution. Invalid or missing pose, frame,
command-adapter, emergency-stop, speed-limit, or rollout-model information
prevents certified deployment operation. Their current role is a real-robot
interface contract, not evidence of completed robot validation.

## 4. Feedback Actions

### A1. Command Slowdown

**Trigger.** An H-step warning, low `current_h_min`, or persistent low margin.

**Output.** A bounded `slowdown_factor`, scaled nominal command, or conservative
command bound for the existing filtering path.

**Scope.** This is an interface-level command-shaping policy. It does not claim
planner optimality, improved path-planning accuracy, or current experimental
validation.

### A2. Recovery Trigger

**Trigger.** An H2/H3 warning, warning streak, or predicted margin below the
configured threshold.

**Output.** `activate_recovery = True` for optional V4-C Recovery.

**Scope.** Recovery is optional and triggered; it does not replace the nominal
controller or CBF-QP. Verification-to-recovery behavior is supported by tracked
V4-C reports only for their named configurations.

### A3. Replan Request

**Trigger.** Persistent warnings, repeated recovery use, repeated QP
infeasibility, or poor progress under sustained safety intervention.

**Output.** `replan_request = True` to an external planner or task manager,
together with a reason code and relevant safety summary.

**Scope.** This is a planner interface, not an implemented global or local
planner. No replanning performance is claimed without separate implementation
and experiments.

### A4. Risk-Cost Update

**Trigger.** Low H-step minimum `h`, warning streak, recovery frequency, high
control deviation, or QP infeasibility.

**Output.** A bounded `risk_cost` signal, optional warning-region descriptor,
and confidence/status flag for external planner integration.

**Scope.** The paper may describe safety-aware planning feasibility or
risk-cost feedback. It must not claim path-planning accuracy, risk-cost
optimality, or current planner integration.

### A5. Waypoint / Goal Rejection

**Trigger.** A candidate waypoint or goal has low repository `h`, an invalid
frame, an inadmissible start/goal query, or predicted short-horizon risk under
the declared screening model.

**Output.** `rejected_waypoint`, `unsafe_goal_flag`, a rejection reason, and a
request for an alternative local target or goal.

**Scope.** This is an interface-level safety screening rule, not a full planner
or proof that accepted waypoints yield a globally safe path.

### A6. Emergency Stop / Safe Halt

**Trigger.** QP infeasibility with no usable recovery, failed recovery, invalid
pose, invalid map frame, invalid command adapter, unavailable required
emergency stop, or another deployment gate failure.

**Output.** `safe_halt = True` or task abort, zero/aggressiveness-limited command
according to the deployment adapter, and an explicit fault reason.

**Scope.** Uncertainty maps to a conservative fallback. A halt policy is not a
global safety proof and requires a validated robot-specific stopping interface
before physical use.

## 5. Design Principles

- Feedback must be conservative under uncertainty.
- Entering warning mode should be easier than exiting it.
- Warning clearing requires `clear_streak >= K_exit`.
- Recovery success must be followed by H-step verification.
- Repeated recovery should trigger planner-facing feedback rather than be
  treated as indefinitely normal operation.
- A missing or invalid deployment interface should trigger safe halt or
  `not_certified`, never aggressive execution.
- Feedback actions must be bounded, logged, and tied to explicit claim scope.
- Infeasibility, margin warning, recovery failure, and collision must remain
  separate observable outcomes.
- Interface-level and future feedback actions must not be described as
  implemented results.

## 6. Level-1 Offline Reconstruction Status

SAFC has a Level-1 offline reconstruction validation in
`REPORT_SAFC_LEVEL1_OFFLINE_RECONSTRUCTION.md`. This validation maps existing
report-level safety events into SAFC states and feedback actions. It does not
run new experiments or claim performance improvement.

## 7. Level-2 No-Op Instrumentation Status

SAFC has a Level-2 no-op instrumentation validation in
`REPORT_SAFC_LEVEL2_NOOP_INSTRUMENTATION.md`. This validates passive insertion
and logging in a tiny closed-loop smoke path without modifying control. It does
not validate active feedback or performance improvement.

## 8. Level-3A Warning-Streak Slowdown Status

SAFC has a Level-3A minimal active feedback smoke in
`REPORT_SAFC_LEVEL3A_WARNING_SLOWDOWN.md`. This tests bounded warning-streak
slowdown logic and tiny-smoke integration. It does not claim benchmark-level
safety improvement.

## 9. Level-3B Warning-Rich Targeted Status

SAFC Level 3B searches for a naturally warning-rich targeted case and, if
found, tests whether warning-streak slowdown activates under natural warning
conditions. Its claim scope is targeted activation validation, not
benchmark-level performance improvement.

## 10. Level-3B-R Warning Reconciliation Status

SAFC Level 3B-R reconciles report-derived warning evidence against executable
no-op scan contexts. It does not run active slowdown and does not claim
performance improvement.
