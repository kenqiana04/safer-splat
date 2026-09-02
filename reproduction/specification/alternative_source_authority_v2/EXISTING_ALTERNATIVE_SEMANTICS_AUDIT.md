# Existing Alternative Semantics Audit

PR #107 establishes that the baseline QP output is the primary proposal and that `u_des` is only a nominal reference. It explicitly withholds authority from the historical task-local candidate library and prohibits synthetic, rotated, noisy, interpolated, perturbed, or outcome-fitted alternatives. `ALT_AVAILABLE` remained abstract pending this source contract.

PR #107 also makes L4 proposal-only, requires a new candidate identity, and requires full candidate-sensitive C0/L2/L3 recertification under the same state, map, geometry, actuator, and timebase. Its L1 certificate is candidate-independent and L1 FAIL is never repaired by changing candidates.

This V2 task tightens evidence freshness as directed: every alternative evaluation record contains fresh C0, L1, L2, and L3 results, with no certificate-object reuse. Fresh L1 does not change L1 mathematics or make it candidate-sensitive; it re-evaluates/rebinds the same immediate state segment to the alternative attempt's exact cycle identity.

PR #110 supplies the deadline gate: only `DEADLINE_OPEN` allows new alternative evaluation. Warning and expiry forbid it. Backup witness generation remains L3 authority and is not reclassified as alternative generation.
