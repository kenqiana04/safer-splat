# Certificate, source and execution authority

| Fact/operation | Sole authority and contract |
|---|---|
| Propose six local vectors | New versioned recovery-source provider, only after Supervisor route and explicit source registration; no selection or plant rights |
| Candidate identity | Existing immutable `Candidate` provenance plus new source type, snapshot/map/controller/actuator/library identity; no source forgery |
| Once-per-cycle L1 | Existing canonical L1; recovery binds fresh attempts to the same L1 result and cannot mutate it |
| C0/L2/L3 | Existing C0 actuator/provenance gate, canonical L2/H1, canonical L3 finite backup+terminal witness, respectively; no bypass, relaxed radius, tolerance or reused certificate |
| State/arithmetic identity | Existing canonical float32 transition and identity ledger; exact predicted activation vs plant result |
| Route and choose action | `Supervisor.route_transition` and `Supervisor.arbitrate` only; provider and coordinator never select |
| Commit plant | `PlantCommitAdapter.commit` through existing ActiveRunner only |
| Backup token | Existing prepare/activate/consume/invalidate mechanics; no stale resurrection or silent discard of a valid retained token |
| Terminal | Existing TerminalRuntime membership+certificate, Supervisor selection; prefetched fallback must match exact snapshot/map and be re-evaluated next cycle |
| Trace | Existing TraceWriter/ActiveRunner one outcome per public cycle, with additive recovery provenance/reason/cert/status fields |
| Fail close | Global UNKNOWN/identity ambiguity → no recovery action and typed boundary; local FAIL/exhaustion → certified terminal if exact and eligible, otherwise boundary |

The current `make_candidate` lawful source set and `NativeExistingAlternativeProvider` must not be bypassed. Future implementation must add a separately registered `SOURCE_BOUNDED_LOCAL_RECOVERY_V1`; it is not active in V3 and requires fresh source-authority/conformance review. The source value does not imply a safety certificate. Valid retained backup retains priority over a newly proposed search opportunity. Historical 0.025 q remains diagnostic-only.
