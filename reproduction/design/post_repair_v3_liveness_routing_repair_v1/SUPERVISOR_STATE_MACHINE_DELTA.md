# Supervisor-owned state-machine delta (design, not a runtime patch)

The current executable `STATE_TRANSITION_TABLE_V2.csv` has 44 rows. Current relevant rows: `L3_ABSENT_ALT` requires VALID backup + OPEN; `L3_ABSENT_ARB` catches no-search cases; `ALT_NEXT/DONE/GUARD` cover native alternatives; `ARB_BACKUP`, `ARB_EVAL_TERMINAL`, `ARB_TERMINAL`, `ARB_BOUNDARY` arbitrate existing fallback. The new design must version the table, not silently edit the frozen 44-row artifact.

| Source phase | Event | Required facts / guard | Deadline | Candidate / backup / recovery | Destination | Action / certificate authority | Failure mapping / trace |
|---|---|---|---|---|---|---|---|
| L3 | `L3_WITNESS_ABSENT` | Primary, same-cycle L1 PASS, no valid backup, source registered, exact identities, numeric-state key unattempted | OPEN | primary; backup invalid/none/exhausted; recovery idle | TERMINAL_PRECHECK | Supervisor route; no action yet | `RECOVERY_PRECHECK_ADMITTED` |
| L3 | same | Complement of above; existing valid backup always retained | ANY | no recovery admission | Existing 44-row `ALT_SEARCH`/`ARBITRATION` | Frozen Supervisor | existing reason; no new candidate |
| TERMINAL_PRECHECK | `TERMINAL_READY` | exact snapshot/certificate identity, eligible | OPEN | cached certified terminal | RECOVERY_QUERY | TerminalRuntime certificate, Supervisor route | `TERMINAL_FALLBACK_PREFETCHED` |
| TERMINAL_PRECHECK | FAIL/UNKNOWN/stale | no eligible cached terminal | ANY | no recovery | ASSURANCE_BOUNDARY | Supervisor | typed precheck failure; no plant |
| RECOVERY_QUERY | `RECOVERY_CANDIDATE` | candidate source/identity lawful, remaining count 1..6, key unexhausted | OPEN | `SOURCE_BOUNDED_LOCAL_RECOVERY_V1` | C0 | provider proposes; Supervisor routes | candidate ID, index, source, numeric-state key |
| RECOVERY_QUERY | `RECOVERY_EXHAUSTED` or key repeated | no candidate or six attempted | ANY | cached terminal exact | ARBITRATION | Supervisor | `RECOVERY_EXHAUSTED` |
| RECOVERY_QUERY | `DEADLINE_GUARD` | WARNING/EXPIRED | non-OPEN | no new candidate | ARBITRATION | Supervisor | `RECOVERY_DEADLINE_PREEMPTED` |
| RECOVERY_C0 | PASS | matching candidate/binding | OPEN | candidate | L2 | frozen C0 then Supervisor | `RECOVERY_C0_PASS` |
| RECOVERY_C0 | local FAIL excluding `SOURCE_INVALID` | no action authority | OPEN | remaining? query : arbitration | RECOVERY_QUERY / ARBITRATION | Supervisor | typed C0 reason |
| RECOVERY_C0 | `SOURCE_INVALID` / provenance mismatch | source authority broken | ANY | no further candidate | ASSURANCE_BOUNDARY | Supervisor | typed source BLOCK |
| RECOVERY_C0 | UNKNOWN/identity mismatch | global/unresolved evidence | ANY | no action | ASSURANCE_BOUNDARY | Supervisor | typed BLOCK |
| RECOVERY_L2 | PASS | matching L2 evidence | OPEN | candidate | L3 | frozen L2 then Supervisor | `RECOVERY_L2_PASS` |
| RECOVERY_L2 | local FAIL | no action authority | OPEN | remaining? query : arbitration | RECOVERY_QUERY / ARBITRATION | Supervisor | typed L2 reason |
| RECOVERY_L2 | UNKNOWN/identity mismatch | global/unresolved evidence | ANY | no action | ASSURANCE_BOUNDARY | Supervisor | typed BLOCK |
| RECOVERY_L3 | PASS | exact canonical prepared bundle | OPEN | candidate | ARBITRATION | frozen canonical L3 then Supervisor | `RECOVERY_L3_PASS` |
| RECOVERY_L3 | local FAIL | no bundle/action authority | OPEN | remaining? query : arbitration | RECOVERY_QUERY / ARBITRATION | Supervisor | typed L3 reason |
| RECOVERY_L3 | UNKNOWN/identity mismatch | global/unresolved evidence | ANY | no action | ASSURANCE_BOUNDARY | Supervisor | typed BLOCK |
| ARBITRATION | `ARBITRATE` | certified recovery + matching bundle + OPEN | OPEN | selected alternative role | COMMIT via existing `ARB_NAV` | Supervisor.arbitrate, then PlantCommit | existing commit/trace identity |
| ARBITRATION | `ARBITRATE` | no certified recovery, cached terminal still exact | ANY | terminal fallback | existing `ARB_TERMINAL` | Supervisor.arbitrate | one terminal outcome trace |

The primary L3 row splits old `L3_ABSENT_ARB` with `recovery_eligible` vs its exact negation; existing native-alt/valid-backup guard remains higher-priority and mutually exclusive. `recovery_eligible` requires a new typed candidate-local L3 FAIL scope carrier; current unclassified FAIL is routed to the old fallback. Recovery rows require explicit `recovery_mode=true`, source type, candidate identity, phase/event and disjoint PASS/FAIL/UNKNOWN guards. Old rows require `recovery_mode=false` wherever event names overlap. Missing or ambiguous match remains typed BLOCK, never first-match or implicit terminal. No coordinator-side policy tree is permitted. `TERMINAL_PRECHECK` is Supervisor-routed; terminal is cached only for the exact snapshot and authority. Future implementation must prove exhaustive exact-one resolution before any smoke.
