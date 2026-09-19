# Candidate-Scoped Canonical L2 Evidence Repair Specification

## Compatibility contract

The legacy cycle-flat facts remain unchanged for the primary candidate only:

`canonical_l2_x_k1_identity`, `canonical_l2_p_k1_identity`, `canonical_l2_x_k2_identity`, `canonical_l2_p_k2_identity`, `canonical_l2_segment_identity`, `canonical_l2_status`, `canonical_l2_reason`, `canonical_l2_evidence_identity`, and `canonical_selected_candidate_identity`.

Alternative and bounded-recovery evaluations cannot overwrite those fields.

## Scoped contract

Every L2 evaluation records one payload in namespace `canonical_l2_candidate_evidence`, scoped by `candidate.identity.value`. Each payload contains `candidate_identity`, `candidate_role`, `candidate_source_type`, the four predicted state/position identities, `segment_identity`, `status`, `reason`, and `evidence_identity`.

`CanonicalIdentityLedger.record_scoped(trial_id, cycle_index, namespace, scope_key, **payload)` owns scoped observational storage. Namespace and scope keys must be non-empty strings. Payload field names, namespace names, and scope keys are serialized in lexical order. Candidate identity is deterministic and no wall-clock or random value is introduced.

## Anti-rewrite and idempotence

The existing flat `CANONICAL_EVIDENCE_REWRITE_FORBIDDEN:<name>` guard remains unchanged.

For scoped evidence, an identical second write to the same trial/cycle/namespace/scope is explicitly idempotent. A different payload for the same scope is rejected with `CANONICAL_SCOPED_EVIDENCE_REWRITE_FORBIDDEN:<namespace>:<scope_key>`. Different candidate scopes coexist.

## Trace schema decision

Keep `EVALUATION_TRACE_SCHEMA_V2_CERT_EXEC_IDENTITY_V1`. `TraceWriter` contracts `facts` as an extensible tuple of key/value observations: it rejects a small explicit set of scientific outcome keys and canonicalizes the full record at finalization, but does not define a closed fact-name schema. The new namespace is additive observational identity evidence, the existing flat meanings do not change, and no routing/selection/commit consumer reads it. A schema bump would incorrectly imply a change to the transaction or scientific semantics.

## Authority exclusions

Candidate-scoped evidence has no routing, candidate selection, PlantCommit, CBF, geometry, trigger, fallback, or scientific authority. This repair changes neither candidate vectors nor certificate results; it only makes multiple already-authorized L2 evaluations representable.
