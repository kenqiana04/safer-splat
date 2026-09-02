# Report: Freeze Backup Token Runtime Schema V2

## Decision

Backup Token Runtime Schema V2 is frozen without runtime implementation. The immutable L3 certificate bundle, mutable Supervisor token handle, lifecycle state, exact validity predicate, event chain, consumption transaction, and atomic handoff are now separately specified and content-addressable.

`FINAL_STATUS=PASS_BACKUP_TOKEN_RUNTIME_SCHEMA_V2_FREEZE`

`FINAL_DECISION=FREEZE_BACKUP_TOKEN_SCHEMA_AND_ADVANCE_BLOCKER_DAG`

Only next task: `FREEZE_TERMINAL_EMERGENCY_POLICY_V2`.

## Bundle and token split

`IMMUTABLE_BACKUP_CERTIFICATE_BUNDLE_V2` contains the complete L3 witness, exact source candidate identity/role/provenance, fresh C0/L1/L2/L3 references, certification cycle, predicted `x_(k+1)`, certified tail controls/states/segments, optional terminal evidence, and every frozen authority identity. Its canonical SHA-256 excludes only its self-address fields; it never changes during consumption and has no commit authority.

`RETAINED_BACKUP_TOKEN_V2` is a handle containing the bundle reference, activation index, expected state/time, cursor, remaining tail, lifecycle phase, Supervisor status, terminal ref, revision chain, and invalidation reason. PREPARED, RETIRED, and ABORTED map to public status NONE; only ACTIVE maps to VALID/INVALID/EXHAUSTED.

## Temporal and numeric identity

The L3 witness begins at predicted `x_(k+1)` after source action `u_k`. Tail index zero is `u_(k+1)^backup`. Successful exact `u_k` commit at cycle `k` activates the token for `k+1`; there is no premature activation, missing cycle, duplicated source control, or off-by-one reuse.

State/control identities use exact IEEE-754 binary64 bit hex, explicit dtype/dimension/order, canonical UTF-8 JSON, and SHA-256. This is identity serialization, not physical tolerance. Tracking error, delay, disturbance, and hardware equivalence remain unavailable.

## Validity and invalidation

`BACKUP_TOKEN_STILL_VALID` requires all 19 frozen clauses: ACTIVE/VALID lifecycle, exact bundle, time, state, map, geometry, actuator, dynamics/timebase, provenance, cursor, tail/action, admissibility, event, supersession, consumption, terminal-reference, and physical-unknown boundaries. Any mismatch invalidates before execution. INVALID cannot return to VALID without a new L3 witness, bundle, and token identity.

Retained-tail certificate reuse is narrowly allowed only after the validity predicate passes and the exact cursor action identity is checked. The exact selected vector/ID must equal the executed vector/ID; no value-changing transform is permitted.

## Consumption and handoff

Successful exact backup commit marks one cursor entry consumed, advances by exactly one, and updates the expected certified state and next cycle. A failed commit does not advance. Last-action consumption produces EXHAUSTED; terminal evidence may remain visible but carries no terminal authority.

During navigation handoff the old VALID token remains available until the exact selected candidate commits. Success atomically activates the new token for `k+1` and retires the old token, with no NONE gap. Failure aborts the prepared token and leaves the old token unchanged. Multiple prepared bundles are evidence-only; at most one token is ACTIVE.

## Cross-authority compatibility

- Deadline: `COMPATIBLE_WITHOUT_LOGIC_CHANGE`; warning/expiry block new L3 discovery, while an already valid token remains selectable after expiry.
- Alternative: a retained tail is not an alternative source; its authority is the immutable L3 bundle.
- Terminal: `BACKUP_TOKEN_EXHAUSTED != TERMINAL_ACTION_AUTHORIZED`; priority and external emergency behavior remain unresolved.
- Authority drift: map, geometry, actuator, or dynamics/timebase drift causes VALID→INVALID with no legacy fallback.

## Static validation

- BT invariants: BT-01–BT-24 present.
- Lifecycle properties: PBT-01–PBT-20, 20/20 PASS.
- Adversarial scenarios: 20/20 PASS.
- Unit tests: 12/12 PASS.
- Counterexamples: 0.
- Validator: `PASS_BACKUP_TOKEN_RUNTIME_SCHEMA_V2_VALIDATION`.
- Protected/production source diff: 0.
- Runtime/GPU/rollout/pilot/benchmark/formal collection: all 0.

## Remaining blockers

1. Terminal and External Emergency Policy.
2. Independent Evaluation Oracle.

Runtime implementation remains blocked. This schema does not prove real-system recursive safety, real-time behavior, hardware execution fidelity, collision reduction, or deployment readiness.
