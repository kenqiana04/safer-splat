# Minimal Source Audit

- **Plant arithmetic:** `PlantCommitAdapter` owns plant side effects. Its default and frozen GPU-injected transition construct state/action as `torch.float32`, evaluate `x + double_integrator_dynamics(x,u) * float(dt)`, then serialize through `detach().cpu().tolist()` into Python floats.
- **Snapshot serialization:** `RuntimeStateSnapshot.create` converts six state scalars and hashes trial/cycle/state/goal/map/dt. No extra rounding is applied after the plant tuple.
- **L1:** frozen `L1Runtime.evaluate_cycle` constructs the endpoint with Python `p + dt*v` and caches once per `(state identity, cycle)`.
- **L2:** frozen `L2Runtime.evaluate` constructs `p_k1` and `p_k2` with independent Python closed-form expressions.
- **L3/backup:** the frozen builder converts snapshot/candidate into certifier `State/Control`; `BackupCertifier` propagates via `PositionFirstForwardEulerDoubleIntegrator.transition` and obtains swept endpoints from the same host-arithmetic adapter.
- **Terminal:** `TerminalCertifier` uses the shared swept certifier for zero hold; `TerminalRuntime` owns no prediction arithmetic.
- **StartAdmission:** current-state query only; prediction migration is unnecessary, but canonical state identity binding is required.
- **V3 composition:** the V3 stack factory builds the frozen V2 object graph and already supports additive post-build inspection. Counted wrappers expose their modules through `_module`; plant, token-store, trace, and runner dependencies can be replaced before startup.
- **Trace/commit:** `ActiveCommitTransaction` is the fixed commit/token/trace sequencer. A `TraceWriter` subclass can append observational identity fields without altering routing or transaction order.

Decision: additive implementation is feasible. Frozen runtime, certifier, dynamics, V3 geometry, controller, Supervisor, and evidence trees remain byte-identical.
