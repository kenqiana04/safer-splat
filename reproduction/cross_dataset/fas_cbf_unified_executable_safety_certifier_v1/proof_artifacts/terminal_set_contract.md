# Braking-to-Rest Terminal Set V1

`BRAKING_TO_REST_TERMINAL_SET_V1` is a sufficient, online-computable terminal
set for a static represented Gaussian map. A state is admitted only when its
velocity infinity norm is at most `1e-12 m/s`, its full map query is finite and
safe, the map snapshot identity is unchanged, and zero control passes a full
continuous swept-segment certificate for one sample.

The velocity tolerance is a numerical-zero contract: 4096 float64 ulps at unit
scale rounded upward to `1e-12`. It was frozen before tests and was not fitted
to outcomes.

The certificate assumes the normative Euler model, componentwise actuator
bounds, no disturbance, no actuation delay, no tracking error, and a static map
snapshot. It is not a maximal invariant set, a learned terminal controller, or
an infinite-horizon real-robot safety guarantee.
