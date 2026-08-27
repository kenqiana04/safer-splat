# L2/H1 frozen historical replay V1

Result: `CASE_A` / `PASS_L2_H1_FROZEN_REPLAY_VALIDATION_V1`.

The pre-frozen universe contains 6853 rows: 2594 FORMAL_REPLAYABLE, 0 DIAGNOSTIC_RECONSTRUCTABLE, and 4259 NOT_REPLAYABLE. Exactly 788 stored-L1-PASS architecture-reached tuples were directly evaluated with PR #94: 770 PASS, 18 FAIL, and 0 UNKNOWN. The 18 L1 PASS/L2 FAIL rows are a bounded information increment, not performance evidence.

Start with `report/REPORT_VALIDATE_L2_H1_SHADOW_CERTIFIER_ON_FROZEN_REPLAY_V1.md`, `denominator_audit.json`, `selection_bias_audit.md`, and `claim_boundary.md`.
