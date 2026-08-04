# Stopping bound derivation

With frozen `dt=0.05`, `vmax=0.1`, and `umax=0.1`, per-axis one-sample
reaction travel is `dt*vmax=0.005` m and braking travel is
`vmax^2/(2*umax)=0.05` m. The conservative Euclidean
bound is `sqrt(3)` times their sum: `0.0952627944163` m. Adding robot radius,
base margin, zero oracle-state localization/shape/sampling terms, and the
0.03 m tracking target gives a non-map reserve of `0.235262794416` m.
