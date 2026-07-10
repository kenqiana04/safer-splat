# SAFC Final Claim Boundaries

## Supported Claims

- The method stack combines Start-Safe certification/repair, CBF-QP filtering,
  H-step discrete-time verification, optional triggered recovery, and SAFC
  supervisory coordination.
- SAFC can reconstruct prior safety events into a state/action vocabulary.
- SAFC no-op instrumentation can be inserted without modifying commands in
  the validated smoke setting.
- Warning-gated wrapper-level command shaping can be executed after natural
  warning gates in the targeted validations.

## Supported Only Under Named Configurations

- Start-Safe repair/certification results are limited to the repository safety
  field, selected thresholds, repair domains, and named query settings.
- Triggered V4-C recovery claims are limited to the named V4-C configurations,
  horizons, candidate sets, and scenes reported in the V4-C artifacts.
- Collision-free results, where reported, must name the exact configuration and
  must not be converted into a global safety guarantee.

## Targeted Observation Claims

- Level 3C supports fixed-C003 targeted A/B behavior only.
- Level 3D supports small targeted cohort behavior: active warning fewer in
  3/5, equal in 1/5, more in 1/5, with total warning delta -25.
- Level 3E supports targeted policy-variant observations over five candidates:
  current total 164, milder total 182, critical-only total 182.
- VANS shadow audit supports only a counterfactual feasibility observation:
  over five pre-registered contexts, one verified alternative nominal action
  was observed in C002 and no progress-nonworse verified alternative was
  observed.

## Diagnostic Claims

- C004 is negative and scale-sensitive in Level 3E.
- C006 is neutral across tested Level 3E variants.
- No Level 3E active diagnostic run reached the goal.
- The progress proxy is diagnostic goal-distance reduction only.
- VANS remains a diagnostic extension: shadow-selected candidates were not
  executed and do not establish closed-loop warning reduction.

## Interface-Level Claims

- Replan request, risk-cost update, waypoint screening, and deployment halt are
  specified contracts.
- Planner and robot adapters are required before planner-integration or
  real-robot claims.

## Future-Work Claims

- Planner integration.
- Real-robot validation.
- Four-wheel dynamics validation.
- Statistical benchmark evaluation.
- Generalized performance comparison.
- Active Verification-Aware Nominal Action Selection.

## Prohibited Claims

- global safety guarantee;
- generalized warning reduction;
- generalized collision reduction;
- planning accuracy improvement;
- planner optimality;
- complete planner integration;
- complete real-robot validation;
- four-wheel dynamics validation;
- statistical significance;
- new CBF theorem;
- metric clearance when only `h` or `min_safety_h` is available;
- SAFC active feedback is benchmark-validated;
- warning-streak slowdown is the core performance contribution;
- VANS improves safety, warnings, completion, or planner quality.
