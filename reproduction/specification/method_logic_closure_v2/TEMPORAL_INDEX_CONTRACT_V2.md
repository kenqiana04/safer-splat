# Temporal index contract V2

Normative discrete model: `POSITION_FIRST_FORWARD_EULER_DOUBLE_INTEGRATOR_V1`.

- State at decision: `x_k=(p_k,v_k)`.
- Proposed/selected action: `u_k`.
- Position update: `p_(k+1)=p_k+dt*v_k`.
- Velocity update: `v_(k+1)=v_k+dt*u_k`.
- L1: closed `[p_k,p_(k+1)]`; candidate independent.
- L2/H1: closed `[p_(k+1),p_(k+2)(u_k)]`, where `p_(k+2)=p_k+2dt*v_k+dt^2*u_k`.
- An L3 witness for candidate `u_k` begins at predicted `x_(k+1)` after `u_k`; its first retained-tail control is `u_(k+1)` and its first control-sensitive segment begins at `p_(k+2)`.
- After committing `u_k`, the prepared token becomes the cycle `k+1` retained backup. No token is valid before the commit/state-index relation is established.
- Terminal zero-hold is an explicitly certified action at its own index. Repeating the terminal state in a witness record is a documented zero-hold transition, not an accidental duplicate.

Contiguity: the end of L1 equals the start of L2; the L3 witness starts from the same `x_(k+1)` implied by the committed candidate; next-cycle token index equals `k+1`. Continuous-ZOH `p(t)=p_k+t v_k+0.5t^2u_k` is nonnormative and cannot be substituted.
