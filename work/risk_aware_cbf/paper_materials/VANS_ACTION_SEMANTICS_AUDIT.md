# VANS Action Semantics Audit

## Summary

action_semantics_status: grounded
directional_candidate_support: unsupported
multi_candidate_qp_evaluation: supported
shadow_evaluation_state_isolation: passed

## Audited Semantics

1. `u_nom` data type: torch Tensor produced by the existing nominal-command helper.
2. `u_nom` dimension: 3.
3. Physical meaning: bounded acceleration-like command for the 3D double-integrator state, computed from goal-position and velocity error.
4. `u_safe` data type and dimension: torch Tensor, 3D, returned by `cbf.solve_QP(x, u_nom)`.
5. Nominal command generation: `nominal_and_safe()` in `safc_level3b_warning_rich_targeted.py`.
6. CBF-QP input interface: current 6D state `x` and 3D nominal action candidate.
7. CBF-QP output interface: 3D filtered command plus solver status on the CBF object.
8. Command execution location: formal rollout applies `double_integrator_dynamics(x, u_safe) * dt + x`.
9. Progress proxy source: one-step goal-distance reduction under the evaluated filtered command.
10. Explicit planar heading / translational direction: not grounded as a planar heading interface.
11. Repeated CBF-QP calls without core-source modification: supported through fresh evaluator instances.
12. Multiple nominal candidates on the same state: supported with cloned state and fresh CBF evaluator.
13. H-step counterfactual verification on the same state: supported via cloned rollout from the evaluated filtered command.
14. State mutation isolation: cloned state plus formal trajectory update after shadow evaluation.
15. Candidate evaluation effect on controller state: isolated by not reusing the formal CBF evaluator for shadow candidates.

Directional candidates are disabled because the available action semantics are
3D acceleration-like commands, not an explicit planar heading interface. This
audit therefore uses only N0/N1/N2.
