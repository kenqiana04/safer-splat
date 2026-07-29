# Replica Dual-Map Safety Generalization Protocol V1

This is the auditable preflight record for `REDEFINE_CROSS_DATASET_VALIDATION_PROTOCOL_V1`.

## Result

`BLOCKED_BY_REPLICA_ROBOT_CONTRACT_AMBIGUITY`

The frozen Replica V3 input identity, the unmodified SplaTAM pilot-map identity, and the SAFER authority identity all pass their respective preflight checks.  The qualification stops before route generation or any Gaussian-array read because the highest-priority Stonehenge formal source gives no finite, formal `vmax` or `umax`.  The QP is unconstrained; the `[-0.1, 0.1]` clipping applies only to the desired command and is not a physical/control constraint on the QP output.  The Risk-Aware and FAS-CBF freeze files do not resolve this missing bound.

The protocol needs those finite bounds to compute the one-step reachable displacement and hence to freeze `rho_corridor`.  Substituting the desired-command clip would silently change the frozen robot contract.  No route registry, corridor, map-distance query, map modification, fallback map, controller, navigation, CBF-QP, or TUM run was performed.

See `replica_robot_and_dynamics_contract.json` and `REPORT_REPLICA_DUAL_MAP_SAFETY_GENERALIZATION_PROTOCOL_V1.md` for the source-level evidence and the exact reauthorization boundary.
