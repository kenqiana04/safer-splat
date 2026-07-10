# R1 Supervisory Mode Semantics Audit

## Scope

This is the updated Stage-0 interface audit for R1 Verification-Aware
Supervisory Mode Selection. It does not run a shadow context, execute a
supervisor, or modify a formal command.

The provenance-confirmed V1 and V4-B helpers required by the original V4-C
runner are restored with matching source/target hashes. Static closure,
runtime symbols, importability, cloned-state behavior, and a direct-versus-
adapter equivalence check now support an executable M2 shadow interface.

normal_mode_status: shadow_evaluable
slowdown_mode_status: shadow_evaluable
recovery_mode_status: shadow_evaluable
safe_halt_mode_status: interface_only
common_horizon_comparison_supported: true
mode_state_isolation_supported: true
recovery_shadow_evaluation_supported: true
progress_proxy_supported: true
shadow_audit_ready: true

These statuses describe interface support, not method quality or effectiveness.

## M0: normal_filtered_execution

M0 remains the three-dimensional acceleration-like `u_safe` returned by the
existing CBF-QP wrapper and evaluated with the existing repeated-command
H1/H2/H3 verifier. It is included in a future shadow audit.

## M1: warning_gated_slowdown

M1 remains the existing bounded warning-streak policy with warning,
persistent-warning, and critical scales. It acts on a copied command and is
included in a future shadow audit. No slowdown evaluation was run here.

## M2: existing_v4c_recovery

M2 uses the original V4-C H3_N128 configuration: horizon 3, 128 sampled
sequences, `on_margin_violation`, `dt_margin=0.0005`, and
`warning_margin=0.0008`. A thin adapter constructs the namespace and cloned
context, then calls the original `generate_sequences`, `evaluate_sequences`,
and `rollout_sequence` functions. It does not reproduce candidate generation,
cost, ranking, rollout, or selection.

On one deterministic real-flight interface context, the adapter matched direct
original-function evaluation across 22 fields with no critical mismatch. The
selected control was not executed, input state remained unchanged, and RNG was
restored. M2 is included in a future shadow audit.

## M3: grounded_safe_halt

M3 remains excluded. The system is a double integrator, so zero acceleration
does not stop nonzero velocity. No provenance-confirmed stop contract or halt
adapter was found. Its status remains `interface_only`.

## Stage-0 Decision

M0-M2 can be compared under the common H-step diagnostic horizon with isolated
state and a comparable goal-distance-reduction proxy. This makes the
preregistered shadow audit executable as a separate task. It does not establish
shadow opportunities, active effectiveness, recovery performance, or a safety
guarantee.

The current task restores the original V4-C dependency closure and reassesses interface readiness; it does not revalidate recovery performance or R1 effectiveness.
