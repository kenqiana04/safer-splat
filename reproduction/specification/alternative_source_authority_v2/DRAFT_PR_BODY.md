## Purpose

Freeze Alternative Source Authority V2 as a specification-only provenance contract. This PR is based exactly on Draft PR #110 head `52467acd2ab82c300a8f6c3ce712ab0d59d4f4cf` and preserves PRs #107–#110 read-only.

## Frozen contract

- The Supervisor is the sole alternative-search owner; L4 is request-only and never creates, selects, or commits controls.
- V2 default authorization permits only `SOURCE_NATIVE_EXISTING`.
- Predefined-library and policy-output entries require a separate explicit frozen authorization; synthetic sources are forbidden here.
- Random/noisy/interpolated/heuristic/outcome-conditioned/collision-driven generation is prohibited.
- Every candidate binds seven immutable provenance fields; any change requires a new candidate ID.
- Every alternative receives fresh `C0 → L1 → L2 → L3` evidence with no certificate reuse. L1 remains candidate-independent.
- New evaluation is allowed only in `DEADLINE_OPEN`; warning and expiry block it.
- Backup witness authority remains L3 and is not alternative-source generation.
- Alternative absence/failure/UNKNOWN is non-success but does not imply unsafe state.

## Validation

- 10/10 static tests pass.
- `PASS_ALTERNATIVE_SOURCE_AUTHORITY_V2_VALIDATION`.
- Protected/production source mutation count: 0.
- Runtime, candidate generation, rollout, GPU, benchmark, collection, and tuning counts: 0.

## Evidence boundary

No better-control, collision, success-rate, progress, optimality, or search-completeness claim is made. Backup-token, terminal/emergency, and independent-oracle blockers remain unresolved.

`FINAL_STATUS=PASS_ALTERNATIVE_SOURCE_AUTHORITY_V2_FREEZE`

`FINAL_DECISION=FREEZE_ALTERNATIVE_SOURCE_AUTHORITY_AND_ADVANCE_BLOCKER_DAG`

Only next task: `FREEZE_BACKUP_TOKEN_RUNTIME_SCHEMA_V2`.
