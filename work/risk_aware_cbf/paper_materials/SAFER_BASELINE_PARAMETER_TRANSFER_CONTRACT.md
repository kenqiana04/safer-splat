# SAFER Baseline Parameter-Transfer Contract

## Purpose

This contract defines the boundary between metadata-driven scene adaptation and the original SAFER baseline. A scene cannot enter G1 smoke unless this contract is satisfied.

## Frozen Across All Scenes

- Nominal-controller formula and gains.
- CBF-QP objective, constraints, alpha/beta configuration, solver, and tolerance.
- Double-integrator dynamics, integration rule, timestep, control clamp, collision threshold, stop criteria, and maximum step count.
- Gaussian safety query and its filtering/pruning behavior.
- Recovery, Start-Safe repair, Risk-Aware/Adaptive selection, SAFC, R1, slowdown, VANS, and planner state: disabled.

## Metadata-Determined Inputs

- Checkpoint path and format.
- A documented coordinate transform.
- A documented metric-scale transform.
- Scene bounds plus a preregistered start/goal region.
- Optional independent geometry-checker path.

## Prohibited Result-Driven Changes

Robot radius, CBF or control gains, opacity filtering, start-goal difficulty, scene scale, maximum steps, and QP tolerance must not be changed after observing baseline output. A non-metric scene needs one reproducible conversion rule derived from verified dataset metadata, calibrated camera baseline, known object dimension, simulator units, or provenance-confirmed reconstruction scale.

## Pass Criterion

`parameter_transfer_contract_passed=true` only when every frozen item is unchanged, every metadata-driven transform has a recorded source, and no smoke result was used in selection or tuning.
