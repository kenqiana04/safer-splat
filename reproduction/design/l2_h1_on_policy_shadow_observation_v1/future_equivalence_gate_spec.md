# Future Control-Trace Equivalence Gate

Phase 1 compares observer OFF (control) and observer ON with zero authority (shadow) under identical frozen source, environment, config, trial manifest, map identity, and seed policy.

Required identities/equivalences:

1. `control_trace_equivalence`: exact selected action sequence where deterministic execution is promised;
2. `selected_candidate_hash_equivalence`: exact sequence equality;
3. `trial_seed_equivalence`: exact manifest and RNG identity;
4. `map_identity_equivalence`: exact content/snapshot identities;
5. `controller_return_value_equivalence`: exact values/status/branch sequence;
6. exact L0/L1 production outcomes where those outcomes belong to the frozen controller;
7. same termination reason and step count;
8. progress/collision traces only as equivalence QA, never performance evidence.

If exact floating equality is not supported by a frozen dependency, Phase 1's protocol must pre-register a field-specific absolute/relative tolerance and hash the tolerance manifest **before either arm runs**. Tolerances cannot be loosened after seeing differences. Observer-induced scheduling effects outside the frozen tolerance fail G1.

Any failure blocks Phase 2/3. This design task does not execute the gate.

**Scope:** DESIGN ONLY | NO ON-POLICY COLLECTION | NO CONTROLLER AUTHORITY | NO DECISION FEEDBACK | NO PERFORMANCE CLAIM.
