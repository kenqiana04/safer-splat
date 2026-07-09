# Real-Robot Interface Contract

## 1. Purpose

The real robot is intended as a deployment platform, not the current
simulation model. The current repository uses 3D double-integrator dynamics
and cannot be directly described as four-wheel dynamics validation. A physical
demonstration therefore requires explicit interfaces between the GSplat safety
assurance layer and the robot navigation stack.

This contract defines those interfaces and the evidence boundary. Before the
interfaces and experiments exist, the appropriate claim is a deployment plan,
not completed real-world validation.

## 2. Required Interfaces

### I1. Pose Interface

The robot pose, velocity estimate, timestamp, and validity status must be
available in the GSplat map frame. The interface must reject stale, non-finite,
or frame-ambiguous state estimates. The safety layer does not provide
localization; it consumes a pose estimate supplied by the robot stack.

### I2. Frame Calibration Interface

The GSplat map frame must align with the robot/world frame through a calibrated,
versioned transform. The transform procedure must define scale, handedness,
axis convention, origin, uncertainty check, and validation residual. A missing
or invalid transform must trigger stop/fallback rather than an uncalibrated
safety query.

### I3. Nominal Command Interface

An existing planner, teleoperation source, or baseline controller must provide
the nominal command with its command type, frame, units, bounds, timestamp, and
validity. The proposed framework does not add global or local planning.

### I4. Command Adapter

The simulated safe action must be mapped to the robot's actual command space,
such as `cmd_vel` for differential/skid-steer motion or steering and speed for
an Ackermann interface. The adapter must apply declared velocity,
acceleration, steering, and rate limits. A direct interpretation of 3D
double-integrator acceleration as wheel-level control is not valid.

### I5. Short-Horizon Rollout Adapter

DT Verification must use a rollout model consistent with the real command
interface, update period, actuator limits, and measured latency. A
double-integrator audit can remain a simulation reference, but real-robot
claims require a validated differential/skid-steer, Ackermann, or identified
command-response rollout as appropriate.

### I6. Emergency Stop Interface

An uncertain or unsafe condition must trigger a deterministic stop or fallback.
Required triggers include stale pose, invalid calibration, unavailable safety
query, CBF-QP failure, non-finite command, command timeout, unrecovered DT
warning under the deployment policy, and operator emergency stop. The fallback
must be independent of the optimization process.

### I7. Logging Interface

Logs must record synchronized pose, pose age, nominal command, filtered command,
executed command, command limits, repository `h` proxy, DT horizon and warning,
recovery trigger, selected intervention, solver status, adapter status,
latency, stop event, and observed contact/collision outcome. Safety-function
values and metric clearance, if available, must use separate fields.

## 3. Deployment Claim Boundary

### Allowed after a successful, documented demonstration

- The GSplat safety layer can be inserted into the tested navigation stack.
- Command modification, DT warnings, and triggered recovery can be observed
  under the tested interface and scene conditions.
- The deployment adapter is feasible for the tested robot, limits, calibration,
  and command rate.

### Not allowed from the interface contract alone

- full real-world benchmark superiority;
- a four-wheel dynamics theorem or four-wheel-specific planning contribution;
- planner superiority;
- localization improvement; or
- a universal or global safety guarantee.

## 4. Minimal Deployment Experiments

### Experiment 1: Start-Near-Obstacle

- **Purpose:** demonstrate start-state admission, repair/stop behavior, and the
  separation between start certification and normal navigation.
- **Setup:** place the stationary robot at several measured offsets near a
  mapped obstacle, use a low speed limit, verify the map transform before each
  run, and include at least one admissible and one rejected/marginal start.
- **Baseline:** existing nominal command plus baseline CBF-QP without automated
  Start-Safe repair; unsafe starts must still use the deployment emergency-stop
  policy.
- **Safety-layer condition:** enable Start-Safe certification; execute only a
  certified state or a separately approved physical repositioning procedure.
- **Metrics:** certification outcome, repository `h`, optional metric
  clearance, repair/reposition displacement, QP status, command intervention,
  stop count, and contact/collision count.
- **Expected figure/table:** overhead map with tested start locations and a
  table of certification, intervention, and physical outcome.
- **Risk controls:** low speed, safety operator, hardware emergency stop,
  padded obstacle, bounded test area, and no autonomous movement from a
  rejected start.

### Experiment 2: Narrow Passage

- **Purpose:** demonstrate insertion of the safety filter into a navigation
  stack under sustained close-obstacle interaction.
- **Setup:** use a mapped passage wider than the robot plus a conservative
  physical buffer; execute repeated low-speed traversals in both directions.
- **Baseline:** the same nominal command source and robot stack with the
  baseline CBF-QP configuration.
- **Safety-layer condition:** add Start-Safe admission and H-step DT
  Verification; recovery may be disabled for the first staged comparison and
  enabled only after stop behavior is validated.
- **Metrics:** traversal success, minimum measured clearance, repository `h`,
  intervention norm, DT warning count, QP infeasibility, stop count, runtime,
  and contact/collision count.
- **Expected figure/table:** trajectory overlay with obstacle geometry and
  intervention markers; paired table for baseline and safety-layer conditions.
- **Risk controls:** conservative speed/acceleration bounds, spotter, remote
  stop, soft barriers, pre-run calibration check, and immediate stop on stale
  state or unresolved warning.

### Experiment 3: DT-Warning / Recovery Demonstration

- **Purpose:** demonstrate that a predicted finite-horizon margin risk can
  trigger a bounded alternative command before contact.
- **Setup:** construct a repeatable low-speed approach that raises a DT warning
  without requiring collision; validate the robot-consistent rollout model and
  latency before autonomous activation.
- **Baseline:** nominal command plus baseline CBF-QP and DT monitoring, with
  warning-triggered stop as the initial safe reference.
- **Safety-layer condition:** enable optional triggered V4-C-style recovery
  through the real command adapter, execute only the first selected action,
  and re-evaluate at every control update.
- **Metrics:** base and executed predicted minimum `h`, warning count, recovery
  use/success/failure, intervention, command latency, measured clearance,
  stop count, and contact/collision count.
- **Expected figure/table:** synchronized time series of nominal, safe, and
  executed command with `h`, warning, and recovery trigger; event-level outcome
  table.
- **Risk controls:** begin with shadow mode, then stop-only mode, then bounded
  recovery at low speed; maintain hardware emergency stop and terminate on any
  model/measurement inconsistency.
