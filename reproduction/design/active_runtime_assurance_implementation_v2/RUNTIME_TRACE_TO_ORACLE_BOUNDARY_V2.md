# Runtime Trace to Oracle Boundary V2

The active runtime emits only exact immutable runtime facts: trial/authority identities, cycle/state identities, proposal and candidate IDs, typed C0/L1/L2/L3/deadline/token/terminal results, explicit Supervisor-selected action role, selected and executed vector/ID, commit receipt, x_k1, timing observations, and software assurance-boundary events.

`TraceWriter` appends facts and at trial end canonicalizes them, records schema and artifact identities, and finalizes a content-addressed immutable trace lock. Only after that lock exists may the separate post-hoc evaluation process consume the trace under PR #114. Active runtime modules may not import, call, branch on, or receive results from evaluation-oracle decision code. Certificate status is diagnostic input, never a final outcome label. The oracle has no edge back to Supervisor, candidate providers, terminal logic, token state, or plant commit.
