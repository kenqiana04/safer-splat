# Failure Level Classification

This file defines the failure levels used by the redesign program and assigns
current method versions to them. The purpose is to prevent local version
failure from being misread as research-direction failure.

## Level A: Implementation Failure

Definition: the mechanism could not be evaluated because of an integration,
state mutation, window selection, configuration wiring, or metric logging
error.

Examples:

- wrong entrypoint or wrapper path;
- shadow evaluation mutates the formal trajectory;
- wrong start-goal window;
- incorrect metric interpretation;
- missing exact candidate logging.

Current assignments:

- early FC-Aware exact logging gaps before the feasibility probe: Level A
  until logging was repaired;
- report-derived warning-context mismatch before Level 3B-R: Level A/C
  diagnostic, not a slowdown mechanism failure.

## Level B: Configuration Failure

Definition: the mechanism is plausible, but the selected thresholds, candidate
budget, horizon, scale policy, or activation condition are not the right
configuration.

Current assignments:

- Risk-Aware V1 bestD versus default: Level B tradeoff between lower
  constraints and slightly faster default runtime;
- V4-C H3_N128 versus R4_H2_N64: Level B runtime/configuration tradeoff;
- C004 slowdown scale sensitivity: Level B inside the slowdown family.

## Level C: Mechanism Failure

Definition: the implemented mechanism is structurally unable to deliver the
intended benefit even after implementation correctness is established.

Current assignments:

- Risk-Aware Top-k V0 as runtime method: post-query selection reduces QP
  constraints but cannot remove earlier distance/query work;
- Adaptive V1 selected-K-only efficiency: forced candidate union dominates
  final candidate counts;
- primitive MPC-style recovery v0: primitive sequence library leaves 96
  selected margin violations and is dominated by nominal-like sequences;
- warning-streak slowdown: scalar post-filter magnitude scaling cannot change
  direction or solve stop-reason behavior;
- VANS magnitude-only shadow v0: N0/N1/N2 scaling found only 1/189 verified
  opportunity and 0 progress-nonworse opportunities.

## Level D: Mechanism-Family Failure

Definition: at least two substantively different versions within a mechanism
family fail for the same structural reason, after implementation and
measurement are validated.

Current assignments:

- No broad family is closed yet for SAFC feedback.
- The primitive MPC-style v0 profile is frozen, but recovery as a family is
  not closed because V4-C remains positive.
- Magnitude-only VANS is weak, but verification-aware selection as a family is
  not closed because grounded primitives, supervisory mode selection, and
  objective shaping were not tested.

## Level E: Direction Failure

Definition: multiple orthogonal mechanism families fail under validated
implementation and measurement, no credible bounded redesign remains, and
further work would cross paper boundaries or add unjustified complexity.

Current assignments:

- No current top-level direction is classified as Level E.
- SAFC remains open.
- Verification-aware selection remains open.
- Primitive MPC-style recovery v0 and FC-Aware V1 are frozen versions, not
  direction-level closures.

## Required Clarifications

- Slowdown current-version failure is not SAFC failure.
- Magnitude-only VANS failure is not verification-aware selection failure.
- Zero completion is not automatically safety-framework failure.
- Runtime improvement without progress improvement is not Risk-Aware V1
  failure; it limits the claim to efficiency support.
- Collision in fixed and FC-Aware capped trial0 does not prove FC-Aware caused
  the collision; it blocks expansion of that branch.
