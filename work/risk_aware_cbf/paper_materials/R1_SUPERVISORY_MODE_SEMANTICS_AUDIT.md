# R1 Supervisory Mode Semantics Audit

## Scope and Result

This is the Stage 0 interface audit for R1 Verification-Aware Supervisory Mode
Selection. It is not a shadow run and it does not execute a supervisor,
slowdown, recovery, halt, or changed formal command.

The audit stops before Stage 3. The current Git worktree contains historical
V4-C reports and design notes, but not the V4-C recovery implementation needed
to generate and evaluate a recovery candidate from a cloned state. The
`reproduction/scripts/run_official_runpy_smoke.py` wrapper required by the
existing Level-3B, Level-3D, Level-3E, and VANS runners is also absent from the
tracked worktree. A historical text snapshot is not treated as an executable
interface.

normal_mode_status: insufficient_semantics
slowdown_mode_status: implemented_supported
recovery_mode_status: unavailable
safe_halt_mode_status: interface_only
common_horizon_comparison_supported: insufficient_semantics
mode_state_isolation_supported: insufficient_semantics
recovery_shadow_evaluation_supported: unavailable
progress_proxy_supported: implemented_supported
shadow_audit_ready: insufficient_semantics

The permitted status values above describe interface support, not method
quality. In particular, `unavailable` for M2 is not a negative recovery result.

## M0: normal_filtered_execution

The documented formal action is the three-dimensional acceleration-like
`u_safe` returned by `cbf.solve_QP(x, u_nom)`. The official state is six
dimensional: position followed by velocity. The documented wrapper executes
Euler propagation as `double_integrator_dynamics(x, u_safe) * dt + x`.

Existing Level-3 and VANS scripts show a compatible repeated-command H1/H2/H3
verifier and define a diagnostic one-step goal-distance-reduction proxy. A
fresh CBF evaluator on a cloned state is also an established isolation pattern.
However, the executable smoke-wrapper module these scripts import is absent in
this branch, so M0 cannot be executed and replayed from the present source
state. M0 is therefore not marked `shadow_evaluable`.

## M1: warning_gated_slowdown

`safc_warning_slowdown_policy.py` provides a bounded wrapper-level policy. Its
current policy scales are warning `0.75`, persistent warning `0.50`, critical
warning `0.25`, with minimum scale `0.25` and a maximum per-step scale change
of `0.25`. The helper does not itself mutate a control vector; existing active
wrappers apply the resulting scale only to a copied execution command after a
natural H1/H2/H3 warning.

The policy semantics match the Level-3D and Level-3E helper family, but a
counterfactual M1 H-step evaluation cannot be run from the current branch
without the missing smoke-wrapper interface. Its standalone policy contract is
implemented, so its status is `implemented_supported`, not
`shadow_evaluable`.

## M2: existing_v4c_recovery

The retained V4-C documentation identifies two named configurations:

- robust reference: H3_N128, horizon `3`, 128 sequences,
  `activation_mode=on_margin_violation`, `dt_margin=0.0005`;
- tuned reference: R4_H2_N64, horizon `2`, 64 sequences,
  `activation_mode=on_margin_violation`, `dt_margin=0.0005`, `w_goal=0.2`,
  and `w_safety=10.0`.

The design document says V4-C generates H-step control sequences, selects a
sequence using horizon safety and cost, and formally executes only its first
control. It also states that an unsuccessful recovery selects the best
available sequence but records a recovery failure. These statements are
historical design and report evidence, not a callable recovery contract in the
current worktree.

Tracked-file and untracked-file checks find no V4-C runner, candidate generator,
compact configuration artifact, or evaluator implementation. Consequently,
the audit cannot establish candidate generation, recovery success, independent
state isolation, RNG isolation, solver isolation, post-recovery verification,
or runtime for M2. No substitute action or reconstructed recovery is allowed.

## M3: grounded_safe_halt

M3 is not grounded. `dynamics/systems.py` defines a double-integrator state as
`[x, y, z, vx, vy, vz]` and an input as acceleration. With zero control, the
state derivative retains the current velocity, so zero acceleration is not a
stop command and can continue motion under the Euler update. Searches of the
official code found no explicit brake, velocity reset, emergency stop, halt
adapter, or stop contract.

Therefore a zero action is not represented as a safe halt, M3 cannot be
counterfactually rolled out as a grounded halt mode, and M3 is excluded.

## Common Comparison and Isolation Decision

The H1/H2/H3 warning definition and the goal-distance-reduction diagnostic
proxy are semantically compatible in the existing work scripts. Their use for
R1 nevertheless requires a common executable baseline wrapper and independent
M2 evaluator. Neither is available in this branch. Formal executed-command
preservation cannot be empirically checked without a replay, and recovery
state isolation cannot be validated without recovery code.

Stage 3 is therefore blocked by interface limitations. No selector or shadow
runner is added, no C004 smoke is run, and no formal trajectory is produced.

## Required Follow-up Before Reopening R1

1. Restore the original V4-C generator/evaluator and its exact compact
   configuration artifact to a reviewable wrapper-level location.
2. Restore or provide the importable official smoke wrapper required by the
   existing SAFC and VANS runners.
3. Re-run this semantics audit to demonstrate fresh evaluator construction,
   cloned-state behavior, solver/RNG/controller isolation, and the identical
   H-step/progress definitions for M0, M1, and M2.
4. Only after all gates pass, preregister included modes and run the bounded
   shadow audit. Active R1 remains out of scope.

This finding is an interface limitation. It neither validates nor falsifies H7
or the V4-C mechanism.
