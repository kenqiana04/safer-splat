# Deterministic Braking Policy Derivation

For each velocity component, V1 applies
`u_b,i=clip(-v_i/dt,u_min,i,u_max,i)` while requiring bounds to contain zero.
If one sample can reach zero, the exact acceleration `-v_i/dt` is used;
otherwise the maximum available acceleration opposing the velocity is used.
The implementation explicitly prevents sign reversal.

For the available opposing authority `a_i`, the component needs
`ceil(|v_i|/(a_i dt))` samples. Thus
`H_stop(x)=max_i ceil(|v_i|/(a_i dt))`, and the global bound replaces `|v_i|`
with the frozen componentwise speed bound. One additional zero-hold segment is
certified after rest. A moving component with zero opposing authority produces
a typed fail-closed result; no physical bound is changed.
