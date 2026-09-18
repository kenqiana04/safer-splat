# Three bounded architectural options and hard-constraint screening

| Property | A — REENTRY_ONLY | B — CERTIFIED_BOUNDED_LOCAL_RECOVERY | C — BACKUP_COVERAGE_EXTENSION |
|---|---|---|---|
| Safety/authority | No new certificate or source; Supervisor still owns routing | Explicit new finite source authority; same C0/L2/L3 and Supervisor/PlantCommit | Cannot lengthen stale token; any new coverage requires a new fully certified bundle |
| New state/candidate | Re-entry marker only; no new action | Six axis-bound local candidate values; one state-keyed attempt inventory | New token lifecycle/coverage state or fresh bundle |
| Canonical/deadline | Unchanged; may add trace | Canonical transition unchanged; only OPEN permits query; terminal prefetched/cached | Existing token identity/lifecycle must not be reinterpreted |
| Complexity/audit | Low; easily audited | Moderate; new source, disjoint routing, finite cursor and trace fields | High; token proof and handoff migration |
| Break numeric fixed point? | No: same state, same P0/L3 facts, same result | In principle yes if at least one *different* action gets fresh L3 PASS; not guaranteed | No token exists in terminal-only states; cannot create one by extending validity |
| Planning risk | None | Local six-vector one-cycle certificate scan only; no waypoint/path search | Low planning risk but high stale-token safety risk |
| Proof burden / migration | Small but insufficient | PO1–PO20; additive source/routing/provider/trace tests | Must re-prove token temporal/state/map identity and shared-runtime behavior |
| Disposition | REJECTED_BY_EXISTING_SEMANTICS as insufficient for observed numeric fixed point | SELECTED, conditional on explicit source authority and all certificates | REJECTED_BY_EXISTING_SEMANTICS; stale extension violates P1/P3 |

Selection is dominance-based, not a weighted score. A already happens at every cycle and cannot change a numerical zero-action fixed point. C cannot lawfully resurrect an absent/stale token. B is the minimum remaining design that can introduce a causally different local action while still requiring the entire frozen certificate/commit chain. The six candidates are the ±axis actuator extrema in three dimensions, mechanically derived from frozen bounds, not selected from the 85 outcomes. They are not asserted sufficient for NI success.
