# Geometry authority trace

## Controller base footprint authority

The frozen Stonehenge runtime has one operational radius chain:

1. `run.py:47-52` selects the Stonehenge scene and assigns `radius = 0.015` metres.
2. `run.py:115` passes that same variable into `CBF(gsplat, dynamics, alpha, beta, radius, ...)`.
3. `cbf/cbf_utils.py:45` consumes `self.radius` at the shared Gaussian clearance entry point: `query_distance(x[..., :3], radius=self.radius, ...)`.
4. The frozen equivalence runner independently records `controller_radius: 0.015` at `server_run_one.py:340`.

The authority is therefore unique and resolved for this Stonehenge controller. V2 names it `CONTROLLER_GEOMETRY_AUTHORITY`. The future L0 implementation must consume the runtime controller authority value and identity read-only; it must not reproduce the literal `0.015` in a second L0 configuration.

Required authority identity:

- source path: `run.py`
- source field: Stonehenge scene variable `radius`
- upstream commit: `3c2ad6122d61436c845cb449c41fae0cd2c1608f`
- Git blob: `361f09fc8f37e4713ea2fc8975d82d56cb9be46a`
- units: metres
- consumer chain: controller construction → `CBF.radius` → Gaussian query `radius`

If that chain is missing, ambiguous, nonfinite, negative, or inconsistent with logged provenance, V2 L0 must fail closed as unresolved and must not fall back to an independent default radius.

## Certification margin authority

The margin is a separate pre-existing policy, not a new fit. In commit `04ebca2b1b35124ad0e61ebed96e491c9edae4bb`, `task_config.py:20-22` separately declared:

- `ROBOT_RADIUS_M = 0.1`
- `FIXED_SAFETY_MARGIN_M = 0.01`
- `ROBOT_EFFECTIVE_RADIUS_M = ROBOT_RADIUS_M + FIXED_SAFETY_MARGIN_M`

The independent field name, separate assignment, and explicit additive composition predate PR #105 and all present design decisions. V2 preserves only the `FIXED_SAFETY_MARGIN_M=0.01` policy. It rejects the former independent shadow base radius and instead composes the margin with the controller authority.

## V2 composition

`r_L0_eff = r_controller + m_cert = 0.015 + 0.01 = 0.025 m`

`h_L0(p)=min_i[phi_i*d_i^2-r_L0_eff^2]`

The effective radius appears once in the barrier. No other radius, margin, epsilon, map inflation, or Gaussian-scale inflation is added by this contract.
