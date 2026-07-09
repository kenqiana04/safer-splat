# SAFC State Machine Specification

## 1. State List

- **S0. Pre-Execution Certification**
- **S1. Nominal Filtering**
- **S2. Verified Execution**
- **S3. Warning-Aware Execution**
- **S4. Recovery Mode**
- **S5. Replan Requested**
- **S6. Safe Halt / Abort**

The state machine is an architectural specification. Except where an existing
report supports a component behavior, it must not be described as a fully
implemented or experimentally validated supervisor.

## 2. State Semantics

### S0. Pre-Execution Certification

**Meaning.** S0 gates task start using Start-Safe and required deployment
validity checks.

**Inputs.** `start_certified`, `start_repaired`, `initial_h_min`,
`start_qp_feasible`, pose/frame validity, and repair/full-query status.

**Outputs.** Task-admission decision, start rejection reason, optional
replan/alternative-start request, or safe halt.

**Allowed actions.**

- Check Start-Safe certification.
- Admit a certified start or a repaired and fully verified start.
- If repair fails, request an alternative start only when an external planner
  or task manager is available; otherwise enter S6.
- Do not execute a normal aggressive command before admission.

### S1. Nominal Filtering

**Meaning.** S1 accepts a nominal command and invokes the existing CBF-QP
filter.

**Inputs.** Current state, `u_nom`, CBF-QP status, command limits, and required
deployment validity.

**Outputs.** `u_safe`, `solver_success`, intervention metrics, and the decision
to verify, recover, or halt.

**Allowed actions.**

- Run CBF-QP filtering on the nominal command.
- If `solver_success`, pass `u_safe` to finite-horizon verification and then S2
  when no warning is present.
- If the solver fails, enter S4 only if a declared recovery path is available
  and allowed; otherwise enter S6.

### S2. Verified Execution

**Meaning.** S2 represents normal execution after successful filtering and a
clear H-step verification result.

**Inputs.** H1/H2/H3 minimum `h`, warning flags, current safety value, execution
status, and progress.

**Outputs.** Bounded executed command and updated warning/clear streaks.

**Allowed actions.**

- Execute only the verified command through the declared dynamics or command
  adapter.
- Monitor H-step minimum `h` and deployment validity.
- If a warning appears, enter S3.
- If an interface becomes invalid, enter S6.

### S3. Warning-Aware Execution

**Meaning.** S3 handles finite-horizon low-margin observations without
mislabeling them as collision.

**Inputs.** Warning flags, `warning_streak`, `clear_streak`, `dt_margin`,
control deviation, progress, and recovery/planner availability.

**Outputs.** Slowdown or conservative command-shaping request, recovery
activation, replan request, or continued bounded execution.

**Allowed actions.**

- Apply bounded slowdown or command shaping when that interface is available.
- Return to S2 only after the warning clears for `K_exit` consecutive checks.
- Enter S4 when warning persistence reaches the recovery policy threshold.
- Enter S5 when repeated warning/recovery symptoms and poor progress indicate a
  route-level issue and replanning is available.
- Enter S6 if no bounded action is available under the declared policy.

### S4. Recovery Mode

**Meaning.** S4 invokes optional triggered recovery after filtering or
verification indicates unresolved risk.

**Inputs.** Recovery candidates, activation reason, current state, baseline
filtered command, warning history, and recovery availability.

**Outputs.** Selected first recovery action, `recovery_success`,
`recovery_failed`, post-recovery H-step verification, and escalation decision.

**Allowed actions.**

- Trigger V4-C-style recovery only under the declared activation policy.
- Execute only the first action of a selected sequence.
- Require post-recovery verification before returning to S2.
- Enter S5 after repeated recovery or unresolved route-level risk when an
  external replanning interface exists.
- Enter S6 after failed recovery or an invalid interface.

### S5. Replan Requested

**Meaning.** S5 reports that persistent safety intervention cannot be resolved
locally by ordinary filtering or occasional recovery.

**Inputs.** Warning and recovery history, QP status, progress, rejected
waypoint/goal information, and planner availability.

**Outputs.** `replan_request`, risk summary, optional `risk_cost`,
waypoint/goal rejection, and waiting/hold command.

**Allowed actions.**

- Send feedback to an external planner or task manager.
- Hold or safely stop while awaiting a new nominal route/command according to
  the deployment policy.
- Return to S1 only after a valid new nominal command and required reset checks.
- Enter S6 if no planner is available, the response is invalid, or a safe wait
  cannot be maintained.

### S6. Safe Halt / Abort

**Meaning.** S6 is the conservative terminal or latched fallback state.

**Inputs.** Any unrecoverable solver, recovery, deployment-interface, start, or
supervisory failure.

**Outputs.** `safe_halt`, abort reason, bounded stop command, and operator/task
notification.

**Allowed actions.**

- Permit no aggressive command.
- Maintain or request the validated safe-stop action.
- Leave S6 only through an explicit external reset and complete re-entry
  through S0; automatic transition is outside this specification.

## 3. Transition Table

| From | Condition | Action | To | Non-claim |
| --- | --- | --- | --- | --- |
| S0 | Start certified, or repaired and full-query verified; required interfaces valid | Admit task and request first nominal command | S1 | Start admission is not a global safety guarantee |
| S0 | Start/repair fails and no valid alternative-start interface is available | Issue safe halt / abort reason | S6 | Halt policy does not prove avoidability of all failures |
| S1 | CBF-QP succeeds and H-step check is clear | Accept bounded filtered command | S2 | Instantaneous feasibility plus finite-horizon clearance is not global safety |
| S1 | CBF-QP fails and a declared recovery path is available | Trigger recovery with failure reason | S4 | Recovery is not guaranteed or globally optimal |
| S1 | CBF-QP fails and no usable recovery path exists | Issue safe halt | S6 | Infeasibility is not collision |
| S2 | Any configured H-step warning appears | Increment warning streak and apply warning policy | S3 | DT warning is not collision |
| S3 | Warning clears for `clear_streak >= K_exit` | Remove warning shaping and resume verified execution | S2 | Hysteresis does not prove future safety |
| S3 | Warning persists to the recovery threshold | Activate optional triggered recovery | S4 | This is not always-on MPC |
| S3 | Repeated warning/intervention with poor progress and replanning available | Emit replan request and risk summary | S5 | Interface request is not an implemented planner |
| S4 | Recovery succeeds and post-recovery verification clears | Execute selected first action and resume monitoring | S2 | Empirical recovery success is configuration-specific |
| S4 | Recovery repeatedly activates or leaves route-level risk and replanning is available | Emit replan request | S5 | No replanning performance is claimed |
| S4 | Recovery fails or post-recovery verification remains unresolved without another bounded response | Issue safe halt | S6 | Safe halt is a conservative policy, not global proof |
| S5 | External planner/task manager returns a valid new nominal command | Reset relevant streaks and filter the new command | S1 | SAFC does not generate the new route |
| S5 | Planner unavailable, response invalid, or safe waiting impossible | Issue safe halt / abort | S6 | No full navigation-stack guarantee is claimed |

## 4. Hysteresis and Fail-Safe Rules

- `warning_streak >= K_enter` enters warning-aware or recovery escalation
  according to the configured policy.
- `clear_streak >= K_exit` is required to exit warning-aware execution.
- `K_exit` should be greater than or equal to `K_enter` so that leaving a
  conservative state is not easier than entering it.
- A missing or invalid deployment interface must not produce aggressive
  execution.
- QP infeasibility and recovery failure must not be silently ignored or merged
  into a generic warning counter.
- Recovery success must be followed by post-recovery H-step verification.
- Repeated recovery must be visible to the planner-facing interface.
- Safe halt is the conservative fallback when no bounded, contract-valid action
  remains.
- Collision, contact, warning, infeasibility, and halt must be logged as
  separate outcomes.

## 5. Pseudocode

The following text is a non-executable state-machine specification:

```text
if not pose_valid or not map_frame_valid or not command_adapter_valid:
    state = SAFE_HALT

if state == PRE_EXECUTION:
    start_status = check_start_safe()
    if start_status.certified_or_repaired_and_verified:
        state = NOMINAL_FILTERING
    elif planner_available and replanning_available:
        emit_alternative_start_request()
        state = REPLAN_REQUESTED
    else:
        state = SAFE_HALT

if state == NOMINAL_FILTERING:
    u_safe, solver_success = cbf_filter(x, u_nom)
    if not solver_success:
        state = RECOVERY_MODE if recovery_available else SAFE_HALT
    else:
        horizon_status = verify_horizon(x, u_safe)
        state = VERIFIED_EXECUTION if horizon_status.clear else WARNING_AWARE

if state == VERIFIED_EXECUTION:
    execute_bounded(u_safe)
    update_warning_and_clear_streaks()
    if horizon_warning:
        state = WARNING_AWARE

if state == WARNING_AWARE:
    emit_bounded_slowdown_if_available()
    if clear_streak >= K_exit:
        state = VERIFIED_EXECUTION
    elif warning_streak >= K_recovery and recovery_available:
        state = RECOVERY_MODE
    elif persistent_route_risk and replanning_available:
        state = REPLAN_REQUESTED
    elif no_contract_valid_action:
        state = SAFE_HALT

if state == RECOVERY_MODE:
    recovery_status = run_triggered_recovery()
    post_status = verify_recovery_result(recovery_status)
    if recovery_status.success and post_status.clear:
        state = VERIFIED_EXECUTION
    elif repeated_recovery and replanning_available:
        state = REPLAN_REQUESTED
    else:
        state = SAFE_HALT

if state == REPLAN_REQUESTED:
    emit_replan_request_with_risk_summary()
    if valid_new_nominal_command_received:
        state = NOMINAL_FILTERING
    elif planner_unavailable or safe_wait_invalid:
        state = SAFE_HALT

if state == SAFE_HALT:
    issue_validated_stop_or_abort()
    block_aggressive_commands()
```

## 6. Level-1 Operational Mapping

The Level-1 reconstruction maps aggregate evidence into the state machine.
This validates operational mappability, not closed-loop performance. Supported,
interface-level, and diagnostic transitions remain separated by claim scope.

## 7. Level-2 Online Instrumentation Status

The state machine has been instrumented in no-op mode in a tiny closed-loop
smoke path. The online instrumentation logs state decisions and feedback
candidates but does not execute feedback actions.
