## Scope

Freeze an independent, posthoc, read-only evaluation oracle contract for the SAFER-Splat V2 method chain. This is specification and static validation only; it implements no runtime/evaluator path and executes no trial.

## Exact lineage

- Base PR: #113, Open Draft
- Base branch: `freeze-terminal-emergency-policy-v2`
- Exact head: `5595e56b756291881fb9f6f17ba3d7551263574f`
- PR #107–#113 artifacts remain unchanged.

## Frozen decisions

- Unique owner: `POSTHOC_EVALUATION_ORACLE`; read-only, after immutable trace lock, `ORACLE_FEEDBACK_AUTHORITY=false`.
- Internal C0/L1/L2/L3 statuses are Tier-D diagnostics and cannot define primary collision outcome.
- Executed action/role facts are Tier C.
- Independent recomputation against the frozen represented map is Tier B and must be labeled `REPRESENTED_MAP_RELATIVE`.
- Scene-matched external GT is Tier A. Replica apartment_0 has a scoped official mesh authority, but current Stonehenge mainline has no corresponding independent GT; physical-collision/real-world-safety claims are not authorized.
- Collision proxy evaluates closed executed segments with the operational footprint `0.015 m`; certification-margin violation is separate at `0.025 m` and is not collision.
- Legacy `run.py` safety is same-map-family endpoint logging and is not the final oracle. Its moving-timeout success label is explicitly rejected.
- Goal authority is the pre-existing 6-D Euclidean predicate `<0.001`; timeout alone is never goal success.
- Progress reuses the historical `(d_start-d_final)/d_start` position-distance formula with no clipping.
- Safety, liveness, assurance behavior, diagnostics, and timing stay separate; there is no composite score.
- Trial is the primary statistical unit; compared variants use identical paired trial identities; UNKNOWN is retained and never SAFE.

## Validation

- Execution lock binds Commit 1 and raw Git blobs.
- Anti-circularity checker: PASS; forbidden feedback/certificate/threshold edges absent.
- Synthetic contract scenarios: 24/24 statically covered.
- Unit/static tests: 6/6 PASS.
- Validator: `PASS_INDEPENDENT_EVALUATION_ORACLE_V2_VALIDATION` (26/26).
- Production/runtime diff: 0.
- GPU/rollout/pilot/official100/formal collection: 0.

## Decision

`FINAL_STATUS=PASS_INDEPENDENT_EVALUATION_ORACLE_V2_FREEZE`

`FINAL_DECISION=FREEZE_INDEPENDENT_EVALUATION_ORACLE_AND_ADVANCE_DAG`

The V6 DAG has no unresolved preimplementation contract blocker. Runtime remains unauthorized; the only next task is `DESIGN_ACTIVE_RUNTIME_ASSURANCE_IMPLEMENTATION_V2`.
