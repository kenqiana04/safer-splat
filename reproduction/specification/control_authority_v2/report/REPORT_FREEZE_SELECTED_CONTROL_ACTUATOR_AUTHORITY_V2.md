# Report: Freeze Selected Control Actuator Authority V2

## Answer-first

1. **Does CBF-QP output execute directly?** Yes, for successful frozen simulation solves. `run.py` assigns the Clarabel result to `u` and passes it unchanged to `double_integrator_dynamics`. Solver-failure fallback is not committed.
2. **Is there hidden saturation?** No post-QP saturation exists. The `[-0.1,0.1]` clamps occur before the QP and shape `u_des`; they do not bound the QP result.
3. **Who owns actuator authority?** V2 freezes one normative benchmark authority with inclusive `u in [-0.1,0.1]^3`, velocity bounds of the same box, and `dt=0.05`. Physical hardware authority remains unknown/outside method.
4. **Which control is certified?** The exact candidate vector and identity that become selected and committed. Any value-changing transform invalidates the prior certificate and requires new identity plus re-certification.
5. **Do backup and terminal share the contract?** Yes. Every backup command and terminal zero action uses the same normative actuator authority.

## Static evidence

`run.py:118-127` forms and clamps `u_des`. `cbf/cbf_utils.py:41-122` builds a QP with CBF constraints but no actuator box constraints. `cbf/cbf_utils.py:125-143,178-202` returns a Clarabel solution only for `Solved`. `run.py:138-147` stops on failure and otherwise sends the same `u` to the plant. `dynamics/systems.py:3-26` interprets it directly as acceleration.

Current simulation verdict: `CERTIFIED_EXECUTION_MATCH_IN_FROZEN_SIMULATION_PATH`.

This verdict does not imply physical execution. No hardware limit, slew/rate/jerk, delay, quantization, or tracking-error authority appears in the active source.

## Frozen V2 authority chain

`u_des → CBF-QP candidate → actuator admission → selected control → identity commit → normative plant update`

- G0 nominal: PD `u_des`; desired, not certified.
- G1 candidate: successful CBF-QP result.
- G2 selected/committed: unique candidate identity after actuator and applicable safety certificates.
- G3 actuator: normative componentwise inclusive hard bounds; physical authority outside method.

Post-certification transformation is forbidden. Explicit clipping can only produce a new candidate identity which re-enters certification. Unknown semantics block and never fall back to the desired or legacy path.

## Alternative, backup, and terminal compatibility

The frozen reusable actuator certificate admits unchanged controls inside the box. Backup braking derives each control from the same bounds and rechecks it. Terminal zero is checked under the same authority. No L2/L3/L5-specific actuator model is allowed.

## Validation and boundary

- Design commit: `5ec1751c586aef70bde0434cc0ae198b4f39ee01`.
- Canonical contract SHA-256: `66eb339744248984e593c196162120f1d8578d4666c0337d828c8c868e65be83`.
- Synthetic tests: 10/10 PASS.
- Validator: `PASS_SELECTED_CONTROL_ACTUATOR_AUTHORITY_V2_FREEZE`, 22/22.
- Runtime/controller/dynamics mutations: 0/0/0.
- Actuator simulation, rollout, GPU, formal cohort, performance evaluation: all 0.
- PR #107 method logic and PR #108 geometry remain unchanged.

No safety improvement, controller improvement, performance gain, physical execution guarantee, or deployment readiness is claimed.

## Blocker DAG

`SELECTED_CONTROL_ACTUATOR_AUTHORITY=RESOLVED`. Remaining blockers are deadline authority, alternative source, terminal/emergency policy, backup-token runtime schema, and independent evaluation oracle.

`FINAL_STATUS=PASS_SELECTED_CONTROL_ACTUATOR_AUTHORITY_V2_FREEZE`

`FINAL_DECISION=FREEZE_SELECTED_CONTROL_ACTUATOR_AUTHORITY_AND_ADVANCE_BLOCKER_DAG`

Only next task: `FREEZE_RUNTIME_ASSURANCE_DEADLINE_AUTHORITY_V2`.
