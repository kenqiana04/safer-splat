# Real-Robot Deployment Plan

## 1. Role of Real-Robot Experiment

The real-robot experiment should be framed as a deployment demonstration and feasibility validation. It should not replace simulation benchmark evidence and should not be described as full four-wheel robot dynamics validation unless a matching robot dynamics model and command interface are added.

Allowed claim:

```text
The safety assurance layer can be inserted between an existing nominal navigation command source and a mobile robot command interface.
```

Not allowed claim:

```text
The method solves full real-world four-wheel navigation.
```

## 2. Assumed Robot Interface

The current repository does not define a concrete robot command interface. The hardware interface is therefore to-be-confirmed.

### Case A: differential / skid-steer style command

```text
cmd_vel = [v, omega]
```

Possible safety-layer actions:

- reduce forward speed near unsafe h values
- stop if h is negative or DT warning persists
- apply heading correction if a safe steering direction is available
- trigger recovery command only when warning conditions are active

### Case B: Ackermann style command

```text
command = [v, steering_angle]
```

or

```text
command = [acceleration, steering_angle]
```

Possible safety-layer actions:

- cap speed as a function of h and predicted H-step risk
- constrain steering within physical limits
- issue braking or slowdown under DT warnings
- reject commands that cannot be certified by the safety query

## 3. Deployment Architecture

```text
Localization / pose source
  + GSplat map / safety field
  + nominal planner or controller command
        |
        v
planner-agnostic safety assurance layer
  - start-state safety / feasibility check
  - CBF-QP or command-filter wrapper
  - H-step DT verification
  - triggered recovery / slowdown / stop
        |
        v
cmd_vel_safe or ackermann_safe
        |
        v
robot base
```

## 4. Required Engineering Interfaces

Required before deployment:

1. Pose input: robot pose in the GSplat/world frame.
2. Map frame alignment: transform between robot frame, camera/map frame, and GSplat frame.
3. Nominal command input: from joystick, local planner, or navigation stack.
4. Safety h query: GSplat ellipsoid query for robot footprint or a conservative proxy.
5. CBF-QP wrapper: command filter compatible with the real command dimension.
6. DT verification rollout: model must match the command interface sufficiently for short-horizon prediction.
7. Recovery command: slowdown, stop, reverse, or heading correction policy.
8. Emergency stop: hardware or operator-level stop independent of software.
9. Logging: pose, nominal command, safe command, h, H-step warnings, recovery triggers, stop events.

## 5. Minimal Real-Robot Experiments

### Experiment A: Start-near-obstacle check

Purpose: show that unsafe or marginal starts are detected before normal execution.

Setup: place the robot near a mapped obstacle boundary. Compare nominal command execution against safety-layer start check.

Metrics:

- start h value or proxy h
- repair / reject / stop decision
- command modification magnitude
- human emergency stop count

### Experiment B: Narrow passage / close obstacle navigation

Purpose: show that the safety layer modifies commands when passing close to mapped GSplat geometry.

Setup: run a nominal controller through a narrow aisle or close pass while logging h and command corrections.

Metrics:

- success / failure
- intervention count
- minimum measured distance or proxy h
- command modification magnitude
- path completion time
- emergency stop count

### Experiment C: DT-warning / recovery demonstration

Purpose: show that short-horizon risk warnings can trigger a recovery action before collision.

Setup: choose a scenario where the nominal command approaches an obstacle or close goal-side boundary.

Metrics:

- DT warning count
- recovery trigger count
- recovery success count
- post-recovery h trend
- command modification magnitude
- completion or safe-stop outcome

## 6. What Can Be Claimed From Real-Robot Demo

Allowed:

- deployability demonstration
- safety layer can be inserted into a real navigation stack
- command modification and warning/recovery behavior are observable
- real-world logs are consistent with the simulation safety interface

Forbidden:

- full benchmark superiority
- global safety guarantee
- planner superiority
- localization improvement
- universal four-wheel robot validation
- replacing the simulation benchmark with one demo

## 7. Minimal Deployment Checklist

1. Confirm robot type and command API.
2. Confirm pose source and update rate.
3. Confirm GSplat-to-robot frame transform.
4. Implement command adapter from safety layer output to robot command.
5. Define speed and steering bounds.
6. Add independent emergency stop.
7. Create logging schema.
8. Run static safety query checks before moving robot.
9. Run low-speed tethered tests.
10. Only then run the three minimal scenes.
