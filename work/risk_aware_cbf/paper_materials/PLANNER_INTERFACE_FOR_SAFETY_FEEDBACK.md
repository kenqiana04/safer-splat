# Planner Interface for Safety Feedback

## 1. Purpose

The proposed framework remains planner-agnostic. SAFC does not implement a
planner. Instead, it defines feedback signals that an external planner,
task manager, or nominal command source can consume. This separation allows the
safety layer to report persistent route-level symptoms without claiming route
generation, planner optimality, or localization.

The interface is asynchronous or synchronous according to the external stack,
but every message should include a validity flag, timestamp, frame identifier,
reason code, and bounded numeric values where applicable. A missing consumer
must not be treated as successful replanning.

## 2. Planner-Facing Feedback Signals

- `replan_request`: Boolean or enumerated request with reason and urgency.
- `risk_cost`: bounded scalar or structured cost update for planner use.
- `rejected_waypoint`: identifier/pose of a candidate rejected by the declared
  safety screen.
- `unsafe_goal_flag`: indicates that the current goal fails the configured
  admission or screening rule.
- `warning_region`: optional map-frame region associated with repeated
  finite-horizon warning.
- `recovery_frequency`: windowed recovery count or rate.
- `low_margin_direction`: optional direction associated with decreasing
  repository `h`; it is not metric clearance.
- `command_deviation_score`: normalized magnitude or history of
  `||u_safe - u_nom||`.
- `emergency_stop_required`: latched request when no contract-valid aggressive
  action remains.

These signals report safety-layer state. They do not prescribe the planner's
internal graph, cost function, search algorithm, or route representation.

## 3. Candidate Use Cases

### Case 1. Verification-Triggered Replanning

Persistent DT warning or repeated recovery sets `replan_request` and attaches
the triggering horizon, warning streak, recovery history, and progress
summary. The external planner may return another route or command, but SAFC
must re-enter filtering and verification before execution. This use case is
currently an interface specification.

### Case 2. Risk-Cost Feedback for Planning

An external planner may increase cost near regions associated with low
repository `h`, repeated warning, large command deviation, or recovery-heavy
execution. SAFC supplies bounded evidence and validity metadata; the planner
owns normalization, spatial propagation, decay, and optimization. No
risk-cost optimality or planning-accuracy improvement is currently claimed.

### Case 3. Safety-Guided Waypoint Screening

Planner candidates may be screened by a valid-frame repository safety query
and, where defined, an H-step verification rule. Rejected candidates are
returned with a reason, while accepted candidates still require ordinary
CBF-QP filtering and online verification. Screening does not prove that a
sequence of accepted waypoints is globally safe or complete.

### Case 4. Nominal Action Selection

If a nominal controller proposes multiple candidate actions, SAFC may request
H-step risk scores before a candidate enters the normal CBF-QP path. The
external command source remains responsible for candidate generation and task
performance; SAFC contributes only bounded safety feedback. This remains a
future experimental option, not part of the current main method.

## 4. Current Paper Boundary

In the current paper, this interface is an architectural and contract-level extension unless additional experiments are explicitly added later. It must not be reported as an implemented planner or validated replanning system.

The currently supported feedback connection is the tracked
verification-to-triggered-recovery path in named V4-C settings. Replan
requests, planner risk-cost updates, waypoint screening, and pre-CBF nominal
candidate scoring remain interface-level or future work.

## 5. Safer Wording

### Allowed

- safety feedback interface to an external planner;
- verification-triggered replanning request;
- risk-cost signal for planner integration;
- safety-guided waypoint screening interface;
- planner-agnostic supervisory contract; and
- future integration with a robot navigation stack.

### Not allowed

- new path planner;
- improved path-planning accuracy;
- planner optimality;
- validated replanning performance;
- completed planner integration; or
- full navigation-stack validation.
