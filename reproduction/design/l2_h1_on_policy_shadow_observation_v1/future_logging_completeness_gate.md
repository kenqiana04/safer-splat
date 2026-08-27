# Future Logging Completeness Gate

Before Phase 3, Phase 2 must demonstrate on its frozen pilot manifest:

- every intended step has either one complete payload or one explicit minimal drop record;
- every complete selected step contains finite numeric `u_k`, `u_k_hash`, commit ID, state ID, and map ref;
- explicit L0/L1/candidate/L2 reachability is present for every complete payload;
- every map ref resolves to an immutable content identity;
- sequence gaps reconcile exactly with drop/error records;
- no instrumentation failure is counted as L2 UNKNOWN;
- candidate synthesis count is zero;
- selected candidate hash joins exactly to `u_k_hash`;
- no required ID collision or off-by-one check fails.

G2 requires zero missing `u_k` among complete selected-step payloads. G3/G4 require 100% explicit reachability and map resolution among complete payloads. Formal collection also reports overall completeness, including drops; no denominator silently excludes a drop.

The gate is not satisfied by an average rate alone. Any systematic missingness, ambiguous map identity, or unexplained sequence gap blocks Phase 3 and requires a separately authorized instrumentation repair.

**Scope:** DESIGN ONLY | NO ON-POLICY COLLECTION | NO CONTROLLER AUTHORITY | NO DECISION FEEDBACK | NO PERFORMANCE CLAIM.
