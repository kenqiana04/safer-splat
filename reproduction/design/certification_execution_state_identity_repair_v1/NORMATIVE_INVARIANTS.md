# Normative Invariants

## CERTIFICATION_EXECUTION_CONTINUITY_INVARIANT_V1

For the same map identity, frozen position-first forward-Euler dynamics, exact dt/timebase, exact committed action, exact state serialization, and no external disturbance:

1. The L2 first predicted position at cycle `k` SHALL equal the actual committed position at cycle `k+1` bitwise.
2. The L2 second predicted position at cycle `k` SHALL equal both the next cycle's canonical L1 endpoint and the actual committed position at cycle `k+2` bitwise.
3. The certifier SHALL consume the same canonical endpoint identities used by execution-continuity validation.

## Additional invariants

- **CEI-01 Single arithmetic authority:** all safety-relevant predicted state construction uses one canonical transition identity.
- **CEI-02 Side-effect separation:** `T_exec` is pure; `PlantCommitAdapter.commit` remains the sole plant side-effect authority.
- **CEI-03 L1 action independence:** the immediate position endpoint is bitwise invariant for all admissible actions.
- **CEI-04 L2 sequentiality:** L2 uses sequential canonical transitions, not an independently rounded closed form.
- **CEI-05 Exact provenance:** every endpoint binds state, action, map, geometry, dynamics, dt, dtype/device, arithmetic, and serialization identities.
- **CEI-06 Mismatch fail-closed:** a state-identity mismatch cannot become PASS or commit-eligible evidence.
- **CEI-07 Backup continuity:** every token state and cursor action is continuous with its canonical predicted lineage.
- **CEI-08 Terminal continuity:** terminal and swept-segment evidence use the same canonical state construction.
- **CEI-09 No authority expansion:** the repair adds no controller, routing, selection, plant, backup, terminal, deadline, or scientific authority.
- **CEI-10 Historical shell isolation:** 0.025 q remains diagnostic-only.
- **CEI-11 Frozen-result preservation:** no prior V3 outcome is rewritten or reclassified.
- **CEI-12 Trace completeness:** every commit-eligible path has complete canonical identity evidence; incomplete evidence is never evaluation-eligible.
