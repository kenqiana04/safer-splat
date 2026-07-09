# Assurance Contracts for the Proposed Safety Layer

## 1. Contract Philosophy

Rather than claiming a single global safety guarantee, the framework defines
module-level assurance contracts. Each contract specifies its input, output,
assumptions, assurance scope, observable failure condition, metrics, and
non-claims. The contracts form a compositional engineering interface, but
their composition does not automatically constitute a formal end-to-end
safety theorem.

The contracts distinguish baseline functions from proposed assurance
functions. Nominal command generation and the per-step CBF-QP are baseline
interfaces. Start-Safe certification, H-step DT Verification, and optional
triggered V4-C recovery are the proposed assurance modules. Real-robot
adaptation remains a future deployment interface until implemented and tested.

## 2. Contract C0: Nominal Command Contract

- **Input:** robot state and goal, or an external planner/controller output.
- **Output:** nominal command `u_nom`.
- **Assumptions:** a nominal command is provided externally or by the baseline
  goal-directed controller; units and frames agree with the safety filter.
- **Assurance scope:** none from the proposed method. This contract defines the
  command boundary consumed by the assurance layer.
- **Failure condition:** command absent, stale, non-finite, frame-inconsistent,
  or outside the adapter's declared command type.
- **Metrics:** command availability, command age, command norm, saturation
  status, and frame identifier.
- **Non-claims:** no planner optimality, no new global or local planner, and no
  localization contribution.

## 3. Contract C1: Start-Safe Feasibility Certification

- **Input:** initial state `x0` and GSplat safety field `h`.
- **Output:** certified start `x0` or repaired start `x0'`, together with
  certification and repair status.
- **Assumptions:** the GSplat representation, repository safety query,
  thresholds, candidate-repair domain, and state/map transform are valid for
  the evaluated scene.
- **Assurance scope:** start-state full-query validation under repository `h`;
  if repair is used, only the returned and validated `x0'` is admitted.
- **Failure condition:** the original start is inadmissible and no repair
  candidate passes the selected full-query validation, or the query itself is
  unavailable.
- **Metrics:** original and repaired `min_safety_h`, certification status,
  repair success, full-query validation count, repair displacement, and
  downstream feasibility status.
- **Non-claims:** no global safety proof, no guarantee beyond the selected
  safety field and validation queries, and no real-robot dynamics validation.

## 4. Contract C2: CBF-QP Safety Filtering

- **Input:** current state `x` and nominal command `u_nom`.
- **Output:** filtered command `u_safe` and `solver_success`.
- **Assumptions:** CBF constraints and the dynamics model are valid for the
  current simulation; state, command bounds, and GSplat query are mutually
  consistent.
- **Assurance scope:** instantaneous CBF-QP feasibility and the returned
  filtering result at the current update.
- **Failure condition:** solver failure, infeasibility, non-finite output, or
  violation of declared command bounds.
- **Metrics:** `solver_success`, `qp_infeasible_count`, intervention norm,
  command saturation, current `h`, and collision outcome reported separately.
- **Non-claims:** instantaneous feasibility does not imply H-step margin
  safety, global collision avoidance, planner quality, or robustness to an
  unmodeled robot.

## 5. Contract C3: H-Step Discrete-Time Verification

- **Input:** state `x`, filtered command `u_safe`, rollout model, horizon set
  `H`, repository safety field, and configured `dt_margin`.
- **Output:** H-step minimum `h`, horizon-specific values, and warning flag.
- **Assumptions:** the selected rollout model, integration step, held command,
  state estimate, and safety query are appropriate for the evaluated
  simulation.
- **Assurance scope:** short-horizon rollout assessment under the selected
  simulation dynamics and finite horizon.
- **Failure condition:** predicted minimum `h` below `dt_margin`, unavailable
  query, non-finite rollout, or inconsistent rollout inputs.
- **Metrics:** H1/H2/H3 minimum `h`, H1/H2/H3 margin violations,
  `DT_warning_count`, warning rate, and collision count as a separate outcome.
- **Non-claims:** not global safety, not collision by itself, not metric
  clearance, and not proof under unmodeled real-robot dynamics.

## 6. Contract C4: Triggered Predictive Recovery

- **Input:** DT warning or margin risk, current state, baseline filtered
  command, candidate recovery actions or sequences, rollout model, and command
  bounds.
- **Output:** executable command `u_exec`, activation status, candidate
  selection status, and recovery outcome.
- **Assumptions:** candidate recovery actions or sequences are available; the
  same declared short-horizon model and safety query can evaluate them; a
  selected command can be executed within bounds.
- **Assurance scope:** empirical reduction of executed margin violations in
  the tested settings. Only the first action of a selected sequence is
  executed before re-evaluation.
- **Failure condition:** no valid candidate, selection failure, executed
  rollout still below margin, or downstream command-interface failure.
- **Metrics:** `recovery_used_count`, `recovery_success_count`,
  `recovery_failed_count`, base and executed horizon-margin violations,
  runtime, progress, QP infeasibility, and collision.
- **Non-claims:** not globally optimal MPC, not an always-on planner, not a
  replacement for the nominal controller or CBF-QP, and not a global safety
  guarantee.

## 7. Contract C5: Real-Robot Deployment Adapter

- **Input:** pose in the GSplat map frame, nominal command, command limits,
  GSplat transform, robot status, and safety-layer output.
- **Output:** safe `cmd_vel` or Ackermann command, adapter status, and
  stop/fallback signal.
- **Assumptions:** the robot interface, time synchronization, frame
  calibration, state estimation, command conversion, limits, and emergency
  stop are implemented and validated.
- **Assurance scope:** deployment demonstration only until the adapter and
  experiments are completed. The adapter must preserve declared units, frames,
  bounds, and timing.
- **Failure condition:** stale or invalid pose, transform mismatch, command
  timeout, unavailable safety query, invalid conversion, verification model
  mismatch, or emergency-stop condition.
- **Metrics:** pose age, transform residual, nominal and safe command,
  intervention magnitude, `h` proxy, DT warning, recovery trigger, stop count,
  command latency, and observed collision or contact.
- **Non-claims:** no four-wheel dynamics validation before the adapter and
  experiments, no localization improvement, no planner superiority, and no
  universal real-world safety guarantee.

## 8. Contract Summary Table

| Contract | Module | Input | Output | Assurance scope | Non-claim |
| --- | --- | --- | --- | --- | --- |
| C0 | Nominal command source (baseline/external) | State and goal or planner output | `u_nom` | Defines the command consumed by the safety layer | No planner optimality or new local/global planner |
| C1 | Start-Safe certification / repair (proposed) | `x0`, GSplat `h` | Certified `x0` or repaired `x0'` | Full-query start validation under repository `h` | No global proof or real-robot dynamics validation |
| C2 | CBF-QP filter (baseline) | `x`, `u_nom` | `u_safe`, `solver_success` | Instantaneous filtering result and feasibility status | Does not imply H-step margin safety |
| C3 | H-step DT Verification (proposed) | `x`, `u_safe`, rollout model, `H` | H-step min `h`, warning | Finite-horizon assessment under selected simulation dynamics | Warning is not collision or global proof |
| C4 | Triggered V4-C recovery (proposed, optional) | DT warning / margin risk and candidates | `u_exec`, recovery status | Empirical reduction of executed margin violations in tested settings | Not globally optimal MPC, always-on planner, or CBF-QP replacement |
| C5 | Real-robot adapter (future deployment) | Map-frame pose, commands, limits, transform | `cmd_vel`/Ackermann command and fallback | Deployment demonstration after implementation and validation | No current four-wheel dynamics validation or universal guarantee |
