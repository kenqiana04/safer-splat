# Frozen position-first control-authority timeline

At `t_k`, the state is `(p_k,v_k)` and the candidate is `u_k`. On `[t_k,t_(k+1)]`, `p(tau)=p_k+tau v_k`; the path is determined by `(p_k,v_k)` and has zero derivative with respect to `u_k`. At `t_(k+1)`, `p_(k+1)=p_k+dt v_k` remains independent of `u_k`, while `v_(k+1)=v_k+dt u_k` is affected. On `[t_(k+1),t_(k+2)]`, the propagated position uses `v_(k+1)` and is candidate-dependent. Thus `p_(k+2)=p_k+2dt v_k+dt^2u_k`.

The immediate segment is therefore primarily execution admission / late-risk detection and a sampled-data consistency check. It is not a candidate safety discriminator. Candidate-dependent position certification cannot begin before the first control-affected segment `[t_(k+1),t_(k+2)]` or endpoint `p_(k+2)`.
