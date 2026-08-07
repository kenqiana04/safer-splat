# H1 segment contract

`S_H1(x_k,u_k)=Segment(p_(k+1),p_(k+2)(u_k))`, parameterized by

`p_H1(alpha)=p_k+(1+alpha)dt*v_k+alpha*dt^2*u_k`, `alpha in [0,1]`.

It is the `FIRST_CONTROL_AFFECTED_SEGMENT`. Its start is shared by all candidates; every interior point and the endpoint depend on `u_k`. In contrast, L1 is `Segment(p_k,p_(k+1))` and has no `u_k` position authority. The same frozen geometry backend may serve both segments, but their causal role, state-machine location, failure semantics, and denominators are different.
