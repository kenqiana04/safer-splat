# Bounded post-repair V3 liveness/routing repair design contract

## Question and immutable outcome

The post-repair 85-pair progress NI result remains FAIL; represented-map hard-safety and integrity remain PASS. The old V3 hard-safety FAIL also remains frozen. The diagnostic reports a concentrated negative tail, 10/10 bottom-tail `EARLY_TERMINAL_LOCK_IN`, and strong descriptive routing associations; it does **not** prove the repair caused progress loss or that terminal policy is defective.

## Hard constraints

P1–P10 in `DESIGN_AUTHORITY.json` are mandatory. Runtime hard radius 0.015 q, zero margin/rho, no epsilon, canonical float32 certification/execution identity, one authoritative Supervisor selector/router, one PlantCommit, and fail-close terminal/boundary are immutable. The 0.025 q historical shell remains diagnostic-only. No success criterion derives from the formal 85 trial IDs, NI outcome, or bottom-tail deltas.

## Narrow prospective property

`ONE_CYCLE_CERTIFIED_REENTRY_OPPORTUNITY`: at a current L1-PASS state where a primary candidate is not fully future-certified, no retained backup is valid, the deadline is OPEN, and a separately authorized recovery source exists, the Supervisor may examine a finite, local candidate set once for that exact numerical state/authority context. Every candidate must pass fresh C0→L2→L3, with the same once-per-cycle L1 result and fresh binding. A passing L3 supplies the existing prepared backup bundle; only the Supervisor may select and the existing commit path may execute. If none pass or any prerequisite is unresolved, retain the frozen terminal evaluation/boundary path. This is an opportunity, not guaranteed goal reachability, hard real-time behavior, or physical safety.

Under the frozen sampled-data dynamics, p(k+1)=p(k)+dt v(k), v(k+1)=v(k)+dt u(k), so current u has zero derivative on immediate position and dt²I on p(k+2). The design never credits u(k) with improving L1's immediate positional h; recovery evidence belongs to L2/H1 and L3's subsequent chain.

## Pre-outcome authority requirement

The present provider accepts only `SOURCE_NATIVE_EXISTING`, and `make_candidate` marks only it and `PRIMARY_NATIVE_CBF_QP` lawful. A future finite recovery source is **not currently authorized**. Implementation must first add a versioned, explicit source authority for exactly the proposed local library and prove C0 provenance/identity; it may not silently set `lawful=true`. If this source authority cannot be frozen without relaxing existing contracts, implementation must block. No runtime source is changed in this task.
