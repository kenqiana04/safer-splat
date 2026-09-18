# Future implementation migration scope (not authorized in this task)

| Future component | Permitted change only after separate implementation authorization | Boundary/test |
|---|---|---|
| New source-authority manifest/provider | Explicit `SOURCE_BOUNDED_LOCAL_RECOVERY_V1`; six bound-derived local vectors; one numeric-state key | No `SOURCE_NATIVE_EXISTING` impersonation, no unregistered lawful flag |
| `runtime_types.py` | Additive source, recovery cursor, terminal-precheck and trace types | Existing serialization/BYPASS identities unchanged or trigger revalidation |
| Versioned Supervisor transition table and `supervisor.py` | Typed L3 FAIL reason/scope, disjoint route rows, exact-one lookup, no new final selector | Unclassified FAIL keeps old fallback; existing `arbitrate` priority preserved; no coordinator routing policy |
| `active_cycle.py` | Execute routed precheck/query/certification stages and immutable context/trace handoff | L1 once, C0→L2→L3, finite six, no direct plant |
| Trace schema/additive writer fields | Candidate source/index, trigger, L3 reason, cached terminal identity, route ID, chosen/fallback reason | Existing one-record-per-cycle/commit atomicity unchanged |
| CPU tests/model checker | New fixtures C01–C18, proof obligations PO1–PO20, old 44-row compatibility and new exhaustive exact-one | Zero counterexamples before GPU |

Prefer **no modification** to CBF math, L1/L2/L3 certifier math, canonical transition, map adapter, hard geometry, PlantCommit, backup-token lifecycle, terminal certificate, or ActiveRunner token/trace semantics. Any required shared-source change needs a new bounded review; BYPASS semantics change mandates fresh BYPASS equivalence. Any source/routing change mandates Active conformance and then separately frozen smoke/pilot. Scientific protocol must be refrozen before fresh paired validation. If source authority or exact-one transition rows cannot be proved, implementation blocks rather than widening this design's scope.
