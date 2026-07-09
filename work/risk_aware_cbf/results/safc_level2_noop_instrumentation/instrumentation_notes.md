# SAFC Level-2 No-Op Instrumentation Notes

## Scope

This is Level-2 no-op closed-loop instrumentation. It inserts passive SAFC
state logging into a tiny smoke execution/evaluation path. It does not modify
executed controls and does not claim performance improvement.

## Entry Point

- Selected entrypoint: `reproduction/scripts/run_official_runpy_smoke.py`
- Instrumentation completed: `true`
- Reason: Existing bounded official smoke wrapper imported successfully.

The selected existing wrapper is imported as a module. Its bounded scene and
core objects are reused, but its `main` function is not called because that
function writes a trajectory CSV and plot. Official source is not modified.

## No-Op Guarantee

The SAFC helper accepts only scalar/Boolean event snapshots and emits
supervisory decisions and candidates. It neither accepts nor returns action
vectors. The runner reads the original command variables before and after each
SAFC decision and executes the original baseline `u` variable.

## Equivalence Check

- Strength: `strong_action_delta_check`
- `max_abs_delta_u_nom`: `0.0`
- `max_abs_delta_u_safe`: `0.0`
- `max_abs_delta_u_exec`: `0.0`

The check is successful only when every delta is zero, every decision has
`no_op=true`, and no decision has `modifies_control=true`.

## Logged State Behavior

Observed states: S0_PreExecutionCertification, S1_NominalFiltering, S2_VerifiedExecution.

Only grouped transitions and candidate counts are committed. No per-step
timeline or full trial dump is written.

## Claim Boundaries

- No active feedback.
- No slowdown.
- No replanning.
- No planner improvement.
- No warning reduction claim.
- No collision reduction claim.
- No real-robot validation.
- No global safety guarantee.

## Limitations

- Tiny smoke only.
- Not full100.
- Not flight20.
- Not Level 3.
- Not an active policy.
- Not planner integration.
- Not real-robot deployment.
