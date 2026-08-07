# H1 control-authority derivation

Under the frozen `POSITION_FIRST_FORWARD_EULER_DOUBLE_INTEGRATOR_V1`, `p_(k+1)=p_k+dt*v_k` and `v_(k+1)=v_k+dt*u_k`. For `alpha in [0,1]`, the first control-affected position segment is

`p_H1(alpha;x_k,u_k)=p_(k+1)+alpha*dt*v_(k+1)=p_k+(1+alpha)*dt*v_k+alpha*dt^2*u_k`.

Therefore `d p_H1(alpha)/d u_k=alpha*dt^2*I`: it is zero at the shared start point, nonzero for every `alpha>0`, and equals `dt^2*I` at `p_(k+2)`. `u_(k+1)` changes `v_(k+2)` only after the H1 position segment has been formed under the frozen update order. This is model-specific and is not a universal double-integrator statement.
