## Summary

This draft diagnoses the frozen Case C primary-reachability funnel from PR #102 without changing any scientific evidence.

## Frozen identity

- PR #102 head: `80a7e691937f9e45b68e1c606befa03ff0a12553`
- Protocol SHA: `e8ea8f3fda15ab81664829ea6f71fcb37f772ad613c13f61007856c16117791a`
- FORMAL_COLLECTION_LOCK SHA: `c30adc48099e8d7b90c980d84389cc1fa693cc1f87d3fc519089efb7cb81b756`
- Analysis execution lock SHA: `08cecef117031f599167ca944ba1ac9ac78da94a908a314ecf750729073e6d59`
- POST_REVEAL_EVIDENCE_LOCK SHA: `a25172a98838d1e132ffc0f0a178029ead0f67dcf44b3ec634eb331c2113d1e4`

## Data-only funnel

- Formal result records: 14,122
- L1 PASS / FAIL / UNKNOWN / other: 0 / 0 / 0 / 14,122 `NOT_REACHED`
- L2 reached true / false / invalid: 0 / 14,122 / 0
- Typed L2 status: 0
- Earliest universal blocking gate: G6 (`l1_status=PASS`)
- G6 first-failing count: 14,122
- Reachability reason: 14,122 `L0_BLOCKED`

`14122 -> G6 -> downstream L2 support=0 -> N_primary=0`

## Minimal source evidence

The formal runner builds the real frozen adapter. `ReadOnlyFrozenCertifierAdapter.evaluate` calls L0 first; if L0 is not PASS, it writes L1 and L2 as `NOT_REACHED`, sets `l2_reached=false`, and records `L0_BLOCKED` without invoking either L1 or L2. The worker still writes a formal result record, explaining why result-record completeness is 14,122 while L2 reach is zero.

## Scope and recovery note

The canonical table was streamed once. A post-scan `Path.write_text(newline=...)` portability error occurred after four compact CSVs were written. Remaining JSON summaries were recovered from those compact files; the canonical table was not reread or copied. No historical replay bridge was needed.

No trial, GPU job, bootstrap, primary analysis, collision/progress analysis, scientific remapping, runtime change, or upstream artifact modification occurred.

## Decision

- Root class: `D1_L1_ZERO_PASS_SUPPORT`
- Subcause: `UPSTREAM_L0_BLOCKED_BEFORE_L1_CERTIFIER_EXECUTION`
- Final status: `PASS_L2_H1_PRIMARY_REACHABILITY_DIAGNOSIS_V1`
- Final decision: `FREEZE_REACHABILITY_ROOT_CAUSE_AND_AUTHORIZE_TARGETED_NEXT_STEP`
- Only next task: `DIAGNOSE_L1_SHADOW_CERTIFIER_SEMANTICS_V1`
