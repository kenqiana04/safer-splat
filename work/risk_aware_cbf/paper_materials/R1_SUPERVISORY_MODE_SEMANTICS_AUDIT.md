# R1 Supervisory Mode Semantics Audit

## Scope and Result

This is the Stage 0 interface audit for R1 Verification-Aware Supervisory Mode
Selection. It is not a shadow run and it does not execute a supervisor,
slowdown, recovery, halt, or changed formal command.

The V4-C restoration audit recovered provenance-confirmed, byte-identical
copies of the original runner, sweep, analysis script, and official smoke
wrapper. The recovered runner imports in its original 4090 environment and
exposes candidate generation and evaluation functions. The current Git branch,
however, still lacks the runner's original V1/V4-B helper imports, which are not
permitted restoration targets in this task. A historical report is not used as
a substitute for those missing executable dependencies.

normal_mode_status: shadow_evaluable
slowdown_mode_status: shadow_evaluable
recovery_mode_status: insufficient_semantics
safe_halt_mode_status: interface_only
common_horizon_comparison_supported: insufficient_semantics
mode_state_isolation_supported: insufficient_semantics
recovery_shadow_evaluation_supported: insufficient_semantics
progress_proxy_supported: implemented_supported
shadow_audit_ready: insufficient_semantics

The permitted status values above describe interface support, not method
quality. M2's `insufficient_semantics` status is an interface-dependency gap,
not a negative recovery result.

## M0: normal_filtered_execution

The documented formal action is the three-dimensional acceleration-like
`u_safe` returned by `cbf.solve_QP(x, u_nom)`. The official state is six
dimensional: position followed by velocity. The documented wrapper executes
Euler propagation as `double_integrator_dynamics(x, u_safe) * dt + x`.

Existing Level-3 and VANS scripts show a compatible repeated-command H1/H2/H3
verifier and define a diagnostic one-step goal-distance-reduction proxy. A
fresh CBF evaluator on a cloned state is also an established isolation pattern.
The exact smoke wrapper is restored with a source-matching SHA256. It imports
and exposes the expected scenes in the original 4090 environment, so M0 is now
shadow-evaluable at the wrapper interface. No trajectory was executed here.

## M1: warning_gated_slowdown

`safc_warning_slowdown_policy.py` provides a bounded wrapper-level policy. Its
current policy scales are warning `0.75`, persistent warning `0.50`, critical
warning `0.25`, with minimum scale `0.25` and a maximum per-step scale change
of `0.25`. The helper does not itself mutate a control vector; existing active
wrappers apply the resulting scale only to a copied execution command after a
natural H1/H2/H3 warning.

The policy semantics match the Level-3D and Level-3E helper family. Together
with the restored M0 wrapper, M1 is shadow-evaluable at the wrapper interface.
No counterfactual M1 evaluation was run in this restoration task.

## M2: existing_v4c_recovery

The retained V4-C documentation identifies two named configurations:

- robust reference: H3_N128, horizon `3`, 128 sequences,
  `activation_mode=on_margin_violation`, `dt_margin=0.0005`;
- tuned reference: R4_H2_N64, horizon `2`, 64 sequences,
  `activation_mode=on_margin_violation`, `dt_margin=0.0005`, `w_goal=0.2`,
  and `w_safety=10.0`.

The restored source matches the reports: it generates H-step sequences, selects
the lowest-cost feasible candidate, falls back to the candidate with the best
horizon minimum safety when no candidate passes, returns only its first
control, and marks recovery success/failure. It also exposes
`generate_sequences` and `evaluate_sequences`; the rollout clones input state.

The runner is callable in its original 4090 source environment but cannot be
imported in this Git branch because
`run_risk_aware_v1_pre_cbf_comparison.py` and
`run_v4b_corrective_dt_filter.py` are absent. Consequently M2 cannot yet be
evaluated with current-branch state, solver, RNG, and controller isolation. No
substitute action, copied recovery, or adapter is permitted.

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
R1 nevertheless requires an independent M2 evaluator in the current branch.
The restored source establishes the intended H-step and progress semantics, but
the unresolved helper dependencies prevent common current-branch evaluation,
formal replay, and recovery isolation validation.

Stage 3 is therefore blocked by interface limitations. No selector or shadow
runner is added, no C004 smoke is run, and no formal trajectory is produced.

## Required Follow-up Before Reopening R1

1. Conduct a separate provenance review for the two missing original V4-C
   helper modules before adding them to this branch.
2. Run a separate nonfunctional interface/equivalence task to demonstrate
   fresh evaluator construction,
   cloned-state behavior, solver/RNG/controller isolation, and the identical
   H-step/progress definitions for M0, M1, and M2.
3. Only after all gates pass, preregister included modes and run the bounded
   shadow audit. Active R1 remains out of scope.

This finding is an interface limitation. It neither validates nor falsifies H7
or the V4-C mechanism.
