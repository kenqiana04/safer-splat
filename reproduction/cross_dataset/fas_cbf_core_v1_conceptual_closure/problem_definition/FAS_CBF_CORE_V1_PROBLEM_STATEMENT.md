# Problem statement

Inputs are Gaussian map G, state x_k, nominal control u_nom,k, actuator set U,
sample period Delta t, footprint B, fixed margin rho, flow Phi, backup policy,
terminal set X_T, and an UNKNOWN policy. Outputs are certified nominal,
alternative, backup, or terminal actions; otherwise FAIL_CLOSED_UNRECOVERABLE,
NOT_EVALUABLE_MAP_QUERY, or INFRASTRUCTURE_FAILURE.

The object of certification is the represented Gaussian obstacle field under stated
map and error assumptions. Map certificate, execution certificate, offline
reference-oracle evaluation, and deployment guarantee are different claims.
