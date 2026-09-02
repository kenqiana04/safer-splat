# Backup Token Temporal Schema V2

The normative state is `x_k=(p_k,v_k)` and the source candidate is `u_k` under `POSITION_FIRST_FORWARD_EULER_DOUBLE_INTEGRATOR_V1`:

- `p_(k+1)=p_k+dt*v_k`
- `v_(k+1)=v_k+dt*u_k`
- L1 is the candidate-independent closed segment `[p_k,p_(k+1)]`.
- L2 is `[p_(k+1),p_(k+2)(u_k)]` with `p_(k+2)=p_k+2dt*v_k+dt^2*u_k`.
- The L3 witness begins at predicted `x_(k+1)` after `u_k`.
- Tail element zero is `u_(k+1)^backup`; it is never `u_k`.

L3 completion creates only `PREPARED_UNCOMMITTED`. The token is not a fallback and cannot execute before the exact source candidate commits. Successful commit in cycle `k` atomically activates the token for cycle `k+1`; therefore `activation_cycle = certification_cycle_k + 1`, expected state is `x_(k+1)`, expected cursor is zero, and expected current control is `u_(k+1)^backup`.

On successful exact backup commit at cycle `j`, cursor `q` is consumed once, cursor advances to `q+1`, expected state becomes the bundle's certified next state, and expected cycle becomes `j+1`. No advance occurs before commit, no cursor is skipped, and no action is consumed twice. The repeated legacy terminal state is a documented zero-hold evidence transition, not an accidental control duplication.
