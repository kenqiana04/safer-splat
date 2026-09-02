# Control-Flow Static Trace

## G0 — nominal control authority

`run.py:118-127` constructs the desired command. It computes a PD-like velocity target, clamps `vel_des` componentwise to `[-0.1,0.1]`, forms `u_des`, then clamps `u_des` to the same interval. This is nominal-command shaping only. It does not prove that the later QP solution remains in that box.

## G1 — CBF-QP/certified candidate authority

`run.py:132` calls `cbf.solve_QP(x,u_des)`. `cbf/cbf_utils.py:41-122` forms the QP with `P=I`, `q=-u_des`, and CBF half-space constraints. No actuator box constraints are appended. `cbf/cbf_utils.py:125-143,178-202` accepts the Clarabel vector only when status is `Solved`.

On solver failure, `solve_QP` returns `u_des`, but `run.py:138-143` checks `solver_success` and breaks before the plant update. Therefore the fallback is not committed in this frozen execution path.

The successful QP result is a CBF-feasible candidate. It is not yet evidence of actuator feasibility because the QP contains no actuator-bound rows.

## G2 — committed execution authority

`run.py:132` assigns the successful result directly to `u`. Between that assignment and `run.py:147`, no clip, clamp, saturation, coordinate transform, delay, quantization, or rate limiter exists. `run.py:147` passes the same tensor object/value to `double_integrator_dynamics(x,u)`.

`dynamics/systems.py:3-26` interprets `u` directly as acceleration and concatenates it into the derivative. The simulated relationship is therefore:

`u_selected = u_cbf = u_executed`, conditional on successful solver status.

Verdict: `CERTIFIED_EXECUTION_MATCH_IN_FROZEN_SIMULATION_PATH`.

## G3 — actuator authority

The active `run.py` path exposes no physical actuator model. It has no post-QP saturation, hard acceleration admission, slew/rate/jerk constraint, delay, or quantization. The nominal `u_des` clamp cannot be reclassified as an executed-control bound.

The frozen existing benchmark contract at `.../actuator_contract.json:2-11` defines componentwise inclusive `u,v in [-0.1,0.1]^3`, `dt=0.05`, no hidden clipping, and deferred delta-u/slew/jerk. Its certifier (`actuator_certificate.py:9-22`) admits an unchanged candidate or creates a new identity for an explicitly clipped alternative. V2 adopts these values as a normative benchmark actuator-admissibility authority, not as evidence that current `run.py` implements it and not as a physical hardware guarantee.

Physical rate, delay, quantization, tracking error, and hardware limits remain `OUTSIDE_METHOD_BOUNDARY_UNKNOWN`. Runtime implementation must not begin until the remaining blocker DAG is resolved.

## Backup and terminal

`backup_certifier.py:19-52` checks the initial and every braking control using the same `dynamics.bounds`, then propagates the same control. `braking_backup_policy.py:20-53` derives braking commands from those bounds. `terminal_certificate.py:27-38` uses zero control for both point feasibility and zero-hold segment. V2 freezes the same actuator authority for nominal, alternative, backup, and terminal controls; no layer-local actuator model is permitted.
