# Frozen replay protocol

- Direct upstream: PR #94 at `9bffdd2db585974ee61684cebfc99229aa52c47c`.
- Unit: frozen candidate-state-map-snapshot tuple.
- Source universe: PR #89 normalized one-step rows, non-duplicated PR #87 activated one-step rows, only genuinely logged B3 alternatives, and PR #87 rollout-step rows retained even when not replayable.
- The 6,853-row manifest was frozen before any L2 invocation.
- Formal replay requires full state, numeric candidate, frozen map authority, robot contract, backend identity, and query context.
- Primary evaluation requires stored architecture evidence that L1 passed and L2 was reached.
- Dynamics: position-first forward-Euler double integrator, `dt=0.05`, `p_k1=p_k+dt*v_k`, `p_k2=p_k+2*dt*v_k+dt^2*u_k`.
- Formal backends: exact analytic sphere or conservative signed-distance Lipschitz interval. Sampled diagnostics have no authority; endpoint fallback is disabled.
- No new state, candidate, map, controller decision, rollout, or on-policy collection is permitted.
