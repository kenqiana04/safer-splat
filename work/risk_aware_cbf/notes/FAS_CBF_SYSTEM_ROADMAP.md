# FAS-CBF: Feasibility-Aware Start-Safe CBF Filtering in 3D Gaussian Splatting Maps

## Scope

This roadmap organizes the current reproduction into a planner-agnostic safety layer for 3D Gaussian Splatting maps. The work does not attempt to build a full high-level 3DGS planner. It focuses on a safety layer between a nominal planner/controller and low-level execution.

## System Modules

### FAS-Certify

FAS-Certify performs initial feasibility certification. Given an initial state and a GSplat scene, it queries the official GSplat safety geometry and labels the start as:

- `initial_safe`
- `initial_near_unsafe`
- `initial_unsafe`

The certification result is reported separately from navigation. It is not treated as a meter-clearance measurement.

### FAS-Project

FAS-Project repairs unsafe or near-unsafe starts before navigation. V4-A formulates this as a verified safe-start projection:

```text
minimize ||x_safe - x0||^2
subject to h(x_safe) >= delta under full GSplat safety query verification.
```

The implementation is a black-box verified projection search. Active nearby Gaussian sets are used to seed directions and local search, while final acceptance always uses full-query verification.

### FAS-Budget

FAS-Budget is inherited from V1. It reduces SAFER-Splat CBF runtime by selecting a risk-aware candidate budget before CBF matrix construction.

### FAS-Verify

FAS-Verify is the log-only discrete-time safety audit. Given executed controls and recorded states, it checks one-step predicted safety and actual next-step safety without modifying the controller.

### FAS-Recover

FAS-Recover is a future optional predictive or MPC-style recovery module. It is not implemented in V4-A.

## Relationship to V1/V2/V3/V4-A

| Version | Role in FAS-CBF |
| --- | --- |
| V1 | Efficiency module, i.e. FAS-Budget. |
| V2 | Runtime recovery prototype. Current result shows wrapper-level repulsive recovery cannot remove an already unsafe first sample. |
| V3 StartGuard | Initial certification and heuristic safe-start repair prototype. |
| V4-A | Upgrade V3 repair into verified safe-start projection and add discrete-time safety audit. |

## Claim Boundary

- No new CBF theorem is claimed.
- No official SAFER-Splat source is modified.
- `min_safety_h` is not meter clearance.
- Post-repair navigation is reported separately from original benchmark navigation.
- Verified projection is locally and empirically verified by the full GSplat safety query unless formal conditions are later proved.
