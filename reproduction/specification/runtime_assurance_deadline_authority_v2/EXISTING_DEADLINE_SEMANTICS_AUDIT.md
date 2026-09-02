# Existing Deadline Semantics Audit

The frozen V1 executable certifier accepts a `time_budget`, constructs a monotonic `deadline`, checks it before candidate work, and forwards it into backup certification. Exhaustion returns a non-success classification (`TIME_BUDGET_EXHAUSTED`); backup exhaustion similarly returns no valid witness. These facts support bounded local computation and the prohibition on treating timeout as success.

They do not establish the V2 global authority. The V1 certifier currently constructs its own deadline, while PR #107 requires a cross-layer sample deadline, guard/reserve, and latest-safe commit semantics. V2 therefore quarantines the V1 pattern as a local timeout implementation precedent. Only the Supervisor owns the global cycle deadline and decides whether another stage may start.

PR #107 already requires L4 eligibility to include an open deadline and a retained lawful fallback. Its historical `GUARD_REACHED` semantics map to V2 `DEADLINE_WARNING`: no new high-cost search may begin. No runtime source is changed by this specification.
