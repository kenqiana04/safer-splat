# V1 H2 Constraint-Reduction Reconciliation

V1's method-level active-constraint means are **M1=1600.000** and **M2=160.041** because every method mean uses all 100 terminal records. M1 contributes 2,000 rows for each of the 80 scenarios that enter QP and zero for the 20 G2 Start-Safe rejections, yielding 1,600. M2 reduces rows in G0, G1, G3, and G4, while the same 20 G2 records remain zero, yielding approximately 160.041.

The V1 H2 activation statistic is not a global reduction statistic. It compares M2 with M1 only inside designated G2. All 20 G2 states terminate at Start-Safe, so neither method enters QP and both active-count summaries are zero. Therefore H2 activation is correctly zero under the V1 code but the group does not test H2. The semantic defect is presenting the global reduction alongside the designated-group activation without an explicit stage-entry denominator. V2 records `stage_entered`, `input_constraint_count`, `provably_redundant_count`, and `output_constraint_count` directly and defines dominance activation from the shadow predicate before lock.

PR #80 and its Case-B conclusion remain unchanged.
