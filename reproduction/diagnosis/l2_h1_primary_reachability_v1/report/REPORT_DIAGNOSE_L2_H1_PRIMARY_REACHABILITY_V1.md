# Report: Diagnose L2/H1 Primary Reachability V1

## Answer first

1. `N_L1_PASS / FAIL / UNKNOWN / other = 0 / 0 / 0 / 14,122 NOT_REACHED`.
2. `N_L2_reached true / false = 0 / 14,122`.
3. `N_L2_typed = 0`.
4. Earliest universal blocking gate: `G6 — l1_status=PASS`.
5. G6 first-failing count: `14,122`.
6. Root cause: `D1_L1_ZERO_PASS_SUPPORT`, subcause `UPSTREAM_L0_BLOCKED_BEFORE_L1_CERTIFIER_EXECUTION`.

`14122 -> G6 l1_status=PASS -> downstream L2 support=0 -> N_primary=0`

All 14,122 canonical rows survive G1–G5. Every row then reports `l1_status=NOT_REACHED`, `l2_reached=false`, an untyped L2 status, and `l2_reachability_reason=L0_BLOCKED`. Thus G7 and G8 also have 14,122 overlapping unmet rows, but neither is the first cause: cumulative support was already zero at G6.

## Why 14,122 result records do not imply 14,122 L2 evaluations

The shadow worker writes one result record after each adapter evaluation. The adapter result may legitimately encode that downstream gates were not reached. Therefore:

- formal result record exists: 14,122;
- L2 reached: 0;
- typed L2 PASS/FAIL/UNKNOWN: 0.

Record existence proves logging completeness, not certifier execution.

## Minimal code evidence

The formal trial wrapper dispatches `server_run_one.py`, which constructs the real frozen L0/L1/L2 callables and injects them into `ReadOnlyFrozenCertifierAdapter`. In `evaluate`, `_l0(payload)` runs first. Any L0 result other than PASS assigns L1 and L2 `NOT_REACHED`, reason `L0_BLOCKED`, and `l2_reached=false`. `_l1` is called only after L0 PASS; `_l2` only after L1 PASS. The canonical table builder then applies the frozen G6/G7/G8 tests without remapping these values.

See `minimal_code_path.md` for the bounded five-function trace.

## Evidence boundary

The diagnosis does not show that L1 or L2 was safe, unsafe, or ineffective: neither was reached. It does not change the frozen Case C result, denominator, eligibility, UNKNOWN handling, controller, certifier, map, or threshold. No collision/progress or runtime-efficacy analysis was performed.

The exact split between L0 FAIL and L0 UNKNOWN was not retained by the four compact outputs available after the one-pass packaging failure. The demonstrated branch cause remains direct: all rows carry `L0_BLOCKED` and never reach L1.

## Streaming recovery record

The server streamed the canonical table once and wrote four compact CSVs. JSON serialization then failed because the server Python version does not accept `newline` in `Path.write_text`. The portability call was corrected for reproducibility, but the canonical table was not reread. Remaining summaries were reconstructed only from the compact CSVs; no raw row was copied or printed.

## Decision

- Case: `R1`
- Root class: `D1_L1_ZERO_PASS_SUPPORT`
- Final status: `PASS_L2_H1_PRIMARY_REACHABILITY_DIAGNOSIS_V1`
- Final decision: `FREEZE_REACHABILITY_ROOT_CAUSE_AND_AUTHORIZE_TARGETED_NEXT_STEP`
- Only next task: `DIAGNOSE_L1_SHADOW_CERTIFIER_SEMANTICS_V1`
