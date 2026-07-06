# DT Verification Decision Rule

## Definition

Discrete-Time Verification is the sampled-data safety audit layer in FAS-CBF. Given the current executed state and the control selected by the start-safe CBF navigation layer, it rolls out one or more discrete dynamics steps and queries the repository GSplat ellipsoid safety value along that rollout.

## Why It Is Not a V4-C Submodule

DT Verification is the detector and accounting layer. It can run without any predictive recovery, as in the verification-only audit. V4-C is one possible optional response when DT Verification reports warning/on-margin risk. The method ordering is therefore: start-safe CBF navigation, DT Verification, optional triggered recovery.

## One-Step and H-Step Rollout Verification

H=1 is the immediate one-step check. H=2 is the practical trigger horizon used by the dense-flight R4_H2_N64 configuration. H=3 is retained as a robust reference horizon. The rollout uses the repository discrete double-integrator update and evaluates the GSplat ellipsoid safety value at predicted future positions.

## Base Rollout vs Executed Rollout

In verification-only audit, base and executed rollout are identical because no recovery is executed. In predictive recovery runs, base rollout is the unmodified V1/CBF control rollout and executed rollout is the rollout after a triggered recovery control is selected.

## Margin Violation vs Collision

A margin violation means the H-step minimum safety value is below the chosen DT margin. It is a warning/on-margin sampled-data risk, not a collision. Collision remains reported separately using the repository safety value crossing below zero.

## Safety Value Meaning

`min_safety_h` and related H-step values are repository GSplat ellipsoid safety h values. They are not meter clearance.

## Decision Rule

- Normal execution: H-step minimum safety value is at or above `dt_margin`.
- Warning/on-margin: H-step minimum safety value is below `dt_margin`.
- Trigger optional predictive recovery: warning/on-margin is detected and a recovery module is enabled.
- Unresolved risk: recovery fails or the executed H-step rollout remains below `dt_margin`.

## Paper Wording

V4-A + V1 may be collision-free while still exhibiting sampled-data margin risks, so DT Verification is required to identify those risks. V4-C should be described as an optional triggered recovery module used after DT Verification reports warning/on-margin risk. Margin violations must not be reported as collisions.

## Current Counts

- H=1 margin violations: 463
- H=2 margin violations: 488
- H=3 margin violations: 519
