# SAFER Baseline Navigation Stack Audit

## 1. Purpose

This report audits the current `/disk1/zlab/projects/safer-splat` repository as a navigation safety stack, not as a new experiment. The goal is to identify what is actually implemented for nominal navigation, dynamics, CBF-QP filtering, discrete-time verification, and recovery, so the paper can be positioned accurately.

This audit is static source inspection only. It does not run new trials, full100 evaluation, flight20 continuation, or V4-C experiments.

Generated evidence:

- `work/risk_aware_cbf/scripts/audit_safer_navigation_stack.py`
- `work/risk_aware_cbf/results/navigation_stack_audit/navigation_stack_symbols.json`
- `work/risk_aware_cbf/results/navigation_stack_audit/navigation_stack_audit_raw.md`

## 2. Repository-Level Pipeline

The current executable pipeline is best described as:

```text
GSplat / ellipsoid map
  -> circular start-goal configuration
  -> simple goal-directed nominal action
  -> CBF-QP safety filter
  -> double-integrator rollout
  -> h / collision / solver / runtime logging
  -> optional wrapper-side DT verification
  -> optional wrapper-side triggered V4-C predictive recovery
```

The repository does not expose a full robot navigation stack with localization, map-to-robot calibration, global planning, local planning, or wheel-level command interfaces. The safest paper framing is therefore a planner-agnostic GSplat navigation safety assurance layer.

## 3. Nominal Planner / Controller Audit

### Current nominal action source

The official `run.py` uses a simple PD-like goal-tracking control law. The state is a 6D vector, the goal is a 6D target with zero terminal velocity, and the nominal action is a 3D acceleration command:

- `run.py:118-127`: computes `vel_des`, then `u_des`, then clamps `u_des` to `[-0.1, 0.1]`.
- `run.py:132`: passes `u_des` into `cbf.solve_QP(x, u_des)`.
- `work/risk_aware_cbf/scripts/run_risk_aware_v1_pre_cbf_comparison.py:276-281`: wrapper function `nominal_control(x, goal)` mirrors the same goal-directed action.

### Global planner

Explicit global planner: not found / not implemented in this repository.

There are references to planning terms in reports, notes, and general documentation, but no source-level global planner implementation was found that produces a route, graph path, RRT tree, A* path, or multi-waypoint trajectory for the current safety-filter experiments.

### Local planner

Explicit local planner: not found / not implemented in this repository.

The available nominal behavior is a direct goal-directed controller, not a local planner with obstacle-aware trajectory optimization or waypoint tracking.

### Waypoint tracking

Explicit waypoint tracking: not found / not implemented in this repository.

The start-goal pairs are generated on scene-specific circles:

- `run.py:88-93`
- `work/risk_aware_cbf/scripts/run_risk_aware_v1_pre_cbf_comparison.py:254-273`

The controller tracks a final goal state, not a waypoint sequence.

### Contribution boundary

The paper should say that the nominal command source is an existing or external baseline command source. It should not claim a new planner, localization module, or waypoint-tracking system.

## 4. Dynamics and Control Model Audit

The official dynamics are a 3D double-integrator point model:

- `dynamics/systems.py:3-26`: `double_integrator_dynamics(x, u)` maps `[x, y, z, vx, vy, vz]` and `[ux, uy, uz]` to `[vx, vy, vz, ax, ay, az]`.
- `dynamics/systems.py:40-69`: `DoubleIntegrator.system` returns `f`, `g`, and the state Jacobian for relative-degree-2 CBF construction.
- `run.py:86`: creates `DoubleIntegrator(device=device, ndim=3)`.
- `run.py:147`: advances the state with `double_integrator_dynamics(x, u) * dt + x`.

State vector:

```text
x = [x, y, z, vx, vy, vz]
```

Control vector:

```text
u = [ux, uy, uz]
```

Current model can not directly be called a four-wheel robot model. It is not a differential-drive, skid-steer, Ackermann, or four-wheel dynamics model. It is an abstract point-mass / double-integrator simulation model in 3D.

Real-robot experiments should be framed as deployment interface demonstrations unless a separate robot-specific dynamics adapter and command interface are implemented.

## 5. CBF-QP Safety Filter Audit

The CBF-QP interface is:

```text
input: state x, nominal action u_des
output: filtered action u_out and solver_success status
```

Evidence:

- `cbf/cbf_utils.py:41`: `get_QP_matrices(self, x, u_des, minimal=True)`
- `cbf/cbf_utils.py:45`: queries `self.gsplat.query_distance(x[..., :3], radius=self.radius, distance_type=self.distance_type)`
- `cbf/cbf_utils.py:55`: obtains `f, g, df = self.dynamics.system(x)`
- `cbf/cbf_utils.py:71-72`: sets `P = I` and `q = -u_des`, so the QP stays close to nominal action.
- `cbf/cbf_utils.py:125-143`: `solve_QP` returns the filtered control or falls back to `u_des` after solver failure.
- `cbf/cbf_utils.py:178-202`: uses Clarabel to solve the QP.

Wrapper-side logging extends this without modifying official core code:

- `work/risk_aware_cbf/scripts/run_risk_aware_v1_pre_cbf_comparison.py:385-468`: `DetailedCBF` records h values, selected active Gaussian IDs when available, active constraint count, mapping status, and QP infeasible count.

The h value is the repository safety-function value returned by `GSplatLoader.query_distance`. It is not metric clearance in meters.

## 6. GSplat / Ellipsoid Map Interface Audit

The map interface is `splat.gsplat_utils.GSplatLoader`.

Evidence:

- `splat/gsplat_utils.py:13-22`: `GSplatLoader` accepts a JSON file or Nerfstudio config path.
- `splat/gsplat_utils.py:24-43`: loads Nerfstudio GSplat tensors.
- `splat/gsplat_utils.py:46-82`: loads JSON tensors.
- `splat/gsplat_utils.py:103-190`: `query_distance` computes h, gradient, Hessian, and info.
- `splat/gsplat_utils.py:147-185`: `ball-to-ellipsoid` rotates into ellipsoid frame, solves point-to-ellipsoid distance, and returns signed safety h and derivatives.

The safety query is ellipsoid-based, not point-center substitution.

## 7. Discrete-Time Verification Audit

Discrete-time verification currently appears as wrapper-side evaluation around the baseline CBF-QP output:

- `work/risk_aware_cbf/scripts/run_adaptive_v1_flight20_closed_loop.py:269-293`: `query_min_h` and `rollout_min_h_by_horizon`.
- `work/risk_aware_cbf/scripts/run_adaptive_v1_flight20_closed_loop.py:368-381`: computes nominal H-step warning signals before filtering.
- `work/risk_aware_cbf/scripts/run_adaptive_v1_flight20_closed_loop.py:421-430`: computes executed-control H-step min h values.
- `work/risk_aware_cbf/scripts/run_adaptive_v1_flight20_closed_loop.py:465-470`: logs `H1_min_h`, `H2_min_h`, `H3_min_h`, and margin violation flags.

Interpretation:

- H-step margin violation means the short-horizon predicted min h is below `dt_margin`.
- Margin violation is not collision.
- Collision is logged separately when actual h goes below zero.
- DT verification is a wrapper audit / safety assurance layer around the sampled-data execution, not a proof of global safety.

## 8. Recovery Audit

V4-C recovery is implemented as a wrapper-side triggered predictive recovery, not a replacement for the nominal controller or CBF-QP.

Evidence:

- `work/risk_aware_cbf/scripts/run_v4c_hstep_predictive_recovery.py:468-474`: `should_activate` triggers recovery under `always`, `on_warning`, or `on_margin_violation` modes.
- `work/risk_aware_cbf/scripts/run_v4c_hstep_predictive_recovery.py:522-526`: baseline action is still `u_nom -> cbf.solve_QP`.
- `work/risk_aware_cbf/scripts/run_v4c_hstep_predictive_recovery.py:535-548`: base horizon min h is evaluated and activation is decided.
- `work/risk_aware_cbf/scripts/run_v4c_hstep_predictive_recovery.py:554-588`: if activated, candidate sequences are generated and evaluated; the selected first action becomes `u_exec`.
- `work/risk_aware_cbf/scripts/run_v4c_hstep_predictive_recovery.py:591-604`: the selected action is executed through the same double-integrator update and collision is still checked by actual h.

Positioning:

- V4-C is optional and triggered.
- It does not replace the CBF-QP safety filter.
- It does not replace the nominal planner/controller.
- It should be written as a recovery module under short-horizon DT warnings.

## 9. What SAFER Provides vs What Our Framework Adds

| Component | SAFER / baseline provides | Our framework adds |
|---|---|---|
| GSplat safety map | GSplat loader and ellipsoid safety query | Reuse of the same query for certification, repair, DT audit, and recovery checks |
| Nominal command filtering | CBF-QP filters `u_des` into `u` | Feasibility-aware start checks and wrapper-side diagnostics |
| Dynamics | 3D double-integrator simulation | DT H-step verification using the same rollout model |
| Closed-loop benchmark | Circular start-goal simulation and logs | Start-Safe repair, active-set projection, and post-repair validation framing |
| Runtime / constraints | QP timing and pruning path | Active constraint diagnostics and frozen efficiency ablations |
| Recovery | Not an always-on planner replacement | Optional triggered V4-C predictive recovery under DT warnings |

This should neither overstate nor minimize SAFER. SAFER provides the core GSplat CBF-QP safety filter baseline. Our work enhances it with feasibility-aware start certification, repair, discrete-time verification, triggered recovery, and deployment-oriented safety assurance framing.

## 10. Paper Positioning Recommendation

Recommended positioning:

```text
planner-agnostic safety assurance layer for GSplat-based robot navigation
```

Not recommended:

- complete planner
- complete localization system
- four-wheel-specific planning algorithm
- pure initial safety detector
- global safety guarantee
- full real-robot benchmark claim

The main paper title should not include "four-wheel" unless the method is later adapted to a four-wheel dynamics and command interface. It is safer to discuss the four-wheel platform only in the real-robot deployment section.

## 11. Gaps Before Real-Robot Deployment

Missing interfaces before real-robot deployment:

1. Robot pose source.
2. Map-to-robot frame calibration.
3. GSplat safety query in robot/world frame.
4. Nominal command source from the real navigation stack.
5. `cmd_vel` or Ackermann command interface.
6. Safety-filter output mapping from 3D acceleration to robot commands.
7. DT rollout dynamics matching the real robot.
8. Emergency stop / fallback path.
9. Rosbag or equivalent logging and evaluation metrics.
10. Safety operator procedure and test-space constraints.

Until these are implemented, real-robot work should be described as a deployment plan or interface demonstration, not four-wheel dynamics validation.

## 12. Final Audit Conclusions

- Explicit global planner: not found / not implemented in this repository.
- Explicit local planner: not found / not implemented in this repository.
- Localization interface: not found / not implemented in this repository.
- Four-wheel robot dynamics: not found / not implemented in this repository.
- Current nominal action: simple PD-like goal-directed 3D acceleration command.
- Current dynamics: 3D double-integrator point model.
- Current safety filter: GSplat ellipsoid CBF-QP using Clarabel.
- Current DT verification: wrapper-side H-step min-h audit and margin flags.
- Current V4-C recovery: optional triggered wrapper, not baseline replacement.
- Current best paper framing: planner-agnostic GSplat navigation safety assurance layer.

No new experiments were run for this audit.
