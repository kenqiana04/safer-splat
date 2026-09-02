# Report: Freeze Alternative Source Authority V2

## Decision

`ALTERNATIVE_SOURCE_AUTHORITY` is frozen as a provenance and search-authority contract. The Supervisor is the only alternative-search owner. L4 may request evaluation of an already lawful control but cannot create, select, or commit one.

`FINAL_STATUS=PASS_ALTERNATIVE_SOURCE_AUTHORITY_V2_FREEZE`

`FINAL_DECISION=FREEZE_ALTERNATIVE_SOURCE_AUTHORITY_AND_ADVANCE_BLOCKER_DAG`

Only next task: `FREEZE_BACKUP_TOKEN_RUNTIME_SCHEMA_V2`.

## Legal source taxonomy

- `SOURCE_NATIVE_EXISTING`: the candidate existed before the alternative request; the only default-authorized V2 source.
- `SOURCE_PREDEFINED_LIBRARY`: taxonomy only; requires a separately frozen explicit authorization.
- `SOURCE_POLICY_OUTPUT`: taxonomy only; requires a separately frozen explicit authorization.
- `SOURCE_SYNTHETIC`: forbidden in this contract.

`u_des` is not a native alternative, and the historical task-local candidate library is not V2 authority. Random perturbation, noise injection, interpolation, heuristic steering, outcome-conditioned generation, and collision-driven candidate creation are prohibited. L2/L3 failures, risk, and margin cannot create controls.

## Identity and recertification

Every alternative binds `candidate_id`, source type, creation timestamp, state identity, map identity, actuator authority, and controller identity. Any field change requires a new candidate ID.

Every attempt produces fresh C0, L1, L2, and L3 evidence. Certificate objects cannot be reused. L1 remains candidate-independent: its fresh record binds the unchanged immediate state segment to the exact alternative attempt and does not create a new candidate-sensitive L1 semantic.

An alternative that passes the chain is eligible only for Supervisor arbitration; it still has no direct execution authority.

## Deadline, failure, and backup interaction

Alternative evaluation may begin only in `DEADLINE_OPEN`. `DEADLINE_WARNING` forbids new high-cost alternative search and `DEADLINE_EXPIRED` forbids all alternative search.

Typed outcomes are `NO_ALTERNATIVE_AVAILABLE`, `SOURCE_INVALID`, `PROVENANCE_MISSING`, `ALTERNATIVE_CERTIFICATION_FAILED`, `ALTERNATIVE_SEARCH_BLOCKED_BY_DEADLINE`, and `UNKNOWN_SOURCE`. None is ordinary success, and none alone means unsafe state, collision, global infeasibility, or controller failure.

A backup witness is an L3 product, not an alternative source. A dual-role control must preserve the same candidate provenance and share Geometry, Actuator, Map, State, and fresh recertification identities. Runtime backup-token authority remains unresolved.

## Dependency audit

Alternative Source Authority is resolved without modifying PRs #107–#110. The user-directed next DAG node is Backup Token Runtime Schema because its Geometry, Actuator, Deadline, and Alternative Source prerequisites are now frozen. Terminal/Emergency Policy and Independent Evaluation Oracle remain unresolved; precommit implementation remains blocked.

## Validation and scope

- Contract tests: 10 passed, 0 failed.
- Validator: `PASS_ALTERNATIVE_SOURCE_AUTHORITY_V2_VALIDATION`.
- Protected/production source mutations: 0.
- Runtime/controller/candidate-generation mutations: 0/0/0.
- Rollout/GPU/benchmark/formal collection/tuning: 0/0/0/0/0.

## Scientific non-claims

This contract does not demonstrate better control, lower collision, higher success rate, improved progress, optimality, or completeness of candidate search. It provides no runtime or performance evidence.

## Remaining blockers

1. Backup Token Runtime Schema.
2. Terminal and External Emergency Policy.
3. Independent Evaluation Oracle.
