# Recovery source and family selection

The source ID is `SOURCE_BOUNDED_LOCAL_RECOVERY_V1`; it is neither `PRIMARY_NATIVE_CBF_QP` nor `SOURCE_NATIVE_EXISTING`. It must be explicitly registered as a *recovery-only*, finite, deterministic source in the future registry/C0 path. Source registration does not itself certify an action or modify existing alternative-source defaults. The provider may be queried only by a Supervisor-authorized recovery route.

| Family | Available inputs / bound | Causal/coverage and proof burden | Decision |
|---|---|---|---|
| F1 AXIS_EXTREMA_ONLY | Frozen 3D actuator low/high; at most 6 | At zero velocity, nonzero ±axis acceleration changes `v_(k+1)` and `p_(k+2)`. Has orthogonal directions and can enter existing C0/L2/L3. Finite, local, auditable; no planner. Does not cover diagonal/arbitrary controls. | SELECT |
| F2 AXIS_PLUS_BRAKE | F1 plus current velocity, at most 7 | Velocity-opposing primitive is deterministic and local if exact zero/norm handling is specified, but at the zero-velocity fixed point it degenerates to zero; it adds no mandatory coverage that F1 lacks and increases identity/dedup burden. | REJECT by minimum-sufficient-change rule, not outcome |
| F3 CONTROL_AUTHORITY_AWARE_FINITE_BASIS | F1 plus typed active-constraint/nominal tangent facts, proposed finite bound only after facts frozen | Current runtime has no frozen typed local escape gradient/tangent authority. Inventing it would add query/optimization semantics and planner-like proof burden; cannot reproduce without new authority. | REJECT unavailable-fact gate |

F1 is chosen by hard-constraint dominance, not Formal85, bottom10 membership, progress, map-query result or any trial ID. A finite six-direction basis is **not** complete and does not guarantee safe or improving motion. The historical 0.025 q shell is diagnostic only; hard 0.015 q / margin 0 / rho 0 / no epsilon remain unchanged.
