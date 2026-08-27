# Zero-Authority Contract

For every payload and result:

| Field | Required value |
|---|---|
| `controller_authority` | `false` |
| `execution_authority` | `false` |
| `candidate_selection_authority` | `false` |
| `alternative_authority` | `false` |
| `backup_authority` | `false` |
| `terminal_authority` | `false` |
| `fail_close_authority` | `false` |
| `intervention` | `false` |
| `shadow_only` | `true` |

There is no result-return interface, shared mutable candidate object, controller callback, IPC request from controller to worker, or worker-to-controller queue. `controller_output` equals the frozen controller output and is never a function of `shadow_result`.

If queue enqueue, serialization, worker execution, or shutdown fails, the controller continues the frozen path using the already accepted `u_k`. A minimal health/drop counter may be updated through a nonthrowing, nonblocking primitive; failure to update it is itself an external audit issue, never a controller stop.

L2 semantic fail-closed means an L2 certificate does not claim PASS when formal evaluation yields FAIL/UNKNOWN. It does **not** authorize the observer to stop or change the controller. Observer runtime failure is `OBSERVATION_INCOMPLETE`/observer health, not L2 UNKNOWN.

Future implementation must pass static call-graph/taint review showing no shadow-result consumer in controller code, and an OFF-vs-ON trace-equivalence smoke, before collection.

**Scope:** DESIGN ONLY | NO ON-POLICY COLLECTION | NO CONTROLLER AUTHORITY | NO DECISION FEEDBACK | NO PERFORMANCE CLAIM.
